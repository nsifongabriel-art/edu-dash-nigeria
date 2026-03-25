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

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👪 Parent"])

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        name = st.text_input("Full Name")
        school = st.text_input("School Name")
        if df is not None:
            sub = st.selectbox("Subject", sorted(df['subject'].unique()))
            if st.button("🚀 START EXAM"):
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
        
        # FIXED: Answer persistence logic
        def sync_ans():
            st.session_state.user_answers[curr] = st.session_state[f"q_radio_{curr}"]

        st.radio("Select Answer:", opts, 
                 index=opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None,
                 key=f"q_radio_{curr}", on_change=sync_ans)

        st.divider()
        st.write(f"📊 **Progress:** {len(st.session_state.user_answers)} / {len(q_df)} answered")
        c1, c2, c3 = st.columns(3)
        if curr > 0: c1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: c3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        
        if st.button("🏁 FINISH", type="primary", use_container_width=True) or rem <= 0:
            score = 0
            compact_log = []
            for i, r in q_df.iterrows():
                u_ans = st.session_state.user_answers.get(i, "Skipped")
                correct = str(r['correct_answer'])
                res = "✅" if u_ans == correct else "❌"
                if u_ans == correct: score += 1
                compact_log.append(f"{i+1}|{u_ans}|{correct}|{res}")
            
            # Save data
            entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} || {' ~ '.join(compact_log)}"
            supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
            st.session_state.final_score = score
            st.session_state.exam_active = False
            st.rerun()

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        
        # RESTORED: Friendly AI Review Page
        st.subheader("📝 Learning from Mistakes")
        for i, row in st.session_state.quiz_data.iterrows():
            u_ans = st.session_state.user_answers.get(i, "None")
            is_correct = u_ans == str(row['correct_answer'])
            with st.expander(f"Question {i+1}: {'✅' if is_correct else '❌'}"):
                st.write(f"**Question:** {row['question']}")
                st.write(f"**Your Answer:** {u_ans}")
                st.write(f"**Correct Answer:** {row['correct_answer']}")
                st.info(f"💡 AI Insight: {row.get('explanation', 'Always double-check the key concepts of this topic.')}")
        
        if st.button("🔄 Retake Exam"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Portal")
    if st.text_input("Admin PIN", type="password") == "Lagos2026":
        res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
        if res.data:
            raw_df = pd.DataFrame(res.data)
            def split_safe(v):
                p = str(v).split(" || ")
                return p if len(p) == 4 else [p[0], "N/A", "N/A", ""]
            
            parsed = raw_df['name'].apply(split_safe)
            raw_df['Student'], raw_df['School'], raw_df['Subject'], raw_df['Script'] = zip(*parsed)
            st.dataframe(raw_df[['Student', 'School', 'Subject', 'score', 'created_at']])
            
            pick = st.selectbox("Analyze Student", raw_df['Student'].unique())
            if pick:
                s = raw_df[raw_df['Student'] == pick].iloc[0]
                # COMPACT DOWNLOAD FORMAT
                items = [x.split("|") for x in s['Script'].split(" ~ ")]
                report_df = pd.DataFrame(items, columns=["Q#", "Student", "Correct", "Result"])
                st.table(report_df)
                
                doc_text = f"STUDENT: {pick}\nSCHOOL: {s['School']}\nSUB: {s['Subject']}\nSCORE: {s['score']}\n\nQ# | ANS | CORRECT | STATUS\n"
                for r in items: doc_text += f"{r[0]} | {r[1]} | {r[2]} | {r[3]}\n"
                st.download_button("📥 Download Pro Report (.doc)", doc_text, f"{pick}_Report.doc")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    child_query = st.text_input("Search Student Full Name")
    if child_query:
        res = supabase.table("leaderboard").select("*").execute()
        # Filter only for the searched child to prevent seeing other students' data
        matches = [r for r in res.data if child_query.lower() in r['name'].lower()]
        if matches:
            st.success(f"Results for {child_query}")
            st.table(pd.DataFrame(matches)[['score', 'created_at']])
        else: st.error("No records found for that name.")
