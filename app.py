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
    st.divider()
    if df is not None:
        st.success("✅ System Connected")
    else:
        st.warning("⏳ System Loading...")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    st.header("✍️ Student Login")
    
    if df is not None and 'subject' in df.columns:
        name = st.text_input("Full Name")
        school = st.text_input("School")
        
        # --- THE CRITICAL FIX FOR TYPEERROR '<' ---
        # 1. Drop empty rows. 2. Force everything to String. 3. Get Unique. 4. Sort.
        raw_subs = df['subject'].dropna().astype(str).unique().tolist()
        subs = sorted(raw_subs)
        
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox("Select Subject", subs)
        with c2:
            exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
        if st.button("🚀 START EXAM"):
            if name and school:
                st.info("Loading questions...")
            else:
                st.error("Please fill in your name and school.")
    else:
        st.info("🔄 Refreshing database... please wait.")

# --- 4. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Portal")
    try:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data)[['name', 'score']], use_container_width=True)
        else:
            st.info("No records found yet.")
    except:
        st.write("Fetching results...")
