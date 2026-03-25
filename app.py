import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10)
def load_sheet():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👪 Parent"])
    st.divider()
    st.info("Time Limit: 30 Mins")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School Name")
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", sorted(df['subject'].unique().tolist()))
            with c2: year = st.selectbox("Year", ["All Years"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True))
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'] == subject) & (df['exam'].str.upper() == exam_p)
                if year != "All Years": filt = filt & (df['year'].astype(str) == year)
                q_df = df[filt]
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 40)).reset_index(drop=True)
                    # START 30 MINUTE TIMER
                    st.session_state.expiry_time = time.time() + 1800 
                    st.session_state.exam_active = True
                    st.session_state.current_q = 0
                    st.session_state.user_answers = {}
                    st.session_state.s_info = {"name": name, "school": school, "sub": subject}
                    st.rerun()

    elif st.session_state.get('exam_active'):
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # Robust Timer Calculation
        rem = int(st.session_state.expiry_time - time.time())
        if rem <= 0:
            st.error("⏰ Time is up! Submitting your work...")
            time.sleep(2)
            rem = 0 # Force zero

        st.subheader(f"Q{curr+1} of {len(q_df)} | ⏳ {max(0, rem)//60:02d}:{max(0, rem)%60:02d}")
        
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [str(row['a']), str(row['b']), str(row['c']), str(row['d'])]
        
        # Answer Selection
        choice = st.radio("Select answer:", opts, index=None, key=f"q{curr}_{time.time()}")
        if choice: st.session_state.user_answers[curr] = choice

        st.divider()
        st.write(f"📝 **Progress:** {len(st.session_state.user_answers)} / {len(q_df)} questions answered")
        
        c1, c2, c3 = st.columns(3)
        if curr > 0: c1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: c3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        
        if st.button("🏁 FINISH EXAM", type="primary", use_container_width=True) or rem <= 0:
            score = 0
            details = []
            for i, r in q_df.iterrows():
                u_ans = st.session_state.user_answers.get(i, "Skipped")
                correct = str(r['correct_answer'])
                mark = "✅" if u_ans == correct else "❌"
                if u_ans == correct: score += 1
                # Format for Teacher: Full Question Details
                details.append(f"QUESTION: {r['question']}\nSTUDENT ANSWER: {u_ans}\nCORRECT ANSWER: {correct} ({mark})")
            
            script_str = "\n\n---\n\n".join(details)
            info = st.session_state.s_info
            entry = f"{info['name']} || {info['school']} || {info['sub']} || {script_str}"
            
            supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
            st.session_state.final_score = score
            st.session_state.total_qs = len(q_df)
            st.session_state.exam_active = False
            st.rerun()

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Final Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        st.write("Your results have been sent to the teacher dashboard.")
        if st.button("🔄 Start New Exam"):
            st.session_state.clear()
            st.rerun()

# --- 4. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Diagnostic Center")
    if st.text_input("PIN", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        if res.data:
            raw_df = pd.DataFrame(res.data)
            
            def safe_parse(val):
                parts = str(val).split(" || ")
                return parts if len(parts) == 4 else [parts[0], "N/A", "N/A", "Script missing"]

            parsed = raw_df['name'].apply(safe_parse)
            raw_df['Student'] = [p[0] for p in parsed]
            raw_df['School'] = [p[1] for p in parsed]
            raw_df['Subject'] = [p[2] for p in parsed]
            raw_df['Script'] = [p[3] for p in parsed]

            st.dataframe(raw_df[['Student', 'School', 'Subject', 'score', 'created_at']])
            
            st.divider()
            target = st.selectbox("Select Student for Full Marking Script", raw_df['Student'].unique())
            if target:
                s_data = raw_df[raw_df['Student'] == target].iloc[0]
                st.subheader(f"Marked Script: {target}")
                st.text_area("Question & Answer Breakdown", s_data['Script'], height=400)
                
                doc_report = f"OFFICIAL PERFORMANCE REPORT\nSTUDENT: {target}\nSCHOOL: {s_data['School']}\nSUBJECT: {s_data['Subject']}\nSCORE: {s_data['score']}\n\nDETAILED SCRIPT:\n{s_data['Script']}"
                st.download_button("📥 Download Official DOC Report", doc_report, f"{target}_Performance.doc")
        else: st.info("No records found.")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    child = st.text_input("Enter Child Name")
    if child:
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if child.lower() in r['name'].lower()]
        if matches: st.table(pd.DataFrame(matches)[['score', 'created_at']])
        else: st.error("No record found.")
