import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Güzellik Salonu Paneli", page_icon="💅", layout="wide")

# Veritabanı bağlantısı
def baglan():
    return sqlite3.connect("salon.db")

# --- YAN MENÜ TASARIMI ---
st.sidebar.title("🌸 Salon Yönetimi")
st.sidebar.info("Hoşgeldiniz, Patron! 👋")
menu = st.sidebar.radio("Menü", ["🏠 Ana Sayfa", "📅 Randevu Takvimi", "➕ Yeni Randevu", "👥 Müşteriler", "⚙️ Yönetim Paneli (Fiyat/Personel)"])

# --- 1. ANA SAYFA (DASHBOARD) ---
if menu == "🏠 Ana Sayfa":
    st.title("📊 Günlük Özet Raporu")
    
    conn = baglan()
    try:
        c_mus = conn.cursor()
        c_mus.execute("SELECT COUNT(*) FROM musteriler")
        toplam_musteri = c_mus.fetchone()[0]

        c_ran = conn.cursor()
        c_ran.execute("SELECT COUNT(*) FROM randevular")
        toplam_randevu = c_ran.fetchone()[0]
    except:
        toplam_musteri = 0
        toplam_randevu = 0
    finally:
        conn.close()

    # İstatistik Kartları
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Müşteri", f"{toplam_musteri} Kişi", "📈 Artış Var")
    col2.metric("Toplam Randevu", f"{toplam_randevu} Adet", "📅 Takvim Doluyor")
    col3.metric("Kasa Hedefi", "15.000 TL", "💰 Durum İyi")

    st.image("https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?q=80&w=2000&auto=format&fit=crop", caption="Salon Yönetim Paneli", use_container_width=True)

# --- 2. RANDEVU TAKVİMİ ---
elif menu == "📅 Randevu Takvimi":
    st.header("🗓️ Randevu Listesi")
    
    conn = baglan()
    query = """
        SELECT r.id as RandevuNo, r.tarih as Tarih, r.saat as Saat, m.ad_soyad as Müşteri, 
               h.hizmet_adi as İşlem, p.ad_soyad as Personel, r.durum as Durum
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
        
        # Randevu Silme Butonu
        with st.expander("🗑️ Randevu İptal Et / Sil"):
            silinecek_id = st.selectbox("İptal edilecek randevuyu seç (No):", df["RandevuNo"])
            if st.button("Seçili Randevuyu Sil"):
                conn = baglan()
                conn.execute("DELETE FROM randevular WHERE id = ?", (int(silinecek_id),))
                conn.commit()
                conn.close()
                st.success("Randevu silindi!")
                st.rerun()

# --- 3. YENİ RANDEVU EKLEME ---
elif menu == "➕ Yeni Randevu":
    st.header("✨ Yeni Randevu Oluştur")

    conn = baglan()
    musteriler = pd.read_sql("SELECT id, ad_soyad FROM musteriler", conn)
    hizmetler = pd.read_sql("SELECT id, hizmet_adi, fiyat FROM hizmetler", conn)
    personeller = pd.read_sql("SELECT id, ad_soyad FROM personel", conn)
    conn.close()

    if musteriler.empty or hizmetler.empty:
        st.error("Lütfen önce Yönetim Panelinden Müşteri ve Hizmet ekleyin!")
    else:
        with st.form("randevu_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                secilen_musteri = st.selectbox("Müşteri Seç:", musteriler["ad_soyad"])
                secilen_hizmet = st.selectbox("Hizmet Seç:", hizmetler["hizmet_adi"])
            
            with col2:
                secilen_personel = st.selectbox("Personel Seç:", personeller["ad_soyad"])
                tarih = st.date_input("Randevu Tarihi")
                saat = st.time_input("Randevu Saati")
            
            kaydet_btn = st.form_submit_button("Randevuyu Onayla ✅")

            if kaydet_btn:
                m_id = musteriler[musteriler["ad_soyad"] == secilen_musteri]["id"].values[0]
                h_id = hizmetler[hizmetler["hizmet_adi"] == secilen_hizmet]["id"].values[0]
                p_id = personeller[personeller["ad_soyad"] == secilen_personel]["id"].values[0]

                conn = baglan()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO randevular (musteri_id, personel_id, hizmet_id, tarih, saat, durum)
                    VALUES (?, ?, ?, ?, ?, 'Onaylandı')
                """, (int(m_id), int(p_id), int(h_id), str(tarih), str(saat)))
                conn.commit()
                conn.close()
                st.success(f"Harika! {secilen_musteri} için randevu oluşturuldu.")

# --- 4. MÜŞTERİ YÖNETİMİ ---
elif menu == "👥 Müşteriler":
    st.header("Müşteri Listesi & Kayıt")
    
    with st.expander("➕ Yeni Müşteri Ekle"):
        with st.form("yeni_musteri"):
            ad = st.text_input("Adı Soyadı")
            tel = st.text_input("Telefon")
            notlar = st.text_area("Notlar")
            submit = st.form_submit_button("Kaydet")
            
            if submit:
                conn = baglan()
                try:
                    conn.execute("INSERT INTO musteriler (ad_soyad, telefon, notlar) VALUES (?, ?, ?)", (ad, tel, notlar))
                    conn.commit()
                    st.success("Müşteri Eklendi!")
                    st.rerun()
                except:
                    st.error("Bu numara zaten kayıtlı!")
                finally:
                    conn.close()
    
    conn = baglan()
    df_musteri = pd.read_sql("SELECT ad_soyad, telefon, notlar FROM musteriler", conn)
    st.dataframe(df_musteri, use_container_width=True)
    conn.close()

# --- 5. GELİŞMİŞ YÖNETİM PANELİ (BURASI YENİLENDİ) ---
elif menu == "⚙️ Yönetim Paneli (Fiyat/Personel)":
    st.header("🛠️ Salon Ayarları")
    
    tab1, tab2 = st.tabs(["💅 Hizmet & Fiyatlar", "👩‍💼 Personel Yönetimi"])

    # --- TAB 1: HİZMETLER ---
    with tab1:
        st.subheader("Hizmet Listesi")
        conn = baglan()
        df_hizmet = pd.read_sql("SELECT id, hizmet_adi, sure_dk, fiyat FROM hizmetler", conn)
        st.dataframe(df_hizmet, use_container_width=True)
        
        col_a, col_b = st.columns(2)
        
        # Hizmet Ekleme
        with col_a:
            with st.form("hizmet_ekle"):
                st.write("**Yeni Hizmet Ekle**")
                y_ad = st.text_input("Hizmet Adı (Örn: Cilt Bakımı)")
                y_sure = st.number_input("Süre (Dakika)", min_value=10, value=30)
                y_fiyat = st.number_input("Fiyat (TL)", min_value=0, value=100)
                if st.form_submit_button("Hizmeti Ekle"):
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO hizmetler (hizmet_adi, sure_dk, fiyat) VALUES (?, ?, ?)", (y_ad, y_sure, y_fiyat))
                    conn.commit()
                    st.success("Eklendi!")
                    st.rerun()

        # Hizmet Silme
        with col_b:
            with st.form("hizmet_sil"):
                st.write("**Hizmet Sil**")
                # Silinecek hizmeti seçtirmek için selectbox
                silinecek = st.selectbox("Silinecek Hizmeti Seç", df_hizmet["hizmet_adi"])
                if st.form_submit_button("Seçileni Sil"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM hizmetler WHERE hizmet_adi = ?", (silinecek,))
                    conn.commit()
                    st.warning("Hizmet Silindi!")
                    st.rerun()
        conn.close()

    # --- TAB 2: PERSONEL ---
    with tab2:
        st.subheader("Personel Listesi")
        conn = baglan()
        df_personel = pd.read_sql("SELECT id, ad_soyad, uzmanlik FROM personel", conn)
        st.dataframe(df_personel, use_container_width=True)
        
        col_c, col_d = st.columns(2)
        
        # Personel Ekleme
        with col_c:
            with st.form("personel_ekle"):
                st.write("**Yeni Personel Ekle**")
                p_ad = st.text_input("Ad Soyad")
                p_uzmanlik = st.text_input("Uzmanlık (Örn: Saç Kesim)")
                if st.form_submit_button("Personeli Kaydet"):
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO personel (ad_soyad, uzmanlik) VALUES (?, ?)", (p_ad, p_uzmanlik))
                    conn.commit()
                    st.success("Personel Eklendi!")
                    st.rerun()

        # Personel Silme
        with col_d:
            with st.form("personel_sil"):
                st.write("**Personel Çıkar**")
                p_silinecek = st.selectbox("Silinecek Personel", df_personel["ad_soyad"])
                if st.form_submit_button("Personeli Sil"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM personel WHERE ad_soyad = ?", (p_silinecek,))
                    conn.commit()
                    st.warning("Personel Silindi!")
                    st.rerun()
        conn.close()