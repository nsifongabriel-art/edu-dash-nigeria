import streamlit as st
import pandas as pd
import time
import json
import plotly.express as px
from supabase import create_client, Client
from docx import Document
from io import BytesIO

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=1)
def load_data():
    try: 
        # Added clear error handling for the data fetch
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return None
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except Exception as e:
        return None

df = load_data()

# --- 2. WORD DOC GENERATOR ---
def create_docx(name, score, total, script):
    doc = Document()
    doc.add_heading('VikidylEdu CBT - Report Card', 0)
    doc.add_paragraph(f"Student: {name}")
    doc.add_paragraph(f"Score: {score} / {total}")
    for i, item in enumerate(script):
        doc.add_heading(f"Question {i+1}", level=2)
        doc.add_paragraph(f"Q: {item.get('q', 'N/A')}")
        status = "✅ CORRECT" if item.get('ok') else "❌ INCORRECT"
        doc.add_paragraph(f"Result: {status} | Correct Answer: {item.get('ca', 'N/A')}")
        doc.add_paragraph(f"Explanation: {item.get('ex', 'N/A')}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def get_remark(score, total):
    pct = (score / total) * 100 if total > 0 else 0
    if pct >= 80: return "🌟 **Outstanding!** Excellent mastery."
    elif pct >= 60: return "👍 **Good Job!** You're doing well."
    elif pct >= 45: return "📚 **Fair Effort.** Review your weak areas."
    else: return "🛠️ **Study Harder.** Focused revision required."

# --- 3. UI STYLE ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; }
    .report-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; margin-bottom: 10px; border: 1px solid #e5e7eb; color: #000; }
    .weak-topic { color: #cf1322; font-weight: bold; background-color: #fff1f0; padding: 2px 5px; border-radius: 4px; }
</style>""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
    if df is None:
        st.error("❌ Database Offline")
    else:
        st.success("✅ Database Online")
    
    try:
        res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        for i, entry in enumerate(res.data):
            n = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
            st.markdown(f"<div class='winner-box'>#{i+1} {n}: {entry['score']}</div>", unsafe_allow_html=True)
    except: pass
    role = st.selectbox("Portal", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 5. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("📝 Student Registration")
        c1, c2 = st.columns(2)
        with c1: sch = st.text_input("School Name:")
        with c2: nm = st.text_input("Full Name:")
        
        cy, ce, cs = st.columns(3)
        with cy: 
            yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True) if df is not None else ["2024"]
            yr = st.selectbox("Exam Year", yrs)
        with ce: exm = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
        with cs: 
            # FIXED: This block now handles cases where data is missing to prevent your specific crash
            if df is not None and 'subject' in df.columns:
                sub_list = sorted(df['subject'].unique().tolist())
            else:
                sub_list = ["Loading..."]
            sub = st.selectbox("Select Subject", sub_list)
        
        # Dynamic Slider: Only for "ALL YEARS"
        num_q = st.slider("Select Question Count", 5, 50, 20) if yr == "ALL YEARS" else 50
        
        if st.button("🚀 START EXAM"):
            if not sch or not nm or sub == "Loading...":
                st.error("Please fill all fields and ensure data is loaded.")
            else:
                filt = (df['subject'].str.upper() == sub.upper()) & (df['exam'].str.upper() == exm.upper())
                if yr != "ALL YEARS": filt &= (df['year'].astype(str) == yr)
                q_df = df[filt]
                if not q_df.empty:
                    limit = min(len(q_df), num_q)
                    st.session_state.quiz_data = q_df.sample(n=limit).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "start_time": time.time(), "current_q": 0, "user_answers": {}, "db_id": f"{sch} | {nm} | {sub} | {yr}"})
                    st.rerun()
                else: st.warning("No questions found for this selection.")

    elif 'exam_active' in st.session_state:
        # --- ACTIVE EXAM ---
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.subheader(f"⏱️ Time: {rem//60:02d}:{rem%60:02d}")
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        row = q_df.iloc[curr]

        if 'passage' in row and pd.notna(row['passage']) and str(row['passage']).strip() != "":
            with st.expander("📖 Passage / Instructions", expanded=True):
                st.markdown(f"*{row['passage']}*")

        st.markdown(f"### Q{curr+1}: {row['question']}")
        st.session_state.user_answers[curr] = st.radio("Answer:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with c2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with c3:
            if st.button("🏁 FINISH"):
                score, script = 0, []
                for i, r in q_df.iterrows():
                    ans = st.session_state.user_answers.get(i, "None")
                    cor = str(r['correct_answer']).strip().upper()
                    ok = str(ans).strip().upper() == cor
                    if ok: score += 1
                    script.append({"q": r['question'], "ua": ans, "ca": cor, "ok": ok, "ex": r.get('explanation', 'N/A'), "topic": r.get('topic', 'General Revision')})
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(script), "total_q": len(q_df)}, on_conflict="name").execute()
                st.session_state.update({"final_score": score, "final_script": script})
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.balloons()
        score, total = st.session_state.final_score, len(st.session_state.final_script)
        st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>Score: {score} / {total}</h1>", unsafe_allow_html=True)
        st.info(get_remark(score, total))

        t1, t2, t3 = st.tabs(["📊 Performance", "🔍 Corrections", "📥 Result Doc"])
        with t1:
            s_df = pd.DataFrame(st.session_state.final_script)
            weaks = s_df[s_df['ok'] == False]['topic'].unique()
            if len(weaks) > 0:
                st.warning("⚠️ **Weak Topics:** Review these areas:")
                for w in weaks: st.markdown(f"- <span class='weak-topic'>{w}</span>", unsafe_allow_html=True)
            st.plotly_chart(px.pie(values=[score, total-score], names=['Correct', 'Incorrect'], hole=0.5, color_discrete_sequence=['#28a745', '#dc3545']))
        with t2:
            for i, item in enumerate(st.session_state.final_script):
                with st.expander(f"{'✅' if item['ok'] else '❌'} Q{i+1}"):
                    st.write(f"**Q:** {item['q']}")
                    st.write(f"**Correct Answer:** {item['ca']}")
                    st.info(f"💡 {item['ex']}")
        with t3:
            docx = create_docx(st.session_state.db_id, score, total, st.session_state.final_script)
            st.download_button("📥 Get Word Report", data=docx, file_name="VikidylEdu_Result.docx")
            if st.button("New Exam"): st.session_state.clear(); st.rerun()

# Teacher and Parent Portals remain available but streamlined for speed
elif role == "👨‍🏫 Teacher":
    if st.text_input("Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data: st.table(pd.DataFrame(res.data)[['name', 'score']])

elif role == "👨‍👩‍👧 Parent":
    nm_in = st.text_input("Student Name:")
    if st.button("Find"):
        res = supabase.table("leaderboard").select("*").execute()
        match = [r for r in res.data if nm_in.lower() in r['name'].lower()]
        if match:
            for m in match: st.write(f"**{m['name']}**: {m['score']}")
