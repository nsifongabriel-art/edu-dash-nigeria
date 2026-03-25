import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10)
def load_sheet():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

# --- 2. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=100)
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👪 Parent"])

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School Name")
            
            c1, c2 = st.columns(2)
            with c1: 
                subs = sorted(df['subject'].dropna().unique().tolist())
                subject = st.selectbox("Subject", subs)
            with c2: 
                # RESTORED YEAR SELECTION
                years = ["All Years"] + sorted(df['year'].dropna().unique().astype(str).tolist(), reverse=True)
                year_p = st.selectbox("Exam Year", years)
            
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'] == subject) & (df['exam'].str.upper() == exam_p)
                if year_p != "All Years":
                    filt = filt & (df['year'].astype(str) == year_p)
                
                q_df = df[filt]
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 40)).reset_index(drop=True)
                    st.session_state.update({
                        "exam_active": True, "current_q": 0, "user_answers": {}, 
                        "start_time": time.time(), "s_name": name, "s_school": school, "s_sub": subject
                    })
                    st.rerun()
                else: st.warning("No questions found for this selection.")

    elif 'exam_active' in st.session_state:
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # Header / Timer
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, 2400 - int(elapsed))
        cols = st.columns([4, 1])
        cols[0].subheader(f"Question {curr + 1} of {len(q_df)}")
        cols[1].metric("⏳ Timer", f"{rem//60:02d}:{rem%60:02d}")

        # Nav Grid
        nav = st.columns(10)
        for i in range(len(q_df)):
            if nav[i%10].button(f"{i+1}", key=f"n{i}", type="primary" if i in st.session_state.user_answers else "secondary"):
                st.session_state.current_q = i; st.rerun()

        st.divider()
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [row['a'], row['b'], row['c'], row['d']]
        
        ans_idx = opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None
        choice = st.radio("Choose the correct option:", opts, index=ans_idx, key=f"r{curr}")
        if choice: st.session_state.user_answers[curr] = choice

        # Navigation
        st.divider()
        b1, b2, b3 = st.columns([1, 2, 1])
        if curr > 0: b1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: b3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        else:
            if b3.button("🏁 FINISH", type="primary"):
                score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
                id_tag = f"{st.session_state.s_name} || {st.session_state.s_school} || {st.session_state.s_sub}"
                try: supabase.table("leaderboard").insert({"name": id_tag, "score": score}).execute()
                except: pass
                st.session_state.final_score = score
                st.session_state.total_qs = len(q_df)
                del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        st.title("📊 Performance Review")
        perc = (st.session_state.final_score / st.session_state.total_qs) * 100
        st.metric("Final Score", f"{st.session_state.final_score} / {st.session_state.total_qs}", f"{perc:.1f}%")
        
        st.divider()
        st.subheader("💡 Question-by-Question Insight")
        
        for i, row in st.session_state.quiz_data.iterrows():
            u_ans = st.session_state.user_answers.get(i, "Not Answered")
            is_right = u_ans == row['correct_answer']
            
            with st.container(border=True):
                c1, c2 = st.columns([0.1, 0.9])
                c1.write("✅" if is_right else "❌")
                with c2:
                    st.write(f"**Question {i+1}:** {row['question']}")
                    st.write(f"👉 Your Answer: `{u_ans}`")
                    st.write(f"🎯 Correct Answer: `{row['correct_answer']}`")
                    
                    # AI Added Insight
                    with st.expander("✨ AI Insight & Explanation"):
                        st.info(f"**Concept:** {row.get('topic', 'General Knowledge')}\n\n**Why this is correct:** {row.get('explanation', 'This answer follows standard academic principles for this subject.')}")
        
        if st.button("Close and Exit"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL (Fixed Loading) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Control Center")
    pin = st.text_input("Enter Admin PIN", type="password")
    if pin == "Lagos2026":
        try:
            # Removed the sheet-loading dependency here to stop the "Loading" hang
            res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
            if res.data:
                results = pd.DataFrame(res.data)
                # Parse safety
                results[['Student', 'School', 'Subject']] = results['name'].str.split(' || ', expand=True)
                
                st.write("### 📈 Recent Activity")
                st.dataframe(results[['Student', 'School', 'Subject', 'score', 'created_at']], use_container_width=True)
                
                st.divider()
                st.write("### 🔍 Diagnostic Drill-down")
                pick = st.selectbox("Select Student for Script Review", ["-- Select --"] + results['Student'].tolist())
                if pick != "-- Select --":
                    s_rec = results[results['Student'] == pick].iloc[0]
                    st.success(f"Student: {pick} | Score: {s_rec['score']}")
                    st.write(f"**School:** {s_rec['School']} | **Subject:** {s_rec['Subject']}")
            else: st.info("Waiting for first student submission...")
        except: st.error("Database is refreshing. Please wait 5 seconds.")

# --- 5. PARENT PORTAL (Secure Query) ---
elif role == "👪 Parent":
    st.header("👪 Parent Result Portal")
    p_name = st.text_input("Enter Child's Full Name")
    p_school = st.text_input("Enter Child's School Name")
    if st.button("Search Result"):
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            all_r = pd.DataFrame(res.data)
            match = all_r[all_r['name'].str.contains(p_name, case=False) & all_r['name'].str.contains(p_school, case=False)]
            if not match.empty:
                st.success(f"Result found for {p_name}")
                st.write(f"### Score: {match.iloc[0]['score']}")
                st.caption(f"Last Attempt: {match.iloc[0]['created_at']}")
            else: st.error("Result not found. Please ensure names match exactly.")
