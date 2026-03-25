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
    st.info("Version 3.5: Excellence Edition")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    df = load_sheet()
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School Name")
            c1, c2 = st.columns(2)
            with c1: 
                subject = st.selectbox("Subject", sorted(df['subject'].unique().tolist()))
            with c2: 
                year = st.selectbox("Year", ["All Years"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True))
            
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'] == subject) & (df['exam'].str.upper() == exam_p)
                if year != "All Years": filt = filt & (df['year'].astype(str) == year)
                q_df = df[filt]
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 40)).reset_index(drop=True)
                    st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "start_time": time.time(), "s_name": name, "s_school": school, "s_sub": subject})
                    st.rerun()

    elif 'exam_active' in st.session_state:
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        rem = max(0, 2400 - int(time.time() - st.session_state.start_time))
        
        st.subheader(f"Q{curr+1} of {len(q_df)} | ⏳ {rem//60:02d}:{rem%60:02d}")
        
        row = q_df.iloc[curr]
        st.write(f"### {row['question']}")
        opts = [row['a'], row['b'], row['c'], row['d']]
        ans_idx = opts.index(st.session_state.user_answers[curr]) if curr in st.session_state.user_answers else None
        choice = st.radio("Select answer:", opts, index=ans_idx, key=f"q{curr}")
        if choice: st.session_state.user_answers[curr] = choice

        st.divider()
        b1, b2, b3 = st.columns([1, 2, 1])
        if curr > 0: b1.button("⬅️ Back", on_click=lambda: st.session_state.update({"current_q": curr-1}))
        if curr < len(q_df)-1: b3.button("Next ➡️", on_click=lambda: st.session_state.update({"current_q": curr+1}))
        else:
            if b3.button("🏁 FINISH", type="primary"):
                score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
                try: supabase.table("leaderboard").insert({"name": f"{st.session_state.s_name} || {st.session_state.s_school} || {st.session_state.s_sub}", "score": score}).execute()
                except: pass
                st.session_state.final_score = score
                st.session_state.total_qs = len(q_df)
                del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        perc = (st.session_state.final_score / st.session_state.total_qs) * 100
        
        # --- NEW CELEBRATION LOGIC ---
        if perc >= 80:
            st.balloons()
            st.success(f"🎉 EXCELLENT! You scored {perc:.0f}%. You are ready for the main exam!")
        elif perc >= 50:
            st.info(f"👍 GOOD ATTEMPT! You scored {perc:.0f}%. A little more study and you'll hit 90%!")
        else:
            st.warning(f"📚 STUDY HARDER! You scored {perc:.0f}%. Review the corrections below carefully.")

        # --- RETAKE BUTTON ---
        if st.button("🔄 RETAKE THIS EXAM"):
            st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "start_time": time.time()})
            del st.session_state['final_score']; st.rerun()

        st.subheader("📝 Script Review & AI Insights")
        for i, row in st.session_state.quiz_data.iterrows():
            u_ans = st.session_state.user_answers.get(i, "None")
            is_right = u_ans == row['correct_answer']
            with st.expander(f"Q{i+1}: {'✅' if is_right else '❌'}"):
                st.write(f"**Q:** {row['question']}")
                st.write(f"**Correct:** {row['correct_answer']} | **Yours:** {u_ans}")
                st.info(f"💡 **AI Insight:** {row.get('explanation', 'Consult your notes for this topic.')}")
        
        if st.button("Logout"): st.session_state.clear(); st.rerun()

# --- 4. TEACHER PORTAL (Fixed Loading issues) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    if st.text_input("PIN", type="password") == "Lagos2026":
        try:
            # Direct fetch with no cache for instant results
            response = supabase.table("leaderboard").select("*").order("created_at", desc=True).execute()
            if response.data:
                res_df = pd.DataFrame(response.data)
                
                # Safer parsing for rows that might be formatted differently
                def parse_meta(val):
                    parts = val.split(' || ')
                    return parts if len(parts) == 3 else [val, "N/A", "N/A"]

                meta = res_df['name'].apply(parse_meta)
                res_df['Student'] = [m[0] for m in meta]
                res_df['School'] = [m[1] for m in meta]
                res_df['Subject'] = [m[2] for m in meta]

                st.write("### 📊 Live Results")
                st.dataframe(res_df[['Student', 'School', 'Subject', 'score', 'created_at']], use_container_width=True)
                
                st.divider()
                st.subheader("🔍 Individual Performance Script")
                student_choice = st.selectbox("View analysis for:", ["-- Choose --"] + res_df['Student'].unique().tolist())
                if student_choice != "-- Choose --":
                    row = res_df[res_df['Student'] == student_choice].iloc[0]
                    st.metric("Score", f"{row['score']}")
                    st.write(f"**Subject:** {row['Subject']} | **School:** {row['School']}")
                    st.write("Performance: " + ("Ready" if int(row['score']) > 7 else "Needs Improvement"))
            else: st.info("No data available yet.")
        except Exception as e:
            st.error(f"Error connecting to data: {e}. Please refresh the page.")

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Access")
    child = st.text_input("Child's Full Name")
    schl = st.text_input("Child's School")
    if st.button("Search Result"):
        res = supabase.table("leaderboard").select("*").execute()
        matches = [r for r in res.data if child.lower() in r['name'].lower() and schl.lower() in r['name'].lower()]
        if matches:
            st.success(f"Result found for {child}")
            st.table(pd.DataFrame(matches)[['score', 'created_at']])
        else: st.error("No exact match found.")
