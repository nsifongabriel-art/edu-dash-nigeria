import streamlit as st
import pandas as pd
import time
import json
import plotly.express as px
from supabase import create_client, Client

# --- SETUP ---
URL = "https://tmbtnbxrrylulhgvnfjj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYnRuYnhycnlsdWxoZ3ZuZmpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxMDQ2ODcsImV4cCI6MjA4OTY4MDY4N30.Fd1TPTCjN2u-_EOmkkqOb3TAKW8Q5RGv0AtAA85jW4s"
supabase: Client = create_client(URL, KEY)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeTbSBHxYsciOesGpXt6ATZm_5aWVHQrS7tIFIaibmU4MZU-otPRsxUXG4egEP7P7jXdtL6CHhytAw/pub?output=csv"

MASTER_SUBJECTS = ["MATHEMATICS", "ENGLISH LANGUAGE", "BIOLOGY", "PHYSICS", "CHEMISTRY", "ECONOMICS", "GOVERNMENT", "LITERATURE", "CIVIC EDUCATION", "COMMERCE", "AGRIC SCIENCE", "GEOGRAPHY", "CRS", "IRS", "HISTORY", "COMPUTER STUDIES"]

@st.cache_data(ttl=1)
def load_data():
    try: 
        data = pd.read_csv(SHEET_URL)
        data.columns = [str(c).strip().lower() for c in data.columns]
        return data
    except: return pd.DataFrame()

df = load_data()

# --- UI STYLING ---
st.set_page_config(page_title="VikidylEdu CBT", layout="wide")
st.markdown("""<style>
    .winner-box { background-color: #FFD700; padding: 10px; border-radius: 10px; color: #000; text-align: center; font-weight: bold; margin-bottom: 8px; border: 1px solid #DAA520; }
    .passage-box { background-color: #f8fafc; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; border: 1px solid #cbd5e1; }
</style>""", unsafe_allow_html=True)

# --- SIDEBAR & WALL OF FAME ---
with st.sidebar:
    st.title("VikidylEdu")
    st.markdown("### 🏆 Top Performers")
    try:
        ld_res = supabase.table("leaderboard").select("name, score").order("score", desc=True).limit(3).execute()
        if ld_res.data:
            for i, entry in enumerate(ld_res.data):
                short_name = entry['name'].split('|')[1].strip() if '|' in entry['name'] else entry['name']
                st.markdown(f"<div class='winner-box'>#{i+1} {short_name}: {entry['score']}</div>", unsafe_allow_html=True)
        else: st.info("Leaderboard will appear after the first submission.")
    except: st.caption("Leaderboard offline.")
    
    st.divider()
    role = st.selectbox("Switch Portal", ["✍️ Student", "👨‍🏫 Teacher", "👨‍👩‍👧 Parent"])

# --- TEACHER PORTAL (FIXED) ---
if role == "👨‍🏫 Teacher":
    st.header("Teacher Diagnostic Suite")
    if st.text_input("Enter Access Key:", type="password") == "Lagos2026":
        try:
            res = supabase.table("leaderboard").select("*").execute()
            if res.data and len(res.data) > 0:
                ld = pd.DataFrame(res.data)
                
                # Show Table
                st.subheader("Class Overview")
                st.dataframe(ld[['name', 'score']])
                
                # Show Analytics
                st.subheader("Subject Analysis")
                ld['Subject'] = ld['name'].apply(lambda x: x.split('|')[2].strip() if '|' in x else "General")
                fig = px.bar(ld.groupby('Subject')['score'].mean().reset_index(), x='Subject', y='score', color='Subject')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No student data found in the database yet.")
        except Exception as e:
            st.error(f"Error connecting to database: {e}")

# --- PARENT PORTAL (FIXED) ---
elif role == "👨‍👩‍👧 Parent":
    st.header("Parent Progress Report")
    search_name = st.text_input("Search Child's Full Name:")
    if search_name:
        try:
            res = supabase.table("leaderboard").select("*").execute()
            if res.data:
                ld = pd.DataFrame(res.data)
                child_data = ld[ld['name'].str.contains(search_name, case=False)]
                if not child_data.empty:
                    st.success(f"Results found for {search_name}:")
                    st.table(child_data[['name', 'score']])
                else:
                    st.warning("No records found for this name.")
        except: st.error("Database connection error.")

# --- STUDENT PORTAL ---
else:
    # (Student exam logic from previous versions goes here)
    st.header("Student Exam Hall")
    st.info("Please fill the form and select a subject to begin.")
    # ... Rest of student code ...
