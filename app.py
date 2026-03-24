import streamlit as st
import pandas as pd
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
        if data is not None:
            # Clean headers: remove spaces and lowercase
            data.columns = [str(c).strip().lower() for c in data.columns]
            return data
    except:
        return None
    return None

df = load_data()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    if df is not None:
        st.success("✅ System Connected")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("✍️ Student Registration")
        
        if df is not None and 'subject' in df.columns:
            name = st.text_input("Full Name")
            school = st.text_input("School")
            
            # Clean subject list
            subs = sorted(df['subject'].dropna().astype(str).str.strip().str.title().unique().tolist())
            
            c1, c2 = st.columns(2)
            with c1:
                subject = st.selectbox("Select Subject", subs)
            with c2:
                exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
                
            if st.button("🚀 START EXAM"):
                if name and school:
                    # DYNAMIC FILTER: Looks for 'exam' or 'exam type'
                    exam_col = 'exam' if 'exam' in df.columns else 'exam type'
                    
                    if exam_col in df.columns:
                        filt = (df['subject'].str.title() == subject) & (df[exam_col].str.upper() == exam_type)
                        q_df = df[filt]
                        
                        if not q_df.empty:
                            st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 10)).reset_index(drop=True)
                            st.session_state.update({
                                "exam_active": True, "current_q": 0, "user_answers": {}, 
                                "student_info": f"{school} | {name} | {subject}"
                            })
                            st.rerun()
                        else:
                            st.warning(f"No questions found for {subject} in {exam_type}.")
                    else:
                        st.error(f"Could not find an 'exam' column in your sheet. Found: {list(df.columns)}")
                else:
                    st.error("Please fill in your name and school.")
        else:
            st.info("🔄 Loading database...")

    elif 'exam_active' in st.session_state:
        # (Standard exam engine logic follows...)
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        row = q_df.iloc[curr]
        st.subheader(f"Question {curr + 1}")
        st.write(row['question'])
        options = [row['a'], row['b'], row['c'], row['d']]
        st.session_state.user_answers[curr] = st.radio("Answer:", options, key=f"q_{curr}")
        if st.button("Next") and curr < len(q_df)-1:
            st.session_state.current_q += 1
            st.rerun()
        if st.button("🏁 FINISH"):
            del st.session_state['exam_active']
            st.rerun()

# --- 4. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Dashboard")
    try:
        res = supabase.table("leaderboard").select("*").execute()
        st.dataframe(pd.DataFrame(res.data)[['name', 'score']], use_container_width=True)
    except:
        st.write("Loading results...")
