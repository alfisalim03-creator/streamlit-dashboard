import streamlit as st
import pandas as pd
import json
from google.oauth2.service_account import Credentials
import gspread

# Memaksa tampilan layar penuh (mengatasi masalah Google Sites)
st.set_page_config(page_title="Dashboard SBU", layout="wide")

st.title("Dashboard Performa Telecollection & Anti-Churn")

# Mengambil kredensial dari sistem rahasia Streamlit (bukan dari file lokal)
key_dict = json.loads(st.secrets["textkey"])
creds = Credentials.from_service_account_info(key_dict, scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

# Membuka Google Sheets (Ganti dengan nama file atau URL sheet Anda)
sheet = client.open("Data Pencapaian Collection 2026").sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Menampilkan data dalam tabel lebar dan membuat filter
st.dataframe(df, use_container_width=True)
