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

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🇳🇬 Edu-Dash")
    role = st.radio("Who is using the app?", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])
    st.divider()
    if role == "👨‍🏫 Teacher":
        pwd = st.text_input("Teacher Password:", type="password")
        if pwd != "Lagos2026": # You can change this password!
            st.warning("Please enter the correct password to access Teacher tools.")
            st.stop()

# --- 3. STUDENT VIEW ---
if role == "✍️ Student":
    tab1, tab2 = st.tabs(["📝 Practice Quiz", "📚 Study Materials"])
    
    with tab1:
        st.header("National Practice Portal")
        name = st.text_input("Student Name:", placeholder="Type your full name")
        col1, col2 = st.columns(2)
        with col1: sel_exam = st.selectbox("Exam:", ["BECE", "WAEC", "JAMB"])
        with col2: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
        
        if st.button("🚀 Start Exam"):
            st.session_state.exam_start = time.time()
            st.session_state.score = 0
            st.session_state.q_idx = 0

        if name and 'exam_start' in st.session_state:
            # Exam Logic
            quiz_df = df[(df['Exam'].astype(str).str.upper().isin(['BECE', 'BESE'])) & (df['Subject'] == sel_subj)]
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.subheader(f"Question {st.session_state.q_idx + 1}")
                st.write(q['Question'])
                ans = st.radio("Choose:", [q['A'], q['B'], q['C'], q['D']], key=f"std_{st.session_state.q_idx}")
                
                if st.button("Submit Answer"):
                    col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                    if str(ans).strip() == str(q[col]).strip():
                        st.success("Correct! 🎉")
                        st.session_state.score += 1
                        supabase.table("leaderboard").upsert({"name": name, "score": st.session_state.score}, on_conflict="name").execute()
                    else: st.error(f"Wrong! Answer: {q[col]}")
                
                if st.button("Next Question ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()

        # LEADERBOARD (Back for Students!)
        st.divider()
        st.subheader("🏆 National Leaderboard")
        try:
            res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(10).execute()
            if res.data: st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        except: st.write("Updating scores...")

    with tab2:
        st.header("Study Materials")
        st.info("Find links to notes and PDFs below:")
        # This part reads from your Google sheet if you add a 'Link' column there
        st.write("📖 [Mathematics BECE Guide](https://google.com)") 
        st.write("📖 [English Grammar Notes](https://google.com)")

# --- 4. TEACHER VIEW ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher Dashboard")
    
    # 1. Score Management
    st.subheader("📊 Class Results")
    res = supabase.table("leaderboard").select("name, score").order("score", desc=True).execute()
    if res.data:
        t_df = pd.DataFrame(res.data)
        st.dataframe(t_df, use_container_width=True)
        st.download_button("Download Scores", t_df.to_csv(), "results.csv")

    # 2. Material Upload Instruction
    st.divider()
    st.subheader("📤 Upload Materials")
    st.write("To add new PDFs or notes for students:")
    st.write("1. Upload file to Google Drive.")
    st.write("2. Copy the 'Share' link.")
    st.write("3. Paste it into your Google Sheet under a new 'Materials' column.")

# --- 5. PARENT VIEW ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Parental Portal")
    child = st.text_input("Enter Child's Full Name:")
    if child:
        res = supabase.table("leaderboard").select("*").eq("name", child).execute()
        if res.data:
            st.metric("Exam Points", f"{res.data[0]['score']}")
            st.success("Your child is progressing well! ✅")
        else: st.error("No data found for this name.")

st.divider()
st.caption("Edu-Dash Nigeria © 2026")
