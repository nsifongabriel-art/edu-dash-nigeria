import streamlit as st

# The Title of your app
st.title("🇳🇬 Edu-Dash Nigeria")

# A simple welcome message
st.write("Welcome to the Success Package for JSS3 and SSS3 students.")

# A selector to simulate the "Exam Type"
exam = st.selectbox("Select Exam Focus:", ["BECE", "WAEC", "NECO", "JAMB"])

st.write(f"You are currently viewing the {exam} preparation dashboard.")
