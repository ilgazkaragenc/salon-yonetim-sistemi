import sqlite3

# Veritabanına bağlanma fonksiyonu
def baglan():
    return sqlite3.connect("salon.db")

def musteri_ekle():
    print("\n--- 👤 YENİ MÜŞTERİ EKLE ---")
    ad = input("Müşteri Adı Soyadı: ")
    tel = input("Telefon Numarası: ")
    notlar = input("Özel Not (Alerji vb.): ")

    conn = baglan()
    cursor = conn.cursor()
    
    try:
        # Veriyi ekle
        cursor.execute("INSERT INTO musteriler (ad_soyad, telefon, notlar) VALUES (?, ?, ?)", (ad, tel, notlar))
        conn.commit()
        print(f"\n✅ {ad} başarıyla kaydedildi!")
    except sqlite3.IntegrityError:
        print("\n❌ HATA: Bu telefon numarası zaten kayıtlı!")
    finally:
        conn.close()

def musteri_listele():
    print("\n--- 📋 MÜŞTERİ LİSTESİ ---")
    conn = baglan()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, ad_soyad, telefon, notlar FROM musteriler")
    veriler = cursor.fetchall()
    conn.close()

    if not veriler:
        print("📭 Henüz kayıtlı müşteri yok.")
    else:
        print(f"{'ID':<4} {'AD SOYAD':<20} {'TELEFON':<15} {'NOT'}")
        print("-" * 50)
        for v in veriler:
            print(f"{v[0]:<4} {v[1]:<20} {v[2]:<15} {v[3]}")

# --- MENÜ SİSTEMİ ---
if __name__ == "__main__":
    while True:
        print("\n" + "="*30)
        print("   MÜŞTERİ YÖNETİM PANELİ")
        print("="*30)
        print("1. Yeni Müşteri Ekle")
        print("2. Müşterileri Listele")
        print("3. Çıkış")
        
        secim = input("Seçiminiz (1-3): ")
        
        if secim == '1':
            musteri_ekle()
        elif secim == '2':
            musteri_listele()
        elif secim == '3':
            print("Çıkış yapılıyor...")
            break
        else:
            print("Geçersiz seçim!")