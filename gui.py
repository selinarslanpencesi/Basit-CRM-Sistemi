"""
gui.py — CRM Sistemi Gelişmiş Grafik Arayüzü (Tkinter)
Müşteri, Satış ve Destek Talebi yönetimi.

YENİLİKLER:
 - Dashboard: aylık ciro çubuk grafiği (Canvas ile), şehir bazlı dağılım
 - Satış sayfasında toplam ciro özet şeridi + sıralama/filtre
 - Talep sayfasında gelişmiş filtre (öncelik + durum)
 - Müşteri kartında "Detay" penceresi (tüm satış + talepler tek ekranda)
 - Sağ alt köşe durum çubuğu
 - Veri dışa aktarma (CSV)
 - Karanlık/Aydınlık mod geçişi
 - Not alanı müşteriye eklendi
 - Satis notlar alanı gösterime eklendi
 - Sidebar'da aktif sekme vurgulama
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys, csv
from datetime import datetime
from collections import defaultdict

_KLASOR = os.path.dirname(os.path.abspath(__file__))
if _KLASOR not in sys.path:
    sys.path.insert(0, _KLASOR)

from musteri import Musteri, Satis, DestekTalebi
from veritabani import (
    musterileri_kaydet, musterileri_yukle, musteri_bul, musteri_sil, musteri_ara,
    satislari_kaydet,   satislari_yukle,   satis_bul,   satis_sil,   musterinin_satislari,
    talepleri_kaydet,   talepleri_yukle,   talep_bul,   talep_sil,   musterinin_talepleri,
    acik_talepler,
)

# ── TEMA SİSTEMİ ─────────────────────────────────────────────────────────────

TEMALAR = {
    "light": {
        "BG_ANA":     "#F0F4F8",
        "BG_SIDEBAR": "#1B2B3A",
        "BG_KART":    "#FFFFFF",
        "BG_GIRDI":   "#E8F0FE",
        "GRI_CIZGI":  "#CBD5E1",
        "YAZI_ANA":   "#1E293B",
        "YAZI_ACIK":  "#64748B",
        "YAZI_BEYAZ": "#FFFFFF",
        "BANNER":     "#2563EB",
        "BANNER2":    "#1D4ED8",
    },
    "dark": {
        "BG_ANA":     "#0F172A",
        "BG_SIDEBAR": "#0A1628",
        "BG_KART":    "#1E293B",
        "BG_GIRDI":   "#1E293B",
        "GRI_CIZGI":  "#334155",
        "YAZI_ANA":   "#F1F5F9",
        "YAZI_ACIK":  "#94A3B8",
        "YAZI_BEYAZ": "#FFFFFF",
        "BANNER":     "#1D4ED8",
        "BANNER2":    "#1E40AF",
    },
}

MAVİ    = "#2563EB"
MAVİ_HOV= "#1D4ED8"
YESIL   = "#16A34A"
YESIL_HOV="#15803D"
KIRMIZI = "#DC2626"
TURUNCU = "#EA580C"
ACCENT  = "#7C3AED"

ONCELIK_RENK = {"Düşük": "#22C55E", "Orta": "#F59E0B", "Yüksek": "#EF4444", "Acil": "#7C3AED"}
DURUM_RENK   = {"Açık": "#EF4444", "İşlemde": "#F59E0B", "Çözüldü": "#22C55E", "Kapatıldı": "#64748B"}
SATIS_RENK   = {"Beklemede": "#F59E0B", "Tamamlandı": "#22C55E", "İptal": "#EF4444"}
GRAFIK_RENKLER = ["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6","#EC4899","#06B6D4","#84CC16","#F97316","#6366F1","#14B8A6","#FB923C"]

FONT_BASLIK = ("Segoe UI", 15, "bold")
FONT_ALT    = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_KUCUK  = ("Segoe UI", 9)

aktif_tema = "light"

def T(anahtar):
    return TEMALAR[aktif_tema].get(anahtar, "#000000")

def _buton(parent, text, command, bg=None, fg=None, width=None, font_size=10):
    if bg is None: bg = MAVİ
    if fg is None: fg = T("YAZI_BEYAZ")
    kw = dict(
        text=text, command=command,
        bg=bg, fg=fg, relief="flat", cursor="hand2",
        font=("Segoe UI", font_size, "bold"),
        padx=12, pady=6, bd=0,
        activebackground=MAVİ_HOV, activeforeground=fg,
    )
    if width: kw["width"] = width
    b = tk.Button(parent, **kw)
    hov = MAVİ_HOV if bg == MAVİ else bg
    b.bind("<Enter>", lambda e: b.config(bg=hov))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def _ayirici(parent, renk=None, pady=4):
    if renk is None: renk = T("GRI_CIZGI")
    tk.Frame(parent, bg=renk, height=1).pack(fill="x", pady=pady)

def _tarih():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


# ─────────────────────────────────────────────────────────────────────────────
# ANA UYGULAMA
# ─────────────────────────────────────────────────────────────────────────────

class CRMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💼 CRM Pro — Müşteri Yönetimi")
        self.root.geometry("1280x760")
        self.root.configure(bg=T("BG_ANA"))
        self.root.resizable(True, True)
        self.root.minsize(1000, 620)

        self.musteriler = musterileri_yukle()
        self.satislar   = satislari_yukle()
        self.talepler   = talepleri_yukle()
        self._iliskileri_bagla()

        self.aktif_sayfa = "musteriler"
        self._sidebar_butonlar = {}
        self._arayuz_kur()
        self.musteri_listesi_goster()

    def _iliskileri_bagla(self):
        musteri_map = {m.musteri_id: m for m in self.musteriler}
        for s in self.satislar:
            m = musteri_map.get(s.musteri_id)
            if m and s not in m.satislar:
                m.satislar.append(s)
        for t in self.talepler:
            m = musteri_map.get(t.musteri_id)
            if m and t not in m.talepler:
                m.talepler.append(t)

    # ─── LAYOUT ──────────────────────────────────────────────────────────────

    def _arayuz_kur(self):
        # BANNER
        self.banner = tk.Frame(self.root, bg=T("BANNER"), height=56)
        self.banner.pack(fill="x", side="top")
        self.banner.pack_propagate(False)

        tk.Label(self.banner, text="💼", font=("Segoe UI", 20), bg=T("BANNER"), fg=T("YAZI_BEYAZ")).pack(side="left", padx=(16, 4))
        tk.Label(self.banner, text="CRM Pro", font=("Segoe UI", 18, "bold"), bg=T("BANNER"), fg=T("YAZI_BEYAZ")).pack(side="left")
        tk.Label(self.banner, text="Müşteri İlişkileri Yönetimi", font=("Segoe UI", 10, "italic"), bg=T("BANNER"), fg="#BFDBFE").pack(side="left", padx=12)

        # Tema değiştir
        tk.Button(self.banner, text="🌙 Karanlık Mod" if aktif_tema=="light" else "☀️ Aydınlık Mod",
                  font=("Segoe UI", 9), bg=T("BANNER2"), fg=T("YAZI_BEYAZ"),
                  relief="flat", cursor="hand2", padx=10, pady=4, bd=0,
                  command=self._tema_degistir).pack(side="right", padx=8)

        # CSV Dışa Aktar
        tk.Button(self.banner, text="📥 CSV Dışa Aktar",
                  font=("Segoe UI", 9), bg=T("BANNER2"), fg=T("YAZI_BEYAZ"),
                  relief="flat", cursor="hand2", padx=10, pady=4, bd=0,
                  command=self._csv_aktar).pack(side="right", padx=4)

        self.banner_ozet = tk.Frame(self.banner, bg=T("BANNER"))
        self.banner_ozet.pack(side="right", padx=8)
        self._banner_ozet_guncelle()

        # GÖVDE
        govde = tk.Frame(self.root, bg=T("BG_ANA"))
        govde.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(govde, bg=T("BG_SIDEBAR"), width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._sidebar_kur()

        # İçerik
        self.icerik_cerceve = tk.Frame(govde, bg=T("BG_ANA"))
        self.icerik_cerceve.pack(side="left", fill="both", expand=True)
        self._arama_kur()

        self.canvas = tk.Canvas(self.icerik_cerceve, bg=T("BG_ANA"), highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.icerik_cerceve, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.icerik = tk.Frame(self.canvas, bg=T("BG_ANA"))
        self._canvas_pencere = self.canvas.create_window((0, 0), window=self.icerik, anchor="nw")
        self.icerik.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._canvas_pencere, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Durum çubuğu
        self.durum_cubugu = tk.Label(self.root, text="Hazır  |  CRM Pro v2.0",
                                     font=("Segoe UI", 8), bg=T("BG_SIDEBAR"),
                                     fg=T("YAZI_ACIK"), anchor="w", padx=10)
        self.durum_cubugu.pack(side="bottom", fill="x")

    def _durum_guncelle(self, mesaj):
        self.durum_cubugu.config(text=f"{mesaj}  |  {_tarih()}")

    def _tema_degistir(self):
        global aktif_tema
        aktif_tema = "dark" if aktif_tema == "light" else "light"
        # Pencereyi yeniden başlat
        for w in self.root.winfo_children():
            w.destroy()
        self._sidebar_butonlar = {}
        self._arayuz_kur()
        self._sayfa_goster(self.aktif_sayfa)

    def _sayfa_goster(self, sayfa):
        if sayfa == "musteriler":   self._sayfa_musteriler()
        elif sayfa == "satislar":   self._sayfa_satislar()
        elif sayfa == "talepler":   self._sayfa_talepler()
        elif sayfa == "dashboard":  self._sayfa_dashboard()

    def _banner_ozet_guncelle(self):
        for w in self.banner_ozet.winfo_children():
            w.destroy()
        toplam_ciro = sum(s.toplam_tutar() for s in self.satislar if s.durum == "Tamamlandı")
        acik = len(acik_talepler(self.talepler))
        for ikon, deger, etiket in [
            ("👥", len(self.musteriler), "Müşteri"),
            ("💰", f"{toplam_ciro:,.0f}₺", "Ciro"),
            ("🎫", acik, "Açık Talep"),
        ]:
            f = tk.Frame(self.banner_ozet, bg=T("BANNER2"), padx=14, pady=4)
            f.pack(side="left", padx=4)
            tk.Label(f, text=f"{ikon} {deger}", font=("Segoe UI", 11, "bold"), bg=T("BANNER2"), fg=T("YAZI_BEYAZ")).pack()
            tk.Label(f, text=etiket, font=("Segoe UI", 8), bg=T("BANNER2"), fg="#BFDBFE").pack()

    def _sidebar_kur(self):
        tk.Label(self.sidebar, text="MENÜ", font=("Segoe UI", 8, "bold"),
                 bg=T("BG_SIDEBAR"), fg="#64748B").pack(pady=(20, 6), padx=16, anchor="w")

        self._sidebar_butonlar = {}
        for metin, sayfa, komut in [
            ("👥  Müşteriler",  "musteriler",  self._sayfa_musteriler),
            ("💰  Satışlar",    "satislar",    self._sayfa_satislar),
            ("🎫  Destek",      "talepler",    self._sayfa_talepler),
            ("📊  Dashboard",   "dashboard",   self._sayfa_dashboard),
        ]:
            b = tk.Button(
                self.sidebar, text=f"  {metin}",
                font=("Segoe UI", 10), bg=T("BG_SIDEBAR"), fg="#CBD5E1",
                relief="flat", anchor="w", cursor="hand2",
                activebackground="#253447", activeforeground=T("YAZI_BEYAZ"),
                padx=10, pady=9, bd=0, command=komut,
            )
            b.pack(fill="x", padx=6, pady=1)
            self._sidebar_butonlar[sayfa] = b

        _ayirici(self.sidebar, renk="#2E3F50", pady=10)
        tk.Label(self.sidebar, text="İŞLEMLER", font=("Segoe UI", 8, "bold"),
                 bg=T("BG_SIDEBAR"), fg="#64748B").pack(pady=(4, 6), padx=16, anchor="w")

        for metin, renk, komut in [
            ("  ➕  Yeni Müşteri", MAVİ,   self._yeni_musteri_ekrani),
            ("  🛒  Yeni Satış",   YESIL,  self._yeni_satis_ekrani),
            ("  🎫  Yeni Talep",   ACCENT, self._yeni_talep_ekrani),
        ]:
            tk.Button(self.sidebar, text=metin, font=("Segoe UI", 10),
                      bg=renk, fg=T("YAZI_BEYAZ"), relief="flat", anchor="w",
                      cursor="hand2", padx=10, pady=9, bd=0,
                      command=komut).pack(fill="x", padx=6, pady=2)

        # Sidebar alt bilgi
        tk.Label(self.sidebar, text=f"v2.0 — {datetime.now().strftime('%d.%m.%Y')}",
                 font=("Segoe UI", 8), bg=T("BG_SIDEBAR"), fg="#475569").pack(side="bottom", pady=8)

    def _sidebar_aktif_goster(self, sayfa):
        for s, b in self._sidebar_butonlar.items():
            if s == sayfa:
                b.config(bg="#253447", fg=T("YAZI_BEYAZ"))
            else:
                b.config(bg=T("BG_SIDEBAR"), fg="#CBD5E1")

    def _arama_kur(self):
        arama_f = tk.Frame(self.icerik_cerceve, bg=T("BG_ANA"), padx=16, pady=10)
        arama_f.pack(fill="x")
        tk.Label(arama_f, text="🔍", font=("Segoe UI", 12), bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(side="left", padx=(0, 6))
        self.arama_var = tk.StringVar()
        self.arama_var.trace("w", lambda *_: self._arama_uygula())
        self.arama_entry = tk.Entry(arama_f, textvariable=self.arama_var, font=("Segoe UI", 11),
                 bg=T("BG_GIRDI"), relief="flat", fg=T("YAZI_ANA"))
        self.arama_entry.pack(side="left", fill="x", expand=True, ipady=6)
        tk.Label(arama_f, text="ESC: Temizle", font=("Segoe UI", 8),
                 bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(side="left", padx=6)
        self.root.bind("<Escape>", lambda e: self.arama_var.set(""))

    # ─── NAVİGASYON ──────────────────────────────────────────────────────────

    def _sayfa_musteriler(self):
        self.aktif_sayfa = "musteriler"
        self._sidebar_aktif_goster("musteriler")
        self.musteri_listesi_goster()

    def _sayfa_satislar(self):
        self.aktif_sayfa = "satislar"
        self._sidebar_aktif_goster("satislar")
        self.satis_listesi_goster()

    def _sayfa_talepler(self):
        self.aktif_sayfa = "talepler"
        self._sidebar_aktif_goster("talepler")
        self.talep_listesi_goster()

    def _sayfa_dashboard(self):
        self.aktif_sayfa = "dashboard"
        self._sidebar_aktif_goster("dashboard")
        self.dashboard_goster()

    def _arama_uygula(self, *_):
        if self.aktif_sayfa == "musteriler":
            self.musteri_listesi_goster(arama=self.arama_var.get())

    # ─── CSV AKTAR ───────────────────────────────────────────────────────────

    def _csv_aktar(self):
        dosya = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyası", "*.csv")],
            title="Müşteri Listesini Dışa Aktar",
            initialfile="musteriler_export.csv",
        )
        if not dosya:
            return
        try:
            with open(dosya, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["ID", "Ad Soyad", "Telefon", "E-posta", "Şehir",
                             "Satış Sayısı", "Toplam Ciro (₺)", "Açık Talep"])
                for m in self.musteriler:
                    satislar_m = musterinin_satislari(self.satislar, m.musteri_id)
                    ciro = sum(s.toplam_tutar() for s in satislar_m if s.durum == "Tamamlandı")
                    acik = len([t for t in musterinin_talepleri(self.talepler, m.musteri_id) if t.durum in ("Açık","İşlemde")])
                    w.writerow([m.musteri_id, m.ad, m.telefon, m.email, m.sehir,
                                len(satislar_m), f"{ciro:.2f}", acik])
            messagebox.showinfo("✅ Başarılı", f"CSV dışa aktarıldı:\n{dosya}")
            self._durum_guncelle(f"CSV aktarıldı → {os.path.basename(dosya)}")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # ─── MÜŞTERİ SAYFASI ─────────────────────────────────────────────────────

    def musteri_listesi_goster(self, arama=""):
        for w in self.icerik.winfo_children():
            w.destroy()

        liste = musteri_ara(self.musteriler, arama) if arama else self.musteriler

        baslik_f = tk.Frame(self.icerik, bg=T("BG_ANA"), padx=16, pady=8)
        baslik_f.pack(fill="x")
        tk.Label(baslik_f, text=f"👥 Müşteriler  ({len(liste)})",
                 font=FONT_BASLIK, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(side="left")

        # Şehir filtresi
        sehirler = sorted(set(m.sehir for m in self.musteriler if m.sehir))
        self._musteri_sehir_var = tk.StringVar(value="Tümü")
        f_f = tk.Frame(baslik_f, bg=T("BG_ANA"))
        f_f.pack(side="right")
        tk.Label(f_f, text="Şehir:", font=FONT_KUCUK, bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(side="left")
        ttk.Combobox(f_f, textvariable=self._musteri_sehir_var,
                     values=["Tümü"] + sehirler, state="readonly", width=12,
                     font=FONT_KUCUK).pack(side="left", padx=4)
        _buton(f_f, "Filtrele",
               lambda: self.musteri_listesi_goster(arama=self.arama_var.get()),
               bg=MAVİ, font_size=9).pack(side="left")

        secili_sehir = self._musteri_sehir_var.get()
        if secili_sehir != "Tümü":
            liste = [m for m in liste if m.sehir == secili_sehir]

        if not liste:
            tk.Label(self.icerik, text="Sonuç bulunamadı.",
                     font=FONT_NORMAL, bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(pady=40)
            return

        self._durum_guncelle(f"{len(liste)} müşteri listeleniyor")
        for m in liste:
            self._musteri_karti(m)

    def _musteri_karti(self, m):
        kart = tk.Frame(self.icerik, bg=T("BG_KART"), padx=16, pady=12,
                        highlightbackground=T("GRI_CIZGI"), highlightthickness=1)
        kart.pack(fill="x", padx=16, pady=5)

        ust = tk.Frame(kart, bg=T("BG_KART"))
        ust.pack(fill="x")

        # Avatar
        renkler_av = [MAVİ, YESIL, ACCENT, TURUNCU, "#0891B2", "#7C3AED"]
        av_renk = renkler_av[m.musteri_id % len(renkler_av)]
        tk.Label(ust, text=m.ad[0].upper(), font=("Segoe UI", 14, "bold"),
                 bg=av_renk, fg=T("YAZI_BEYAZ"), width=3, pady=4).pack(side="left", padx=(0, 12))

        bilgi_f = tk.Frame(ust, bg=T("BG_KART"))
        bilgi_f.pack(side="left", fill="x", expand=True)
        tk.Label(bilgi_f, text=m.ad, font=("Segoe UI", 12, "bold"),
                 bg=T("BG_KART"), fg=T("YAZI_ANA")).pack(anchor="w")
        alt = f"📞 {m.telefon}"
        if m.email: alt += f"   ✉️  {m.email}"
        if m.sehir: alt += f"   📍 {m.sehir}"
        tk.Label(bilgi_f, text=alt, font=FONT_KUCUK, bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(anchor="w")

        sag = tk.Frame(ust, bg=T("BG_KART"))
        sag.pack(side="right")

        satislar_m = musterinin_satislari(self.satislar, m.musteri_id)
        talepler_m = musterinin_talepleri(self.talepler, m.musteri_id)
        toplam = sum(s.toplam_tutar() for s in satislar_m if s.durum == "Tamamlandı")

        for etiket, deger, renk in [
            ("Satış", len(satislar_m), MAVİ),
            ("Ciro",  f"{toplam:,.0f}₺", YESIL),
            ("Talep", len(talepler_m), ACCENT),
        ]:
            chip = tk.Frame(sag, bg=renk, padx=8, pady=3)
            chip.pack(side="left", padx=3)
            tk.Label(chip, text=str(deger), font=("Segoe UI", 10, "bold"),
                     bg=renk, fg=T("YAZI_BEYAZ")).pack()
            tk.Label(chip, text=etiket, font=("Segoe UI", 7),
                     bg=renk, fg=T("YAZI_BEYAZ")).pack()

        btn_f = tk.Frame(kart, bg=T("BG_KART"))
        btn_f.pack(fill="x", pady=(8, 0))
        _buton(btn_f, "📋 Detay",      lambda mid=m.musteri_id: self._musteri_detay(mid),       bg="#0891B2", font_size=9).pack(side="left", padx=(0, 4))
        _buton(btn_f, "✏️ Düzenle",   lambda mid=m.musteri_id: self._musteri_duzenle(mid),     bg=MAVİ,     font_size=9).pack(side="left", padx=4)
        _buton(btn_f, "🛒 Satış Ekle",lambda mid=m.musteri_id: self._yeni_satis_ekrani(mid),   bg=YESIL,    font_size=9).pack(side="left", padx=4)
        _buton(btn_f, "🎫 Talep Ekle",lambda mid=m.musteri_id: self._yeni_talep_ekrani(mid),   bg=ACCENT,   font_size=9).pack(side="left", padx=4)
        _buton(btn_f, "🗑 Sil",        lambda mid=m.musteri_id: self._musteri_sil(mid),         bg="#FEE2E2", fg=KIRMIZI, font_size=9).pack(side="right")

    def _musteri_detay(self, musteri_id):
        """Müşteriye ait tüm satış ve talepleri tek pencerede göster."""
        m = musteri_bul(self.musteriler, musteri_id)
        if not m: return

        pen = tk.Toplevel(self.root)
        pen.title(f"Müşteri Detayı — {m.ad}")
        pen.geometry("680x560")
        pen.configure(bg=T("BG_ANA"))
        pen.grab_set()

        # Başlık
        bant = tk.Frame(pen, bg=MAVİ, pady=14)
        bant.pack(fill="x")
        tk.Label(bant, text=f"📋 {m.ad}", font=FONT_BASLIK, bg=MAVİ, fg=T("YAZI_BEYAZ")).pack()
        tk.Label(bant, text=f"📞 {m.telefon}  |  ✉️  {m.email}  |  📍 {m.sehir}",
                 font=FONT_KUCUK, bg=MAVİ, fg="#BFDBFE").pack()

        nb = ttk.Notebook(pen)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        # Satışlar sekmesi
        sat_f = tk.Frame(nb, bg=T("BG_ANA"))
        nb.add(sat_f, text=f"🛒 Satışlar ({len(musterinin_satislari(self.satislar, musteri_id))})")

        s_canvas = tk.Canvas(sat_f, bg=T("BG_ANA"), highlightthickness=0)
        s_sb = ttk.Scrollbar(sat_f, orient="vertical", command=s_canvas.yview)
        s_canvas.configure(yscrollcommand=s_sb.set)
        s_sb.pack(side="right", fill="y")
        s_canvas.pack(fill="both", expand=True)
        s_ic = tk.Frame(s_canvas, bg=T("BG_ANA"))
        s_cw = s_canvas.create_window((0, 0), window=s_ic, anchor="nw")
        s_ic.bind("<Configure>", lambda e: s_canvas.configure(scrollregion=s_canvas.bbox("all")))
        s_canvas.bind("<Configure>", lambda e: s_canvas.itemconfig(s_cw, width=e.width))

        satislar_m = musterinin_satislari(self.satislar, musteri_id)
        toplam_ciro = sum(s.toplam_tutar() for s in satislar_m if s.durum == "Tamamlandı")
        ozet_f = tk.Frame(s_ic, bg="#EFF6FF", padx=12, pady=8)
        ozet_f.pack(fill="x", padx=8, pady=6)
        tk.Label(ozet_f, text=f"Toplam Ciro: {toplam_ciro:,.2f} ₺  |  Satış Sayısı: {len(satislar_m)}",
                 font=FONT_ALT, bg="#EFF6FF", fg=MAVİ).pack(anchor="w")

        for s in satislar_m:
            r = SATIS_RENK.get(s.durum, T("GRI_CIZGI"))
            sf = tk.Frame(s_ic, bg=T("BG_KART"), padx=10, pady=8,
                          highlightbackground=r, highlightthickness=2)
            sf.pack(fill="x", padx=8, pady=3)
            ust2 = tk.Frame(sf, bg=T("BG_KART"))
            ust2.pack(fill="x")
            tk.Label(ust2, text=f" {s.durum} ", font=("Segoe UI", 8, "bold"),
                     bg=r, fg=T("YAZI_BEYAZ")).pack(side="left", padx=(0, 8))
            tk.Label(ust2, text=s.urun, font=FONT_ALT, bg=T("BG_KART"), fg=T("YAZI_ANA")).pack(side="left")
            tk.Label(ust2, text=f"{s.toplam_tutar():,.2f} ₺", font=FONT_ALT,
                     bg=T("BG_KART"), fg=YESIL).pack(side="right")
            alt2 = f"{s.adet} adet × {s.fiyat:.2f} ₺  |  {s.tarih}"
            if s.notlar: alt2 += f"  |  Not: {s.notlar}"
            tk.Label(sf, text=alt2, font=FONT_KUCUK, bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(anchor="w")

        if not satislar_m:
            tk.Label(s_ic, text="Satış kaydı yok.", font=FONT_NORMAL,
                     bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(pady=20)

        # Talepler sekmesi
        tal_f = tk.Frame(nb, bg=T("BG_ANA"))
        nb.add(tal_f, text=f"🎫 Talepler ({len(musterinin_talepleri(self.talepler, musteri_id))})")

        talepler_m = musterinin_talepleri(self.talepler, musteri_id)
        for t in talepler_m:
            or_ = ONCELIK_RENK.get(t.oncelik, T("GRI_CIZGI"))
            tf2 = tk.Frame(tal_f, bg=T("BG_KART"), padx=10, pady=8,
                           highlightbackground=or_, highlightthickness=2)
            tf2.pack(fill="x", padx=8, pady=3)
            ust3 = tk.Frame(tf2, bg=T("BG_KART"))
            ust3.pack(fill="x")
            tk.Label(ust3, text=f" {t.oncelik} ", font=("Segoe UI", 8, "bold"),
                     bg=or_, fg=T("YAZI_BEYAZ")).pack(side="left", padx=(0, 6))
            dr = DURUM_RENK.get(t.durum, T("GRI_CIZGI"))
            tk.Label(ust3, text=f" {t.durum} ", font=("Segoe UI", 8, "bold"),
                     bg=dr, fg=T("YAZI_BEYAZ")).pack(side="left")
            tk.Label(ust3, text=f" #{t.talep_id}", font=FONT_KUCUK,
                     bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(side="right")
            tk.Label(tf2, text=t.aciklama, font=FONT_KUCUK, bg=T("BG_KART"),
                     fg=T("YAZI_ANA"), wraplength=520, justify="left").pack(anchor="w", pady=2)
            if t.cozum:
                tk.Label(tf2, text=f"✅ {t.cozum}", font=FONT_KUCUK,
                         bg=T("BG_KART"), fg=YESIL).pack(anchor="w")

        if not talepler_m:
            tk.Label(tal_f, text="Talep kaydı yok.", font=FONT_NORMAL,
                     bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(pady=20)

    def _musteri_sil(self, musteri_id):
        m = musteri_bul(self.musteriler, musteri_id)
        if m and messagebox.askyesno("Sil", f"'{m.ad}' silinsin mi?"):
            musteri_sil(self.musteriler, musteri_id)
            musterileri_kaydet(self.musteriler)
            self._banner_ozet_guncelle()
            self._durum_guncelle(f"'{m.ad}' silindi")
            self.musteri_listesi_goster()

    # ─── MÜŞTERİ EKLE / DÜZENLE ──────────────────────────────────────────────

    def _yeni_musteri_ekrani(self, musteri=None):
        pencere = tk.Toplevel(self.root)
        pencere.title("Müşteri Ekle" if not musteri else "Müşteri Düzenle")
        pencere.geometry("420x440")
        pencere.configure(bg=T("BG_ANA"))
        pencere.grab_set()

        bant = tk.Frame(pencere, bg=MAVİ, pady=14)
        bant.pack(fill="x")
        tk.Label(bant, text="👤 " + ("Yeni Müşteri" if not musteri else "Müşteri Düzenle"),
                 font=FONT_BASLIK, bg=MAVİ, fg=T("YAZI_BEYAZ")).pack()

        ic = tk.Frame(pencere, bg=T("BG_ANA"), padx=28, pady=16)
        ic.pack(fill="both", expand=True)

        alanlar = {}
        for etiket, key, dolgu in [
            ("Ad Soyad *", "ad",      musteri.ad      if musteri else ""),
            ("Telefon *",  "telefon", musteri.telefon if musteri else ""),
            ("E-posta",    "email",   musteri.email   if musteri else ""),
            ("Şehir",      "sehir",   musteri.sehir   if musteri else ""),
        ]:
            tk.Label(ic, text=etiket, font=("Segoe UI", 9, "bold"),
                     bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(6, 0))
            var = tk.StringVar(value=dolgu)
            tk.Entry(ic, textvariable=var, font=FONT_NORMAL,
                     bg=T("BG_GIRDI"), relief="flat", fg=T("YAZI_ANA")).pack(fill="x", ipady=5)
            alanlar[key] = var

        def kaydet():
            ad      = alanlar["ad"].get().strip()
            telefon = alanlar["telefon"].get().strip()
            if not ad or not telefon:
                messagebox.showerror("Hata", "Ad ve telefon zorunludur!", parent=pencere)
                return
            if musteri:
                musteri.ad      = ad
                musteri.telefon = telefon
                musteri.email   = alanlar["email"].get().strip()
                musteri.sehir   = alanlar["sehir"].get().strip()
                messagebox.showinfo("✅", "Müşteri güncellendi!", parent=pencere)
                self._durum_guncelle(f"'{ad}' güncellendi")
            else:
                yeni = Musteri(ad, telefon, alanlar["email"].get().strip(), alanlar["sehir"].get().strip())
                self.musteriler.append(yeni)
                messagebox.showinfo("✅", f"'{ad}' eklendi!", parent=pencere)
                self._durum_guncelle(f"Yeni müşteri '{ad}' eklendi")
            musterileri_kaydet(self.musteriler)
            self._banner_ozet_guncelle()
            pencere.destroy()
            self.musteri_listesi_goster()

        _buton(ic, "💾 Kaydet", kaydet, font_size=11).pack(fill="x", pady=8)
        _buton(ic, "İptal", pencere.destroy, bg=T("GRI_CIZGI"), fg=T("YAZI_ANA")).pack(fill="x")

    def _musteri_duzenle(self, musteri_id):
        m = musteri_bul(self.musteriler, musteri_id)
        if m: self._yeni_musteri_ekrani(musteri=m)

    # ─── SATIŞ SAYFASI ───────────────────────────────────────────────────────

    def satis_listesi_goster(self):
        for w in self.icerik.winfo_children():
            w.destroy()

        baslik_f = tk.Frame(self.icerik, bg=T("BG_ANA"), padx=16, pady=8)
        baslik_f.pack(fill="x")
        tk.Label(baslik_f, text=f"💰 Satışlar  ({len(self.satislar)})",
                 font=FONT_BASLIK, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(side="left")

        # Durum filtresi
        f_f = tk.Frame(baslik_f, bg=T("BG_ANA"))
        f_f.pack(side="right")
        self._satis_filtre_var = getattr(self, "_satis_filtre_var", tk.StringVar(value="Tümü"))
        ttk.Combobox(f_f, textvariable=self._satis_filtre_var,
                     values=["Tümü"] + Satis.DURUMLAR, state="readonly",
                     width=12, font=FONT_KUCUK).pack(side="left", padx=4)
        _buton(f_f, "Filtrele", self.satis_listesi_goster, bg=YESIL, font_size=9).pack(side="left")

        # Özet şeridi
        toplam_ciro = sum(s.toplam_tutar() for s in self.satislar if s.durum == "Tamamlandı")
        bekleyen    = sum(s.toplam_tutar() for s in self.satislar if s.durum == "Beklemede")
        ozet = tk.Frame(self.icerik, bg="#F0FDF4", padx=16, pady=10)
        ozet.pack(fill="x", padx=16, pady=(0, 4))
        for etiket, deger, renk in [
            ("✅ Tamamlanan Ciro", f"{toplam_ciro:,.2f} ₺", YESIL),
            ("⏳ Bekleyen Tutar",  f"{bekleyen:,.2f} ₺",    TURUNCU),
            ("📦 Toplam Satış",   str(len(self.satislar)),  MAVİ),
        ]:
            ck = tk.Frame(ozet, bg=T("BG_KART"), padx=14, pady=8)
            ck.pack(side="left", padx=6)
            tk.Label(ck, text=deger, font=("Segoe UI", 13, "bold"), bg=T("BG_KART"), fg=renk).pack()
            tk.Label(ck, text=etiket, font=FONT_KUCUK, bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack()

        secili = self._satis_filtre_var.get()
        liste = self.satislar if secili == "Tümü" else [s for s in self.satislar if s.durum == secili]

        if not liste:
            tk.Label(self.icerik, text="Gösterilecek satış yok.",
                     font=FONT_NORMAL, bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(pady=40)
            return

        self._durum_guncelle(f"{len(liste)} satış listeleniyor")
        for s in liste:
            self._satis_karti(s)

    def _satis_karti(self, s):
        renk = SATIS_RENK.get(s.durum, T("GRI_CIZGI"))
        kart = tk.Frame(self.icerik, bg=T("BG_KART"), padx=16, pady=10,
                        highlightbackground=renk, highlightthickness=2)
        kart.pack(fill="x", padx=16, pady=4)

        ust = tk.Frame(kart, bg=T("BG_KART"))
        ust.pack(fill="x")
        tk.Label(ust, text=f" {s.durum} ", font=("Segoe UI", 9, "bold"),
                 bg=renk, fg=T("YAZI_BEYAZ"), padx=6, pady=2).pack(side="left", padx=(0, 10))
        tk.Label(ust, text=s.urun, font=("Segoe UI", 11, "bold"),
                 bg=T("BG_KART"), fg=T("YAZI_ANA")).pack(side="left")
        tk.Label(ust, text=f"{s.toplam_tutar():,.2f} ₺", font=("Segoe UI", 12, "bold"),
                 bg=T("BG_KART"), fg=YESIL).pack(side="right")

        m = musteri_bul(self.musteriler, s.musteri_id)
        alt_metin = f"👤 {m.ad if m else 'Bilinmiyor'}  |  {s.adet} adet × {s.fiyat:.2f}₺  |  📅 {s.tarih}"
        if s.notlar: alt_metin += f"  |  📝 {s.notlar}"
        tk.Label(kart, text=alt_metin, font=FONT_KUCUK, bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(anchor="w", pady=(4,0))

        btn_f = tk.Frame(kart, bg=T("BG_KART"))
        btn_f.pack(fill="x", pady=(6, 0))
        _buton(btn_f, "✏️ Durum Güncelle",
               lambda sid=s.satis_id: self._satis_durum_guncelle(sid),
               bg="#FEF3C7", fg="#92400E", font_size=9).pack(side="left", padx=(0, 4))
        _buton(btn_f, "🗑 Sil",
               lambda sid=s.satis_id: self._satis_sil(sid),
               bg="#FEE2E2", fg=KIRMIZI, font_size=9).pack(side="right")

    def _satis_sil(self, satis_id):
        s = satis_bul(self.satislar, satis_id)
        if s and messagebox.askyesno("Sil", f"'{s.urun}' satışı silinsin mi?"):
            m = musteri_bul(self.musteriler, s.musteri_id)
            if m and s in m.satislar: m.satislar.remove(s)
            satis_sil(self.satislar, satis_id)
            satislari_kaydet(self.satislar)
            self._banner_ozet_guncelle()
            self._durum_guncelle(f"'{s.urun}' satışı silindi")
            self.satis_listesi_goster()

    def _satis_durum_guncelle(self, satis_id):
        s = satis_bul(self.satislar, satis_id)
        if not s: return
        pencere = tk.Toplevel(self.root)
        pencere.title("Durum Güncelle")
        pencere.geometry("320x200")
        pencere.configure(bg=T("BG_ANA"))
        pencere.grab_set()
        tk.Label(pencere, text=f"Satış: {s.urun}", font=FONT_ALT, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(pady=(20,4))
        tk.Label(pencere, text="Yeni Durum:", font=FONT_NORMAL, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack()
        durum_var = tk.StringVar(value=s.durum)
        ttk.Combobox(pencere, textvariable=durum_var, values=Satis.DURUMLAR,
                     state="readonly", font=FONT_NORMAL).pack(pady=6, padx=24, fill="x")
        def kaydet():
            s.durum_guncelle(durum_var.get())
            satislari_kaydet(self.satislar)
            self._banner_ozet_guncelle()
            pencere.destroy()
            self.satis_listesi_goster()
        _buton(pencere, "Güncelle", kaydet).pack(pady=10)

    # ─── YENİ SATIŞ ──────────────────────────────────────────────────────────

    def _yeni_satis_ekrani(self, onceden_musteri_id=None):
        pencere = tk.Toplevel(self.root)
        pencere.title("Yeni Satış")
        pencere.geometry("420x460")
        pencere.configure(bg=T("BG_ANA"))
        pencere.grab_set()

        bant = tk.Frame(pencere, bg=YESIL, pady=14)
        bant.pack(fill="x")
        tk.Label(bant, text="🛒 Yeni Satış", font=FONT_BASLIK, bg=YESIL, fg=T("YAZI_BEYAZ")).pack()

        ic = tk.Frame(pencere, bg=T("BG_ANA"), padx=28, pady=14)
        ic.pack(fill="both", expand=True)

        tk.Label(ic, text="Müşteri *", font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(4,0))
        musteri_adlari = [f"{m.ad} (ID:{m.musteri_id})" for m in self.musteriler]
        if not musteri_adlari:
            messagebox.showwarning("Uyarı", "Önce müşteri ekleyin!", parent=pencere)
            pencere.destroy()
            return
        musteri_var = tk.StringVar()
        if onceden_musteri_id:
            mb = musteri_bul(self.musteriler, onceden_musteri_id)
            if mb: musteri_var.set(f"{mb.ad} (ID:{mb.musteri_id})")
        ttk.Combobox(ic, textvariable=musteri_var, values=musteri_adlari,
                     state="readonly", font=FONT_NORMAL).pack(fill="x", pady=4)

        alanlar = {}
        for etiket, key, dolgu in [
            ("Ürün Adı *",    "urun",  ""),
            ("Birim Fiyat *", "fiyat", ""),
            ("Adet",          "adet",  "1"),
            ("Notlar",        "notlar",""),
        ]:
            tk.Label(ic, text=etiket, font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(6,0))
            var = tk.StringVar(value=dolgu)
            tk.Entry(ic, textvariable=var, font=FONT_NORMAL, bg=T("BG_GIRDI"), relief="flat", fg=T("YAZI_ANA")).pack(fill="x", ipady=5)
            alanlar[key] = var

        tk.Label(ic, text="Durum", font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(6,0))
        durum_var = tk.StringVar(value="Tamamlandı")
        ttk.Combobox(ic, textvariable=durum_var, values=Satis.DURUMLAR,
                     state="readonly", font=FONT_NORMAL).pack(fill="x")

        def kaydet():
            ms = musteri_var.get()
            if not ms:
                messagebox.showerror("Hata", "Müşteri seçin!", parent=pencere)
                return
            mid = int(ms.split("ID:")[1].rstrip(")"))
            urun = alanlar["urun"].get().strip()
            if not urun:
                messagebox.showerror("Hata", "Ürün adı boş olamaz!", parent=pencere)
                return
            try:
                fiyat = float(alanlar["fiyat"].get())
                adet  = int(alanlar["adet"].get())
            except ValueError:
                messagebox.showerror("Hata", "Fiyat ve adet sayı olmalıdır!", parent=pencere)
                return
            yeni = Satis(urun, fiyat, adet, mid, notlar=alanlar["notlar"].get().strip(),
                         durum=durum_var.get(), tarih=_tarih())
            self.satislar.append(yeni)
            m = musteri_bul(self.musteriler, mid)
            if m: m.satislar.append(yeni)
            satislari_kaydet(self.satislar)
            self._banner_ozet_guncelle()
            self._durum_guncelle(f"Yeni satış '{urun}' eklendi")
            messagebox.showinfo("✅", "Satış eklendi!", parent=pencere)
            pencere.destroy()
            self.satis_listesi_goster()

        _buton(ic, "💾 Kaydet", kaydet, font_size=11).pack(fill="x", pady=8)
        _buton(ic, "İptal", pencere.destroy, bg=T("GRI_CIZGI"), fg=T("YAZI_ANA")).pack(fill="x")

    # ─── DESTEK TALEPLERİ ────────────────────────────────────────────────────

    def talep_listesi_goster(self):
        for w in self.icerik.winfo_children():
            w.destroy()

        baslik_f = tk.Frame(self.icerik, bg=T("BG_ANA"), padx=16, pady=8)
        baslik_f.pack(fill="x")
        tk.Label(baslik_f, text=f"🎫 Destek Talepleri  ({len(self.talepler)})",
                 font=FONT_BASLIK, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(side="left")

        ff = tk.Frame(baslik_f, bg=T("BG_ANA"))
        ff.pack(side="right")

        self.talep_filtre_var    = getattr(self, "talep_filtre_var",    tk.StringVar(value="Tümü"))
        self.talep_oncelik_var   = getattr(self, "talep_oncelik_var",   tk.StringVar(value="Tümü"))

        tk.Label(ff, text="Durum:", font=FONT_KUCUK, bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(side="left")
        ttk.Combobox(ff, textvariable=self.talep_filtre_var,
                     values=["Tümü"] + DestekTalebi.DURUMLAR, state="readonly",
                     width=10, font=FONT_KUCUK).pack(side="left", padx=4)
        tk.Label(ff, text="Öncelik:", font=FONT_KUCUK, bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(side="left")
        ttk.Combobox(ff, textvariable=self.talep_oncelik_var,
                     values=["Tümü"] + DestekTalebi.ONCELIKLER, state="readonly",
                     width=10, font=FONT_KUCUK).pack(side="left", padx=4)
        _buton(ff, "Filtrele", self.talep_listesi_goster, bg=ACCENT, font_size=9).pack(side="left")

        secili_d = self.talep_filtre_var.get()
        secili_o = self.talep_oncelik_var.get()
        liste = [t for t in self.talepler
                 if (secili_d == "Tümü" or t.durum == secili_d)
                 and (secili_o == "Tümü" or t.oncelik == secili_o)]

        if not liste:
            tk.Label(self.icerik, text="Gösterilecek talep yok.",
                     font=FONT_NORMAL, bg=T("BG_ANA"), fg=T("YAZI_ACIK")).pack(pady=40)
            return

        self._durum_guncelle(f"{len(liste)} talep listeleniyor")
        for t in liste:
            self._talep_karti(t)

    def _talep_karti(self, t):
        or_ = ONCELIK_RENK.get(t.oncelik, T("GRI_CIZGI"))
        dr  = DURUM_RENK.get(t.durum, T("GRI_CIZGI"))
        kart = tk.Frame(self.icerik, bg=T("BG_KART"), padx=16, pady=10,
                        highlightbackground=or_, highlightthickness=2)
        kart.pack(fill="x", padx=16, pady=4)

        ust = tk.Frame(kart, bg=T("BG_KART"))
        ust.pack(fill="x")
        tk.Label(ust, text=f" {t.oncelik} ", font=("Segoe UI", 9, "bold"),
                 bg=or_, fg=T("YAZI_BEYAZ"), padx=6).pack(side="left", padx=(0,6))
        tk.Label(ust, text=f" {t.durum} ", font=("Segoe UI", 9, "bold"),
                 bg=dr, fg=T("YAZI_BEYAZ"), padx=6).pack(side="left", padx=(0,10))
        tk.Label(ust, text=t.kategori, font=FONT_KUCUK,
                 bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(side="left")
        tk.Label(ust, text=f"#{t.talep_id}", font=("Segoe UI", 9, "bold"),
                 bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(side="right")

        tk.Label(kart, text=t.aciklama, font=FONT_NORMAL,
                 bg=T("BG_KART"), fg=T("YAZI_ANA"), wraplength=600, justify="left").pack(anchor="w", pady=4)

        m = musteri_bul(self.musteriler, t.musteri_id)
        alt = f"👤 {m.ad if m else 'Bilinmiyor'}  |  📅 {t.tarih}"
        if t.cozum: alt += f"  |  ✅ {t.cozum[:60]}"
        tk.Label(kart, text=alt, font=FONT_KUCUK, bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(anchor="w")

        btn_f = tk.Frame(kart, bg=T("BG_KART"))
        btn_f.pack(fill="x", pady=(6,0))
        _buton(btn_f, "✏️ Güncelle",
               lambda tid=t.talep_id: self._talep_guncelle(tid),
               bg="#EDE9FE", fg=ACCENT, font_size=9).pack(side="left", padx=(0,4))
        _buton(btn_f, "✅ Çöz",
               lambda tid=t.talep_id: self._talep_coz(tid),
               bg="#DCFCE7", fg=YESIL, font_size=9).pack(side="left", padx=4)
        _buton(btn_f, "🗑 Sil",
               lambda tid=t.talep_id: self._talep_sil(tid),
               bg="#FEE2E2", fg=KIRMIZI, font_size=9).pack(side="right")

    def _talep_coz(self, talep_id):
        t = talep_bul(self.talepler, talep_id)
        if not t: return
        pencere = tk.Toplevel(self.root)
        pencere.title("Talep Çöz")
        pencere.geometry("380x220")
        pencere.configure(bg=T("BG_ANA"))
        pencere.grab_set()
        tk.Label(pencere, text="✅ Çözüm Açıklaması", font=FONT_ALT, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(pady=(16,6))
        cozum_var = tk.StringVar()
        tk.Entry(pencere, textvariable=cozum_var, font=FONT_NORMAL,
                 bg=T("BG_GIRDI"), relief="flat", fg=T("YAZI_ANA")).pack(fill="x", padx=24, ipady=6)
        def kaydet():
            c = cozum_var.get().strip()
            if not c:
                messagebox.showerror("Hata", "Çözüm açıklaması boş olamaz!", parent=pencere)
                return
            t.talebi_coz(c)
            talepleri_kaydet(self.talepler)
            self._banner_ozet_guncelle()
            self._durum_guncelle(f"Talep #{t.talep_id} çözüldü")
            pencere.destroy()
            self.talep_listesi_goster()
        _buton(pencere, "✅ Çözüldü Olarak İşaretle", kaydet, bg=YESIL).pack(pady=14, padx=24, fill="x")

    def _talep_guncelle(self, talep_id):
        t = talep_bul(self.talepler, talep_id)
        if not t: return
        pencere = tk.Toplevel(self.root)
        pencere.title("Talep Güncelle")
        pencere.geometry("360x230")
        pencere.configure(bg=T("BG_ANA"))
        pencere.grab_set()
        ic = tk.Frame(pencere, bg=T("BG_ANA"), padx=24, pady=16)
        ic.pack(fill="both", expand=True)
        tk.Label(ic, text="Durum:", font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w")
        durum_var = tk.StringVar(value=t.durum)
        ttk.Combobox(ic, textvariable=durum_var, values=DestekTalebi.DURUMLAR,
                     state="readonly", font=FONT_NORMAL).pack(fill="x", pady=4)
        tk.Label(ic, text="Öncelik:", font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w")
        oncelik_var = tk.StringVar(value=t.oncelik)
        ttk.Combobox(ic, textvariable=oncelik_var, values=DestekTalebi.ONCELIKLER,
                     state="readonly", font=FONT_NORMAL).pack(fill="x", pady=4)
        def kaydet():
            t.durum_guncelle(durum_var.get())
            t.oncelik = oncelik_var.get()
            talepleri_kaydet(self.talepler)
            pencere.destroy()
            self.talep_listesi_goster()
        _buton(ic, "💾 Güncelle", kaydet).pack(fill="x", pady=8)

    def _talep_sil(self, talep_id):
        t = talep_bul(self.talepler, talep_id)
        if t and messagebox.askyesno("Sil", "Bu talep silinsin mi?"):
            m = musteri_bul(self.musteriler, t.musteri_id)
            if m and t in m.talepler: m.talepler.remove(t)
            talep_sil(self.talepler, talep_id)
            talepleri_kaydet(self.talepler)
            self._banner_ozet_guncelle()
            self._durum_guncelle(f"Talep #{talep_id} silindi")
            self.talep_listesi_goster()

    # ─── YENİ DESTEK TALEBİ ──────────────────────────────────────────────────

    def _yeni_talep_ekrani(self, onceden_musteri_id=None):
        pencere = tk.Toplevel(self.root)
        pencere.title("Yeni Destek Talebi")
        pencere.geometry("440x460")
        pencere.configure(bg=T("BG_ANA"))
        pencere.grab_set()

        bant = tk.Frame(pencere, bg=ACCENT, pady=14)
        bant.pack(fill="x")
        tk.Label(bant, text="🎫 Yeni Destek Talebi", font=FONT_BASLIK, bg=ACCENT, fg=T("YAZI_BEYAZ")).pack()

        ic = tk.Frame(pencere, bg=T("BG_ANA"), padx=28, pady=14)
        ic.pack(fill="both", expand=True)

        tk.Label(ic, text="Müşteri *", font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w")
        musteri_adlari = [f"{m.ad} (ID:{m.musteri_id})" for m in self.musteriler]
        if not musteri_adlari:
            messagebox.showwarning("Uyarı", "Önce müşteri ekleyin!", parent=pencere)
            pencere.destroy()
            return
        musteri_var = tk.StringVar()
        if onceden_musteri_id:
            mb = musteri_bul(self.musteriler, onceden_musteri_id)
            if mb: musteri_var.set(f"{mb.ad} (ID:{mb.musteri_id})")
        ttk.Combobox(ic, textvariable=musteri_var, values=musteri_adlari,
                     state="readonly", font=FONT_NORMAL).pack(fill="x", pady=4)

        tk.Label(ic, text="Açıklama *", font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(6,0))
        aciklama_text = tk.Text(ic, font=FONT_NORMAL, bg=T("BG_GIRDI"), relief="flat", height=4, fg=T("YAZI_ANA"))
        aciklama_text.pack(fill="x")

        ikili = tk.Frame(ic, bg=T("BG_ANA"))
        ikili.pack(fill="x", pady=6)
        kat_var     = tk.StringVar(value="Genel")
        oncelik_var = tk.StringVar(value="Orta")
        for etiket, var, secenekler, side in [
            ("Kategori", kat_var,     ["Genel","Teknik","Fatura","Teslimat","Diğer"], "left"),
            ("Öncelik",  oncelik_var, DestekTalebi.ONCELIKLER,                       "right"),
        ]:
            f = tk.Frame(ikili, bg=T("BG_ANA"))
            f.pack(side=side, fill="x", expand=True, padx=(0,4) if side=="left" else (4,0))
            tk.Label(f, text=etiket, font=("Segoe UI", 9, "bold"), bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w")
            ttk.Combobox(f, textvariable=var, values=secenekler,
                         state="readonly", font=FONT_NORMAL).pack(fill="x")

        def kaydet():
            ms = musteri_var.get()
            if not ms:
                messagebox.showerror("Hata", "Müşteri seçin!", parent=pencere)
                return
            mid = int(ms.split("ID:")[1].rstrip(")"))
            aciklama = aciklama_text.get("1.0", "end").strip()
            if not aciklama:
                messagebox.showerror("Hata", "Açıklama boş olamaz!", parent=pencere)
                return
            yeni = DestekTalebi(aciklama=aciklama, oncelik=oncelik_var.get(),
                                musteri_id=mid, kategori=kat_var.get(), tarih=_tarih())
            self.talepler.append(yeni)
            m = musteri_bul(self.musteriler, mid)
            if m: m.talepler.append(yeni)
            talepleri_kaydet(self.talepler)
            self._banner_ozet_guncelle()
            self._durum_guncelle("Yeni destek talebi oluşturuldu")
            messagebox.showinfo("✅", "Talep oluşturuldu!", parent=pencere)
            pencere.destroy()
            self.talep_listesi_goster()

        _buton(ic, "💾 Talep Oluştur", kaydet, bg=ACCENT, font_size=11).pack(fill="x", pady=8)
        _buton(ic, "İptal", pencere.destroy, bg=T("GRI_CIZGI"), fg=T("YAZI_ANA")).pack(fill="x")

    # ─── DASHBOARD ───────────────────────────────────────────────────────────

    def dashboard_goster(self):
        for w in self.icerik.winfo_children():
            w.destroy()

        tk.Label(self.icerik, text="📊 Dashboard",
                 font=FONT_BASLIK, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", padx=16, pady=(12,6))
        _ayirici(self.icerik)

        # İstatistik kartları
        stat_f = tk.Frame(self.icerik, bg=T("BG_ANA"))
        stat_f.pack(fill="x", padx=16, pady=8)

        toplam_ciro    = sum(s.toplam_tutar() for s in self.satislar if s.durum == "Tamamlandı")
        bekleyen_satis = [s for s in self.satislar if s.durum == "Beklemede"]
        acik_t         = acik_talepler(self.talepler)
        iptal_satis    = [s for s in self.satislar if s.durum == "İptal"]
        ortalama_ciro  = (toplam_ciro / len(self.musteriler)) if self.musteriler else 0

        for baslik, deger, renk, ikon in [
            ("Toplam Müşteri",   len(self.musteriler),          MAVİ,      "👥"),
            ("Toplam Satış",     len(self.satislar),            YESIL,     "🛒"),
            ("Toplam Ciro",      f"{toplam_ciro:,.0f} ₺",      "#0891B2", "💰"),
            ("Müşteri Başı Ciro",f"{ortalama_ciro:,.0f} ₺",   ACCENT,    "📈"),
            ("Bekleyen Satış",   len(bekleyen_satis),           TURUNCU,   "⏳"),
            ("Açık Talepler",    len(acik_t),                   KIRMIZI,   "🎫"),
        ]:
            kart = tk.Frame(stat_f, bg=renk, padx=16, pady=14, width=140)
            kart.pack(side="left", padx=4, fill="y")
            kart.pack_propagate(False)
            tk.Label(kart, text=ikon, font=("Segoe UI", 18), bg=renk, fg=T("YAZI_BEYAZ")).pack()
            tk.Label(kart, text=str(deger), font=("Segoe UI", 14, "bold"),
                     bg=renk, fg=T("YAZI_BEYAZ")).pack()
            tk.Label(kart, text=baslik, font=("Segoe UI", 8),
                     bg=renk, fg=T("YAZI_BEYAZ"), wraplength=120).pack()

        # ── Aylık Ciro Grafiği ────────────────────────────────────────────────
        tk.Label(self.icerik, text="📅 Aylık Tamamlanan Ciro",
                 font=FONT_ALT, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", padx=16, pady=(18,4))

        aylik = defaultdict(float)
        for s in self.satislar:
            if s.durum == "Tamamlandı" and s.tarih:
                try:
                    ay = s.tarih[:7]  # "AA.BB.YYYY" → ilk 7 char: "AA.BB.Y" olmaz, düzelt
                    # Tarih formatı: "GG.AA.YYYY HH:MM"
                    parca = s.tarih.split(".")
                    ay_kisa = f"{parca[1]}/{parca[2][:4]}"
                    aylik[ay_kisa] += s.toplam_tutar()
                except:
                    pass

        if aylik:
            aylar_sirali = sorted(aylik.keys(), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0])))
            degerler     = [aylik[a] for a in aylar_sirali]
            max_val      = max(degerler) if degerler else 1

            GRAFIK_Y = 180
            GRAFIK_X = 700
            sol_pad  = 70
            sag_pad  = 20
            ust_pad  = 20
            alt_pad  = 40
            cubuk_bosluk = 8

            gf = tk.Frame(self.icerik, bg=T("BG_KART"), padx=8, pady=8,
                          highlightbackground=T("GRI_CIZGI"), highlightthickness=1)
            gf.pack(fill="x", padx=16, pady=4)
            c = tk.Canvas(gf, bg=T("BG_KART"), height=GRAFIK_Y+alt_pad+ust_pad,
                          width=GRAFIK_X, highlightthickness=0)
            c.pack(fill="x")

            n    = len(aylar_sirali)
            alan = GRAFIK_X - sol_pad - sag_pad
            gw   = max(10, alan // n - cubuk_bosluk) if n > 0 else 40
            step = alan // n if n > 0 else alan

            # Y ekseni çizgileri
            for i in range(5):
                y = ust_pad + (GRAFIK_Y * i // 4)
                c.create_line(sol_pad, y, GRAFIK_X-sag_pad, y,
                              fill=T("GRI_CIZGI"), dash=(3,3))
                val = max_val * (4-i) / 4
                c.create_text(sol_pad-6, y, text=f"{val/1000:.0f}K",
                              font=("Segoe UI", 7), anchor="e", fill=T("YAZI_ACIK"))

            for i, (ay, val) in enumerate(zip(aylar_sirali, degerler)):
                x0 = sol_pad + i * step + cubuk_bosluk // 2
                x1 = x0 + gw
                bar_h = int((val / max_val) * GRAFIK_Y) if max_val > 0 else 0
                y0 = ust_pad + GRAFIK_Y - bar_h
                y1 = ust_pad + GRAFIK_Y
                renk_g = GRAFIK_RENKLER[i % len(GRAFIK_RENKLER)]
                c.create_rectangle(x0, y0, x1, y1, fill=renk_g, outline="", width=0)
                # Değer etiketi
                c.create_text((x0+x1)//2, y0-4, text=f"{val/1000:.0f}K",
                              font=("Segoe UI", 7, "bold"), fill=T("YAZI_ANA"), anchor="s")
                # Ay etiketi
                c.create_text((x0+x1)//2, ust_pad+GRAFIK_Y+12, text=ay,
                              font=("Segoe UI", 7), fill=T("YAZI_ACIK"), anchor="n")

        # ── Şehir Dağılımı ────────────────────────────────────────────────────
        alt_f = tk.Frame(self.icerik, bg=T("BG_ANA"))
        alt_f.pack(fill="x", padx=16, pady=4)

        # Sol: En çok harcayan
        sol = tk.Frame(alt_f, bg=T("BG_ANA"))
        sol.pack(side="left", fill="both", expand=True, padx=(0,8))
        tk.Label(sol, text="🏆 En Çok Harcayan Müşteriler",
                 font=FONT_ALT, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(12,4))
        sirali = sorted(
            self.musteriler,
            key=lambda m: sum(s.toplam_tutar() for s in musterinin_satislari(self.satislar, m.musteri_id) if s.durum=="Tamamlandı"),
            reverse=True
        )[:5]
        maks_ciro = sum(s.toplam_tutar() for s in musterinin_satislari(self.satislar, sirali[0].musteri_id) if s.durum=="Tamamlandı") if sirali else 1

        for i, m in enumerate(sirali, 1):
            ciro = sum(s.toplam_tutar() for s in musterinin_satislari(self.satislar, m.musteri_id) if s.durum=="Tamamlandı")
            satir = tk.Frame(sol, bg=T("BG_KART"), padx=12, pady=8,
                             highlightbackground=T("GRI_CIZGI"), highlightthickness=1)
            satir.pack(fill="x", pady=2)
            tk.Label(satir, text=f"#{i}", font=("Segoe UI", 10, "bold"),
                     bg=T("BG_KART"), fg=MAVİ, width=3).pack(side="left")
            bilgi = tk.Frame(satir, bg=T("BG_KART"))
            bilgi.pack(side="left", fill="x", expand=True)
            tk.Label(bilgi, text=m.ad, font=FONT_NORMAL, bg=T("BG_KART"), fg=T("YAZI_ANA")).pack(anchor="w")
            oran = int((ciro / maks_ciro) * 100) if maks_ciro > 0 else 0
            bar_f = tk.Frame(bilgi, bg=T("GRI_CIZGI"), height=4)
            bar_f.pack(fill="x", pady=2)
            bar_dolu = tk.Frame(bar_f, bg=MAVİ, height=4, width=max(4, int(oran * 1.4)))
            bar_dolu.place(x=0, y=0)
            tk.Label(satir, text=f"{ciro:,.0f} ₺", font=("Segoe UI", 10, "bold"),
                     bg=T("BG_KART"), fg=YESIL).pack(side="right")

        # Sağ: Şehir dağılımı
        sag = tk.Frame(alt_f, bg=T("BG_ANA"))
        sag.pack(side="right", fill="both", expand=True, padx=(8,0))
        tk.Label(sag, text="📍 Şehir Bazlı Müşteri Dağılımı",
                 font=FONT_ALT, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", pady=(12,4))
        sehir_say = defaultdict(int)
        for m in self.musteriler:
            if m.sehir: sehir_say[m.sehir] += 1
        max_s = max(sehir_say.values()) if sehir_say else 1
        for idx, (sehir, say) in enumerate(sorted(sehir_say.items(), key=lambda x: -x[1])):
            sf = tk.Frame(sag, bg=T("BG_KART"), padx=12, pady=6,
                          highlightbackground=T("GRI_CIZGI"), highlightthickness=1)
            sf.pack(fill="x", pady=2)
            renk_s = GRAFIK_RENKLER[idx % len(GRAFIK_RENKLER)]
            tk.Label(sf, text="●", font=("Segoe UI", 12), bg=T("BG_KART"), fg=renk_s).pack(side="left", padx=(0,6))
            tk.Label(sf, text=sehir, font=FONT_NORMAL, bg=T("BG_KART"), fg=T("YAZI_ANA")).pack(side="left")
            tk.Label(sf, text=f"{say} müşteri", font=FONT_KUCUK,
                     bg=T("BG_KART"), fg=T("YAZI_ACIK")).pack(side="right")
            bar2 = tk.Frame(sf, bg=renk_s, height=4, width=max(6, int((say/max_s)*120)))
            bar2.pack(side="right", padx=8)

        # Acil talepler
        tk.Label(self.icerik, text="🔴 Acil / Yüksek Öncelikli Açık Talepler",
                 font=FONT_ALT, bg=T("BG_ANA"), fg=T("YAZI_ANA")).pack(anchor="w", padx=16, pady=(16,4))
        kritik = [t for t in acik_t if t.oncelik in ("Acil","Yüksek")]
        if not kritik:
            tk.Label(self.icerik, text="✅ Acil talep yok!", font=FONT_NORMAL,
                     bg=T("BG_ANA"), fg=YESIL).pack(anchor="w", padx=16, pady=4)
        else:
            for t in kritik[:6]:
                renk = ONCELIK_RENK.get(t.oncelik, T("GRI_CIZGI"))
                satir = tk.Frame(self.icerik, bg=T("BG_KART"), padx=14, pady=6,
                                 highlightbackground=renk, highlightthickness=2)
                satir.pack(fill="x", padx=16, pady=3)
                tk.Label(satir, text=f" {t.oncelik} ", font=("Segoe UI", 9, "bold"),
                         bg=renk, fg=T("YAZI_BEYAZ")).pack(side="left", padx=(0,8))
                m = musteri_bul(self.musteriler, t.musteri_id)
                tk.Label(satir, text=f"{m.ad if m else '?'}  —  {t.aciklama[:65]}",
                         font=FONT_KUCUK, bg=T("BG_KART"), fg=T("YAZI_ANA")).pack(side="left")

        self._durum_guncelle("Dashboard yüklendi")


if __name__ == "__main__":
    root = tk.Tk()
    app  = CRMApp(root)
    root.mainloop()
