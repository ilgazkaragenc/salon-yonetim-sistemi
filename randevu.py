import sqlite3

def baglan():
    return sqlite3.connect("salon.db")

def listeleri_getir(tablo_adi):
    conn = baglan()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {tablo_adi}")
    liste = cursor.fetchall()
    conn.close()
    return liste

def randevu_olustur():
    print("\n--- 📅 YENİ RANDEVU OLUŞTUR ---")
    
    # 1. Müşteri Seçimi
    print("\n--- MÜŞTERİ SEÇİN ---")
    musteriler = listeleri_getir("musteriler")
    for m in musteriler:
        print(f"[{m[0]}] {m[1]}") # ID ve Ad
    m_id = input("Müşteri Numarası (ID) girin: ")

    # 2. Hizmet Seçimi
    print("\n--- HİZMET SEÇİN ---")
    hizmetler = listeleri_getir("hizmetler")
    for h in hizmetler:
        print(f"[{h[0]}] {h[1]} ({h[3]} TL)")
    h_id = input("Hizmet Numarası (ID) girin: ")

    # 3. Personel Seçimi
    print("\n--- PERSONEL SEÇİN ---")
    personel = listeleri_getir("personel")
    for p in personel:
        print(f"[{p[0]}] {p[1]}")
    p_id = input("Personel Numarası (ID) girin: ")

    # 4. Tarih ve Saat
    tarih = input("\nTarih (Yıl-Ay-Gün, örn: 2023-10-25): ")
    saat = input("Saat (örn: 14:30): ")

    # 5. Kaydetme İşlemi
    conn = baglan()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO randevular (musteri_id, personel_id, hizmet_id, tarih, saat, durum)
            VALUES (?, ?, ?, ?, ?, 'Onaylandı')
        """, (m_id, p_id, h_id, tarih, saat))
        conn.commit()
        print("\n✅ Randevu başarıyla oluşturuldu!")
    except Exception as e:
        print(f"\n❌ HATA: {e}")
    finally:
        conn.close()

def randevulari_goster():
    print("\n--- 🗓️ GÜNCEL RANDEVU LİSTESİ ---")
    conn = baglan()
    cursor = conn.cursor()
    
    # Bu sorgu biraz karmaşık çünkü ID'ler yerine isimleri getiriyoruz (JOIN işlemi)
    sorgu = """
        SELECT r.id, r.tarih, r.saat, m.ad_soyad, h.hizmet_adi, p.ad_soyad, r.durum
        FROM randevular r
        JOIN musteriler m ON r.musteri_id = m.id
        JOIN hizmetler h ON r.hizmet_id = h.id
        JOIN personel p ON r.personel_id = p.id
        ORDER BY r.tarih, r.saat
    """
    cursor.execute(sorgu)
    kayitlar = cursor.fetchall()
    conn.close()

    if not kayitlar:
        print("📭 Henüz randevu yok.")
    else:
        print(f"{'TARİH':<12} {'SAAT':<6} {'MÜŞTERİ':<15} {'İŞLEM':<15} {'PERSONEL':<10}")
        print("-" * 65)
        for r in kayitlar:
            # r[1]=Tarih, r[2]=Saat, r[3]=Müşteri, r[4]=Hizmet, r[5]=Personel
            print(f"{r[1]:<12} {r[2]:<6} {r[3]:<15} {r[4]:<15} {r[5]:<10}")

# --- MENÜ ---
if __name__ == "__main__":
    while True:
        print("\n" + "="*30)
        print("   RANDEVU YÖNETİM MERKEZİ")
        print("="*30)
        print("1. Randevu Oluştur")
        print("2. Randevuları Listele")
        print("3. Çıkış")
        
        secim = input("Seçiminiz (1-3): ")
        
        if secim == '1':
            randevu_olustur()
        elif secim == '2':
            randevulari_goster()
        elif secim == '3':
            print("Çıkış yapılıyor...")
            break
        else:
            print("Geçersiz seçim!")