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
        background-color: #ff4b4b !important; color: white !important;
        border-radius: 8px !important; height: 48px !important; font-weight: bold !important;
    }
    .exam-header {
        background-color: #f0f2f6; padding: 10px; border-radius: 5px;
        text-align: center; border-bottom: 3px solid #ff4b4b; margin-bottom: 20px;
    }
    .correction-card {
        padding: 10px; border-radius: 5px; margin-bottom: 8px; border-left: 5px solid #ff4b4b;
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
    
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        name = st.text_input("Full Name")
        school = st.text_input("School Name")
        
        if df is not None:
            c1, c2, c3 = st.columns(3)
            with c1: subject = st.selectbox("Subject", sorted(df['subject'].unique()))
            with c2: year = st.selectbox("Year", ["All Years"] + sorted(df['year'].unique().astype(str), reverse=True))
            with c3: exam_p = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM", use_container_width=True):
                if name and school:
                    q_df = df[df['subject'] == subject]
                    if not q_df.empty:
                        q_df = q_df.sample(n=min(40, len(q_df))).reset_index(drop=True)
                        st.session_state.update({
                            "quiz_data": q_df, "expiry_time": time.time() + 1800,
                            "exam_active": True, "current_q": 0, "user_answers": {},
                            "s_info": {"name": name, "school": school, "sub": subject},
                            "confirm_submit": False
                        })
                        st.rerun()

    elif st.session_state.get('exam_active'):
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        st.markdown(f'<div class="exam-header"><h2>📖 {st.session_state.s_info["sub"].upper()} EXAMINATION</h2></div>', unsafe_allow_html=True)

        rem = int(st.session_state.expiry_time - time.time())
        st.subheader(f"Question {curr+1}/{len(q_df)} | ⏳ {max(0, rem)//60:02d}:{max(0, rem)%60:02d}")
        
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [str(row['a']), str(row['b']), str(row['c']), str(row['d'])]
        
        def sync(): st.session_state.user_answers[curr] = st.session_state[f"r_{curr}"]
        st.radio("Your Answer:", opts, index=opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None, key=f"r_{curr}", on_change=sync)

        st.divider()
        c1, _, c3 = st.columns(3)
        if curr > 0: c1.button("⬅️ Previous", on_click=lambda: st.session_state.update({"current_q": curr-1}), use_container_width=True)
        if curr < len(q_df)-1: c3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}), use_container_width=True)
        
        if not st.session_state.confirm_submit:
            if st.button("🏁 FINISH EXAM", use_container_width=True):
                st.session_state.confirm_submit = True; st.rerun()
        else:
            un = len(q_df) - len(st.session_state.user_answers)
            if un > 0: st.warning(f"⚠️ **REMARK:** You have {un} unattempted questions.")
            else: st.success("✅ **REMARK:** All questions answered.")
            
            cs1, cs2 = st.columns(2)
            if cs1.button("❌ Back", use_container_width=True): st.session_state.confirm_submit = False; st.rerun()
            if cs2.button("✅ Submit Result", type="primary", use_container_width=True) or rem <= 0:
                score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == str(r['correct_answer']))
                
                # Save Detailed Script for Review/Teacher
                script_list = []
                for i, r in q_df.iterrows():
                    u_a = st.session_state.user_answers.get(i, "Skipped")
                    c_a = str(r['correct_answer'])
                    res_icon = "✅" if u_a == c_a else "❌"
                    script_list.append(f"{r['question']} | {u_a} | {c_a} | {res_icon}")
                
                script_str = " ||| ".join(script_list)
                entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} || {script_str}"
                supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
                
                st.session_state.review_data = script_list
                st.session_state.final_score = score
                st.session_state.exam_active = False
                st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        
        # 1. Competiton Ranking
        with st.expander("🌎 GLOBAL RANKING", expanded=False):
            ranks = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(5).execute()
            for r in ranks.data: st.write(f"🥇 {r['name'].split(' || ')[0]} - {r['score']} pts")

        # 2. Student Corrections (Learn from mistakes)
        st.subheader("📚 Review Your Answers")
        for line in st.session_state.review_data:
            q, u, c, res = line.split(" | ")
            bg = "#d4edda" if res == "✅" else "#f8d7da"
            st.markdown(f'<div class="correction-card" style="background:{bg};"><b>Q: {q}</b><br>Your: {u} | Correct: {c} {res}</div>', unsafe_allow_html=True)

        if st.button("🔄 New Exam", use_container_width=True):
            for k in ['quiz_data', 'expiry_time', 'exam_active', 'current_q', 'user_answers', 'final_score', 'confirm_submit', 'review_data']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

# --- 5. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("PIN", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        if res.data:
            selected = st.selectbox("Select Student Script:", [f"{r['id']} - {r['name'].split(' || ')[0]}" for r in res.data])
            target = next(item for item in res.data if str(item['id']) in selected)
            parts = target['name'].split(" || ")
            
            if len(parts) >= 4:
                st.info(f"Student: {parts[0]} | Score: {target['score']}")
                q_rows = [line.split(" | ") for line in parts[3].split(" ||| ")]
                analysis_df = pd.DataFrame(q_rows, columns=["Question", "Student Answer", "Correct", "Status"])
                st.table(analysis_df)
                
                # DOC Download for Printing
                doc_content = f"Student: {parts[0]}\nScore: {target['score']}\n\n" + analysis_df.to_string()
                st.download_button("📥 Download/Print Script (DOC)", data=doc_content, file_name=f"{parts[0]}_Result.doc")

# --- 6. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    p_n = st.text_input("Child Name")
    if st.button("Search"):
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if p_n.lower() in r['name'].lower()]
        for m in matches:
            st.success(f"Subject: {m['name'].split(' || ')[2]} | Score: {m['score']}")
            st.info(f"AI Readiness: Based on this {m['score']} score, your child is showing steady progress!")
