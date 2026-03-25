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
def load_sheet():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])

# --- 3. STUDENT PORTAL (With 40-Min Timer & Remarks) ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School")
            subs = sorted(df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist())
            years = ["ALL YEARS"] + sorted(df['year'].dropna().unique().astype(str).tolist(), reverse=True)
            
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", subs)
            with c2: year_p = st.selectbox("Year", years)
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'].str.title() == subject) & (df['exam'].str.upper() == exam_p)
                if year_p != "ALL YEARS": filt = filt & (df['year'].astype(str) == year_p)
                q_df = df[filt]
                
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 40)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "start_time": time.time(), "s_name": name, "s_school": school, "s_sub": subject})
                    st.rerun()
                else: st.warning("No questions found.")

    elif 'exam_active' in st.session_state:
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, 2400 - int(elapsed))
        st.metric("⏳ Time Remaining", f"{rem//60:02d}:{rem%60:02d}")
        
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.write(q_df.iloc[curr]['question'])
        ans = st.radio("Choose:", [q_df.iloc[curr]['a'], q_df.iloc[curr]['b'], q_df.iloc[curr]['c'], q_df.iloc[curr]['d']], key=f"q_{curr}")
        st.session_state.user_answers[curr] = ans
        
        if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        if st.button("🏁 FINISH"):
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            missed = [r.get('topic', 'General') for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) != r['correct_answer']]
            
            # Diagnostic Packaging
            diag_str = f"School: {st.session_state.s_school} | Subject: {st.session_state.s_sub} | Weakness: {', '.join(list(set(missed))[:3])}"
            try: supabase.table("leaderboard").insert({"name": f"{st.session_state.s_name} || {diag_str}", "score": score}).execute()
            except: pass
            
            st.session_state.final_score = score
            st.session_state.total_qs = len(q_df)
            st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        perc = (st.session_state.final_score / st.session_state.total_qs)
        st.info("Remark: " + ("Excellent work, you are ready!" if perc >= 0.7 else "Keep practicing, focus on your weak areas."))
        if st.button("Restart"): del st.session_state['final_score']; st.rerun()

# --- 4. TEACHER & PARENT PORTALS (Independent Loading) ---
elif role in ["👪 Parent", "👨‍🏫 Teacher"]:
    st.header(f"{role} Portal")
    try:
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        results = pd.DataFrame(res.data)
        
        if role == "👨‍🏫 Teacher":
            if st.text_input("PIN", type="password") == "Lagos2026":
                # Diagnostic Logic
                results[['Student', 'Diagnostic']] = results['name'].str.split(' || ', expand=True)
                
                st.write("### 🔍 Individual Performance Analysis")
                selected = st.selectbox("Select Student to Analyze", ["-- Choose --"] + results['Student'].tolist())
                
                if selected != "-- Choose --":
                    student_data = results[results['Student'] == selected].iloc[0]
                    st.success(f"**Analysis for {selected}**")
                    st.write(f"**Context:** {student_data['Diagnostic']}")
                    st.metric("Score", f"{student_data['score']}")
                    if "Weakness" in student_data['Diagnostic']:
                        st.warning(f"🚩 **Teacher's Tip:** Focus remediation on: {student_data['Diagnostic'].split('Weakness: ')[1]}")
                
                st.divider()
                st.write("### 📋 All Records")
                st.dataframe(results[['Student', 'score', 'Diagnostic', 'created_at']])
        
        elif role == "👪 Parent":
            child = st.text_input("Enter Child's Full Name")
            if child and not results.empty:
                match = results[results['name'].str.contains(child, case=False)]
                if not match.empty:
                    score = match.iloc[0]['score']
                    st.metric("Latest Score", score)
                    st.write("🎯 **Readiness:** " + ("High" if score >= 7 else "Needs Improvement"))
    except: st.error("Database is syncing... please try again.")
