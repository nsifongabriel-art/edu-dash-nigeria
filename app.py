import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"

try:
    supabase: Client = create_client(URL, KEY)
except Exception:
    st.error("⚠️ Database connection failed.")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10)
def load_sheet():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

# --- 2. CUSTOM PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    /* Make the navigation buttons small square boxes */
    div.stButton > button {
        width: 40px !important;
        height: 40px !important;
        padding: 0px !important;
        border-radius: 5px !important;
        margin: 2px !important;
    }
    /* Style for answered questions */
    .answered-btn {
        background-color: #28a745 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👪 Parent"])

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    
    if 'p_name' not in st.session_state: st.session_state.p_name = ""
    if 'p_school' not in st.session_state: st.session_state.p_school = ""

    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        name = st.text_input("Full Name", value=st.session_state.p_name)
        school = st.text_input("School Name", value=st.session_state.p_school)
        
        if df is not None:
            c1, c2, c3 = st.columns(3)
            with c1: subject = st.selectbox("Subject", sorted(df['subject'].unique()))
            with c2: year = st.selectbox("Year", ["All Years"] + sorted(df['year'].unique().astype(str), reverse=True))
            with c3: exam_p = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM", key="start_btn_global"):
                if not name or not school:
                    st.warning("Please enter your name and school.")
                else:
                    st.session_state.p_name = name
                    st.session_state.p_school = school
                    
                    if year == "All Years":
                        q_df = df[df['subject'] == subject]
                        limit = 50
                    else:
                        q_df = df[(df['subject'] == subject) & (df['year'].astype(str) == year)]
                        limit = 40
                    
                    if q_df.empty:
                        st.warning(f"No questions found.")
                    else:
                        q_df = q_df.sample(n=min(limit, len(q_df))).reset_index(drop=True)
                        st.session_state.update({
                            "quiz_data": q_df, "expiry_time": time.time() + 1800,
                            "exam_active": True, "current_q": 0, "user_answers": {},
                            "s_info": {"name": name, "school": school, "sub": subject, "year": year, "type": exam_p}
                        })
                        st.rerun()

    elif st.session_state.get('exam_active'):
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # --- PROFESSIONAL HORIZONTAL GRID NAVIGATION ---
        st.write("### 🧭 Progress Tracker")
        
        # We use a container to wrap the buttons horizontally
        nav_container = st.container()
        with nav_container:
            # Create rows of 10 buttons each
            n_rows = (len(q_df) // 10) + 1
            for r in range(n_rows):
                cols = st.columns(10)
                for c in range(10):
                    idx = r * 10 + c
                    if idx < len(q_df):
                        with cols[c]:
                            # Label logic
                            is_answered = idx in st.session_state.user_answers
                            is_current = idx == curr
                            
                            # Streamlit doesn't support dynamic class injection easily, 
                            # so we use 'primary' for current and standard for others.
                            # Visual indicator: Answered questions get a checkmark prefix.
                            label = f"✓{idx+1}" if is_answered else f"{idx+1}"
                            
                            if st.button(label, key=f"nav_sq_{idx}", type="primary" if is_current else "secondary"):
                                st.session_state.current_q = idx
                                st.rerun()
        
        st.divider()

        if 'expiry_time' in st.session_state:
            rem = int(st.session_state.expiry_time - time.time())
            if rem <= 0: rem = 0
            
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
            
            if st.button("🏁 FINISH EXAM", type="primary", use_container_width=True) or rem <= 0:
                score = 0
                full_script = []
                for i, r in q_df.iterrows():
                    u_ans = st.session_state.user_answers.get(i, "Skipped")
                    correct = str(r['correct_answer'])
                    mark = "✅" if u_ans == correct else "❌"
                    if u_ans == correct: score += 1
                    full_script.append(f"{r['question']} | {u_ans} | {correct} | {mark}")
                
                entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} ({st.session_state.s_info['year']}) || {' ||| '.join(full_script)}"
                
                try:
                    supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
                    st.session_state.final_score = score
                    st.session_state.exam_active = False
                    st.rerun()
                except Exception:
                    st.error("📡 Connection error. Result not saved.")

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        with st.expander("📝 Review Mistakes & AI Insights"):
            for i, row in st.session_state.quiz_data.iterrows():
                u_ans = st.session_state.user_answers.get(i, "None")
                is_correct = u_ans == str(row['correct_answer'])
                st.write(f"**Q{i+1}: {row['question']}**")
                st.write(f"{'✅' if is_correct else '❌'} Your Ans: {u_ans} | Correct: {row['correct_answer']}")
                st.info(f"💡 AI Insight: {row.get('explanation', 'Keep practicing!')}")
                st.divider()
        
        if st.button("🔄 Start New Exam"): 
            for key in ['quiz_data', 'expiry_time', 'exam_active', 'current_q', 'user_answers', 'final_score', 's_info']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

# --- 5. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Portal")
    pin = st.text_input("PIN", type="password")
    if pin == "Lagos2026":
        t_name = st.text_input("Student Name")
        t_school = st.text_input("School Name")
        
        if st.button("🔍 Search Attempts", key="t_search_main"):
            try:
                res = supabase.table("leaderboard").select("*").execute()
                matches = [r for r in res.data if t_name.lower() in r['name'].lower() and t_school.lower() in r['name'].lower()]
                
                if matches:
                    raw_df = pd.DataFrame(matches)
                    def parse(v):
                        p = str(v).split(" || ")
                        return p if len(p) == 4 else [p[0], "N/A", "N/A", ""]
                    raw_df['Student'], raw_df['School'], raw_df['Subject'], raw_df['Script'] = zip(*raw_df['name'].apply(parse))
                    raw_df['Display'] = raw_df['created_at'].apply(lambda x: x[:16].replace("T", " ")) + " - Score: " + raw_df['score'].astype(str)
                    st.session_state.teacher_results = raw_df
                else:
                    st.error("No attempts found.")
            except Exception:
                st.error("📡 Connection timed out.")

        if 'teacher_results' in st.session_state:
            res_df = st.session_state.teacher_results
            selected_label = st.selectbox("Select specific attempt:", ["-- Select --"] + res_df['Display'].tolist())
            
            if selected_label != "-- Select --":
                s = res_df[res_df['Display'] == selected_label].iloc[0]
                
                if st.checkbox("Check to delete this record"):
                    if st.button("🗑️ DELETE PERMANENTLY"):
                        supabase.table("leaderboard").delete().eq("id", s['id']).execute()
                        st.success("Deleted!")
                        del st.session_state.teacher_results
                        time.sleep(1)
                        st.rerun()

                items = [x.split(" | ") for x in s['Script'].split(" ||| ")]
                items = [i for i in items if len(i) == 4]
                
                if items:
                    st.markdown(f"### 📋 Script Table for {s['Student']}")
                    report_df = pd.DataFrame(items, columns=["Question Text", "Student Choice", "Correct Answer", "Result"])
                    st.table(report_df)
                    
                    doc_content = f"REPORT: {s['Student']}\nSCORE: {s['score']}\n\n"
                    for i in items: doc_content += f"Q: {i[0]}\nAns: {i[1]} | Correct: {i[2]} ({i[3]})\n\n"
                    st.download_button("📥 Download (.doc)", doc_content, f"{s['Student']}_Report.doc", key="dl_btn_teacher")

# --- 6. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    p_name = st.text_input("Child Name")
    p_school = st.text_input("School Name")
    if st.button("Check Result"):
        try:
            res = supabase.table("leaderboard").select("*").execute()
            matches = [r for r in res.data if p_name.lower() in r['name'].lower() and p_school.lower() in r['name'].lower()]
            if matches:
                for m in matches:
                    p = m['name'].split(" || ")
                    st.success(f"Date: {m['created_at'][:10]} | Subject: {p[2] if len(p)>2 else 'N/A'} | Score: {m['score']}")
            else: st.error("No record found.")
        except Exception:
            st.error("📡 Database busy.")            
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
                    full_script.append(f"{r['question']} | {u_ans} | {correct} | {mark}")
                
                entry = f"{st.session_state.s_info['name']} || {st.session_state.s_info['school']} || {st.session_state.s_info['sub']} ({st.session_state.s_info['year']}) || {' ||| '.join(full_script)}"
                
                try:
                    supabase.table("leaderboard").insert({"name": entry, "score": score}).execute()
                    st.session_state.final_score = score
                    st.session_state.exam_active = False
                    st.rerun()
                except Exception:
                    st.error("📡 Connection error. Result not saved.")

    elif 'final_score' in st.session_state:
        st.balloons()
        st.header(f"🏆 Score: {st.session_state.final_score} / {len(st.session_state.quiz_data)}")
        with st.expander("📝 Review Mistakes & AI Insights"):
            for i, row in st.session_state.quiz_data.iterrows():
                u_ans = st.session_state.user_answers.get(i, "None")
                is_correct = u_ans == str(row['correct_answer'])
                st.write(f"**Q{i+1}: {row['question']}**")
                st.write(f"{'✅' if is_correct else '❌'} Your Ans: {u_ans} | Correct: {row['correct_answer']}")
                st.info(f"💡 AI Insight: {row.get('explanation', 'Keep practicing!')}")
                st.divider()
        # RESTART: Notice we don't clear st.session_state completely so name/school stays
        if st.button("🔄 Restart"): 
            for key in ['quiz_data', 'expiry_time', 'exam_active', 'current_q', 'user_answers', 'final_score', 's_info']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

# --- 4. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Portal")
    pin = st.text_input("PIN", type="password")
    if pin == "Lagos2026":
        t_name = st.text_input("Student Name")
        t_school = st.text_input("School Name")
        
        if st.button("🔍 Search Attempts", key="t_search_btn"):
            try:
                res = supabase.table("leaderboard").select("*").execute()
                matches = [r for r in res.data if t_name.lower() in r['name'].lower() and t_school.lower() in r['name'].lower()]
                
                if matches:
                    raw_df = pd.DataFrame(matches)
                    def parse(v):
                        p = str(v).split(" || ")
                        return p if len(p) == 4 else [p[0], "N/A", "N/A", ""]
                    raw_df['Student'], raw_df['School'], raw_df['Subject'], raw_df['Script'] = zip(*raw_df['name'].apply(parse))
                    raw_df['Display'] = raw_df['created_at'].apply(lambda x: x[:16].replace("T", " ")) + " - Score: " + raw_df['score'].astype(str)
                    st.session_state.teacher_results = raw_df
                else:
                    st.error("No attempts found.")
            except Exception:
                st.error("📡 Connection timed out.")

        if 'teacher_results' in st.session_state:
            res_df = st.session_state.teacher_results
            selected_label = st.selectbox("Select specific attempt:", ["-- Select --"] + res_df['Display'].tolist())
            
            if selected_label != "-- Select --":
                s = res_df[res_df['Display'] == selected_label].iloc[0]
                
                if st.checkbox("Check to delete this record"):
                    if st.button("🗑️ DELETE PERMANENTLY"):
                        supabase.table("leaderboard").delete().eq("id", s['id']).execute()
                        st.success("Deleted!")
                        del st.session_state.teacher_results
                        time.sleep(1)
                        st.rerun()

                items = [x.split(" | ") for x in s['Script'].split(" ||| ")]
                items = [i for i in items if len(i) == 4]
                
                if items:
                    st.markdown(f"### 📋 Script Table for {s['Student']}")
                    report_df = pd.DataFrame(items, columns=["Question Text", "Student Choice", "Correct Answer", "Result"])
                    st.table(report_df)
                    
                    doc_content = f"REPORT: {s['Student']}\nSCORE: {s['score']}\n\n"
                    for i in items: doc_content += f"Q: {i[0]}\nAns: {i[1]} | Correct: {i[2]} ({i[3]})\n\n"
                    st.download_button("📥 Download (.doc)", doc_content, f"{s['Student']}_Report.doc", key="dl_btn")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    p_name = st.text_input("Child Name")
    p_school = st.text_input("School Name")
    if st.button("Check Result"):
        try:
            res = supabase.table("leaderboard").select("*").execute()
            matches = [r for r in res.data if p_name.lower() in r['name'].lower() and p_school.lower() in r['name'].lower()]
            if matches:
                for m in matches:
                    p = m['name'].split(" || ")
                    st.success(f"Date: {m['created_at'][:10]} | Subject: {p[2] if len(p)>2 else 'N/A'} | Score: {m['score']}")
            else: st.error("No record found.")
        except Exception:
            st.error("📡 Database busy.")
