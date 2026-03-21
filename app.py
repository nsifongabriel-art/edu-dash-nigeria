import streamlit as st
import pandas as pd
import random
from supabase import create_client, Client

# --- 1. CONNECT TO SUPABASE ---
# These are the keys you found!
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# --- 2. CONNECT TO GOOGLE SHEETS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"Sheet Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. APP LOGIC ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0

st.title("🇳🇬 Edu-Dash Success Package")

with st.sidebar:
    st.header("Student Login")
    name = st.text_input("Full Name:", placeholder="e.g. Gabriel Nsifon")
    exam = st.selectbox("Select Exam:", ["BECE", "WAEC", "JAMB"])
    subject = st.selectbox("Select Subject:", ["Mathematics", "English", "Biology"])
    st.divider()
    st.metric("Your Points", st.session_state.score)

# Filter Questions
if not df.empty:
    questions = df[(df['Exam'] == exam) & (df['Subject'] == subject)]
else:
    questions = pd.DataFrame()

if questions.empty:
    st.info("No questions found. Check your Google Sheet names (Exam/Subject)!")
elif not name:
    st.warning("Please enter your name in the sidebar to start.")
else:
    q = questions.iloc[st.session_state.q_idx]
    st.subheader(f"Question {st.session_state.q_idx + 1}")
    st.write(f"### {q['Question']}")
    
    options = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
    user_choice = st.radio("Pick the correct one:", options, key=f"q_{st.session_state.q_idx}")
    
    if st.button("Submit Answer"):
        if str(user_choice) == str(q['Correct_Answer']):
            st.success("Correct! 🎉 +1 Point")
            st.session_state.score += 1
            # SAVE TO SUPABASE
            try:
                supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
            except:
                pass # If it fails, we keep going
        else:
            st.error(f"Incorrect. The answer is {q['Correct_Answer']}")

    if st.button("Next Question ➡️"):
        st.session_state.q_idx = random.randint(0, len(questions)-1)
        st.rerun()

# --- 4. NATIONAL LEADERBOARD ---
st.divider()
st.subheader("🏆 National Leaderboard")
try:
    res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(5).execute()
    if res.data:
        st.table(pd.DataFrame(res.data))
    else:
        st.write("First student to score gets the #1 spot!")
except:
    st.write("Leaderboard coming soon...")
