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

# --- 2. INITIALIZE SESSION STATE (The fix for unticking) ---
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

# --- 3. STUDENT PORTAL ---
if st.sidebar.selectbox("Portal", ["✍️ Student", "👨‍🏫 Teacher", "👪 Parent"]) == "✍️ Student":
    df = load_sheet()
    
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        name = st.text_input("Full Name")
        school = st.text_input("School Name")
        if df is not None:
            sub = st.selectbox("Subject", sorted(df['subject'].unique()))
            if st.button("🚀 START (30 MINS)"):
                q_df = df[df['subject'] == sub].sample(n=min(len(df[df['subject']==sub]), 40)).reset_index(drop=True)
                st.session_state.update({
                    "quiz_data": q_df, "expiry_time": time.time() + 1800,
                    "exam_active": True, "current_q": 0, "user_answers": {},
                    "s_info": {"name": name, "school": school, "sub": sub}
                })
                st.rerun()

    elif st.session_state.get('exam_active'):
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        rem = int(st.session_state.expiry_time - time.time())
        
        st.subheader(f"Q{curr+1}/{len(q_df)} | ⏳ {max(0, rem)//60:02d}:{max(0, rem)%60:02d}")
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        
        opts = [str(row['a']), str(row['b']), str(row['c']), str(row['d'])]
        
        # --- THE FIX: Hard-binding the selection to Session State ---
        def save_ans():
            st.session_state.user_answers[curr] = st.session_state[f"temp_q_{curr}"]

        st.radio("Select Answer:", opts, 
                 index=opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None,
                 key=f"temp_q_{curr}", on_change=save_ans)

        st.divider()
        c1, c2, c3 = st.columns(3)
        if curr > 0: c1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: c3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        
        if st.button("🏁 FINISH", type="primary", use_container_width=True) or rem <= 0:
            score = 0
            report_lines = []
            for i, r in q_df.iterrows():
                u_ans = st.session_state.user_answers.get(i, "Skipped")
                correct = str(r['correct_answer'])
                res = "OK" if u_ans == correct else "X"
                if u_ans == correct: score += 1
                # Compact format for DB: Q#|User|Correct|Status
                report_lines.append(f"{i+1}|{u_ans[:15]}|{correct[:15]}|{res}")
            
            script_compact = " ~ ".join(report_lines)
            info = st.session_state.s_info
            entry = f"{info['name']} || {info['school']} || {info['sub']} || {script_compact}"
            supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
            st.session_state.final_score = score
            st.session_state.exam_active = False
            st.rerun()

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score}")
        with st.expander("📝 Review Corrections"):
            for i, row in st.session_state.quiz_data.iterrows():
                u_ans = st.session_state.user_answers.get(i, "None")
                st.write(f"**Q{i+1}:** {row['question']}")
                st.write(f"Ans: {u_ans} | Correct: {row['correct_answer']}")
                st.divider()
        if st.button("New Exam"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL ---
elif st.session_state.get('portal') == "👨‍🏫 Teacher" or True: # Simplified for logic flow
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("PIN", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        if res.data:
            raw_df = pd.DataFrame(res.data)
            def parse(val):
                p = str(val).split(" || ")
                return p if len(p) == 4 else [p[0], "N/A", "N/A", ""]
            
            parsed = raw_df['name'].apply(parse)
            raw_df['Student'], raw_df['School'], raw_df['Subject'], raw_df['Script'] = zip(*parsed)
            st.dataframe(raw_df[['Student', 'School', 'Subject', 'score']])
            
            pick = st.selectbox("Select Student", raw_df['Student'].unique())
            if pick:
                s = raw_df[raw_df['Student'] == pick].iloc[0]
                # --- PROFESSIONAL COMPACT TABLE ---
                st.markdown("### 📊 Compact Marking Script")
                items = s['Script'].split(" ~ ")
                table_data = [item.split("|") for item in items]
                report_df = pd.DataFrame(table_data, columns=["Q#", "Student Choice", "Correct Answer", "Result"])
                st.table(report_df)
                
                # DOC FORMAT (Tabular)
                doc_text = f"VIKIDYLEDU REPORT\nST: {pick} | SCH: {s['School']} | SUB: {s['Subject']} | SCORE: {s['score']}\n"
                doc_text += "\nQ# | CHOICE | CORRECT | RESULT\n" + "-"*35 + "\n"
                for row in table_data:
                    doc_text += f"{row[0].ljust(3)}| {row[1].ljust(10)}| {row[2].ljust(10)}| {row[3]}\n"
                
                st.download_button("📥 Download Compact DOC", doc_text, f"{pick}_Report.doc")
