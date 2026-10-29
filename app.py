import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from google.oauth2.service_account import Credentials
import gspread

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Dashboard Pencapaian Collection",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kustomisasi CSS untuk mempercantik UI dan menyembunyikan elemen bawaan Streamlit
st.markdown("""
<style>
    /* Menyembunyikan menu burger dan footer default Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Styling untuk Kartu Metrik (KPI) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Memberi warna khusus pada border kiri setiap metrik seperti di HTML asli */
    div[data-testid="metric-container"]:nth-child(1) { border-left: 5px solid #10b981; } /* Hijau - Revenue */
    div[data-testid="metric-container"]:nth-child(2) { border-left: 5px solid #4f46e5; } /* Ungu - Pelanggan */
    div[data-testid="metric-container"]:nth-child(3) { border-left: 5px solid #0ea5e9; } /* Biru - Telecollection */
    div[data-testid="metric-container"]:nth-child(4) { border-left: 5px solid #6366f1; } /* Nila - Retention */
    div[data-testid="metric-container"]:nth-child(5) { border-left: 5px solid #10b981; } /* Hijau - Winback */
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI MENGAMBIL DATA DARI GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=300) # Data di-cache selama 5 menit agar cepat, namun akan update jika di-refresh
def load_data():
    try:
        # Mengambil kredensial dari Streamlit Secrets
        key_dict = json.loads(st.secrets["textkey"])
        creds = Credentials.from_service_account_info(key_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        
        # Buka Spreadsheet (Pastikan nama ini SAMA PERSIS dengan di Google Drive)
        workbook = client.open("Data Pencapaian Collection 2026")
        
        # Mengambil data dari tab "SLA3" (Ubah nama sheet jika berbeda)
        sheet_sla3 = workbook.worksheet("SLA3").get_all_records()
        df_sla3 = pd.DataFrame(sheet_sla3)
        
        # Mengambil data dari tab "Progres" (Ubah nama sheet jika berbeda)
        try:
            sheet_progres = workbook.worksheet("Progres").get_all_records()
            df_progres = pd.DataFrame(sheet_progres)
        except Exception:
            df_progres = pd.DataFrame() # Kosongkan jika tab tidak ditemukan
            
        return df_sla3, df_progres
    
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Tampilkan status memuat data
with st.spinner("Sinkronisasi data dari server..."):
    df_sla3, df_progres = load_data()

# ==========================================
# 3. HELPER FUNCTION (Pemformatan Angka)
# ==========================================
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

def format_compact(angka):
    if angka >= 1_000_000_000:
        return f"Rp {angka / 1_000_000_000:.1f} M"
    elif angka >= 1_000_000:
        return f"Rp {angka / 1_000_000:.1f} Jt"
    return format_rupiah(angka)

# Pastikan kolom tanggal berformat datetime
if not df_sla3.empty:
    df_sla3['Tanggal'] = pd.to_datetime(df_sla3['Tanggal'], errors='coerce')
    df_sla3['Periode'] = df_sla3['Tanggal'].dt.strftime('%B %Y')
    df_sla3 = df_sla3.dropna(subset=['Tanggal'])

# ==========================================
# 4. TAMPILAN HEADER & TAB
# ==========================================
st.title("Dashboard Pencapaian Collection")
st.markdown("Monitoring Pencapaian, Efektifitas, dan Progres Tagihan Nasional.")

# Tombol Sinkronisasi Manual
if st.button("🔄 Sinkronkan Data"):
    st.cache_data.clear()
    st.rerun()
st.divider()

# Membuat Tab Layout seperti di HTML
tab1, tab2 = st.tabs(["Pencapaian Collection (DataAgregat)", "Progres Tagihan"])

# ==========================================
# TAB 1: PENCAPAIAN COLLECTION (SLA 3)
# ==========================================
with tab1:
    if df_sla3.empty:
        st.warning("Data SLA 3 tidak tersedia atau kosong.")
    else:
        # --- KONTROL FILTER ---
        col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
        
        with col_f1:
            list_periode = ["Semua Periode"] + list(df_sla3['Periode'].unique())
            filter_periode = st.selectbox("Filter Periode", list_periode, key='p_sla3')
            
        with col_f2:
            list_region = ["Semua Region"] + sorted(list(df_sla3['Region'].unique()))
            filter_region = st.selectbox("Filter Region", list_region, key='r_sla3')
            
        with col_f3:
            min_date = df_sla3['Tanggal'].min().date()
            max_date = df_sla3['Tanggal'].max().date()
            start_date = st.date_input("Tanggal Mulai", value=min_date, key='sd_sla3')
            
        with col_f4:
            end_date = st.date_input("Tanggal Akhir", value=max_date, key='ed_sla3')

        # Logika Filter Data
        df_filtered = df_sla3.copy()
        if filter_periode != "Semua Periode":
            df_filtered = df_filtered[df_filtered['Periode'] == filter_periode]
        if filter_region != "Semua Region":
            df_filtered = df_filtered[df_filtered['Region'] == filter_region]
            
        df_filtered = df_filtered[(df_filtered['Tanggal'].dt.date >= start_date) & (df_filtered['Tanggal'].dt.date <= end_date)]

        st.markdown("<br>", unsafe_allow_html=True)

        # --- WADAH METRIK KPI (TOTAL & KATEGORI) ---
        total_rupiah = df_filtered['Rupiah'].sum()
        total_pelanggan = df_filtered['Pelanggan'].sum()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Keseluruhan Revenue", format_rupiah(total_rupiah))
        col_m2.metric("Total Keseluruhan Pelanggan", f"{total_pelanggan:,.0f} Plg")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Menghitung per kategori (Telecollection, Retention, Winback)
        tele_df = df_filtered[df_filtered['Type FU'].str.contains('tele', case=False, na=False)]
        ret_df = df_filtered[df_filtered['Type FU'].str.contains('reten', case=False, na=False)]
        win_df = df_filtered[df_filtered['Type FU'].str.contains('win', case=False, na=False)]

        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Telecollection (Revenue)", format_rupiah(tele_df['Rupiah'].sum()), f"{tele_df['Pelanggan'].sum():,.0f} Pelanggan", delta_color="off")
        col_k2.metric("Retention (Revenue)", format_rupiah(ret_df['Rupiah'].sum()), f"{ret_df['Pelanggan'].sum():,.0f} Pelanggan", delta_color="off")
        col_k3.metric("Winback (Revenue)", format_rupiah(win_df['Rupiah'].sum()), f"{win_df['Pelanggan'].sum():,.0f} Pelanggan", delta_color="off")

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- GRAFIK TREN (LINE CHART) ---
        st.subheader("📈 Tren Pencapaian")
        if not df_filtered.empty:
            # Agregasi data per tanggal
            tren_data = df_filtered.groupby('Tanggal')['Rupiah'].sum().reset_index()
            
            fig_tren = px.line(tren_data, x='Tanggal', y='Rupiah', 
                               markers=True, 
                               color_discrete_sequence=['#4f46e5'],
                               template="simple_white")
            
            fig_tren.update_layout(
                yaxis_title="Total Rupiah",
                xaxis_title="",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=10, b=0),
                height=350
            )
            # Custom formatter sumbu Y
            fig_tren.update_yaxes(tickprefix="Rp ")
            st.plotly_chart(fig_tren, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- WADAH BAWAH (BAR CHART & LEADERBOARD) ---
        col_b1, col_b2 = st.columns([1, 1.5])
        
        with col_b1:
            judul_bar = "🏆 Top Kinerja Region" if filter_region == "Semua Region" else f"🏆 Top Kinerja KP - Region {filter_region}"
            st.subheader(judul_bar)
            
            if not df_filtered.empty:
                # Drill-down logic: jika ALL Region, group by Region. Jika tidak, group by KP.
                group_col = 'Region' if filter_region == "Semua Region" else 'KP'
                
                bar_data = df_filtered.groupby(group_col)['Rupiah'].sum().reset_index()
                bar_data = bar_data.sort_values(by='Rupiah', ascending=True) # Ascending agar teratas di atas grafik bar
                
                bar_color = '#6366f1' if filter_region == "Semua Region" else '#10b981'
                
                fig_bar = px.bar(bar_data, x='Rupiah', y=group_col, orientation='h',
                                 color_discrete_sequence=[bar_color],
                                 template="simple_white")
                
                fig_bar.update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=10, b=0), height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
                
        with col_b2:
            st.subheader("Leaderboard Agen & Efektifitas")
            if not df_filtered.empty:
                # Agregasi data agen
                if 'Outbound' not in df_filtered.columns:
                    df_filtered['Outbound'] = df_filtered.get('Jumlah_Outbound', 0) # Fallback kolom
                
                lb_data = df_filtered.groupby(['Nama Agen']).agg(
                    Region=('Region', lambda x: ', '.join(set(x))),
                    Total_Rupiah=('Rupiah', 'sum'),
                    Total_Pelanggan=('Pelanggan', 'sum'),
                    Outbound=('Outbound', 'sum')
                ).reset_index()
                
                # Format Rupiah
                lb_data['Revenue'] = lb_data['Total_Rupiah'].apply(format_rupiah)
                
                # Hitung Efektifitas
                lb_data['Efektifitas'] = lb_data.apply(
                    lambda row: f"{(row['Total_Pelanggan'] / row['Outbound']) * 100:.1f}%" if row['Outbound'] > 0 else "-", 
                    axis=1
                )
                
                # Sortir default (berdasarkan Rupiah tertinggi)
                lb_data = lb_data.sort_values(by='Total_Rupiah', ascending=False).reset_index(drop=True)
                lb_data.index = lb_data.index + 1 # Jadikan index sebagai ranking (1, 2, 3...)
                
                # Tampilkan tabel yang elegan
                st.dataframe(
                    lb_data[['Nama Agen', 'Region', 'Outbound', 'Total_Pelanggan', 'Revenue', 'Efektifitas']],
                    use_container_width=True,
                    height=400
                )

# ==========================================
# TAB 2: PROGRES TAGIHAN
# ==========================================
with tab2:
    if df_progres.empty:
        st.info("Data Progres Tagihan tidak ditemukan di Google Sheets (Pastikan ada tab bernama 'Progres').")
    else:
        st.write("Fitur Progres Tagihan sedang dalam pengembangan penyesuaian tata letak...")
        # Jika Anda ingin menampilkan tabel mentah sementara
        st.dataframe(df_progres.head(50), use_container_width=True)
