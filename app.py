import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. DATABASE & CONFIG ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"

try:
    supabase: Client = create_client(URL, KEY)
except Exception:
    st.error("📡 Database connection issue.")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10)
def load_sheet():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

# --- 2. CUSTOM CSS FOR CLEAN TEXT NAVIGATION ---
st.markdown("""
    <style>
    /* 1. Make Navigation look like plain clickable numbers */
    div[data-testid="column"] button[kind="secondary"] {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        color: #555 !important;
        min-width: 35px !important;
        width: auto !important;
        padding: 5px !important;
        font-size: 16px !important;
    }
    
    /* 2. Highlight for the Current Question */
    div[data-testid="column"] button[kind="primary"]:not([use_container_width="true"]) {
        background: none !important;
        border: none !important;
        color: #ff4b4b !important;
        text-decoration: underline !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }

    /* 3. Keep Action Buttons (Start/Finish/Next) Large and Professional */
    button[use_container_width="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 8px !important;
        height: 45px !important;
        font-weight: bold !important;
    }
    
    /* 4. Color Answered Questions Green */
    .answered-text {
        color: #28a745 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👪 Parent"])

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    
    if 'p_name' not in st.session_state: st.session_state.p_name = ""
    if 'p_school' not in st.session_state: st.session_state.p_school = ""

    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Registration")
        name = st.text_input("Full Name", value=st.session_state.p_name)
        school = st.text_input("School Name", value=st.session_state.p_school)
        
        if df is not None:
            c1, c2, c3 = st.columns(3)
            with c1: subject = st.selectbox("Subject", sorted(df['subject'].unique()))
            with c2: year = st.selectbox("Year", ["All Years"] + sorted(df['year'].unique().astype(str), reverse=True))
            with c3: exam_p = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM", use_container_width=True):
                if name and school:
                    st.session_state.p_name, st.session_state.p_school = name, school
                    limit = 50 if year == "All Years" else 40
                    q_df = df[df['subject'] == subject] if year == "All Years" else df[(df['subject'] == subject) & (df['year'].astype(str) == year)]
                    if not q_df.empty:
                        q_df = q_df.sample(n=min(limit, len(q_df))).reset_index(drop=True)
                        st.session_state.update({
                            "quiz_data": q_df, "expiry_time": time.time() + 1800,
                            "exam_active": True, "current_q": 0, "user_answers": {},
                            "s_info": {"name": name, "school": school, "sub": subject, "year": year}
                        })
                        st.rerun()
                else: st.warning("Please enter your name and school.")

    elif st.session_state.get('exam_active'):
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # --- BOX-FREE HORIZONTAL NAVIGATION ---
        st.write("Jump to:")
        # We use columns but our CSS removes the 'box' style from them
        nav_cols = st.columns(10) 
        for i in range(len(q_df)):
            with nav_cols[i % 10]:
                is_ans = i in st.session_state.user_answers
                # Change the number look if answered
                label = f"✓{i+1}" if is_ans else f"{i+1}"
                if st.button(label, key=f"n_{i}", type="primary" if i == curr else "secondary"):
                    st.session_state.current_q = i
                    st.rerun()

        st.divider()

        if 'expiry_time' in st.session_state:
            rem = int(st.session_state.expiry_time - time.time())
            st.subheader(f"Q{curr+1}/{len(q_df)} | ⏳ {max(0, rem)//60:02d}:{max(0, rem)%60:02d}")
            
            row = q_df.iloc[curr]
            st.write(f"### {row['question']}")
            
            opts = [str(row['a']), str(row['b']), str(row['c']), str(row['d'])]
            def sync(): st.session_state.user_answers[curr] = st.session_state[f"r_{curr}"]
            
            st.radio("Select Answer:", opts, 
                     index=opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None, 
                     key=f"r_{curr}", on_change=sync)

            st.divider()
            c1, c2, c3 = st.columns(3)
            if curr > 0: c1.button("⬅️ Previous", on_click=lambda: st.session_state.update({"current_q": curr-1}), use_container_width=True)
            if curr < len(q_df)-1: c3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}), use_container_width=True)
            
            st.write("")
            if st.button("🏁 FINISH EXAM", use_container_width=True) or (rem <= 0):
                score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == str(r['correct_answer']))
                script = " ||| ".join([f"{r['question']} | {st.session_state.user_answers.get(i,'--')} | {r['correct_answer']} | {'✅' if st.session_state.user_answers.get(i)==str(r['correct_answer']) else '❌'}" for i, r in q_df.iterrows()])
                entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} || {script}"
                try:
                    supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
                    st.session_state.final_score = score
                    st.session_state.exam_active = False
                    st.rerun()
                except: st.error("Save failed. Check your internet connection.")

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Final Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        if st.button("🔄 Start New Exam", use_container_width=True): 
            for k in ['quiz_data', 'expiry_time', 'exam_active', 'current_q', 'user_answers', 'final_score']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

# --- 5. TEACHER & PARENT ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Portal")
    if st.text_input("PIN", type="password") == "Lagos2026":
        t_name = st.text_input("Student Name")
        if st.button("🔍 Search"):
            res = supabase.table("leaderboard").select("*").execute()
            matches = [r for r in res.data if t_name.lower() in r['name'].lower()]
            if matches: st.session_state.teacher_results = pd.DataFrame(matches)
        if 'teacher_results' in st.session_state:
            st.dataframe(st.session_state.teacher_results[['name', 'score', 'created_at']])

elif role == "👪 Parent":
    st.header("👪 Parent Access")
    p_name = st.text_input("Child Name")
    if st.button("Check Result"):
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if p_name.lower() in r['name'].lower()]
        for m in matches: st.success(f"Score: {m['score']} ({m['created_at'][:10]})")
