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

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    button[use_container_width="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 8px !important;
        height: 48px !important;
        font-weight: bold !important;
    }
    .exam-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        border-bottom: 3px solid #ff4b4b;
        margin-bottom: 20px;
    }
    .correction-box {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #eee;
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
        st.header("✍️ Student Registration")
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
                            "s_info": {"name": name, "school": school, "sub": subject, "year": year},
                            "confirm_submit": False
                        })
                        st.rerun()
                else: st.warning("Please enter your name and school.")

    elif st.session_state.get('exam_active'):
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        sub_title = st.session_state.s_info['sub']
        
        st.markdown(f'<div class="exam-header"><h2>📖 {sub_title.upper()} EXAMINATION</h2></div>', unsafe_allow_html=True)

        if 'expiry_time' in st.session_state:
            rem = int(st.session_state.expiry_time - time.time())
            st.subheader(f"Question {curr+1} of {len(q_df)} | ⏳ {max(0, rem)//60:02d}:{max(0, rem)%60:02d}")
            
            row = q_df.iloc[curr]
            st.write(f"### {row['question']}")
            
            opts = [str(row['a']), str(row['b']), str(row['c']), str(row['d'])]
            def sync(): st.session_state.user_answers[curr] = st.session_state[f"r_{curr}"]
            
            st.radio("Select answer:", opts, 
                     index=opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None, 
                     key=f"r_{curr}", on_change=sync)

            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                if curr > 0:
                    if st.button("⬅️ Previous", use_container_width=True):
                        st.session_state.current_q -= 1
                        st.rerun()
            with c3:
                if curr < len(q_df)-1:
                    if st.button("Next ➡️", use_container_width=True):
                        st.session_state.current_q += 1
                        st.rerun()

            if not st.session_state.get("confirm_submit"):
                if st.button("🏁 FINISH EXAM", use_container_width=True):
                    st.session_state.confirm_submit = True
                    st.rerun()
            else:
                unattempted = len(q_df) - len(st.session_state.user_answers)
                if unattempted > 0: st.warning(f"⚠️ **REMARK:** {unattempted} questions remaining.")
                else: st.success("✅ Remark: All questions answered.")
                
                col_sub1, col_sub2 = st.columns(2)
                if col_sub1.button("❌ Back", use_container_width=True):
                    st.session_state.confirm_submit = False
                    st.rerun()
                if col_sub2.button("✅ Submit", type="primary", use_container_width=True) or (rem <= 0):
                    score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == str(r['correct_answer']))
                    
                    # Store Results for Review
                    review_data = []
                    for i, r in q_df.iterrows():
                        u_a = st.session_state.user_answers.get(i, "Skipped")
                        c_a = str(r['correct_answer'])
                        review_data.append({"q": r['question'], "u": u_a, "c": c_a, "res": "✅" if u_a == c_a else "❌"})
                    
                    st.session_state.review_list = review_data
                    st.session_state.final_score = score
                    st.session_state.exam_active = False
                    st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        
        # --- CORRECTIONS & REMARKS SECTION ---
        with st.expander("📝 VIEW CORRECTIONS & REMARKS", expanded=True):
            for idx, item in enumerate(st.session_state.review_list):
                color = "#d4edda" if item['res'] == "✅" else "#f8d7da"
                st.markdown(f"""
                    <div style="background-color:{color}; padding:10px; border-radius:5px; margin-bottom:10px; color:#333;">
                        <strong>Q{idx+1}: {item['q']}</strong><br>
                        Your Answer: {item['u']} | Correct: {item['c']} | {item['res']}
                    </div>
                """, unsafe_allow_html=True)

        if st.button("🔄 Start New Exam", use_container_width=True): 
            for k in ['quiz_data', 'expiry_time', 'exam_active', 'current_q', 'user_answers', 'final_score', 'confirm_submit', 'review_list']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

# --- TEACHER & PARENT REMAIN UNCHANGED ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher Portal")
    if st.text_input("PIN", type="password") == "Lagos2026":
        t_n = st.text_input("Student Name")
        if st.button("Search"):
            res = supabase.table("leaderboard").select("*").execute()
            st.session_state.teacher_results = pd.DataFrame([r for r in res.data if t_n.lower() in r['name'].lower()])
        if 'teacher_results' in st.session_state: st.dataframe(st.session_state.teacher_results[['name', 'score', 'created_at']])

elif role == "👪 Parent":
    st.header("Parent Access")
    p_n = st.text_input("Child Name")
    if st.button("Check"):
        res = supabase.table("leaderboard").select("*").execute()
        for m in [r for r in res.data if p_n.lower() in r['name'].lower()]:
            st.success(f"Score: {m['score']} ({m['created_at'][:10]})")
