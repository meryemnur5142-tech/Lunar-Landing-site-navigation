#!/usr/bin/env python3
"""AY NAVIGATOR: Mons Mouton / VIPER için iniş sonrası görev planlayıcı (LUNA-AI paket modülü).

Not: Bu sürüm SPICE doğrulaması için luna_ai.spice_manager bağımlılığı kullanır.
Ne yapar?
  1) NASA PGDA'daki LDEM_80S_20MPP_ADJ.TIF'i (2.6 GB, COG) İNDİRMEDEN, internetten sadece gereken
     pencereyi okuyarak keser (HTTP range request). Kesilen DEM yerelde önbelleğe alınır.
  2) Eğim haritası hesaplar
  3) NASA/JPL SPICE (MOON_ME) ile güneş yüksekliği/azimutu ve DEM gölge haritasını çıkarır
  4) 30 günlük "güneşli zaman oranı" haritası verir (oran 0 = örneklenen anlarda güneş yok)
  5) Eğim limiti + gölge cezasıyla A* rota planlar (iniş noktası -> ulaşılabilir gölgeli hedef)
  6) Zaman adımlı güç/batarya simülasyonu: gidiş, gölgede kalış süresi, dönüş, şarj süresi
  7) --tur N ile "karanlıkta çalış -> güneşe dön, şarj ol -> tekrar git" döngüsünü N kez yapar
  8) Dünya yönü / ufuk / arazi engelli görüş ve iletişim görünürlüğü
  9) Yerel yüzey pürüzlülüğü, katalog bazlı krater mesafesi, rota yükseklik profili
  10) Sonuçları PNG + JSON + CSV olarak kaydeder

Kullanım:
  python ay_navigator.py --test                         # kendi kendini test eder (internet gerekmez)
  python ay_navigator.py --sentetik                     # sentetik krater ile demo (internet gerekmez)
  python ay_navigator.py                                # GERÇEK veri: VIPER bölgesi, otomatik başlangıç/hedef
  python ay_navigator.py --inis 31.62,-85.42 --tur 3    # iniş noktası (boylam,enlem) + 3 tur
  python ay_navigator.py --dem mons_mouton.tif          # elle kesilmiş DEM kullan
  Kalite: --err LDEM_ERR.TIF --effres LDEM_EFFRES.TIF (isteğe bağlı eşikler: --max-err-m, --max-effres-m)
  Diğer: --tarih 2026-11-27T00:00 --yari-km 10 --faktor 4 --bas satir,sutun --hedef satir,sutun
         --soc0 1.0 --kalis-saat 3 --panel-el 0 --cikti klasor --yenile

Gerekli paketler: numpy, scipy, matplotlib, rasterio, pyproj, spiceypy
  python -m pip install numpy scipy matplotlib rasterio pyproj spiceypy
Boylam DOĞU pozitiftir. VIPER/Mons Mouton bölgesi: ~31.6°D (+31.6), ~85.4°G (-85.4).

Parametre etiketleri RoverParam içinde: [K]=NASA kaynaklı, [T]=kaynaktan türetilmiş, [V]=VARSAYIM.
Veri atfı: Barker et al., 2023, Planet. Sci. J., 4, 183 (doi:10.3847/PSJ/acf3e1).
"""
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import os
import re
import warnings
import shutil
import urllib.request
from pathlib import Path
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, uniform_filter, label, map_coordinates

UTC = timezone.utc
J2000 = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
AY_PROJ = "+proj=longlat +R=1737400 +no_defs"
LDEM_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF"
VARSAYILAN_BOYLAM, VARSAYILAN_ENLEM = 31.62, -85.42   # VIPER keşif alanı merkezi (Zacny 2025)


# ======================================================================================
# 1) PARAMETRELER
# ======================================================================================
@dataclass
class RoverParam:
    rover_kutlesi_kg: float = 447.0    # [K] NASA NTRS 20240013291 VIPER roving mass
    batarya_Wh: float = 5420.0        # [K] NASA VIPER batarya, ömür başı, 0°C
    batarya_kimyasi: str | None = None # [TBD] NASA-belgeli kimya bilgisi olmadan tahmin ETME
    psr_giris_soc_min: float = 0.85   # [V] LUNA-AI gereksinimi, NASA VIPER prosedürü değil
    soc_min: float = 0.10             # [V] alt güvenlik sınırı
    panel_pik_W: float = 320.0        # [K] tek yüz panel 320 W, köşe panel 450 W; toplam güç DEĞİL
    panel_normal_el_deg: float = 0.0  # [V] güneşe dönükken panel normalinin yüksekliği (0 = dikey panel)
    P_hibernasyon_W: float = 108.0    # [T] 5420 Wh/50 saat türetim; NASA ölçülmüş tüketim değil
    P_surus_W: float = 300.0          # [V] sürüş gücü
    P_operasyon_W: float = 600.0      # [T] ~5420 Wh / 9 saat (gölgede matkaplı çalışma)
    hiz_ms: float = 0.10              # [V] planlama hızı 0.1 m/s; NASA onaylı operasyon hızı değil
    max_egim_deg: float = 15.0        # [V] rota sınırı; iniş yüzeyi sınırı AYRIDIR
    egim_ceza: float = 1.0            # [V] rotada eğim cezası katsayısı
    golge_ceza: float = 0.3           # [V] rotada gölge cezası (güneşli yolu tercih)

    def tuketim_W(self, mod):
        return {"hibernasyon": self.P_hibernasyon_W, "surus": self.P_surus_W,
                "operasyon": self.P_operasyon_W}[mod]


# ======================================================================================
# 2) DEM: UZAKTAN KESME (COG), OKUMA, SENTETİK, YARDIMCILAR
# ======================================================================================
def dem_geometri_kontrol(src):
    """Bu planlayıcı kuzey yukarı, kare pikselli, metrik Ay projeksiyonu kullanır."""
    from pyproj import CRS
    if src.crs is None:
        raise ValueError("DEM koordinat sistemi eksik.")
    crs = CRS.from_wkt(src.crs.to_wkt())
    if not crs.is_projected or not 1_730_000 <= getattr(crs.ellipsoid, "semi_major_metre", 0) <= 1_745_000:
        raise ValueError("Ay için tanımlanmış projeksiyonlu DEM gerekli.")
    if any(not math.isclose(a.unit_conversion_factor, 1.0) for a in crs.axis_info[:2]):
        raise ValueError("DEM yatay koordinat birimi metre olmalı.")
    t = src.transform
    if t.b or t.d or t.a <= 0 or t.e >= 0 or not math.isclose(t.a, -t.e):
        raise ValueError("DEM kuzey yukarı ve kare pikselli olmalı.")


def yukseklik_oku(src, window=None, kalite=False):
    """Önce veri maskesi, sonra ölçek, ofset ve düşey birim dönüşümü."""
    etiket = src.tags(1)
    birim_metni = src.units[0] or etiket.get("units") or src.tags().get("z#units")
    if not birim_metni:
        warnings.warn("Düşey birim belirtilmemiş; metre varsayıldı.")
    birim = re.sub(r"\s*\([^()]*\)\s*$", "", (birim_metni or "m").strip().lower()).strip()
    katsayi = {"m": 1, "meter": 1, "meters": 1, "metre": 1, "metres": 1,
               "km": 1000, "kilometer": 1000, "kilometers": 1000, "kilometre": 1000,
               "kilometres": 1000, "ft": 0.3048, "foot": 0.3048, "feet": 0.3048}
    if birim not in katsayi:
        raise ValueError(f"Desteklenmeyen yükseklik birimi: {birim}")
    veri = src.read(1, window=window, masked=True).astype("float32").filled(np.nan)
    for dolgu in (etiket.get("_FillValue"), etiket.get("missing_value"), src.tags().get("z#_FillValue")):
        if dolgu is not None:
            veri[veri == float(dolgu)] = np.nan
    if src.nodata is None and np.any(veri == -32768):
        warnings.warn("NoData tanımsız; ham -32768 dolgu değerleri maskelendi.")
        veri[veri == -32768] = np.nan
    olcek, ofset = src.scales[0], src.offsets[0]
    if not np.isfinite([olcek, ofset]).all() or olcek == 0:
        raise ValueError(f"Geçersiz ölçek/ofset: {olcek}, {ofset}")
    if (olcek, ofset) != (1, 0):
        print(f"Raster dönüşümü: ölçek={olcek:g}, ofset={ofset:g}, birim={birim}")
    veri = (veri * olcek + ofset) * katsayi[birim]
    if not kalite and np.any(np.abs(veri[np.isfinite(veri)]) > 12000):
        raise ValueError("Ay referans küresine göre ±12000 m denetim sınırı aşıldı; dolgu, düşey birim, ölçek ve ofseti kontrol edin.")
    veri[~np.isfinite(veri)] = np.nan
    return veri


def dem_kes(kaynak, boylam, enlem, yari_m, cikti):
    """LDEM (yerel dosya veya https linki) içinden ROI penceresini keser.
    Kaynak bir COG olduğu için URL verilirse dosyanın tamamı değil, sadece pencere kadar veri indirilir."""
    try:
        import rasterio
        from pyproj import Transformer
        from rasterio.windows import Window, from_bounds
    except ImportError:
        sys.exit("HATA: rasterio ve pyproj gerekli ->  pip install rasterio pyproj")
    ortam = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".TIF,.tif,.tiff",
                 GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="3", GDAL_HTTP_TIMEOUT="60",
                 VSI_CACHE="TRUE", VSI_CACHE_SIZE=str(256 * 1024 * 1024))
    print(f"DEM kesiliyor: {kaynak}\n  merkez=({boylam:.3f}°D, {enlem:.3f}°)  yarıçap={yari_m / 1000:g} km")
    with rasterio.Env(**ortam):
        try:
            src = rasterio.open(kaynak)
        except Exception as e:
            sys.exit(f"HATA: DEM açılamadı ({e}).\n  İnternet/proxy ayarını kontrol edin ya da dosyayı elle indirip "
                     f"--kes <yerel_dosya.TIF> ile verin.")
        with src:
            dem_geometri_kontrol(src)
            x, y = Transformer.from_crs(AY_PROJ, src.crs, always_xy=True).transform(boylam, enlem)
            w = from_bounds(x - yari_m, y - yari_m, x + yari_m, y + yari_m, src.transform)
            w = Window(int(math.floor(w.col_off)), int(math.floor(w.row_off)),
                       int(math.ceil(w.width)), int(math.ceil(w.height)))
            try:
                w = w.intersection(Window(0, 0, src.width, src.height))
            except Exception:
                sys.exit("HATA: istenen konum DEM kapsamının (80°G-90°G) dışında.")
            veri = yukseklik_oku(src, w)
            profil = dict(driver="GTiff", dtype="float32", count=1, crs=src.crs, nodata=float("nan"),
                          height=veri.shape[0], width=veri.shape[1], transform=src.window_transform(w),
                          compress="deflate")
    with rasterio.open(cikti, "w", **profil) as dst:
        dst.write(veri, 1)
        dst.set_band_unit(1, "m")
    mn, mx = np.nanmin(veri), np.nanmax(veri)
    print(f"  Kesildi: {cikti}  boyut={veri.shape}  min={mn:.0f} m  max={mx:.0f} m")
    if mx - mn > 25000 or abs(mn) > 20000 or abs(mx) > 20000:
        print("  UYARI: yükseklik aralığı beklenenden çok büyük; birim metre olmayabilir, kaynağı kontrol edin.")
    return cikti


def dem_oku(yol):
    """GeoTIFF DEM -> (dem[m], piksel_m, crs_wkt, (x_sol_ust, y_sol_ust))."""
    import rasterio
    with rasterio.open(yol) as src:
        dem_geometri_kontrol(src)
        dem = yukseklik_oku(src)
        t = src.transform
        return dem, float(src.res[0]), (src.crs.to_wkt() if src.crs else None), (float(t.c), float(t.f))


def dem_doldur(dem):
    """NaN pikselleri en yakın geçerli değerle doldurur."""
    maske = np.isnan(dem)
    if not maske.any():
        return dem
    if maske.all():
        sys.exit("HATA: DEM tamamen boş (NaN).")
    idx = distance_transform_edt(maske, return_distances=False, return_indices=True)
    return dem[tuple(idx)]


def dem_kucult(dem, piksel_m, faktor):
    """Blok ortalamasıyla küçültme (hız için; örn. faktor=4: 20 m -> 80 m). Sol-üst köşe sabit kalır."""
    if faktor <= 1:
        return dem, piksel_m
    nr, nc = (dem.shape[0] // faktor) * faktor, (dem.shape[1] // faktor) * faktor
    k = dem[:nr, :nc].reshape(nr // faktor, faktor, nc // faktor, faktor).mean(axis=(1, 3))
    return k.astype("float32"), piksel_m * faktor


def blok_maksimum(dizi, faktor):
    """Eksik değer içeren blok bilinmiyor olarak kalır."""
    nr, nc = (boyut // faktor for boyut in dizi.shape)
    return dizi[:nr*faktor, :nc*faktor].reshape(nr, faktor, nc, faktor).max(axis=(1, 3))


def egim_guvenli(dem, piksel_m, faktor):
    kaynak = egim_hesapla(dem, piksel_m)
    kaynak[~np.isfinite(dem)] = np.nan
    return kaynak, blok_maksimum(kaynak, faktor)


def kalite_oku(yol, dem_yolu):
    """Aynı yerleşimdeki tam üründen veya kesilmiş üründen DEM penceresini oku."""
    import rasterio
    from rasterio.windows import Window
    with rasterio.open(dem_yolu) as hedef, rasterio.open(yol) as src:
        dem_geometri_kontrol(src)
        if src.crs != hedef.crs or not np.allclose(src.res, hedef.res, rtol=0, atol=1e-7):
            raise ValueError("Kalite rasterının projeksiyonu veya çözünürlüğü DEM ile uyuşmuyor.")
        col, row = (~src.transform) * (hedef.transform.c, hedef.transform.f)
        c, r = round(col), round(row)
        if (abs(c-col) > 1e-5 or abs(r-row) > 1e-5 or min(c, r) < 0 or
                c + hedef.width > src.width or r + hedef.height > src.height):
            raise ValueError("Kalite rasterı DEM pikselleriyle hizalı değil veya alanı kapsamıyor.")
        veri = yukseklik_oku(src, Window(c, r, hedef.width, hedef.height), kalite=True)
        veri[veri < 0] = np.nan
        return veri


def boylam_enlem_to_piksel(boylam, enlem, crs, kose, piksel_orijinal_m, faktor, sekil):
    """(boylam, enlem) -> çalışma gridinde (satır, sütun). Gridin dışındaysa hata verir."""
    from pyproj import Transformer
    x, y = Transformer.from_crs(AY_PROJ, crs, always_xy=True).transform(boylam, enlem)
    c = int(math.floor((x - kose[0]) / piksel_orijinal_m / faktor))
    r = int(math.floor((kose[1] - y) / piksel_orijinal_m / faktor))
    if not (0 <= r < sekil[0] and 0 <= c < sekil[1]):
        raise ValueError(f"({boylam}, {enlem}) kesilen DEM'in dışında (satır={r}, sütun={c}, grid={sekil}).")
    return r, c


def sentetik_dem(n=300, piksel_m=40.0):
    """Demo/test: 12x12 km, ortada 400 m derin krater + kenar sırtı + engel tepe + hafif eğim."""
    yy, xx = np.mgrid[0:n, 0:n]
    x, y = (xx - n / 2) * piksel_m, (yy - n / 2) * piksel_m
    r = np.hypot(x, y)
    krater = -400 * np.exp(-r ** 2 / (2 * 1200 ** 2))
    sirt = 40 * np.exp(-((r - 2300) / 400) ** 2)
    tepe = 120 * np.exp(-(((x + 3500) ** 2 + (y - 1500) ** 2) / (2 * 700 ** 2)))
    gurultu = gaussian_filter(np.random.default_rng(1).normal(0, 1, (n, n)), 6) * 100
    return (krater + sirt + tepe + 0.02 * x + gurultu).astype("float32"), piksel_m


def egim_hesapla(dem, piksel_m):
    """Horn (1981) 3x3 sobel-türevi: eğim DERECE; NoData veya kenar -> NaN.

    z1 z2 z3
    z4 z5 z6     dx=((z3+2*z6+z9)-(z1+2*z4+z7))/(8*pixel)
    z7 z8 z9     dy=((z7+2*z8+z9)-(z1+2*z2+z3))/(8*pixel)
    Güvenlik için kaynak gridde hesaplanıp küçültmede blok maksimumu alınır.
    """
    from scipy.ndimage import convolve, minimum_filter
    z = np.asarray(dem, dtype=np.float64)
    if piksel_m <= 0:
        raise ValueError("Piksel boyutu pozitif metre olmalı")
    finite = np.isfinite(z)
    safe = np.where(finite, z, 0.0)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)/(8*piksel_m)
    ky = np.array([[-1,-2,-1], [0,0,0], [1,2,1]], dtype=float)/(8*piksel_m)
    # scipy.ndimage.convolve çekirdeği ters çevirdiği için işaret değişir,
    # arctan(hypot) için işaret önemsizdir.
    dx = convolve(safe, kx, mode="nearest")
    dy = convolve(safe, ky, mode="nearest")
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    slope[minimum_filter(finite.astype("uint8"), size=3, mode="constant", cval=0) == 0] = np.nan
    return slope


def tepe_golgeleme(dem, piksel_m, az_deg=315.0, el_deg=35.0):
    """Sadece görsel için klasik hillshade."""
    gy, gx = np.gradient(dem.astype("float64"), piksel_m)
    egim, bakis = np.arctan(np.hypot(gx, gy)), np.arctan2(-gx, gy)
    az, el = math.radians(az_deg), math.radians(el_deg)
    return np.clip(np.sin(el) * np.cos(egim) + np.cos(el) * np.sin(egim) * np.cos(az - bakis), 0, 1)


# ======================================================================================
# 3) GÜNEŞ KONUMU (NASA/JPL SPICE; varsayılan MOON_ME)
# ======================================================================================
def _utc(t):
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t.astimezone(UTC)


# DE440 efemerisi + ona uygun Ay yönelim ve MOON_ME çerçeve dosyaları.
# Kaynak: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/
SPICE_KERNEL_URLS = {
    "naif0012.tls": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls",
    "de440s.bsp": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp",
    "moon_pa_de440_200625.bpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_de440_250416.tf",
}
_SPICE = None
_GUNES_MODELI = "spice"


def _kernel_indir_yedek(dizin, offline=False):
    """luna_ai paketi yoksa yedek: yerelde ara, yoksa NAIF'ten indir. SHA256 doğrulaması YOKTUR;
    yalnızca dosya başlığı (DAF/ veya KPL/) denetlenir. En yeni eşleşen ad NAIF klasör listesinden bulunur."""
    taban = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/"
    liste = [("lsk/", r"naif\d{4}\.tls", "naif0012.tls"), ("spk/planets/", r"de440s\.bsp", "de440s.bsp"),
             ("pck/", r"moon_pa_de440_\d+\.bpc", "moon_pa_de440_200625.bpc"),
             ("fk/satellites/", r"moon_de440_\d+\.tf", "moon_de440_250416.tf")]
    istek = lambda u: urllib.request.Request(u, headers={"User-Agent": "AyNavigator/2.1"})
    yollar = []
    for alt, desen, bilinen in liste:
        yerel = sorted(p for p in dizin.iterdir() if p.is_file() and re.fullmatch(desen, p.name) and p.stat().st_size > 100)
        if yerel:
            yollar.append(yerel[-1]); continue
        if offline:
            raise RuntimeError(f"SPICE çekirdeği eksik ({desen}) -> {dizin}. İnternet açıkken bir kez çalıştırın "
                               f"veya dosyayı elle koyun: {taban}{alt}")
        adlar = []
        try:
            with urllib.request.urlopen(istek(taban + alt), timeout=60) as c:
                adlar = sorted(set(re.findall(r'href="(' + desen + r')"', c.read().decode("utf-8", "replace"))))
        except Exception as hata:
            print(f"  NAIF klasör listesi okunamadı ({hata}); bilinen ad denenecek: {bilinen}")
        ad = adlar[-1] if adlar else bilinen
        hedef, gecici = dizin / ad, dizin / (ad + ".part")
        print(f"NASA NAIF çekirdeği indiriliyor: {ad} ...", flush=True)
        try:
            with urllib.request.urlopen(istek(taban + alt + ad), timeout=120) as c, open(gecici, "wb") as f:
                shutil.copyfileobj(c, f)
            with open(gecici, "rb") as f:
                if f.read(4) not in (b"DAF/", b"KPL/"):
                    raise RuntimeError("indirilen dosya SPICE çekirdeği değil (proxy/giriş sayfası olabilir)")
            gecici.replace(hedef)
        except Exception as hata:
            gecici.unlink(missing_ok=True)
            raise RuntimeError(f"NASA çekirdeği indirilemedi ({ad}): {hata}\n  Elle indirin: {taban}{alt}{ad} -> {dizin}") from hata
        yollar.append(hedef)
    return yollar


def spice_hazirla(kernel_dir="kernels", offline=False):
    """SPICE çekirdeklerini yerel olarak saklar; sessiz analitik geri dönüş yapmaz."""
    global _SPICE
    try:
        import spiceypy as spice
    except ImportError as hata:
        raise RuntimeError("SPICE için 'python -m pip install spiceypy' çalıştırın.") from hata
    dizin = Path(kernel_dir).expanduser().resolve()
    dizin.mkdir(parents=True, exist_ok=True)
    # Tekrar çalıştırmada yüklü kernel/çerçeve karışmasını önle.
    spice.kclear()
    # Yeni LUNA-AI ile AYNI SHA256 doğrulamalı kernel yöneticisini kullan.
    # Tek dosyalı eski indirici eksik/bozuk kernel dosyasını fark etmiyordu.
    try:
        from luna_ai.spice_manager import download_and_verify
        yollar = list(download_and_verify(dizin, offline=offline))
    except ImportError:
        print("UYARI: luna_ai paketi bulunamadı; yedek kernel indirici kullanılıyor (SHA256 doğrulaması yok).")
        yollar = _kernel_indir_yedek(dizin, offline)
    for yol in yollar:
        spice.furnsh(str(yol))          # spiceypy Path değil str ister
    try:
        # Hem Güneş hem Dünya, istenen takvim uçlarında MOON_ME'de çalışmalı.
        for tarih in ("2024-01-01 00:00:00 UTC", "2026-11-27 00:00:00 UTC", "2035-12-31 00:00:00 UTC"):
            ornek = spice.str2et(tarih)
            for hedef in ("SUN", "EARTH"):
                spice.spkpos(hedef, ornek, "MOON_ME", "LT+S", "MOON")
        assert spice.namfrm("MOON_ME") != 0
    except Exception as hata:
        spice.kclear()
        raise RuntimeError(f"SPICE kernel seti eksik/uyumsuz: {hata}") from hata
    _SPICE = spice
    print(f"Güneş konumu: NASA/JPL SPICE DE440 / MOON_ME, çekirdek klasörü: {dizin}")


def gunes_konumu_spice(t, enlem, boylam):
    """MOON_ME'de Ay yüzeyinden Güneş merkezi: (yükseklik, kuzeyden saat yönü azimut).

    Boylam doğuya doğru pozitiftir; Ay'ın atmosferi yoktur. İniş alanı merkezinin
    küresel yüzeyi kullanılır. Arazi ufuk/gölgesi ayrı DEM gölge modelinde hesaplanır.
    """
    if _SPICE is None:
        raise RuntimeError("SPICE başlatılmadı; spice_hazirla() çağırılmalı.")
    zaman = _utc(t).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
    et = _SPICE.str2et(zaman)
    merkezden_gunese, _ = _SPICE.spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")
    lat, lon = math.radians(enlem), math.radians(boylam)
    c, sl = math.cos(lat), math.sin(lat)
    cl, so = math.cos(lon), math.sin(lon)
    up = np.array([c * cl, c * so, sl])
    east = np.array([-so, cl, 0.0])
    north = np.array([-sl * cl, -sl * so, c])
    # MOON_ME sabit koordinatlarında gözlemci yaklaşık 1737.4 km küresel yüzeyde.
    g = np.asarray(merkezden_gunese, dtype=float) - 1737.4 * up
    guneyukari = float(np.dot(g, up))
    dogu = float(np.dot(g, east))
    kuzey = float(np.dot(g, north))
    yukseklik = math.degrees(math.atan2(guneyukari, math.hypot(dogu, kuzey)))
    azimut = math.degrees(math.atan2(dogu, kuzey)) % 360.0
    return yukseklik, azimut


def gunes_konumu(t, enlem, boylam):
    if _GUNES_MODELI == "analitik":  # yalnızca çevrimdışı birim testi / açık demo modu
        return gunes_konumu_analitik(t, enlem, boylam)
    return gunes_konumu_spice(t, enlem, boylam)


def gunes_alt_noktasi(t):
    """Güneşin Ay'da tam tepede olduğu nokta: (enlem_deg, boylam_deg [doğu +]).
    Not: Ay'ın librasyonu (±~8°) dahil değildir; kutup bölgesinde gölge zamanlamasında farklar yaratabilir."""
    d = (_utc(t) - J2000).total_seconds() / 86400.0
    g = math.radians(357.528 + 0.9856003 * d)
    lam_gunes = 280.460 + 0.9856474 * d + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
    L_ay = 218.316 + 13.176396 * d                    # Ay'ın ortalama ekliptik boylamı
    omega = 125.04452 - 0.05295377 * d                # Ay yörünge çıkış düğümü
    enlem = 1.5424 * math.sin(math.radians(lam_gunes - omega))
    boylam = (lam_gunes - L_ay) % 360.0 - 180.0
    return enlem, boylam


def gunes_konumu_analitik(t, enlem, boylam):
    """Yaklaşık analitik güneş modeli; yalnızca --test veya --sentetik --analitik-gunes."""
    dlt_deg, lon_s = gunes_alt_noktasi(t)
    phi, dlt, H = map(math.radians, (enlem, dlt_deg, boylam - lon_s))
    E = -math.cos(dlt) * math.sin(H)
    N = math.cos(phi) * math.sin(dlt) - math.sin(phi) * math.cos(dlt) * math.cos(H)
    U = math.sin(phi) * math.sin(dlt) + math.cos(phi) * math.cos(dlt) * math.cos(H)
    return math.degrees(math.asin(max(-1.0, min(1.0, U)))), math.degrees(math.atan2(E, N)) % 360.0


def grid_yonleri(boylam, enlem, crs=None):
    """Güney kutup stereografik gridde yerel (kuzey, doğu) birim vektörleri -> ((nx,ny),(ex,ey)).
    crs (WKT) + pyproj varsa sayısal, yoksa analitik: x = rho*sin(lon), y = rho*cos(lon);
    kuzey (enlem artışı) kutuptan dışarı doğrudur."""
    if crs is not None:
        try:
            from pyproj import Transformer
            tr = Transformer.from_crs(AY_PROJ, crs, always_xy=True)
            x0, y0 = tr.transform(boylam, enlem)
            xn, yn = tr.transform(boylam, enlem + 1e-4)
            xe, ye = tr.transform(boylam + 1e-4, enlem)
            nv, ev = np.array([xn - x0, yn - y0]), np.array([xe - x0, ye - y0])
            return tuple(nv / np.linalg.norm(nv)), tuple(ev / np.linalg.norm(ev))
        except Exception:
            pass
    lam = math.radians(boylam)
    return (math.sin(lam), math.cos(lam)), (math.cos(lam), -math.sin(lam))


def yatay_yon_grid(az_deg, boylam, enlem, crs=None):
    """Güneşe doğru yatay birim vektör (grid x, y)."""
    N, E = grid_yonleri(boylam, enlem, crs)
    a = math.radians(az_deg)
    return (math.cos(a) * N[0] + math.sin(a) * E[0], math.cos(a) * N[1] + math.sin(a) * E[1])


# ======================================================================================
# 4) GÖLGE, AYDINLANMA ORANI, GÜÇ
# ======================================================================================
def golge_haritasi(dem, piksel_m, el_deg, yatay_xy):
    """True = gölgede. Güneş yönüne hizalı çerçevede ufuk taraması O(N^2).
    Bölge dışı = engel yok; Ay eğriliği ve ROI içi güneş yönü değişimi ihmal edilir."""
    nr, nc = dem.shape
    if el_deg <= 0:
        return np.ones(dem.shape, bool)
    sx, sy = yatay_xy
    adim_yuk = piksel_m * math.tan(math.radians(el_deg))
    M = int(math.ceil(math.hypot(nr, nc))) + 2
    c0, r0, m0 = (nc - 1) / 2.0, (nr - 1) / 2.0, (M - 1) / 2.0
    ii, jj = np.meshgrid(np.arange(M) - m0, np.arange(M) - m0, indexing="ij")
    r, c = r0 - (ii * sy + jj * sx), c0 + (ii * sx - jj * sy)
    icerde = (r >= 0) & (r <= nr - 1) & (c >= 0) & (c <= nc - 1)
    Z = np.where(icerde, map_coordinates(dem.astype("float64"), [r, c], order=1, mode="nearest"), -1e9)
    golge_r = np.zeros((M, M), bool)
    H = np.full(M, -1e9)
    for i in range(M - 1, -1, -1):                    # güneş tarafından uzağa doğru
        ufuk = H - adim_yuk
        golge_r[i] = ufuk > Z[i] + 1e-3
        H = np.maximum(Z[i], ufuk)
    rr, cc = np.mgrid[0:nr, 0:nc]
    xo, yo = cc - c0, -(rr - r0)
    u, v = xo * sx + yo * sy + m0, -xo * sy + yo * sx + m0
    return map_coordinates(golge_r.astype("float32"), [u, v], order=1, mode="nearest") > 0.5


def aydinlanma_orani(dem, piksel_m, boylam, enlem, t0, gun=30, adim_saat=6, crs=None):
    """Her pikselin 'gun' gün boyunca güneş gördüğü zaman oranı (0 = örneklenen anlarda güneş yok)."""
    toplam, adim = np.zeros(dem.shape), int(gun * 24 / adim_saat)
    for k in range(adim):
        el, az = gunes_konumu(t0 + timedelta(hours=k * adim_saat), enlem, boylam)
        if el > 0:
            toplam += ~golge_haritasi(dem, piksel_m, el, yatay_yon_grid(az, boylam, enlem, crs))
    return toplam / adim


def isik_gucu_haritasi(dem, piksel_m, el_deg, yatay_xy, golge, par):
    """Her pikselde panel gücü (W). Rover'ın paneli güneşe çevirebildiği varsayılır (azimut hizalı).
    Arazi güneşe doğru yükseliyorsa panel normali yukarı yatar."""
    if el_deg <= 0:
        return np.zeros(dem.shape)
    gy, gx = np.gradient(dem.astype("float64"), piksel_m)
    egim_gunese = gx * yatay_xy[0] + (-gy) * yatay_xy[1]
    panel_el = par.panel_normal_el_deg + np.degrees(np.arctan(egim_gunese))
    cos_gelis = np.clip(np.cos(np.radians(el_deg - panel_el)), 0.0, 1.0)
    return np.where(golge, 0.0, par.panel_pik_W * cos_gelis)


_GUC_ONBELLEK = {}


def _guc_haritasi(dem, piksel_m, boylam, enlem, t, par, crs):
    """Aynı anın güç haritasını önbellekler (bisection ve çoklu tur simülasyonlarını hızlandırır)."""
    anahtar = (id(dem), round(t.timestamp()), boylam, enlem, piksel_m, crs, par.panel_pik_W, par.panel_normal_el_deg)
    g = _GUC_ONBELLEK.get(anahtar)
    if g is None:
        el, az = gunes_konumu(t, enlem, boylam)
        h = yatay_yon_grid(az, boylam, enlem, crs)
        g = isik_gucu_haritasi(dem, piksel_m, el, h, golge_haritasi(dem, piksel_m, el, h), par).astype("float32")
        if len(_GUC_ONBELLEK) > 800:
            _GUC_ONBELLEK.clear()
        _GUC_ONBELLEK[anahtar] = g
    return g


# ======================================================================================
# 5) ROTA: 8 komşulu A* (metre bazlı maliyet, eğim limiti = duvar, gölge/eğim cezası)
# ======================================================================================
def a_yildiz(dem, egim, piksel_m, bas, hedef, par, golge=None):
    """Maliyet = 3B yol uzunluğu * (1 + egim_ceza*egim/max_egim + golge_ceza*gölge). Rota yoksa None."""
    n, m = dem.shape
    engel = ~(egim <= par.max_egim_deg)               # NaN de engel
    if engel[bas] or engel[hedef]:
        return None
    adimlar = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    g = np.full((n, m), np.inf)
    g[bas] = 0.0
    onceki = {}

    def h(p):                                         # octile mesafe (kabul edilebilir)
        dr, dc = abs(p[0] - hedef[0]), abs(p[1] - hedef[1])
        return piksel_m * ((dr + dc) + (math.sqrt(2) - 2) * min(dr, dc))

    acik = [(h(bas), bas)]
    while acik:
        f, p = heapq.heappop(acik)
        if p == hedef:
            break
        if f > g[p] + h(p) + 1e-9:                    # eski kayıt
            continue
        for dr, dc in adimlar:
            q = (p[0] + dr, p[1] + dc)
            if not (0 <= q[0] < n and 0 <= q[1] < m) or engel[q]:
                continue
            if dr and dc and (engel[p[0], q[1]] or engel[q[0], p[1]]):
                continue
            yol3d = math.hypot(piksel_m * math.hypot(dr, dc), float(dem[q] - dem[p]))
            ceza = 1.0 + par.egim_ceza * egim[q] / par.max_egim_deg + (par.golge_ceza if (golge is not None and golge[q]) else 0.0)
            yeni = g[p] + yol3d * ceza
            if yeni < g[q]:
                g[q], onceki[q] = yeni, p
                heapq.heappush(acik, (yeni + h(q), q))
    if hedef != bas and hedef not in onceki:
        return None
    rota = [hedef]
    while rota[-1] != bas:
        rota.append(onceki[rota[-1]])
    return rota[::-1]


def rota_zamanlari(rota, dem, egim, piksel_m, par):
    """Düğümlere varış zamanları (s) ve toplam 3B uzunluk (m). Hız eğimle azalır (yarıya kadar)."""
    t, L = [0.0], 0.0
    for a, b in zip(rota[:-1], rota[1:]):
        uz = math.hypot(piksel_m * math.hypot(b[0] - a[0], b[1] - a[1]), float(dem[b] - dem[a]))
        v = par.hiz_ms * (1.0 - 0.5 * min(1.0, float(egim[b]) / par.max_egim_deg))
        t.append(t[-1] + uz / v)
        L += uz
    return np.array(t), L


def otomatik_noktalar(egim, oran, dem, piksel_m, par, bas=None, min_mesafe_m=1500.0):
    """Ulaşılabilir (eğim limitiyle bağlı) bölgede örnekleme boyunca gölgeli bir hedef seçer.
    bas verilirse (iniş noktası): hedef = o noktadan ulaşılabilen en yakın düz gölge adayı pikseli.
    bas yoksa: en çok düz gölge adayı içeren bağlı bölge seçilir, hedef = harita merkezine en yakın PSR pikseli,
    başlangıç = hedefe en yakın (>= min_mesafe_m) yeterince güneşli düz piksel."""
    gecis = egim <= par.max_egim_deg
    etiket, _ = label(gecis, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    psr = (oran == 0.0) & (egim <= 5.0) & gecis
    if not psr.any():
        psr = (oran == 0.0) & gecis
    if not psr.any():
        raise RuntimeError("Ulaşılabilir örnekleme boyunca gölgeli hedef (oran=0) bulunamadı; --yari-km veya --faktor değiştirin, "
                           "ya da --hedef ile elle seçin.")
    rr, cc = np.mgrid[0:dem.shape[0], 0:dem.shape[1]]
    if bas is not None:
        L = etiket[bas]
        if L == 0:
            raise RuntimeError("Başlangıç noktasının eğimi limiti aşıyor; başka bir --inis/--bas seçin.")
        psr = psr & (etiket == L)
        if not psr.any():
            raise RuntimeError("Bu başlangıçtan ulaşılabilen örnekleme boyunca gölgeli hedef yok; --yari-km'yi büyütün ya da --hedef verin.")
        uzak = np.hypot(rr - bas[0], cc - bas[1]) * piksel_m
        aday = psr & (uzak >= 200.0)
        if not aday.any():
            aday = psr
        ai = np.argwhere(aday)
        return bas, tuple(int(v) for v in ai[np.argmin(uzak[aday])])
    sayim = np.bincount(etiket[psr], minlength=etiket.max() + 1)
    L = int(np.argmax(sayim))
    psr = psr & (etiket == L)
    merkez = np.array(dem.shape) / 2.0
    pi = np.argwhere(psr)
    hedef = tuple(int(v) for v in pi[np.argmin(np.hypot(pi[:, 0] - merkez[0], pi[:, 1] - merkez[1]))])
    uzak = np.hypot(rr - hedef[0], cc - hedef[1]) * piksel_m
    for esik in (0.5, 0.4, 0.3, 0.2, 0.1):
        aday = (oran >= esik * oran.max()) & (egim <= 5.0) & (uzak >= min_mesafe_m) & (etiket == L)
        if aday.any():
            ai = np.argwhere(aday)
            return tuple(int(v) for v in ai[np.argmin(uzak[aday])]), hedef
    raise RuntimeError("Uygun başlangıç bulunamadı; --bas ile elle seçin.")


# ======================================================================================
# 6) BATARYA SİMÜLASYONU
# ======================================================================================
def enerji_simulasyonu(dem, piksel_m, boylam, enlem, t0, sure_s, dt_s, konum_fn, mod_fn, par,
                       soc0=1.0, harita_dt_s=1800.0, crs=None, dur_kosulu=None, faz_sinirlari=()):
    """konum_fn(t_s)->(satır,sütun); mod_fn(t_s)->'hibernasyon'|'surus'|'operasyon'.
    Gölge/güç haritası harita_dt_s'de bir yenilenir. dur_kosulu(t_s, soc)->True ise erken biter.
    Not: Batarya 0'a inebilir ve geri toparlanabilir; gerçek rover bunu yapmaz (soc_min'i hata sayın)."""
    zaman = np.unique(np.r_[np.arange(0, sure_s, dt_s), faz_sinirlari, sure_s])
    n = len(zaman)
    soc, p_in, p_out, golgede = np.empty(n), np.empty(n), np.empty(n), np.empty(n, bool)
    E_Wh = soc0 * par.batarya_Wh
    guc, son, k_son = None, -1e18, n - 1
    for k, ts in enumerate(zaman):
        if guc is None or ts - son >= harita_dt_s:
            guc = _guc_haritasi(dem, piksel_m, boylam, enlem, t0 + timedelta(seconds=float(ts)), par, crs)
            son = ts
        r, c = konum_fn(ts)
        ri, ci = int(np.clip(round(r), 0, dem.shape[0] - 1)), int(np.clip(round(c), 0, dem.shape[1] - 1))
        pin, pout = float(guc[ri, ci]), par.tuketim_W(mod_fn(ts))
        soc[k], p_in[k], p_out[k], golgede[k] = E_Wh / par.batarya_Wh, pin, pout, pin == 0.0
        if dur_kosulu is not None and dur_kosulu(ts, soc[k]):
            k_son = k
            break
        if k + 1 < n:
            adim_s = zaman[k + 1] - ts
            E_Wh = min(par.batarya_Wh, max(0.0, E_Wh + (pin - pout) * adim_s / 3600.0))
    s = slice(0, k_son + 1)
    return {"zaman_s": zaman[s], "soc": soc[s], "p_in": p_in[s], "p_out": p_out[s], "golgede": golgede[s],
            "soc_son": E_Wh / par.batarya_Wh}
def golgede_dayanma_suresi_saat(par, mod="operasyon", soc0=1.0):
    """Güneş girişi yokken soc0'dan soc_min'e dayanma süresi (saat), basit analitik."""
    return (soc0 - par.soc_min) * par.batarya_Wh / par.tuketim_W(mod)


def gorev_simule(dem, ps, egim, boylam, enlem, t0, rota, par, soc0=1.0, kalis_saat=None,
                 max_sarj_saat=200.0, dt_s=600.0, crs=None):
    """Görev: başlangıç -> hedef (sürüş) -> hedefte kalış (operasyon) -> dönüş (sürüş) -> başlangıçta şarj."""
    rr, cc = np.array([p[0] for p in rota], float), np.array([p[1] for p in rota], float)
    t_node, uzunluk = rota_zamanlari(rota, dem, egim, ps, par)
    T1 = float(t_node[-1])                            # varış (gidiş süresi)
    gidis = lambda ts: (np.interp(ts, t_node, rr), np.interp(ts, t_node, cc))
    donus = lambda ts: (np.interp(T1 - ts, t_node, rr), np.interp(T1 - ts, t_node, cc))   # rotayı tersten izle

    def senaryo(kalis_h):
        """Verilen kalış süresi için konum/mod fonksiyonları ve faz sınırları (T2: dönüş başı, T3: başlangıca varış)."""
        T2 = T1 + kalis_h * 3600.0
        T3 = T2 + T1

        def konum(ts):
            if ts < T1: return gidis(ts)
            if ts < T2: return rr[-1], cc[-1]
            if ts < T3: return donus(ts - T2)
            return rr[0], cc[0]

        def mod(ts):
            if ts < T1 or T2 <= ts < T3: return "surus"
            if T1 <= ts < T2: return "operasyon"
            return "hibernasyon"
        return konum, mod, T2, T3

    def en_az_soc(kalis_h):
        konum, mod, T2, T3 = senaryo(kalis_h)
        s = enerji_simulasyonu(dem, ps, boylam, enlem, t0, T3, dt_s, konum, mod, par, soc0=soc0, crs=crs,
                              faz_sinirlari=(T1, T2, T3))
        return min(float(s["soc"].min()), s["soc_son"])

    # 1) Sadece gidiş: varış bataryası
    sim1 = enerji_simulasyonu(dem, ps, boylam, enlem, t0, T1, dt_s, gidis, lambda ts: "surus", par,
                              soc0=soc0, crs=crs)
    soc_varis = sim1["soc_son"]
    # 2) Gölgede kalış süresi: dönüş dahil batarya soc_min'in altına düşmeyecek en uzun süre (ikiye bölme)
    yeterli = en_az_soc(0.0) >= par.soc_min
    if kalis_saat is not None:
        kalis_h = float(kalis_saat)
    elif not yeterli:
        kalis_h = 0.0
    else:
        lo, hi = 0.0, max(0.0, (soc_varis - par.soc_min) * par.batarya_Wh / par.P_operasyon_W)
        if en_az_soc(hi) >= par.soc_min:
            lo = hi
        else:
            for _ in range(12):
                orta = (lo + hi) / 2
                lo, hi = (orta, hi) if en_az_soc(orta) >= par.soc_min else (lo, orta)
        kalis_h = lo
    konum, mod, T2, T3 = senaryo(kalis_h)

    sim = enerji_simulasyonu(dem, ps, boylam, enlem, t0, T3 + max_sarj_saat * 3600.0, dt_s, konum, mod, par,
                             soc0=soc0, crs=crs, faz_sinirlari=(T1, T2, T3), dur_kosulu=lambda ts, s: ts >= T3 and s >= 0.999)
    z = sim["zaman_s"]
    en_az = float(sim["soc"][z <= T3].min())
    sarj = float((z[-1] - T3) / 3600.0) if sim["soc"][-1] >= 0.999 and z[-1] >= T3 else None
    soc_at = lambda T: float(np.interp(T, z, sim["soc"]))
    ozet = {
        "baslangic_zamani_utc": t0.strftime("%Y-%m-%d %H:%M"),
        "rota_uzunluk_m": round(uzunluk, 1),
        "rota_maks_egim_deg": round(float(max(egim[p] for p in rota)), 1),
        "gidis_suresi_saat": round(T1 / 3600.0, 2),
        "soc_baslangic_pct": round(soc0 * 100, 1),
        "soc_varis_pct": round(soc_varis * 100, 1),
        "golgede_kalis_saat": round(kalis_h, 2),
        "donus_icin_yeterli_enerji": bool(en_az >= par.soc_min - 1e-9),
        "soc_donus_basinda_pct": round(soc_at(T2) * 100, 1),
        "soc_baslangica_varis_pct": round(soc_at(T3) * 100, 1),
        "gorev_boyunca_min_soc_pct": round(en_az * 100, 1),
        "soc_min_ihlali": bool(sim["soc"].min() < par.soc_min - 1e-9),
        "sarj_suresi_saat_(donustan_%100'e)": None if sarj is None else round(sarj, 1),
        "analitik_golgede_dayanma_operasyon_saat": round(golgede_dayanma_suresi_saat(par, "operasyon"), 1),
        "analitik_golgede_dayanma_hibernasyon_saat": round(golgede_dayanma_suresi_saat(par, "hibernasyon"), 1),
    }
    return sim, ozet, (T1, T2, T3)


def coklu_tur(dem, ps, egim, boylam, enlem, t0, rota, par, tur, soc0=1.0, kalis_saat=None, crs=None):
    """Döngü: karanlıkta çalış -> güneşli başlangıca dön, tam şarj ol -> tekrar git. 'tur' kez tekrarlar.
    Dönüş: (birleşik_sim, tur_özetleri, faz_zamanları[ofsetli])."""
    simler, ozetler, fazlar, ofset = [], [], [], 0.0
    t_cur, soc_cur = t0, soc0
    for i in range(tur):
        print(f"  Tur {i + 1}/{tur} simüle ediliyor ({t_cur:%Y-%m-%d %H:%M} UTC) ...")
        sim, ozet, (T1, T2, T3) = gorev_simule(dem, ps, egim, boylam, enlem, t_cur, rota, par, soc0=soc_cur,
                                               kalis_saat=kalis_saat, crs=crs)
        ozet["tur"] = i + 1
        simler.append((sim, ofset)); ozetler.append(ozet); fazlar.append((ofset + T1, ofset + T2, ofset + T3))
        sure = float(sim["zaman_s"][-1])
        ofset += sure
        t_cur = t0 + timedelta(seconds=ofset)
        soc_cur = float(sim["soc"][-1])
        if not ozet["donus_icin_yeterli_enerji"]:
            print("  UYARI: dönüş için yeterli enerji yok; tur döngüsü durduruldu.")
            break
        if ozet["soc_min_ihlali"]:
            print("  Şarj beklerken batarya rezervi ihlal edildi; yeni tur başlatılmadı.")
            break
        if ozet["sarj_suresi_saat_(donustan_%100'e)"] is None:
            print("  UYARI: başlangıç noktasında bu sürede tam şarj sağlanamadı; tur döngüsü durduruldu.")
            break
    birlesik = {k: np.concatenate([(s[k] + o) if k == "zaman_s" else s[k] for s, o in simler])
                for k in ("zaman_s", "soc", "p_in", "p_out", "golgede")}
    return birlesik, ozetler, fazlar


def en_iyi_zaman(boylam, enlem, t_ref, gun=30, adim_saat=6):
    """t_ref'ten itibaren 'gun' gün içinde ROI merkezinde güneşin en yüksek olduğu an."""
    adaylar = [t_ref + timedelta(hours=k * adim_saat) for k in range(int(gun * 24 / adim_saat))]
    return max(adaylar, key=lambda t: gunes_konumu(t, enlem, boylam)[0])


# ======================================================================================
# 7) DÜNYA GÖRÜNÜRLÜĞÜ, PÜRÜZLÜLÜK, KRATER KATALOĞU VE ROTA PROFİLİ
# ======================================================================================
AY_YARICAP_M = 1737400.0
DUNYA_YARICAP_KM = 6371.0


def dunya_konumu(t, enlem, boylam):
    """Dünya merkezinin yerel yatay koordinatları; Dünya diskinin yaklaşık açısal yarıçapı.

    SPICE zorunludur; yaklaşık Güneş modeliyle Dünya yönü hesaplanamaz.
    """
    if _SPICE is None:
        raise RuntimeError("Dünya görünürlüğü SPICE gerektiriyor. --analitik-gunes ile kullanılamaz.")
    et = _SPICE.str2et(_utc(t).strftime("%Y-%m-%d %H:%M:%S.%f UTC"))
    pos, _ = _SPICE.spkpos("EARTH", et, "MOON_ME", "LT+S", "MOON")
    phi, lam = math.radians(enlem), math.radians(boylam)
    up = np.array([math.cos(phi)*math.cos(lam), math.cos(phi)*math.sin(lam), math.sin(phi)])
    east = np.array([-math.sin(lam), math.cos(lam), 0.0])
    north = np.array([-math.sin(phi)*math.cos(lam), -math.sin(phi)*math.sin(lam), math.cos(phi)])
    # Ortalama referans küresi + anten yüksekliği: yükseklik DEM'den burada alınmıyor.
    v = np.asarray(pos, float) - (AY_YARICAP_M / 1000.0) * up
    yukseklik = math.degrees(math.atan2(np.dot(v, up), math.hypot(np.dot(v, east), np.dot(v, north))))
    azimut = math.degrees(math.atan2(np.dot(v, east), np.dot(v, north))) % 360.0
    acisal_yaricap = math.degrees(math.asin(min(1.0, DUNYA_YARICAP_KM / np.linalg.norm(v))))
    return float(yukseklik), float(azimut), float(acisal_yaricap)


def arazi_ufku(dem, ps, nokta, yon_xy, anten_m=2.0, adim_px=0.5):
    """Işın boyunca örneklenen arazi ufku (derece); Ay eğriliği yaklaşık düzeltmesi.

    ROI dışında arazi bilinmez: görünür sonucu yalnızca ROI içi içindir.
    DEM mutlak yükseklikleri aynı Ay referans küresine göre olmalıdır.
    """
    r0, c0 = nokta
    dx, dy = yon_xy
    nr, nc = dem.shape
    if not (0 <= r0 < nr and 0 <= c0 < nc):
        raise ValueError("Ufuk noktası DEM dışında")
    if not math.isfinite(dem[int(r0), int(c0)]):
        return float('nan'), 0.0
    v = np.array([dx, dy], float)
    v /= np.linalg.norm(v)
    # col -> +x; row -> -y
    c_end = ((nc-1-c0)/v[0]) if v[0] > 1e-12 else ((-c0)/v[0] if v[0] < -1e-12 else float('inf'))
    r_end = ((r0)/v[1]) if v[1] > 1e-12 else ((r0-(nr-1))/v[1] if v[1] < -1e-12 else float('inf'))
    max_px = min(c_end, r_end)
    if max_px <= 0:
        return -90.0, 0.0
    d_px = np.arange(max(adim_px, 0.5), max_px, max(adim_px, 0.5))
    if len(d_px) == 0:
        return -90.0, 0.0
    rr = r0 - d_px*v[1]
    cc = c0 + d_px*v[0]
    z = map_coordinates(dem.astype(float), [rr, cc], order=1, mode="nearest")
    d = d_px*ps
    # R + yerel merkez yüksekliği ~ ay küresel yarıçapı
    r_ay = AY_YARICAP_M + float(dem[int(r0), int(c0)])
    if r_ay <= 0:
        raise ValueError("Ay yarıçapı + DEM yükseklik değeri geçersiz")
    ek_egim = (z - (float(dem[int(r0), int(c0)]) + anten_m) - d*d/(2*r_ay))/d
    return float(np.degrees(np.arctan(np.max(ek_egim)))), float(d[-1])


def gorus_durumu(dem, ps, nokta, enlem, boylam, tarih, crs=None, anten_m=2.0):
    el, az, disk = dunya_konumu(tarih, enlem, boylam)
    yon = yatay_yon_grid(az, boylam, enlem, crs)
    ufuk, erisim_m = arazi_ufku(dem, ps, nokta, yon, anten_m=anten_m)
    # Ufukta disk kısmen görünüyorsa "kısmi"; dünyayı tek nokta kabul etmiyoruz.
    durum = ("bilinmiyor" if not math.isfinite(ufuk) else
             "tam_disk" if el-disk > max(ufuk, 0.0) else
             "kismi_disk" if el+disk > max(ufuk, 0.0) else "gorunmuyor")
    return dict(dunya_yukseklik_deg=round(el, 4), dunya_azimut_deg=round(az, 4),
                dunya_acisal_yaricap_deg=round(disk, 4), arazi_ufuk_deg=round(ufuk, 4),
                yukseklik_farki_deg=round(el-max(ufuk, 0.0), 4),
                gorus=durum, gorus_hatti_acik=(durum in ("tam_disk", "kismi_disk")),
                taranan_arazi_m=round(erisim_m, 1),
                uyari="ROI dışındaki dağlar/engebeler hesaba katılmadı; RF/DSN link bütçesi hesaplanmadı")


def grid_nokta_lonlat(nokta, boylam, enlem, ps, sekil, crs=None, kose=None):
    if crs is None or kose is None:
        return boylam, enlem  # yalnızca sentetik testte; gerçek yerel konum iddiası yok
    from pyproj import Transformer
    r, c = nokta
    x = kose[0] + (c + 0.5)*ps
    y = kose[1] - (r + 0.5)*ps
    lon, lat = Transformer.from_crs(crs, AY_PROJ, always_xy=True).transform(x, y)
    return float(lon), float(lat)


def yuzey_puruzlulugu(kaynak_dem, kaynak_ps, calisma_faktor, pencere_m=100.0):
    """Yerel detrend edilmiş yükselti standart sapması (m), engel yüksekliği değil.

    Önce yüksek çözünürlüklü DEM üzerinde hesapla, sonra maksimum blok değeri al.
    NoData çevresinde belirsizlik NaN kalır.
    """
    from scipy.ndimage import minimum_filter
    n = max(3, int(round(pencere_m/kaynak_ps)) | 1)
    a = np.asarray(kaynak_dem, dtype=float)
    finite = np.isfinite(a)
    v = np.where(finite, a, 0.0)
    count = uniform_filter(finite.astype(float), size=n, mode="nearest")
    local_mean = uniform_filter(v, size=n, mode="nearest") / np.maximum(count, 1e-12)
    # Detrend lineer düzlem yerine Gauss düşük frekans topoğrafyasını kaldırır.
    # Eğim etkisini azaltır ancak yönteme/pencereye bağımlıdır.
    residual = a - gaussian_filter(np.where(finite, a, np.nanmean(a[finite]) if finite.any() else 0), sigma=max(1.0, n/3))
    rr = np.where(finite, residual, 0.0)
    avg = uniform_filter(rr, size=n, mode="nearest")/np.maximum(count, 1e-12)
    avg2 = uniform_filter(rr*rr, size=n, mode="nearest")/np.maximum(count, 1e-12)
    rms = np.sqrt(np.maximum(avg2-avg*avg, 0.0))
    valid = minimum_filter(finite.astype('uint8'), size=n, mode='constant', cval=0).astype(bool)
    rms[~valid] = np.nan
    return blok_maksimum(rms.astype("float32"), calisma_faktor) if calisma_faktor > 1 else rms.astype("float32")


def krater_katalogu_oku(yol, crs, kose, ps, sekil):
    """Katalog CSV: lon,lat,radius_m [opsiyonel name]. Yalnızca kataloglu kraterler."""
    if not yol:
        return []
    if not crs or not kose:
        raise ValueError("Krater CSV koordinat eşlemesi için gerçek, projeksiyonlu DEM gerekli.")
    from pyproj import Transformer
    tr = Transformer.from_crs(AY_PROJ, crs, always_xy=True)
    sonuc=[]
    with open(yol, encoding="utf-8-sig", newline="") as f:
        for i, v in enumerate(csv.DictReader(f), 2):
            try:
                lon = float(v["lon"]); lat = float(v["lat"])
                radius = float(v["radius_m"])
                if not all(map(math.isfinite, [lon, lat, radius])) or radius <= 0:
                    raise ValueError("Geçersiz merkez/yarıçap")
                x,y = tr.transform(lon,lat)
                col=(x-kose[0])/ps-0.5; row=(kose[1]-y)/ps-0.5
                sonuc.append(dict(name=v.get("name") or f"krater_{i}", lon=lon,lat=lat,
                                  radius_m=radius, row=row, col=col, x_m=x,y_m=y))
            except (KeyError, ValueError) as e:
                raise ValueError(f"Krater CSV satır {i}: lon,lat,radius_m alanları zorunlu: {e}") from e
    return sonuc


def en_yakin_krater(nokta, kraterler, ps, kose=None):
    if not kraterler:
        return None
    r,c=nokta
    x=kose[0]+(c+0.5)*ps; y=kose[1]-(r+0.5)*ps
    a=min(kraterler,key=lambda k: math.hypot(x-k["x_m"],y-k["y_m"])-k["radius_m"])
    uzaklik=math.hypot(x-a["x_m"],y-a["y_m"])
    return dict(krater=a["name"], merkez_uzaklik_m=round(uzaklik,1),
                kenar_uzaklik_m=round(max(0,uzaklik-a["radius_m"]),1),
                krater_icerisinde=bool(uzaklik<a["radius_m"]),
                radius_m=a["radius_m"], lon=a["lon"],lat=a["lat"])


def rota_profili(rota, dem, ps, egim, puruz=None, kraterler=None, kose=None):
    d=0.0; out=[]
    for i,(r,c) in enumerate(rota):
        if i:
            pr,pc=rota[i-1]
            d+=math.hypot(ps*math.hypot(r-pr,c-pc),float(dem[r,c]-dem[pr,pc]))
        item=dict(sira=i, satir=r, sutun=c, mesafe_m=round(d,2), yukseklik_m=round(float(dem[r,c]),3),
                  egim_deg=round(float(egim[r,c]),3))
        if puruz is not None:
            item["puruzluluk_std_m"] = round(float(puruz[r,c]),3) if math.isfinite(puruz[r,c]) else None
        if kraterler:
            item["krater_kenar_uzaklik_m"]=en_yakin_krater((r,c),kraterler,ps,kose)["kenar_uzaklik_m"]
        out.append(item)
    return out


def ilave_analiz_kaydet(cikti, dem, ps, egim, puruz, rota, profil, t0, lon, lat, crs, kose,
                        anten_m, kraterler, iletisim_adim_saat, iletisim_gun):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from dataclasses import asdict
    os.makedirs(cikti, exist_ok=True)
    locs={}
    for ad,nokta in (("inis",rota[0]),("hedef",rota[-1])):
        lo,la=grid_nokta_lonlat(nokta,lon,lat,ps,dem.shape,crs,kose)
        locs[ad]=dict(nokta=nokta,lon=lo,lat=la,
                       **gorus_durumu(dem,ps,nokta,la,lo,t0,crs,anten_m))
        locs[ad]["en_yakin_krater"]=en_yakin_krater(nokta,kraterler,ps,kose)
        locs[ad]["puruzluluk_std_m"]=(round(float(puruz[nokta]),3) if math.isfinite(puruz[nokta]) else None)
    times=[]
    n=int(iletisim_gun*24/iletisim_adim_saat)
    for i in range(n):
        t=t0+timedelta(hours=i*iletisim_adim_saat)
        v={"utc":t.isoformat()}
        for ad,loc in locs.items():
            v[ad]=gorus_durumu(dem,ps,loc["nokta"],loc["lat"],loc["lon"],t,crs,anten_m)
        times.append(v)
    for ad,loc in locs.items():
        valid=[v[ad]["gorus_hatti_acik"] for v in times if v[ad]["gorus"]!="bilinmiyor"]
        loc["orneklenmis_gorunurluk_orani"] = round(sum(valid)/len(valid),4) if valid else None
    # 15 örnek noktada başlangıç zamanında görüş, rota boyunca uyarı niteliğinde.
    samples=sorted(set(np.linspace(0,len(rota)-1,num=min(15,len(rota)),dtype=int)))
    path_visibility=[]
    for i in samples:
        p=rota[i]; lo,la=grid_nokta_lonlat(p,lon,lat,ps,dem.shape,crs,kose)
        path_visibility.append({"sira":i,"mesafe_m":profil[i]["mesafe_m"],
                                **gorus_durumu(dem,ps,p,la,lo,t0,crs,anten_m)})
    with open(os.path.join(cikti,"rota_yukseklik_profili.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(profil[0]));w.writeheader();w.writerows(profil)
    with open(os.path.join(cikti,"dunya_gorunurluk.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["utc","inis_dunya_el_deg","inis_ufuk_deg","inis_gorus","hedef_dunya_el_deg","hedef_ufuk_deg","hedef_gorus"])
        for v in times:
            w.writerow([v["utc"],v["inis"]["dunya_yukseklik_deg"],v["inis"]["arazi_ufuk_deg"],v["inis"]["gorus"],
                        v["hedef"]["dunya_yukseklik_deg"],v["hedef"]["arazi_ufuk_deg"],v["hedef"]["gorus"]])
    out={"tarih_utc":t0.isoformat(),"parametreler":{"anten_yuksekligi_m":anten_m,
         "iletisim_ornekleme_saat":iletisim_adim_saat,"iletisim_gun":iletisim_gun,
         "krater_katalog_kaydi":len(kraterler),"krater_uzaklik_yontemi":"Krater kenarına projeksiyon düzleminde yaklaşık uzaklık",
         "puruzlulukk_yontemi":"Kaynak DEM yerel trend çıkarıldıktan sonra yükseklik std (m), blok maksimumu"},
         "konumlar":locs,"rota_gorus_ornekleri":path_visibility,
         "uyarilar":["Görüş fiziksel görüş hattıdır; anten yönelimi, link bütçesi, Dünya istasyonu, RF ve regolit etkileri dahil DEĞİL",
                    "ROI dışı topografya hesaba katılmadığı için görünür kararı kesin değildir",
                    "Dünya merkezine göre küresel yerel düşey ve yaklaşık Dünya diski kullanılır",
                    "Krater yakınlığı yalnızca sağlanan CSV kataloğundaki kraterlere göredir"],
         "iletisim_zaman_serisi":times}
    with open(os.path.join(cikti,"arazi_iletisim.json"),"w",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=lambda x: int(x) if isinstance(x,np.integer) else float(x))
    fig,ax=plt.subplots(2,2,figsize=(14,10))
    rr,cc=zip(*rota)
    m=ax[0,0].imshow(puruz,cmap="magma");ax[0,0].plot(cc,rr,"c-",lw=1.5)
    fig.colorbar(m,ax=ax[0,0],label="m (yerel std)");ax[0,0].set_title("Yüzey pürüzlülüğü (yaklaşık)")
    ax[0,1].plot([v["mesafe_m"]/1000 for v in profil],[v["yukseklik_m"] for v in profil]);
    ax[0,1].set(xlabel="Rota boyunca mesafe (km)",ylabel="DEM yüksekliği (m)",title="Rota yükseklik profili")
    xx=[i*iletisim_adim_saat/24 for i in range(len(times))]
    for ad,renk in (("inis","tab:blue"),("hedef","tab:orange")):
        ax[1,0].plot(xx,[v[ad]["dunya_yukseklik_deg"] for v in times],label=ad+" Dünya",color=renk)
        ax[1,0].plot(xx,[v[ad]["arazi_ufuk_deg"] for v in times],ls="--",alpha=.7,label=ad+" arazi ufku",color=renk)
    ax[1,0].axhline(0,color="black",lw=.5)
    ax[1,0].set(xlabel="Gün",ylabel="Yükseklik (°)",title="Dünya ve ufuk açısı");ax[1,0].legend(fontsize=8)
    for ad,renk in (("inis","tab:blue"),("hedef","tab:orange")):
        ax[1,1].step(xx,[int(v[ad]["gorus_hatti_acik"]) for v in times],where="post",label=ad,color=renk)
    ax[1,1].set(xlabel="Gün",ylabel="Görüş hattı (1 = açık)",ylim=(-.1,1.15),title="Dünya fiziksel görüşü (bağlantı garantisi değil)")
    ax[1,1].legend()
    fig.tight_layout();fig.savefig(os.path.join(cikti,"arazi_iletisim.png"),dpi=130);plt.close(fig)
    return out


# ======================================================================================
# 7) ÇIKTILAR
# ======================================================================================
def grafik_ciz(dem, ps, egim, oran, golge0, rota, sim, fazlar, par, baslik, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rr, cc = [p[0] for p in rota], [p[1] for p in rota]

    def rota_ciz(a):
        a.plot(cc, rr, "r-", lw=2); a.plot(cc[0], rr[0], "go", ms=9); a.plot(cc[-1], rr[-1], "y*", ms=15, mec="k")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10.5))
    a = ax[0, 0]
    a.imshow(tepe_golgeleme(dem, ps), cmap="gray")
    a.imshow(np.ma.masked_where(~golge0, golge0.astype(float)), cmap="Blues", alpha=0.55, vmin=0, vmax=1.3)
    rota_ciz(a); a.set_title("Arazi + başlangıç anı gölgesi (mavi) + rota\n(yeşil: başlangıç, sarı yıldız: hedef)")
    a = ax[0, 1]
    im = a.imshow(oran, cmap="YlOrRd", vmin=0, vmax=max(oran.max(), 1e-6)); rota_ciz(a)
    fig.colorbar(im, ax=a, fraction=0.046); a.set_title("Güneşli zaman oranı (30 gün); 0 = örneklenen anlarda güneş yok")
    a = ax[1, 0]
    im = a.imshow(egim, cmap="viridis", vmin=0, vmax=30); rota_ciz(a)
    fig.colorbar(im, ax=a, fraction=0.046); a.set_title(f"Eğim (°); rota limiti {par.max_egim_deg:.0f}°")
    a = ax[1, 1]
    t = sim["zaman_s"] / 3600.0
    a.fill_between(t, 0, 100, where=~sim["golgede"], color="orange", alpha=0.15, label="rover güneşte")
    a.plot(t, sim["soc"] * 100, "b", lw=2, label="batarya doluluğu")
    a.axhline(par.soc_min * 100, color="r", ls="--", lw=1, label="alt sınır")
    for i, faz in enumerate(fazlar):
        for T, ad in zip(faz, ("varış", "dönüş başı", "başlangıca varış")):
            a.axvline(T / 3600.0, color="k", ls=":", lw=1)
            if i == 0:
                a.text(T / 3600.0 - 0.4, 55, ad, rotation=90, va="center", ha="right", fontsize=8,
                       backgroundcolor="white")
    a.set(xlabel="saat (görev başından)", ylabel="%", ylim=(0, 100), title="Görev boyunca batarya")
    a.legend(loc="lower right")
    fig.suptitle(baslik, fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 0.97)); plt.savefig(yol, dpi=110); plt.close(fig)


def sonuclari_kaydet(klasor, ozetler, sim):
    os.makedirs(klasor, exist_ok=True)
    with open(os.path.join(klasor, "sonuc.json"), "w", encoding="utf-8") as f:
        json.dump({"turlar": ozetler}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(klasor, "zaman_serisi.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["saat", "soc_pct", "p_giris_W", "p_cikis_W", "golgede"])
        for z, s, pi, po, g in zip(sim["zaman_s"], sim["soc"], sim["p_in"], sim["p_out"], sim["golgede"]):
            w.writerow([round(z / 3600, 3), round(s * 100, 2), round(pi, 1), po, int(g)])


# ======================================================================================
# 8) KENDİ KENDİNİ TEST (internet gerekmez)
# ======================================================================================
def kendi_testi():
    global _GUNES_MODELI
    eski_model = _GUNES_MODELI
    _GUNES_MODELI = "analitik"  # İnternetsiz regresyon testleri
    ok = True

    def kontrol(ad, kosul, bilgi=""):
        nonlocal ok
        print(f"[{'OK ' if kosul else 'HATA'}] {ad} {bilgi}"); ok &= bool(kosul)

    el, _ = gunes_konumu(datetime(2023, 8, 23, 12, 33, tzinfo=UTC), -69.37, 32.32)
    kontrol("Chandrayaan-3 iniş anı güneş yüksekliği 5-10°", 5 <= el <= 10, f"(= {el:.1f}°)")
    lon_dolunay = gunes_alt_noktasi(datetime(2023, 8, 31, 1, 35, tzinfo=UTC))[1]
    kontrol("Dolunayda alt-güneş boylamı |x|<8°", abs(lon_dolunay) < 8, f"(= {lon_dolunay:.1f}°)")
    lon_yeni = gunes_alt_noktasi(datetime(2023, 8, 16, 9, 38, tzinfo=UTC))[1]
    kontrol("Yeni ayda alt-güneş boylamı ~±180°", abs(abs(lon_yeni) - 180) < 8, f"(= {lon_yeni:.1f}°)")
    mx = max(gunes_konumu(datetime(2026, 11, 14, tzinfo=UTC) + timedelta(hours=h), -85.4, 31.6)[0]
             for h in range(0, 24 * 30, 3))
    kontrol("85,4°G'de güneş en fazla 3-8°", 3 <= mx <= 8, f"(= {mx:.1f}°)")
    N, E = grid_yonleri(0.0, -85.0)
    kontrol("Analitik grid yönleri: boylam 0'da kuzey=+y, doğu=+x", np.allclose(N, (0, 1)) and np.allclose(E, (1, 0)))
    N, E = grid_yonleri(90.0, -85.0)
    kontrol("Analitik grid yönleri: boylam 90°D'de kuzey=+x, doğu=-y", np.allclose(N, (1, 0), atol=1e-9) and np.allclose(E, (0, -1), atol=1e-9))
    dem = np.zeros((200, 200), np.float32); dem[:, 100:104] = 50.0
    g = golge_haritasi(dem, 20.0, 5.0, (1.0, 0.0)); uz = int(g[100, :100].sum())
    kontrol("Duvar gölge uzunluğu (beklenen 28.6 px)", abs(uz - 28.6) <= 3, f"(= {uz} px)")
    g2 = golge_haritasi(dem, 20.0, 5.0, (-1.0, 0.0))
    kontrol("Güneş ters yönde: gölge doğuda", g2[100, 104:].sum() > 20 and g2[100, :100].sum() == 0)
    kontrol("Güneş ufuk altında: her yer gölge", golge_haritasi(dem, 20.0, -1.0, (1.0, 0.0)).all())
    par = RoverParam()
    y, x = np.mgrid[0:300, 0:300]
    tepe = (500 * np.exp(-((x - 150) ** 2 + (y - 150) ** 2) / (2 * 40.0 ** 2))).astype("float32")
    eg = egim_hesapla(tepe, 20.0)
    rota = a_yildiz(tepe, eg, 20.0, (5, 5), (294, 294), par)
    kontrol("A*: rota bulundu ve eğim limitine uyuyor", rota is not None and max(eg[p] for p in rota) <= par.max_egim_deg + 1e-6)
    kontrol("A*: kapalı hedef için None", a_yildiz(tepe, eg, 20.0, (5, 5), (150, 150), par) is None)
    sim = enerji_simulasyonu(np.zeros((50, 50), np.float32), 20.0, 31.0, -84.6, datetime(2026, 11, 14, tzinfo=UTC),
                             6 * 3600, 600, lambda t: (25, 25), lambda t: "hibernasyon", par, soc0=1.0)
    kontrol("Batarya: doluluk 0-1 arasında", 0 <= sim["soc"].min() and sim["soc"].max() <= 1.0)
    # Bağımsız SPICE örnekleri: DE421, moon_pa_de421_1900-2050,
    # moon_080317.tf, naif0012.tls; SUN/MOON, MOON_ME, LT+S, UTC.
    referans = [("2023-08-23T12:33", 1.322908), ("2026-02-14", -0.405925),
                ("2026-05-14", 1.478474), ("2026-08-14", 0.215128),
                ("2026-11-14", -1.557269), ("2026-11-27", -1.501204)]
    for tarih, beklenen in referans:
        lat, _ = gunes_alt_noktasi(datetime.fromisoformat(tarih))
        kontrol("SPICE deklinasyonu " + tarih, abs(lat - beklenen) < 0.05)

    duvar = np.zeros((24, 24), dtype=np.float32)
    duvar[:, 10] = 20
    ortalama, aralik = dem_kucult(duvar, 20, 4)
    _, blok = egim_guvenli(duvar, 20, 4)
    kontrol("İnce duvar blok maksimumunda korunur",
            np.nanmax(egim_hesapla(ortalama, aralik)) < 15 and np.all(blok[1:-1, 2] > 15)
            and a_yildiz(ortalama, blok, aralik, (2, 1), (2, 4), par) is None)
    duvar[5, 5] = np.nan
    _, blok = egim_guvenli(duvar, 20, 4)
    kontrol("Eksik iç piksel: iç bölgedeki yalnız ilgili bloğu kapatır",
            np.isnan(blok[1:-1, 1:-1]).sum() == 1 and np.isnan(blok[1, 1]))
    duvar[5, 4] = np.nan
    _, blok = egim_guvenli(duvar, 20, 4)
    kontrol("Sınırdaki eksik piksel komşu türevi de etkiler", np.isnan(blok[1, 0]))
    duz = np.zeros((2, 2))
    kontrol("Kapalı köşeden çapraz geçiş yok",
            a_yildiz(duz, np.array([[0, 20], [20, 0]]), 20, (0, 0), (1, 1), par) is None)

    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
    profil = dict(driver="GTiff", height=2, width=2, count=1, dtype="int16",
                  crs="+proj=stere +lat_0=-90 +lon_0=0 +R=1737400 +units=m",
                  transform=from_origin(1000, 2000, 20, 20))
    with MemoryFile() as mf, mf.open(**profil) as src:
        dem_geometri_kontrol(src)
        src.write(np.array([[-32768, 4], [8, 12]], dtype="int16"), 1)
        src.scales, src.offsets = (0.5,), (1,)
        src.set_band_unit(1, "m (reference sphere)")
        with warnings.catch_warnings(record=True) as kayit:
            warnings.simplefilter("always")
            deger = yukseklik_oku(src)
        kontrol("Etiketsiz dolgu ölçekten önce maskelenir",
                np.isnan(deger[0, 0]) and any("-32768" in str(w.message) for w in kayit))
        kontrol("Açıklamalı metre birimi, ölçek ve ofset", deger[1, 0] == 5)
    with MemoryFile() as mf, mf.open(**dict(profil, crs="EPSG:3857")) as src:
        try:
            dem_geometri_kontrol(src)
        except ValueError:
            kontrol("Dünya projeksiyonu reddedilir", True)
        else:
            kontrol("Dünya projeksiyonu reddedilir", False)
    print("\nTÜM TESTLER GEÇTİ" if ok else "\nBAZI TESTLER BAŞARISIZ")
    _GUNES_MODELI = eski_model
    return ok


# ======================================================================================
# 9) ANA AKIŞ
# ======================================================================================
def _nokta(s):
    r, c = s.split(","); return int(r), int(c)


def _lonlat(s):
    lo, la = s.split(","); return float(lo), float(la)


def main():
    ap = argparse.ArgumentParser(description="Ay Navigator (Mons Mouton / VIPER)")
    ap.add_argument("--test", action="store_true", help="analitik referanslarla çevrimdışı regresyon testi (gerçek SPICE testi değildir)")
    ap.add_argument("--kernel-dir", default="kernels", help="NASA SPICE çekirdekleri için klasör")
    ap.add_argument("--kernel-offline", action="store_true", help="SPICE çekirdeklerini indirme; sadece yerelden oku")
    ap.add_argument("--analitik-gunes", action="store_true", help="yalnızca açıkça istenen yaklaşık/demo güneş modeli")
    ap.add_argument("--sentetik", action="store_true", help="gerçek veri yerine sentetik krater demosu")
    ap.add_argument("--kes", nargs="?", const=LDEM_URL, help=f"DEM kaynağı (URL veya yerel .TIF); varsayılan: {LDEM_URL}")
    ap.add_argument("--dem", help="daha önce kesilmiş DEM (GeoTIFF); verilirse internete gerek yok")
    for ad in ("err", "effres"):
        ap.add_argument(f"--{ad}", help="DEM ile hizalı LOLA kalite GeoTIFF dosyası")
        ap.add_argument(f"--max-{ad}-m", type=float, help="Blokta izin verilen en yüksek değer (m)")
    ap.add_argument("--yenile", action="store_true", help="önbellekteki kesimi yok say, yeniden kes")
    ap.add_argument("--lon", type=float, default=VARSAYILAN_BOYLAM, help="ROI merkez boylamı (DOĞU +)")
    ap.add_argument("--lat", type=float, default=VARSAYILAN_ENLEM, help="ROI merkez enlemi (güney -)")
    ap.add_argument("--yari-km", type=float, default=10.0, help="kesim yarıçapı (km)")
    ap.add_argument("--inis", type=_lonlat, help="iniş noktası 'boylam,enlem' (örn 31.62,-85.42); rota buradan başlar")
    ap.add_argument("--tarih", help="görev başlangıcı UTC, örn 2026-11-27T00:00 (yoksa 30 gün içindeki en iyi an)")
    ap.add_argument("--faktor", type=int, help="DEM küçültme faktörü (gerçek DEM için varsayılan 4)")
    ap.add_argument("--bas", type=_nokta, help="başlangıç satır,sütun (küçültülmüş gridde)")
    ap.add_argument("--hedef", type=_nokta, help="hedef satır,sütun")
    ap.add_argument("--tur", type=int, default=1, help="karanlık-güneş döngüsü tekrar sayısı")
    ap.add_argument("--soc0", type=float, default=1.0)
    ap.add_argument("--kalis-saat", type=float, help="gölgede kalış süresini elle ver (yoksa enerjiye göre hesaplanır)")
    ap.add_argument("--panel-el", type=float, default=0.0, help="panel normal yüksekliği (0=dikey)")
    ap.add_argument("--cikti", default="cikti")
    ap.add_argument("--anten-m",type=float,default=2.0,help="Yerel anten yüksekliği (m)")
    ap.add_argument("--puruz-pencere-m",type=float,default=100.0,help="Pürüzlülük yerel pencere çapı (m)")
    ap.add_argument("--krater-csv",help="lon,lat,radius_m,name sütunlu krater kataloğu CSV")
    ap.add_argument("--iletisim-gun",type=float,default=30.0,help="Görüş hattı örnekleme süresi (gün)")
    ap.add_argument("--iletisim-adim-saat",type=float,default=6.0,help="Görüş hattı zaman adımı (saat)")
    ap.add_argument("--sadece-eski",action="store_true",help="Yeni arazi/iletişim analizlerini atla")
    a = ap.parse_args()

    if not 0 <= a.soc0 <= 1 or (a.kalis_saat is not None and not (math.isfinite(a.kalis_saat) and a.kalis_saat >= 0)):
        ap.error("Başlangıç doluluğu 0–1 arasında, kalış süresi sonlu ve sıfır veya pozitif olmalı.")
    if not (0 <= a.anten_m <= 100 and a.puruz_pencere_m > 0 and
            0 < a.iletisim_adim_saat <= 720 and 0 < a.iletisim_gun <= 365):
        ap.error("Anten/pürüzlülük/iletişim örnekleme parametreleri geçersiz")
    if a.analitik_gunes and not a.sadece_eski:
        ap.error("Dünya konumu için SPICE gerekir. --analitik-gunes ile --sadece-eski seçin.")
    if a.test:
        sys.exit(0 if kendi_testi() else 1)

    global _GUNES_MODELI
    if a.sentetik and a.analitik_gunes and not a.sadece_eski:
        ap.error("Sentetik analitik demoda --sadece-eski gerekli; Dünya hesabı SPICE ister")
    if a.analitik_gunes:
        _GUNES_MODELI = "analitik"
        print("UYARI: Yaklaşık analitik Güneş modeli kullanılıyor; gerçek zamanlı gölge güvenliği için uygun değildir.")
    else:
        spice_hazirla(kernel_dir=a.kernel_dir, offline=a.kernel_offline)

    par = RoverParam(panel_normal_el_deg=a.panel_el)
    crs, kose, ps0 = None, None, None
    if a.sentetik:
        dem, ps = sentetik_dem(); faktor = a.faktor or 1
        print("Sentetik krater demosu (GERÇEK VERİ DEĞİL)")
    else:
        dem_yolu = a.dem
        if not dem_yolu:
            dem_yolu = os.path.join(a.cikti, f"dem_v2_{a.lon:+.2f}_{a.lat:+.2f}_{a.yari_km:g}km.tif")
            os.makedirs(a.cikti, exist_ok=True)
            if os.path.exists(dem_yolu) and not a.yenile:
                print(f"Önbellekteki DEM kullanılıyor: {dem_yolu}  (yeniden kesmek için --yenile)")
            else:
                dem_kes(a.kes or LDEM_URL, a.lon, a.lat, a.yari_km * 1000.0, dem_yolu)
        dem, ps, crs, kose = dem_oku(dem_yolu)
        ps0, faktor = ps, (a.faktor or 4)
        print(f"DEM: {dem_yolu}  {dem.shape}  piksel={ps:g} m")
    kaynak_dem = dem
    if faktor < 1 or min(dem.shape) // faktor < 2:
        sys.exit("HATA: küçültme faktörü bu DEM için geçersiz.")
    kaynak_egim, egim = egim_guvenli(kaynak_dem, ps, faktor)
    dem, ps = dem_kucult(dem_doldur(kaynak_dem), ps, faktor)
    print(f"Kaynak eğimi >15°: {np.mean(kaynak_egim[np.isfinite(kaynak_egim)] > 15)*100:.2f}% (ölçülebilen pikseller)")
    print(f"Çalışma gridi: {dem.shape}, piksel={ps:g} m, eksik eğimli blok={np.isnan(egim).sum()}")
    boylam, enlem = a.lon, a.lat
    if crs:
        from pyproj import Transformer
        merkez_x = kose[0] + dem.shape[1] * ps / 2
        merkez_y = kose[1] - dem.shape[0] * ps / 2
        boylam, enlem = Transformer.from_crs(crs, AY_PROJ, always_xy=True).transform(merkez_x, merkez_y)
    print(f"Güneş hesabı için grid merkezi: {boylam:.6f}, {enlem:.6f}")
    arazi_egim = egim
    egim = egim.copy()
    kalite = {}
    for ad in ("err", "effres"):
        yol, limit = getattr(a, ad), getattr(a, f"max_{ad}_m")
        if limit is not None and (not yol or not math.isfinite(limit) or limit < 0):
            ap.error(f"--max-{ad}-m için --{ad} dosyası ve geçerli eşik gerekli.")
        if yol:
            if a.sentetik:
                ap.error("Kalite katmanı gerçek DEM gerektirir.")
            kalite[ad] = blok_maksimum(kalite_oku(yol, dem_yolu), faktor)
            if limit is not None:
                egim[~(kalite[ad] <= limit)] = np.nan

    inis_px = None
    if a.inis:
        if crs is None:
            sys.exit("HATA: --inis gerçek DEM ile kullanılır (sentetik demoda --bas kullanın).")
        try:
            inis_px = boylam_enlem_to_piksel(a.inis[0], a.inis[1], crs, kose, ps0, faktor, dem.shape)
        except ValueError as e:
            sys.exit(f"HATA: {e}")
        q = boylam_enlem_to_piksel(*a.inis, crs, kose, ps0, 1, kaynak_dem.shape)
        print(f"İniş {a.inis}: {ps0:g} m piksel {q}, yükseklik={kaynak_dem[q]:.2f} m, "
              f"eğim={kaynak_egim[q]:.2f}°; rota bloğu {inis_px} ({ps:g} m), maksimum eğim={arazi_egim[inis_px]:.2f}°")

    t_ref = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    if a.tarih:
        t0 = _utc(datetime.fromisoformat(a.tarih))
    else:
        t0 = en_iyi_zaman(boylam, enlem, t_ref); print("Tarih verilmedi: güneşin en yüksek olduğu an seçildi")
    el0, az0 = gunes_konumu(t0, enlem, boylam)
    print(f"Başlangıç: {t0:%Y-%m-%d %H:%M} UTC  güneş yüksekliği={el0:.1f}°  azimut={az0:.0f}°")

    print("30 günlük aydınlanma oranı hesaplanıyor ...")
    oran = aydinlanma_orani(dem, ps, boylam, enlem, t0, crs=crs)
    bas, hedef = (a.bas or inis_px), a.hedef
    for nokta in (bas, hedef):
        if nokta is not None and not (0 <= nokta[0] < dem.shape[0] and 0 <= nokta[1] < dem.shape[1]):
            sys.exit(f"HATA: seçilen nokta grid dışında: {nokta}")
    if bas is None or hedef is None:
        try:
            b2, h2 = otomatik_noktalar(egim, oran, dem, ps, par, bas=bas)
        except RuntimeError as e:
            sys.exit(f"HATA: {e}")
        bas, hedef = (bas or b2), (hedef or h2)
    print(f"Başlangıç piksel={bas} (güneşli oran {oran[bas]:.2f})  Hedef piksel={hedef} (güneşli oran {oran[hedef]:.2f})")

    golge0 = golge_haritasi(dem, ps, el0, yatay_yon_grid(az0, boylam, enlem, crs))
    rota = a_yildiz(dem, egim, ps, bas, hedef, par, golge=golge0)
    if rota is None:
        sys.exit("HATA: eğim limitine uyan rota yok. Başka bas/hedef seçin ya da --faktor değiştirin.")

    print("Görev simüle ediliyor ...")
    sim, ozetler, fazlar = coklu_tur(dem, ps, egim, boylam, enlem, t0, rota, par, max(1, a.tur), soc0=a.soc0,
                                     kalis_saat=a.kalis_saat, crs=crs)
    for oz in ozetler:
        for ad, katman in kalite.items():
            degerler = np.array([katman[q] for q in rota])
            sonlu = degerler[np.isfinite(degerler)]
            oz[f"rota_{ad}_maks_m"] = float(sonlu.max()) if sonlu.size else None
            oz[f"rota_{ad}_eksik_blok"] = int(degerler.size - sonlu.size)
    sonuclari_kaydet(a.cikti, ozetler, sim)
    if not a.sadece_eski:
        print("Pürüzlülük, Dünya görüşü, krater uzaklığı ve rota profili hesaplanıyor ...")
        puruz = yuzey_puruzlulugu(kaynak_dem,ps0 or ps,faktor,a.puruz_pencere_m)
        # Katalog verisi yoksa krater mesafesi bilinmiyor; DEM'den krater icat edilmez.
        kraterler = krater_katalogu_oku(a.krater_csv,crs,kose,ps,dem.shape)
        profil = rota_profili(rota,dem,ps,egim,puruz,kraterler,kose)
        ilave = ilave_analiz_kaydet(a.cikti,dem,ps,egim,puruz,rota,profil,t0,boylam,enlem,crs,kose,
                                   a.anten_m,kraterler,a.iletisim_adim_saat,a.iletisim_gun)
        for ad,loc in ilave["konumlar"].items():
            print(f"{ad}: Dünya el={loc['dunya_yukseklik_deg']:.2f}°, az={loc['dunya_azimut_deg']:.2f}°, "
                  f"arazi ufku={loc['arazi_ufuk_deg']:.2f}°, görüş={loc['gorus']}, "
                  f"pürüzlülük={loc['puruzluluk_std_m']} m, krater={loc['en_yakin_krater']}")
        print("Ek çıktılar: arazi_iletisim.png/json, dunya_gorunurluk.csv, rota_yukseklik_profili.csv")
    grafik_ciz(dem, ps, egim, oran, golge0, rota, sim, fazlar, par,
               f"Ay Navigator | {enlem:.1f}°, {boylam:.1f}° | başlangıç {t0:%Y-%m-%d %H:%M} UTC | "
               f"{len(ozetler)} tur | panel_el={par.panel_normal_el_deg}°",
               os.path.join(a.cikti, "ay_navigator.png"))
    for oz in ozetler:
        print(f"\n=== TUR {oz['tur']} ÖZETİ ===")
        for k, v in oz.items():
            if k != "tur":
                print(f"{k:45s}: {v}")
        if not oz["donus_icin_yeterli_enerji"]:
            print("UYARI: Bu kalış süresiyle gidiş-dönüşte batarya rezervi korunamıyor.")
    print(f"\nKaydedildi: {a.cikti}/ay_navigator.png, sonuc.json, zaman_serisi.csv")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as hata:
        sys.exit(f"HATA: {hata}")