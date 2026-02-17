import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. SAYFA AYARLARI VE TASARIM (CSS) ---
st.set_page_config(page_title="Gold Salon Yönetimi", page_icon="✂️", layout="wide")

# Özel Tasarım Kodları
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
    .stButton>button {border-radius: 20px; font-weight: bold; width: 100%;}
</style>
""", unsafe_allow_html=True)

# --- 2. VERİTABANI BAĞLANTISI ---
def baglan():
    return sqlite3.connect("salon.db")

# Tabloları kontrol et ve yoksa oluştur (Tamir Fonksiyonu)
def db_kontrol():
    conn = baglan()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, telefon TEXT, notlar TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS hizmetler (id INTEGER PRIMARY KEY AUTOINCREMENT, hizmet_adi TEXT, sure_dk INTEGER, fiyat REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, uzmanlik TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS randevular (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, personel_id INTEGER, hizmet_id INTEGER, tarih TEXT, saat TEXT, durum TEXT)")
    conn.commit()
    conn.close()

db_kontrol() # Uygulama açılınca veritabanını kontrol et

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3962/3962455.png", width=80)
    st.title("Salon Yönetimi")
    st.markdown("---")
    menu = st.radio("MENÜ", ["📊 Dashboard", "📅 Randevu Takvimi", "➕ Yeni Randevu", "👥 Müşteriler", "⚙️ Ayarlar (Personel/Hizmet)"])
    st.markdown("---")

# --- 4. DASHBOARD (ANA EKRAN) ---
if menu == "📊 Dashboard":
    st.title("📊 Yönetim Paneli")
    conn = baglan()
    
    # İstatistikler
    try:
        mus = pd.read_sql("SELECT count(*) FROM musteriler", conn).iloc[0,0]
        ran = pd.read_sql("SELECT count(*) FROM randevular", conn).iloc[0,0]
        ciro_sql = "SELECT SUM(h.fiyat) FROM randevular r JOIN hizmetler h ON r.hizmet_id = h.id"
        ciro = pd.read_sql(ciro_sql, conn).iloc[0,0]
        ciro = ciro if ciro else 0
    except:
        mus=0; ran=0; ciro=0
    finally:
        conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Müşteri", f"{mus}")
    c2.metric("Toplam Randevu", f"{ran}")
    c3.metric("Tahmini Ciro", f"{ciro} TL")

    st.markdown("---")
    
    # Grafikler
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📆 Bugünün Randevuları")
        bugun = datetime.now().strftime("%Y-%m-%d")
        conn = baglan()
        df_bugun = pd.read_sql(f"""
            SELECT r.saat, m.ad_soyad, h.hizmet_adi 
            FROM randevular r 
            JOIN musteriler m ON r.musteri_id=m.id 
            JOIN hizmetler h ON r.hizmet_id=h.id 
            WHERE r.tarih='{bugun}' ORDER BY r.saat""", conn)
        conn.close()
        if not df_bugun.empty:
            st.dataframe(df_bugun, use_container_width=True)
        else:
            st.info("Bugün için kayıtlı randevu yok.")

    with col2:
        st.subheader("📈 Hizmet Dağılımı")
        conn = baglan()
        df_gr = pd.read_sql("SELECT h.hizmet_adi, count(*) as adet FROM randevular r JOIN hizmetler h ON r.hizmet_id=h.id GROUP BY h.hizmet_adi", conn)
        conn.close()
        if not df_gr.empty:
            st.bar_chart(df_gr.set_index("hizmet_adi"))

# --- 5. RANDEVU TAKVİMİ ---
elif menu == "📅 Randevu Takvimi":
    st.title("🗓️ Randevu Ajandası")
    conn = baglan()
    df = pd.read_sql("""
        SELECT r.id as No, r.tarih, r.saat, m.ad_soyad as Müşteri, h.hizmet_adi as İşlem, p.ad_soyad as Personel 
        FROM randevular r
        JOIN musteriler m ON r.musteri_id = m.id
        JOIN hizmetler h ON r.hizmet_id = h.id
        JOIN personel p ON r.personel_id = p.id
        ORDER BY r.tarih DESC, r.saat ASC
    """, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        with st.expander("🗑️ Randevu Sil"):
            sil_id = st.selectbox("Silinecek No:", df['No'])
            if st.button("Seçili Randevuyu Sil"):
                conn = baglan()
                conn.execute("DELETE FROM randevular WHERE id=?", (int(sil_id),))
                conn.commit()
                conn.close()
                st.success("Silindi!")
                st.rerun()
    else:
        st.warning("Randevu bulunamadı.")

# --- 6. YENİ RANDEVU ---
elif menu == "➕ Yeni Randevu":
    st.title("✨ Yeni Randevu Ekle")
    conn = baglan()
    m_df = pd.read_sql("SELECT * FROM musteriler", conn)
    h_df = pd.read_sql("SELECT * FROM hizmetler", conn)
    p_df = pd.read_sql("SELECT * FROM personel", conn)
    conn.close()

    if m_df.empty or h_df.empty:
        st.error("Lütfen önce Müşteri ve Hizmet ekleyin (Ayarlar menüsünden).")
    else:
        with st.form("randevu_add"):
            c1, c2 = st.columns(2)
            with c1:
                sec_m = st.selectbox("Müşteri", m_df['ad_soyad'])
                sec_h = st.selectbox("Hizmet", h_df['hizmet_adi'])
            with c2:
                sec_p = st.selectbox("Personel", p_df['ad_soyad'])
                tar = st.date_input("Tarih")
                saa = st.time_input("Saat")
            
            if st.form_submit_button("Randevuyu Kaydet ✅"):
                m_id = m_df[m_df['ad_soyad']==sec_m]['id'].values[0]
                h_id = h_df[h_df['hizmet_adi']==sec_h]['id'].values[0]
                p_id = p_df[p_df['ad_soyad']==sec_p]['id'].values[0]
                
                conn = baglan()
                conn.execute("INSERT INTO randevular (musteri_id, personel_id, hizmet_id, tarih, saat) VALUES (?,?,?,?,?)", 
                             (int(m_id), int(p_id), int(h_id), str(tar), str(saa)))
                conn.commit()
                conn.close()
                st.success("Randevu Oluşturuldu!")

# --- 7. MÜŞTERİ YÖNETİMİ ---
elif menu == "👥 Müşteriler":
    st.title("👥 Müşteri Listesi")
    with st.expander("➕ Yeni Müşteri Ekle"):
        with st.form("mus_add"):
            ad = st.text_input("Ad Soyad")
            tel = st.text_input("Telefon")
            notlar = st.text_area("Notlar")
            if st.form_submit_button("Müşteriyi Kaydet"):
                conn = baglan()
                conn.execute("INSERT INTO musteriler (ad_soyad, telefon, notlar) VALUES (?,?,?)", (ad, tel, notlar))
                conn.commit()
                conn.close()
                st.success("Eklendi!")
                st.rerun()
    
    conn = baglan()
    st.dataframe(pd.read_sql("SELECT * FROM musteriler", conn), use_container_width=True)
    conn.close()

# --- 8. AYARLAR (HİZMET & PERSONEL) ---
elif menu == "⚙️ Ayarlar (Personel/Hizmet)":
    st.title("⚙️ Salon Ayarları")
    tab1, tab2 = st.tabs(["Hizmetler", "Personel"])

    with tab1:
        st.subheader("Hizmet Listesi")
        conn = baglan()
        st.dataframe(pd.read_sql("SELECT * FROM hizmetler", conn), use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.form("hiz_add"):
                h_ad = st.text_input("Hizmet Adı")
                h_fiyat = st.number_input("Fiyat", value=100)
                h_sure = st.number_input("Süre (dk)", value=30)
                if st.form_submit_button("Hizmet Ekle"):
                    conn.execute("INSERT INTO hizmetler (hizmet_adi, sure_dk, fiyat) VALUES (?,?,?)", (h_ad, h_sure, h_fiyat))
                    conn.commit()
                    st.rerun()
        with c2:
             with st.form("hiz_del"):
                h_sil = st.text_input("Silinecek Hizmet Adı (Tam Yazın)")
                if st.form_submit_button("Hizmeti Sil"):
                    conn.execute("DELETE FROM hizmetler WHERE hizmet_adi=?", (h_sil,))
                    conn.commit()
                    st.warning("Silindi!")
                    st.rerun()
        conn.close()

    with tab2:
        st.subheader("Personel Listesi")
        conn = baglan()
        st.dataframe(pd.read_sql("SELECT * FROM personel", conn), use_container_width=True)
        
        c3, c4 = st.columns(2)
        with c3:
            with st.form("per_add"):
                p_ad = st.text_input("Personel Adı")
                p_uzm = st.text_input("Uzmanlık")
                if st.form_submit_button("Personel Ekle"):
                    conn.execute("INSERT INTO personel (ad_soyad, uzmanlik) VALUES (?,?)", (p_ad, p_uzm))
                    conn.commit()
                    st.rerun()
        with c4:
            with st.form("per_del"):
                p_sil = st.text_input("Silinecek Personel Adı")
                if st.form_submit_button("Personeli Sil"):
                    conn.execute("DELETE FROM personel WHERE ad_soyad=?", (p_sil,))
                    conn.commit()
                    st.warning("Silindi!")
                    st.rerun()
        conn.close()