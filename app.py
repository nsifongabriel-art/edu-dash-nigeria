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

MASTER_SUBJECTS = ["MATHEMATICS", "ENGLISH LANGUAGE", "BIOLOGY", "PHYSICS", "CHEMISTRY", "ECONOMICS", "GOVERNMENT", "LITERATURE", "CIVIC EDUCATION", "COMMERCE", "AGRIC SCIENCE", "GEOGRAPHY", "CRS", "IRS", "HISTORY", "COMPUTER STUDIES"]

@st.cache_data(ttl=1)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

def get_remark(score, total):
    if total <= 0: return "No Data"
    pct = (score / total) * 100
    if pct >= 75: return "🌟 Excellent!"
    elif pct >= 50: return "👍 Good job."
    else: return "📚 Needs improvement."

# --- 2. UI STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; border: 1px solid #DAA520; }
    .passage-box { background-color: #f8fafc; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; border: 1px solid #cbd5e1; color: #000; }
    .question-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #1E3A8A; font-size: 20px; border: 1px solid #e5e7eb; color: #000; }
</style>""", unsafe_allow_html=True)

# --- 3. SIDEBAR & LEADERBOARD ---
with st.sidebar:
    st.title("VikidylEdu")
    st.markdown("### 🏆 Top Performers")
    try:
        ld_res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        if ld_res.data:
            for i, entry in enumerate(ld_res.data):
                short_name = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
                st.markdown(f"<div class='winner-box'>#{i+1} {short_name}: {entry['score']}</div>", unsafe_allow_html=True)
    except: st.caption("Leaderboard loading...")
    
    st.divider()
    role = st.selectbox("Switch Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 4. STUDENT PORTAL (RESTORED FORM) ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("📝 Student Registration")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School Name:")
        with c2: name = st.text_input("Student Full Name:")
        
        y_col, e_col, s_col = st.columns(3)
        with y_col: year_choice = st.selectbox("Exam Year", ["ALL YEARS (Mixed)"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True) if not df.empty else ["2024"])
        with e_col: exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Select Subject", MASTER_SUBJECTS)
        
        if st.button("🚀 START EXAM") and school and name:
            filt = (df['subject'].str.upper() == subj) & (df['exam'].str.upper() == exam_type)
            if year_choice != "ALL YEARS (Mixed)": filt &= (df['year'].astype(str) == year_choice)
            quiz_df = df[filt]
            
            if not quiz_df.empty:
                st.session_state.quiz_data = quiz_df.sample(n=min(len(quiz_df), 20)).reset_index(drop=True)
                st.session_state.exam_active, st.session_state.start_time, st.session_state.current_q = True, time.time(), 0
                st.session_state.user_answers = {}
                st.session_state.db_id = f"{school} | {name} | {subj} | {year_choice}"
                st.rerun()
            else: st.warning(f"🚧 No questions found for {subj} {year_choice}.")
    else:
        # EXAM QUESTIONS
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        q = q_df.iloc[curr]
        st.write(f"Question {curr+1} of {len(q_df)}")
        
        if 'passage' in q_df.columns and pd.notnull(q['passage']):
            cl, cr = st.columns([1, 1])
            with cl: st.markdown(f"<div class='passage-box'><b>Passage:</b><br>{q['passage']}</div>", unsafe_allow_html=True)
            with cr:
                st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
                st.session_state.user_answers[curr] = st.radio("Answer:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")
        else:
            st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
            st.session_state.user_answers[curr] = st.radio("Answer:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")

        st.divider()
        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with c2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with c3:
            if st.button("🏁 SUBMIT GRADE"):
                score, script_data = 0, []
                for i, row in q_df.iterrows():
                    u_a = st.session_state.user_answers.get(i, "None")
                    is_correct = str(u_a).strip().upper() == str(row['correct_answer']).strip().upper()
                    if is_correct: score += 1
                    script_data.append({"q": row['question'], "ua": u_a, "ca": row['correct_answer'], "ok": is_correct, "topic": row.get('topic', 'General')})
                
                try:
                    supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(script_data), "total_q": len(q_df)}, on_conflict="name").execute()
                except: pass
                st.session_state.final_score, st.session_state.final_script = score, script_data
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Score: {st.session_state.final_score} / {len(st.session_state.final_script)}")
        st.info(get_remark(st.session_state.final_score, len(st.session_state.final_script)))
        if st.button("Restart"): st.session_state.clear(); st.rerun()

# --- 5. TEACHER PORTAL (RESTORED ANALYSIS) ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher Diagnostic Suite")
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "General")
            
            # CHART
            st.subheader("Performance by Subject")
            fig = px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', color='Subject')
            st.plotly_chart(fig, use_container_width=True)
            
            # AUDIT
            st.subheader("Student Records")
            sel = st.selectbox("Select Student to Audit:", ["-- Select --"] + ld['name'].tolist())
            if sel != "-- Select --":
                row = ld[ld['name'] == sel].iloc[0]
                st.write(f"**Remark:** {get_remark(row['score'], row.get('total_q', 10))}")
                st.dataframe(ld[ld['name'] == sel][['name', 'score']])
        else: st.info("No data yet.")

# --- 6. PARENT PORTAL (RESTORED) ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Parent Portal")
    child = st.text_input("Enter Child's Name:")
    if child:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            res_df = ld[ld['name'].str.contains(child, case=False)]
            if not res_df.empty:
                st.table(res_df[['name', 'score']])
            else: st.warning("No records found.")
