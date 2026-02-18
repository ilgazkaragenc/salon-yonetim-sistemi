import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Salon Yönetimi", page_icon="✂️", layout="wide")

# --- OKUNABİLİRLİK TAMİR EDİLMİŞ TASARIM ---
st.markdown("""
<style>
    /* 1. Ana Arka Plan (Koyu) */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    /* 2. Yan Menü */
    section[data-testid="stSidebar"] {
        background-color: #262730;
        border-right: 1px solid #41444C;
    }
    
    /* 3. Genel Yazı Renkleri (Başlıklar vs Beyaz Olsun) */
    h1, h2, h3, h4, h5, h6, p, label {
        color: #FAFAFA !important;
    }

    /* --- 4. KRİTİK DÜZELTME: GİRİŞ KUTULARI --- */
    /* Kutuların içi Beyaz, Yazılar SİYAH olsun */
    
    /* Text Input ve Date Input Kutuları */
    .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {
        background-color: #ffffff !important; /* Arka plan Beyaz */
        color: #000000 !important; /* Yazı SİYAH */
        border: 1px solid #ddd;
    }
    
    /* Dropdown (Seçim Kutuları) */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Seçeneklerin Rengi */
    div[role="listbox"] ul {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* 5. Kartlar (Metrics) */
    div[data-testid="metric-container"] {
        background-color: #1F2229;
        border: 1px solid #41444C;
        padding: 15px;
        border-radius: 8px;
        color: #FAFAFA;
        border-left: 5px solid #FFD700;
    }
    div[data-testid="metric-container"] label {
        color: #dddddd !important; /* Kart başlıkları hafif gri */
    }
    div[data-testid="metric-container"] div {
        color: #FAFAFA !important; /* Kart sayıları beyaz */
    }
    
    /* 6. Butonlar - Altın Sarısı ve Siyah Yazı */
    .stButton>button {
        background-color: #FFD700;
        color: #000000 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        height: 45px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #E6C200;
        color: #000000 !important;
    }
    
    /* Başarı Mesajları */
    .stSuccess {
        background-color: #d4edda;
        color: #155724 !important;
    }
    .stSuccess p {
        color: #155724 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. VERİTABANI YÖNETİCİSİ ---
def baglan():
    return sqlite3.connect("salon.db")

def sistemi_baslat():
    conn = baglan()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, telefon TEXT, notlar TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS hizmetler (id INTEGER PRIMARY KEY AUTOINCREMENT, hizmet_adi TEXT, sure_dk INTEGER, fiyat REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, uzmanlik TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS randevular (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, personel_id INTEGER, 
        hizmet_id INTEGER, tarih TEXT, saat TEXT, durum TEXT, odeme_turu TEXT, odenen_tutar REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS giderler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, kategori TEXT, tutar REAL, tarih TEXT, notlar TEXT)""")
    try: c.execute("ALTER TABLE randevular ADD COLUMN odeme_turu TEXT"); 
    except: pass
    try: c.execute("ALTER TABLE randevular ADD COLUMN odenen_tutar REAL"); 
    except: pass
    conn.commit()
    conn.close()

sistemi_baslat()

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3962/3962455.png", width=100)
    st.title("Salon Yönetimi")
    st.markdown("---")
    menu = st.radio("MENÜ", ["📊 Dashboard", "📅 Randevu Takvimi", "➕ Yeni Randevu", "💰 Finans & Kasa", "👥 Müşteriler", "⚙️ Ayarlar"])
    st.markdown("---")
    st.caption("v3.3 Black Text Fix")

# --- 4. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 İşletme Özeti")
    conn = baglan()
    try:
        mus = pd.read_sql("SELECT count(*) FROM musteriler", conn).iloc[0,0]
        gelir = pd.read_sql("SELECT SUM(odenen_tutar) FROM randevular WHERE durum='Ödendi'", conn).iloc[0,0] or 0
        gider = pd.read_sql("SELECT SUM(tutar) FROM giderler", conn).iloc[0,0] or 0
        net_kar = gelir - gider
    except: mus=0; gelir=0; gider=0; net_kar=0
    finally: conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Müşteri", f"{mus}")
    c2.metric("Toplam Gelir", f"{gelir:,.0f} TL")
    c3.metric("Toplam Gider", f"{gider:,.0f} TL")
    
    delta_color = "normal" if net_kar >= 0 else "inverse"
    msg = "Kârdasın" if net_kar >= 0 else "Zarardasın"
    c4.metric("NET KÂR", f"{net_kar:,.0f} TL", delta=msg, delta_color=delta_color)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gelir vs Gider")
        st.bar_chart(pd.DataFrame({"Tip": ["Gelir", "Gider"], "Tutar": [gelir, gider]}).set_index("Tip"))
    with col2:
        st.subheader("En Çok Yapılan İşlemler")
        conn = baglan()
        df_pop = pd.read_sql("SELECT h.hizmet_adi, count(*) as adet FROM randevular r JOIN hizmetler h ON r.hizmet_id=h.id GROUP BY h.hizmet_adi", conn)
        conn.close()
        if not df_pop.empty: st.bar_chart(df_pop.set_index("hizmet_adi"))

# --- 5. RANDEVU TAKVİMİ ---
elif menu == "📅 Randevu Takvimi":
    st.title("🗓️ Randevu Listesi")
    conn = baglan()
    df = pd.read_sql("""SELECT r.id as No, r.tarih, r.saat, m.ad_soyad, h.hizmet_adi, r.durum 
        FROM randevular r JOIN musteriler m ON r.musteri_id = m.id JOIN hizmetler h ON r.hizmet_id = h.id 
        ORDER BY r.tarih DESC""", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        with st.expander("🗑️ Randevu Sil"):
            sil_id = st.selectbox("Silinecek No:", df['No'])
            if st.button("Sil"):
                conn=baglan(); conn.execute("DELETE FROM randevular WHERE id=?", (int(sil_id),)); conn.commit(); conn.close(); st.success("Silindi!"); st.rerun()
    else: st.info("Randevu yok.")

# --- 6. YENİ RANDEVU ---
elif menu == "➕ Yeni Randevu":
    st.title("✨ Yeni Randevu")
    conn = baglan()
    m = pd.read_sql("SELECT * FROM musteriler", conn)
    h = pd.read_sql("SELECT * FROM hizmetler", conn)
    p = pd.read_sql("SELECT * FROM personel", conn)
    conn.close()
    
    if m.empty: st.error("Müşteri Ekleyin")
    else:
        with st.form("new_app"):
            c1, c2 = st.columns(2)
            sel_m = c1.selectbox("Müşteri", m['ad_soyad'])
            sel_h = c1.selectbox("Hizmet", h['hizmet_adi'])
            sel_p = c2.selectbox("Personel", p['ad_soyad'])
            date = c2.date_input("Tarih")
            time = c2.time_input("Saat")
            if st.form_submit_button("Kaydet ✅"):
                m_id = m[m['ad_soyad']==sel_m]['id'].values[0]
                h_id = h[h['hizmet_adi']==sel_h]['id'].values[0]
                p_id = p[p['ad_soyad']==sel_p]['id'].values[0]
                conn=baglan(); conn.execute("INSERT INTO randevular (musteri_id, personel_id, hizmet_id, tarih, saat, durum) VALUES (?,?,?,?,?, 'Onaylandı')", (int(m_id), int(p_id), int(h_id), str(date), str(time))); conn.commit(); conn.close(); st.success("Oluşturuldu!"); st.rerun()

# --- 7. FİNANS ---
elif menu == "💰 Finans & Kasa":
    st.title("💰 Kasa İşlemleri")
    t1, t2 = st.tabs(["Ödeme Al", "Masraf Gir"])
    with t1:
        conn = baglan()
        df = pd.read_sql("SELECT r.id, m.ad_soyad, h.fiyat FROM randevular r JOIN musteriler m ON r.musteri_id=m.id JOIN hizmetler h ON r.hizmet_id=h.id WHERE r.durum='Onaylandı'", conn)
        conn.close()
        if df.empty: st.success("Borçlu yok.")
        else:
            for i, row in df.iterrows():
                c1, c2 = st.columns([3,1])
                c1.write(f"**{row['ad_soyad']}** - {row['fiyat']} TL")
                if c2.button("Nakit Al", key=f"n{row['id']}"):
                    conn=baglan(); conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Nakit', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id'])); conn.commit(); conn.close(); st.rerun()
    with t2:
        with st.form("gider"):
            bas = st.text_input("Gider Adı")
            tut = st.number_input("Tutar")
            if st.form_submit_button("Kaydet"):
                conn=baglan(); conn.execute("INSERT INTO giderler (baslik, tutar) VALUES (?,?)", (bas, tut)); conn.commit(); conn.close(); st.success("Gider Eklendi"); st.rerun()

# --- 8. MÜŞTERİLER ---
elif menu == "👥 Müşteriler":
    st.title("👥 Müşteri Listesi")
    with st.form("add_mus"):
        ad = st.text_input("Ad Soyad")
        tel = st.text_input("Tel")
        if st.form_submit_button("Ekle"):
            conn=baglan(); conn.execute("INSERT INTO musteriler (ad_soyad, telefon) VALUES (?,?)", (ad, tel)); conn.commit(); conn.close(); st.rerun()
    conn=baglan(); st.dataframe(pd.read_sql("SELECT * FROM musteriler", conn), use_container_width=True); conn.close()

# --- 9. AYARLAR ---
elif menu == "⚙️ Ayarlar":
    st.title("⚙️ Ayarlar")
    c1, c2 = st.columns(2)
    with c1:
        with st.form("add_hiz"):
            ad = st.text_input("Hizmet"); fiy = st.number_input("Fiyat", value=100)
            if st.form_submit_button("Hizmet Ekle"):
                conn=baglan(); conn.execute("INSERT INTO hizmetler (hizmet_adi, fiyat) VALUES (?,?)", (ad, fiy)); conn.commit(); conn.close(); st.rerun()
    with c2:
        with st.form("add_per"):
            ad = st.text_input("Personel");
            if st.form_submit_button("Personel Ekle"):
                conn=baglan(); conn.execute("INSERT INTO personel (ad_soyad) VALUES (?)", (ad,)); conn.commit(); conn.close(); st.rerun()
