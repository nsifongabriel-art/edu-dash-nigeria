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
                    # TIMER FIX: Using a concrete timestamp
                    st.session_state.expiry_time = time.time() + 1800 
                    st.session_state.exam_active = True
                    st.session_state.current_q = 0
                    st.session_state.user_answers = {}
                    st.session_state.s_info = {"name": name, "school": school, "sub": subject}
                    st.rerun()

    elif st.session_state.get('exam_active'):
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # Timer Calculation
        rem = int(st.session_state.expiry_time - time.time())
        
        if rem <= 0:
            st.warning("⚠️ Time Expired! Please click Finish to save.")
            rem = 0

        st.subheader(f"Q{curr+1} of {len(q_df)} | ⏳ {rem//60:02d}:{rem%60:02d}")
        
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [str(row['a']), str(row['b']), str(row['c']), str(row['d'])]
        
        # Radio selection
        prev_ans = st.session_state.user_answers.get(curr)
        idx = opts.index(prev_ans) if prev_ans in opts else None
        choice = st.radio("Select answer:", opts, index=idx, key=f"q{curr}_{curr}")
        if choice: st.session_state.user_answers[curr] = choice

        st.divider()
        st.write(f"📊 **Progress:** {len(st.session_state.user_answers)} / {len(q_df)} answered")
        
        b1, b2, b3 = st.columns([1, 1, 1])
        if curr > 0: b1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: b3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        
        if st.button("🏁 FINISH EXAM", type="primary", use_container_width=True):
            score = 0
            details = []
            for i, r in q_df.iterrows():
                u_ans = st.session_state.user_answers.get(i, "Skipped")
                correct = str(r['correct_answer'])
                mark = "✅" if u_ans == correct else "❌"
                if u_ans == correct: score += 1
                details.append(f"Q: {r['question']} | Ans: {u_ans} | Correct: {correct} ({mark})")
            
            script_str = " ||| ".join(details)
            info = st.session_state.s_info
            entry = f"{info['name']} || {info['school']} || {info['sub']} || {script_str}"
            
            try:
                supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
                st.session_state.final_score = score
                st.session_state.total_qs = len(q_df)
                st.session_state.exam_active = False
                st.rerun()
            except Exception as e:
                st.error(f"Save Error: {e}")

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        if st.button("🔄 Start New"):
            st.session_state.clear()
            st.rerun()

# --- 4. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("PIN", type="password") == "Lagos2026":
        try:
            res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
            if res.data:
                raw_df = pd.DataFrame(res.data)
                
                # Column Error Prevention
                def safe_split(val):
                    parts = str(val).split(" || ")
                    return parts if len(parts) == 4 else [parts[0], "N/A", "N/A", "No Script"]

                parsed = raw_df['name'].apply(safe_split)
                raw_df['Student'] = [p[0] for p in parsed]
                raw_df['School'] = [p[1] for p in parsed]
                raw_df['Subject'] = [p[2] for p in parsed]
                raw_df['Full_Script'] = [p[3] for p in parsed]

                st.dataframe(raw_df[['Student', 'School', 'Subject', 'score', 'created_at']])
                
                st.divider()
                pick = st.selectbox("View Student Script", raw_df['Student'].unique())
                if pick:
                    s_data = raw_df[raw_df['Student'] == pick].iloc[0]
                    st.text_area("Marked Script", s_data['Full_Script'].replace(" ||| ", "\n\n"), height=300)
                    
                    doc_out = f"REPORT: {pick}\nSCORE: {s_data['score']}\n\n{s_data['Full_Script'].replace(' ||| ', '\n\n')}"
                    st.download_button("📥 Download DOC", doc_out, f"{pick}.doc")
        except: st.info("Loading results...")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Portal")
    child = st.text_input("Enter Child Name")
    if child:
        res = supabase.table("leaderboard").select("*").execute()
        # Filter logic that avoids KeyError
        matches = [r for r in res.data if child.lower() in r['name'].lower()]
        if matches:
            st.table(pd.DataFrame(matches)[['score', 'created_at']])
        else: st.error("No record found.")
