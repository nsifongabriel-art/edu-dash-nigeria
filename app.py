import streamlit as st
import pandas as pd
import time
import json
from supabase import create_client, Client
from docx import Document
from io import BytesIO

# --- 1. SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# Verified CSV Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        if data.empty: return None
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

df = load_data()

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    # RESTORED PORTAL OPTIONS
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    st.divider()
    if df is not None:
        st.success("✅ Database Online")
    else:
        st.warning("⏳ Connecting to Database...")

# --- 3. PARENT PORTAL (RESTORED) ---
if role == "👪 Parent":
    st.header("👪 Parent Dashboard")
    st.info("Search for your child's name to see their latest scores.")
    
    search_nm = st.text_input("Enter Student Full Name:")
    res = supabase.table("leaderboard").select("*").execute()
    
    if res.data:
        p_df = pd.DataFrame(res.data)
        if search_nm:
            p_df = p_df[p_df['name'].str.contains(search_nm, case=False, na=False)]
        st.dataframe(p_df[['name', 'score', 'total_q']], use_container_width=True)
    else:
        st.write("No results found in the system yet.")

# --- 4. STUDENT PORTAL (FIXED CRASH) ---
elif role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("📝 Registration")
        
        # UI Fields
        sch = st.text_input("School Name:")
        nm = st.text_input("Full Name:")
        
        # CRASH PREVENTION: Only run these if df is ready
        if df is not None:
            c1, c2, c3 = st.columns(3)
            with c1:
                yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True)
                yr = st.selectbox("Year", yrs)
            with c2:
                exm = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            with c3:
                # This line was crashing in your screenshot
                sub_list = sorted(df['subject'].unique().tolist())
                sub = st.selectbox("Subject", sub_list)

            if st.button("🚀 START"):
                if sch and nm:
                    filt = (df['subject'].str.upper() == sub.upper()) & (df['exam'].str.upper() == exm.upper())
                    if yr != "ALL YEARS": filt &= (df['year'].astype(str) == yr)
                    q_df = df[filt]
                    if not q_df.empty:
                        st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 20)).reset_index(drop=True)
                        st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "db_id": f"{sch} | {nm} | {sub}"})
                        st.rerun()
                    else: st.warning("No questions available for this selection.")
                else: st.error("Please fill in School and Name.")
        else:
            st.info("Fetching subjects from Google Sheets... please wait.")

    # (Exam logic follows here...)
