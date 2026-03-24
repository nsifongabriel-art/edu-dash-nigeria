import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- 1. DATABASE SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# Your verified CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        if data.empty: return None
        # CLEANER: Force all headers to lowercase and remove spaces
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except Exception as e:
        return None

df = load_data()

# --- 2. UI LAYOUT ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")

with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    st.divider()
    
    # DEBUG TOOL IN SIDEBAR
    if df is not None:
        st.success("✅ Database Online")
        if 'subject' not in df.columns:
            st.error(f"Error: No 'subject' column. I found: {list(df.columns)}")
    else:
        st.warning("⏳ Database Offline. Check CSV link.")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    st.header("📝 Student Registration")
    
    # SAFETY SHIELD: Only show selectors if 'subject' column exists
    if df is not None and 'subject' in df.columns:
        sch = st.text_input("School Name:")
        nm = st.text_input("Full Name:")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            yrs = ["ALL YEARS"] + sorted(df['year'].unique().astype(str).tolist(), reverse=True)
            yr = st.selectbox("Year", yrs)
        with c2:
            exm = st.selectbox("Exam", ["JAMB", "WAEC", "NECO", "BECE"])
        with c3:
            # THIS IS THE FIX: This line will no longer crash
            sub_list = sorted(df['subject'].unique().tolist())
            sub = st.selectbox("Subject", sub_list)
            
        if st.button("🚀 START"):
            st.info("Exam starting...")
    else:
        st.error("Cannot load registration. Please check Google Sheet column headers.")

# --- 4. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Dashboard")
    st.write("Results will appear here.")
