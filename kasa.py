import streamlit as st
import sqlite3
import pandas as pd

# --- AYARLAR ---
st.set_page_config(page_title="Kasa Yönetimi", page_icon="💳", layout="wide")

# Veritabanına Bağlanma
def baglan():
    return sqlite3.connect("salon.db")

# --- AKILLI GÜNCELLEME SİSTEMİ ---
# Bu fonksiyon, senin mevcut veritabanına bakar. 
# Eğer "Ödeme" sütunları yoksa, verilerini bozmadan onları ekler.
def veritabani_guncelle():
    conn = baglan()
    cursor = conn.cursor()
    
    try:
        # Randevular tablosuna 'odeme_turu' sütunu ekle
        cursor.execute("ALTER TABLE randevular ADD COLUMN odeme_turu TEXT")
        # Randevular tablosuna 'odenen_tutar' sütunu ekle
        cursor.execute("ALTER TABLE randevular ADD COLUMN odenen_tutar REAL")
        conn.commit()
        # Eğer burası çalışırsa güncelleme yapılmış demektir
        st.toast("Sistem Güncellendi: Ödeme altyapısı kuruldu! 🚀")
    except sqlite3.OperationalError:
        # Hata verirse korkma, zaten sütunlar var demektir.
        pass
    finally:
        conn.close()

# Uygulama başlarken kontrol et
veritabani_guncelle()

# --- KASA EKRANI TASARIMI ---
def kasa_ekrani():
    st.title("💳 Kasa ve Ödeme Terminali")
    
    # İki ayrı sekme yapalım: Ödeme Alma ve Raporlar
    tab1, tab2 = st.tabs(["💵 Ödeme Bekleyenler", "📊 Günlük Ciro Raporu"])
    
    # --- SEKME 1: ÖDEME AL ---
    with tab1:
        conn = baglan()
        # SQL Sorgusu: Durumu 'Onaylandı' olan randevuları getir
        # Müşteri adını ve Hizmet adını diğer tablolardan çekiyoruz (JOIN işlemi)
        sql = """
            SELECT r.id, r.saat, m.ad_soyad, h.hizmet_adi, h.fiyat 
            FROM randevular r
            JOIN musteriler m ON r.musteri_id = m.id
            JOIN hizmetler h ON r.hizmet_id = h.id
            WHERE r.durum = 'Onaylandı'
            ORDER BY r.tarih, r.saat
        """
        df = pd.read_sql(sql, conn)
        conn.close()
        
        if df.empty:
            st.success("Harika! Şuan ödemesi beklenen bir müşteri yok. 🎉")
        else:
            st.info(f"Bekleyen {len(df)} adet ödeme var.")
            
            # Her borçlu müşteri için bir kart oluştur
            for index, row in df.iterrows():
                with st.expander(f"💰 {row['ad_soyad']} - {row['hizmet_adi']} ({row['fiyat']} TL)"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    
                    with c1:
                        st.write(f"**Saat:** {row['saat']}")
                        st.write(f"**Tutar:** {row['fiyat']} TL")
                    
                    with c2:
                        if st.button("💵 Nakit Al", key=f"nakit_{row['id']}"):
                            conn = baglan()
                            conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Nakit', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Nakit tahsil edildi!")
                            st.rerun()
                            
                    with c3:
                        if st.button("💳 Kart Çek", key=f"kart_{row['id']}"):
                            conn = baglan()
                            conn.execute("UPDATE randevular SET durum='Ödendi', odeme_turu='Kredi Kartı', odenen_tutar=? WHERE id=?", (row['fiyat'], row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Kart işlemi başarılı!")
                            st.rerun()

    # --- SEKME 2: RAPOR ---
    with tab2:
        conn = baglan()
        # Sadece 'Ödendi' olanları raporla
        sql_rapor = """
            SELECT tarih, odeme_turu, SUM(odenen_tutar) as Toplam
            FROM randevular 
            WHERE durum='Ödendi'
            GROUP BY tarih, odeme_turu
            ORDER BY tarih DESC
        """
        df_rapor = pd.read_sql(sql_rapor, conn)
        conn.close()
        
        if not df_rapor.empty:
            st.dataframe(df_rapor, use_container_width=True)
            
            toplam_para = df_rapor['Toplam'].sum()
            st.metric("Toplam Kasa", f"{toplam_para} TL")
        else:
            st.warning("Henüz kasaya giren para yok.")

if __name__ == "__main__":
    kasa_ekrani()