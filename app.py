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

# --- 2. UI CONFIG ---
st.set_page_config(page_title="Edu-Dash | Vikidyledu", page_icon="🇳🇬", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 12px; height: 3.5em; background-color: #1E3A8A; color: white; font-weight: bold; border: 2px solid #FFD700; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .created-by { text-align: center; color: #1E3A8A; padding: 25px; font-weight: bold; font-size: 1.1em; border-top: 3px double #EEE; margin-top: 50px;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=70)
    st.title("Vikidyledu Dash")
    role = st.selectbox("Navigation Menu", ["✍️ Student Portal", "👨‍🏫 Teacher Suite", "👨‍👩‍👧 Parent Center"])
    st.divider()
    st.caption("Developed by: **Ufford I.I**")
    st.caption("Vikidyledu Center © 2026")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student Portal":
    st.header("🎯 Student Learning Hub")
    s_tab1, s_tab2 = st.tabs(["📝 Practice Exam", "📚 Digital Library"])
    
    with s_tab1:
        with st.form("exam_setup"):
            st.subheader("Step 1: Identity")
            c1, c2 = st.columns(2)
            with c1: school_name = st.text_input("School Name:")
            with c2: student_name = st.text_input("Full Name:")
            
            st.subheader("Step 2: Select Level & Category")
            lvl_col, cat_col, ex_col = st.columns(3)
            
            with lvl_col:
                level = st.selectbox("Educational Level:", ["Junior College (JSS)", "Senior College (SSS)"])
            
            with cat_col:
                if level == "Junior College (JSS)":
                    category = st.selectbox("Category:", ["General Junior"])
                    subjects = ["Mathematics", "English", "Basic Science", "Social Studies", "CCA", "PVS", "National Value"]
                    exams = ["BECE"]
                else:
                    category = st.selectbox("Department:", ["Science", "Business", "Humanities/Arts"])
                    exams = ["NECO", "WAEC (SSCE)", "JAMB"]
                    if category == "Science":
                        subjects = ["Mathematics", "English", "Physics", "Chemistry", "Biology", "Further Maths", "Geography"]
                    elif category == "Business":
                        subjects = ["Mathematics", "English", "Financial Accounting", "Commerce", "Economics", "Office Practice"]
                    else: # Humanities
                        subjects = ["Mathematics", "English", "Literature in English", "Government", "History", "CRS/IRS", "Yoruba/Igbo/Hausa"]

            with ex_col:
                sel_exam = st.selectbox("Exam Type:", exams)
            
            sel_subj = st.selectbox("Choose Subject:", subjects)
            
            submitted = st.form_submit_state = st.form_submit_button("🚀 START TIMED EXAM")
            
            if submitted and school_name and student_name:
                st.session_state.exam_start = time.time()
                st.session_state.score = 0
                st.session_state.q_idx = 0
                st.session_state.current_school = school_name
                st.session_state.current_student = student_name
                st.session_state.current_subj = sel_subj
                st.rerun()

        # Quiz Logic
        if 'exam_start' in st.session_state:
            st.divider()
            quiz_df = df[(df['Subject'] == st.session_state.current_subj)] # Logic to filter by level/exam can be added to your Sheet
            
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.markdown(f"#### Question {st.session_state.q_idx + 1}")
                st.info(q['Question'])
                
                ans = st.radio("Pick your answer:", [q['A'], q['B'], q['C'], q['D']], key=f"q_{st.session_state.q_idx}")
                
                if st.button("✅ Submit Answer"):
                    col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                    if str(ans).strip() == str(q[col]).strip():
                        st.success("Correct! 🎉")
                        st.session_state.score += 1
                        db_id = f"{st.session_state.current_school} | {st.session_state.current_student} | {st.session_state.current_subj}"
                        supabase.table("leaderboard").upsert({"name": db_id, "score": st.session_state.score}, on_conflict="name").execute()
                    else:
                        st.error(f"Incorrect. The right answer was {q[col]}")
                    
                    # Show Explanation
                    exp_col = 'Explanation' if 'Explanation' in q else 'Short_Explanation'
                    if exp_col in q and pd.notna(q[exp_col]):
                        st.warning(f"💡 **Teacher's Explanation:** {q[exp_col]}")

                if st.button("Move to Next Question ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()
            else:
                st.warning(f"Question bank for {st.session_state.current_subj} is being updated. Please try another subject!")

# --- 5. TEACHER & PARENT VIEWS (Keeping the School Logic) ---
# [Code remains the same as previous for Teacher/Parent for brevity, filtering by school]
elif role == "👨‍🏫 Teacher Suite":
    st.header("👨‍🏫 Teacher Administration")
    pwd = st.text_input("Security Code:", type="password")
    if pwd == "Lagos2026":
        t_tab1, t_tab2 = st.tabs(["📊 Performance Tracking", "📤 Material Manager"])
        with t_tab1:
            t_school = st.text_input("Enter School Name to filter:")
            if t_school:
                res = supabase.table("leaderboard").select("*").ilike("name", f"{t_school}%").execute()
                if res.data:
                    res_df = pd.DataFrame(res.data)
                    st.dataframe(res_df, use_container_width=True)
        with t_tab2:
            st.subheader("Upload Study Material Links")
            # [Previous upload logic here]

elif role == "👨‍👩‍👧 Parent Center":
    st.header("📊 Progress Report")
    p_school = st.text_input("School:")
    p_child = st.text_input("Child's Name:")
    if p_school and p_child:
        search = f"{p_school} | {p_child}%"
        res = supabase.table("leaderboard").select("*").ilike("name", search).execute()
        if res.data:
            for item in res.data:
                st.metric(item['name'].split('|')[-1], f"{item['score']} Pts")

# --- FOOTER ---
st.markdown(f"<div class='created-by'>Created by Ufford I.I  Vikidyledu Center © 2026</div>", unsafe_allow_html=True)
