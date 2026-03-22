import streamlit as st
import pandas as pd
import time
import random
import json
import plotly.express as px
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

MASTER_SUBJECTS = [
    "MATHEMATICS", "ENGLISH LANGUAGE", "BIOLOGY", "PHYSICS", "CHEMISTRY", 
    "ECONOMICS", "GOVERNMENT", "LITERATURE IN ENGLISH", "CIVIC EDUCATION",
    "COMMERCE", "AGRICULTURAL SCIENCE", "GEOGRAPHY", "CRS", "IRS", "HISTORY", "COMPUTER STUDIES"
]

@st.cache_data(ttl=1)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        for col in ['exam', 'subject', 'year', 'topic']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().upper()
        return data
    except: return pd.DataFrame()

df = load_data()

def get_remark(score, total):
    if total <= 0: return "No Data"
    pct = (score / total) * 100
    if pct >= 75: return "🌟 Excellent! Brilliant performance."
    elif pct >= 50: return "👍 Good job. Keep practicing."
    else: return "📚 Needs improvement."

# --- 2. UI ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .passage-box { background-color: #F8FAFC; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; height: 450px; overflow-y: auto; font-size: 18px; color: #1E293B; line-height: 1.6; }
    .question-box { background-color: #ffffff; padding: 25px; border-radius: 12px; border-left: 10px solid #1E3A8A; font-size: 20px; border: 1px solid #ddd; color: #000; }
    .timer-text { font-size: 28px; font-weight: bold; color: #D32F2F; text-align: center; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=50)
    st.title("VikidylEdu")
    role = st.selectbox("Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("CBT Portal")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School:")
        with c2: name = st.text_input("Full Name:")
        
        y_col, e_col, s_col = st.columns(3)
        sheet_years = sorted(df['year'].unique().tolist(), reverse=True) if not df.empty else ["2024"]
        with y_col: year_choice = st.selectbox("Year", ["ALL YEARS (Mixed)"] + sheet_years)
        with e_col: exam_type = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", MASTER_SUBJECTS)
        
        q_count = 0
        if year_choice == "ALL YEARS (Mixed)":
            q_count = st.select_slider("Questions:", options=[20, 50, 100])

        if st.button("🚀 START EXAM") and school and name:
            filt = (df['exam'] == exam_type) & (df['subject'] == subj)
            if year_choice != "ALL YEARS (Mixed)": filt &= (df['year'] == year_choice)
            quiz_df = df[filt]
            
            if not quiz_df.empty:
                limit = q_count if q_count > 0 else len(quiz_df)
                st.session_state.quiz_data = quiz_df.sample(n=min(len(quiz_df), limit)).reset_index(drop=True)
                st.session_state.exam_active, st.session_state.start_time = True, time.time()
                st.session_state.current_q, st.session_state.user_answers = 0, {}
                st.session_state.db_id = f"{school} | {name} | {subj} | {year_choice}"
                st.rerun()
            else: st.warning(f"🚧 {subj} ({year_choice}) is currently unavailable.")
    else:
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.markdown(f"<div class='timer-text'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        q = q_df.iloc[curr]
        
        has_passage = 'passage' in q_df.columns and pd.notnull(q['passage'])
        
        if has_passage:
            col_l, col_r = st.columns([1, 1])
            with col_l: st.markdown(f"<div class='passage-box'><b>Passage:</b><br>{q['passage']}</div>", unsafe_allow_html=True)
            with col_r:
                st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
                st.session_state.user_answers[curr] = st.radio("Answer:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")
        else:
            st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
            st.session_state.user_answers[curr] = st.radio("Answer:", [q['a'], q['b'], q['c'], q['d']], key=f"q_{curr}")
        
        st.divider()
        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Previous") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with c2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with c3:
            if st.button("🏁 FINISH"):
                score, script_data = 0, []
                c_col = 'correct_answer' if 'correct_answer' in df.columns else 'correct_answee'
                for i, row in q_df.iterrows():
                    u_a = st.session_state.user_answers.get(i, "No Answer")
                    c_a = str(row[c_col]).strip().upper()
                    is_correct = str(u_a).strip().upper() == c_a
                    if is_correct: score += 1
                    script_data.append({"q": row['question'], "ua": u_a, "ca": c_a, "ok": is_correct, "topic": row.get('topic', 'General')})
                
                try:
                    supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(script_data), "total_q": len(q_df)}, on_conflict="name").execute()
                except: pass
                st.session_state.final_score, st.session_state.final_script = score, script_data
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Final Score: {st.session_state.final_score} / {len(st.session_state.final_script)}")
        st.button("Restart", on_click=lambda: st.session_state.clear())

# --- 4. TEACHER DIAGNOSTICS ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            t1, t2 = st.tabs(["📊 Subject Trends", "🔍 Student Topic Audit"])
            
            with t1:
                ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if len(x.split('|'))>2 else "Unknown")
                fig = px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', title="Subject Averages")
                st.plotly_chart(fig)
            
            with t2:
                selected = st.selectbox("Select Student:", ["-- Select --"] + ld['name'].tolist())
                if selected != "-- Select --":
                    row = ld[ld['name'] == selected].iloc[0]
                    script = json.loads(row['script'])
                    sd = pd.DataFrame(script)
                    # Topic Analysis
                    topic_perf = sd.groupby('topic')['ok'].mean().reset_index()
                    topic_perf['Percentage'] = topic_perf['ok'] * 100
                    st.write(f"### Topic Breakdown for {selected}")
                    st.plotly_chart(px.bar(topic_perf, x='topic', y='Percentage', color='topic', range_y=[0,100]))
                    
                    for i, item in enumerate(script):
                        with st.expander(f"Q{i+1} ({item['topic']})"):
                            st.write(f"**Q:** {item['q']}")
                            st.write(f"**Ans:** {item['ua']} | **Correct:** {item['ca']}")

elif role == "👨‍👩‍👧 Parent":
    n = st.text_input("Child Name:")
    if n:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            st.table(ld[ld['name'].str.contains(n, case=False)][['name', 'score']])
