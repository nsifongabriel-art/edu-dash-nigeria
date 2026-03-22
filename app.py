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

# --- 2. WORD DOC GENERATOR ---
def create_docx(name, score, total, script):
    doc = Document()
    doc.add_heading('VikidylEdu CBT - Detailed Correction', 0)
    doc.add_paragraph(f"Student Record: {name}")
    doc.add_paragraph(f"Final Score: {score} / {total}")
    
    for i, item in enumerate(script):
        doc.add_heading(f"Question {i+1}", level=2)
        doc.add_paragraph(f"Q: {item.get('q', 'N/A')}")
        res = "✅ CORRECT" if item.get('ok') else "❌ INCORRECT"
        doc.add_paragraph(f"Result: {res}")
        doc.add_paragraph(f"Correct Answer: {item.get('ca', 'N/A')}")
        doc.add_paragraph(f"Explanation: {item.get('ex', 'No explanation available.')}")
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def get_remark(score, total):
    if total <= 0: return ""
    pct = (score / total) * 100
    if pct >= 80: return "🌟 **Remark:** Outstanding! Master-level performance."
    elif pct >= 60: return "👍 **Remark:** Good job! A few more revisions and you'll hit 100%."
    elif pct >= 45: return "📚 **Remark:** Fair effort. Please review the corrections below."
    else: return "🛠️ **Remark:** Don't be discouraged. Focus your study on the missed topics."

# --- 3. UI STYLE ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; }
    .report-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; margin-bottom: 10px; border: 1px solid #e5e7eb; color: #000; }
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
    if 'exam_active' not in st.session_state:
        st.header("📝 Registration")
        c1, c2 = st.columns(2)
        with c1: sch = st.text_input("School Name:")
        with c2: nm = st.text_input("Full Name (First & Surname):")
        
        cy, ce, cs = st.columns(3)
        with cy: 
            yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True) if not df.empty else ["2024"]
            yr = st.selectbox("Year", yrs)
        with ce: exm = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
        with cs: sub = st.selectbox("Subject", sorted(df['subject'].unique().tolist()) if not df.empty else ["ENGLISH"])
        
        num_q = st.slider("Number of Questions", 5, 50, 20)
        
        if st.button("🚀 START"):
            if not sch or len(nm.strip().split()) < 2:
                st.error("Enter School and Full Name.")
            else:
                filt = (df['subject'].str.upper() == sub.upper()) & (df['exam'].str.upper() == exm.upper())
                if yr != "ALL YEARS": filt &= (df['year'].astype(str) == yr)
                q_df = df[filt]
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), num_q)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "start_time": time.time(), "current_q": 0, "user_answers": {}, "db_id": f"{sch} | {nm} | {sub} | {yr}"})
                    st.rerun()
                else: st.warning("No questions found.")
    else:
        # EXAM TIMER
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.subheader(f"⏱️ {rem//60:02d}:{rem%60:02d}")
        
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        row = q_df.iloc[curr]
        st.markdown(f"### Q{curr+1}: {row['question']}")
        st.session_state.user_answers[curr] = st.radio("Choose:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        col1, col2, col3 = st.columns([1,1,2])
        with col1: 
            if st.button("⬅️ Previous") and curr > 0: st.session_state.current_q -= 1; st.rerun()
        with col2:
            if st.button("Next ➡️") and curr < len(q_df)-1: st.session_state.current_q += 1; st.rerun()
        with col3:
            if st.button("🏁 FINISH & GRADE"):
                score, script = 0, []
                for i, r in q_df.iterrows():
                    ans = st.session_state.user_answers.get(i, "None")
                    cor = str(r['correct_answer']).strip().upper()
                    ok = str(ans).strip().upper() == cor
                    if ok: score += 1
                    script.append({"q": r['question'], "ua": ans, "ca": cor, "ok": ok, "ex": r.get('explanation', 'N/A')})
                supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score, "script": json.dumps(script), "total_q": len(q_df)}, on_conflict="name").execute()
                st.session_state.final_score, st.session_state.final_script = score, script
                del st.session_state['exam_active']; st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Score: {st.session_state.final_score} / {len(st.session_state.final_script)}")
        st.info(get_remark(st.session_state.final_score, len(st.session_state.final_script)))
        
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            docx_data = create_docx(st.session_state.db_id, st.session_state.final_score, len(st.session_state.final_script), st.session_state.final_script)
            st.download_button("📥 Detailed Report (Word)", data=docx_data, file_name="Report.docx")
        with c_dl2:
            st.download_button("📥 Raw Data (CSV)", data=pd.DataFrame(st.session_state.final_script).to_csv(index=False), file_name="Result.csv")
            
        with st.expander("🔍 Detailed Correction"):
            for item in st.session_state.final_script:
                st.markdown(f"<div class='report-card'><b>{'✅' if item['ok'] else '❌'} {item['q']}</b><br>Correct: {item['ca']}<br><i>💡 {item['ex']}</i></div>", unsafe_allow_html=True)
        if st.button("New Exam"): st.session_state.clear(); st.rerun()

# --- 6. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Access Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "N/A")
            st.plotly_chart(px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', color='Subject'))
            
            sel = st.selectbox("Student Audit:", ["-- Select --"] + ld['name'].tolist())
            if sel != "-- Select --":
                row = ld[ld['name'] == sel].iloc[0]
                scr = json.loads(row['script'])
                st.write(get_remark(row['score'], len(scr)))
                st.download_button("📥 Download Word Report", data=create_docx(row['name'], row['score'], len(scr), scr), file_name=f"{sel}.docx")
                st.download_button("📥 Download CSV", data=pd.DataFrame(scr).to_csv(index=False), file_name=f"{sel}.csv")
        else: st.info("No records.")

# --- 7. PARENT PORTAL ---
elif role == "👨‍👩‍👧 Parent":
    s_in = st.text_input("School:")
    n_in = st.text_input("Child Name:")
    if st.button("Find Result") and s_in and n_in:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = pd.DataFrame(res.data)
            match = ld[(ld['name'].str.contains(s_in, case=False)) & (ld['name'].str.contains(n_in, case=False))]
            if not match.empty:
                st.table(match[['name', 'score']])
                for _, r in match.iterrows():
                    p_scr = json.loads(r['script'])
                    st.write(get_remark(r['score'], len(p_scr)))
                    st.download_button(f"📥 Get Report for {r['name'].split('|')[1]}", data=create_docx(r['name'], r['score'], len(p_scr), p_scr), file_name="Report.docx")
            else: st.error("No record found.")
