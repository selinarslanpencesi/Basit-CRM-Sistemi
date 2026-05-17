"""
Proje 10: Basit CRM Sistemi
Sınıflar: Musteri, Satis, DestekTalebi
"""


class Musteri:
    """Müşteri bilgilerini ve işlemlerini yöneten sınıf."""

    _id_sayaci = 1

    def __init__(self, ad, telefon, email="", sehir="", musteri_id=None):
        if musteri_id:
            self.musteri_id = musteri_id
        else:
            self.musteri_id = Musteri._id_sayaci
            Musteri._id_sayaci += 1

        self.ad       = ad
        self.telefon  = telefon
        self.email    = email
        self.sehir    = sehir
        self.satislar = []          # Satis nesnelerinin listesi
        self.talepler = []          # DestekTalebi nesnelerinin listesi

    # ── Yardımcı metodlar ────────────────────────────────────────────────────

    def musteri_ekle_satis(self, satis):
        """Müşteriye bir satış kaydı bağlar."""
        self.satislar.append(satis)

    def musteri_ekle_talep(self, talep):
        """Müşteriye bir destek talebi bağlar."""
        self.talepler.append(talep)

    def toplam_harcama(self):
        """Müşterinin tüm satışlardaki toplam harcamasını döndürür."""
        return sum(s.fiyat * s.adet for s in self.satislar)

    def acik_talepler(self):
        """Müşterinin açık destek taleplerini döndürür."""
        return [t for t in self.talepler if t.durum == "Açık"]

    def bilgi_goster(self):
        bilgi  = f"[ID: {self.musteri_id}] {self.ad}\n"
        bilgi += f"  📞 {self.telefon}  |  ✉️  {self.email}  |  📍 {self.sehir}\n"
        bilgi += f"  Toplam Harcama: {self.toplam_harcama():.2f} ₺"
        bilgi += f"  |  Satış: {len(self.satislar)}  |  Açık Talep: {len(self.acik_talepler())}"
        return bilgi

    # ── Serileştirme ─────────────────────────────────────────────────────────

    def to_dict(self):
        return {
            "musteri_id": self.musteri_id,
            "ad":         self.ad,
            "telefon":    self.telefon,
            "email":      self.email,
            "sehir":      self.sehir,
        }

    @staticmethod
    def from_dict(veri):
        m = Musteri(
            ad         = veri["ad"],
            telefon    = veri["telefon"],
            email      = veri.get("email", ""),
            sehir      = veri.get("sehir", ""),
            musteri_id = veri["musteri_id"],
        )
        if veri["musteri_id"] >= Musteri._id_sayaci:
            Musteri._id_sayaci = veri["musteri_id"] + 1
        return m


# ─────────────────────────────────────────────────────────────────────────────

class Satis:
    """Bir ürün satışını temsil eden sınıf."""

    _id_sayaci = 1
    DURUMLAR = ["Beklemede", "Tamamlandı", "İptal"]

    def __init__(self, urun, fiyat, adet=1, musteri_id=None, notlar="", durum="Tamamlandı", satis_id=None, tarih=""):
        if satis_id:
            self.satis_id = satis_id
        else:
            self.satis_id = Satis._id_sayaci
            Satis._id_sayaci += 1

        self.urun       = urun
        self.fiyat      = float(fiyat)
        self.adet       = int(adet)
        self.musteri_id = musteri_id
        self.notlar     = notlar
        self.durum      = durum
        self.tarih      = tarih

    def toplam_tutar(self):
        return self.fiyat * self.adet

    def durum_guncelle(self, yeni_durum):
        if yeni_durum not in Satis.DURUMLAR:
            raise ValueError(f"Geçersiz durum. Seçenekler: {Satis.DURUMLAR}")
        self.durum = yeni_durum

    def bilgi_goster(self):
        return (
            f"[SatışID: {self.satis_id}] {self.urun} — "
            f"{self.adet} adet × {self.fiyat:.2f} ₺ = {self.toplam_tutar():.2f} ₺  [{self.durum}]"
        )

    def to_dict(self):
        return {
            "satis_id":   self.satis_id,
            "urun":       self.urun,
            "fiyat":      self.fiyat,
            "adet":       self.adet,
            "musteri_id": self.musteri_id,
            "notlar":     self.notlar,
            "durum":      self.durum,
            "tarih":      self.tarih,
        }

    @staticmethod
    def from_dict(veri):
        s = Satis(
            urun       = veri["urun"],
            fiyat      = veri["fiyat"],
            adet       = veri.get("adet", 1),
            musteri_id = veri.get("musteri_id"),
            notlar     = veri.get("notlar", ""),
            durum      = veri.get("durum", "Tamamlandı"),
            satis_id   = veri["satis_id"],
            tarih      = veri.get("tarih", ""),
        )
        if veri["satis_id"] >= Satis._id_sayaci:
            Satis._id_sayaci = veri["satis_id"] + 1
        return s


# ─────────────────────────────────────────────────────────────────────────────

class DestekTalebi:
    """Müşteri destek taleplerini yöneten sınıf."""

    _id_sayaci = 1
    ONCELIKLER = ["Düşük", "Orta", "Yüksek", "Acil"]
    DURUMLAR   = ["Açık", "İşlemde", "Çözüldü", "Kapatıldı"]

    def __init__(self, aciklama, oncelik="Orta", musteri_id=None, kategori="Genel",
                 talep_id=None, durum="Açık", cozum="", tarih=""):
        if talep_id:
            self.talep_id = talep_id
        else:
            self.talep_id = DestekTalebi._id_sayaci
            DestekTalebi._id_sayaci += 1

        self.aciklama   = aciklama
        self.oncelik    = oncelik
        self.musteri_id = musteri_id
        self.kategori   = kategori
        self.durum      = durum
        self.cozum      = cozum
        self.tarih      = tarih

    def talebi_coz(self, cozum_metni):
        """Talebi çözülmüş olarak işaretler."""
        self.cozum = cozum_metni
        self.durum = "Çözüldü"

    def durum_guncelle(self, yeni_durum):
        if yeni_durum not in DestekTalebi.DURUMLAR:
            raise ValueError(f"Geçersiz durum. Seçenekler: {DestekTalebi.DURUMLAR}")
        self.durum = yeni_durum

    def bilgi_goster(self):
        return (
            f"[TalepID: {self.talep_id}] [{self.oncelik}] {self.aciklama[:60]}"
            f"  — Durum: {self.durum}  |  Kategori: {self.kategori}"
        )

    def to_dict(self):
        return {
            "talep_id":   self.talep_id,
            "aciklama":   self.aciklama,
            "oncelik":    self.oncelik,
            "musteri_id": self.musteri_id,
            "kategori":   self.kategori,
            "durum":      self.durum,
            "cozum":      self.cozum,
            "tarih":      self.tarih,
        }

    @staticmethod
    def from_dict(veri):
        t = DestekTalebi(
            aciklama   = veri["aciklama"],
            oncelik    = veri.get("oncelik", "Orta"),
            musteri_id = veri.get("musteri_id"),
            kategori   = veri.get("kategori", "Genel"),
            talep_id   = veri["talep_id"],
            durum      = veri.get("durum", "Açık"),
            cozum      = veri.get("cozum", ""),
            tarih      = veri.get("tarih", ""),
        )
        if veri["talep_id"] >= DestekTalebi._id_sayaci:
            DestekTalebi._id_sayaci = veri["talep_id"] + 1
        return t
