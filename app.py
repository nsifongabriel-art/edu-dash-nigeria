import streamlit as st
import pandas as pd
import time
import json
import plotly.express as px
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=1)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; }
    .timer-red { color: #ff4b4b; font-size: 30px; font-weight: bold; text-align: center; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .timer-normal { color: #1E3A8A; font-size: 30px; font-weight: bold; text-align: center; }
    .report-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; margin-bottom: 10px; }
</style>""", unsafe_allow_html=True)

# --- 3. SHARED HELPERS ---
def show_leaderboard():
    st.markdown("### 🏆 Wall of Fame")
    try:
        res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        for i, entry in enumerate(res.data):
            name = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
            st.markdown(f"<div class='winner-box'>#{i+1} {name} ({entry['score']} pts)</div>", unsafe_allow_html=True)
    except: st.caption("Leaderboard updating...")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
    show_leaderboard()
    st.divider()
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 5. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("📝 Registration")
        col1, col2 = st.columns(2)
        with col1: school = st.text_input("School Name:")
        with col2: name = st.text_input("Full Name (First & Surname):")
        
        exam_type = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        subj = st.selectbox("Subject", sorted(df['subject'].unique().tolist()) if not df.empty else ["MATHEMATICS"])
        
        if st.button("🚀 START EXAM"):
            if not school or len(name.strip().split()) < 2:
                st.error("Please provide School and Full Name (First + Surname).")
            else:
                quiz_df = df[(df['subject'].str.upper() == subj.upper()) & (df['exam'].str.upper() == exam_type.upper())]
                if not quiz_df.empty:
                    st.session_state.quiz_data = quiz_df.sample(n=min(len(quiz_df), 20)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "start_time": time.time(), "current_q": 0, "user_answers": {}, "db_id": f"{school} | {name} | {subj}"})
                    st.rerun()
                else: st.warning("No questions found.")
    else:
        # TIMER LOGIC
        elapsed = int(time.time() - st.session_state.start_time)
        rem = max(0, 1800 - elapsed)
        timer_class = "timer-red" if rem < 300 else "timer-normal"
        st.markdown(f"<div class='{timer_class}'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        q = q_df.iloc[curr]
        
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.markdown(f"### {q['question']}")
        st.session_state.user_answers[curr] = st.radio("Choose:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")
        
        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Previous") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with c2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with c3:
            if st.button("🏁 FINISH"):
                score, results = 0, []
                for i, row in q_df.iterrows():
                    ua = st.session_state.user_answers.get(i, "No Answer")
                    ca = str(row['correct_answer']).strip().upper()
                    is_ok = str(ua).strip().upper() == ca
                    if is_ok: score += 1
                    results.append({"q": row['question'], "ua": ua, "ca": ca, "ok": is_ok, "ex": row.get('explanation', 'None')})
                
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(results), "total_q": len(q_df)}, on_conflict="name").execute()
                st.session_state.final_score, st.session_state.final_script = score, results
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Final Score: {st.session_state.final_score} / {len(st.session_state.final_script)}")
        with st.expander("📖 Review Solutions"):
            for item in st.session_state.final_script:
                status = "✅" if item['ok'] else "❌"
                st.markdown(f"<div class='report-card'><b>{status} {item['q']}</b><br>Your: {item['ua']} | Correct: {item['ca']}<br><i>💡 {item['ex']}</i></div>", unsafe_allow_html=True)
        if st.button("New Exam"): st.session_state.clear(); st.rerun()

# --- 6. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "General")
            
            st.subheader("📊 Subject Averages")
            st.plotly_chart(px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', color='Subject'))
            
            st.subheader("📂 Student Audit")
            sel = st.selectbox("Select Student:", ["-- Select --"] + ld['name'].tolist())
            if sel != "-- Select --":
                row = ld[ld['name']
