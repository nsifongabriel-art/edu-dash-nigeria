import streamlit as st

# ... (keep your existing title and selectbox code) ...

st.subheader("Daily Progress 🎯")

# Let's simulate the progress
done = 15
goal = 30
percentage = done / goal

# Display the bar
st.progress(percentage)
st.write(f"You've completed {done} out of {goal} questions today!")
