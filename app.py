import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame()

df = load_data()

st.set_page_config(page_title="Edu-Dash Nigeria", page_icon="🇳🇬", layout="wide")

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🇳🇬 Edu-Dash")
    role = st.radio("Access Level:", ["✍️ Student", "👨‍👩‍👧 Parent", "👨‍🏫 Teacher"])
    st.divider()

# --- 3. STUDENT VIEW ---
if role == "✍️ Student":
    tab1, tab2 = st.tabs(["📝 Take Exam", "📚 Study Materials"])
    
    with tab1:
        st.header("Exam Practice Portal")
        name = st.text_input("Full Name:", key="std_name")
        sel_exam = st.selectbox("Exam:", ["BECE", "WAEC", "JAMB"])
        sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
        
        if st.button("🚀 Start Exam"):
            st.session_state.exam_start = time.time()
            st.session_state.score = 0
            st.session_state.q_idx = 0

        if name and 'exam_start' in st.session_state:
            # Quiz Logic
            quiz_df = df[(df['Exam'].astype(str).str.upper().isin(['BECE', 'BESE'])) & (df['Subject'] == sel_subj)]
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.subheader(f"Question {st.session_state.q_idx + 1}")
                st.write(q['Question'])
                ans = st.radio("Select Answer:", [q['A'], q['B'], q['C'], q['D']], key=f"q_{st.session_state.q_idx}")
                
                if st.button("Submit"):
                    col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                    if str(ans).strip() == str(q[col]).strip():
                        st.success("Correct! 🎉")
                        st.session_state.score += 1
                        supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
                    else:
                        st.error(f"Wrong. Answer: {q[col]}")
                        if 'Explanation' in q and pd.notna(q['Explanation']):
                            st.info(f"💡 Explanation: {q['Explanation']}")
                
                if st.button("Next ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()

    with tab2:
        st.header("Digital Library")
        st.write("Download notes and past questions below:")
        # You can add real links to your Google Drive here
        materials = {
            "Mathematics": "https://google.com/search?q=WAEC+Maths+Notes",
            "English": "https://google.com/search?q=BECE+English+Past+Questions",
            "Biology": "https://google.com/search?q=JAMB+Biology+Syllabus"
        }
        for sub, link in materials.items():
            st.link_button(f"📖 Download {sub} Study Guide", link)

# --- 4. PARENT VIEW ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Parental Monitoring Dashboard")
    search_name = st.text_input("Enter Child's Full Name:")
    if search_name:
        res = supabase.table("leaderboard").select("*").eq("name", search_name).execute()
        if res.data:
            st.metric(label=f"Current Progress", value=f"{res.data[0]['score']} Points")
            st.success("✅ Student is active.")
        else: st.error("No records found.")

# --- 5. TEACHER VIEW ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher's Admin Dashboard")
    
    # Leaderboard Check
    st.subheader("📊 Class Performance")
    try:
        res = supabase.table("leaderboard").select("name, score").order("score", desc=True).execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
    except: st.write("Updating scores...")

    # Question Management Instructions
    st.divider()
    st.subheader("⚙️ Manage Questions")
    st.info("To add more questions, simply update your Google Sheet. The app will refresh automatically!")

st.divider()
st.caption("Edu-Dash Nigeria © 2026")
