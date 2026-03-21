import streamlit as st
import pandas as pd
import random

# 1. Database Connection (Link fixed to CSV format)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data
def load_questions():
    try:
        # We add on_bad_lines to skip empty rows if they exist
        data = pd.read_csv(SHEET_URL, on_bad_lines='skip')
        return data
    except Exception as e:
        st.error(f"Error loading sheet: {e}")
        return pd.DataFrame(columns=["Exam", "Subject", "Question", "A", "B", "C", "D", "Correct_Answer", "Explanation"])

df = load_questions()

# 2. Interface & Sidebar
st.title("🇳🇬 Edu-Dash Nigeria")

with st.sidebar:
    st.header("Student Portal")
    # I changed "BECE" to "BESE" to match your screenshot exactly!
    sel_exam = st.selectbox("Select Exam:", ["BESE", "WAEC", "NECO", "JAMB"])
    sel_subject = st.selectbox("Select Subject:", ["Mathematics", "English", "Biology"])

# 3. Filtering Logic
quiz_data = df[(df['Exam'] == sel_exam) & (df['Subject'] == sel_subject)]

if quiz_data.empty:
    st.warning(f"Waiting for data... Make sure your Google Sheet has 'Exam' as {sel_exam} and 'Subject' as {sel_subject}.")
    st.info("Check that your Column Headers match: Exam, Subject, Question, A, B, C, D, Correct_Answer, Explanation")
else:
    # 4. Quiz Logic
    if 'q_idx' not in st.session_state:
        st.session_state.q_idx = 0
    
    # Ensure index is within range
    if st.session_state.q_idx >= len(quiz_data):
        st.session_state.q_idx = 0

    q_row = quiz_data.iloc[st.session_state.q_idx]
    
    st.subheader(f"Practice: {sel_subject}")
    
    # Display the Question
    st.write(f"**{q_row['Question']}**")
    
    # Options
    options = [str(q_row['A']), str(q_row['B']), str(q_row['C']), str(q_row['D'])]
    user_choice = st.radio("Choose the correct answer:", options, key=f"q_{st.session_state.q_idx}")

    if st.button("Submit Answer"):
        # Check if user choice matches the text in Correct_Answer column
        if str(user_choice) == str(q_row['Correct_Answer']):
            st.success("Correct! ✅")
            st.balloons()
        else:
            st.error(f"Incorrect. ❌ The right answer was: {q_row['Correct_Answer']}")
            if 'Explanation' in q_row and pd.notna(q_row['Explanation']):
                st.info(f"💡 Explanation: {q_row['Explanation']}")
    
    # Button to shuffle to a new question
    if st.button("Next Question ➡️"):
        st.session_state.q_idx = random.randint(0, len(quiz_data) - 1)
        st.rerun()
