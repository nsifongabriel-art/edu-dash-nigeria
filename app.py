import streamlit as st
import pandas as pd
import random
from supabase import create_client, Client

# --- 1. CONNECT TO SUPABASE ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# --- 2. YOUR GOOGLE SHEET LINK (CORRECTED) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10) # Refreshes every 10 seconds so you see changes fast
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Edu-Dash Nigeria", page_icon="🇳🇬")
st.title("🇳🇬 Edu-Dash Success Package")

# Sidebar for Login
with st.sidebar:
    st.header("Student Portal")
    name = st.text_input("Full Name:", placeholder="Enter your name")
    
    # IMPORTANT: These must match your Sheet exactly
    exam_list = ["BESE", "WAEC", "JAMB"]
    subject_list = ["Mathematics", "English", "Biology"]
    
    sel_exam = st.selectbox("Select Exam:", exam_list)
    sel_subject = st.selectbox("Select Subject:", subject_list)
    
    if 'score' not in st.session_state: st.session_state.score = 0
    st.divider()
    st.metric("Your Total Score", st.session_state.score)

# --- 4. FILTERING LOGIC ---
if df.empty:
    st.error("Wait! The app can't read your Google Sheet. Make sure it is 'Published to Web' as a CSV.")
elif not name:
    st.info("👈 Please enter your name in the sidebar to start the quiz!")
else:
    # Filter by Exam and Subject
    quiz_df = df[(df['Exam'] == sel_exam) & (df['Subject'] == sel_subject)]

    if quiz_df.empty:
        st.warning(f"No questions found for {sel_exam} - {sel_subject}. Check your Google Sheet spelling!")
        st.write("Current Sheet Headers:", list(df.columns)) # Helps us debug
    else:
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        
        # Ensure index stays within range
        if st.session_state.q_idx >= len(quiz_df):
            st.session_state.q_idx = 0
            
        q = quiz_df.iloc[st.session_state.q_idx]
        
        st.write(f"### Question: {q['Question']}")
        
        # Options
        opts = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
        ans = st.radio("Select the correct answer:", opts, key=f"q_{st.session_state.q_idx}")

        if st.button("Submit Answer"):
            if str(ans) == str(q['Correct_Answer']):
                st.success("Correct! Well done. 🎯")
                st.session_state.score += 1
                # SAVE TO LEADERBOARD
                try:
                    supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
                except:
                    pass
            else:
                st.error(f"Incorrect. The right answer is: {q['Correct_Answer']}")
                if pd.notna(q.get('Explanation')):
                    st.info(f"💡 {q['Explanation']}")

        if st.button("Next Question ➡️"):
            st.session_state.q_idx = random.randint(0, len(quiz_df)-1)
            st.rerun()

# --- 5. LEADERBOARD ---
st.divider()
st.subheader("🏆 National Leaderboard")
try:
    res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(5).execute()
    if res.data:
        st.table(pd.DataFrame(res.data))
    else:
        st.write("First student to score gets the #1 spot!")
except:
    st.write("Leaderboard loading...")
