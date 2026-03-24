import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONNECTIONS ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)

# Using the Public Web Link you provided
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

@st.cache_data(ttl=10)
def load_data():
    try: 
        # We load the data and immediately force all headers to lowercase
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except:
        return None

df = load_data()

# --- 2. THE UI ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")

# Portal Selector in Sidebar
with st.sidebar:
    st.title("VikidylEdu")
    role = st.selectbox("Portal", ["✍️ Student", "👪 Parent", "👨‍🏫 Teacher"])
    
    # Connection Status
    if df is not None:
        st.success("✅ System Ready")
    else:
        st.error("⏳ System Loading...")

# --- 3. STUDENT PORTAL ---
if role == "✍️ Student":
    st.header("📝 Student Login")
    
    # SAFETY CHECK: Only try to show subjects if 'df' is ready and has 'subject'
    if df is not None and 'subject' in df.columns:
        name = st.text_input("Full Name")
        school = st.text_input("School")
        
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox("Subject", sorted(df['subject'].unique()))
        with c2:
            exam = st.selectbox("Exam Type", ["JAMB", "WAEC", "NECO", "BECE"])
            
        if st.button("🚀 Start Exam"):
            if name and school:
                st.session_state.exam_started = True
                st.success(f"Welcome {name}! Loading questions...")
            else:
                st.warning("Please fill in your details.")
    else:
        # This replaces the Crash Box with a helpful message
        st.info("The exam database is currently updating. Please wait 10 seconds and refresh.")
        if df is not None:
            st.write("Checking columns... Found:", list(df.columns))

# --- 4. PARENT PORTAL ---
elif role == "👪 Parent":
    st.header("👪 Parent Portal")
    st.write("Search for student results below:")
    try:
        res = supabase.table("leaderboard").select("name, score").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        else:
            st.info("No results recorded yet.")
    except:
        st.error("Unable to reach the results server.")
