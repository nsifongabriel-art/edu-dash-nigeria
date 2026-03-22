import streamlit as st
import pandas as pd
import time
import json
import plotly.express as px
from supabase import create_client, Client

# --- 1. DATABASE & DATA SETUP ---
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

# --- 2. PROFESSIONAL STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; border: 1px solid #DAA520; }
    .timer-red { color: #ff4b4b; font-size: 30px; font-weight: bold; text-align: center; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .timer-normal { color: #1E3A8A; font-size: 30px; font-weight: bold; text-align: center; }
    .report-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; margin-bottom: 10px; border: 1px solid #e5e7eb; color: #000; }
</style>""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
    st.markdown("### 🏆 Top 3 Scholars")
    try:
        ld_res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        if ld_res.data:
            for i, entry in enumerate(ld_res.data):
                clean_name = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
                st.markdown(f"<div class='winner-box'>#{i+1} {clean_name} - {entry['score']} pts</div>", unsafe_allow_html=True)
    except: st.caption("Leaderboard loading...")
    st.divider()
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("📝 Registration")
        c1, c2 = st.columns(2)
        with c1: school_input = st.text_input("School Name:")
        with c2: name_input = st.text_input("Full Name (First & Surname):")
        
        exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
        subj = st.selectbox("Subject", sorted(df['subject'].unique().tolist()) if not df.empty else ["ENGLISH"])
        
        if st.button("🚀 START"):
            if not school_input or len(name_input.strip().split()) < 2:
                st.error("Please enter School and both Firstname/Surname.")
            else:
                quiz_df = df[(df['subject'].str.upper() == subj.upper()) & (df['exam'].str.upper() == exam_type.upper())]
                if not quiz_df.empty:
                    st.session_state.quiz_data = quiz_df.sample(n=min(len(quiz_df), 20)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "start_time": time.time(), "current_q": 0, "user_answers": {}, "db_id": f"{school_input} | {name_input} | {subj}"})
                    st.rerun()
                else: st.warning("Subject questions not found.")
    else:
        # Timer
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        t_style = "timer-red" if rem < 300 else "timer-normal"
        st.markdown(f"<div class='{t_style}'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        row = q_df.iloc[curr]
        
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.markdown(f"### {row['question']}")
        st.session_state.user_answers[curr] = st.radio("Choose:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        col1, col2, col3 = st.columns([1,1,2])
        with col1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with col2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with col3:
            if st.button("🏁 SUBMIT"):
                score, results = 0, []
                for i, r in q_df.iterrows():
                    ans = st.session_state.user_answers.get(i, "None")
                    correct = str(r['correct_answer']).strip().upper()
                    is_ok = str(ans).strip().upper() == correct
                    if is_ok: score += 1
                    results.append({"q": r['question'], "ua": ans, "ca": correct, "ok": is_ok, "ex": r.get('explanation', 'No explanation provided.')})
                
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(results), "total_q": len(q_df)}, on_conflict="name").execute()
                st.session_state.final_score, st.session_state.final_script = score, results
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Final Score: {st.session_state.final_score} / {len(st.session_state.final_script)}")
        with st.expander("📖 View Solutions & Explanations"):
            for item in st.session_state.final_script:
                icon = "✅" if item['ok'] else "❌"
                st.markdown(f"<div class='report-card'><b>{icon} {item['q']}</b><br>You: {item['ua']} | Correct: {item['ca']}<br><i>💡 {item['ex']}</i></div>", unsafe_allow_html=True)
        if st.button("Restart"): st.session_state.clear(); st.rerun()

# --- 5. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher Diagnostic Suite")
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "N/A")
            
            st.subheader("📊 Subject Analysis")
            fig = px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', color='Subject', title="Average Scores by Subject")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📂 Student Script Audit")
            sel_name = st.selectbox("Select Student Record:", ["-- Select --"] + ld['name'].tolist())
            if sel_name != "-- Select --":
                student_row = ld[ld['name'] == sel_name].iloc[0]
                script_data = json.loads(student_row['script'])
                st.download_button("📥 Download Script (CSV)", data=pd.DataFrame(script_data).to_csv(index=False), file_name=f"{sel_name}.csv")
                for item in script_data:
                    st.write(f"**Q:** {item['q']} | **Result:** {'✅' if item['ok'] else '❌'}")
        else: st.info("No student records found.")

# --- 6. PARENT PORTAL ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Parent Portal")
    sch_search = st.text_input("Enter Child's School:")
    name_search = st.text_input("Enter Child's Full Name:")
    if st.button("🔍 Find Result") and sch_search and name_search:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            match = ld[(ld['name'].str.contains(sch_search, case=False)) & (ld['name'].str.contains(name_search, case=False))]
            if not match.empty:
                st.table(match[['name', 'score']])
            else: st.error("No record found. Check spelling or school name.")
