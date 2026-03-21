import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame()

df = load_data()

st.set_page_config(page_title="Edu-Dash Nigeria", page_icon="🇳🇬")
st.title("🇳🇬 Edu-Dash Success Package")

# Exam Duration: 30 Minutes
TOTAL_TIME = 30 * 60

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Student Portal")
    name = st.text_input("Enter Full Name:")
    sel_exam = st.selectbox("Select Exam:", ["BECE", "WAEC", "JAMB"])
    sel_subject = st.selectbox("Select Subject:", ["Mathematics", "English", "Biology"])
    
    if st.button("🚀 Start Timed Exam"):
        st.session_state.exam_start = time.time()
        st.session_state.score = 0
        st.session_state.q_idx = 0
        st.rerun()

    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("Your Points", st.session_state.score)

# --- 3. EXAM LOGIC ---
if not name:
    st.info("👈 Enter your name and click 'Start Timed Exam'!")
elif 'exam_start' not in st.session_state:
    st.warning("👈 Click 'Start Timed Exam' to begin!")
else:
    elapsed = time.time() - st.session_state.exam_start
    remaining = max(0, int(TOTAL_TIME - elapsed))
    
    if remaining > 0:
        st.sidebar.subheader(f"⏳ Time: {remaining//60:02d}:{remaining%60:02d}")
    else:
        st.error("🚨 Time is up!")
        st.stop()

    quiz_df = df[(df['Exam'].astype(str).str.strip().str.upper() == sel_exam) & 
                 (df['Subject'].astype(str).str.strip() == sel_subject)]

    if quiz_df.empty:
        st.warning(f"No questions found for {sel_exam} {sel_subject}.")
    else:
        q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
        st.write(f"### Question {st.session_state.q_idx + 1}")
        st.write(f"**{q['Question']}**")
        
        ans = st.radio("Choose answer:", [q['A'], q['B'], q['C'], q['D']], key=st.session_state.q_idx)
        
        if st.button("Submit Answer"):
            col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
            if str(ans).strip() == str(q[col]).strip():
                st.success("Correct! 🎉")
                st.session_state.score += 1
                try:
                    # UPDATED SAVE: No 'id' required
                    supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
                except Exception as e:
                    st.error(f"Save Error: {e}")
            else:
                st.error(f"Wrong. Answer was: {q[col]}")

        if st.button("Next Question ➡️"):
            st.session_state.q_idx += 1
            st.rerun()

# --- 4. LEADERBOARD ---
st.divider()
st.subheader("🏆 National Leaderboard")
try:
    res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(5).execute()
    if res.data:
        st.table(pd.DataFrame(res.data))
except:
    st.write("Leaderboard updating...")
