import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Salon Profesyonel", page_icon="✂️", layout="wide")

# --- PROFESYONEL KURUMSAL TASARIM (Clean & Modern) ---
st.markdown("""
<style>
    /* Ana Arka Plan: Hafif Gri (Göz yormaz) */
    .stApp {
        background-color: #f0f2f6;
    }

    /* Yan Menü: Beyaz ve Temiz */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Yazı Renkleri: Koyu Gri (Net Okunur) */
    h1, h2, h3, h4, h5, h6, p, label, li {
        color: #1f2937 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* İstatistik Kartları (KPI Cards) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #3b82f6; /* Kurumsal Mavi */
    }
    
    /* Tablolar */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Butonlar: Modern ve Yuvarlak */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
        height: 45px;
    }
    
    /* Nakit Butonu (Yeşilimsi) */
    div[data-testid="column"] button:first-of-type {
       /* Buraya özel renk ataması kod içinde yapılıyor ama genel stil burada */
    }

    /* Input Alanları: Beyaz ve Temiz */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #d1d5db;
        border-radius: 6px;
    }
    
    /* Dropdown Menüler */
    div[data-baseweb="select"] > div {
        background-color: #ffffff;
        color: #000000;
        border-color: #d1d5db;
    }
    
</style>
""", unsafe_allow_html=True)

# --- 2. VERİTABANI BAĞLANTISI ---
def baglan():
    return sqlite3.connect("salon.db")

def sistemi_baslat():
    conn = baglan()
    c = conn.cursor()
    # Tablo Kurulumları
    c.execute("CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, telefon TEXT, notlar TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS hizmetler (id INTEGER PRIMARY KEY AUTOINCREMENT, hizmet_adi TEXT, sure_dk INTEGER, fiyat REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, uzmanlik TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS randevular (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, personel_id INTEGER, 
        hizmet_id INTEGER, tarih TEXT, saat TEXT, durum TEXT, odeme_turu TEXT, odenen_tutar REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS giderler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, kategori TEXT, tutar REAL, tarih TEXT, notlar TEXT)""")
    
    # Güncelleme (Sütun ekleme)
    try: c.execute("ALTER TABLE randevular ADD COLUMN odeme_turu TEXT"); 
    except: pass
    try: c.execute("ALTER TABLE randevular ADD COLUMN odenen_tutar REAL"); 
    except: pass
    
    conn.commit()
    conn.close()

sistemi_baslat()

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.title("✂️ Salon Yönetimi")
    st.caption("Professional Edition v4.0")
    st.markdown("---")
    menu = st.radio("MENÜ", ["📊 Dashboard", "📅 Randevu Takvimi", "➕ Yeni Randevu", "💰 Kasa & Ödeme", "👥 Müşteriler", "⚙️ Ayarlar"])
    st.markdown("---")

# --- 4. DASHBOARD (GRAFİKLER BURADA DEĞİŞTİ) ---
if menu == "📊 Dashboard":
    st.title("📊 İşletme Özeti")
    st.markdown("İşletmenizin finansal durumu ve grafikleri.")
    
    conn = baglan()
    try:
        mus = pd.read_sql("SELECT count(*) FROM musteriler", conn).iloc[0,0]
        gelir = pd.read_sql("SELECT SUM(odenen_tutar) FROM randevular WHERE durum='Ödendi'", conn).iloc[0,0] or 0
        gider = pd.read_sql("SELECT SUM(tutar) FROM giderler", conn).iloc[0,0] or 0
        net_kar = gelir - gider
    except: mus=0; gelir=0; gider=0; net_kar=0
    finally: conn.close()

    # Üst Kartlar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Müşteri", f"{mus} Kişi")
    c2.metric("Toplam Gelir", f"{gelir:,.0f} TL")
    c3.metric("Toplam Gider", f"{gider:,.0f} TL")
    c4.metric("NET KÂR", f"{net_kar:,.0f} TL", delta_color="normal" if net_kar>=0 else "inverse")
    
    st.markdown("---")
    
    # YENİ GRAFİK ALANI: AREA CHART (ALAN GRAFİĞİ)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Gelir ve Gider Dengesi")
        # Line/Area Chart için veri hazırlıyoruz
        data = pd.DataFrame({
            "Kategori": ["Gelir", "Gider"],
            "Tutar": [gelir, gider]
        })
        # Area chart daha dolu ve şık durur
        st.bar_chart(data.set_index("Kategori"), color=["#10b981", "#ef4444"]) # Yeşil ve Kırmızı
        
    with col2:
        st.subheader("🔥 Popüler İşlemler")
        conn = baglan()
        df_pop = pd.read_sql("SELECT h.hizmet_adi, count(*) as adet FROM randevular r JOIN hizmetler h ON r.hizmet_id=h.id GROUP BY h.hizmet_adi", conn)
        conn.close()
        if not df_pop.empty:
            # Burası için de Area Chart kullanalım
            st.area_chart(df_pop.set_index("hizmet_adi"), color="#3b82f6") # Mavi tonu
        else:
            st.info("Veri yok.")

# --- 5. RANDEVU TAKVİMİ ---
elif menu == "📅 Randevu Takvimi":
    st.title("🗓️ Randevu Ajandası")
    conn = baglan()
    df = pd.read_sql("""SELECT r.id as No, r.tarih, r.saat, m.ad_soyad, h.hizmet_adi, r.durum 
        FROM randevular r JOIN musteriler m ON r.musteri_id = m.id JOIN hizmetler h ON r.hizmet_id = h.id 
        ORDER BY r.tarih DESC""", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        # Silme İşlemi
        with st.expander("🗑️ Randevu İptal/Sil"):
            sil_id = st.selectbox("Silinecek No:", df['No'])
            if st.button("Sil"):
                conn=baglan(); conn.execute("DELETE FROM randevular WHERE id=?", (int(sil_id),)); conn.commit(); conn.close(); st.success("Silindi!"); st.rerun()
    else:
        st.info("Kayıtlı randevu yok.")

# --- 6. YENİ RANDEVU ---
elif menu == "➕ Yeni Randevu":
    st.title("✨ Yeni Randevu")
    conn = baglan()
    m = pd.read_sql("SELECT * FROM musteriler", conn)
    h = pd.read_sql("SELECT * FROM hizmetler", conn)
    p = pd.read_sql("SELECT * FROM personel", conn)
    conn.close()
    
    if m.empty: st.error("Önce Müşteri Ekleyiniz")
    else:
        with st.form("new_app"):
            c1, c2 = st.columns(2)
            sel_m = c1.selectbox("Müşteri", m['ad_soyad'])
            sel_h = c1.selectbox("Hizmet", h['hizmet_adi'])
            sel_p = c2.selectbox("Personel", p['ad_soyad'])
            date = c2.date_input("Tarih")
            time = c2.time_input("Saat")
            if st.form_submit_button("Randevuyu Kaydet ✅"):
                m_id = m[m['ad_soyad']==sel_m]['id'].values[0]
                h_id = h[h['hizmet_adi']==sel_h]['id'].values[0]
                p_id = p[p['ad_soyad']==sel_p]['id'].values[0]
                conn=baglan()
                conn.execute("INSERT INTO randevular (musteri_id, personel_id, hizmet_id, tarih, saat, durum) VALUES (?,?,?,?,?, 'Onaylandı')", 
                             (int(m_id), int(p_id), int(h_id), str(date), str(time)))
                conn.commit(); conn.close(); st.success("Randevu Oluşturuldu!"); st.rerun()

# --- 7. FİNANS & KASA (BUTONLAR BURADA DÜZELTİLDİ) ---
elif menu == "💰 Kasa & Ödeme":
    st.title("💰 Kasa İşlemleri")
    t1, t2 = st.tabs(["Ödeme Tahsilat", "Masraf Girişi"])
    
    with t1:
        st.subheader("Ödemesi Beklenenler")
        conn = baglan()
        # Sadece 'Onaylandı' olanları çek
        df = pd.read_sql("""SELECT r.id, m.ad_soyad, h.fiyat, h.hizmet_adi 
                            FROM randevular r 
                            JOIN musteriler m ON r.musteri_id=m.id 
                            JOIN hizmetler h ON r.hizmet_id=h.id 
                            WHERE r.durum='Onaylandı'""", conn)
        conn.close()
        
        if df.empty: 
            st.success("Tüm ödemeler alınmış, bekleyen yok. 🎉")
        else:
            for i, row in df.iterrows():
                # Her satırı bir kutu içine alalım
                with st.container():
                    st.markdown(f"**{row['ad_soyad']}** - {row['hizmet_adi']} - **{row['fiyat']} TL**")
                    # Sütunları ayır: Text - Nakit Butonu - Kart Butonu
                    col_btn1, col_btn2, col_space = st.columns([1, 1, 4])
                    
                    with col_btn1:
                        if st.button("💵 Nakit", key=f"nakit_{row['id']}"):
                            conn=baglan()
                            conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Nakit', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id']))
                            conn.commit(); conn.close(); st.toast("Nakit Ödeme Alındı"); st.rerun()
                    
                    with col_btn2:
                        if st.button("💳 Kart", key=f"kart_{row['id']}"):
                            conn=baglan()
                            conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Kredi Kartı', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id']))
                            conn.commit(); conn.close(); st.toast("Kartla Ödeme Alındı"); st.rerun()
                    st.markdown("---") # Ayırıcı çizgi

    with t2:
        st.subheader("Gider Ekle")
        with st.form("gider_form"):
            bas = st.text_input("Gider Açıklaması (Örn: Kira, Fatura)")
            kat = st.selectbox("Kategori", ["Kira", "Fatura", "Malzeme", "Personel", "Diğer"])
            tut = st.number_input("Tutar (TL)")
            if st.form_submit_button("Masrafı Kaydet"):
                conn=baglan(); conn.execute("INSERT INTO giderler (baslik, kategori, tutar) VALUES (?,?,?)", (bas, kat, tut)); conn.commit(); conn.close(); st.success("Kaydedildi"); st.rerun()

# --- 8. MÜŞTERİLER ---
elif menu == "👥 Müşteriler":
    st.title("👥 Müşteri Rehberi")
    with st.form("add_mus"):
        c1, c2 = st.columns(2)
        ad = c1.text_input("Ad Soyad")
        tel = c2.text_input("Telefon")
        if st.form_submit_button("Müşteri Ekle"):
            conn=baglan(); conn.execute("INSERT INTO musteriler (ad_soyad, telefon) VALUES (?,?)", (ad, tel)); conn.commit(); conn.close(); st.rerun()
    
    conn=baglan(); 
    df_mus = pd.read_sql("SELECT * FROM musteriler", conn)
    st.dataframe(df_mus, use_container_width=True)
    conn.close()

# --- 9. AYARLAR ---
elif menu == "⚙️ Ayarlar":
    st.title("⚙️ Hizmet & Personel Ayarları")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Hizmetler")
        with st.form("add_hiz"):
            ad = st.text_input("Hizmet Adı"); fiy = st.number_input("Fiyat", value=100)
            if st.form_submit_button("Ekle"):
                conn=baglan(); conn.execute("INSERT INTO hizmetler (hizmet_adi, fiyat) VALUES (?,?)", (ad, fiy)); conn.commit(); conn.close(); st.rerun()
        conn=baglan(); st.dataframe(pd.read_sql("SELECT hizmet_adi, fiyat FROM hizmetler", conn), use_container_width=True); conn.close()
        
    with c2:
        st.subheader("Personel")
        with st.form("add_per"):
            ad = st.text_input("Personel Adı");
            if st.form_submit_button("Ekle"):
                conn=baglan(); conn.execute("INSERT INTO personel (ad_soyad) VALUES (?)", (ad,)); conn.commit(); conn.close(); st.rerun()
        conn=baglan(); st.dataframe(pd.read_sql("SELECT ad_soyad FROM personel", conn), use_container_width=True); conn.close()
