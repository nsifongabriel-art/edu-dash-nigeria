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
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. UTILITIES ---
def create_docx(name, score, total, script):
    doc = Document()
    doc.add_heading('VikidylEdu CBT - Official Result', 0)
    doc.add_paragraph(f"Student: {name}")
    doc.add_paragraph(f"Score: {score} / {total} ({int(score/total*100)}%)")
    for i, item in enumerate(script):
        doc.add_heading(f"Q{i+1}", level=2)
        status = "CORRECT" if item.get('ok') else "INCORRECT"
        doc.add_paragraph(f"Result: {status}")
        doc.add_paragraph(f"Your Ans: {item.get('ua')} | Correct Ans: {item.get('ca')}")
        doc.add_paragraph(f"Explanation: {item.get('ex', 'N/A')}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def get_remark(score, total):
    pct = (score / total) * 100
    if pct >= 80: return "🌟 **Outstanding!** You have mastered this subject. Keep maintaining this standard."
    elif pct >= 60: return "👍 **Good Job!** You have a solid grasp, but check the corrections for minor gaps."
    elif pct >= 45: return "📚 **Fair Effort.** You passed, but several topics need urgent review."
    else: return "🛠️ **Revision Needed.** Please study the explanations carefully and retake the test."

# --- 3. UI STYLE ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; }
    .report-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; margin-bottom: 10px; border: 1px solid #e5e7eb; color: #000; }
    .weak-topic { background-color: #fff1f0; border: 1px solid #ffa39e; padding: 5px; border-radius: 5px; color: #cf1322; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
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
        st.header("📝 Start New Exam")
        c1, c2 = st.columns(2)
        with c1: sch = st.text_input("School:")
        with c2: nm = st.text_input("Full Name:")
        cy, ce, cs = st.columns(3)
        with cy: 
            yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True) if not df.empty else ["2024"]
            yr = st.selectbox("Year", yrs)
        with ce: exm = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with cs: 
            sub_list = sorted(df['subject'].unique().tolist()) if not df.empty else ["No Data"]
            sub = st.selectbox("Subject", sub_list)
        
        num_q = st.slider("Questions", 5, 50, 20) if yr == "ALL YEARS" else 50
        
        if st.button("🚀 START"):
            if not sch or len(nm.strip().split()) < 2: st.error("Enter School and Full Name.")
            else:
                filt = (df['subject'].str.upper() == sub.upper()) & (df['exam'].str.upper() == exm.upper())
                if yr != "ALL YEARS": filt &= (df['year'].astype(str) == yr)
                q_df = df[filt]
                if not q_df.empty:
                    limit = min(len(q_df), num_q)
                    st.session_state.quiz_data = q_df.sample(n=limit).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "start_time": time.time(), "current_q": 0, "user_answers": {}, "db_id": f"{sch} | {nm} | {sub} | {yr}"})
                    st.rerun()
                else: st.warning("No questions found.")
    
    elif 'exam_active' in st.session_state:
        # --- ACTIVE EXAM ---
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.subheader(f"⏱️ {rem//60:02d}:{rem%60:02d}")
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        row = q_df.iloc[curr]

        if 'passage' in row and pd.notna(row['passage']) and str(row['passage']).strip() != "":
            with st.expander("📖 Passage / Instructions", expanded=True):
                st.markdown(f"*{row['passage']}*")

        st.markdown(f"### Q{curr+1}: {row['question']}")
        st.session_state.user_answers[curr] = st.radio("Choose:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        c1, c2, c3 = st.columns([1,1,2])
        with c1: 
            if st.button("⬅️ Back") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with col2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with col3:
            if st.button("🏁 FINISH"):
                score, script = 0, []
                for i, r in q_df.iterrows():
                    ans = st.session_state.user_answers.get(i, "None")
                    cor = str(r['correct_answer']).strip().upper()
                    ok = str(ans).strip().upper() == cor
                    if ok: score += 1
                    # Capture topic/category if available in your sheet
                    topic = r.get('topic', 'General')
                    script.append({"q": r['question'], "ua": ans, "ca": cor, "ok": ok, "ex": r.get('explanation', 'N/A'), "topic": topic})
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(script), "total_q": len(q_df)}, on_conflict="name").execute()
                st.session_state.update({"final_score": score, "final_script": script})
                del st.session_state['exam_active']; st.rerun()

    # --- RESULT PHASE (THE NEW ANALYSIS ENGINE) ---
    if 'final_score' in st.session_state:
        score = st.session_state.final_score
        total = len(st.session_state.final_script)
        
        st.balloons()
        st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>Score: {score} / {total}</h1>", unsafe_allow_html=True)
        st.info(get_remark(score, total))

        tab1, tab2, tab3 = st.tabs(["📊 Performance Analysis", "🔍 Corrections & Explanations", "📥 Downloads"])

        with tab1:
            st.subheader("Analysis & Tips")
            # Calculate Weak Topics
            script_df = pd.DataFrame(st.session_state.final_script)
            weak_topics = script_df[script_df['ok'] == False]['topic'].unique()
            
            if len(weak_topics) > 0:
                st.warning("⚠️ **Focus Areas:** You struggled with these topics. Give them extra attention:")
                for t in weak_topics:
                    st.markdown(f"- <span class='weak-topic'>{t}</span>", unsafe_allow_html=True)
            else:
                st.success("🌟 Perfect score! You have no weak topics in this set.")
            
            # Simple Chart
            fig = px.pie(values=[score, total-score], names=['Correct', 'Incorrect'], color_discrete_sequence=['#28a745', '#dc3545'], hole=0.4)
            st.plotly_chart(fig)

        with tab2:
            st.subheader("Step-by-Step Corrections")
            for i, item in enumerate(st.session_state.final_script):
                status_color = "green" if item['ok'] else "red"
                with st.expander(f"{'✅' if item['ok'] else '❌'} Question {i+1}"):
                    st.write(f"**Q:** {item['q']}")
                    st.markdown(f"**Your Answer:** {item['ua']}")
                    st.markdown(f"**Correct Answer:** <span style='color:green; font-weight:bold;'>{item['ca']}</span>", unsafe_allow_html=True)
                    st.info(f"💡 **Explanation:** {item['ex']}")

        with tab3:
            st.subheader("Get Your Official Result")
            docx_data = create_docx(st.session_state.db_id, score, total, st.session_state.final_script)
            st.download_button("📥 Download Result (Word Doc)", data=docx_data, file_name="VikidylEdu_Result.docx")
            if st.button("🔄 Take Another Exam"):
                st.session_state.clear()
                st.rerun()

# [Teacher and Parent Portals remain the same as previous corrected version]
