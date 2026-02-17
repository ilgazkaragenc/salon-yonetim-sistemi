import sqlite3

def baglan():
    return sqlite3.connect("salon.db")

def hizmet_ekle():
    print("\n--- 💅 YENİ HİZMET EKLE ---")
    ad = input("Hizmet Adı (Örn: Saç Kesimi): ")
    sure = input("Süresi (Dakika olarak, örn: 30): ")
    fiyat = input("Fiyatı (TL olarak, örn: 250): ")

    conn = baglan()
    cursor = conn.cursor()
    # Hizmeti veritabanına kaydet
    cursor.execute("INSERT INTO hizmetler (hizmet_adi, sure_dk, fiyat) VALUES (?, ?, ?)", (ad, sure, fiyat))
    conn.commit()
    conn.close()
    print(f"\n✅ {ad} hizmeti başarıyla eklendi!")

def personel_ekle():
    print("\n--- 👩‍💼 YENİ PERSONEL EKLE ---")
    ad = input("Personel Adı Soyadı: ")
    uzmanlik = input("Uzmanlık Alanı (Örn: Manikür): ")

    conn = baglan()
    cursor = conn.cursor()
    # Personeli veritabanına kaydet
    cursor.execute("INSERT INTO personel (ad_soyad, uzmanlik) VALUES (?, ?)", (ad, uzmanlik))
    conn.commit()
    conn.close()
    print(f"\n✅ {ad} ekibe katıldı!")

def listeleri_goster():
    conn = baglan()
    cursor = conn.cursor()

    print("\n--- 📋 HİZMET LİSTESİ ---")
    cursor.execute("SELECT * FROM hizmetler")
    for h in cursor.fetchall():
        # h[1]=Ad, h[2]=Süre, h[3]=Fiyat
        print(f"ID: {h[0]} | {h[1]} ({h[2]} dk) - {h[3]} TL")

    print("\n--- 👥 PERSONEL LİSTESİ ---")
    cursor.execute("SELECT * FROM personel")
    for p in cursor.fetchall():
        # p[1]=Ad, p[2]=Uzmanlık
        print(f"ID: {p[0]} | {p[1]} ({p[2]})")
    
    conn.close()

# --- MENÜ SİSTEMİ ---
if __name__ == "__main__":
    while True:
        print("\n" + "="*30)
        print("   HİZMET & PERSONEL YÖNETİMİ")
        print("="*30)
        print("1. Yeni Hizmet Ekle")
        print("2. Yeni Personel Ekle")
        print("3. Listeleri Gör")
        print("4. Çıkış")
        
        secim = input("Seçiminiz (1-4): ")
        
        if secim == '1':
            hizmet_ekle()
        elif secim == '2':
            personel_ekle()
        elif secim == '3':
            listeleri_goster()
        elif secim == '4':
            print("Çıkış yapılıyor...")
            break
        else:
            print("Geçersiz seçim!")