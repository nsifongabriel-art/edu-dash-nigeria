import streamlit as st
import time

# 1. Setup and Title
st.set_page_config(page_title="Edu-Dash Nigeria", page_icon="🇳🇬")
st.title("🇳🇬 Edu-Dash Nigeria")

# 2. Sidebar / Navigation
with st.sidebar:
    st.header("Student Profile")
    st.write("Hello, Chidi! 👋")
    st.info("🥇 Badge: Daily Champion")
    exam = st.selectbox("Change Exam Focus:", ["BECE", "WAEC", "NECO", "JAMB"])

# 3. Main Dashboard Progress
st.subheader(f"{exam} Preparation Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Daily Goal", value="25/30", delta="5 more to go!")

with col2:
    st.metric(label="Class Rank", value="#12", delta="Up 4 spots")

# Progress Bar Logic
done = 25 
goal = 30
percentage = done / goal
st.progress(percentage)

if done >= goal:
    st.success("Daily Goal Reached! 🌟")
    st.balloons()

# 4. Practice Session
st.divider()
st.subheader("Interactive Practice 📝")

# Question Data
questions = [
    {
        "question": "What is the value of x if 2x + 5 = 15?",
        "options": ["5", "10", "15", "20"],
        "answer": "5",
        "explanation": "Subtract 5 from both sides: 2x = 10. Then divide by 2: x = 5."
    }
]

# Timed Challenge
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

elapsed = int(time.time() - st.session_state.start_time)
remaining = max(0, 60 - elapsed)
st.write(f"⏳ Time Remaining: {remaining} seconds")

# Question Display
q = questions[0]
user_choice = st.radio(q["question"], q["options"])

if st.button("Submit Answer"):
    if user_choice == q["answer"]:
        st.success("Correct! ✅")
    else:
        st.error(f"Incorrect. ❌ The correct answer was {q['answer']}.")
        st.info(f"💡 Explanation: {q['explanation']}")
