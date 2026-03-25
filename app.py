import streamlit as st
import pandas as pd
import json
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
                if year_p != "ALL YEARS":
                    filt = filt & (df['year'].astype(str) == year_p)
                
                q_df = df[filt]
                if not q_df.empty:
                    # Set question count - up to 50 if available
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 50)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "info": f"{school} | {name} | {subject} | {year_p}"})
                    st.rerun()
                else: st.warning("No questions found for this selection.")

    elif 'exam_active' in st.session_state:
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.write(q_df.iloc[curr]['question'])
        opts = [q_df.iloc[curr]['a'], q_df.iloc[curr]['b'], q_df.iloc[curr]['c'], q_df.iloc[curr]['d']]
        st.session_state.user_answers[curr] = st.radio("Pick one:", opts, key=f"q_{curr}")
        
        c1, c2 = st.columns(2)
        with c1:
            if curr > 0 and st.button("⬅️ Back"): st.session_state.current_q -= 1; st.rerun()
        with c2:
            if curr < len(q_df)-1:
                if st.button("Next ➡️"): st.session_state.current_q += 1; st.rerun()
            else:
                if st.button("🏁 FINISH"):
                    wrong_topics = []
                    score = 0
                    for i, r in q_df.iterrows():
                        if st.session_state.user_answers.get(i) == r['correct_answer']: score += 1
                        else: wrong_topics.append(r.get('topic', 'General'))
                    
                    # Fault-tolerant Database Insert
                    try:
                        supabase.table("leaderboard").insert({
                            "name": st.session_state.info, 
                            "score": score
                        }).execute()
                    except: pass 
                    
                    st.session_state.final_score = score
                    st.session_state.total_qs = len(q_df)
                    del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        for i, row in st.session_state.quiz_data.iterrows():
            with st.expander(f"Question {i+1} Review"):
                st.write(row['question'])
                st.write(f"Your Answer: {st.session_state.user_answers.get(i)}")
                st.write(f"Correct Answer: {row['correct_answer']}")
                st.info(f"💡 Explanation: {row.get('explanation', 'Practice makes perfect!')}")
        if st.button("Restart"): del st.session_state['final_score']; st.rerun()

# --- 4. PARENT & TEACHER PORTALS (Fault Tolerant) ---
else:
    st.header(f"{role} Portal")
    try:
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        all_data = pd.DataFrame(res.data)
        
        if role == "👪 Parent":
            s_name = st.text_input("Child's Name")
            if s_name and not all_data.empty:
                match = all_data[all_data['name'].str.contains(s_name, case=False)]
                st.dataframe(match[['name', 'score', 'created_at']])
        
        elif role == "👨‍🏫 Teacher":
            pin = st.text_input("PIN", type="password")
            if pin == "Lagos2026":
                st.dataframe(all_data)
                st.download_button("Download CSV", all_data.to_csv(index=False), "results.csv")
    except: st.error("Database connection busy. Please try again in 10 seconds.")
