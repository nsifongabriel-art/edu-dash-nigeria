import streamlit as st
import pandas as pd
import time
import random
import json
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3VuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=1)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        for col in ['exam', 'subject', 'year']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().str.upper()
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""
    <style>
    .question-box { background-color: #ffffff; padding: 25px; border-radius: 12px; border-left: 12px solid #1E3A8A; 
                    font-size: 22px !important; color: #000000 !important; line-height: 1.6; border: 1px solid #ddd; }
    .timer-text { font-size: 32px; font-weight: bold; color: #D32F2F; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
    role = st.selectbox("Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("CBT Exam Setup")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School:")
        with c2: name = st.text_input("Full Name:")
        
        y_col, e_col, s_col, q_col = st.columns(4)
        with y_col: year_choice = st.selectbox("Year", ["ALL YEARS", "2020", "2021", "2022", "2023", "2024"])
        with e_col: exam = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", sorted(df['subject'].unique()) if not df.empty else ["ENGLISH"])
        with q_col: q_count = st.selectbox("Number of Questions", [20, 50, 70, 100, 200])

        if st.button("🚀 START SHUFFLED EXAM") and school and name:
            filt = (df['exam'] == exam.upper()) & (df['subject'] == subj.upper())
            if year_choice != "ALL YEARS": filt &= (df['year'] == year_choice)
            
            quiz_df = df[filt]
            if not quiz_df.empty:
                # Shuffle and Limit
                quiz_data = quiz_df.sample(n=min(len(quiz_df), q_count)).reset_index(drop=True) 
                st.session_state.quiz_data = quiz_data
                st.session_state.exam_active = True
                st.session_state.start_time = time.time()
                st.session_state.current_q = 0
                st.session_state.user_answers = {}
                st.session_state.db_id = f"{school} | {name} | {subj} | {year_choice}"
                st.rerun()
            else: st.error("No questions found.")
    else:
        # EXAM IN PROGRESS
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.markdown(f"<div class='timer-text'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        q = q_df.iloc[curr]
        
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.markdown(f'<div class="question-box">{q["question"]}</div>', unsafe_allow_html=True)
        
        opts = [str(q['a']), str(q['b']), str(q['c']), str(q['d'])]
        ans = st.radio("Choose:", opts, key=f"q_{curr}")
        st.session_state.user_answers[curr] = ans
        
        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with c2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with c3:
            if st.button("🏁 SUBMIT EXAM"):
                score = 0
                script_data = []
                c_col = next((c for c in ['correct_answer', 'correct_answee'] if c in df.columns), 'correct_answer')
                
                for i, row in q_df.iterrows():
                    u_a = st.session_state.user_answers.get(i, "Skipped")
                    c_a = str(row[c_col]).strip().upper()
                    is_correct = str(u_a).strip().upper() == c_a
                    if is_correct: score += 1
                    script_data.append({"q": row['question'], "ua": u_a, "ca": c_a, "ok": is_correct})
                
                # SAVE TO DB (Including Script)
                supabase.table("leaderboard").upsert({
                    "name": st.session_state.db_id, 
                    "score": score,
                    "script": json.dumps(script_data) # This saves the entire script!
                }, on_conflict="name").execute()
                
                st.session_state.final_score = score
                st.session_state.final_script = script_data
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Exam Completed! Score: {st.session_state.final_score}")
        with st.expander("Review My Answers"):
            for item in st.session_state.final_script:
                color = "green" if item['ok'] else "red"
                st.write(f"**Q:** {item['q']}")
                st.markdown(f"Your Answer: :{color}[{item['ua']}] | Correct: :green[{item['ca']}]")
        if st.button("New Test"): st.session_state.clear(); st.rerun()

# --- 5. TEACHER SUITE (WITH SCRIPT VISIBILITY) ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        st.header("Teacher Diagnostic Suite")
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            selected_student = st.selectbox("Select a Student to view their full Script:", ld['name'].tolist())
            
            if selected_student:
                student_row = ld[ld['name'] == selected_student].iloc[0]
                st.write(f"### Results for: {selected_student}")
                st.metric("Total Score", student_row['score'])
                
                if 'script' in student_row and student_row['script']:
                    try:
                        script = json.loads(student_row['script'])
                        for i, item in enumerate(script):
                            with st.expander(f"Q{i+1}: {item['q'][:50]}..."):
                                st.write(f"**Question:** {item['q']}")
                                st.write(f"**Student Answer:** {item['ua']}")
                                st.write(f"**Correct Answer:** {item['ca']}")
                                if not item['ok']: st.error("Student missed this question.")
                                else: st.success("Student got this right.")
                    except: st.warning("Script format incompatible.")
                else: st.info("No script data found for this entry.")

elif role == "👨‍👩‍👧 Parent":
    n = st.text_input("Child Name:")
    if n:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            st.table(ld[ld['name'].str.contains(n, case=False)][['name', 'score']])
