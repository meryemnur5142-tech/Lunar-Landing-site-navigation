# status: draft
# owner: Agent D
# depends_on:
#   - docs/conops/CONOPS.md (§5 Yer-Araç Sınırı)
#   - docs/adr/ADR-006_Ground_Flight_Protokol.md
#   - autonomy/autonomy_matrix.md (iletişim kaybı matrisi)
#   - safety/fdir_implementation.md §4
#   - interfaces/schemas/earth_visibility_windows.schema.yaml
#   - infrastructure/repo_integration_map.md
#   - docs/qar/QAR_TABLE.md (COM-001..COM-006)
# open_items:
#   - TBD-COM-004: Frekans bandı seçimi (X-band vs Ka-band) — P-CRIT
#   - TBD-COM-005: TX gücü (W) — §10 güç alt sistemi
#   - TBD-COM-006: HGA kazancı (dBi) — §10 yapı alt sistemi
#   - TBD-COM-007: Hedef link marjı (dB)
#   - TBD-COM-008: Uplink veri hızı (bps)
#   - TBD-COM-009: Downlink telemetri veri hızı (bps)
#   - TBD-COM-010: Downlink bilim verisi veri hızı (bps)
#   - TBD-COM-011: SCLK-UTC drift toleransı (ms)
#   - TBD-COM-012: UTC senkronizasyon frekansı
#   - TBD-COM-013: Güney kutbu blackout periyot max süresi (saat)
#   - TBD-COM-014: Komut kimlik doğrulama mekanizması detayları

# Haberleşme Mimari Dokümanı — LUNA-AI

**Belge ID:** LUNA-AI-COM-F3-001
**Versiyon:** 0.1-draft
**Tarih:** 2026-11-14
**Sahip:** Agent D

---

## Mimari Genel Bakış

LUNA-AI yer-araç haberleşmesi, Ay mesafesinde (~384.400 km) gerçekleşmektedir.
Temel kısıtlar: yüksek ışık gecikmesi (~1,3 s tek yön), periyodik blackout, sınırlı bant genişliği ve radyasyon ortamında hata oranı.

**Protokol kararı (ADR-006):** CCSDS (Consultative Committee for Space Data Systems) benimsenmiştir.

| Katman | Standart | Amaç |
|--------|----------|------|
| Veri bağlantı | CCSDS TM/TC Sync & Channel Coding | Bit hata düzeltme (Reed-Solomon veya LDPC) |
| Paket | CCSDS Space Packet (133.0-B) | Telemetri ve bilim downlink |
| Komut | CCSDS Telecommand (232.0-B) | Uplink; öncelik ve ACK yerleşik |
| Dosya transferi | CCSDS CFDP (727.0-B) | Görev planı yükleme, yazılım güncelleme |

---

## 1. Link Budget

### 1.1 Frekans Bandı Trade-off: X-band vs Ka-band

Her iki band için avantaj/dezavantaj değerlendirmesi:

| Kriter | X-band (~8 GHz) | Ka-band (~26 GHz) |
|--------|----------------|-------------------|
| Kazanç (eşit anten boyutu) | Referans | ~10 dB fazla (λ daha kısa) |
| Veri hızı (eşit bant genişliği) | Daha düşük | Daha yüksek |
| Yönlendirme hassasiyeti | Daha toleranslı | Daha hassas (dar demet) |
| Yağış zayıflaması (Dünya istasyonu) | < 1 dB (10 GHz altı pratikte ihmal) | 3–10 dB (40 GHz'de; 26 GHz'de orta) |
| NASA DSN uyumluluğu | Birincil standart (34 m ve 70 m çanaklar) | DSN 34 m çanaklar destekler; Ka-band konfigürasyonu gerekir |
| Lunar heritage | LRO, VIPER, Chandrayaan-3 | LRO Ka-band deneme; Lunar Flashlight |
| Araç donanım olgunluğu | Yüksek (geniş tedarik zinciri) | Orta (küçük araçlar için daha yeni) |
| Serbest uzay yolu kaybı (aynı mesafe) | Daha az | Daha fazla (~10 dB) |

**Trade-off sonucu:** X-band birincil haberleşme bandı olarak önerilir; DSN uyumluluğu, bileşen olgunluğu ve yönlendirme toleransı nedeniyle. Ka-band yüksek veri hızı bilim downlink'i için ileride değerlendirilebilir (§10 anten boyutu ve güç bütçesiyle birlikte). Nihai karar: TBD-COM-004.

### 1.2 Anten Tipi Trade-off: HGA vs UHF Omni

| Kriter | HGA (High-Gain) | UHF Omni |
|--------|----------------|----------|
| Kazanç | Yüksek (20–35 dBi; anten boyutuna bağlı) | Düşük (~0–3 dBi) |
| Veri hızı | Yüksek (bilim verisi için gerekli) | Düşük; yalnızca beacon ve acil komut |
| Yönlendirme gereksinimi | Araç veya anten servo ile Dünya'ya yönelmeli | Yönlendirme gerektirmez (omnidirectional) |
| Kullanılabilirlik | Yalnızca Dünya görüş hattında ve anten yönelimi doğruysa | Her zaman |
| Redürdans rolü | Birincil yüksek hızlı kanal | Yedek/acil kanal |

**Mimari karar:** HGA + UHF omni çifti (redundancy_matrix.md referansı). HGA nominal telemetri ve bilim downlink'i için; UHF omni acil beacon, kurtarma komutu ve SURVIVAL modu için. UHF omni yalnızca `docs/architecture/SAFETY_STATE_MACHINE.md` SURVIVAL durumunda aktif kalır.

### 1.3 Link Budget Parametreleri

Tüm sayısal değerler §10 araç verisi beklenmektedir. Yapısal referans için `communication/link_budget_template.yaml` dosyasına bakınız.

| Parametre | Sembol | Birim | Durum |
|-----------|--------|-------|-------|
| Frekans bandı | f | GHz | TBD-COM-004 |
| TX gücü | P_tx | W | TBD-COM-005 |
| HGA kazancı | G_tx | dBi | TBD-COM-006 |
| Serbest uzay yolu kaybı (Ay mesafesi) | L_fs | dB | ~272 dB @ X-band; ~281 dB @ Ka-band |
| Alıcı gürültü figürü | NF | dB | TBD (DSN standartları) |
| Gerekli Eb/N0 | Eb/N0_req | dB | TBD (mod ve kodlama seçimine bağlı) |
| Hedef link marjı | M_link | dB | TBD-COM-007 (≥ 3 dB önerilir) |
| Uplink veri hızı | R_up | bps | TBD-COM-008 |
| Downlink telemetri veri hızı | R_down_tel | bps | TBD-COM-009 |
| Downlink bilim verisi veri hızı | R_down_sci | bps | TBD-COM-010 |

**QAR referansları:**
- QAR-COM-002: Telemetri güncelleme periyodu ≤ 10 s (nominal) → downlink veri hızı bu periyodu karşılamalı
- QAR-COM-003: Kritik durum telemetri ≤ 1 s → minimum bant genişliği boyutlandırmasını belirler
- QAR-COM-005: Komut bütünlüğü %100 (CRC hata tespiti) → CCSDS CRC-16/CCITT ile karşılanır

---

## 2. Relay Topolojisi

### 2.1 Doğrudan Dünya Bağlantısı

**Geometri kısıtı:** Ay güney kutbu (~89°S) sabit bir noktada değil; Ay yüzeyi Dünya'ya göre döner. Güney kutbunda yüzeyde duran bir araç için Dünya, ufkun yakınında (alçak elevasyonda) görünür.

- Tipik görünürlük oranı: Ay güney kutbu yakınında Dünya sürekli görünmez; birkaç derece elevasyonda kısmi görünürlük söz konusudur.
- `interfaces/schemas/earth_visibility_windows.schema.yaml` → `earth_visible` alanı ve `visibility_windows_next_7days` dizisi planlama için kullanılır.
- Pencere süresi ve frekansı: Orbital mekanik simülasyonu (SPICE DE440, lunar-navigator `pipeline/ephem/`) tamamlandığında kesinleşecektir. TBD-COM-013: güney kutbu için tipik maksimum blackout süresi.

**Link penceresi (CONOPS §6.2):** Günde yaklaşık 2–4 link penceresi, her pencere 15–45 dakika (varsayım; orbital mekanik analiziyle güncellenecek).

### 2.2 LunaNet / Relay Uydusu

NASA'nın planlanan LunaNet altyapısı (Lunar Gateway dahil) veya ticari relay uyduları, güney kutbu kapsama boşluklarını azaltabilir.

| Seçenek | Artı | Eksi | LUNA-AI için Durum |
|---------|------|------|--------------------|
| Doğrudan Dünya | Altyapı bağımsız | Blackout periyotları | Birincil mod |
| LunaNet relay | Kesintisiz (tasarım hedefi) | Erişilebilirlik belirsiz (görev tarihi TBD) | Fırsatçı; varsa kullan |
| Ticari relay (Intuitive Machines vb.) | Hızlı erişim | Maliyet, SLA | P2 değerlendirme |

**Relay ekstra gecikme:** Relay üzerinden ek yol: relay konumuna bağlı ~0.1–0.5 s ek gecikme.

### 2.3 Blackout Periyotları

Güney kutbu geometrisinde Dünya görünürlüğü kesintileri:

- `earth_visibility_windows.schema.yaml` → `longest_outage_duration_hours`: 60 günlük penceredeki en uzun kesinti süresi (kaynak: lunar-navigator 60-gün pencere analizi).
- Tipik güney kutbu Dünya blackout: Ay yörüngesi geometrisine bağlı; saatlerden onlarca saate çıkabilir. TBD-COM-013.
- Araç bu periyotlarda tamamen otonom çalışır (QAR-COM-004: ≥ TBD saatlik otonom çalışma).

### 2.4 Uyum Notu 6: Görünürlük ≠ Link Planlaması

`earth_visibility_windows.schema.yaml` açıkça belirtir:
> "Dünya ufukta görünür mü" (geometrik) ≠ haberleşme link planlaması (veri hızı/kuyruk) — ayrı katmanlar.

Bu ayrım korunmalıdır:

| Katman | Sorumlu Veri | Kaynak |
|--------|-------------|--------|
| **Geometrik görünürlük** | `earth_visible`, `next_change_time` | `earth_visibility_windows.schema.yaml` (SPICE ephem) |
| **Link kalitesi** | `link_margin_db`, `achieved_data_rate_bps` | Link budget hesabı; §10 donanım |
| **Kuyruk planlaması** | Downlink penceresinde hangi kuyruğun ne kadar bant alacağı | §4 Veri Kuyruk Yönetimi |

Görünürlük **gerekli koşuldur**; link kalitesi **yeterlilik koşuludur**. İkisi birbirinin yerine geçemez.

---

## 3. Gecikme Modeli

### 3.1 Işık Gecikmesi

Ay-Dünya ortalama mesafe: ~384.400 km

```
Tek yön ışık gecikmesi = 384.400.000 m / 299.792.458 m/s ≈ 1,282 s
Gidiş-dönüş (RTT) ≈ 2,56 s
```

Mesafe varyasyonu: Ay yörüngesi hafif eliptik (356.500–406.700 km arası). Gecikme aralığı: 1,19–1,36 s tek yön. SPICE DE440 bu varyasyonu doğru modeller.

### 3.2 Relay Ekstra Gecikme

Relay uydusu üzerinden:
- Relay konumuna (EML-1, EML-2, Ay etrafı yörünge) göre değişir.
- Tipik ek gecikme: 0,05–0,5 s (relay'in Dünya-Ay geometrisindeki konumuna bağlı).
- Toplam tek yön: 1,3 s + relay ekstra ≈ 1,4–1,8 s.

### 3.3 Komut İşleme Gecikmesi (Araç Tarafı)

QAR-COM-001: Komut işleme gecikmesi < 500 ms (komut alındı → icra edildi).

```
Toplam uçtan uca gecikme (nominal):
  Yer → araç tek yön ışık: ~1,28 s
  Araç komut işleme:        < 0,50 s (QAR-COM-001)
  ─────────────────────────────────
  Toplam (yer komutu → araç eylemi): < 1,78 s

Gidiş-dönüş onay süresi (ACK):
  Yer → araç + işleme + araç → yer: ~3,06 s minimum
```

**TC-IMMEDIATE komutları (P1):** CCSDS Telecommand öncelik alanı; yazılım kuyruklarını atlar. Araç donanım kesme seviyesinde işler.

### 3.4 Telemetri Gecikme Zinciri

```
Araç sensör ölçümü → paketleme → downlink gönderimi → Dünya alımı:
  Paketleme + kuyruk + RF iletim: araç tarafı < 1 s (nominal)
  Işık gecikmesi: ~1,28 s
  Yer alım + depaketleme: < 0,5 s
  ─────────────────────────────────
  Toplam: ~3 s (en kötü durum nominal)
```

QAR-COM-002: Telemetri güncelleme periyodu ≤ 10 s (nominal); bu gecikme dahil.
QAR-COM-003: Kritik durum ≤ 1 s araç tarafı gönderim; ışık gecikmesi hariç.

---

## 4. Veri Kuyruk Yönetimi

### 4.1 Öncelik Sırası

Downlink ve uplink kuyruklarında şu öncelik sıralaması uygulanır:

```
P1 (en yüksek): Abort komutu / TC-IMMEDIATE
P2: Güvenlik telemetrisi (CAUTION, RETURN_REQUIRED, SURVIVAL paketleri)
P3: Görev komutları (TC-CONDITIONAL, TC-PLAN, TC-PARAM)
P4: Nominal telemetri (subsistem durum güncellemeleri)
P5 (en düşük): Bilim verisi (büyük hacim; ertelenebilir)
```

CCSDS Telecommand `Priority` alanı bu sıralamayı doğrudan karşılar (ADR-006).

### 4.2 Kuyruk Tipleri

| Kuyruk | Yön | Boyut | TTL | Kayıp Stratejisi |
|--------|-----|-------|-----|-----------------|
| TC-IMMEDIATE | Uplink | Küçük (< 10 paket) | Sonsuz (alınana kadar retry) | Hiç kayıp olmaz; retry ile gönderilir |
| Güvenlik telemetrisi | Downlink | Orta (ring buffer, 100 paket) | 1 saat | En eski paket silinir (ring); en son durum korunur |
| Görev komutları | Uplink | Orta (50 paket) | 24 saat | FIFO; süresi geçenler silinir |
| Nominal telemetri | Downlink | Büyük (ring buffer, 1000 paket) | 2 saat | En eski paket silinir |
| Bilim verisi | Downlink | Çok büyük (flash depolama; TBD-COM-010 veri hızına bağlı) | 7 gün | Öncelikli bilim verisi korunur; düşük öncelikli üzerine yazılır |

Boyut değerleri TBD; §10 OBC belleği ve veri hızı kesinleştikten sonra güncellenecek.

### 4.3 Downlink Penceresi Kısıtlı Senaryosu

Link penceresi dar olduğunda bant genişliğinin kullanım sıralaması:

```
Link penceresi açıldı → downlink fırsatı:

1. Önce buffered güvenlik telemetrisi boşalt (tüm P2 paketler)
   [CONOPS §6.3 Kural 4: "Araç tamponlanmış tüm telemetriyi önce boşaltır"]
2. Nominal telemetri (P4): link kapasitesi kalıyorsa
3. Bilim verisi (P5): kalan kapasite; link bitmeden kesilir

Uplink kuyruğu:
1. TC-IMMEDIATE (varsa): derhal işle
2. TC-CONDITIONAL, TC-PLAN, TC-PARAM: FIFO sırasıyla
```

**Dar pencere durumunda kesim noktası:** Downlink penceresi kapanmadan önce P5 bilim verisi kesilir; P2 güvenlik telemetrisi asla kesilmez. Kesilmiş bilim verisi arabellekte TTL süresince tutulur; sonraki pencerede devam eder.

### 4.4 FDIR §4 ile Tutarlılık

`safety/fdir_implementation.md §4` (Haberleşme Kesintisi FDIR):
- Link timeout sayacı bu mimari ile tutarlı: araç tarafında link timeout = son başarılı downlink onayından itibaren süre.
- Recovery girişimi (retry): her TBD-COM-002 / TBD-COM-003 saniyede yeniden bağlantı girişimi; bu mimari katman FDIR'a timeout sinyali gönderir.
- SURVIVAL modunda: yalnızca UHF omni beacon aktif kalır; HGA ve yüksek veri hızı downlink kesilir.

---

## 5. Otonom Çalışma Kuralları (Link Yokken)

### 5.1 Devreye Girme Zamanı

İletişim kaybı detection → otonom çalışma geçişi:

```
link_timeout < TBD-COM-002 (uyarı eşiği):
  → Araç mevcut görev planını devam ettirir (CONOPS §6.3 Kural 1)
  → FDIR CAUTION tetikler (SAFETY_STATE_MACHINE CAUTION koşulları)
  → Retry başlar

link_timeout = TBD-COM-002 (uyarı eşiği) aşıldı:
  → Otonom mod tam aktif: Görev Planlayıcı ve FDIR bağımsız çalışır
  → Yeni risk alınmaz; PSR girişi BEKLE moduna girer

link_timeout = TBD-FDIR-006 (kritik eşik, COM-004) aşıldı:
  → RETURN_REQUIRED tetikler
  → Safe haven dönüşü başlar
```

### 5.2 Otonomi Matrisi İletişim Kaybı Hizalaması

Otonomi matrisi `autonomy/autonomy_matrix.md` İletişim Kaybı Matrisi ile tam uyum:

| Faz | Rota Değişikliği | PSR Girişi | Safe Haven Değişikliği | Acil Dönüş |
|-----|-----------------|------------|----------------------|------------|
| SURFACE_EXPLORATION | OTN | BEKLE (bekleme süresi: TBD-COM-003) | OTN (yedek listeden) | ACL |
| PSR_OPS | OTN (sınır içi) | YAS | ACL (enerji kritik + tıkandıysa) | ACL |
| RETURN | OTN | YAS | OTN | ACL |
| SAFE_STATE | YAS | YAS | ACL | ACL |

**PSR içinde link yok + enerji kritik:** Otonomi matrisi özel durumu:
> "ACL acil dönüş tetiklenir. FDIR → RETURN_REQUIRED geçişi → Power Mgmt dönüş rezervi onaylar → Planner rota üretir."

### 5.3 Pre-Planned Abort Trigger Listesi

Link kaybıyla ilgili abort trigger'lar (otonomi matrisi ABT serisi):

| Trigger | Koşul | Referans |
|---------|-------|---------|
| ABT-004 | `link_timeout > TBD-PLAN-008` AND `faz=PSR_OPS` AND `energy_critical=true` | Otonomi matrisi; `fdir_implementation.md §4.3` |
| ABT-001 | `return_reserve_wh < HC-006.threshold` (link durumundan bağımsız tetikler) | Her fazda; `mission_planner.md §6.2` |

**Link yokken kural özeti (CONOPS §6.3):**
1. Araç aktif görev planını devam ettirir — yeni risk almaz, PSR girişi yapmaz.
2. Durum makinesi CAUTION'da kalır; RETURN_REQUIRED kendi tetikleyicileriyle olur.
3. Otonom karar alma yetkisi tam aktif.
4. Link penceresi açılınca tamponlanmış tüm telemetri önce boşaltılır, ardından yeni komut alınır.
5. Çakışan komut + otonom karar: TC-IMMEDIATE her zaman önce; diğerleri FDIR onayından geçer.

### 5.4 `fdir_implementation.md §4.3` ile Çapraz Referans

`safety/fdir_implementation.md §4.3` "Pre-planned autonomous behavior" akışı bu mimarinin doğrudan uygulama tarafıdır:
- A.1: Otonom mod aktif; görev planı yerel kopyadan devam → §5.2 SURFACE_EXPLORATION OTN
- A.3: Retry girişimi (TBD-COM-003 saniyede) → §4.4 retry mekanizması
- A.4: `link_timeout_extended` → RETURN_REQUIRED → §5.1 kritik eşik aşımı

---

## 6. Zaman Mimarisi

### 6.1 SCLK (Spacecraft Clock)

**Format:** 64-bit sayaç; yüksek çözünürlüklü donanım saatinden beslenir.

```
SCLK yapısı (CCSDS CUC formatı önerisi):
  - Coarse time:  32-bit tam sayı (saniye)
  - Fine time:    16-bit alt saniye (1/65536 saniye çözünürlük ≈ 15 µs)
  - Toplam: 48-bit etkin; ek alanlar CCSDS başlık uzantısıyla taşınır
```

**Çözünürlük:** ≤ 1 ms (donanım bağımlı; TBD-COM-011 ile belirlenir).
**Telemetri damgalama:** Tüm telemetri paketleri SCLK zaman damgası ile gönderilir. UTC'ye dönüşüm yer segmentinde SCLK kernel ile yapılır (aşağıya bkz.).

### 6.2 UTC Senkronizasyon

**Yöntem:** CCSDS Time Distribution mesajı (uplink üzerinden gönderilir); araç SCLK-UTC korelasyon parametrelerini günceller.

**Frekans:** Her link penceresi başlangıcında (TBD-COM-012); en azından günde bir kez.

**SCLK-UTC drift toleransı:** TBD-COM-011. Referans: QAR-NAV-003 (konum güncelleme ≥ 10 Hz); zaman damgası tutarsızlığı navigasyon çıktılarını etkiler.

**Drift kaynakları:**
- Araç donanım osilatör termal değişimi (PSR gibi uç sıcaklıklarda)
- Radyasyon kaynaklı osilatör frekans kayması

### 6.3 SPICE SCLK Kernel

**Kaynak:** lunar-navigator `infrastructure/repo_integration_map.md` → `pipeline/ephem/` SPICE DE440 pipeline.

```
SCLK kernel güncelleme stratejisi:
  1. Yer segmenti: Her link penceresinde güncel SCLK korelasyon parametrelerini hesapla
  2. SPICE SCLK kernel (.tsc dosyası) yeni korelasyon noktasıyla güncellenir
  3. Güncellenen kernel yer segmenti arşivinde saklanır (görev sonrası analiz için)
  4. Araç tarafında SCLK kernel kullanılmaz; araç yalnızca donanım sayacını çalıştırır
  5. Tüm SCLK→UTC dönüşümleri yer segmentinde yapılır (SPICE CSPICE kütüphanesi)
```

**Efemeris geçerlilik aralığı:** `earth_visibility_windows.schema.yaml` → `ephemeris_validity_range` alanı; 2024–2035 aralığı (TBD-TIME-001 görev tarihi bu aralıkta seçilir).

### 6.4 Telemetri Event Zaman Damgalama

**Politika:** Araç tarafından üretilen tüm telemetri paketleri **SCLK** ile damgalanır.

**Gerekçe:**
- UTC senkronizasyon gecikmesi veya drift SCLK'yı etkilemez (donanım sayacı sürekli çalışır)
- SCLK→UTC dönüşümü kayıpsız yapılır (yer segmentinde kernel ile)
- UTC damgalama araç tarafında yapılsaydı: drift ve senkronizasyon hatası telemetriyi doğrudan kirletirdi

**Yer segmenti işlemi:** Telemetri alındığında SPICE `sct2e` fonksiyonu ile SCLK → ephemeris time (ET) → UTC dönüşümü yapılır.

---

## 7. Komut Authentication

### 7.1 Mevcut Durum (ADR-006)

ADR-006: Başlangıçta yalnızca **CCSDS CRC-16/CCITT** bütünlük kontrolü uygulanır. CRC, tek bit hata tespiti garantisi sağlar (QAR-COM-005: %100 CRC hata tespiti).

Şifreleme / authentication: CCSDS Security Layer (355.0-B) ilerleyen fazda değerlendirilecek (ADR-006 §Sonuçlar madde 3).

### 7.2 Hedef Authentication Mekanizması

Yetkisiz komut önleme için önerilen mimari:

```
Uplink Komut Kimlik Doğrulama Zinciri:

1. Yer segmenti: Her komut paketi → HMAC-SHA256 imzası ekle
   - Anahtar: paylaşılan gizli anahtar (yer + araç fabrika yüklü)
   - Mesaj: Komut içeriği + SCLK zaman damgası (replay saldırısı önlemi)

2. Araç: HMAC-SHA256 doğrulama
   - Anahtar eşleşiyor + SCLK farkı < tolerans → komut geçerli
   - Doğrulama başarısız → komut reddedilir; FDIR uyarısı

3. TC-IMMEDIATE (P1): HMAC doğrulaması kesme seviyesinde; < 10 ms (QAR-PWR-004 ile analoji)
4. Diğer komutlar: Normal işlem kuyruğunda doğrulama
```

**Replay saldırısı koruması:** Komut SCLK zaman damgası + monoton artan sıra numarası. Araç son N sıra numarasını önbellekte tutar; tekrar eden sıra → reddet.

**Anahtar yönetimi:** TBD-COM-014. Olası yaklaşımlar: (a) sabit fabrika anahtarı (basit, düşük risk Ay görevinde), (b) görev başında yer uplink ile anahtar değişimi. Karar §10 güvenlik analizi sonrasında.

### 7.3 CCSDS Security Layer (355.0-B) Yol Haritası

| Faz | Authentication Seviyesi |
|-----|------------------------|
| P1 (mevcut taslak) | CRC-16 bütünlük kontrolü |
| P2 | HMAC-SHA256 imza (§7.2) |
| P3 | CCSDS Security Layer 355.0-B; AES-256 şifreleme |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent D görev D4 (F3-1) |
