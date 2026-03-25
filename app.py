import streamlit as st
import pandas as pd
import time
from datetime import datetime
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

# --- 3. STUDENT PORTAL (Fixed Answer Stickiness & Register) ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        name = st.text_input("Full Name")
        school = st.text_input("School Name")
        if df is not None:
            c1, c2, c3 = st.columns(3)
            with c1: subject = st.selectbox("Subject", sorted(df['subject'].unique()))
            with c2: year = st.selectbox("Year", sorted(df['year'].unique().astype(str), reverse=True))
            with c3: exam_p = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM (30 MINS)"):
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
                # Format: Question | User Ans | Correct | Mark
                full_script.append(f"{r['question']} | {u_ans} | {correct} | {mark}")
            
            entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} ({st.session_state.s_info['year']} {st.session_state.s_info['type']}) || {' ||| '.join(full_script)}"
            supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
            st.session_state.final_score = score
            st.session_state.exam_active = False
            st.rerun()

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        with st.expander("📝 Friendly Review & AI Insights"):
            for i, row in st.session_state.quiz_data.iterrows():
                u_ans = st.session_state.user_answers.get(i, "None")
                is_correct = u_ans == str(row['correct_answer'])
                st.write(f"**Q{i+1}: {row['question']}**")
                st.write(f"{'✅' if is_correct else '❌'} Your Ans: {u_ans} | Correct: {row['correct_answer']}")
                st.info(f"💡 AI Insight: {row.get('explanation', 'Keep practicing this concept!')}")
                st.divider()
        if st.button("🔄 Restart"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL (Attempt Picker & Tabular View) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Portal")
    if st.text_input("PIN", type="password") == "Lagos2026":
        t_name = st.text_input("Student Name")
        t_school = st.text_input("School Name")
        
        if st.button("🔍 Search Attempts"):
            res = supabase.table("leaderboard").select("*").execute()
            matches = [r for r in res.data if t_name.lower() in r['name'].lower() and t_school.lower() in r['name'].lower()]
            
            if matches:
                raw_df = pd.DataFrame(matches)
                def parse(v):
                    p = str(v).split(" || ")
                    return p if len(p) == 4 else [p[0], "N/A", "N/A", ""]
                
                raw_df['Student'], raw_df['School'], raw_df['Subject'], raw_df['Script'] = zip(*raw_df['name'].apply(parse))
                
                # Create a readable attempt label: Date + Time + Subject
                raw_df['Attempt_Label'] = raw_df['created_at'].apply(lambda x: datetime.fromisoformat(x.split('+')[0]).strftime('%Y-%m-%d %H:%M'))
                raw_df['Display'] = raw_df['Attempt_Label'] + " - Score: " + raw_df['score'].astype(str) + " (" + raw_df['Subject'] + ")"
                
                st.success(f"Found {len(raw_df)} attempts for {t_name}")
                selected_display = st.selectbox("Select specific attempt to download:", raw_df['Display'])
                
                if selected_display:
                    s = raw_df[raw_df['Display'] == selected_display].iloc[0]
                    
                    # --- THE TABULAR DISPLAY ---
                    st.markdown(f"### 📋 Script Table for {s['Student']}")
                    items = [x.split(" | ") for x in s['Script'].split(" ||| ")]
                    # Handle cases where questions might have extra pipes
                    clean_items = [i if len(i)==4 else ["Error in data", "N/A", "N/A", "N/A"] for i in items]
                    
                    report_df = pd.DataFrame(clean_items, columns=["Question Text", "Student Choice", "Correct Answer", "Result"])
                    st.table(report_df)
                    
                    # --- COMPACT DOC DOWNLOAD ---
                    doc_content = f"VIKIDYLEDU OFFICIAL REPORT\n"
                    doc_content += f"STUDENT: {s['Student']}\nSCHOOL: {s['School']}\nSUBJECT: {s['Subject']}\nSCORE: {s['score']}\nDATE: {s['Attempt_Label']}\n\n"
                    doc_content += "Q# | QUESTION | STUDENT | CORRECT | RESULT\n" + "-"*50 + "\n"
                    for idx, row in enumerate(clean_items):
                        doc_content += f"{idx+1} | {row[0][:40]}... | {row[1]} | {row[2]} | {row[3]}\n"
                    
                    st.download_button("📥 Download This Attempt (.doc)", doc_content, f"{s['Student']}_Attempt_{s['Attempt_Label']}.doc")
            else: st.error("No attempts found.")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    p_name = st.text_input("Child Name")
    p_school = st.text_input("School Name")
    if st.button("Check Result"):
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if p_name.lower() in r['name'].lower() and p_school.lower() in r['name'].lower()]
        if matches:
            for m in matches:
                p = m['name'].split(" || ")
                st.success(f"Date: {m['created_at'][:10]} | Subject: {p[2]} | Score: {m['score']}")
        else: st.error("No record found.")
