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

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=2)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        if data.empty: return None
        # FORCE CLEANING: Removes spaces, invisible marks, and makes everything lowercase
        data.columns = [str(c).strip().lower().replace(' ', '') for c in data.columns]
        return data
    except Exception as e:
        st.session_state['err_msg'] = str(e)
        return None

df = load_data()

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    st.divider()
    if df is not None:
        st.success("✅ Database Online")
        # DEBUGGER: If it crashes, this will show us why
        if 'subject' not in df.columns:
            st.error(f"Missing 'subject' column! Found: {list(df.columns)}")
    else:
        st.warning("⏳ Connecting...")

# --- 3. STUDENT PORTAL (ANTI-CRASH) ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("📝 Registration")
        sch = st.text_input("School Name:")
        nm = st.text_input("Full Name:")
        
        # SAFETY CHECK: Only proceed if df exists AND has 'subject'
        if df is not None and 'subject' in df.columns:
            c1, c2, c3 = st.columns(3)
            with c1:
                yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True)
                yr = st.selectbox("Year", yrs)
            with c2:
                exm = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
            with c3:
                sub_list = sorted(df['subject'].unique().tolist())
                sub = st.selectbox("Subject", sub_list)

            if st.button("🚀 START"):
                if sch and nm:
                    filt = (df['subject'].str.upper() == sub.upper()) & (df['exam'].str.upper() == exm.upper())
                    if yr != "ALL YEARS": filt &= (df['year'].astype(str) == yr)
                    q_df = df[filt]
                    if not q_df.empty:
                        st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 20)).reset_index(drop=True)
                        st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "db_id": f"{sch}|{nm}|{sub}"})
                        st.rerun()
                    else: st.warning("No questions found.")
        elif df is not None:
            st.error("The Google Sheet headers are incorrect. Please check the sidebar for the error.")
        else:
            st.info("Loading questions...")

# (Remaining logic for Parent/Teacher remains same)
