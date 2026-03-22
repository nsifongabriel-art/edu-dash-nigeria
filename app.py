import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=2)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

# --- 2. UI CONFIG ---
st.set_page_config(page_title="VikidylEdu CBT Portal", page_icon="🇳🇬", layout="wide")
st.markdown("""<style>
    .stButton>button { border-radius: 8px; width: 100%; font-weight: bold; }
    .timer-text { font-size: 26px; font-weight: bold; color: #D32F2F; text-align: center; background: #FFEBEE; padding: 10px; border-radius: 10px; border: 2px solid #D32F2F; }
    .created-by { text-align: center; color: #1E3A8A; padding: 20px; font-weight: bold; border-top: 2px solid #EEE; margin-top: 40px;}
</style>""", unsafe_allow_html=True)

# --- 3. LOGIC HELPERS ---
def clean_lb(data):
    if not data: return pd.DataFrame()
    ld = pd.DataFrame(data)
    def parse_name(val):
        parts = val.split('|')
        sch = parts[0].strip() if len(parts) > 0 else "N/A"
        nam = parts[1].strip() if len(parts) > 1 else "N/A"
        dtl = f"{parts[2].strip() if len(parts) > 2 else ''} ({parts[3].strip() if len(parts) > 3 else ''})"
        return pd.Series([nam, sch, dtl])
    
    ld[['Student', 'School', 'Exam Details']] = ld['name'].apply(parse_name)
    return ld[['Student', 'School', 'Exam Details', 'score']].sort_values(by="score", ascending=False)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=60)
    st.title("VikidylEdu")
    role = st.selectbox("Switch User Role", ["✍️ Student Portal", "👨‍🏫 Teacher Suite", "👨‍👩‍👧 Parent Center"])
    st.divider()
    st.caption("Developed by: **Ufford I.I.**\nVikidylEdu Centre © 2026")

# --- 5. STUDENT PORTAL ---
if role == "✍️ Student Portal":
    t1, t2 = st.tabs(["📝 CBT Exam", "🏆 Leaderboard"])
    with t1:
        if 'exam_active' not in st.session_state:
            c1, c2 = st.columns(2)
            with c1: school = st.text_input("School Name:")
            with c2: name = st.text_input("Student Name:")
            
            l_col, y_col, e_col = st.columns(3)
            with l_col: level = st.selectbox("Level", ["Junior (JSS)", "Senior (SSS)"])
            with y_col: year = st.selectbox("Year", [str(y) for y in range(2026, 2014, -1)])
            with e_col: exam_type = st.selectbox("Exam", ["BECE"] if "Junior" in level else ["WAEC", "NECO", "JAMB"])
            
            # Subject lists based on level
            if "Senior" in level:
                subj = st.selectbox("Subject", ["Mathematics", "English", "Physics", "Chemistry", "Biology", "Economics", "Government"])
            else:
                subj = st.selectbox("Subject", ["Mathematics", "English", "Basic Science", "Social Studies"])

            if st.button("🚀 START EXAM") and school and name:
                st.session_state.exam_active = True
                st.session_state.start_time = time.time()
                st.session_state.current_q = 0
                st.session_state.user_answers = {}
                st.session_state.db_id = f"{school} | {name} | {subj} | {year}"
                st.session_state.s_subj = subj.strip().lower()
                st.session_state.s_year = str(year).strip()
                st.rerun()
        else:
            # Exam in progress logic
            elapsed = time.time() - st.session_state.start_time
            rem = max(0, 1800 - int(elapsed))
            m, s = divmod(rem, 60)
            st.markdown(f"<div class='timer-text'>⏱️ {m:02d}:{s:02d}</div>", unsafe_allow_html=True)
            
            quiz_df = df[(df['subject'] == st.session_state.s_subj) & (df['year'] == st.session_state.s_year)]
            if not quiz_df.empty:
                curr = st.session_state.current_q
                total = len(quiz_df)
                q_data = quiz_df.iloc[curr]
                
                st.subheader(f"Question {curr + 1} of {total}")
                st.info(q_data['question'])
                opts = [str(q_data['a']), str(q_data['b']), str(q_data['c']), str(q_data['d'])]
                saved = st.session_state.user_answers.get(curr, None)
                choice = st.radio("Choose:", opts, index=opts.index(saved) if saved in opts else 0)
                st.session_state.user_answers[curr] = choice
                
                c1, c2, c3 = st.columns([1,1,2])
                with c1: 
                    if st.button("⬅️ Prev") and curr > 0: 
                        st.session_state.current_q -= 1; st.rerun()
                with c2: 
                    if st.button("Next ➡️") and curr < total - 1: 
                        st.session_state.current_q += 1; st.rerun()
                with c3:
                    if st.button("🏁 FINISH"):
                        score = 0
                        c_col = next((c for c in ['correct_answer', 'correct_answee'] if c in df.columns), 'correct_answer')
                        for k, v in st.session_state.user_answers.items():
                            if str(v).strip().upper() == str(quiz_df.iloc[k][c_col]).strip().upper(): score += 1
                        supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}, on_conflict="name").execute()
                        st.session_state.final_score = score
                        st.session_state.finished_rows = quiz_df.to_dict('records')
                        del st.session_state['exam_active']; st.rerun()
            
            if 'final_score' in st.session_state:
                st.success(f"Final Score: {st.session_state.final_score}")
                with st.expander("🔍 View Correct Answers & Explanations"):
                    for i, r in enumerate(st.session_state.finished_rows):
                        st.write(f"**Q{i+1}:** {r['question']}\n**Answer:** {r.get('correct_answer', 'Check Sheet')}")
                        if 'explanation' in r: st.caption(f"💡 {r['explanation']}")
                if st.button("Restart"): st.session_state.clear(); st.rerun()

    with t2:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data: st.table(clean_lb(res.data).head(15))

# --- 6. TEACHER SUITE ---
elif role == "👨‍🏫 Teacher Suite":
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("Enter Access Key:", type="password") == "Lagos2026":
        ts = st.text_input("Filter Results by School Name:")
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            full_df = clean_lb(res.data)
            if ts:
                filtered = full_df[full_df['School'].str.contains(ts, case=False)]
                st.dataframe(filtered, use_container_width=True)
            else:
                st.dataframe(full_df, use_container_width=True)
    else: st.info("Please enter the teacher's key to view analytics.")

# --- 7. PARENT CENTER ---
elif role == "👨‍👩‍👧 Parent Center":
    st.header("👨‍👩‍👧 Parent Progress Report")
    p_school = st.text_input("Your Child's School:")
    p_name = st.text_input("Your Child's Full Name:")
    
    if p_school and p_name:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            full_df = clean_lb(res.data)
            # Find the specific child in that specific school
            child_results = full_df[(full_df['Student'].str.contains(p_name, case=False)) & 
                                    (full_df['School'].str.contains(p_school, case=False))]
            if not child_results.empty:
                st.success(f"Showing results for {p_name}")
                st.table(child_results)
            else: st.warning("No results found for that name and school combination.")

st.markdown("<div class='created-by'>Created by Ufford I.I. VikidylEdu Centre © 2026</div>", unsafe_allow_html=True)
