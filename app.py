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
                    # REDUCED TIME TO 30 MINUTES (1800 SECONDS)
                    st.session_state.update({
                        "exam_active": True, "current_q": 0, "user_answers": {}, 
                        "expiry_time": time.time() + 1800, 
                        "s_name": name, "s_school": school, "s_sub": subject
                    })
                    st.rerun()

    elif 'exam_active' in st.session_state:
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        
        # FIXED TIMER LOGIC
        rem = int(st.session_state.expiry_time - time.time())
        
        if rem <= 0:
            st.error("⏰ Time is up! Auto-submitting...")
            time.sleep(1)
            # Auto-submit logic would go here, for now we trigger finish
            rem = 0 

        st.subheader(f"Q{curr+1} of {len(q_df)} | ⏳ {max(0, rem)//60:02d}:{max(0, rem)%60:02d}")
        
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [row['a'], row['b'], row['c'], row['d']]
        ans_idx = opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None
        choice = st.radio("Select answer:", opts, index=ans_idx, key=f"q{curr}")
        if choice: st.session_state.user_answers[curr] = choice

        st.divider()
        st.write(f"📊 **Progress Tracker:** {len(st.session_state.user_answers)} / {len(q_df)} Answered")
        
        b1, b2, b3 = st.columns([1, 2, 1])
        if curr > 0: b1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: b3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        else:
            if b3.button("🏁 FINISH", type="primary") or rem <= 0:
                score = 0
                script_parts = []
                for i, r in q_df.iterrows():
                    u_ans = st.session_state.user_answers.get(i, "No Answer")
                    is_right = "✅" if u_ans == r['correct_answer'] else "❌"
                    if u_ans == r['correct_answer']: score += 1
                    # NOW SAVING: Question + User Answer + Correct Answer
                    script_parts.append(f"Q: {r['question']} | Your Ans: {u_ans} | Correct: {r['correct_answer']} ({is_right})")
                
                script_str = " ||| ".join(script_parts)
                full_entry = f"{st.session_state.s_name} || {st.session_state.s_school} || {st.session_state.s_sub} || {script_str}"
                
                try: supabase.table("leaderboard").insert({"name": full_entry, "score": score}).execute()
                except: pass
                st.session_state.final_score = score
                st.session_state.total_qs = len(q_df)
                del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        if st.button("🔄 RETAKE"):
            st.session_state.clear(); st.rerun()
        if st.button("Logout"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Diagnostic Dashboard")
    if st.text_input("PIN", type="password") == "Lagos2026":
        try:
            res = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
            if res.data:
                res_df = pd.DataFrame(res.data)
                def parse_data(val):
                    p = val.split(' || ')
                    return p if len(p) == 4 else [p[0], "N/A", "N/A", "Script missing"]
                
                meta = res_df['name'].apply(parse_data)
                res_df['Student'] = [m[0] for m in meta]
                res_df['School'] = [m[1] for m in meta]
                res_df['Subject'] = [m[2] for m in meta]
                res_df['Full_Script'] = [m[3] for m in meta]

                st.dataframe(res_df[['Student', 'School', 'Subject', 'score', 'created_at']], use_container_width=True)
                
                st.divider()
                target = st.selectbox("Analyze Student Script", ["-- Select --"] + res_df['Student'].tolist())
                if target != "-- Select --":
                    s_row = res_df[res_df['Student'] == target].iloc[0]
                    st.subheader(f"Detailed Marking for {target}")
                    # DISPLAYING FULL QUESTIONS + ANSWERS
                    st.text_area("Marked Script", s_row['Full_Script'].replace(" ||| ", "\n\n"), height=400)
                    
                    doc_txt = f"VIKIDYLEDU REPORT: {target}\nSCORE: {s_row['score']}\n\n{s_row['Full_Script'].replace(' ||| ', '\n\n')}"
                    st.download_button("📥 Download DOC Report", doc_txt, f"{target}_Full_Script.doc", "application/msword")
            else: st.info("No data.")
        except: st.error("Database connection refresh...")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    child = st.text_input("Student Name")
    if st.button("Search"):
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if child.lower() in r['name'].lower()]
        if matches: st.table(pd.DataFrame(matches)[['score', 'created_at']])
        else: st.error("Not found.")
