import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=2)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. UI CONFIG ---
st.set_page_config(page_title="VikidylEdu CBT", page_icon="🇳🇬", layout="wide")
st.markdown("""<style>
    .stButton>button { border-radius: 8px; width: 100%; font-weight: bold; }
    .q-btn { background-color: #F0F2F6; border: 1px solid #CCC; margin: 2px; }
    .timer-text { font-size: 28px; font-weight: bold; color: #D32F2F; text-align: center; background: #FFEBEE; padding: 10px; border-radius: 10px; border: 2px solid #D32F2F; }
    .created-by { text-align: center; color: #1E3A8A; padding: 20px; font-weight: bold; border-top: 2px solid #EEE; margin-top: 40px;}
</style>""", unsafe_allow_html=True)

# --- 3. LOGIC HELPERS ---
def clean_lb(data):
    if not data: return pd.DataFrame()
    ld = pd.DataFrame(data)
    def parse_name(val):
        parts = val.split('|')
        return pd.Series([parts[1].strip() if len(parts)>1 else "N/A", parts[0].strip() if len(parts)>0 else "N/A", f"{parts[2].strip() if len(parts)>2 else ''} ({parts[3].strip() if len(parts)>3 else ''})"])
    ld[['Student', 'School', 'Details']] = ld['name'].apply(parse_name)
    return ld[['Student', 'School', 'Details', 'score']].sort_values(by="score", ascending=False)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=60)
    st.title("VikidylEdu")
    role = st.selectbox("Menu", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])
    st.caption("Developed by: **Ufford I.I.**\nVikidylEdu Centre © 2026")

# --- 5. STUDENT CBT PORTAL ---
if role == "✍️ Student":
    t1, t2 = st.tabs(["📝 CBT Exam Room", "🏆 Leaderboard"])
    
    with t1:
        if 'exam_active' not in st.session_state:
            # Registration Form
            c1, c2 = st.columns(2)
            with c1: school = st.text_input("School:")
            with c2: name = st.text_input("Full Name:")
            
            l_col, y_col, e_col = st.columns(3)
            with l_col: level = st.selectbox("Level", ["Junior (JSS)", "Senior (SSS)"])
            with y_col: year = st.selectbox("Year", [str(y) for y in range(2026, 2014, -1)])
            with e_col: exam = st.selectbox("Exam", ["BECE"] if "Junior" in level else ["WAEC", "NECO", "JAMB"])
            
            subjs = ["Mathematics", "English", "Physics", "Chemistry", "Biology"] # Simplified for demo
            subj = st.selectbox("Select Subject", subjs)

            if st.button("🚀 START CBT EXAM") and school and name:
                st.session_state.exam_active = True
                st.session_state.start_time = time.time()
                st.session_state.current_q = 0
                st.session_state.user_answers = {} # Store answers here
                st.session_state.db_id = f"{school} | {name} | {subj} | {year}"
                st.session_state.s_subj = subj.strip().lower()
                st.session_state.s_year = str(year).strip()
                st.rerun()
        
        else:
            # --- TIMER ---
            elapsed = time.time() - st.session_state.start_time
            rem = max(0, 1800 - int(elapsed))
            m, s = divmod(rem, 60)
            st.markdown(f"<div class='timer-text'>⏱️ {m:02d}:{s:02d}</div>", unsafe_allow_html=True)
            
            if rem <= 0:
                st.error("🚨 Time Up! Exam Submitted.")
                if st.button("See Final Score"): st.session_state.clear(); st.rerun()
            
            # --- FETCH QUESTIONS ---
            quiz_df = df[(df['subject'] == st.session_state.s_subj) & (df['year'] == st.session_state.s_year)]
            
            if not quiz_df.empty:
                total = len(quiz_df)
                curr = st.session_state.current_q
                q_data = quiz_df.iloc[curr]
                
                # --- NAVIGATION GRID ---
                st.write("### Question Navigation")
                cols = st.columns(10)
                for i in range(total):
                    btn_label = f"{i+1}"
                    if cols[i % 10].button(btn_label, key=f"nav_{i}"):
                        st.session_state.current_q = i
                        st.rerun()
                
                st.divider()
                
                # --- QUESTION DISPLAY ---
                st.subheader(f"Question {curr + 1} of {total}")
                st.info(q_data['question'])
                
                # Pre-fill answer if already selected
                saved_ans = st.session_state.user_answers.get(curr, None)
                options = [str(q_data['a']), str(q_data['b']), str(q_data['c']), str(q_data['d'])]
                
                choice = st.radio("Select your answer:", options, index=options.index(saved_ans) if saved_ans in options else 0)
                
                # Save answer immediately on change
                st.session_state.user_answers[curr] = choice
                
                # --- PREV / NEXT BUTTONS ---
                b1, b2, b3 = st.columns([1,1,2])
                with b1:
                    if st.button("⬅️ Previous") and curr > 0:
                        st.session_state.current_q -= 1
                        st.rerun()
                with b2:
                    if st.button("Next ➡️") and curr < total - 1:
                        st.session_state.current_q += 1
                        st.rerun()
                with b3:
                    if st.button("🏁 FINISH & SUBMIT EXAM"):
                        # Calculate Score at the end
                        score = 0
                        c_col = next((c for c in ['correct_answer', 'correct_answee'] if c in df.columns), None)
                        for idx, user_choice in st.session_state.user_answers.items():
                            actual_correct = str(quiz_df.iloc[idx][c_col]).strip().upper()
                            if str(user_choice).strip().upper() == actual_correct:
                                score += 1
                        
                        supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}, on_conflict="name").execute()
                        st.session_state.final_score = score
                        st.session_state.exam_finished = True
                        del st.session_state['exam_active']
                        st.rerun()

            # --- EXPLANATION TAB (Show after submission) ---
            if 'exam_finished' in st.session_state:
                st.success(f"Final Score: {st.session_state.final_score}")
                with st.expander("🔍 View Explanations for all questions"):
                    for i in range(len(quiz_df)):
                        row = quiz_df.iloc[i]
                        st.write(f"**Q{i+1}:** {row['question']}")
                        st.write(f"✅ Correct Answer: {row['correct_answer']}")
                        if 'explanation' in row: st.write(f"💡 *Explanation:* {row['explanation']}")
                        st.divider()
                if st.button("Restart"): st.session_state.clear(); st.rerun()

    with t2:
        st.subheader("🏆 Leaderboard")
        res = supabase.table("leaderboard").select("*").execute()
        if res.data: st.table(clean_lb(res.data).head(10))

st.markdown("<div class='created-by'>Created by Ufford I.I. VikidylEdu Centre © 2026</div>", unsafe_allow_html=True)
