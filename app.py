import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. DATABASE SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame()

df = load_data()

# --- 2. UI CONFIGURATION ---
st.set_page_config(page_title="Edu-Dash | VikidylEdu", page_icon="🇳🇬", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #1E3A8A; color: white; font-weight: bold; border: 2px solid #FFD700; }
    .created-by { text-align: center; color: #1E3A8A; padding: 25px; font-weight: bold; font-size: 1.2em; border-top: 3px double #EEE; margin-top: 50px;}
    .leaderboard-box { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #ddd; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Helper function to clean leaderboard names
def get_clean_leaderboard(res_data):
    if not res_data: return pd.DataFrame()
    ld_df = pd.DataFrame(res_data)
    # Splits "School | Name | Subject" into columns
    ld_df['School'] = ld_df['name'].apply(lambda x: x.split('|')[0].strip() if '|' in x else "General")
    ld_df['Student'] = ld_df['name'].apply(lambda x: x.split('|')[1].strip() if '|' in x else x)
    return ld_df[['Student', 'School', 'score']]

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=70)
    st.title("VikidylEdu Portal")
    role = st.selectbox("Navigation Menu", ["✍️ Student Portal", "👨‍🏫 Teacher Suite", "👨‍👩‍👧 Parent Center"])
    st.divider()
    st.write("**App Developer:**")
    st.success("Ufford I.I.")
    st.write("**Institution:**")
    st.info("VikidylEdu Centre")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student Portal":
    st.header("🎯 Student Learning Hub")
    s_tab1, s_tab2, s_tab3 = st.tabs(["📝 Practice Exam", "📚 Digital Library", "🏆 Leaderboard"])
    
    with s_tab1:
        c1, c2 = st.columns(2)
        with c1: school_name = st.text_input("School Name:")
        with c2: student_name = st.text_input("Full Name:")
        
        level = st.selectbox("Educational Level:", ["Junior College (JSS)", "Senior College (SSS)"])
        col_a, col_b = st.columns(2)
        
        if level == "Junior College (JSS)":
            with col_a: sel_exam = st.selectbox("Exam Type:", ["BECE"])
            with col_b: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Basic Science", "Social Studies", "CCA", "PVS", "National Value"])
        else:
            with col_a: 
                dept = st.selectbox("Department:", ["Science", "Business", "Humanities/Arts"])
                sel_exam = st.selectbox("Exam Type:", ["NECO", "WAEC (SSCE)", "JAMB"])
            with col_b:
                if dept == "Science": subjects = ["Mathematics", "English", "Physics", "Chemistry", "Biology", "Further Maths", "Geography"]
                elif dept == "Business": subjects = ["Mathematics", "English", "Financial Accounting", "Commerce", "Economics", "Office Practice"]
                else: subjects = ["Mathematics", "English", "Literature in English", "Government", "History", "CRS/IRS", "Yoruba/Igbo/Hausa"]
                sel_subj = st.selectbox("Subject:", subjects)

        if st.button("🚀 START TIMED EXAM") and school_name and student_name:
            st.session_state.exam_start = time.time()
            st.session_state.score = 0
            st.session_state.q_idx = 0
            st.session_state.current_user = f"{school_name} | {student_name} | {sel_subj}"
            st.session_state.active_subj = sel_subj
            st.rerun()

        if 'exam_start' in st.session_state:
            st.divider()
            quiz_df = df[df['Subject'].astype(str).str.strip() == st.session_state.active_subj]
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.info(f"Question {st.session_state.q_idx + 1}: {q['Question']}")
                ans = st.radio("Choose:", [q['A'], q['B'], q['C'], q['D']], key=f"ans_{st.session_state.q_idx}")
                
                if st.button("✅ Submit"):
                    correct_col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                    if str(ans).strip() == str(q[correct_col]).strip():
                        st.success("Correct!")
                        st.session_state.score += 1
                        supabase.table("leaderboard").upsert({"name": st.session_state.current_user, "score": st.session_state.score}, on_conflict="name").execute()
                    else: st.error(f"Wrong. Answer: {q[correct_col]}")
                if st.button("Next ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()

    with s_tab3:
        st.subheader("🏆 National Top 10")
        res = supabase.table("leaderboard").select("*").order("score", desc=True).limit(10).execute()
        if res.data:
            st.table(get_clean_leaderboard(res.data))

# --- 5. TEACHER SUITE ---
elif role == "👨‍🏫 Teacher Suite":
    st.header("👨‍🏫 Teacher Suite")
    pwd = st.text_input("Key:", type="password")
    if pwd == "Lagos2026":
        t_school = st.text_input("Filter by School Name:")
        if t_school:
            res = supabase.table("leaderboard").select("*").ilike("name", f"{t_school}%").execute()
            if res.data: st.dataframe(get_clean_leaderboard(res.data), use_container_width=True)

# --- 6. PARENT CENTER ---
elif role == "👨‍👩‍👧 Parent Center":
    st.header("📊 Progress Report")
    ps = st.text_input("School Name:")
    pc = st.text_input("Child Name:")
    if ps and pc:
        res = supabase.table("leaderboard").select("*").ilike("name", f"{ps} | {pc}%").execute()
        if res.data:
            st.table(get_clean_leaderboard(res.data))

st.markdown("<div class='created-by'>Created by Ufford I.I. VikidylEdu Centre © 2026</div>", unsafe_allow_html=True)
