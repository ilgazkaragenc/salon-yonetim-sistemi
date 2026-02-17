import sqlite3

def veritabani_baslat():
    # Bu kod çalıştığında 'salon.db' adında bir dosya oluşturur.
    conn = sqlite3.connect("salon.db")
    cursor = conn.cursor()
    
    # 1. Müşteriler Tablosu (Ad, Tel, Notlar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad TEXT NOT NULL,
        telefon TEXT UNIQUE,
        notlar TEXT,
        yasakli_mi BOOLEAN DEFAULT 0,
        puan INTEGER DEFAULT 0
    )
    """)

    # 2. Personel Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad TEXT NOT NULL,
        uzmanlik TEXT,
        telefon TEXT
    )
    """)

    # 3. Hizmetler Tablosu (Fiyat ve Süre)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hizmetler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hizmet_adi TEXT NOT NULL,
        sure_dk INTEGER,
        fiyat REAL
    )
    """)

    # 4. Randevular Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS randevular (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_id INTEGER,
        personel_id INTEGER,
        hizmet_id INTEGER,
        tarih TEXT,
        saat TEXT,
        durum TEXT DEFAULT 'Bekliyor',
        FOREIGN KEY(musteri_id) REFERENCES musteriler(id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Veritabanı ve Tablolar Başarıyla Oluşturuldu!")

if __name__ == "__main__":
    veritabani_baslat()