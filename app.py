import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=1) # Set to 1 second so your new JAMB questions show up instantly
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        # Clean the actual data inside the columns too
        for col in ['exam', 'subject', 'year']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().str.upper()
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. LOGIC HELPERS ---
def get_remark(score_pct):
    if score_pct >= 75: return "🌟 Excellent! Brilliant performance."
    elif score_pct >= 50: return "👍 Good job. Keep practicing."
    else: return "📚 Review the passages and try again."

def clean_lb(data):
    if not data: return pd.DataFrame()
    ld = pd.DataFrame(data)
    def parse_name(val):
        parts = val.split('|')
        return pd.Series([parts[1].strip() if len(parts)>1 else "N/A", parts[0].strip() if len(parts)>0 else "N/A", f"{parts[2].strip() if len(parts)>2 else ''} ({parts[3].strip() if len(parts)>3 else ''})"])
    ld[['Student', 'School', 'Details']] = ld['name'].apply(parse_name)
    return ld[['Student', 'School', 'Details', 'score']]

# --- 3. UI ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("<style>.timer-text { font-size: 30px; font-weight: bold; color: red; text-align: center; }</style>", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu")
    role = st.selectbox("Role", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- 5. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state:
        # REGISTRATION
        c1, c2 = st.columns(2)
        with c1: school = st.text_input("School:")
        with c2: name = st.text_input("Full Name:")
        
        y_col, e_col, s_col = st.columns(3)
        with y_col: year = st.selectbox("Year", ["2020", "2021", "2022", "2023", "2024", "2025", "2026"])
        with e_col: exam = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with s_col: subj = st.selectbox("Subject", ["MATHEMATICS", "ENGLISH", "BIOLOGY", "PHYSICS", "CHEMISTRY"])

        if st.button("🚀 START EXAM"):
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
        
        # SEARCH LOGIC (Fuzzy Match)
        quiz_df = df[
            (df['exam'] == st.session_state.s_exam) & 
            (df['subject'] == st.session_state.s_subj) & 
            (df['year'] == st.session_state.s_year)
        ]
        
        if not quiz_df.empty:
            curr = st.session_state.current_q
            total = len(quiz_df)
            q_data = quiz_df.iloc[curr]
            
            st.subheader(f"Question {curr+1} of {total}")
            
            # PASSAGE SUPPORT: If text is long, use a text area
            st.text_area("Read the Question/Passage below:", value=q_data['question'], height=250, disabled=True)
            
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
                if st.button("🏁 FINISH EXAM"):
                    score = 0
                    for k, v in st.session_state.user_answers.items():
                        if str(v).strip().upper() == str(quiz_df.iloc[k]['correct_answer']).strip().upper(): score += 1
                    supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}, on_conflict="name").execute()
                    st.session_state.final_score = score
                    st.session_state.finished_data = quiz_df.to_dict('records')
                    del st.session_state['exam_active']; st.rerun()
        else:
            st.error(f"No questions found for {st.session_state.s_exam} {st.session_state.s_subj} {st.session_state.s_year}")
            if st.button("Return"): st.session_state.clear(); st.rerun()

    if 'final_score' in st.session_state:
        st.success(f"Exam Finished! Score: {st.session_state.final_score}")
        with st.expander("Review Explanations"):
            for i, r in enumerate(st.session_state.finished_data):
                st.write(f"**Q{i+1}:** {r['question']}")
                st.write(f"✅ Correct: {r['correct_answer']}")
        if st.button("New Exam"): st.session_state.clear(); st.rerun()

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

st.markdown("---")
st.caption("VikidylEdu Centre © 2026")
