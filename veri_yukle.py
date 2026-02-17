import sqlite3

def ornek_verileri_yukle():
    conn = sqlite3.connect("salon.db")
    cursor = conn.cursor()

    print("🔄 Veriler yükleniyor...")

    # 1. Örnek Müşteriler
    musteriler = [
        ("Selin Demir", "5551112233", "Hassas cilt"),
        ("Ayşe Yılmaz", "5554445566", "VIP Müşteri"),
        ("Zeynep Kaya", "5557778899", "Kahve sever")
    ]
    for m in musteriler:
        try:
            cursor.execute("INSERT INTO musteriler (ad_soyad, telefon, notlar) VALUES (?, ?, ?)", m)
        except:
            pass # Zaten varsa geç

    # 2. Örnek Personel
    personeller = [
        ("Merve Uzman", "Manikür", "5051234567"),
        ("Ali Kesimci", "Saç Tasarım", "5059876543")
    ]
    for p in personeller:
        cursor.execute("INSERT INTO personel (ad_soyad, uzmanlik, telefon) VALUES (?, ?, ?)", p)

    # 3. Örnek Hizmetler
    hizmetler = [
        ("Manikür", 45, 300),
        ("Pedikür", 60, 400),
        ("Saç Kesimi", 30, 250),
        ("Fön", 20, 100)
    ]
    for h in hizmetler:
        cursor.execute("INSERT INTO hizmetler (hizmet_adi, sure_dk, fiyat) VALUES (?, ?, ?)", h)

    conn.commit()
    conn.close()
    print("✅ Harika! Dükkanın içi doldu. Artık randevu verebilirsin.")

if __name__ == "__main__":
    ornek_verileri_yukle()