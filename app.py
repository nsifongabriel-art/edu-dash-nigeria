import streamlit as st
import pandas as pd
import time
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
        # Standardize for searching
        for col in ['exam', 'subject', 'year']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().str.upper()
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. HIGH CONTRAST STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")

st.markdown("""
    <style>
    /* Make the question text bold, large, and dark black */
    .question-box {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        border-left: 10px solid #1E3A8A;
        font-size: 22px !important;
        color: #000000 !important;
        line-height: 1.6;
        margin-bottom: 20px;
    }
    .stRadio label { font-size: 18px !important; color: #1E3A8A !important; font-weight: bold; }
    .timer-text { font-size: 32px; font-weight: bold; color: #D32F2F; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC HELPERS ---
def clean_lb(data):
    if not data: return pd.DataFrame()
    ld = pd.DataFrame(data)
    def parse_name(val):
        parts = val.split('|')
        return pd.Series([parts[1].strip() if len(parts)>1 else "N/A", parts[0].strip() if len(parts)>0 else "N/A", f"{parts[2].strip() if len(parts)>2 else ''} ({parts[3].strip() if len(parts)>3 else ''})"])
    ld[['Student', 'School', 'Details']] = ld['name'].apply(parse_name)
    return ld[['Student', 'School', 'Details', 'score']]

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=60)
    st.title("VikidylEdu")
    role = st.selectbox("Switch Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 5. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        st.header("Exam Registration")
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School:")
        with c2: name = st.text_input("Full Name:")
        
        y_col, e_col, s_col = st.columns(3)
        with y_col: year = st.selectbox("Year", ["2020", "2021", "2022", "2023", "2024", "2025", "2026"])
        with e_col: exam = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", ["MATHEMATICS", "ENGLISH", "BIOLOGY", "PHYSICS", "CHEMISTRY"])

        if st.button("🚀 START EXAM") and school and name:
            st.session_state.exam_active = True
            st.session_state.start_time = time.time()
            st.session_state.current_q = 0
            st.session_state.user_answers = {}
            st.session_state.db_id = f"{school} | {name} | {subj} | {year}"
            st.session_state.s_exam = exam.strip().upper()
            st.session_state.s_subj = subj.strip().upper()
            st.session_state.s_year = year.strip().upper()
            st.rerun()
    else:
        # TIMER
        rem = max(0, 1800 - int(time.time() - st.session_state.start_time))
        st.markdown(f"<div class='timer-text'>⏱️ {rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
        
        # FILTER DATA
        quiz_df = df[(df['exam'] == st.session_state.s_exam) & 
                     (df['subject'] == st.session_state.s_subj) & 
                     (df['year'] == st.session_state.s_year)]
        
        if not quiz_df.empty:
            curr = st.session_state.current_q
            total = len(quiz_df)
            q_data = quiz_df.iloc[curr]
            
            st.subheader(f"Question {curr+1} of {total}")
            
            # --- HIGH CONTRAST QUESTION BOX ---
            st.markdown(f"""<div class="question-box">{q_data['question']}</div>""", unsafe_allow_html=True)
            
            opts = [str(q_data['a']), str(q_data['b']), str(q_data['c']), str(q_data['d'])]
            saved = st.session_state.user_answers.get(curr, None)
            choice = st.radio("Select Answer:", opts, index=opts.index(saved) if saved in opts else 0)
            st.session_state.user_answers[curr] = choice
            
            c1, c2, c3 = st.columns([1,1,2])
            with c1: 
                if st.button("⬅️ Prev") and curr > 0: st.session_state.current_q -= 1; st.rerun()
            with c2: 
                if st.button("Next ➡️") and curr < total - 1: st.session_state.current_q += 1; st.rerun()
            with c3:
                if st.button("🏁 SUBMIT EXAM"):
                    score = 0
                    c_col = next((c for c in ['correct_answer', 'correct_answee'] if c in df.columns), 'correct_answer')
                    for k, v in st.session_state.user_answers.items():
                        if str(v).strip().upper() == str(quiz_df.iloc[k][c_col]).strip().upper(): score += 1
                    supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}, on_conflict="name").execute()
                    st.session_state.final_score = score
                    st.session_state.finished_data = quiz_df.to_dict('records')
                    st.session_state.final_user_ans = st.session_state.user_answers.copy()
                    del st.session_state['exam_active']; st.rerun()
        else:
            st.error("No questions found.")
            if st.button("Return"): st.session_state.clear(); st.rerun()

    # --- REVIEW SECTION WITH EXPLANATIONS ---
    if 'final_score' in st.session_state:
        st.success(f"Final Score: {st.session_state.final_score}")
        st.header("📝 Post-Exam Review")
        
        for i, r in enumerate(st.session_state.finished_data):
            user_ans = st.session_state.final_user_ans.get(i, "No Answer")
            correct_ans = r.get('correct_answer', 'Check Sheet')
            
            with st.expander(f"Question {i+1}: {r['question'][:50]}..."):
                st.write(f"**Full Question:** {r['question']}")
                st.write(f"**Your Answer:** {user_ans}")
                st.write(f"**Correct Answer:** :green[{correct_ans}]")
                
                # Show Explanation if it exists in the Google Sheet
                expl = r.get('explanation', 'No explanation provided for this question.')
                st.info(f"💡 **Explanation:** {expl}")
        
        if st.button("Start New Exam"): st.session_state.clear(); st.rerun()

elif role == "👨‍🏫 Teacher":
    if st.text_input("Key:", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data: st.dataframe(clean_lb(res.data))

elif role == "👨‍👩‍👧 Parent":
    n = st.text_input("Child Name:")
    if n:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            ld = clean_lb(res.data)
            st.table(ld[ld['Student'].str.contains(n, case=False)])

st.caption("VikidylEdu Centre © 2026")
