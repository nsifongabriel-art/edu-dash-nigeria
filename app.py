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
        pwd = st.text_input("Admin Password:", type="password")
        if pwd != "Lagos2026": 
            st.error("🔒 Unauthorized.")
            st.stop()

# --- 3. STUDENT VIEW ---
if role == "✍️ Student":
    tab1, tab2 = st.tabs(["📝 Practice Quiz", "📚 Study Materials"])
    
    with tab1:
        st.header("Practice Portal")
        school = st.text_input("School Name:")
        name = st.text_input("Full Name:")
        sel_exam = st.selectbox("Exam:", ["BECE", "NECO", "WAEC", "JAMB"])
        sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
        
        if st.button("🚀 Start Exam") and school and name:
            st.session_state.exam_start = time.time()
            st.session_state.score = 0
            st.session_state.q_idx = 0

        if 'exam_start' in st.session_state:
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
                        db_id = f"{school} | {name} | {sel_subj}"
                        supabase.table("leaderboard").upsert({"name": db_id, "score": st.session_state.score}, on_conflict="name").execute()
                    else:
                        st.error(f"Wrong. The answer was {q[col]}")
                    
                    # --- SHORT EXPLANATION ADDED HERE ---
                    exp_col = 'Explanation' if 'Explanation' in q else 'Short_Explanation'
                    if exp_col in q and pd.notna(q[exp_col]):
                        st.info(f"💡 **Teacher's Note:** {q[exp_col]}")

                if st.button("Next Question ➡️"):
                    st.session_state.q_idx += 1
                    st.rerun()

    with tab2:
        st.header("Study Materials")
        # Fetches materials uploaded by teachers
        try:
            mat_res = supabase.table("materials").select("*").execute()
            if mat_res.data:
                for m in mat_res.data:
                    st.link_button(f"📖 {m['subject']}: {m['title']}", m['link'])
            else:
                st.write("No materials uploaded yet.")
        except: st.write("Check back soon for notes!")

# --- 4. TEACHER VIEW ---
elif role == "👨‍🏫 Teacher":
    t_tab1, t_tab2, t_tab3 = st.tabs(["📊 Grades", "📤 Upload Materials", "💬 Parent Feedback"])
    
    with t_tab1:
        st.subheader("Student Results")
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)

    with t_tab2:
        st.subheader("Post Study Materials")
        m_title = st.text_input("Material Title (e.g. Algebra Notes)")
        m_subj = st.selectbox("Subject:", ["Mathematics", "English", "Biology"])
        m_link = st.text_input("Google Drive Link:")
        if st.button("Save Material"):
            supabase.table("materials").insert({"title": m_title, "subject": m_subj, "link": m_link}).execute()
            st.success("Material live for students!")

    with t_tab3:
        st.subheader("Notes from Parents")
        try:
            feed = supabase.table("feedback").select("*").execute()
            if feed.data: st.table(pd.DataFrame(feed.data))
        except: st.write("No feedback yet.")

# --- 5. PARENT VIEW ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Parental Portal")
    p_school = st.text_input("School:")
    p_child = st.text_input("Child Name:")
    
    if p_school and p_child:
        search = f"{p_school} | {p_child}%"
        res = supabase.table("leaderboard").select("*").ilike("name", search).execute()
        if res.data:
            for item in res.data:
                st.info(f"**{item['name'].split('|')[-1]}**: {item['score']} Points")
            
            st.divider()
            st.subheader("Send Feedback to Teacher")
            msg = st.text_area("How can the school help your child?")
            if st.button("Submit Feedback"):
                supabase.table("feedback").insert({"parent": p_child, "school": p_school, "message": msg}).execute()
                st.success("Feedback sent! 📩")

st.divider()
st.caption("Edu-Dash Nigeria © 2026")
