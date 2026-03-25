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
        name = st.text_input("Full Name")
        school = st.text_input("School Name")
        if df is not None:
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", sorted(df['subject'].unique()))
            with c2: year = st.selectbox("Year", sorted(df['year'].unique().astype(str), reverse=True))
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                q_df = df[(df['subject'] == subject) & (df['year'].astype(str) == year)].sample(n=min(40, len(df))).reset_index(drop=True)
                st.session_state.update({
                    "quiz_data": q_df, "expiry_time": time.time() + 1800,
                    "exam_active": True, "current_q": 0, "user_answers": {},
                    "s_info": {"name": name, "school": school, "sub": subject, "year": year, "type": exam_p}
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
        
        def sync(): st.session_state.user_answers[curr] = st.session_state[f"r_{curr}"]
        
        st.radio("Select Answer:", opts, index=opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None, key=f"r_{curr}", on_change=sync)

        st.divider()
        b1, b2, b3 = st.columns(3)
        if curr > 0: b1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: b3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        
        if st.button("🏁 FINISH", type="primary", use_container_width=True) or rem <= 0:
            score = 0
            full_script = []
            for i, r in q_df.iterrows():
                u_ans = st.session_state.user_answers.get(i, "Skipped")
                correct = str(r['correct_answer'])
                mark = "✅" if u_ans == correct else "❌"
                if u_ans == correct: score += 1
                full_script.append(f"Q: {r['question']} ~ A: {u_ans} ~ C: {correct} ~ {mark}")
            
            entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} ({st.session_state.s_info['year']} {st.session_state.s_info['type']}) || {' ||| '.join(full_script)}"
            supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
            st.session_state.final_score = score
            st.session_state.exam_active = False
            st.rerun()

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        with st.expander("📝 Review Corrections & AI Insights"):
            for i, row in st.session_state.quiz_data.iterrows():
                u_ans = st.session_state.user_answers.get(i, "None")
                is_correct = u_ans == str(row['correct_answer'])
                st.write(f"**Q{i+1}: {row['question']}**")
                st.write(f"{'✅' if is_correct else '❌'} Your Answer: {u_ans} | Correct: {row['correct_answer']}")
                st.info(f"💡 AI Insight: {row.get('explanation', 'Review this topic carefully.')}")
                st.divider()
        if st.button("🔄 Restart"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL (Search-Based) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Search Portal")
    if st.text_input("Admin PIN", type="password") == "Lagos2026":
        t_name = st.text_input("Search Student Name")
        t_school = st.text_input("Search School Name")
        if st.button("Query Database"):
            res = supabase.table("leaderboard").select("*").execute()
            matches = [r for r in res.data if t_name.lower() in r['name'].lower() and t_school.lower() in r['name'].lower()]
            if matches:
                raw_df = pd.DataFrame(matches)
                def parse(v):
                    p = str(v).split(" || ")
                    return p if len(p) == 4 else [p[0], "N/A", "N/A", ""]
                raw_df['Student'], raw_df['School'], raw_df['Subject'], raw_df['Script'] = zip(*raw_df['name'].apply(parse))
                st.dataframe(raw_df[['Student', 'School', 'Subject', 'score', 'created_at']])
                
                pick = st.selectbox("Select Student for Full DOC Script", raw_df['Student'].unique())
                if pick:
                    s = raw_df[raw_df['Student'] == pick].iloc[0]
                    # Format script for professional download
                    script_lines = s['Script'].split(" ||| ")
                    doc_content = f"OFFICIAL REPORT\nNAME: {pick}\nSCHOOL: {s['School']}\nSUB: {s['Subject']}\nSCORE: {s['score']}\n\n"
                    for line in script_lines: doc_content += f"{line.replace(' ~ ', '\n   ')}\n\n"
                    
                    st.download_button("📥 Download Marked Script (.doc)", doc_content, f"{pick}_Script.doc")
            else: st.error("No match found.")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    p_name = st.text_input("Enter Student's Full Name")
    p_school = st.text_input("Enter School Name")
    if st.button("View Result"):
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if p_name.lower() in r['name'].lower() and p_school.lower() in r['name'].lower()]
        if matches:
            for m in matches:
                p = m['name'].split(" || ")
                st.success(f"Score: {m['score']} | Subject: {p[2] if len(p)>2 else 'N/A'}")
        else: st.error("Result not found.")
