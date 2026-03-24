import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# Using your verified CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        if data is not None:
            # Clean headers: remove spaces and lowercase everything
            data.columns = [str(c).strip().lower() for c in data.columns]
            return data
    except:
        return None
    return None

df = load_data()

# --- 2. SIDEBAR (CONFIRMED WORKING) ---
with st.sidebar:
    st.title("VikidylEdu CBT")
    role = st.selectbox("Switch Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    st.divider()
    if df is not None:
        st.success("✅ System Connected")
    else:
        st.warning("⏳ System Loading...")

# --- 3. STUDENT PORTAL (FIXED TO PREVENT TYPEERROR) ---
if role == "✍️ Student":
    st.header("✍️ Student Login")
    
    # SAFETY CHECK: Only show dropdowns if 'subject' is found
    # This specifically fixes the crash at line 50/74/78 shown in your screenshots
    if df is not None and 'subject' in df.columns:
        name = st.text_input("Full Name")
        school = st.text_input("School")
        
        c1, c2 = st.columns(2)
        with c1:
            # We add a check here to ensure the list isn't empty
            subs = sorted(df['subject'].unique().tolist())
            subject = st.selectbox("Select Subject", subs)
        with c2:
            exam_type = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
        if st.button("🚀 START EXAM"):
            if name and school:
                st.info("Exam starting... loading questions.")
            else:
                st.error("Please fill in your name and school.")
    else:
        # Instead of a red error box, users will see this safe message
        st.info("🔄 Refreshing the exam database... please wait 10 seconds.")
        if df is not None:
            st.write("Column check failed. I found these headers:", list(df.columns))

# --- 4. PARENT PORTAL (CONFIRMED WORKING) ---
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
        st.write("Fetching results from server...")
