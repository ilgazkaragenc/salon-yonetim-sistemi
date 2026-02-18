import streamlit as st
import sqlite3
import pandas as pd
import altair as alt # Grafik motorunu ekledik
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Salon Profesyonel", page_icon="✂️", layout="wide")

# --- PROFESYONEL KURUMSAL TASARIM ---
st.markdown("""
<style>
    /* Arka Plan */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Yan Menü */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Kartlar */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #0d6efd; /* Mavi Çizgi */
    }
    
    /* Başlıklar */
    h1, h2, h3, p, label {
        color: #212529 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Butonlar */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        height: 45px;
        transition: 0.3s;
    }

    /* Inputlar */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #ced4da;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. VERİTABANI ---
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
    st.title("✂️ Salon Yönetimi")
    st.markdown("---")
    menu = st.radio("MENÜ", ["📊 Dashboard", "📅 Randevu Takvimi", "➕ Yeni Randevu", "💰 Kasa & Ödeme", "👥 Müşteriler", "⚙️ Ayarlar"])
    st.markdown("---")

# --- 4. DASHBOARD (GRAFİKLER DÜZELTİLDİ) ---
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

    # KARTLAR
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Müşteri Sayısı", f"{mus}")
    c2.metric("Toplam Gelir", f"{gelir:,.0f} TL")
    c3.metric("Toplam Gider", f"{gider:,.0f} TL")
    c4.metric("NET DURUM", f"{net_kar:,.0f} TL", delta_color="normal" if net_kar>=0 else "inverse")
    
    st.markdown("---")
    
    # --- PROFESYONEL GRAFİKLER (ALTAIR KULLANARAK) ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Gelir vs Gider")
        # Pasta Grafiği Verisi
        source = pd.DataFrame({
            "Kategori": ["Gelir", "Gider"],
            "Tutar": [gelir, gider]
        })
        
        # Donut Chart (Halka Grafik)
        base = alt.Chart(source).encode(theta=alt.Theta("Tutar", stack=True))
        pie = base.mark_arc(outerRadius=120, innerRadius=60).encode(
            color=alt.Color("Kategori", scale=alt.Scale(domain=['Gelir', 'Gider'], range=['#198754', '#dc3545'])), # Yeşil ve Kırmızı
            order=alt.Order("Tutar", sort="descending"),
            tooltip=["Kategori", "Tutar"]
        )
        text = base.mark_text(radius=140).encode(
            text="Tutar",
            order=alt.Order("Tutar", sort="descending"),
            color=alt.value("black") 
        )
        st.altair_chart(pie + text, use_container_width=True)

    with col2:
        st.subheader("🔥 En Popüler Hizmetler")
        conn = baglan()
        df_pop = pd.read_sql("SELECT h.hizmet_adi, count(*) as adet FROM randevular r JOIN hizmetler h ON r.hizmet_id=h.id GROUP BY h.hizmet_adi", conn)
        conn.close()
        
        if not df_pop.empty:
            # Yatay Çubuk Grafiği
            bar_chart = alt.Chart(df_pop).mark_bar().encode(
                x=alt.X('adet', title='İşlem Sayısı'),
                y=alt.Y('hizmet_adi', sort='-x', title='Hizmet'),
                color=alt.Color('hizmet_adi', legend=None),
                tooltip=['hizmet_adi', 'adet']
            ).properties(height=300)
            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.info("Grafik için veri bekleniyor...")

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
        with st.expander("🗑️ Kayıt Sil"):
            sil_id = st.selectbox("Silinecek No:", df['No'])
            if st.button("Sil"):
                conn=baglan(); conn.execute("DELETE FROM randevular WHERE id=?", (int(sil_id),)); conn.commit(); conn.close(); st.success("Silindi!"); st.rerun()
    else:
        st.info("Kayıt yok.")

# --- 6. YENİ RANDEVU ---
elif menu == "➕ Yeni Randevu":
    st.title("✨ Yeni Randevu")
    conn = baglan()
    m = pd.read_sql("SELECT * FROM musteriler", conn)
    h = pd.read_sql("SELECT * FROM hizmetler", conn)
    p = pd.read_sql("SELECT * FROM personel", conn)
    conn.close()
    
    if m.empty: st.error("Lütfen önce Müşteri Ekleyin")
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
                conn.commit(); conn.close(); st.success("Kaydedildi!"); st.rerun()

# --- 7. KASA VE ÖDEME ---
elif menu == "💰 Kasa & Ödeme":
    st.title("💰 Kasa İşlemleri")
    t1, t2 = st.tabs(["Ödeme Al", "Masraf Gir"])
    
    with t1:
        st.subheader("Ödemesi Beklenenler")
        conn = baglan()
        df = pd.read_sql("""SELECT r.id, m.ad_soyad, h.fiyat, h.hizmet_adi 
                            FROM randevular r 
                            JOIN musteriler m ON r.musteri_id=m.id 
                            JOIN hizmetler h ON r.hizmet_id=h.id 
                            WHERE r.durum='Onaylandı'""", conn)
        conn.close()
        
        if df.empty: 
            st.success("Tüm ödemeler alınmış. ✅")
        else:
            for i, row in df.iterrows():
                with st.container():
                    col_info, col_btn1, col_btn2 = st.columns([3, 1, 1])
                    col_info.info(f"**{row['ad_soyad']}** - {row['hizmet_adi']} ({row['fiyat']} TL)")
                    
                    if col_btn1.button("💵 Nakit", key=f"n{row['id']}"):
                        conn=baglan(); conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Nakit', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id'])); conn.commit(); conn.close(); st.rerun()
                    
                    if col_btn2.button("💳 Kart", key=f"k{row['id']}"):
                        conn=baglan(); conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Kredi Kartı', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id'])); conn.commit(); conn.close(); st.rerun()

    with t2:
        st.subheader("Harcama Gir")
        with st.form("gider_form"):
            bas = st.text_input("Açıklama")
            kat = st.selectbox("Kategori", ["Kira", "Fatura", "Malzeme", "Personel", "Diğer"])
            tut = st.number_input("Tutar (TL)")
            if st.form_submit_button("Kaydet"):
                conn=baglan(); conn.execute("INSERT INTO giderler (baslik, kategori, tutar) VALUES (?,?,?)", (bas, kat, tut)); conn.commit(); conn.close(); st.success("Kaydedildi"); st.rerun()

# --- 8. MÜŞTERİLER ---
elif menu == "👥 Müşteriler":
    st.title("👥 Müşteriler")
    with st.form("add_mus"):
        c1, c2 = st.columns(2)
        ad = c1.text_input("Ad Soyad")
        tel = c2.text_input("Telefon")
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
        conn=baglan(); st.dataframe(pd.read_sql("SELECT hizmet_adi, fiyat FROM hizmetler", conn), use_container_width=True); conn.close()
    with c2:
        with st.form("add_per"):
            ad = st.text_input("Personel");
            if st.form_submit_button("Personel Ekle"):
                conn=baglan(); conn.execute("INSERT INTO personel (ad_soyad) VALUES (?)", (ad,)); conn.commit(); conn.close(); st.rerun()
        conn=baglan(); st.dataframe(pd.read_sql("SELECT ad_soyad FROM personel", conn), use_container_width=True); conn.close()
