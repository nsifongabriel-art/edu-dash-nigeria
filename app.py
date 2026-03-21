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
    .stButton>button { border-radius: 12px; height: 3em; background-color: #1E3A8A; color: white; font-weight: bold; border: 2px solid #FFD700; }
    .created-by { text-align: center; color: #1E3A8A; padding: 25px; font-weight: bold; font-size: 1.1em; border-top: 3px double #EEE; margin-top: 50px;}
    .stSelectbox label { color: #1E3A8A; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Helper for Leaderboard Data
def clean_lb(data):
    if not data: return pd.DataFrame()
    ld = pd.DataFrame(data)
    # New format: "School | Name | Subject | Year"
    ld['School'] = ld['name'].apply(lambda x: x.split('|')[0].strip() if '|' in x else "General")
    ld['Student'] = ld['name'].apply(lambda x: x.split('|')[1].strip() if '|' in x else x)
    ld['Details'] = ld['name'].apply(lambda x: x.split('|')[-2].strip() + " (" + x.split('|')[-1].strip() + ")" if '|' in x else "Quiz")
    return ld[['Student', 'School', 'Details', 'score']]

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=65)
    st.title("VikidylEdu Dash")
    role = st.selectbox("Switch View:", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])
    st.divider()
    st.caption("Developed by: **Ufford I.I.**")
    st.caption("VikidylEdu Centre © 2026")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    st.header("🎯 Learning & Practice")
    t1, t2, t3 = st.tabs(["📝 Quiz", "📚 Library", "🏆 Leaderboard"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("Your School:")
        with c2: name = st.text_input("Your Full Name:")
        
        st.divider()
        
        # Selection Logic
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        with row1_col1:
            level = st.selectbox("Level:", ["Junior (JSS)", "Senior (SSS)"])
        with row1_col2:
            years = [str(y) for y in range(2026, 2010, -1)] # Dynamic years
            sel_year = st.selectbox("Exam Year:", years)
        with row1_col3:
            exams = ["BECE"] if "Junior" in level else ["WAEC", "NECO", "JAMB"]
            sel_exam = st.selectbox("Exam:", exams)

        dept_col, subj_col = st.columns(2)
        if "Senior" in level:
            with dept_col: dept = st.selectbox("Dept:", ["Science", "Business", "Arts"])
            with subj_col:
                if dept == "Science": subjs = ["Mathematics", "English", "Physics", "Chemistry", "Biology"]
                elif dept == "Business": subjs = ["Mathematics", "English", "Accounting", "Commerce", "Economics"]
                else: subjs = ["Mathematics", "English", "Government", "Literature", "History"]
                sel_subj = st.selectbox("Subject:", subjs)
        else:
            with dept_col: st.info("Level: Junior Secondary")
            with subj_col: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Basic Science", "Social Studies"])

        if st.button("🚀 Start Exam") and school and name:
            st.session_state.exam_start = time.time()
            st.session_state.score = 0
            st.session_state.q_idx = 0
            # NEW ID FORMAT: School | Name | Subject | Year
            st.session_state.db_id = f"{school} | {name} | {sel_subj} | {sel_year}"
            st.session_state.active_subj = sel_subj
            st.session_state.active_year = sel_year
            st.rerun()

        if 'exam_start' in st.session_state:
            st.divider()
            # Search logic: Match both Subject and Year in your Google Sheet
            # Ensure your Google Sheet has a 'Year' column!
            quiz_df = df[(df['Subject'].astype(str) == st.session_state.active_subj)]
            if 'Year' in df.columns:
                quiz_df = quiz_df[quiz_df['Year'].astype(str) == st.session_state.active_year]

            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.subheader(f"Question {st.session_state.q_idx + 1}")
                st.info(q['Question'])
                ans = st.radio("Select Answer:", [q['A'], q['B'], q['C'], q['D']], key=f"q_{st.session_state.q_idx}")
                
                if st.button("Submit Answer"):
                    c_col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                    if str(ans).strip() == str(q[c_col]).strip():
                        st.success("Correct! 🎉")
                        st.session_state.score += 1
                        supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": st.session_state.score}, on_conflict="name").execute()
                    else: st.error(f"Wrong. Answer was {q[c_col]}")
                
                if st.button("Next ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()
            else:
                st.warning(f"No questions found for {st.session_state.active_subj} ({st.session_state.active_year}).")

    with t3:
        st.subheader("🏆 Global Leaderboard")
        res = supabase.table("leaderboard").select("*").order("score", desc=True).limit(15).execute()
        if res.data: st.table(clean_lb(res.data))

# --- 5. TEACHER & PARENT (Simplified for filtered viewing) ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher Analytics")
    pwd = st.text_input("Key:", type="password")
    if pwd == "Lagos2026":
        ts = st.text_input("Enter School Name to filter:")
        if ts:
            res = supabase.table("leaderboard").select("*").ilike("name", f"{ts}%").execute()
            if res.data: st.dataframe(clean_lb(res.data), use_container_width=True)

elif role == "👨‍👩‍👧 Parent":
    st.header("Parental Report")
    ps = st.text_input("School:")
    pc = st.text_input("Child's Name:")
    if ps and pc:
        res = supabase.table("leaderboard").select("*").ilike("name", f"{ps} | {pc}%").execute()
        if res.data: st.table(clean_lb(res.data))

st.markdown(f"<div class='created-by'>Created by Ufford I.I. VikidylEdu Centre © 2026</div>", unsafe_allow_html=True)
