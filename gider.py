import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- AYARLAR ---
st.set_page_config(page_title="Gider Takibi", page_icon="💸", layout="wide")

# Veritabanı Bağlantısı
def baglan():
    return sqlite3.connect("salon.db")

# Tablo Kontrolü (Otomatik Kurulum)
def tablo_kur():
    conn = baglan()
    c = conn.cursor()
    # Giderler tablosu yoksa oluştur
    c.execute("""
        CREATE TABLE IF NOT EXISTS giderler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT,
            kategori TEXT,
            tutar REAL,
            tarih TEXT,
            notlar TEXT
        )
    """)
    conn.commit()
    conn.close()

tablo_kur() # Başlangıçta çalıştır

# --- GİDER EKRANI ---
def gider_ekrani():
    st.title("💸 Gider ve Masraf Yönetimi")
    
    col1, col2 = st.columns([1, 2])
    
    # --- SOL TARAF: YENİ GİDER EKLEME ---
    with col1:
        st.header("Harcama Ekle")
        with st.form("gider_form"):
            baslik = st.text_input("Harcama Adı (Örn: Kira, Şampuan)")
            kategori = st.selectbox("Kategori", ["Kira/Aidat", "Fatura (Elektrik/Su)", "Malzeme Alımı", "Personel Gideri", "Diğer"])
            tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
            tarih = st.date_input("Harcama Tarihi", datetime.now())
            notlar = st.text_area("Not (Opsiyonel)")
            
            kaydet = st.form_submit_button("Masrafı Kaydet ➖")
            
            if kaydet:
                if baslik and tutar > 0:
                    conn = baglan()
                    conn.execute("INSERT INTO giderler (baslik, kategori, tutar, tarih, notlar) VALUES (?, ?, ?, ?, ?)", 
                                 (baslik, kategori, tutar, str(tarih), notlar))
                    conn.commit()
                    conn.close()
                    st.success("Harcama kaydedildi!")
                    st.rerun()
                else:
                    st.error("Lütfen başlık ve tutar girin!")

    # --- SAĞ TARAF: LİSTE VE GRAFİK ---
    with col2:
        st.header("📊 Gider Analizi")
        
        conn = baglan()
        # Tüm giderleri çek
        df = pd.read_sql("SELECT * FROM giderler ORDER BY tarih DESC", conn)
        conn.close()
        
        if not df.empty:
            # 1. Özet Kartları
            toplam_gider = df['tutar'].sum()
            en_buyuk_kalem = df.loc[df['tutar'].idxmax()]['baslik']
            
            k1, k2 = st.columns(2)
            k1.metric("Toplam Harcama", f"{toplam_gider} TL", delta="-Gider", delta_color="inverse")
            k2.metric("En Büyük Kalem", en_buyuk_kalem)
            
            st.markdown("---")
            
            # 2. Pasta Grafiği (Paralar Nereye Gidiyor?)
            st.subheader("Harcama Dağılımı")
            # Kategorilere göre grupla ve topla
            df_grup = df.groupby("kategori")["tutar"].sum().reset_index()
            
            # Streamlit'in pasta grafiği
            st.bar_chart(df_grup.set_index("kategori"))

            # 3. Detaylı Liste
            with st.expander("Detaylı Harcama Listesi (Tıkla Gör)"):
                st.dataframe(df, use_container_width=True)
                
                # Silme Butonu
                sil_id = st.selectbox("Silinecek Kayıt ID", df['id'])
                if st.button("Seçili Gideri Sil"):
                    conn = baglan()
                    conn.execute("DELETE FROM giderler WHERE id=?", (sil_id,))
                    conn.commit()
                    conn.close()
                    st.warning("Kayıt silindi.")
                    st.rerun()
        else:
            st.info("Henüz kaydedilmiş bir gider yok. İşler yolunda! 😎")

if __name__ == "__main__":
    gider_ekrani()