import streamlit as st
import pandas as pd
import plotly.express as px
import json
from google.oauth2.service_account import Credentials
import gspread

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Dashboard Pencapaian Collection", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. SUNTIKAN CSS & ANIMASI (MENDUPLIKASI TAILWIND & HTML LAMA)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Mengubah font keseluruhan dan background */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #f8fafc; }
    
    /* Menyembunyikan elemen bawaan Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ANIMASI KUSTOM SEPERTI DI HTML ANDA */
    @keyframes rowFadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* KELAS UNTUK KARTU KPI */
    .kpi-card {
        background-color: white;
        padding: 1.25rem;
        border-radius: 1rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f5f9;
        opacity: 0;
        animation: rowFadeIn 0.6s ease forwards;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-title { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 0.25rem; }
    .kpi-value { font-size: 1.875rem; font-weight: 700; line-height: 1.2; margin: 0; }
    .kpi-sub { font-size: 0.875rem; font-weight: 500; margin-top: 0.25rem; }
    
    /* TABEL LEADERBOARD KUSTOM */
    .custom-table { width: 100%; border-collapse: collapse; text-align: left; }
    .custom-table th { background-color: #f8fafc; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #f1f5f9; }
    .custom-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #f1f5f9; }
    .animate-row { opacity: 0; animation: rowFadeIn 0.5s ease forwards; }
    .animate-row:hover { background-color: #f8fafc; }
    
    /* WADAH KARTU UNTUK GRAFIK */
    .chart-container {
        background-color: white; padding: 1.25rem; border-radius: 1rem; 
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); border: 1px solid #f1f5f9;
        opacity: 0; animation: rowFadeIn 0.8s ease forwards;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI PEMBANTU (UI KUSTOM)
# ==========================================
def render_kpi(title, value, subtext, border_hex, text_hex, sub_hex, delay_ms):
    html = f"""
    <div class="kpi-card" style="border-left: 4px solid {border_hex}; animation-delay: {delay_ms}ms;">
        <p class="kpi-title">{title}</p>
        <h3 class="kpi-value" style="color: {text_hex};">{value}</h3>
        <p class="kpi-sub" style="color: {sub_hex};">{subtext}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# ==========================================
# 4. AMBIL DATA
# ==========================================
@st.cache_data(ttl=300)
def load_data():
    try:
        key_dict = json.loads(st.secrets["textkey"])
        creds = Credentials.from_service_account_info(key_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        workbook = client.open("Data Pencapaian Collection 2026")
        
        df_sla3 = pd.DataFrame(workbook.worksheet("DataAgregat").get_all_records())
        try: df_progres = pd.DataFrame(workbook.worksheet("DataProgres").get_all_records())
        except: df_progres = pd.DataFrame()
            
        return df_sla3, df_progres
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
        return pd.DataFrame(), pd.DataFrame()

with st.spinner("Sinkronisasi data dari server..."):
    df_sla3, df_progres = load_data()

if not df_sla3.empty:
    df_sla3['Tanggal'] = pd.to_datetime(df_sla3['Tanggal'], errors='coerce')
    df_sla3['Periode'] = df_sla3['Tanggal'].dt.strftime('%B %Y')
    df_sla3 = df_sla3.dropna(subset=['Tanggal'])

# ==========================================
# 5. HEADER DASHBOARD
# ==========================================
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div style="opacity:0; animation: rowFadeIn 0.3s ease forwards;">
        <h1 style="font-size: 1.875rem; font-weight: 700; color: #1e293b; margin-bottom: 0;">Dashboard Pencapaian Collection</h1>
        <p style="font-size: 0.875rem; color: #64748b; margin-top: 0.25rem;">Monitoring Pencapaian, Efektifitas, dan Progres Tagihan Nasional.</p>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Sinkronkan Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<hr style='margin: 1rem 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

# TABS
tab1, tab2 = st.tabs(["Pencapaian Collection (SLA 3)", "Progres Tagihan"])

# ==========================================
# TAB 1: SLA 3
# ==========================================
with tab1:
    if not df_sla3.empty:
        # FILTER KONTROL
        st.markdown("<div style='opacity:0; animation: rowFadeIn 0.4s ease forwards;'>", unsafe_allow_html=True)
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1: filter_periode = st.selectbox("Periode", ["Semua Periode"] + list(df_sla3['Periode'].unique()))
        with col_f2: filter_region = st.selectbox("Region", ["Semua Region"] + sorted(list(df_sla3['Region'].unique())))
        with col_f3: start_date = st.date_input("Tanggal Mulai", value=df_sla3['Tanggal'].min().date())
        with col_f4: end_date = st.date_input("Tanggal Akhir", value=df_sla3['Tanggal'].max().date())
        st.markdown("</div>", unsafe_allow_html=True)

        # APPLY FILTER
        df_filtered = df_sla3.copy()
        if filter_periode != "Semua Periode": df_filtered = df_filtered[df_filtered['Periode'] == filter_periode]
        if filter_region != "Semua Region": df_filtered = df_filtered[df_filtered['Region'] == filter_region]
        df_filtered = df_filtered[(df_filtered['Tanggal'].dt.date >= start_date) & (df_filtered['Tanggal'].dt.date <= end_date)]

        st.markdown("<br>", unsafe_allow_html=True)

        # WADAH KPI 1 (TOTAL)
        tot_rp = df_filtered['Rupiah'].sum()
        tot_plg = df_filtered['Pelanggan'].sum()
        c1, c2 = st.columns(2)
        with c1: render_kpi("Total Keseluruhan Revenue", format_rupiah(tot_rp), "", "#10b981", "#059669", "#10b981", 100)
        with c2: render_kpi("Total Keseluruhan Pelanggan", f"{tot_plg:,.0f}", "", "#4f46e5", "#4338ca", "#4f46e5", 200)

        st.markdown("<br>", unsafe_allow_html=True)

        # WADAH KPI 2 (SUB)
        tele_df = df_filtered[df_filtered['Type FU'].str.contains('tele', case=False, na=False)]
        ret_df = df_filtered[df_filtered['Type FU'].str.contains('reten', case=False, na=False)]
        win_df = df_filtered[df_filtered['Type FU'].str.contains('win', case=False, na=False)]
        
        c3, c4, c5 = st.columns(3)
        with c3: render_kpi("Telecollection", format_rupiah(tele_df['Rupiah'].sum()), f"{tele_df['Pelanggan'].sum():,.0f} Pelanggan", "#0ea5e9", "#334155", "#0ea5e9", 300)
        with c4: render_kpi("Retention", format_rupiah(ret_df['Rupiah'].sum()), f"{ret_df['Pelanggan'].sum():,.0f} Pelanggan", "#6366f1", "#334155", "#6366f1", 400)
        with c5: render_kpi("Winback", format_rupiah(win_df['Rupiah'].sum()), f"{win_df['Pelanggan'].sum():,.0f} Pelanggan", "#10b981", "#334155", "#10b981", 500)

        st.markdown("<br>", unsafe_allow_html=True)

        # GRAFIK TREN
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 0.875rem; color: #334155; margin-bottom: 1rem;'>📈 Tren Pencapaian</h3>", unsafe_allow_html=True)
        if not df_filtered.empty:
            tren_data = df_filtered.groupby('Tanggal')['Rupiah'].sum().reset_index()
            fig_tren = px.line(tren_data, x='Tanggal', y='Rupiah', markers=True, color_discrete_sequence=['#4f46e5'], template="simple_white")
            fig_tren.update_layout(xaxis_title="", yaxis_title="", hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0), height=280)
            st.plotly_chart(fig_tren, use_container_width=True)
        st.markdown("</div><br>", unsafe_allow_html=True)

        # BAR CHART & LEADERBOARD HTML KUSTOM
        col_b1, col_b2 = st.columns([1, 1.5])
        
        with col_b1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            judul_bar = "🏆 Top Kinerja Region" if filter_region == "Semua Region" else f"🏆 Top Kinerja KP - {filter_region}"
            st.markdown(f"<h3 style='font-size: 0.875rem; color: #334155; margin-bottom: 1rem;'>{judul_bar}</h3>", unsafe_allow_html=True)
            if not df_filtered.empty:
                group_col = 'Region' if filter_region == "Semua Region" else 'KP'
                bar_data = df_filtered.groupby(group_col)['Rupiah'].sum().reset_index().sort_values(by='Rupiah', ascending=True)
                bar_color = '#6366f1' if filter_region == "Semua Region" else '#10b981'
                fig_bar = px.bar(bar_data, x='Rupiah', y=group_col, orientation='h', color_discrete_sequence=[bar_color], template="simple_white")
                fig_bar.update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=0, b=0), height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_b2:
            # Membangun tabel HTML murni untuk efek animasi berjenjang per baris persis seperti HTML Anda
            st.markdown("<div class='chart-container' style='padding: 0; overflow: hidden;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='font-size: 0.875rem; color: #334155; padding: 1.25rem; border-bottom: 1px solid #f1f5f9; margin:0;'>🏆 Leaderboard Agen</h3>", unsafe_allow_html=True)
            
            if not df_filtered.empty:
                if 'Outbound' not in df_filtered.columns: df_filtered['Outbound'] = df_filtered.get('Jumlah_Outbound', 0)
                lb = df_filtered.groupby('Nama Agen').agg(
                    Region=('Region', lambda x: ', '.join(set(x))),
                    Rp=('Rupiah', 'sum'),
                    Plg=('Pelanggan', 'sum')
                ).reset_index().sort_values('Rp', ascending=False).head(15) # Tampilkan top 15
                
                table_html = "<div style='max-height: 400px; overflow-y: auto;'><table class='custom-table'><thead><tr><th>Agen & Region</th><th>Rp & Pelanggan</th><th>Capaian</th></tr></thead><tbody>"
                
                for i, row in lb.iterrows():
                    delay = i * 40 # Jeda animasi per baris
                    medal = "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"<span style='color:#cbd5e1'>{i+1}</span>"
                    pct = (row['Rp'] / (230000000)) * 100 # Anggap target base 230jt sesuai kode Anda
                    badge_bg = "#d1fae5" if pct >= 100 else "#ffe4e6"
                    badge_color = "#047857" if pct >= 100 else "#e11d48"
                    
                    table_html += f"""
                    <tr class='animate-row' style='animation-delay: {delay}ms;'>
                        <td>
                            <div style='display: flex; gap: 0.75rem; align-items: flex-start;'>
                                <span style='font-size: 1.1rem; width: 20px; text-align:center;'>{medal}</span>
                                <div>
                                    <div style='font-weight: 700; color: #334155; font-size: 0.875rem;'>{row['Nama Agen']}</div>
                                    <div style='font-size: 0.75rem; color: #94a3b8;'>{row['Region']}</div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div style='font-weight: 600; color: #334155; font-size: 0.875rem;'>{format_rupiah(row['Rp'])}</div>
                            <div style='font-size: 0.75rem; color: #94a3b8;'>{row['Plg']:,} pelanggan</div>
                        </td>
                        <td>
                            <span style='background-color: {badge_bg}; color: {badge_color}; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 700;'>
                                {pct:.1f}%
                            </span>
                        </td>
                    </tr>
                    """
                table_html += "</tbody></table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 2: PROGRES TAGIHAN
# ==========================================
with tab2:
    st.markdown("<div style='opacity:0; animation: rowFadeIn 0.5s ease forwards;'><br><p style='text-align:center; color:#64748b;'>Menunggu data Progres Tagihan terisi...</p></div>", unsafe_allow_html=True)
