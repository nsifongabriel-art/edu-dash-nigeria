import streamlit as st
import pandas as pd
from supabase import create_client, Client
from io import BytesIO

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

df = load_data()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    if df is not None: st.success("✅ System Connected")

# --- 3. STUDENT PORTAL (With Results & Explanations) ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School")
            subs = sorted(df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist())
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", subs)
            with c2: exam_p = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START"):
                filt = (df['subject'].str.title() == subject) & (df['exam'].str.upper() == exam_p)
                q_df = df[filt]
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 10)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "info": f"{school} | {name} | {subject}"})
                    st.rerun()
                else: st.warning("No questions found.")

    elif 'exam_active' in st.session_state:
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.write(q_df.iloc[curr]['question'])
        ans = st.radio("Pick one:", [q_df.iloc[curr]['a'], q_df.iloc[curr]['b'], q_df.iloc[curr]['c'], q_df.iloc[curr]['d']], key=f"q_{curr}")
        st.session_state.user_answers[curr] = ans
        
        if st.button("Next") and curr < len(q_df)-1:
            st.session_state.current_q += 1; st.rerun()
        if st.button("🏁 FINISH"):
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            supabase.table("leaderboard").insert({"name": st.session_state.info, "score": score}).execute()
            st.session_state.final_score = score; del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Your Score: {st.session_state.final_score} / 10")
        for i, row in st.session_state.quiz_data.iterrows():
            with st.expander(f"Question {i+1} Review"):
                st.write(row['question'])
                st.write(f"Your Answer: {st.session_state.user_answers.get(i)}")
                st.write(f"Correct Answer: {row['correct_answer']}")
                st.info(f"💡 Explanation: {row.get('explanation', 'Keep practicing!')}")
        if st.button("Restart"): del st.session_state['final_score']; st.rerun()

# --- 4. PARENT PORTAL (With Query Search) ---
elif role == "👪 Parent":
    st.header("👪 Parent Query Portal")
    search_name = st.text_input("Enter Child's Full Name:")
    search_school = st.text_input("Enter School Name:")
    
    if st.button("🔍 Search Records"):
        res = supabase.table("leaderboard").select("*").execute()
        p_df = pd.DataFrame(res.data)
        # Filter by name and school within the combined string
        match = p_df[p_df['name'].str.contains(search_name, case=False) & p_df['name'].str.contains(search_school, case=False)]
        if not match.empty:
            st.table(match[['name', 'score', 'created_at']])
            avg_score = match['score'].mean()
            if avg_score >= 7: st.success("✅ Remark: Your child is highly ready for the exam!")
            else: st.warning("⚠️ Remark: More practice recommended in this subject.")
        else: st.error("No records found for this student.")

# --- 5. TEACHER PORTAL (Admin Dashboard) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Management Dashboard")
    pin = st.text_input("Enter Admin PIN:", type="password")
    if pin == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            t_df = pd.DataFrame(res.data)
            st.write("### All Student Scores")
            st.dataframe(t_df)
            
            # Export to Excel/CSV
            csv = t_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download All Scores (CSV)", csv, "results.csv", "text/csv")
