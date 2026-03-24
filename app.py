import streamlit as st
import pandas as pd
import time
import json
from supabase import create_client, Client
from docx import Document
from io import BytesIO

# --- 1. SETUP & DATA LOADING ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# YOUR VERIFIED CSV LINK
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=1)
def load_data():
    try: 
        # Attempt to load CSV
        data = pd.read_csv(SHEET_URL)
        if data.empty: return None
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except Exception as e:
        # This will show us the real error in the sidebar if it fails
        st.session_state['db_error'] = str(e)
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

# --- 3. SIDEBAR (Portal Selection) ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    # THE MISSING PARENTS SECTION IS BACK
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    
    st.divider()
    if df is not None:
        st.success("✅ Database: Connected")
    else:
        st.error("❌ Database: Offline")
        if 'db_error' in st.session_state:
            st.info(f"Error: {st.session_state['db_error']}")

# --- 4. STUDENT PORTAL ---
if role == "✍️ Student":
    if 'exam_active' not in st.session_state and 'final_score' not in st.session_state:
        st.header("📝 Registration")
        c1, c2 = st.columns(2)
        sch = c1.text_input("School Name:")
        nm = c2.text_input("Full Name:")
        
        # CRASH PROTECTION: Check if df exists before making lists
        if df is not None:
            yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True)
            yr = st.selectbox("Exam Year", yrs)
            exm = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            sub_list = sorted(df['subject'].unique().tolist())
            sub = st.selectbox("Select Subject", sub_list)
            
            if st.button("🚀 START EXAM"):
                if sch and nm:
                    filt = (df['subject'].str.upper() == sub.upper()) & (df['exam'].str.upper() == exm.upper())
                    if yr != "ALL YEARS": filt &= (df['year'].astype(str) == yr)
                    q_df = df[filt]
                    if not q_df.empty:
                        st.session_state.quiz_data = q_df.sample(n=min(len(q_df), 20)).reset_index(drop=True)
                        st.session_state.update({"exam_active": True, "current_q": 0, "user_answers": {}, "db_id": f"{sch}|{nm}|{sub}"})
                        st.rerun()
                    else: st.warning("No questions found for this selection.")
                else: st.error("Please enter School and Name.")
        else:
            st.warning("Please wait for the database to connect...")

    elif 'exam_active' in st.session_state:
        # (Standard Exam logic)
        q_df = st.session_state.quiz_data
        curr = st.session_state.current_q
        row = q_df.iloc[curr]
        st.write(f"Question {curr+1} of {len(q_df)}")
        st.subheader(row['question'])
        st.session_state.user_answers[curr] = st.radio("Choose:", [row['a'], row['b'], row['c'], row['d']], key=f"q_{curr}")
        
        if st.button("Next") and curr < len(q_df)-1: 
            st.session_state.current_q += 1; st.rerun()
        if st.button("🏁 FINISH"):
            # Scoring logic and save to Supabase
            score = sum(1 for i, r in q_df.iterrows() if st.session_state.user_answers.get(i) == r['correct_answer'])
            supabase.table("leaderboard").upsert({"name": st.session_state.db_id, "score": score}).execute()
            st.session_state.final_score = score
            del st.session_state['exam_active']; st.rerun()

# --- 5. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Dashboard")
    st.write("View the latest student performance records below.")
    res = supabase.table("leaderboard").select("name, score").execute()
    if res.data:
        p_df = pd.DataFrame(res.data)
        st.dataframe(p_df, use_container_width=True)
    else:
        st.info("No records found yet.")

# --- 6. TEACHER PORTAL ---
elif role == "👨‍🏫 Teacher":
    st.header("👨‍🏫 Teacher Administration")
    if st.text_input("Enter Teacher Pin:", type="password") == "Lagos2026":
        st.success("Access Granted")
        # Add Admin tools here
