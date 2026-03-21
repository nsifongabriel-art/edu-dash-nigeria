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

# --- 2. PROFESSIONAL UI CONFIG ---
st.set_page_config(page_title="Edu-Dash | Vikidyledu", page_icon="🇳🇬", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; height: 3em; background-color: #1E3A8A; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #F0F2F6; border-radius: 5px; padding: 10px; }
    .created-by { text-align: center; color: #1E3A8A; padding: 20px; font-weight: bold; font-size: 1.2em; border-top: 2px solid #EEE; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=80)
    st.title("Edu-Dash Portal")
    role = st.selectbox("I am a...", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])
    st.divider()
    st.write("**System Status:** 🟢 Live")
    st.write(f"**Dev:** Ufford I.I")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    st.header("🎯 Vikidyledu Student Center")
    s_tab1, s_tab2 = st.tabs(["📝 Practice Exam", "📚 Study Materials"])
    
    with s_tab1:
        with st.container():
            c1, c2 = st.columns(2)
            with c1: school_name = st.text_input("School Name:", placeholder="e.g. Vikidyledu International")
            with c2: student_name = st.text_input("Full Name:", placeholder="e.g. John Doe")
            
            ex_col, sub_col = st.columns(2)
            with ex_col: sel_exam = st.selectbox("Exam Type:", ["BECE", "NECO", "WAEC", "JAMB"])
            with sub_col: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
            
            if st.button("🚀 Start Exam Session") and school_name and student_name:
                st.session_state.exam_start = time.time()
                st.session_state.score = 0
                st.session_state.q_idx = 0

        if 'exam_start' in st.session_state:
            # Quiz Logic
            quiz_df = df[(df['Exam'].astype(str).str.upper().isin(['BECE', 'BESE', 'NECO', 'WAEC', 'JAMB'])) & (df['Subject'] == sel_subj)]
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.markdown(f"#### Question {st.session_state.q_idx + 1}")
                st.info(q['Question'])
                
                ans = st.radio("Choose the correct option:", [q['A'], q['B'], q['C'], q['D']], key=f"q_{st.session_state.q_idx}")
                
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("✅ Submit"):
                        col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                        if str(ans).strip() == str(q[col]).strip():
                            st.success("Correct! 🎉")
                            st.session_state.score += 1
                            db_id = f"{school_name} | {student_name} | {sel_subj}"
                            supabase.table("leaderboard").upsert({"name": db_id, "score": st.session_state.score}, on_conflict="name").execute()
                        else:
                            st.error(f"Wrong. Correct: {q[col]}")
                        
                        exp_col = 'Explanation' if 'Explanation' in q else 'Short_Explanation'
                        if exp_col in q and pd.notna(q[exp_col]):
                            st.warning(f"💡 **Explanation:** {q[exp_col]}")
                with btn2:
                    if st.button("Next ➡️"):
                        st.session_state.q_idx += 1
                        st.rerun()

    with s_tab2:
        st.subheader("📚 Digital Library")
        try:
            mat_res = supabase.table("materials").select("*").execute()
            if mat_res.data:
                for m in mat_res.data:
                    with st.expander(f"📖 {m['subject']} - {m['title']}"):
                        st.link_button("Download/View Resource", m['link'])
            else: st.write("Materials will be uploaded by your teacher soon.")
        except: st.write("Connection to Library lost...")

# --- 5. TEACHER SUITE ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Administration")
    pwd = st.text_input("Security Code:", type="password")
    if pwd == "Lagos2026":
        t_tab1, t_tab2, t_tab3 = st.tabs(["📊 School Grades", "📤 Post Materials", "💬 Parents"])
        
        with t_tab1:
            t_school = st.text_input("Enter your School Name to filter scores:")
            if t_school:
                res = supabase.table("leaderboard").select("*").ilike("name", f"{t_school}%").execute()
                if res.data:
                    res_df = pd.DataFrame(res.data)
                    res_df['Student'] = res_df['name'].apply(lambda x: x.split('|')[1] if '|' in x else x)
                    res_df['Subject'] = res_df['name'].apply(lambda x: x.split('|')[2] if '|' in x else "General")
                    st.dataframe(res_df[['Student', 'Subject', 'score']], use_container_width=True)
                    st.download_button("📥 Download Excel", res_df.to_csv(), f"{t_school}_grades.csv")
                else: st.write("No scores recorded for this school yet.")

        with t_tab2:
            st.subheader("Add Study Material")
            m_t = st.text_input("Document Title:")
            m_s = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
            m_l = st.text_input("Google Drive Share Link:")
            if st.button("Publish to Students"):
                supabase.table("materials").insert({"title": m_t, "subject": m_s, "link": m_l}).execute()
                st.success("Published Successfully!")

        with t_tab3:
            st.subheader("Feedback from Parents")
            try:
                f_res = supabase.table("feedback").select("*").execute()
                if f_res.data: st.table(f_res.data)
            except: st.write("No messages currently.")
    else: st.warning("Please enter the teacher's secret code.")

# --- 6. PARENT CENTER ---
elif role == "👨‍👩‍👧 Parent":
    st.header("📊 Child Progress Report")
    p_school = st.text_input("Child's School:")
    p_child = st.text_input("Child's Full Name:")
    if p_school and p_child:
        search = f"{p_school} | {p_child}%"
        res = supabase.table("leaderboard").select("*").ilike("name", search).execute()
        if res.data:
            for item in res.data:
                score = item['score']
                subj = item['name'].split('|')[-1]
                st.metric(f"Subject: {subj}", f"{score} Points")
            
            st.divider()
            st.subheader("Message the Teacher")
            msg = st.text_area("Observations/Requests:")
            if st.button("Send Message"):
                supabase.table("feedback").insert({"parent": p_child, "school": p_school, "message": msg}).execute()
                st.success("Message delivered to the teacher's suite!")

# --- FOOTER ---
st.markdown("<div class='created-by'>Created by Ufford I.I of the Vikidyledu Center © 2026</div>", unsafe_allow_html=True)
