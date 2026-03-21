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

# --- 3. SESSION STATE FOR TIMER ---
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

with st.sidebar:
    st.header("Student Portal")
    name = st.text_input("Full Name:", placeholder="Enter name")
    sel_exam = st.selectbox("Select Exam:", ["BESE", "WAEC", "JAMB"])
    sel_subject = st.selectbox("Select Subject:", ["Mathematics", "English", "Biology"])
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("Your Score", st.session_state.score)

if df.empty:
    st.error("Cannot read Google Sheet.")
elif not name:
    st.info("👈 Enter your name in the sidebar!")
else:
    quiz_df = df[(df['Exam'].astype(str).str.strip() == sel_exam) & 
                 (df['Subject'].astype(str).str.strip() == sel_subject)]

    if quiz_df.empty:
        st.warning(f"No questions found for {sel_exam} {sel_subject}.")
    else:
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
        
        # --- TIMER LOGIC ---
        limit = 30 # 30 seconds per question
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, int(limit - elapsed))
        
        if remaining > 0:
            st.warning(f"⏳ Time Remaining: {remaining} seconds")
            # Auto-refresh to update timer
            if remaining > 1:
                time.sleep(1)
                st.rerun()
        else:
            st.error("⏰ Time is up for this question!")

        st.write(f"### {q['Question']}")
        opts = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
        
        # Disable radio if time is up
        ans = st.radio("Select answer:", opts, key=f"q_{st.session_state.q_idx}", disabled=(remaining == 0))

        if st.button("Submit Answer", disabled=(remaining == 0)):
            if str(ans).strip() == str(q['Correct_Answee']).strip():
                st.success("Correct! 🎉")
                st.session_state.score += 1
                try:
                    supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
                except: pass
            else:
                st.error(f"Wrong. Answer was: {q['Correct_Answee']}")

        if st.button("Next Question ➡️"):
            st.session_state.q_idx += 1
            st.session_state.start_time = time.time() # Reset timer for next question
            st.rerun()

# --- LEADERBOARD ---
st.divider()
st.subheader("🏆 National Leaderboard")
try:
    res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(5).execute()
    if res.data: st.table(pd.DataFrame(res.data))
except: st.write("Loading leaderboard...")
