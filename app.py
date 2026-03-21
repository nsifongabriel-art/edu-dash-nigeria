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
st.set_page_config(page_title="Edu-Dash Nigeria", page_icon="🇳🇬", layout="wide")

# Custom CSS for a "Premium" Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .stExpander { border: none !important; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); }
    footer {visibility: hidden;}
    .created-by { text-align: center; color: #6c757d; padding: 20px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR BRANDING ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=80)
    st.title("Edu-Dash Pro")
    role = st.selectbox("Switch Dashboard:", ["✍️ Student Portal", "👨‍🏫 Teacher Suite", "👨‍👩‍👧 Parent Center"])
    st.divider()
    st.info("🚀 Empowering Nigerian Students for BECE, NECO, WAEC & JAMB.")
    st.write("**Created by Gabriel Okon**") # <--- YOUR BRANDING

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student Portal":
    st.header("🎯 Learning Center")
    s_tab1, s_tab2 = st.tabs(["📝 Take an Exam", "📚 Library & Notes"])
    
    with s_tab1:
        with st.container():
            col1, col2 = st.columns(2)
            with col1: school = st.text_input("Enter School Name:")
            with col2: name = st.text_input("Enter Full Name:")
            
            exam_col, subj_col = st.columns(2)
            with exam_col: sel_exam = st.selectbox("Target Exam:", ["BECE", "NECO", "WAEC", "JAMB"])
            with subj_col: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
            
            if st.button("Start Timed Session") and school and name:
                st.session_state.exam_start = time.time()
                st.session_state.score = 0
                st.session_state.q_idx = 0

        if 'exam_start' in st.session_state:
            # Quiz Logic
            quiz_df = df[(df['Exam'].astype(str).str.upper().isin(['BECE', 'BESE', 'NECO'])) & (df['Subject'] == sel_subj)]
            if not quiz_df.empty:
                q = quiz_df.iloc[st.session_state.q_idx % len(quiz_df)]
                st.markdown(f"### Question {st.session_state.q_idx + 1}")
                st.info(q['Question'])
                
                ans = st.radio("Choose the correct option:", [q['A'], q['B'], q['C'], q['D']], key=f"q_{st.session_state.q_idx}")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Submit Answer"):
                        col = 'Correct_Answee' if 'Correct_Answee' in q else 'Correct_Answer'
                        if str(ans).strip() == str(q[col]).strip():
                            st.success("Correct! 🎉")
                            st.session_state.score += 1
                            db_id = f"{school} | {name} | {sel_subj}"
                            supabase.table("leaderboard").upsert({"name": db_id, "score": st.session_state.score}, on_conflict="name").execute()
                        else:
                            st.error(f"Wrong. Correct: {q[col]}")
                        
                        # Show Explanation
                        exp_col = 'Explanation' if 'Explanation' in q else 'Short_Explanation'
                        if exp_col in q and pd.notna(q[exp_col]):
                            st.warning(f"💡 **Explanation:** {q[exp_col]}")
                with c2:
                    if st.button("Next Question ➡️"):
                        st.session_state.q_idx += 1
                        st.rerun()

    with s_tab2:
        st.subheader("Reference Materials")
        try:
            mat_res = supabase.table("materials").select("*").execute()
            if mat_res.data:
                for m in mat_res.data:
                    with st.expander(f"📖 {m['subject']} - {m['title']}"):
                        st.write("Review these notes to improve your score.")
                        st.link_button("View Document", m['link'])
            else: st.write("No materials available yet.")
        except: st.write("Updating library...")

# --- 5. TEACHER SUITE ---
elif role == "👨‍🏫 Teacher Suite":
    st.header("Admin Dashboard")
    pwd = st.text_input("Security Key:", type="password")
    if pwd == "Lagos2026":
        t_tab1, t_tab2, t_tab3 = st.tabs(["📊 Gradebook", "📤 Material Manager", "💬 Feedback"])
        
        with t_tab1:
            st.subheader("Student Performance")
            res = supabase.table("leaderboard").select("*").execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data), use_container_width=True)

        with t_tab2:
            st.subheader("Add Study Material")
            m_t = st.text_input("Title")
            m_s = st.selectbox("Subject", ["Mathematics", "English", "Biology"])
            m_l = st.text_input("URL (Google Drive)")
            if st.button("Upload to Portal"):
                supabase.table("materials").insert({"title": m_t, "subject": m_s, "link": m_l}).execute()
                st.success("Added!")

        with t_tab3:
            st.subheader("Parent Messages")
            try:
                f_res = supabase.table("feedback").select("*").execute()
                if f_res.data: st.table(f_res.data)
            except: st.write("No messages.")
    else: st.warning("Enter valid key for admin access.")

# --- 6. PARENT CENTER ---
elif role == "👨‍👩‍👧 Parent Center":
    st.header("Progress Report")
    ps = st.text_input("School:")
    pc = st.text_input("Child's Name:")
    if ps and pc:
        search = f"{ps} | {pc}%"
        res = supabase.table("leaderboard").select("*").ilike("name", search).execute()
        if res.data:
            for item in res.data:
                st.metric(item['name'].split('|')[-1], f"{item['score']} Pts")
            
            st.divider()
            msg = st.text_area("Message for the Teacher:")
            if st.button("Send to School"):
                supabase.table("feedback").insert({"parent": pc, "school": ps, "message": msg}).execute()
                st.success("Sent!")

# --- FOOTER ---
st.markdown(f"---")
st.markdown(f"<div class='created-by'>Ufford I. I.VikidylEdu-Center Nigeria © 2026 | Created by VIKIDYLEDU CENTER</div>", unsafe_allow_html=True)
