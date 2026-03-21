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
    .stSelectbox label { font-weight: bold; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

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
    s_tab1, s_tab2 = st.tabs(["📝 Practice Exam", "📚 Digital Library"])
    
    with s_tab1:
        # Identity Section
        c1, c2 = st.columns(2)
        with c1: school_name = st.text_input("School Name:", placeholder="e.g. VikidylEdu Academy")
        with c2: student_name = st.text_input("Full Name:", placeholder="e.g. Samuel Ade")

        st.divider()
        
        # Level Selection (Triggers UI Change)
        level = st.selectbox("Educational Level:", ["Junior College (JSS)", "Senior College (SSS)"])

        # Dynamic Logic for Departments and Subjects
        col_a, col_b = st.columns(2)
        
        if level == "Junior College (JSS)":
            with col_a: sel_exam = st.selectbox("Exam Type:", ["BECE"])
            with col_b: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Basic Science", "Social Studies", "CCA", "PVS", "National Value"])
        else:
            with col_a: 
                dept = st.selectbox("Department:", ["Science", "Business", "Humanities/Arts"])
                sel_exam = st.selectbox("Exam Type:", ["NECO", "WAEC (SSCE)", "JAMB"])
            with col_b:
                if dept == "Science":
                    subjects = ["Mathematics", "English", "Physics", "Chemistry", "Biology", "Further Maths", "Geography"]
                elif dept == "Business":
                    subjects = ["Mathematics", "English", "Financial Accounting", "Commerce", "Economics", "Office Practice"]
                else: # Humanities
                    subjects = ["Mathematics", "English", "Literature in English", "Government", "History", "CRS/IRS", "Yoruba/Igbo/Hausa"]
                sel_subj = st.selectbox("Subject:", subjects)

        if st.button("🚀 START TIMED EXAM"):
            if not school_name or not student_name:
                st.error("Please enter your School and Name first!")
            else:
                st.session_state.exam_start = time.time()
                st.session_state.score = 0
                st.session_state.q_idx = 0
                st.session_state.current_user = f"{school_name} | {student_name} | {sel_subj}"
                st.session_state.active_subj = sel_subj
                st.rerun()

        # Quiz Active State
        if 'exam_start' in st.session_state:
            st.divider()
            # Filter question bank by subject
            quiz_df = df[df['Subject'].astype(str).str.strip() == st.session_state.active_subj]
            
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.markdown(f"#### Question {st.session_state.q_idx + 1}")
                st.info(q['Question'])
                
                ans = st.radio("Choose your answer:", [q['A'], q['B'], q['C'], q['D']], key=f"ans_{st.session_state.q_idx}")
                
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("✅ Submit Answer"):
                        correct_col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                        if str(ans).strip() == str(q[correct_col]).strip():
                            st.success("Correct! 🎉")
                            st.session_state.score += 1
                            supabase.table("leaderboard").upsert({"name": st.session_state.current_user, "score": st.session_state.score}, on_conflict="name").execute()
                        else:
                            st.error(f"Wrong. The correct answer was: {q[correct_col]}")
                        
                        exp_col = 'Explanation' if 'Explanation' in q else 'Short_Explanation'
                        if exp_col in q and pd.notna(q[exp_col]):
                            st.warning(f"💡 **Teacher's Note:** {q[exp_col]}")

                with btn2:
                    if st.button("Next Question ➡️"):
                        st.session_state.q_idx += 1
                        st.rerun()
            else:
                st.warning(f"The question bank for {st.session_state.active_subj} is being prepared. Please try another subject!")

    with s_tab2:
        st.subheader("📚 Digital Library")
        st.write("Access your school's shared resources below:")
        try:
            mats = supabase.table("materials").select("*").execute()
            if mats.data:
                for m in mats.data:
                    with st.expander(f"📖 {m['subject']} - {m['title']}"):
                        st.link_button("Download Resource", m['link'])
            else: st.write("No materials uploaded for your level yet.")
        except: st.write("Connect to internet to load materials.")

# --- 5. TEACHER SUITE ---
elif role == "👨‍🏫 Teacher Suite":
    st.header("👨‍🏫 Teacher Administration")
    pwd = st.text_input("Security Code:", type="password")
    if pwd == "Lagos2026":
        t_tab1, t_tab2, t_tab3 = st.tabs(["📊 Performance", "📤 Post Materials", "💬 Feedback"])
        
        with t_tab1:
            t_school = st.text_input("Enter School Name to filter grades:")
            if t_school:
                res = supabase.table("leaderboard").select("*").ilike("name", f"{t_school}%").execute()
                if res.data:
                    res_df = pd.DataFrame(res.data)
                    st.dataframe(res_df, use_container_width=True)
                else: st.write("No students recorded for this school.")

        with t_tab2:
            st.subheader("Upload to Student Library")
            m_t = st.text_input("Document Title:")
            m_s = st.selectbox("Subject:", ["Mathematics", "English", "Physics", "Chemistry", "Biology", "Economics", "Government"])
            m_l = st.text_input("Google Drive Link:")
            if st.button("Publish Material"):
                supabase.table("materials").insert({"title": m_t, "subject": m_s, "link": m_l}).execute()
                st.success("Resource is now live!")

        with t_tab3:
            st.subheader("Parent Observation Notes")
            try:
                f_res = supabase.table("feedback").select("*").execute()
                if f_res.data: st.table(f_res.data)
            except: st.write("No feedback received yet.")
    else: st.info("Enter Teacher's Security Key for access.")

# --- 6. PARENT CENTER ---
elif role == "👨‍👩‍👧 Parent Center":
    st.header("📊 Child Progress Report")
    p_school = st.text_input("Enter School Name:")
    p_child = st.text_input("Enter Child's Full Name:")
    if p_school and p_child:
        search = f"{p_school} | {p_child}%"
        res = supabase.table("leaderboard").select("*").ilike("name", search).execute()
        if res.data:
            for item in res.data:
                score = item['score']
                subj = item['name'].split('|')[-1]
                st.metric(f"Subject: {subj}", f"{score} Points")
            
            st.divider()
            st.subheader("Direct Message to Teacher")
            msg = st.text_area("Observations or Requests:")
            if st.button("Submit Message"):
                supabase.table("feedback").insert({"parent": p_child, "school": p_school, "message": msg}).execute()
                st.success("Message sent successfully!")

# --- FOOTER ---
st.markdown("<div class='created-by'>Created by Ufford I.I. VikidylEdu Centre © 2026</div>", unsafe_allow_html=True)
