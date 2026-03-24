import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# Your verified Google Sheet CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        if data is not None:
            # Clean headers: remove spaces and lowercase everything
            data.columns = [str(c).strip().lower() for c in data.columns]
            return data
    except:
        return None
    return None

df = load_data()

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    st.divider()
    if df is not None:
        st.success("✅ System Connected")
    else:
        st.warning("⏳ System Loading...")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    # If exam hasn't started and no final score is shown
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        
        if df is not None and 'subject' in df.columns:
            name = st.text_input("Full Name")
            school = st.text_input("School")
            
            # FIX: Merge duplicate 'Mathematics' and sort
            raw_subs = df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist()
            subs = sorted(raw_subs)
            
            c1, c2 = st.columns(2)
            with c1:
                subject = st.selectbox("Select Subject", subs)
            with c2:
                exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
                
            if st.button("🚀 START EXAM"):
                if name and school:
                    # Filter questions based on selection
                    filt = (df['subject'].str.title() == subject) & (df['exam'].str.upper() == exam_type)
                    q_df = df[filt]
                    
                    if not q_df.empty:
                        # Pick 10 random questions
                        st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 10)).reset_index(drop=True)
                        st.session_state.update({
                            "exam_active": True, 
                            "current_q": 0, 
                            "user_answers": {}, 
                            "student_info": f"{school} | {name} | {subject}"
                        })
                        st.rerun()
                    else:
                        st.warning(f"No questions found for {subject} in {exam_type}.")
                else:
                    st.error("Please fill in your name and school.")
        else:
            st.info("🔄 Loading database...")

    # THE EXAM ENGINE
    elif 'exam_active' in st.session_state:
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        row = q_df.iloc[curr]
        
        st.subheader(f"Question {curr + 1} of {len(q_df)}")
        st.write(row['question'])
        
        # Display Options
        options = [row['a'], row['b'], row['c'], row['d']]
        choice = st.radio("Choose your answer:", options, key=f"q_{curr}")
        st.session_state.user_answers[curr] = choice

        col1, col2 = st.columns(2)
        with col1:
            if curr > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.current_q -= 1
                    st.rerun()
        with col2:
            if curr < len(q_df) - 1:
                if st.button("Next ➡️"):
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                if st.button("🏁 FINISH & SUBMIT"):
                    # Calculate Score
                    score = 0
                    for i, r in q_df.iterrows():
                        if st.session_state.user_answers.get(i) == r['correct_answer']:
                            score += 1
                    
                    # Save to Supabase Leaderboard
                    supabase.
