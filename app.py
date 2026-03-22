import streamlit as st
import pandas as pd
import time
import json
import plotly.express as px
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

MASTER_SUBJECTS = ["MATHEMATICS", "ENGLISH LANGUAGE", "BIOLOGY", "PHYSICS", "CHEMISTRY", "ECONOMICS", "GOVERNMENT", "LITERATURE", "CIVIC EDUCATION", "COMMERCE", "AGRIC SCIENCE", "GEOGRAPHY", "CRS", "IRS", "HISTORY", "COMPUTER STUDIES"]

@st.cache_data(ttl=1)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. UI STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 5px; }
    .passage-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; height: 450px; overflow-y: auto; font-size: 18px; line-height: 1.6; border: 1px solid #d1d5db; }
    .question-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #1E3A8A; font-size: 20px; border: 1px solid #e5e7eb; color: #000; }
</style>""", unsafe_allow_html=True)

# --- 3. SIDEBAR & LEADERBOARD ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=50)
    st.title("VikidylEdu")
    
    # --- WALL OF FAME LOGIC ---
    st.markdown("### 🏆 Wall of Fame (Top 3)")
    try:
        res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        if res.data:
            icons = ["🥇", "🥈", "🥉"]
            for i, entry in enumerate(res.data):
                # Clean name for display (extract student name from name|school|subj string)
                display_name = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
                st.markdown(f"<div class='winner-box'>{icons[i]} {display_name}: {entry['score']} pts</div>", unsafe_allow_html=True)
    except:
        st.caption("Leaderboard loading...")

    st.divider()
    role = st.selectbox("Select Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("CBT Hall")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School Name:")
        with c2: name = st.text_input("Student Full Name:")
        
        y_col, e_col, s_col = st.columns(3)
        available_years = ["ALL YEARS (Mixed)"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True) if not df.empty else ["2024"]
        with y_col: year_choice = st.selectbox("Year", available_years)
        with e_col: exam_type = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", MASTER_SUBJECTS)
        
        if st.button("🚀 BEGIN EXAM") and school and name:
            filt = (df['subject'].str.upper() == subj) & (df['exam'].str.upper() == exam_type)
            if year_choice != "ALL YEARS (Mixed)": filt &= (df['year'].astype(str) == year_choice)
            quiz_df = df[filt]
            
            if not quiz_df.empty:
                st.session_state.quiz_data = quiz_df.sample(n=min(len(quiz_df), 20)).reset_index(drop=True)
                st.session_state.exam_active, st.session_state.start_time, st.session_state.current_q = True, time.time(), 0
                st.session_state.user_answers = {}
                st.session_state.db_id = f"{school} | {name} | {subj} | {year_choice}"
                st.rerun()
            else: st.warning(f"🚧 No questions found for {subj} {year_choice}.")
    else:
        # EXAM VIEW (Includes Passage Support)
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        q = q_df.iloc[curr]
        
        if 'passage' in q_df.columns and pd.notnull(q['passage']):
            col1, col2 = st.columns([1, 1])
            with col1: st.markdown(f"<div class='passage-box'>{q['passage']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
                st.session_state.user_answers[curr] = st.radio("Select:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")
        else:
            st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
            st.session_state.user_answers[curr] = st.radio("Select:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")

        # Navigation & Submit logic remains same as previous working version...
        if st.button("🏁 FINISH"):
            # Grading logic...
            st.session_state.clear()
            st.rerun()

# --- 5. TEACHER SUITE ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        st.subheader("Diagnostic Analytics")
        # Pull data from Supabase
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            # Create the Subject Analytics chart
            # ... (Chart logic from previous step)
