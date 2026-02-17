import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Güzellik Salonu Paneli", page_icon="💅", layout="wide")

# Veritabanı bağlantısı
def baglan():
    conn = sqlite3.connect("salon.db")
    return conn

# --- YAN MENÜ TASARIMI ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3962/3962455.png", width=80)
st.sidebar.title("🌸 Salon Yönetimi")
st.sidebar.markdown("---") # Çizgi çeker
menu = st.sidebar.radio("Menü", ["🏠 Ana Sayfa (Dashboard)", "📅 Randevu Takvimi", "➕ Yeni Randevu", "👥 Müşteriler", "⚙️ Yönetim Paneli"])
st.sidebar.markdown("---")
st.sidebar.info("👋 İyi çalışmalar Patron!")

# --- 1. ANA SAYFA (DASHBOARD) ---
if menu == "🏠 Ana Sayfa (Dashboard)":
    # Başlık Tasarımı
    st.markdown("""
    <h1 style='text-align: center; color: #E6007E;'>✨ Güzellik Salonu Yönetim Paneli ✨</h1>
    <p style='text-align: center;'>İşletmenizin anlık durumu aşağıdadır.</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    conn = baglan()
    
    # Verileri Çekelim
    try:
        # Toplamlar
        df_musteri = pd.read_sql("SELECT count(*) as sayi FROM musteriler", conn)
        toplam_musteri = df_musteri['sayi'][0]

        df_randevu = pd.read_sql("SELECT count(*) as sayi FROM randevular", conn)
        toplam_randevu = df_randevu['sayi'][0]
        
        # Ciro Hesabı (Basitçe hizmet fiyatlarını topluyoruz)
        query_ciro = """
        SELECT SUM(h.fiyat) as ciro 
        FROM randevular r 
        JOIN hizmetler h ON r.hizmet_id = h.id
        """
        df_ciro = pd.read_sql(query_ciro, conn)
        toplam_ciro = df_ciro['ciro'][0] if df_ciro['ciro'][0] else 0

        # Hizmet Dağılımı (Grafik için)
        query_grafik = """
        SELECT h.hizmet_adi, COUNT(r.id) as adet
        FROM randevular r
        JOIN hizmetler h ON r.hizmet_id = h.id
        GROUP BY h.hizmet_adi
        """
        df_grafik = pd.read_sql(query_grafik, conn)

    except:
        toplam_musteri = 0
        toplam_randevu = 0
        toplam_ciro = 0
        df_grafik = pd.DataFrame()
    finally:
        conn.close()

    # İstatistik Kartları (Renkli Kutular)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Toplam Müşteri", f"{toplam_musteri}", "Kişi")
    col2.metric("📅 Toplam Randevu", f"{toplam_randevu}", "Adet")
    col3.metric("💰 Tahmini Ciro", f"{toplam_ciro} TL", "TL")
    col4.metric("🎯 Aylık Hedef", "%65", "Tamamlandı")

    st.markdown("---")

    # Grafik ve Bugünün İşleri
    col_sol, col_sag = st.columns([2, 1]) # Sol taraf geniş, sağ taraf dar

    with col_sol:
        st.subheader("📊 En Çok Yapılan İşlemler")
        if not df_grafik.empty:
            # Bar grafiği çizdiriyoruz
            st.bar_chart(df_grafik.set_index("hizmet_adi"))
        else:
            st.info("Veri olmadığı için grafik oluşmadı.")

    with col_sag:
        st.subheader("📆 Bugünün Randevuları")
        conn = baglan()
        bugun = datetime.now().strftime("%Y-%m-%d")
        
        query_bugun = f"""
        SELECT saat, m.ad_soyad 
        FROM randevular r
        JOIN musteriler m ON r.musteri_id = m.id
        WHERE r.tarih = '{bugun}'
        ORDER BY saat ASC
        """
        df_bugun = pd.read_sql(query_bugun, conn)
        conn.close()

        if not df_bugun.empty:
            st.table(df_bugun)
        else:
            st.success("Bugün için kayıtlı randevu yok. Keyfine bak! ☕")

# --- 2. RANDEVU TAKVİMİ ---
elif menu == "📅 Randevu Takvimi":
    st.header("🗓️ Randevu Listesi")
    conn = baglan()
    query = """
        SELECT r.id as No, r.tarih as Tarih, r.saat as Saat, m.ad_soyad as Müşteri, 
               h.hizmet_adi as İşlem, p.ad_soyad as Personel
        FROM randevular r
        JOIN musteriler m ON r.musteri_id = m.id
        JOIN hizmetler h ON r.hizmet_id = h.id
        JOIN personel p ON r.personel_id = p.id
        ORDER BY r.tarih DESC, r.saat ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        st.warning("Henüz hiç randevu yok.")
    else:
        st.dataframe(df, use_container_width=True)
        
        # Silme Bölümü
        with st.expander("🗑️ Randevu Sil"):
            sil_id = st.selectbox("Silinecek Randevu No:", df["No"])
            if st.button("Seçili Randevuyu Sil"):
                conn = baglan()
                conn.execute("DELETE FROM randevular WHERE id = ?", (int(sil_id),))
                conn.commit()
                conn.close()
                st.success("Silindi!")
                st.rerun()

# --- 3. YENİ RANDEVU EKLEME ---
elif menu == "➕ Yeni Randevu":
    st.header("✨ Yeni Randevu Oluştur")