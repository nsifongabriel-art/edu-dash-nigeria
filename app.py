import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# Your Public Web Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        # Added error handling directly in the loader
        data = pd.read_csv(SHEET_URL)
        if data is not None:
            data.columns = [str(c).strip().lower() for c in data.columns]
            return data
    except:
        return None
    return None

df = load_data()

# --- 2. SIDEBAR (PORTALS ARE BACK) ---
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
    st.header("📝 Student Login")
    
    # THE SAFETY SHIELD: This prevents line 50 from ever crashing again
    if df is not None and 'subject' in df.columns:
        name = st.text_input("Full Name")
        school = st.text_input("School")
        
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox("Select Subject", sorted(df['subject'].unique().tolist()))
        with c2:
            exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
        if st.button("🚀 START EXAM"):
            if name and school:
                st.session_state.started = True
                st.info("Preparing your questions...")
            else:
                st.error("Please enter your name and school.")
    else:
        # Instead of a crash, the user sees this
        st.info("The exam database is refreshing. Please wait about 10 seconds.")
        if df is not None:
            st.write("Headers found:", list(df.columns))

# --- 4. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Portal")
    st.write("Latest Student Performance Records:")
    try:
        res = supabase.table("leaderboard").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data)[['name', 'score']], use_container_width=True)
        else:
            st.info("No records found yet.")
    except:
        st.write("Fetching results...")
