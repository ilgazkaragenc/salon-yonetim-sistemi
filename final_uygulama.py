import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. SAYFA VE PREMIUM TASARIM AYARLARI ---
st.set_page_config(page_title="Gold Salon Yönetimi", page_icon="✂️", layout="wide")

# CSS İle Özel Tasarım (Burası Sitenin Kıyafetidir)
st.markdown("""
<style>
    /* GENEL SAYFA YAPISI */
    .stApp {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
    }
    
    /* YAN MENÜ (SIDEBAR) TASARIMI */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e; /* Koyu Lacivert */
        border-right: 1px solid #ddd;
    }
    section[data-testid="stSidebar"] h1, p, span, label, div {
        color: #ffffff !important; /* Yan menü yazıları beyaz */
    }
    
    /* İSTATİSTİK KARTLARI (METRICS) */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #d63384; /* Pembe Çizgi */
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* Gölge Efekti */
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.02); /* Üzerine gelince büyüme efekti */
        border-left-color: #ffc107; /* Rengi altına dönsün */
    }
    
    /* BUTONLAR */
    .stButton>button {
        background: linear-gradient(90deg, #d63384, #c2185b);
        color: white !important;
        border-radius: 25px;
        height: 50px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 10px rgba(214, 51, 132, 0.3);
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #c2185b, #880e4f);
        box-shadow: 0 6px 15px rgba(214, 51, 132, 0.5);
        transform: translateY(-2px);
    }
    
    /* TABLOLAR */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden; /* Köşeleri yuvarla */
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        background-color: white;
    }
    
    /* BAŞLIKLAR */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* BAŞARI VE HATA KUTULARI */
    .stSuccess {
        background-color: #d4edda;
        border-radius: 10px;
    }
    .stError {
        background-color: #f8d7da;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. VERİTABANI YÖNETİCİSİ ---
def baglan():
    return sqlite3.connect("salon.db")

def sistemi_baslat():
    conn = baglan()
    c = conn.cursor()
    
    # Tabloları oluştur
    c.execute("CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, telefon TEXT, notlar TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS hizmetler (id INTEGER PRIMARY KEY AUTOINCREMENT, hizmet_adi TEXT, sure_dk INTEGER, fiyat REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, uzmanlik TEXT)")
    
    # Randevular (Ödeme sütunları dahil)
    c.execute("""CREATE TABLE IF NOT EXISTS randevular (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, personel_id INTEGER, 
        hizmet_id INTEGER, tarih TEXT, saat TEXT, durum TEXT, odeme_turu TEXT, odenen_tutar REAL)""")
    
    # Giderler (Masraf)
    c.execute("""CREATE TABLE IF NOT EXISTS giderler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, kategori TEXT, tutar REAL, tarih TEXT, notlar TEXT)""")
    
    # Eksik sütun kontrolü (Eski veritabanları için tamir kiti)
    try: c.execute("ALTER TABLE randevular ADD COLUMN odeme_turu TEXT"); 
    except: pass
    try: c.execute("ALTER TABLE randevular ADD COLUMN odenen_tutar REAL"); 
    except: pass

    conn.commit()
    conn.close()

sistemi_baslat() # Başlangıçta çalıştır

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3962/3962455.png", width=100)
    st.title("Salon Yönetimi")
    st.markdown("---")
    menu = st.radio("MENÜ", [
        "📊 Dashboard (Patron)", 
        "📅 Randevu Takvimi", 
        "➕ Yeni Randevu", 
        "💰 Finans & Kasa",
        "👥 Müşteriler", 
        "⚙️ Ayarlar"
    ])
    st.markdown("---")
    st.info("Sistem Versiyonu: 3.0 (Gold Design)")

# --- 4. MODÜL: DASHBOARD (PATRON EKRANI) ---
if menu == "📊 Dashboard (Patron)":
    st.title("📊 İşletme Özeti")
    conn = baglan()
    
    # Veri Çekme
    try:
        # Toplam M
