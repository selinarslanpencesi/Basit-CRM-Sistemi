"""
veritabani.py — JSON tabanlı CRM veri katmanı
Müşteri, Satış ve DestekTalebi kayıtlarını okur/yazar.
"""

import json
import os
from musteri import Musteri, Satis, DestekTalebi

KLASOR            = os.path.dirname(os.path.abspath(__file__))
MUSTERILER_DOSYA  = os.path.join(KLASOR, "musteriler.json")
SATISLAR_DOSYA    = os.path.join(KLASOR, "satislar.json")
TALEPLER_DOSYA    = os.path.join(KLASOR, "talepler.json")


# ── MÜŞTERİ VERİTABANI ───────────────────────────────────────────────────────

def musterileri_kaydet(musteri_listesi):
    veri = [m.to_dict() for m in musteri_listesi]
    with open(MUSTERILER_DOSYA, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)


def musterileri_yukle():
    if not os.path.exists(MUSTERILER_DOSYA):
        return []
    try:
        with open(MUSTERILER_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        return [Musteri.from_dict(m) for m in veri]
    except (json.JSONDecodeError, KeyError):
        return []


def musteri_bul(musteri_listesi, musteri_id):
    for m in musteri_listesi:
        if m.musteri_id == musteri_id:
            return m
    return None


def musteri_sil(musteri_listesi, musteri_id):
    for i, m in enumerate(musteri_listesi):
        if m.musteri_id == musteri_id:
            musteri_listesi.pop(i)
            return True
    return False


def musteri_ara(musteri_listesi, anahtar):
    """Ada, telefona veya e-postaya göre müşteri arar."""
    anahtar = anahtar.lower()
    return [
        m for m in musteri_listesi
        if anahtar in m.ad.lower()
        or anahtar in m.telefon.lower()
        or anahtar in m.email.lower()
    ]


def sehire_gore_filtrele(musteri_listesi, sehir):
    return [m for m in musteri_listesi if m.sehir.lower() == sehir.lower()]


# ── SATIŞ VERİTABANI ─────────────────────────────────────────────────────────

def satislari_kaydet(satis_listesi):
    veri = [s.to_dict() for s in satis_listesi]
    with open(SATISLAR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)


def satislari_yukle():
    if not os.path.exists(SATISLAR_DOSYA):
        return []
    try:
        with open(SATISLAR_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        return [Satis.from_dict(s) for s in veri]
    except (json.JSONDecodeError, KeyError):
        return []


def satis_bul(satis_listesi, satis_id):
    for s in satis_listesi:
        if s.satis_id == satis_id:
            return s
    return None


def satis_sil(satis_listesi, satis_id):
    for i, s in enumerate(satis_listesi):
        if s.satis_id == satis_id:
            satis_listesi.pop(i)
            return True
    return False


def musterinin_satislari(satis_listesi, musteri_id):
    return [s for s in satis_listesi if s.musteri_id == musteri_id]


# ── DESTEK TALEBİ VERİTABANI ─────────────────────────────────────────────────

def talepleri_kaydet(talep_listesi):
    veri = [t.to_dict() for t in talep_listesi]
    with open(TALEPLER_DOSYA, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)


def talepleri_yukle():
    if not os.path.exists(TALEPLER_DOSYA):
        return []
    try:
        with open(TALEPLER_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        return [DestekTalebi.from_dict(t) for t in veri]
    except (json.JSONDecodeError, KeyError):
        return []


def talep_bul(talep_listesi, talep_id):
    for t in talep_listesi:
        if t.talep_id == talep_id:
            return t
    return None


def talep_sil(talep_listesi, talep_id):
    for i, t in enumerate(talep_listesi):
        if t.talep_id == talep_id:
            talep_listesi.pop(i)
            return True
    return False


def musterinin_talepleri(talep_listesi, musteri_id):
    return [t for t in talep_listesi if t.musteri_id == musteri_id]


def oncelige_gore_talep(talep_listesi, oncelik):
    return [t for t in talep_listesi if t.oncelik == oncelik]


def acik_talepler(talep_listesi):
    return [t for t in talep_listesi if t.durum in ("Açık", "İşlemde")]
