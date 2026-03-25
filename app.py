import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

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

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School")
            subs = sorted(df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist())
            years = ["ALL YEARS"] + sorted(df['year'].dropna().unique().astype(str).tolist(), reverse=True)
            
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", subs)
            with c2: year_p = st.selectbox("Exam Year", years)
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'].str.title() == subject) & (df['exam'].str.upper() == exam_p)
                if year_p != "ALL YEARS": filt = filt & (df['year'].astype(str) == year_p)
                q_df = df[filt]
                
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 40)).reset_index(drop=True)
                    st.session_state.update({
                        "exam_active": True, "current_q": 0, "user_answers": {}, 
                        "start_time": time.time(), "info": f"{school} | {name} | {subject} | {exam_p}"
                    })
                    st.rerun()
                else: st.warning("No questions found for this selection.")

    elif 'exam_active' in st.session_state:
        # ⏱️ 40 MINUTE TIMER
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 2400 - int(elapsed)) # 2400s = 40 mins
        mins, secs = divmod(remaining, 60)
        st.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
        
        if remaining <= 0:
            st.error("⏰ Time Expired! Submitting...")
            # Auto-submit logic...
        
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        row = q_df.iloc[curr]
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.write(row['question'])
        st.session_state.user_answers[curr] = st.radio("Choose:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        if st.button("Next ➡️") and curr < len(q_df)-1:
            st.session_state.current_q += 1; st.rerun()
        if st.button("🏁 FINISH"):
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            try:
                supabase.table("leaderboard").insert({"name": st.session_state.info, "score": score}).execute()
            except: pass
            st.session_state.final_score = score; st.session_state.total_qs = len(q_df); del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        for i, row in st.session_state.quiz_data.iterrows():
            with st.expander(f"Question {i+1} Review"):
                st.write(row['question'])
                st.write(f"**Correct Answer:** {row['correct_answer']}")
                st.info(f"💡 Explanation: {row.get('explanation', 'Refer to textbook.')}")
        if st.button("Restart"): del st.session_state['final_score']; st.rerun()

# --- 4. TEACHER & PARENT PORTALS ---
elif role in ["👪 Parent", "👨‍🏫 Teacher"]:
    st.header(f"{role} Portal")
    try:
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        t_df = pd.DataFrame(res.data)
        
        if role == "👨‍🏫 Teacher":
            if st.text_input("PIN", type="password") == "Lagos2026":
                st.write("### 📊 Diagnostic Dashboard")
                f_school = st.selectbox("School Filter", ["All"] + sorted(list(t_df['name'].str.split('|').str[0].unique())))
                if f_school != "All": t_df = t_df[t_df['name'].str.contains(f_school)]
                st.dataframe(t_df[['name', 'score', 'created_at']], use_container_width=True)
                st.download_button("Download Report", t_df.to_csv(index=False), "results.csv")
        
        elif role == "👪 Parent":
            child = st.text_input("Enter Child's Full Name")
            if child and not t_df.empty:
                match = t_df[t_df['name'].str.contains(child, case=False)]
                st.table(match[['name', 'score', 'created_at']])
    except: st.error("Refreshing database connection...")
