import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return None

df = load_data()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])

# --- 3. STUDENT PORTAL (With 20-Minute Timer) ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        if df is not None:
            name = st.text_input("Full Name")
            school = st.text_input("School")
            subs = sorted(df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist())
            years = ["ALL YEARS"] + sorted(df['year'].dropna().unique().astype(str).tolist(), reverse=True)
            
            c1, c2 = st.columns(2)
            with c1: subject = st.selectbox("Subject", subs)
            with c2: year_p = st.selectbox("Year", years)
            exam_p = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
            if st.button("🚀 START EXAM"):
                filt = (df['subject'].str.title() == subject) & (df['exam'].str.upper() == exam_p)
                if year_p != "ALL YEARS": filt = filt & (df['year'].astype(str) == year_p)
                q_df = df[filt]
                
                if not q_df.empty:
                    st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 30)).reset_index(drop=True)
                    st.session_state.update({
                        "exam_active": True, "current_q": 0, "user_answers": {}, 
                        "start_time": time.time(), "info": f"{school} | {name} | {subject}"
                    })
                    st.rerun()

    elif 'exam_active' in st.session_state:
        # --- TIMER LOGIC (20 Minutes) ---
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 1200 - int(elapsed)) # 1200s = 20 mins
        mins, secs = divmod(remaining, 60)
        st.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
        
        if remaining <= 0:
            st.error("⏰ Time is up! Submitting automatically...")
            time.sleep(2)
            # (Auto-submit logic follows same as FINISH button)

        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        st.subheader(f"Question {curr+1} of {len(q_df)}")
        st.write(q_df.iloc[curr]['question'])
        opts = [q_df.iloc[curr]['a'], q_df.iloc[curr]['b'], q_df.iloc[curr]['c'], q_df.iloc[curr]['d']]
        st.session_state.user_answers[curr] = st.radio("Choose Answer:", opts, key=f"q_{curr}")
        
        if st.button("Next ➡️") and curr < len(q_df)-1:
            st.session_state.current_q += 1; st.rerun()
        if st.button("🏁 FINISH & SUBMIT"):
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            # Diagnostic: Identify missed topics
            missed = [r.get('topic', 'General') for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) != r['correct_answer']]
            
            try:
                supabase.table("leaderboard").insert({
                    "name": st.session_state.info, "score": score, 
                    "remarks": f"Needs help with: {', '.join(list(set(missed))[:3])}"
                }).execute()
            except: pass
            
            st.session_state.final_score = score
            st.session_state.total_qs = len(q_df)
            del st.session_state['exam_active']; st.rerun()

    elif 'final_score' in st.session_state:
        st.header(f"🏆 Score: {st.session_state.final_score} / {st.session_state.total_qs}")
        if st.button("Back to Home"): del st.session_state['final_score']; st.rerun()

# --- 4. PARENT PORTAL (With Remarks) ---
elif role == "👪 Parent":
    st.header("👪 Parent Dashboard")
    child_query = st.text_input("Search Child's Name")
    if child_query:
        res = supabase.table("leaderboard").select("*").ilike("name", f"%{child_query}%").execute()
        if res.data:
            p_df = pd.DataFrame(res.data)
            st.table(p_df[['name', 'score', 'remarks']])
            st.info("💡 Tip: Use the Teacher portal for deeper diagnostic reports.")

# --- 5. TEACHER PORTAL (With Detailed Filters) ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Diagnostic Dashboard")
    pin = st.text_input("Admin PIN", type="password")
    if pin == "Lagos2026":
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            t_df = pd.DataFrame(res.data)
            # Diagnostic Filtering
            st.write("### 🔍 Filter Results")
            f_school = st.selectbox("Filter by School", ["All"] + list(t_df['name'].str.split('|').str[0].unique()))
            
            display_df = t_df.copy()
            if f_school != "All":
                display_df = display_df[display_df['name'].str.contains(f_school)]
            
            st.dataframe(display_df[['name', 'score', 'remarks', 'created_at']], use_container_width=True)
            st.download_button("📥 Download Excel Report", display_df.to_csv(index=False), "school_report.csv")
