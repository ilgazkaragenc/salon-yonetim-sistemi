import streamlit as st
import sqlite3
import pandas as pd

# --- AYARLAR ---
st.set_page_config(page_title="Finansal Raporlar", page_icon="📈", layout="wide")

def baglan():
    return sqlite3.connect("salon.db")

def rapor_ekrani():
    st.title("📈 Patron Paneli: Kâr & Zarar Analizi")
    st.markdown("İşletmenizin genel finansal sağlığı aşağıdadır.")

    conn = baglan()

    # 1. TOPLAM GELİR (Kasaya Giren)
    # Sadece 'Ödendi' durumundaki paraları topla
    df_gelir = pd.read_sql("SELECT SUM(odenen_tutar) as Toplam FROM randevular WHERE durum='Ödendi'", conn)
    toplam_gelir = df_gelir['Toplam'][0]
    if toplam_gelir is None: toplam_gelir = 0

    # 2. TOPLAM GİDER (Cepten Çıkan)
    df_gider = pd.read_sql("SELECT SUM(tutar) as Toplam FROM giderler", conn)
    toplam_gider = df_gider['Toplam'][0]
    if toplam_gider is None: toplam_gider = 0

    conn.close()

    # 3. NET KÂR HESABI
    net_kar = toplam_gelir - toplam_gider

    # --- KARTLARLA GÖSTERİM ---
    col1, col2, col3 = st.columns(3)

    # Gelir Kartı (Yeşil)
    col1.metric("💰 Toplam Gelir (Kasa)", f"{toplam_gelir:,.2f} TL", delta="Giriş")

    # Gider Kartı (Kırmızı)
    col2.metric("💸 Toplam Gider (Masraf)", f"{toplam_gider:,.2f} TL", delta="-Çıkış", delta_color="inverse")

    # Net Kâr Kartı (Duruma Göre Renkli)
    if net_kar >= 0:
        durum_mesaji = "Harika! Kârdasın 🥳"
        renk = "normal" # Yeşilimsi
    else:
        durum_mesaji = "Dikkat! Zarardasın ⚠️"
        renk = "inverse" # Kırmızımsı
        
    col3.metric("🏆 NET KÂR", f"{net_kar:,.2f} TL", delta=durum_mesaji, delta_color=renk)

    st.markdown("---")

    # --- GRAFİKLİ ANALİZ ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 Gelir vs Gider Dengesi")
        # Basit bir karşılaştırma tablosu yapıp grafiğe dökelim
        veri = {
            "Tip": ["Gelir (Kazanılan)", "Gider (Harcanan)"],
            "Tutar": [toplam_gelir, toplam_gider]
        }
        df_karsilastirma = pd.DataFrame(veri)
        
        # Bar grafiği
        st.bar_chart(df_karsilastirma.set_index("Tip"), color=["#27ae60"]) # Yeşil tonu

    with c2:
        st.subheader("💡 Patron Notu")
        if net_kar > 0:
            st.success(f"""
            Tebrikler Patron! 
            Şu ana kadar cebine net **{net_kar} TL** kaldı.
            İşler yolunda gidiyor.
            """)
            st.balloons()
        elif net_kar == 0:
            st.warning("Ne kâr ne zarar. Başabaş noktasındasın.")
        else:
            st.error(f"""
            Patron, işler biraz sıkıntılı.
            Şu an **{abs(net_kar)} TL** içeridesin.
            Harcamaları kıssan veya daha çok müşteri bulsan iyi olur!
            """)

if __name__ == "__main__":
    rapor_ekrani()