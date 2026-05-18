# 🗂️ CRM Pro

Python ve Tkinter ile geliştirilmiş masaüstü müşteri ilişkileri yönetim (CRM) uygulaması.

---

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Dosya Yapısı](#dosya-yapısı)
- [Mimari](#mimari)
- [Kullanım](#kullanım)
- [Veri Yapısı](#veri-yapısı)
- [Geliştirme Önerileri](#geliştirme-önerileri)

---

## Genel Bakış

| Alan | Bilgi |
|---|---|
| **Programlama Dili** | Python 3.x |
| **Arayüz Kütüphanesi** | tkinter (standart kütüphane) |
| **Veri Saklama** | JSON dosyaları |
| **Mimari** | 3 Katmanlı (Model / Veri Erişim / Sunum) |
| **Dosya Sayısı** | 3 Python + 3 JSON |

---

## Özellikler

- Müşteri ekleme, düzenleme, silme ve arama
- Satış takibi (durum: Beklemede / Tamamlandı / İptal)
- Destek talebi yönetimi (öncelik: Düşük / Orta / Yüksek / Acil)
- Canlı dashboard: istatistik kartları, aylık ciro grafiği, şehir dağılımı
- Karanlık / Aydınlık tema desteği
- CSV dışa aktarma
- Müşteri detay penceresi (bağlı satışlar ve talepler)
- Şehre göre müşteri filtreleme
- Arama: ad, telefon ve e-postada eş zamanlı

---

## Kurulum

**Gereksinimler:** Python 3.x (tkinter standart kütüphaneyle birlikte gelir, ek kurulum gerekmez.)

```bash
# Repoyu klonla
git clone https://github.com/kullanici/crm-pro.git
cd crm-pro

# Uygulamayı başlat
python gui.py
```

---

## Dosya Yapısı

```
crm-pro/
│
├── musteri.py          # Veri modeli: Musteri, Satis, DestekTalebi sınıfları
├── veritabani.py       # JSON okuma/yazma ve sorgulama fonksiyonları
├── gui.py              # Tkinter arayüzü (CRMApp sınıfı ve tüm ekranlar)
│
├── musteriler.json     # Müşteri kayıtları (12 örnek kayıt)
├── satislar.json       # Satış kayıtları (24 örnek kayıt)
└── talepler.json       # Destek talebi kayıtları (16 örnek kayıt)
```

---

## Mimari

Proje 3 katmanlı bir mimari izler:

```
┌─────────────────────────────────────────────┐
│           gui.py  (CRMApp)                  │  ← Sunum Katmanı
│  Müşteri / Satış / Talep / Dashboard        │
└────────────────────┬────────────────────────┘
                     │ import
┌────────────────────▼────────────────────────┐
│           veritabani.py                     │  ← Veri Erişim Katmanı
│  yukle / kaydet / bul / sil / filtrele      │
└────────────────────┬────────────────────────┘
                     │ import
┌────────────────────▼────────────────────────┐
│           musteri.py                        │  ← Model Katmanı
│  Musteri  │  Satis  │  DestekTalebi         │
└──────────────────┬──┴──────────────────────┘
                   │ okuma/yazma
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
musteriler.json  satislar.json  talepler.json
```

---

## Kullanım

### Müşteri Yönetimi
Sol kenar çubuğundan **Müşteriler** sayfasına gidin. Arama çubuğu; ad, telefon ve e-postada eş zamanlı arama yapar. **Yeni** butonu ile müşteri ekleyin; kart üzerindeki **Detay** butonu ile o müşterinin tüm satış ve taleplerini görüntüleyin.

### Satış Takibi
**Satışlar** sayfasında tarihe veya tutara göre sıralama ve durum filtrelemesi yapabilirsiniz. Toplam ciro özet şeridinde anlık olarak görüntülenir.

### Destek Talepleri
**Talepler** sayfasında öncelik ve durum çift filtresi uygulanabilir. Talep kartındaki **Çöz** butonu ile çözüm metni girerek talebi kapatabilirsiniz.

### Dashboard
**Dashboard** sayfası 6 istatistik kartı, aylık ciro çubuk grafiği (saf Canvas ile çizilir, matplotlib gerekmez), en çok harcayan müşteri listesi ve şehir dağılımını gösterir.

### CSV Dışa Aktarma
Üst banner'daki **CSV Dışa Aktar** butonu ile müşteri, satış ve talep verilerinin tamamını tek bir dosyaya kaydedebilirsiniz.

### Tema Değiştirme
Üst banner'daki tema butonu ile Aydınlık ↔ Karanlık mod arasında geçiş yapılır.

---

## Veri Yapısı

### musteriler.json

```json
{
  "musteri_id": 1,
  "ad": "Ahmet Yılmaz",
  "telefon": "0532 111 2233",
  "email": "ahmet.yilmaz@gmail.com",
  "sehir": "İstanbul"
}
```

> `satislar` ve `talepler` listeleri JSON'da saklanmaz; uygulama başlarken `_iliskileri_bagla()` ile bellekte oluşturulur.

### satislar.json

```json
{
  "satis_id": 1,
  "urun": "Laptop Pro 15\"",
  "fiyat": 18500.0,
  "adet": 1,
  "musteri_id": 1,
  "notlar": "Hızlı teslimat istedi",
  "durum": "Tamamlandı",
  "tarih": "05.01.2025 09:15"
}
```

### talepler.json

```json
{
  "talep_id": 1,
  "aciklama": "Laptop ekranında dikey çizgiler...",
  "oncelik": "Yüksek",
  "musteri_id": 1,
  "kategori": "Teknik",
  "durum": "Açık",
  "cozum": "",
  "tarih": "10.01.2025 10:00"
}
```

---

## Durum ve Öncelik Değerleri

| Model | Alan | Geçerli Değerler |
|---|---|---|
| Satis | durum | `Beklemede` \| `Tamamlandı` \| `İptal` |
| DestekTalebi | durum | `Açık` \| `İşlemde` \| `Çözüldü` \| `Kapatıldı` |
| DestekTalebi | oncelik | `Düşük` \| `Orta` \| `Yüksek` \| `Acil` |
| DestekTalebi | kategori | `Teknik` \| `Fatura` \| `Teslimat` \| `Genel` |

---

## Geliştirme Önerileri

- **SQLite entegrasyonu** — JSON yerine `sqlite3` ile daha güvenilir depolama
- **Raporlama** — `matplotlib` ile pasta/çizgi grafik desteği
- **E-posta bildirimleri** — `smtplib` ile acil taleplerde otomatik bildirim
- **Kullanıcı yönetimi** — Rol tabanlı erişim (admin / satış temsilcisi)
- **Veri doğrulama** — Telefon ve e-posta için regex kontrolü
- **Arama geçmişi** — Son aramaların hatırlanması
