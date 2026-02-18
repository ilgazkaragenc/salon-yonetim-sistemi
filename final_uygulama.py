import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. SAYFA VE TASARIM AYARLARI ---
st.set_page_config(page_title="Gold Salon Yönetimi", page_icon="✂️", layout="wide")

# Özel CSS (Premium Görünüm)
st.markdown("""
<style>
    .stApp {background-color: #f8f9fa;}
    [data-testid="stSidebar"] {background-color: #2c3e50;}
    [data-testid="stSidebar"] * {color: white !important;}
    div[data-testid="metric-container"] {
        background-color: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #E6007E;
    }
    h1, h2, h3 {color: #2c3e50;}
    .stDataFrame {background-color: white; padding: 10px; border-radius: 10px;}
    .stButton>button {border-radius: 20px; font-weight: bold; width: 100%; transition: 0.3s;}
    .stButton>button:hover {transform: scale(1.02);}
    .success-box {padding:10px; background-color:#d4edda; color:#155724; border-radius:10px;}
    .error-box {padding:10px; background-color:#f8d7da; color:#721c24; border-radius:10px;}
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
    st.image("https://cdn-icons-png.flaticon.com/512/3962/3962455.png", width=80)
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
    st.info("Sistem Versiyonu: 3.0 (Final)")

# --- 4. MODÜL: DASHBOARD (PATRON EKRANI) ---
if menu == "📊 Dashboard (Patron)":
    st.title("📊 İşletme Özeti")
    conn = baglan()
    
    # Veri Çekme
    try:
        # Toplam Müşteri
        mus = pd.read_sql("SELECT count(*) FROM musteriler", conn).iloc[0,0]
        
        # Finansal Veriler
        gelir = pd.read_sql("SELECT SUM(odenen_tutar) FROM randevular WHERE durum='Ödendi'", conn).iloc[0,0] or 0
        gider = pd.read_sql("SELECT SUM(tutar) FROM giderler", conn).iloc[0,0] or 0
        net_kar = gelir - gider
        
    except:
        mus=0; gelir=0; gider=0; net_kar=0
    finally:
        conn.close()

    # Üst Kartlar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Toplam Müşteri", f"{mus}")
    c2.metric("💰 Toplam Gelir", f"{gelir:,.0f} TL")
    c3.metric("💸 Toplam Gider", f"{gider:,.0f} TL")
    
    # Kâr Durumuna Göre Renkli Kart
    delta_color = "normal" if net_kar >= 0 else "inverse"
    msg = "Kârdasın! 🚀" if net_kar >= 0 else "Zarardasın! ⚠️"
    c4.metric("🏆 NET KÂR", f"{net_kar:,.0f} TL", delta=msg, delta_color=delta_color)

    st.markdown("---")

    # Grafikler
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gelir vs Gider")
        chart_data = pd.DataFrame({"Tip": ["Gelir", "Gider"], "Tutar": [gelir, gider]})
        st.bar_chart(chart_data.set_index("Tip"), color=["#27ae60"])
    
    with col2:
        st.subheader("En Çok Yapılan İşlemler")
        conn = baglan()
        df_pop = pd.read_sql("SELECT h.hizmet_adi, count(*) as adet FROM randevular r JOIN hizmetler h ON r.hizmet_id=h.id GROUP BY h.hizmet_adi", conn)
        conn.close()
        if not df_pop.empty: st.bar_chart(df_pop.set_index("hizmet_adi"))

# --- 5. MODÜL: RANDEVU TAKVİMİ ---
elif menu == "📅 Randevu Takvimi":
    st.title("🗓️ Randevu Ajandası")
    conn = baglan()
    df = pd.read_sql("""
        SELECT r.id as No, r.tarih, r.saat, m.ad_soyad, h.hizmet_adi, p.ad_soyad as Personel, r.durum 
        FROM randevular r
        JOIN musteriler m ON r.musteri_id = m.id
        JOIN hizmetler h ON r.hizmet_id = h.id
        JOIN personel p ON r.personel_id = p.id
        ORDER BY r.tarih DESC, r.saat ASC
    """, conn)
    conn.close()

    # Renklendirme
    def highlight_status(val):
        color = '#d4edda' if val == 'Ödendi' else '#fff3cd' if val == 'Onaylandı' else 'white'
        return f'background-color: {color}'

    if not df.empty:
        st.dataframe(df.style.map(highlight_status, subset=['durum']), use_container_width=True)
        with st.expander("🗑️ Randevu İptal Et / Sil"):
            sil_id = st.selectbox("Silinecek No:", df['No'])
            if st.button("Seçili Randevuyu Sil"):
                conn = baglan()
                conn.execute("DELETE FROM randevular WHERE id=?", (int(sil_id),))
                conn.commit()
                conn.close()
                st.success("Silindi!"); st.rerun()
    else:
        st.info("Henüz kayıtlı randevu yok.")

# --- 6. MODÜL: YENİ RANDEVU ---
elif menu == "➕ Yeni Randevu":
    st.title("✨ Yeni Randevu Oluştur")
    conn = baglan()
    m = pd.read_sql("SELECT * FROM musteriler", conn)
    h = pd.read_sql("SELECT * FROM hizmetler", conn)
    p = pd.read_sql("SELECT * FROM personel", conn)
    conn.close()

    if m.empty: st.error("Önce Müşteri Ekleyin!")
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
                
                conn = baglan()
                conn.execute("INSERT INTO randevular (musteri_id, personel_id, hizmet_id, tarih, saat, durum) VALUES (?,?,?,?,?, 'Onaylandı')", 
                             (int(m_id), int(p_id), int(h_id), str(date), str(time)))
                conn.commit()
                conn.close()
                st.success("Randevu Oluşturuldu!"); st.rerun()

# --- 7. MODÜL: FİNANS & KASA (BİRLEŞTİRİLMİŞ) ---
elif menu == "💰 Finans & Kasa":
    st.title("💰 Finans Merkezi")
    tab1, tab2, tab3 = st.tabs(["📥 Gelir (Kasa)", "📤 Gider (Masraf)", "📄 Raporlar"])

    # TAB 1: ÖDEME ALMA
    with tab1:
        st.subheader("Ödeme Bekleyen Müşteriler")
        conn = baglan()
        df_borc = pd.read_sql("""
            SELECT r.id, r.saat, m.ad_soyad, h.hizmet_adi, h.fiyat 
            FROM randevular r JOIN musteriler m ON r.musteri_id=m.id JOIN hizmetler h ON r.hizmet_id=h.id
            WHERE r.durum='Onaylandı' ORDER BY r.tarih
        """, conn)
        conn.close()
        
        if df_borc.empty: st.success("Bekleyen ödeme yok.")
        else:
            for i, row in df_borc.iterrows():
                with st.expander(f"💵 {row['ad_soyad']} - {row['fiyat']} TL"):
                    c1, c2 = st.columns(2)
                    if c1.button("Nakit Al", key=f"n{row['id']}"):
                        conn=baglan(); conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Nakit', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id'])); conn.commit(); conn.close(); st.rerun()
                    if c2.button("Kart Çek", key=f"k{row['id']}"):
                        conn=baglan(); conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Kredi Kartı', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id'])); conn.commit(); conn.close(); st.rerun()

    # TAB 2: GİDER GİRİŞİ
    with tab2:
        st.subheader("Masraf Ekle")
        with st.form("masraf_form"):
            baslik = st.text_input("Gider Adı (Örn: Kira, Fatura)")
            kat = st.selectbox("Kategori", ["Kira", "Fatura", "Malzeme", "Personel", "Diğer"])
            tut = st.number_input("Tutar (TL)", min_value=0.0)
            if st.form_submit_button("Harcamayı Kaydet ➖"):
                conn=baglan(); conn.execute("INSERT INTO giderler (baslik, kategori, tutar, tarih) VALUES (?,?,?,?)", (baslik, kat, tut, str(datetime.now().date()))); conn.commit(); conn.close(); st.success("Kaydedildi!"); st.rerun()
        
        conn=baglan(); st.write("Son Harcamalar:"); st.dataframe(pd.read_sql("SELECT * FROM giderler ORDER BY id DESC LIMIT 5", conn)); conn.close()

    # TAB 3: DETAYLI RAPOR
    with tab3:
        conn = baglan()
        df_gelir = pd.read_sql("SELECT tarih, odeme_turu, sum(odenen_tutar) as Tutar FROM randevular WHERE durum='Ödendi' GROUP BY tarih, odeme_turu", conn)
        st.write("Gelir Detayı:"); st.dataframe(df_gelir, use_container_width=True)
        conn.close()

# --- 8. MODÜL: MÜŞTERİLER ---
elif menu == "👥 Müşteriler":
    st.title("👥 Müşteri Yönetimi")
    with st.expander("Yeni Müşteri Ekle"):
        with st.form("add_mus"):
            ad = st.text_input("Ad Soyad")
            tel = st.text_input("Telefon")
            if st.form_submit_button("Kaydet"):
                conn=baglan(); conn.execute("INSERT INTO musteriler (ad_soyad, telefon) VALUES (?,?)", (ad, tel)); conn.commit(); conn.close(); st.success("Eklendi"); st.rerun()
    conn=baglan(); st.dataframe(pd.read_sql("SELECT * FROM musteriler", conn), use_container_width=True); conn.close()

# --- 9. MODÜL: AYARLAR ---
elif menu == "⚙️ Ayarlar":
    st.title("⚙️ Hizmet & Personel Ayarları")
    t1, t2 = st.tabs(["Hizmetler", "Personel"])
    
    with t1:
        conn=baglan(); st.dataframe(pd.read_sql("SELECT * FROM hizmetler", conn)); conn.close()
        with st.form("add_hiz"):
            h_ad = st.text_input("Hizmet Adı"); h_fiyat = st.number_input("Fiyat", value=100)
            if st.form_submit_button("Ekle"):
                conn=baglan(); conn.execute("INSERT INTO hizmetler (hizmet_adi, fiyat) VALUES (?,?)", (h_ad, h_fiyat)); conn.commit(); conn.close(); st.rerun()
    
    with t2:
        conn=baglan(); st.dataframe(pd.read_sql("SELECT * FROM personel", conn)); conn.close()
        with st.form("add_per"):
            p_ad = st.text_input("Personel Adı")
            if st.form_submit_button("Ekle"):
                conn=baglan(); conn.execute("INSERT INTO personel (ad_soyad) VALUES (?)", (p_ad,)); conn.commit(); conn.close(); st.rerun()
