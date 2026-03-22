import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. DATABASE SETUP ---
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
st.set_page_config(page_title="Edu-Dash | VikidylEdu", page_icon="🇳🇬", layout="wide")
st.markdown("""<style>
    .stButton>button { border-radius: 12px; height: 3em; background-color: #1E3A8A; color: white; font-weight: bold; border: 2px solid #FFD700; }
    .timer-box { font-size: 22px; font-weight: bold; color: #D32F2F; text-align: center; padding: 10px; border: 2px solid #D32F2F; border-radius: 10px; margin-bottom: 20px; }
    .created-by { text-align: center; color: #1E3A8A; padding: 20px; font-weight: bold; font-size: 1.1em; border-top: 2px solid #EEE; margin-top: 40px;}
</style>""", unsafe_allow_html=True)

def clean_lb(data):
    if not data: return pd.DataFrame()
    ld = pd.DataFrame(data)
    def parse_name(val):
        parts = val.split('|')
        return pd.Series([parts[1].strip() if len(parts)>1 else "N/A", parts[0].strip() if len(parts)>0 else "N/A", f"{parts[2].strip() if len(parts)>2 else ''} ({parts[3].strip() if len(parts)>3 else ''})"])
    ld[['Student', 'School', 'Details']] = ld['name'].apply(parse_name)
    return ld[['Student', 'School', 'Details', 'score']].sort_values(by="score", ascending=False)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/education.png", width=60)
    st.title("VikidylEdu Dash")
    role = st.selectbox("Navigation", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])
    st.caption("Developed by: **Ufford I.I.**\nVikidylEdu Centre © 2026")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    st.header("🎯 Practice Center")
    t1, t2, t3 = st.tabs(["📝 Quiz Room", "📚 Library", "🏆 Leaderboard"])
    
    with t1:
        if 'exam_start' not in st.session_state:
            c1, c2 = st.columns(2)
            with c1: school = st.text_input("School Name:")
            with c2: name = st.text_input("Full Name:")
            l_col, y_col, e_col = st.columns(3)
            with l_col: level = st.selectbox("Level:", ["Junior (JSS)", "Senior (SSS)"])
            with y_col: sel_year = st.selectbox("Exam Year:", [str(y) for y in range(2026, 2014, -1)])
            with e_col: sel_exam = st.selectbox("Exam Type:", ["BECE"] if "Junior" in level else ["WAEC", "NECO", "JAMB"])
            
            dept_col, subj_col = st.columns(2)
            if "Senior" in level:
                with dept_col: dept = st.selectbox("Dept:", ["Science", "Business", "Humanities/Arts"])
                with subj_col:
                    sub_list = ["Mathematics", "English", "Physics", "Chemistry", "Biology"] if dept=="Science" else ["Mathematics", "English", "Accounting", "Commerce", "Economics"] if dept=="Business" else ["Mathematics", "English", "Government", "Literature", "History"]
                    sel_subj = st.selectbox("Subject:", sub_list)
            else:
                with subj_col: sel_subj = st.selectbox("Subject:", ["Mathematics", "English", "Basic Science", "Social Studies", "CCA", "PVS", "National Value"])

            if st.button("🚀 Start Exam") and school and name:
                st.session_state.exam_start, st.session_state.score, st.session_state.q_idx = time.time(), 0, 0
                st.session_state.db_id = f"{school} | {name} | {sel_subj} | {sel_year}"
                st.session_state.search_subj, st.session_state.search_year = sel_subj.strip().lower(), str(sel_year).strip()
                st.rerun()
        
        else:
            elapsed = time.time() - st.session_state.exam_start
            remaining = max(0, 1800 - int(elapsed))
            mins, secs = divmod(remaining, 60)
            st.markdown(f"<div class='timer-box'>⏳ {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
            
            if remaining <= 0:
                st.error("🚨 TIME EXPIRED!"); st.button("Finish", on_click=lambda: st.session_state.pop('exam_start'))
            else:
                if not df.empty:
                    quiz_df = df[(df['subject'].astype(str).str.strip().str.lower() == st.session_state.search_subj) & 
                                (df['year'].astype(str).str.strip() == st.session_state.search_year)]

                    if not quiz_df.empty:
                        total_q = len(quiz_df)
                        idx = st.session_state.q_idx
                        
                        if idx < total_q:
                            q = quiz_df.iloc[idx]
                            st.subheader(f"Question {idx + 1} of {total_q}")
                            st.info(q['question'])
                            ans = st.radio("Choose Answer:", [str(q['a']), str(q['b']), str(q['c']), str(q['d'])], key=f"q_{idx}")
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("✅ Submit"):
                                    c_col = next((c for c in ['correct_answer', 'correct_answee'] if c in df.columns), None)
                                    # --- CRITICAL FIX: STRIP AND UPPERCASE BOTH SIDES ---
                                    user_choice = str(ans).strip().upper()
                                    correct_val = str(q[c_col]).strip().upper()
                                    
                                    if user_choice == correct_val:
                                        st.success("Correct! 🎉")
                                        st.session_state.score += 1
                                        supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": st.session_state.score}, on_conflict="name").execute()
                                    else:
                                        st.error(f"Wrong. The correct answer was: {q[c_col]}")
                            with c2:
                                if st.button("Next ➡️"):
                                    st.session_state.q_idx += 1; st.rerun()
                        else:
                            st.balloons(); st.success(f"Final Score: {st.session_state.score}/{total_q}")
                            if st.button("Restart"): del st.session_state['exam_start']; st.rerun()
                    else: st.warning("No questions found."); st.button("Back", on_click=lambda: st.session_state.pop('exam_start'))

    with t3:
        st.subheader("🏆 Leaderboard")
        try:
            res = supabase.table("leaderboard").select("*").execute()
            if res.data: st.table(clean_lb(res.data).head(15))
        except: st.write("Refreshing...")

# --- 5. TEACHER & PARENT ---
elif role == "👨‍🏫 Teacher":
    st.header("Teacher Suite")
    if st.text_input("Key:", type="password") == "Lagos2026":
        ts = st.text_input("Filter School:")
        if ts:
            res = supabase.table("leaderboard").select("*").ilike("name", f"{ts}%").execute()
            if res.data: st.dataframe(clean_lb(res.data), use_container_width=True)

elif role == "👨‍👩‍👧 Parent":
    st.header("Parent Report")
    ps, pc = st.text_input("School:"), st.text_input("Child:")
    if ps and pc:
        res = supabase.table("leaderboard").select("*").ilike("name", f"{ps} | {pc}%").execute()
        if res.data: st.table(clean_lb(res.data))

st.markdown("<div class='created-by'>Created by Ufford I.I. VikidylEdu Centre © 2026</div>", unsafe_allow_html=True)
