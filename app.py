import streamlit as st
import pandas as pd
import random

# 1. Database Connection
# Replace the URL below with your "Published as CSV" link from Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7.../pub?output=csv"

@st.cache_data
def load_questions():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        # Fallback if the sheet isn't linked yet
        return pd.DataFrame(columns=["Exam", "Subject", "Question", "A", "B", "C", "D", "Correct_Answer", "Explanation"])

df = load_questions()

# 2. Interface & Sidebar
st.title("🇳🇬 Edu-Dash Nigeria")

with st.sidebar:
    st.header("Student Portal")
    sel_exam = st.selectbox("Select Exam:", ["BECE", "WAEC", "NECO", "JAMB"])
    sel_subject = st.selectbox("Select Subject:", ["Mathematics", "English", "Biology"])

# 3. Filtering Logic
# This picks only the rows that match the user's selection
quiz_data = df[(df['Exam'] == sel_exam) & (df['Subject'] == sel_subject)]

if quiz_data.empty:
    st.warning(f"No questions found for {sel_exam} {sel_subject} yet. Add some to your Google Sheet!")
else:
    # 4. Quiz Logic
    # We pick one random question from the filtered list
    if 'q_idx' not in st.session_state:
        st.session_state.q_idx = random.randint(0, len(quiz_data) - 1)
    
    q_row = quiz_data.iloc[st.session_state.q_idx]
    
    st.subheader(f"Practice: {sel_subject}")
    options = [q_row['A'], q_row['B'], q_row['C'], q_row['D']]
    user_choice = st.radio(q_row['Question'], options)

    if st.button("Submit Answer"):
        if user_choice == q_row['Correct_Answer']:
            st.success("Correct! ✅")
            st.balloons()
        else:
            st.error(f"Incorrect. ❌ The right answer was: {q_row['Correct_Answer']}")
            st.info(f"💡 Explanation: {q_row['Explanation']}")
        
        # Button to load a new question
        if st.button("Next Question ➡️"):
            st.session_state.q_idx = random.randint(0, len(quiz_data) - 1)
            st.rerun()
