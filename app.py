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
    role = st.radio("Access Level:", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])
    st.divider()
    
    if role == "👨‍🏫 Teacher":
        pwd = st.text_input("School Admin Password:", type="password")
        if pwd != "Lagos2026": 
            st.error("🔒 Unauthorized access.")
            st.stop()

# --- 3. STUDENT VIEW ---
if role == "✍️ Student":
    tab1, tab2 = st.tabs(["📝 Practice Quiz", "📚 Study Materials"])
    
    with tab1:
        st.header("Practice Portal")
        school = st.text_input("Your School Name:", placeholder="e.g. Bright Minds Academy")
        name = st.text_input("Student Full Name:", placeholder="e.g. Gabriel Okon")
        
        col1, col2 = st.columns(2)
        with col1: sel_exam = st.selectbox("Exam:", ["BECE", "NECO", "WAEC", "JAMB"])
        with col2: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
        
        if st.button("🚀 Start Exam"):
            if not school or not name:
                st.error("Please enter both School and Name to track your progress!")
            else:
                st.session_state.exam_start = time.time()
                st.session_state.score = 0
                st.session_state.q_idx = 0

        if 'exam_start' in st.session_state:
            # Quiz logic
            quiz_df = df[(df['Exam'].astype(str).str.upper().isin(['BECE', 'BESE', 'NECO'])) & (df['Subject'] == sel_subj)]
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.subheader(f"Question {st.session_state.q_idx + 1}")
                st.write(f"**{q['Question']}**")
                ans = st.radio("Select Answer:", [q['A'], q['B'], q['C'], q['D']], key=f"q_{st.session_state.q_idx}")
                
                if st.button("Submit Answer"):
                    col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                    if str(ans).strip() == str(q[col]).strip():
                        st.success("Correct! 🎉")
                        st.session_state.score += 1
                        # Unique ID for Database: School_Name_Subject
                        db_id = f"{school} | {name} | {sel_subj}"
                        supabase.table("leaderboard").upsert({"name": db_id, "score": st.session_state.score}, on_conflict="name").execute()
                    else:
                        st.error(f"Wrong. The answer was {q[col]}")
                
                if st.button("Next Question ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()

    # National Leaderboard
    st.divider()
    st.subheader("🏆 National Top Performers")
    try:
        res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(10).execute()
        if res.data:
            lead_df = pd.DataFrame(res.data)
            # Split the ID to show just the student name
            lead_df['Student'] = lead_df['name'].apply(lambda x: x.split('|')[1] if '|' in x else x)
            lead_df['School'] = lead_df['name'].apply(lambda x: x.split('|')[0] if '|' in x else "General")
            st.table(lead_df[['Student', 'School', 'score']])
    except: st.write("Refreshing leaderboard...")

# --- 4. TEACHER VIEW ---
elif role == "👨‍🏫 Teacher":
    st.header("School Administration")
    res = supabase.table("leaderboard").select("*").execute()
    if res.data:
        full_df = pd.DataFrame(res.data)
        # Create columns for School, Student, and Subject
        full_df['School'] = full_df['name'].apply(lambda x: x.split('|')[0].strip() if '|' in x else "Unknown")
        full_df['Student'] = full_df['name'].apply(lambda x: x.split('|')[1].strip() if '|' in x else x)
        full_df['Subject'] = full_df['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "General")

        schools_list = full_df['School'].unique()
        selected_school = st.selectbox("Select School to view grades:", schools_list)
        
        filtered_df = full_df[full_df['School'] == selected_school]
        st.write(f"### Results for {selected_school}")
        st.dataframe(filtered_df[['Student', 'Subject', 'score']], use_container_width=True)
        st.download_button("📥 Download School Result Sheet", filtered_df.to_csv(), f"{selected_school}_results.csv")

# --- 5. PARENT VIEW ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Student Progress Tracker")
    p_school = st.text_input("Enter School Name:")
    p_child = st.text_input("Enter Child's Full Name:")
    
    if p_school and p_child:
        search_term = f"{p_school} | {p_child}%"
        res = supabase.table("leaderboard").select("*").ilike("name", search_term).execute()
        if res.data:
            st.success(f"Report for {p_child} at {p_school}:")
            for item in res.data:
                subj = item['name'].split('|')[-1].strip()
                score = item['score']
                status = "🌟 Great Work!" if score >= 5 else "⚠️ Needs more practice"
                st.info(f"**{subj}**: {score} Points - {status}")
        else:
            st.error("No data found. Please check spelling or school name.")

st.divider()
st.caption("Edu-Dash Nigeria © 2026")
