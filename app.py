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
    if pct >= 75: return "🌟 Excellent! Brilliant performance."
    elif pct >= 50: return "👍 Good job. Keep practicing."
    else: return "📚 Needs improvement. Review explanations."

# --- 2. UI STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; }
    .passage-box { background-color: #f8fafc; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; border: 1px solid #cbd5e1; color: #000; }
    .question-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #1E3A8A; font-size: 20px; border: 1px solid #e5e7eb; color: #000; }
    .timer-text { font-size: 30px; font-weight: bold; color: #D32F2F; text-align: center; }
</style>""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
    st.markdown("### 🏆 Top Performers")
    try:
        ld_res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        if ld_res.data:
            for i, entry in enumerate(ld_res.data):
                short_name = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
                st.markdown(f"<div class='winner-box'>#{i+1} {short_name}: {entry['score']}</div>", unsafe_allow_html=True)
    except: pass
    
    st.divider()
    role = st.selectbox("Switch Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("📝 Registration")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School Name:")
        with c2: name = st.text_input("Full Name (First & Surname):")
        
        y_col, e_col, s_col = st.columns(3)
        with y_col: year_choice = st.selectbox("Year", ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True) if not df.empty else ["2024"])
        with e_col: exam_type = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", MASTER_SUBJECTS)
        
        if st.button("🚀 START"):
            if not school or len(name.strip().split()) < 2:
                st.error("Please enter School and Full Name (First & Surname).")
            else:
                filt = (df['subject'].str.upper() == subj) & (df['exam'].str.upper() == exam_type)
                if year_choice != "ALL YEARS": filt &= (df['year'].astype(str) == year_choice)
                quiz_df = df[filt]
                if not quiz_df.empty:
                    st.session_state.quiz_data = quiz_df.sample(n=min(len(quiz_df), 20)).reset_index(drop=True)
                    st.session_state.exam_active, st.session_state.start_time, st.session_state.current_q = True, time.time(), 0
                    st.session_state.user_answers = {}
                    st.session_state.db_id = f"{school} | {name} | {subj} | {year_choice}"
                    st.rerun()
                else: st.warning("Subject not yet uploaded.")
    else:
        # TIMER
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.markdown(f"<div class='timer-text'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        if rem <= 0: st.warning("Time up! Please submit."); 

        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        q = q_df.iloc[curr]
        
        if 'passage' in q_df.columns and pd.notnull(q['passage']):
            cl, cr = st.columns([1, 1])
            with cl: st.markdown(f"<div class='passage-box'>{q['passage']}</div>", unsafe_allow_html=True)
            with cr:
                st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
                st.session_state.user_answers[curr] = st.radio("Select:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")
        else:
            st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
            st.session_state.user_answers[curr] = st.radio("Select:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")

        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with c2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with c3:
            if st.button("🏁 SUBMIT"):
                score, script = 0, []
                for i, row in q_df.iterrows():
                    ua = st.session_state.user_answers.get(i, "None")
                    ca = str(row['correct_answer']).strip().upper()
                    ok = str(ua).strip().upper() == ca
                    if ok: score += 1
                    script.append({"q": row['question'], "ua": ua, "ca": ca, "ok": ok, "ex": row.get('explanation', 'No explanation provided.'), "topic": row.get('topic', 'General')})
                
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(script), "total_q": len(q_df)}, on_conflict="name").execute()
                st.session_state.final_score, st.session_state.final_script = score, script
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Score: {st.session_state.final_score} / {len(st.session_state.final_script)}")
        st.info(get_remark(st.session_state.final_score, len(st.session_state.final_script)))
        with st.expander("🔍 View Corrections & Explanations"):
            for item in st.session_state.final_script:
                color = "green" if item['ok'] else "red"
                st.markdown(f"<p style='color:{color}'><b>Q: {item['q']}</b></p>", unsafe_allow_html=True)
                st.write(f"Your Answer: {item['ua']} | Correct: {item['ca']}")
                st.write(f"💡 {item['ex']}")
                st.divider()
        if st.button("Restart"): st.session_state.clear(); st.rerun()

# --- 5. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "N/A")
            
            st.subheader("📊 Subject Analysis")
            st.plotly_chart(px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', color='Subject'))
            
            st.subheader("🔍 Student Audit & Download")
            sel = st.selectbox("Select Student:", ["-- Select --"] + ld['name'].tolist())
            if sel != "-- Select --":
                row = ld[ld['name'] == sel].iloc[0]
                script_list = json.loads(row['script'])
                st.write(f"**Score:** {row['score']} | **Remark:** {get_remark(row['score'], len(script_list))}")
                st.download_button("📥 Download Child's Script", data=json.dumps(script_list, indent=2), file_name=f"{sel}_script.json")
                st.json(script_list)

# --- 6. PARENT PORTAL ---
elif role == "👨‍👩‍👧 Parent":
    p_school = st.text_input("Child's School:")
    p_name = st.text_input("Child's Full Name:")
    if st.button("Check Result") and p_school and p_name:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            match = ld[(ld['name'].str.contains(p_school, case=False)) & (ld['name'].str.contains(p_name, case=False))]
            if not match.empty:
                st.table(match[['name', 'score']])
            else: st.error("No record found.")
