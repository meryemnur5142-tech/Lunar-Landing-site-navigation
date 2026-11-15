#!/usr/bin/env python3
"""AY API: arayüz (UI) için tek giriş noktası.  ay_navigator.py ile AYNI klasörde durmalıdır.

Ne yapar?  Kullanıcının girdiği tarih-saat (UTC) için Mons Mouton / VIPER bölgesinde
  * en verimli 1. ve 2. iniş noktası, en riskli 1. ve 2. nokta (yüzdelerle),
  * her noktanın kriter kırılımı (eğim, pürüzlülük, iletişim, güneş, karanlık hedefe erişim, rölyef, veri güvenilirliği),
  * araç bilgi kutusu (kütle, batarya, panel, hız, dayanma süreleri),
  * güneş / Dünya / Ay bilgisi, en iyi noktalar için "karanlığa git-dön" enerji özeti,
  * her nokta için 2D harita görseli (PNG) ve tek bir JSON çıktısı üretir.

Arayüz tarafı kullanımı (Python):
    from ay_api import analiz
    sonuc = analiz("2026-11-27T00:00:00Z", cikti="cikti_arayuz")      # dict (JSON'a çevrilebilir)
Komut satırı:
    python ay_api.py --tarih 2026-11-27T00:00:00Z                     # gerçek NASA verisi + SPICE
    python ay_api.py --sentetik                                       # internetsiz DEMO (bilimsel geçerliliği YOK)
    python ay_api.py --test                                           # çevrimdışı kendi testleri

PUANLAMA (arayüze yazılacak tanım): Her kriter için skor s in [0,1]; s=1 "olabilecek en iyi" (kriterin %100 verimli
değeri), s=0 "kesinlikle inilmemesi gereken" değerdir. Verimlilik % = SUM(agirlik_i * s_i)  (agirliklar toplamı 100).
Risk % = 100 - Verimlilik %. Güneş ve iletişim, fiziksel olarak ulaşılamayan %100 yerine ROI içindeki EN İYİ konuma
göre normalize edilir; diğer kriterler mutlak sınırlara göredir. [V] ile işaretli eşikler takım varsayımıdır.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

import ay_navigator as nav

UTC = timezone.utc

# --------------------------------------------------------------------------------------
# AYARLAR
# --------------------------------------------------------------------------------------
VARSAYILAN_AGIRLIK = {          # toplam = 100 (takım kararı örnekleri: eğim 25-30, pürüzlülük 15-20, iletişim 15-20)
    "egim": 25.0,
    "puruzluluk": 20.0,
    "iletisim": 15.0,
    "gunes": 15.0,
    "karanlik_hedef": 10.0,
    "yerel_rolyef": 10.0,
    "veri_guvenilirligi": 5.0,
}
KRITER_ADI = {
    "egim": "Eğim", "puruzluluk": "Yüzey pürüzlülüğü", "iletisim": "Dünya ile iletişim (görüş)",
    "gunes": "Güneş aydınlanması (enerji)", "karanlik_hedef": "Karanlık (gölge) hedefe erişim",
    "yerel_rolyef": "Yerel yükselti farkı (rölyef)", "veri_guvenilirligi": "Veri güvenilirliği",
}
VARSAYILAN_AYAR = dict(
    iniş_egim_limiti_deg=15.0,         # [K] LUNA-AI gereksinimi: iniş elipsinde eğim <= 15°
    elips_yari_eksen_m=(500.0, 250.0), # [V] 500x250 m 3-sigma elips; yarı eksen kabul edildi (konservatif)
    puruz_limit_m=10.0,                # [V] 100 m pencerede detrend yükselti std'si; bu değerde skor 0
    rolyef_limit_m=100.0,              # [V] elips içi maksimum yükselti farkı; bu değerde skor 0
    dunya_min_el_deg=5.0,              # [V] LUNA-AI: Dünya yerel ufuktan en az 5° yüksekte
    karanlik_oran_esik=0.05,           # örneklenen sürenin %5'inden azında güneş görürse "karanlık hedef"
    aday_aralik_m=500.0, min_secim_aralik_m=1500.0,
    pencere_gun=30.0, adim_saat=6.0,
    nan_orani_max_en_iyi=0.10, nan_orani_max_riskli=0.50,
    yuzde_modu="mutlak",               # "mutlak": skorların kendisi | "goreli": ROI'deki en iyi=%100, en kötü=%0 olacak şekilde gerilir
)


class AnalizHatasi(RuntimeError):
    pass


# --------------------------------------------------------------------------------------
# YARDIMCILAR
# --------------------------------------------------------------------------------------
def _utc(t):
    if isinstance(t, str):
        t = datetime.fromisoformat(t.replace("Z", "+00:00"))
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t.astimezone(UTC)


def json_guvenli(x):
    if isinstance(x, dict):
        return {str(k): json_guvenli(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_guvenli(v) for v in x]
    if isinstance(x, np.ndarray):
        return json_guvenli(x.tolist())
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(float(x)) else None
    if isinstance(x, datetime):
        return x.isoformat()
    return x


def agirlik_dogrula(agirlik):
    if set(agirlik) != set(VARSAYILAN_AGIRLIK):
        raise ValueError(f"Kriterler şunlar olmalı: {sorted(VARSAYILAN_AGIRLIK)}")
    if any((not math.isfinite(v)) or v < 0 for v in agirlik.values()):
        raise ValueError("Ağırlıklar sonlu ve negatif olmayan sayılar olmalı")
    if abs(sum(agirlik.values()) - 100.0) > 1e-6:
        raise ValueError(f"Ağırlıkların toplamı 100 olmalı (şu an {sum(agirlik.values()):g})")
    return dict(agirlik)


def rover_bilgi(par=None):
    """Arayüzün köşesindeki 'sadece bilgi' kutusu için araç özeti."""
    par = par or nav.RoverParam()
    sat = lambda etiket, deger, birim, kaynak: dict(etiket=etiket, deger=deger, birim=birim, kaynak=kaynak)
    surus_saat = (1 - par.soc_min) * par.batarya_Wh / par.P_surus_W
    kutu = [
        sat("Araç", "VIPER (referans)", "", "K"),
        sat("Kütle", par.rover_kutlesi_kg, "kg", "K"),
        sat("Batarya kapasitesi", par.batarya_Wh, "Wh", "K"),
        sat("Güneş paneli (tek yüz, tepe)", par.panel_pik_W, "W", "K"),
        sat("Planlama hızı", par.hiz_ms, "m/s", "V"),
        sat("Maks. tırmanma eğimi", par.max_egim_deg, "°", "V"),
        sat("Karanlıkta çalışma (operasyon, %100→%{:.0f})".format(par.soc_min * 100),
            round(nav.golgede_dayanma_suresi_saat(par, "operasyon"), 1), "saat", "T"),
        sat("Karanlıkta hibernasyon", round(nav.golgede_dayanma_suresi_saat(par, "hibernasyon"), 1), "saat", "T"),
        sat("Sürüş (güneş girişi yok)", round(surus_saat, 1), "saat", "T"),
        sat("Sürüş menzili (güneşsiz, tek yön ayrılmış enerji ile)", round(menzil_maks_m(par) / 1000, 2), "km", "T"),
    ]
    return dict(kutu=kutu, parametreler=_par_dict(par),
                aciklama="K=NASA kaynaklı, T=kaynaktan türetilmiş, V=takım varsayımı")


def _par_dict(par):
    from dataclasses import asdict
    return asdict(par)


def menzil_maks_m(par):
    """Güneş girişi olmadan, enerjinin yarısı gidişe/yarısı dönüşe ayrılırsa tek yön sürüş menzili (m)."""
    return 0.5 * (1 - par.soc_min) * par.batarya_Wh / par.P_surus_W * par.hiz_ms * 3600.0


def ay_dunya_bilgi(t):
    """Dünya-Ay mesafesi ve Ay evresi (yalnızca SPICE yüklüyse)."""
    s = nav._SPICE
    if s is None:
        return None
    try:
        et = s.str2et(_utc(t).strftime("%Y-%m-%dT%H:%M:%S UTC"))
        ay_dunya, _ = s.spkpos("MOON", et, "J2000", "LT+S", "EARTH")
        gunes_ay, _ = s.spkpos("SUN", et, "J2000", "LT+S", "MOON")
        dunya_ay = -np.asarray(ay_dunya, float)
        cos_f = float(np.dot(dunya_ay, gunes_ay) / (np.linalg.norm(dunya_ay) * np.linalg.norm(gunes_ay)))
        return dict(dunya_ay_mesafe_km=round(float(np.linalg.norm(ay_dunya)), 1),
                    ay_evresi_aydinlik_orani=round((1 + cos_f) / 2, 4))
    except Exception as hata:  # bilgi amaçlı; ana analizi durdurmaz
        return dict(hata=str(hata))


def gunes_hazirla(model="spice", kernel_dir="kernels", offline=False):
    """Güneş/Dünya kaynağını seçer. 'spice': NASA/JPL SPICE (internet gerekir, ilk seferde çekirdek iner)."""
    if model == "analitik":
        nav._GUNES_MODELI = "analitik"
    elif model == "spice":
        nav._GUNES_MODELI = "spice"
        nav.spice_hazirla(kernel_dir=kernel_dir, offline=offline)
    else:
        raise ValueError("model 'spice' veya 'analitik' olmalı")


def demo_dunya_konumu(t, enlem, boylam):
    """SADECE DEMO/TEST: yaklaşık libron sinüsleriyle Dünya yönü. Gerçek değildir; faz bilinmiyor."""
    gun = (_utc(t) - datetime(2026, 1, 1, tzinfo=UTC)).total_seconds() / 86400.0
    lat_e = 6.68 * math.sin(2 * math.pi * gun / 27.212)
    lon_e = 7.9 * math.sin(2 * math.pi * gun / 27.555)
    phi, dlt, h = map(math.radians, (enlem, lat_e, boylam - lon_e))
    e = -math.cos(dlt) * math.sin(h)
    n = math.cos(phi) * math.sin(dlt) - math.sin(phi) * math.cos(dlt) * math.cos(h)
    u = math.sin(phi) * math.sin(dlt) + math.cos(phi) * math.cos(dlt) * math.cos(h)
    return (math.degrees(math.asin(max(-1.0, min(1.0, u)))), math.degrees(math.atan2(e, n)) % 360.0, 0.26)


# --------------------------------------------------------------------------------------
# VERİ HAZIRLAMA
# --------------------------------------------------------------------------------------
def dem_yukle(dem_yolu, lon, lat, yari_km, cikti, yenile=False):
    """Yerel DEM verilmediyse NASA PGDA COG'dan yalnızca ROI penceresini keser ve önbelleğe alır."""
    if not dem_yolu:
        os.makedirs(cikti, exist_ok=True)
        dem_yolu = os.path.join(cikti, f"dem_v2_{lon:+.2f}_{lat:+.2f}_{yari_km:g}km.tif")
        if yenile or not os.path.exists(dem_yolu):
            nav.dem_kes(nav.LDEM_URL, lon, lat, yari_km * 1000.0, dem_yolu)
    dem, ps, crs, kose = nav.dem_oku(dem_yolu)
    return dem, ps, crs, kose, dem_yolu


def grid_hazirla(kaynak_dem, ps0, faktor, puruz_pencere_m=100.0):
    """Çalışma gridi: eğim (kaynak çözünürlükte hesaplanıp blok MAKSİMUMU), küçültülmüş DEM, ölçüm oranı, pürüzlülük."""
    if faktor < 1 or min(kaynak_dem.shape) // faktor < 8:
        raise AnalizHatasi("Küçültme faktörü bu DEM için geçersiz (grid çok küçük kalır).")
    _, egim = nav.egim_guvenli(kaynak_dem, ps0, faktor)
    olcum, _ = nav.dem_kucult(np.isfinite(kaynak_dem).astype("float32"), ps0, faktor)
    dem, ps = nav.dem_kucult(nav.dem_doldur(kaynak_dem), ps0, faktor)
    puruz = nav.yuzey_puruzlulugu(kaynak_dem, ps0, faktor, puruz_pencere_m)
    return dict(dem=dem, ps=ps, egim=egim, olcum=olcum, puruz=puruz)


def elips_ofsetleri(ps, yari_a_m, yari_b_m, aci_deg=0.0):
    """Elips iç piksel ofsetleri (dr, dc) ve yarıçap (px). Uzun eksen aci_deg ile sütun (x) ekseni arasındadır."""
    ra, rb = yari_a_m / ps, yari_b_m / ps
    r = int(math.ceil(max(ra, rb))) + 1
    rr, cc = np.mgrid[-r:r + 1, -r:r + 1]
    th = math.radians(aci_deg)
    x = cc * math.cos(th) - rr * math.sin(th)
    y = cc * math.sin(th) + rr * math.cos(th)
    m = (x / ra) ** 2 + (y / rb) ** 2 <= 1.0
    dr, dc = rr[m].astype(int), cc[m].astype(int)
    if len(dr) == 0:
        dr, dc = np.array([0]), np.array([0])
    return dr, dc, r


def zaman_haritalari(dem, ps, lon, lat, crs, t0, gun, adim_saat, dunya_fn, dunya_min_el, gunes_fn=None):
    """Pencere boyunca (a) her pikselin güneş gördüğü zaman oranı, (b) Dünya'yı görme oranı, (c) t0 anındaki durumlar."""
    gunes_fn = gunes_fn or nav.gunes_konumu
    n = max(1, int(round(gun * 24.0 / adim_saat)))
    g_say, d_say = np.zeros(dem.shape), np.zeros(dem.shape)
    ilk = {}
    for k in range(n):
        t = t0 + timedelta(hours=k * adim_saat)
        el, az = gunes_fn(t, lat, lon)
        h = nav.yatay_yon_grid(az, lon, lat, crs)
        lit = ~nav.golge_haritasi(dem, ps, el, h) if el > 0 else np.zeros(dem.shape, bool)
        g_say += lit
        vis = np.zeros(dem.shape, bool)
        el_e = az_e = disk = None
        if dunya_fn is not None:
            el_e, az_e, disk = dunya_fn(t, lat, lon)
            if el_e >= dunya_min_el:
                vis = ~nav.golge_haritasi(dem, ps, el_e, nav.yatay_yon_grid(az_e, lon, lat, crs))
            d_say += vis
        if k == 0:
            ilk = dict(lit=lit, vis=vis, gunes_el=el, gunes_az=az, h_gunes=h, dunya_el=el_e, dunya_az=az_e,
                       dunya_disk=disk, h_dunya=(nav.yatay_yon_grid(az_e, lon, lat, crs) if az_e is not None else None))
    return g_say / n, (d_say / n if dunya_fn is not None else None), ilk, n


# --------------------------------------------------------------------------------------
# PUANLAMA
# --------------------------------------------------------------------------------------
def _p95(a):
    out = np.full(a.shape[0], np.nan)
    ok = np.isfinite(a).any(axis=1)
    if ok.any():
        out[ok] = np.nanpercentile(a[ok], 95, axis=1)
    return out


def _nanort(a):
    ok = np.isfinite(a).any(axis=1)
    out = np.full(a.shape[0], np.nan)
    if ok.any():
        out[ok] = np.nanmean(a[ok], axis=1)
    return out


def aday_metrikleri(G, ayar, oran_gunes, oran_dunya, ilk, karanlik_mesafe_m, err=None):
    """Aday noktalar (adım aralıklı ızgara) için elips içi ham metrikler. G = grid_hazirla çıktısı."""
    dem, ps = G["dem"], G["ps"]
    dr, dc, R = elips_ofsetleri(ps, *ayar["elips_yari_eksen_m"])
    nr, nc = dem.shape
    adim = max(1, int(round(ayar["aday_aralik_m"] / ps)))
    rows = np.arange(R, nr - R, adim)
    cols = np.arange(R, nc - R, adim)
    if len(rows) == 0 or len(cols) == 0:
        raise AnalizHatasi("ROI iniş elipsini sığdırmak için çok küçük; yarıçapı büyütün (--yari-km).")
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    rr, cc = rr.ravel(), cc.ravel()
    IR, IC = rr[:, None] + dr[None, :], cc[:, None] + dc[None, :]
    egim = G["egim"][IR, IC]
    z = dem[IR, IC]
    m = dict(
        satir=rr, sutun=cc,
        nan_orani=np.isnan(egim).mean(axis=1),
        egim_p95=_p95(egim),
        rolyef=z.max(axis=1) - z.min(axis=1),
        puruz=_nanort(G["puruz"][IR, IC]),
        olcum=G["olcum"][IR, IC].mean(axis=1),
        gunes_oran=oran_gunes[IR, IC].mean(axis=1),
        gunes_simdi=ilk["lit"][rr, cc] & (ilk["gunes_el"] > 0),
        karanlik_mesafe_m=karanlik_mesafe_m[rr, cc],
        egim_merkez=G["egim"][rr, cc],
    )
    if oran_dunya is not None:
        m["dunya_oran"] = oran_dunya[IR, IC].mean(axis=1)
        m["dunya_simdi"] = ilk["vis"][rr, cc]
    if err is not None:
        m["err_p95"] = _p95(err[IR, IC])
    return m


def skorlar(m, ayar, par, agirlik, oran_gunes, oran_dunya):
    """Kriter skorları (0..1), 1 = ideal. Bilinmeyen veri skoru 0 olur (UNKNOWN != SAFE)."""
    k = len(m["satir"])
    cl = lambda x: np.clip(np.nan_to_num(x, nan=0.0), 0.0, 1.0)
    s = {}
    s["egim"] = cl(1.0 - m["egim_p95"] / ayar["iniş_egim_limiti_deg"])
    s["puruzluluk"] = cl(1.0 - m["puruz"] / ayar["puruz_limit_m"])
    ref_g = max(float(np.nanpercentile(oran_gunes[np.isfinite(oran_gunes)], 99)), 1e-3)
    s["gunes"] = 0.5 * cl(m["gunes_oran"] / ref_g) + 0.5 * m["gunes_simdi"].astype(float)
    if "dunya_oran" in m:
        ref_d = max(float(np.nanpercentile(oran_dunya, 99)), 1e-3)
        s["iletisim"] = 0.5 * cl(m["dunya_oran"] / ref_d) + 0.5 * m["dunya_simdi"].astype(float)
    else:
        s["iletisim"] = np.zeros(k)
    menzil = menzil_maks_m(par)
    ideal = 0.25 * menzil
    d = m["karanlik_mesafe_m"]
    s["karanlik_hedef"] = np.where(np.isfinite(d), cl(1.0 - (d - ideal) / max(menzil - ideal, 1.0)), 0.0)
    s["yerel_rolyef"] = cl(1.0 - m["rolyef"] / ayar["rolyef_limit_m"])
    veri = cl((m["olcum"] - 0.8) / 0.2)
    if "err_p95" in m:
        veri = veri * cl(1.0 - m["err_p95"] / 5.0)          # [V] LOLA dikey belirsizlik 5 m'de skor 0
    s["veri_guvenilirligi"] = veri
    verim = sum(agirlik[a] * s[a] for a in agirlik)            # 0..100
    return s, verim


def sec_ayrik(sira, satir, sutun, ps, min_aralik_m, adet):
    """Sıralı aday indekslerinden birbirine en az min_aralik_m uzak 'adet' tanesini seçer (greedy NMS)."""
    secilen = []
    for i in sira:
        if all(math.hypot((satir[i] - satir[j]) * ps, (sutun[i] - sutun[j]) * ps) >= min_aralik_m for j in secilen):
            secilen.append(int(i))
            if len(secilen) == adet:
                break
    return secilen


# --------------------------------------------------------------------------------------
# GÖRSELLER
# --------------------------------------------------------------------------------------
def _gorsel_kes(G, r, c, yari_m):
    h = max(8, int(round(yari_m / G["ps"])))
    r0, r1 = max(0, r - h), min(G["dem"].shape[0], r + h + 1)
    c0, c1 = max(0, c - h), min(G["dem"].shape[1], c + h + 1)
    return r0, r1, c0, c1


def site_gorseli(yol, G, site, ilk, ayar, baslik, yari_m=2500.0, renk="tab:green"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Ellipse
    r, c = site["satir"], site["sutun"]
    r0, r1, c0, c1 = _gorsel_kes(G, r, c, yari_m)
    dem, ps = G["dem"], G["ps"]
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    ax.imshow(nav.tepe_golgeleme(dem, ps)[r0:r1, c0:c1], cmap="gray", extent=(c0 - .5, c1 - .5, r1 - .5, r0 - .5))
    sl = G["egim"][r0:r1, c0:c1]
    ax.imshow(np.ma.masked_where(~(sl > ayar["iniş_egim_limiti_deg"]), np.ones_like(sl)), cmap=ListedColormap(["red"]), alpha=0.45,
              extent=(c0 - .5, c1 - .5, r1 - .5, r0 - .5), vmin=0, vmax=1)
    ax.imshow(np.ma.masked_where(np.isfinite(sl), np.ones_like(sl)), cmap="Greys", alpha=0.6,
              extent=(c0 - .5, c1 - .5, r1 - .5, r0 - .5), vmin=0, vmax=1)
    gol = ~ilk["lit"][r0:r1, c0:c1]
    ax.imshow(np.ma.masked_where(~gol, np.ones(gol.shape)), cmap="Blues", alpha=0.4,
              extent=(c0 - .5, c1 - .5, r1 - .5, r0 - .5), vmin=0, vmax=1.3)
    a_m, b_m = ayar["elips_yari_eksen_m"]
    ax.add_patch(Ellipse((c, r), 2 * a_m / ps, 2 * b_m / ps, fill=False, ec=renk, lw=2.2))
    ax.plot([c], [r], "o", color=renk, mec="white", ms=7)
    L = 0.3 * (c1 - c0)
    for h, ad, rn in ((ilk["h_gunes"], "Güneş", "gold"), (ilk.get("h_dunya"), "Dünya", "deepskyblue")):
        if h is not None and (ad != "Güneş" or ilk["gunes_el"] > 0) and (ad != "Dünya" or (ilk["dunya_el"] or -1) > 0):
            ax.annotate("", xy=(c + L * h[0], r - L * h[1]), xytext=(c, r),
                        arrowprops=dict(arrowstyle="->", color=rn, lw=2.2))
            ax.text(c + 1.08 * L * h[0], r - 1.08 * L * h[1], ad, color=rn, fontsize=9, weight="bold")
    km = 1000.0 / ps
    ax.plot([c0 + 2, c0 + 2 + km], [r1 - 3, r1 - 3], "w-", lw=3); ax.text(c0 + 2, r1 - 5, "1 km", color="w", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(c0 - .5, c1 - .5); ax.set_ylim(r1 - .5, r0 - .5)
    ax.set_title(baslik, fontsize=11)
    fig.text(0.5, 0.01, "Kırmızı: eğim > {:g}°  |  gri: ölçüm yok  |  mavi: t0 anında gölge  |  elips: iniş hatası".format(
        ayar["iniş_egim_limiti_deg"]), ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(yol, dpi=130); plt.close(fig)


def genel_harita(yol, G, siteler, ilk, ayar):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(nav.tepe_golgeleme(G["dem"], G["ps"]), cmap="gray")
    from matplotlib.colors import ListedColormap
    ax.imshow(np.ma.masked_where(~(G["egim"] > ayar["iniş_egim_limiti_deg"]), np.ones(G["dem"].shape)),
              cmap=ListedColormap(["red"]), alpha=0.4, vmin=0, vmax=1)
    for s in siteler:
        renk = "lime" if s["tur"] == "en_verimli" else "red"
        ax.plot(s["sutun"], s["satir"], "o", color=renk, mec="white", ms=11)
        ax.text(s["sutun"] + 3, s["satir"] - 3, f"{s['id']} %{s['yuzde']:.0f}", color=renk, fontsize=10, weight="bold",
                bbox=dict(fc="black", alpha=0.5, pad=1))
    ax.set_title("Seçilen iniş noktaları (yeşil: verimli, kırmızı: riskli)"); ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)


# --------------------------------------------------------------------------------------
# ANA FONKSİYON
# --------------------------------------------------------------------------------------
def analiz(tarih_utc, *, dem_yolu=None, lon=nav.VARSAYILAN_BOYLAM, lat=nav.VARSAYILAN_ENLEM, yari_km=10.0, faktor=4,
           sentetik=False, cikti="cikti_arayuz", agirliklar=None, ayar=None, par=None, gunes_model="spice",
           kernel_dir="kernels", kernel_offline=False, err_yolu=None, gorev_adedi=2, gorsel=True, yenile=False,
           dunya_fn=None, gunes_fn=None, soc0=1.0, log=print):
    """Arayüzün çağıracağı ana fonksiyon. Dönüş: JSON'a çevrilebilir dict (aynı içerik cikti/arayuz_sonuc.json)."""
    t0 = _utc(tarih_utc)
    nav._GUC_ONBELLEK.clear()           # aynı id'li farklı DEM ile bayat güç haritası riskini önle
    agirlik = agirlik_dogrula(agirliklar or VARSAYILAN_AGIRLIK)
    A = dict(VARSAYILAN_AYAR, **(ayar or {}))
    par = par or nav.RoverParam()
    os.makedirs(cikti, exist_ok=True)
    uyarilar = []

    # 1) güneş/Dünya kaynağı
    if sentetik:
        nav._GUNES_MODELI = "analitik"
        dunya_fn = dunya_fn or demo_dunya_konumu
        uyarilar.append("SENTETİK DEMO: gerçek arazi/Dünya verisi değildir, bilimsel geçerliliği yoktur.")
    else:
        gunes_hazirla(gunes_model, kernel_dir, kernel_offline)
        if gunes_model == "analitik":
            uyarilar.append("Yaklaşık analitik güneş modeli kullanıldı; Dünya yönü için SPICE gerekir.")
        dunya_fn = dunya_fn or (nav.dunya_konumu if nav._SPICE is not None else None)
    if dunya_fn is None:
        raise AnalizHatasi("Dünya konumu için SPICE gerekli (gunes_model='spice').")

    # 2) DEM
    if sentetik:
        kaynak, ps0 = nav.sentetik_dem(n=300, piksel_m=40.0)
        crs = kose = None
        faktor = 1
        dem_kaynagi = "SYNTHETIC"
    else:
        log("DEM hazırlanıyor ...")
        kaynak, ps0, crs, kose, dem_kaynagi = dem_yukle(dem_yolu, lon, lat, yari_km, cikti, yenile)
    G = grid_hazirla(kaynak, ps0, faktor)
    err = None
    if err_yolu and not sentetik:
        err = nav.blok_maksimum(nav.kalite_oku(err_yolu, dem_kaynagi), faktor)
    dem, ps = G["dem"], G["ps"]
    if crs:
        from pyproj import Transformer
        lon_m, lat_m = Transformer.from_crs(crs, nav.AY_PROJ, always_xy=True).transform(
            kose[0] + dem.shape[1] * ps / 2, kose[1] - dem.shape[0] * ps / 2)
    else:
        lon_m, lat_m = lon, lat

    # 3) zaman boyunca güneş + Dünya haritaları
    log("Güneş ve Dünya görüş haritaları hesaplanıyor ...")
    oran_g, oran_d, ilk, n_ornek = zaman_haritalari(dem, ps, lon_m, lat_m, crs, t0, A["pencere_gun"], A["adim_saat"],
                                                    dunya_fn, A["dunya_min_el_deg"], gunes_fn)
    karanlik = oran_g <= A["karanlik_oran_esik"]
    if karanlik.sum() < 3:
        esik = float(np.nanpercentile(oran_g, 10))
        karanlik = oran_g <= esik
        uyarilar.append("Örneklenen pencerede (neredeyse) tamamen gölgeli piksel yok; en karanlık %10 hedef sayıldı.")
    from scipy.ndimage import distance_transform_edt
    kmesafe = distance_transform_edt(~karanlik) * ps

    # 4) adaylar ve puanlar
    log("Aday iniş noktaları puanlanıyor ...")
    M = aday_metrikleri(G, A, oran_g, oran_d, ilk, kmesafe, err)
    S, verim = skorlar(M, A, par, agirlik, oran_g, oran_d)
    risk = 100.0 - verim
    engelli = (M["egim_p95"] > A["iniş_egim_limiti_deg"]) | (M["nan_orani"] > A["nan_orani_max_en_iyi"]) | ~np.isfinite(M["egim_p95"])
    k_toplam = len(verim)

    iyi_ok = ~engelli
    if not iyi_ok.any():
        uyarilar.append("Hiçbir aday sert sınırları (eğim/veri) sağlamıyor; en iyi sıralama sınırları AŞAN adaylar arasındadır.")
        iyi_ok = M["nan_orani"] <= A["nan_orani_max_riskli"]
    kotu_ok = M["nan_orani"] <= A["nan_orani_max_riskli"]
    if A["yuzde_modu"] not in ("mutlak", "goreli"):
        raise ValueError("yuzde_modu 'mutlak' veya 'goreli' olmalı")
    ref = verim[kotu_ok] if kotu_ok.any() else verim
    v_min, v_max = float(ref.min()), float(ref.max())
    goreli = np.clip((verim - v_min) / max(v_max - v_min, 1e-9) * 100.0, 0.0, 100.0)   # 100 = ROI'deki en iyi aday
    sira_iyi = [i for i in np.argsort(-np.where(iyi_ok, verim, -np.inf)) if iyi_ok[i]]
    sira_kotu = [i for i in np.argsort(-np.where(kotu_ok, risk, -np.inf)) if kotu_ok[i]]
    iyi = sec_ayrik(sira_iyi, M["satir"], M["sutun"], ps, A["min_secim_aralik_m"], 2)
    kotu = sec_ayrik(sira_kotu, M["satir"], M["sutun"], ps, A["min_secim_aralik_m"], 2)
    if len(iyi) < 2 or len(kotu) < 2:
        uyarilar.append("ROI küçük olduğu için 2 + 2 ayrık nokta seçilemedi; --yari-km değerini büyütün.")

    def konum(i):
        return nav.grid_nokta_lonlat((int(M["satir"][i]), int(M["sutun"][i])), lon_m, lat_m, ps, dem.shape, crs, kose)

    def kayit(i, tur, sira):
        lo, la = konum(i)
        d = {}
        ham = {"egim": (M["egim_p95"][i], "° (elips içi %95)"), "puruzluluk": (M["puruz"][i], "m (100 m pencere std)"),
               "iletisim": (M.get("dunya_oran", np.full(k_toplam, np.nan))[i], "oran (Dünya görünür süre)"),
               "gunes": (M["gunes_oran"][i], "oran (güneşli süre)"),
               "karanlik_hedef": (M["karanlik_mesafe_m"][i], "m (en yakın karanlık hedef, düz mesafe)"),
               "yerel_rolyef": (M["rolyef"][i], "m (elips içi yükselti farkı)"),
               "veri_guvenilirligi": (M["olcum"][i], "oran (ölçülmüş piksel)")}
        for a in agirlik:
            d[a] = dict(ad=KRITER_ADI[a], agirlik=agirlik[a], skor=round(float(S[a][i]), 4),
                        puan=round(float(agirlik[a] * S[a][i]), 2), risk_puani=round(float(agirlik[a] * (1 - S[a][i])), 2),
                        ham_deger=(None if not math.isfinite(float(ham[a][0])) else round(float(ham[a][0]), 4)),
                        birim=ham[a][1])
        uy = []
        if M["egim_p95"][i] > A["iniş_egim_limiti_deg"]:
            uy.append("Elips içi eğim sınırı aşıyor")
        if M["nan_orani"][i] > A["nan_orani_max_en_iyi"]:
            uy.append("Elipste ölçülmemiş (NoData) piksel var")
        if not M["gunes_simdi"][i]:
            uy.append("Seçilen anda nokta gölgede veya Güneş ufkun altında")
        if "dunya_simdi" in M and not M["dunya_simdi"][i]:
            uy.append("Seçilen anda Dünya görünmüyor (eşik {:g}° + arazi ufku)".format(A["dunya_min_el_deg"]))
        return dict(id=f"{'V' if tur == 'en_verimli' else 'R'}{sira}", sira=sira, tur=tur, lon=round(lo, 5), lat=round(la, 5),
                    satir=int(M["satir"][i]), sutun=int(M["sutun"][i]),
                    verimlilik_yuzde=round(float(verim[i]), 1), risk_yuzde=round(float(risk[i]), 1),
                    verimlilik_goreli_yuzde=round(float(goreli[i]), 1), risk_goreli_yuzde=round(float(100.0 - goreli[i]), 1),
                    yuzde=round(float((verim[i] if A["yuzde_modu"] == "mutlak" else goreli[i]) if tur == "en_verimli"
                                      else (risk[i] if A["yuzde_modu"] == "mutlak" else 100.0 - goreli[i])), 1),
                    sert_sinir_asildi=bool(engelli[i]), kriterler=d, uyarilar=uy, gorsel_png=None)

    en_verimli = [kayit(i, "en_verimli", n + 1) for n, i in enumerate(iyi)]
    en_riskli = [kayit(i, "en_riskli", n + 1) for n, i in enumerate(kotu)]
    tum = en_verimli + en_riskli

    # 5) görseller
    if gorsel:
        gdir = os.path.join(cikti, "siteler"); os.makedirs(gdir, exist_ok=True)
        for s in tum:
            yol = os.path.join(gdir, f"{s['id']}.png")
            ad = "Verimli" if s["tur"] == "en_verimli" else "Riskli"
            bas = f"{ad} #{s['sira']}: %{s['yuzde']:.0f} {'verimlilik' if s['tur'] == 'en_verimli' else 'risk'}  ({s['lat']:.3f}°, {s['lon']:.3f}°D)"
            site_gorseli(yol, G, s, ilk, A, bas, renk="tab:green" if s["tur"] == "en_verimli" else "tab:red")
            s["gorsel_png"] = os.path.abspath(yol)
        genel = os.path.join(cikti, "genel_harita.png")
        genel_harita(genel, G, tum, ilk, A)
    else:
        genel = None

    # 6) en iyi noktalar için karanlığa git-dön görev özeti
    gorev = []
    for s in en_verimli[:max(0, gorev_adedi)]:
        gorev.append(dict(site_id=s["id"], **gorev_ozeti(G, s, oran_g, A, par, lon_m, lat_m, t0, crs, kose, soc0)))

    # 7) ortam bilgisi
    ortam = dict(tarih_utc=t0.isoformat(), bolge_merkez=dict(lon=round(lon_m, 5), lat=round(lat_m, 5)),
                 gunes=dict(yukseklik_deg=round(ilk["gunes_el"], 3), azimut_deg=round(ilk["gunes_az"], 2)),
                 dunya=(None if ilk["dunya_el"] is None else dict(yukseklik_deg=round(ilk["dunya_el"], 3),
                                                                 azimut_deg=round(ilk["dunya_az"], 2))),
                 alt_gunes_noktasi_yaklasik=dict(zip(("enlem_deg", "boylam_deg"), map(lambda v: round(v, 3), nav.gunes_alt_noktasi(t0)))),
                 ay_dunya=ay_dunya_bilgi(t0))
    cikti_d = dict(
        surum="1.0", tarih_utc=t0.isoformat(), sentetik_demo=bool(sentetik),
        rover_bilgi=rover_bilgi(par),
        ortam=ortam,
        puanlama=dict(agirliklar=agirlik, kriter_adlari=KRITER_ADI, ayarlar=A,
                      tanim="Verimlilik% = toplam(agirlik*skor); skor 1=ideal, 0=kesinlikle inilmemeli. Risk% = 100 - Verimlilik%. "
                            "'yuzde' alanı yuzde_modu'na göre mutlak veya göreli (ROI'deki en iyi %100) yüzdedir; ikisi de ayrı alanlarda var. "
                            "Güneş ve iletişim ROI içindeki en iyi konuma göre normalize edilir."),
        en_verimli=en_verimli, en_riskli=en_riskli, gorev_ozetleri=gorev,
        genel_harita_png=(os.path.abspath(genel) if genel else None),
        istatistik=dict(aday_sayisi=int(k_toplam), sert_sinir_asan_aday=int(engelli.sum()), zaman_ornek_sayisi=int(n_ornek),
                        pencere_gun=A["pencere_gun"], adim_saat=A["adim_saat"], grid_piksel_m=ps, grid_boyut=list(dem.shape)),
        veri_kaynaklari=dict(dem=dem_kaynagi, yatay_cozunurluk_m=ps0, gunes_dunya=("analitik/DEMO" if sentetik else
                             ("NASA/JPL SPICE (DE440, MOON_ME)" if nav._SPICE is not None else "analitik")),
                             pururluk="LOLA DEM'den yerel detrend std (kaya/regolit pürüzlülüğü DEĞİL)",
                             kayalik="Kaya (rock) haritası kullanılmadı"),
        uyarilar=uyarilar + [
            "LOLA 20 m DEM 0.3 m iniş pürüzlülüğünü veya <5 m kayaları ölçemez; sonuçlar ön eleme niteliğindedir.",
            "Dünya görünürlüğü fiziksel görüş hattıdır; RF link bütçesi/istasyon erişimi dahil değildir.",
            "ROI dışındaki arazi gölge/görüş hesabına katılmadı.",
            "Kaya, termal ve ShadowCam/PSR maskeleri bu sürümde yok (veri bulunmadığı için UNKNOWN)."])
    cikti_d = json_guvenli(cikti_d)
    with open(os.path.join(cikti, "arayuz_sonuc.json"), "w", encoding="utf-8") as f:
        json.dump(cikti_d, f, ensure_ascii=False, indent=2, allow_nan=False)
    return cikti_d


def gorev_ozeti(G, site, oran_g, A, par, lon, lat, t0, crs, kose, soc0):
    """Seçilen iniş noktasından en yakın ulaşılabilir karanlık hedefe git-dön + şarj simülasyonu (ay_navigator)."""
    dem, ps, egim = G["dem"], G["ps"], G["egim"]
    bas = (site["satir"], site["sutun"])
    oran0 = np.where(oran_g <= A["karanlik_oran_esik"], 0.0, np.maximum(oran_g, 1e-6))
    if not (oran0 == 0).any():
        oran0 = np.where(oran_g <= np.nanpercentile(oran_g, 10), 0.0, np.maximum(oran_g, 1e-6))
    try:
        _, hedef = nav.otomatik_noktalar(egim, oran0, dem, ps, par, bas=bas)
        el, az = nav.gunes_konumu(t0, lat, lon)
        golge0 = nav.golge_haritasi(dem, ps, el, nav.yatay_yon_grid(az, lon, lat, crs))
        rota = nav.a_yildiz(dem, egim, ps, bas, hedef, par, golge=golge0)
        if rota is None:
            return dict(durum="ROTA_YOK", neden="Eğim limitine uyan rota bulunamadı")
        sim, ozetler, _ = nav.coklu_tur(dem, ps, egim, lon, lat, t0, rota, par, 1, soc0=soc0, crs=crs)
    except RuntimeError as hata:
        return dict(durum="HEDEF_YOK", neden=str(hata))
    except Exception as hata:  # görev özeti ek bilgidir; ana sonucu düşürmesin
        return dict(durum="HATA", neden=f"{type(hata).__name__}: {hata}")
    oz = ozetler[0]
    adim = max(1, len(rota) // 150)
    yol = [list(nav.grid_nokta_lonlat(p, lon, lat, ps, dem.shape, crs, kose)) for p in rota[::adim]]
    return dict(durum=("TAMAM" if oz["donus_icin_yeterli_enerji"] and not oz["soc_min_ihlali"] else "ENERJI_YETERSIZ"),
                hedef_satir_sutun=list(hedef), hedef_lon_lat=list(nav.grid_nokta_lonlat(hedef, lon, lat, ps, dem.shape, crs, kose)),
                ozet=oz, rota_lon_lat=yol)


# --------------------------------------------------------------------------------------
# TEST
# --------------------------------------------------------------------------------------
def kendi_testi():
    import tempfile
    ok = True

    def kontrol(ad, kosul, bilgi=""):
        nonlocal ok
        print(f"[{'OK ' if kosul else 'HATA'}] {ad} {bilgi}"); ok &= bool(kosul)

    kontrol("Varsayılan ağırlıklar toplamı 100", abs(sum(VARSAYILAN_AGIRLIK.values()) - 100) < 1e-9)
    for kotu in ({**VARSAYILAN_AGIRLIK, "egim": 30.0}, {**VARSAYILAN_AGIRLIK, "egim": -5.0, "gunes": 45.0}, {"egim": 100.0}):
        try:
            agirlik_dogrula(kotu); kontrol("Hatalı ağırlık reddedilir", False)
        except ValueError:
            kontrol("Hatalı ağırlık reddedilir", True)
    dr, dc, r = elips_ofsetleri(40.0, 500.0, 250.0)
    kontrol("Elips ofsetleri simetrik ve merkezi içerir", ((dr == 0) & (dc == 0)).any() and dr.min() == -dr.max())
    kontrol("Elips uzun ekseni sütun yönünde (x)", dc.max() > dr.max())
    sat = np.array([0, 0, 0, 50]); sut = np.array([0, 5, 40, 0])
    kontrol("NMS ayrık seçer (40 px*40 m = 1600 m)", sec_ayrik([0, 1, 2, 3], sat, sut, 40.0, 1500.0, 3) == [0, 2, 3])
    km = menzil_maks_m(nav.RoverParam())
    kontrol("Menzil 2-4 km aralığında", 2000 < km < 4000, f"({km:.0f} m)")
    kutu = rover_bilgi()["kutu"]
    kontrol("Araç bilgi kutusu dolu", len(kutu) >= 8 and any(k["etiket"] == "Kütle" for k in kutu))

    with tempfile.TemporaryDirectory() as d:
        t = "2026-11-27T00:00:00Z"
        s = analiz(t, sentetik=True, cikti=d, log=lambda *a: None, gorev_adedi=1)
        kontrol("2 verimli + 2 riskli nokta", len(s["en_verimli"]) == 2 and len(s["en_riskli"]) == 2)
        kontrol("Verimli #1 >= #2 ve riskli #1 >= #2", s["en_verimli"][0]["verimlilik_yuzde"] >= s["en_verimli"][1]["verimlilik_yuzde"]
                and s["en_riskli"][0]["risk_yuzde"] >= s["en_riskli"][1]["risk_yuzde"])
        kontrol("En verimli > en riskli noktanın verimliliği", s["en_verimli"][0]["verimlilik_yuzde"] > s["en_riskli"][0]["verimlilik_yuzde"],
                f"({s['en_verimli'][0]['verimlilik_yuzde']} vs {s['en_riskli'][0]['verimlilik_yuzde']})")
        for x in s["en_verimli"] + s["en_riskli"]:
            kontrol(f"{x['id']}: yüzdeler 0-100, verim+risk=100, kriter puanları toplamı tutar",
                    0 <= x["yuzde"] <= 100 and abs(x["verimlilik_yuzde"] + x["risk_yuzde"] - 100) < 0.11
                    and abs(sum(k["puan"] for k in x["kriterler"].values()) - x["verimlilik_yuzde"]) < 0.6)
            kontrol(f"{x['id']}: görsel dosyası var", x["gorsel_png"] and os.path.getsize(x["gorsel_png"]) > 5000)
        kontrol("Genel harita var", os.path.exists(s["genel_harita_png"]))
        kontrol("JSON dosyası okunur", json.load(open(os.path.join(d, "arayuz_sonuc.json"), encoding="utf-8"))["surum"] == "1.0")
        pts = [(x["satir"], x["sutun"]) for x in s["en_verimli"] + s["en_riskli"]]
        kontrol("4 nokta birbirinden ayrık", len(set(pts)) == 4)
        kontrol("Görev özeti üretildi", len(s["gorev_ozetleri"]) == 1 and "durum" in s["gorev_ozetleri"][0],
                f"({s['gorev_ozetleri'][0]['durum'] if s['gorev_ozetleri'] else None})")
        # tarih değişince puanlar değişmeli (zamana duyarlılık)
        s2 = analiz("2026-12-05T06:00:00Z", sentetik=True, cikti=d, log=lambda *a: None, gorev_adedi=0, gorsel=False)
        kontrol("Farklı tarih farklı sonuç verir", s2["ortam"]["gunes"] != s["ortam"]["gunes"])
        s3 = analiz(t, sentetik=True, cikti=d, log=lambda *a: None, gorev_adedi=0, gorsel=False, ayar=dict(yuzde_modu="goreli"))
        kontrol("Göreli modda en verimli aday %100'e yakın", s3["en_verimli"][0]["yuzde"] >= 99.0,
                f"(= {s3['en_verimli'][0]['yuzde']})")
        kontrol("Göreli modda en riskli aday %100'e yakın", s3["en_riskli"][0]["yuzde"] >= 90.0,
                f"(= {s3['en_riskli'][0]['yuzde']})")
        try:
            analiz(t, sentetik=True, cikti=d, gorsel=False, gorev_adedi=0, ayar=dict(yuzde_modu="x"), log=lambda *a: None)
            kontrol("Geçersiz yüzde modu reddedilir", False)
        except ValueError:
            kontrol("Geçersiz yüzde modu reddedilir", True)
    print("\nTÜM TESTLER GEÇTİ" if ok else "\nBAZI TESTLER BAŞARISIZ")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Ay Navigator API: iniş noktası puanlama + arayüz JSON'u")
    ap.add_argument("--tarih", default="2026-11-27T00:00:00Z", help="UTC tarih-saat (ISO 8601)")
    ap.add_argument("--dem", help="yerel DEM GeoTIFF (yoksa NASA'dan ROI kesilir)")
    ap.add_argument("--err", help="LOLA hata (ERR) GeoTIFF, isteğe bağlı")
    ap.add_argument("--lon", type=float, default=nav.VARSAYILAN_BOYLAM)
    ap.add_argument("--lat", type=float, default=nav.VARSAYILAN_ENLEM)
    ap.add_argument("--yari-km", type=float, default=10.0)
    ap.add_argument("--faktor", type=int, default=4)
    ap.add_argument("--cikti", default="cikti_arayuz")
    ap.add_argument("--gunes", choices=("spice", "analitik"), default="spice")
    ap.add_argument("--kernel-dir", default="kernels")
    ap.add_argument("--kernel-offline", action="store_true")
    ap.add_argument("--sentetik", action="store_true")
    ap.add_argument("--yenile", action="store_true")
    ap.add_argument("--agirlik", help='JSON: {"egim":25,"puruzluluk":20,...} toplam 100')
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        sys.exit(0 if kendi_testi() else 1)
    ag = json.loads(a.agirlik) if a.agirlik else None
    s = analiz(a.tarih, dem_yolu=a.dem, lon=a.lon, lat=a.lat, yari_km=a.yari_km, faktor=a.faktor, sentetik=a.sentetik,
               cikti=a.cikti, agirliklar=ag, gunes_model=a.gunes, kernel_dir=a.kernel_dir, kernel_offline=a.kernel_offline,
               err_yolu=a.err, yenile=a.yenile)
    for grup in ("en_verimli", "en_riskli"):
        for x in s[grup]:
            print(f"{x['id']}  %{x['yuzde']:5.1f}  ({x['lat']:.4f}°, {x['lon']:.4f}°D)  {'; '.join(x['uyarilar'])}")
    print("Kaydedildi:", os.path.abspath(os.path.join(a.cikti, "arayuz_sonuc.json")))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as hata:
        sys.exit(f"HATA: {hata}")