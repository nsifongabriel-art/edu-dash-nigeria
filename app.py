import streamlit as st
import pd
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

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School")
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
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 2400 - int(elapsed))
        
        # --- TIMER & NAV ---
        c1, c2 = st.columns([3, 1])
        with c1: st.subheader(f"Question {st.session_state.current_q + 1} of {len(q_df)}")
        with c2: st.metric("⏳ Time", f"{remaining//60:02d}:{remaining%60:02d}")

        # Navigation Grid
        grid = st.columns(10)
        for i in range(len(q_df)):
            with grid[i % 10]:
                if st.button(f"{i+1}", key=f"n_{i}", type="primary" if i in st.session_state.user_answers else "secondary"):
                    st.session_state.current_q = i
                    st.rerun()

        st.divider()
        curr = st.session_state.current_q
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [row['a'], row['b'], row['c'], row['d']]
        
        ans_idx = opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None
        choice = st.radio("Select Answer:", opts, index=ans_idx, key=f"r_{curr}")
        if choice: st.session_state.user_answers[curr] = choice

        # --- SUBMISSION ---
        if st.button("🏁 FINISH & REVIEW RESULTS"):
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            diag = f"School: {st.session_state.s_school} | Sub: {st.session_state.s_sub}"
            try:
                supabase.table("leaderboard").insert({"name": f"{st.session_state.s_name} || {diag}", "score": score}).execute()
            except: pass
            st.session_state.final_score = score
            st.session_state.total_qs = len(q_df)
            del st.session_state['exam_active']
            st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Your Result: {st.session_state.final_score} / {st.session_state.total_qs}")
        
        # Personalized Remark
        perc = st.session_state.final_score / st.session_state.total_qs
        if perc >= 0.75: st.success("🌟 Excellent! You are highly ready for your exam.")
        elif perc >= 0.5: st.warning("👍 Good effort! Review the corrections below to improve.")
        else: st.error("📚 Don't be discouraged. Keep studying and focus on the explanations below.")

        st.subheader("📝 Correction & Explanation Screen")
        for i, row in st.session_state.quiz_data.iterrows():
            u_ans = st.session_state.user_answers.get(i, "No Answer")
            is_correct = u_ans == row['correct_answer']
            
            with st.expander(f"Question {i+1}: {'✅ Correct' if is_correct else '❌ Incorrect'}"):
                st.write(f"**Question:** {row['question']}")
                st.write(f"**Your Answer:** {u_ans}")
                st.write(f"**Correct Answer:** {row['correct_answer']}")
                st.info(f"💡 **Explanation:** {row.get('explanation', 'Consult your textbook for more details.')}")
        
        if st.button("Return to Login"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

# --- 4. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("PIN", type="password") == "Lagos2026":
        try:
            res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
            if res.data:
                results = pd.DataFrame(res.data)
                # Re-parse the diagnostic string carefully
                results[['Student', 'Details']] = results['name'].str.split(' || ', expand=True)
                st.dataframe(results[['Student', 'score', 'Details', 'created_at']], use_container_width=True)
            else:
                st.info("No students have submitted their exams yet.")
        except: st.error("Database connection issue. Refreshing...")
