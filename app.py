import streamlit as st
import pandas as pd
import time
import random
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
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
                    font-size: 22px !important; color: #000000 !important; line-height: 1.6; border: 1px solid #ddd; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .timer-text { font-size: 32px; font-weight: bold; color: #D32F2F; text-align: center; }
    .stRadio label { font-size: 19px !important; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. STUDENT PORTAL ---
with st.sidebar:
    st.title("VikidylEdu")
    role = st.selectbox("Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("CBT Mock Registration")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School:")
        with c2: name = st.text_input("Full Name:")
        
        y_col, e_col, s_col = st.columns(3)
        with y_col: year_choice = st.selectbox("Exam Year", ["ALL YEARS (Mixed)", "2020", "2021", "2022", "2023", "2024", "2025"])
        with e_col: exam = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", sorted(df['subject'].unique()) if not df.empty else ["ENGLISH"])

        if st.button("🚀 START SHUFFLED EXAM") and school and name:
            # Filtering
            if year_choice == "ALL YEARS (Mixed)":
                quiz_df = df[(df['exam'] == exam.upper()) & (df['subject'] == subj.upper())]
            else:
                quiz_df = df[(df['exam'] == exam.upper()) & (df['subject'] == subj.upper()) & (df['year'] == year_choice)]
            
            if not quiz_df.empty:
                # RANDOMIZATION LOGIC
                quiz_data = quiz_df.sample(frac=1).reset_index(drop=True) 
                st.session_state.quiz_data = quiz_data
                st.session_state.exam_active = True
                st.session_state.start_time = time.time()
                st.session_state.current_q = 0
                st.session_state.user_answers = {}
                st.session_state.db_id = f"{school} | {name} | {subj} | {year_choice}"
                st.rerun()
            else:
                st.error("No questions found for this selection.")
    else:
        # EXAM UI
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.markdown(f"<div class='timer-text'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        q = q_df.iloc[curr]
        
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.markdown(f'<div class="question-box">{q["question"]}</div>', unsafe_allow_html=True)
        
        opts = [str(q['a']), str(q['b']), str(q['c']), str(q['d'])]
        ans = st.radio("Choose Answer:", opts, key=f"q_{curr}")
        st.session_state.user_answers[curr] = ans
        
        col1, col2, col3 = st.columns([1,1,2])
        with col1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with col2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with col3:
            if st.button("🏁 SUBMIT FOR GRADING"):
                score = 0
                c_col = next((c for c in ['correct_answer', 'correct_answee'] if c in df.columns), 'correct_answer')
                for i, user_ans in st.session_state.user_answers.items():
                    if str(user_ans).strip().upper() == str(q_df.iloc[i][c_col]).strip().upper(): score += 1
                
                # Uploading detailed result for Teacher analytics
                # We store a "Script" in a hidden column or simply show it in the review
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}, on_conflict="name").execute()
                st.session_state.final_score = score
                st.session_state.finished_rows = q_df.to_dict('records')
                st.session_state.final_ans = st.session_state.user_answers.copy()
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Score: {st.session_state.final_score}")
        with st.expander("Review Script & Explanations"):
            for i, r in enumerate(st.session_state.finished_rows):
                u_a = st.session_state.final_ans.get(i, "N/A")
                c_a = r.get('correct_answer', 'Check Sheet')
                color = "green" if str(u_a).upper() == str(c_a).upper() else "red"
                st.markdown(f"**Q{i+1}:** {r['question']}")
                st.markdown(f"Your Answer: :{color}[{u_a}] | Correct: :green[{c_a}]")
                st.info(f"💡 Explanation: {r.get('explanation', 'N/A')}")
        if st.button("New Test"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER SUITE (DIAGNOSTICS) ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        st.header("Teacher Diagnostic Suite")
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            # Filter by student name for deep dive
            search = st.text_input("Search Student Name to see their Script:")
            if search:
                student_data = ld[ld['name'].str.contains(search, case=False)]
                st.write(f"Found {len(student_data)} attempt(s).")
                for index, row in student_data.iterrows():
                    st.write(f"### {row['name']} - Score: {row['score']}")
                    st.info("The teacher can now identify that this student is struggling with the subject mentioned in the name string above.")
            st.divider()
            st.write("### Full Leaderboard")
            st.dataframe(ld)

elif role == "👨‍👩‍👧 Parent":
    n = st.text_input("Enter Child Name:")
    if n:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            st.table(ld[ld['name'].str.contains(n, case=False)])

st.caption("VikidylEdu Centre © 2026")
