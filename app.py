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

# Verified CSV Link (Ends in output=csv)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        if data.empty: return None
        # This cleans headers in case there are still hidden spaces
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except Exception as e:
        return None

df = load_data()

# --- 2. HELPERS ---
def create_docx(name, score, total, script):
    doc = Document()
    doc.add_heading('VikidylEdu CBT - Report Card', 0)
    doc.add_paragraph(f"Student: {name}")
    doc.add_paragraph(f"Score: {score} / {total}")
    for i, item in enumerate(script):
        doc.add_heading(f"Question {i+1}", level=2)
        doc.add_paragraph(f"Q: {item.get('q', 'N/A')}")
        status = "✅ CORRECT" if item.get('ok') else "❌ INCORRECT"
        doc.add_paragraph(f"Result: {status} | Correct Answer: {item.get('ca', 'N/A')}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    st.divider()
    if df is not None:
        st.success("✅ Database Online")
    else:
        st.warning("⏳ Connecting to Database...")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("📝 Registration")
        sch = st.text_input("School Name:")
        nm = st.text_input("Full Name:")
        
        # SAFETY SHIELD: Only show selectors if 'subject' is found
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
                    else: st.warning("No questions found for this selection.")
                else: st.error("Please fill Name and School.")
        else:
            st.info("Searching for subject data... Please wait a moment.")
            if df is not None:
                st.warning(f"Note: Could not find 'subject' column. Found: {list(df.columns)}")

    elif 'exam_active' in st.session_state:
        q_df, curr = st.session_state.quiz_data, st.session_state.current_q
        row = q_df.iloc[curr]
        st.subheader(f"Question {curr+1}")
        st.write(row['question'])
        st.session_state.user_answers[curr] = st.radio("Select Answer:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        if st.button("Next Question") and curr < len(q_df)-1:
            st.session_state.current_q += 1; st.rerun()
        if st.button("🏁 FINISH EXAM"):
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}).execute()
            st.session_state.final_score = score
            del st.session_state['exam_active']; st.rerun()

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Results Portal")
    st.write("Check your child's performance below.")
    try:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            st.table(pd.DataFrame(res.data)[['name', 'score']])
        else:
            st.info("No exam records found yet.")
    except:
        st.error("Could not load results at this time.")

# --- 6. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    if st.text_input("Admin Pin:", type="password") == "Lagos2026":
        st.success("Welcome, Admin")
        # Add teacher controls here
