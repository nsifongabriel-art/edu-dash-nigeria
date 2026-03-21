import streamlit as st
import pandas as pd
import random
import time
from supabase import create_client, Client

# --- 1. CONNECT TO SUPABASE ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# --- 2. GOOGLE SHEET LINK ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10)
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame()

df = load_data()

st.set_page_config(page_title="Edu-Dash Nigeria", page_icon="🇳🇬")
st.title("🇳🇬 Edu-Dash Success Package")

# --- 3. SESSION STATE FOR GLOBAL TIMER ---
# Total time for the whole exam (e.g., 30 minutes = 1800 seconds)
EXAM_LIMIT_SECONDS = 30 * 60 

if 'exam_start_time' not in st.session_state:
    st.session_state.exam_start_time = None

with st.sidebar:
    st.header("Student Portal")
    name = st.text_input("Full Name:", placeholder="Enter name")
    sel_exam = st.selectbox("Select Exam:", ["BECE", "WAEC", "JAMB"]) # Fixed BECE
    sel_subject = st.selectbox("Select Subject:", ["Mathematics", "English", "Biology"])
    
    if st.button("Start Exam"):
        st.session_state.exam_start_time = time.time()
        st.session_state.score = 0
        st.session_state.q_idx = 0
        st.rerun()

    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("Total Points", st.session_state.score)

# --- 4. EXAM LOGIC ---
if df.empty:
    st.error("Cannot read Google Sheet.")
elif not name:
    st.info("👈 Enter your name and click 'Start Exam' to begin!")
elif st.session_state.exam_start_time is None:
    st.warning("Click 'Start Exam' in the sidebar to begin your timed session.")
else:
    # Check Remaining Time
    elapsed = time.time() - st.session_state.exam_start_time
    remaining = max(0, int(EXAM_LIMIT_SECONDS - elapsed))
    
    if remaining > 0:
        mins, secs = divmod(remaining, 60)
        st.sidebar.subheader(f"⏳ Time Left: {mins:02d}:{secs:02d}")
        # Refresh every minute to update sidebar timer (or more often if you prefer)
    else:
        st.error("🚨 EXAM TIME OVER! Your final score has been recorded.")
        st.stop()

    # Filter Questions (Handles BECE/BESE automatically)
    quiz_df = df[
        (df['Exam'].astype(str).str.strip().str.upper().isin(['BECE', 'BESE'])) & 
        (df['Subject'].astype(str).str.strip() == sel_subject)
    ]

    if quiz_df.empty:
        st.warning(f"No questions found for {sel_exam} {sel_subject}.")
    else:
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
        
        st.write(f"### Question {st.session_state.q_idx + 1}")
        st.write(f"**{q['Question']}**")
        
        opts = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
        ans = st.radio("Select answer:", opts, key=f"q_{st.session_state.q_idx}")

        if st.button("Submit Answer"):
            # Check for column name: Correct_Answee or Correct_Answer
            correct_col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
            
            if str(ans).strip() == str(q[correct_col]).strip():
                st.success("Correct! 🎉")
                st.session_state.score += 1
                try:
                    supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
                except: pass
            else:
                st.error(f"Wrong. The correct answer was: {q[correct_col]}")

        if st.button("Next Question ➡️"):
            st.session_state.q_idx += 1
            st.rerun()

# --- LEADERBOARD ---
st.divider()
st.subheader("🏆 National Leaderboard")
try:
    res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(5).execute()
    if res.data: st.table(pd.DataFrame(res.data))
except: st.write("Loading leaderboard...")
