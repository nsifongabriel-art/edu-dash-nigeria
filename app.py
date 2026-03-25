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

# --- 3. STUDENT PORTAL (Fixed Navigation) ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name (e.g. John Doe)")
            school = st.text_input("School Name")
            subs = sorted(df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist())
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", subs)
            with c2: exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'].str.title() == subject) & (df['exam'].str.upper() == exam_p)
                q_df = df[filt]
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 40)).reset_index(drop=True)
                    st.session_state.update({
                        "exam_active": True, "current_q": 0, "user_answers": {}, 
                        "start_time": time.time(), "s_name": name, "s_school": school, "s_sub": subject
                    })
                    st.rerun()

    elif 'exam_active' in st.session_state:
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # Header Info
        c1, c2 = st.columns([3, 1])
        with c1: st.subheader(f"Question {curr + 1} of {len(q_df)}")
        with c2: 
            rem = max(0, 2400 - int(time.time() - st.session_state.start_time))
            st.metric("⏳ Time", f"{rem//60:02d}:{rem%60:02d}")

        # Current Question
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [row['a'], row['b'], row['c'], row['d']]
        ans_idx = opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None
        choice = st.radio("Pick your answer:", opts, index=ans_idx, key=f"q_radio_{curr}")
        if choice: st.session_state.user_answers[curr] = choice

        st.divider()
        
        # Navigation Logic
        col1, col2, col3 = st.columns(3)
        with col1:
            if curr > 0:
                if st.button("⬅️ Previous"): 
                    st.session_state.current_q -= 1
                    st.rerun()
        with col2:
            st.write(f"Answered: {len(st.session_state.user_answers)}/{len(q_df)}")
        with col3:
            if curr < len(q_df) - 1:
                if st.button("Next ➡️"):
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                if st.button("🏁 FINISH EXAM"):
                    score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
                    # Store data as Name | School | Subject
                    full_id = f"{st.session_state.s_name} || {st.session_state.s_school} || {st.session_state.s_sub}"
                    try: supabase.table("leaderboard").insert({"name": full_id, "score": score}).execute()
                    except: pass
                    st.session_state.final_score = score
                    st.session_state.total_qs = len(q_df)
                    del st.session_state['exam_active']
                    st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        st.subheader("Review Corrections")
        for i, row in st.session_state.quiz_data.iterrows():
            u_ans = st.session_state.user_answers.get(i, "No Answer")
            with st.expander(f"Q{i+1}: {'✅' if u_ans == row['correct_answer'] else '❌'}"):
                st.write(f"**Question:** {row['question']}")
                st.write(f"**Correct:** {row['correct_answer']} | **Yours:** {u_ans}")
                st.info(f"💡 Explanation: {row.get('explanation', 'Refer to textbook.')}")
        if st.button("Logout"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL (Fixed Analysis) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("Admin PIN", type="password") == "Lagos2026":
        try:
            res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
            if res.data:
                results = pd.DataFrame(res.data)
                # Parse Name || School || Subject
                results[['Student', 'School', 'Subject']] = results['name'].str.split(' || ', expand=True)
                
                sel_school = st.selectbox("Filter by School", ["All"] + sorted(results['School'].unique().tolist()))
                df_view = results if sel_school == "All" else results[results['School'] == sel_school]
                
                st.dataframe(df_view[['Student', 'School', 'Subject', 'score', 'created_at']], use_container_width=True)
                
                st.divider()
                st.subheader("🔍 Deep Dive Student Analysis")
                target = st.selectbox("Select Student to Analyze", ["-- Select --"] + df_view['Student'].tolist())
                if target != "-- Select --":
                    s_data = df_view[df_view['Student'] == target].iloc[0]
                    st.write(f"### Performance Report for {target}")
                    st.metric("Final Score", f"{s_data['score']}")
                    st.write(f"**Status:** {'Ready for Exam' if int(s_data['score']) >= 7 else 'Needs Remedial Classes'}")
            else: st.info("No records found.")
        except: st.error("Database connecting...")

# --- 5. PARENT PORTAL (Strict Query) ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    st.write("Enter exact details to see your child's result.")
    p_name = st.text_input("Child's Full Name")
    p_school = st.text_input("School Name")
    if st.button("🔍 Search Result"):
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            all_r = pd.DataFrame(res.data)
            # Match strictly on name and school
            match = all_r[all_r['name'].str.contains(p_name, case=False) & all_r['name'].str.contains(p_school, case=False)]
            if not match.empty:
                st.success(f"Result found for {p_name}")
                st.table(match[['score', 'created_at']])
            else: st.error("No exact match found. Please check name and school spelling.")
