# LUNA-AI Güvenlik Durum Makinesi Tasarımı

**Belge ID:** LUNA-AI-ARCH-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı ADR:** ADR-005  
**Bağlı QAR:** FDIR-001, FDIR-002, FDIR-004, FDIR-005

---

## 1. Durum Tanımları

### NOMINAL

Araç tam operasyonel kapasitede çalışmaktadır. Tüm subsistemler kabul edilen parametre aralıklarındadır.

**İzlenen Parametreler:**
- SoC > dönüş eşiği + güvenlik marjı (bkz. QAR PWR-001)
- Navigasyon konum belirsizliği < 0.5 m RMS (NAV-001)
- Tüm kritik bileşen sıcaklıkları nominal aralıkta (THM-004/005)
- Haberleşme link_timeout sayacı < eşik (COM-004)
- Tüm FDIR heartbeat'leri zamanında alınıyor

**İzin Verilen Eylemler:**
- PSR girişi (tüm PSR giriş koşulları sağlanmış ise)
- Tam hız keşif operasyonu
- Bilimsel sensör operasyonu
- Yeni görev planı alma ve uygulama
- Rota replanning

---

### CAUTION

Bir veya daha fazla parametre gözlem aralığında (erken uyarı) ancak henüz kritik eşikte değil. Araç operasyona devam eder fakat risk artmıştır.

**Tetikleyiciler (aşağıdakilerden herhangi biri):**
- SoC < %25 veya öngörülen dönüş marjı < %20
- Navigasyon belirsizliği 0.5–1.0 m RMS
- Herhangi bir bileşen sıcaklığı uyarı aralığında (nominal limitin %80'i)
- Haberleşme link yokluğu > **TBD:** dakika (uyarı eşiği)
- Mission Planner heartbeat gecikmeli (uyarı eşiği; kritik değil)

**İzin Verilen Eylemler:**
- Devam eden operasyon tamamlanır (güvenli son noktaya kadar)
- Yeni PSR girişi yok
- Replanning önceliklendirilir (dönüş rotası hazır tutulur)
- Yer segmentine CAUTION flag gönderilir

**Kısıtlanan Eylemler:**
- Yeni PSR girişi başlatılamaz
- Yüksek güç tüketimli bilimsel operasyon başlatılamaz

---

### RETURN_REQUIRED

Araç güvenli dönüşe başlamalıdır. Devam etmek kabul edilemez risk taşımaktadır.

**Tetikleyiciler (aşağıdakilerden herhangi biri):**
- SoC < %15 (PWR-001) veya öngörülen dönüş enerjisi yetersiz
- Haberleşme link yokluğu > **TBD:** dakika (kritik eşik, COM-004)
- Navigasyon lokalizasyon kaybı recovery başarısız > **TBD:** saniye
- Yer segmentinden RETURN_REQUIRED komutu (TC-IMMEDIATE)
- Termal kritik devam ediyor ve lokal müdahale başarısız

**İzin Verilen Eylemler:**
- Safe haven'a dönüş rotası hesaplama ve icra
- Navigasyon ve FDIR tam çalışır durumda
- Haberleşme aktif (uplink varsa)
- Checkpoint kaydetme

**Kısıtlanan Eylemler:**
- Bilimsel operasyon tamamen dondurulur
- Keşif rotası devam ettirilmez
- PSR girişi kesinlikle yasak

---

### SURVIVAL

Görev kaybı veya araç kaybı riski yüksektir. Tüm kaynaklar hayatta kalma için yönlendirilir.

**Tetikleyiciler (aşağıdakilerden herhangi biri):**
- SoC < %10
- Kritik donanım arızası (hareket kontrol, termal, birincil navigasyon)
- Hızlı aşırı ısınma: **TBD:** °C/dak üzerinde sıcaklık artışı
- FDIR kendi iç heartbeat'ini kaybetti (self-watchdog)
- Çoklu eş zamanlı P1 arızası

**İzin Verilen Eylemler:**
- Navigasyon (minimum moda düşürülmüş: IMU + dead-reckoning)
- FDIR (çekirdek işlevi)
- Haberleşme (minimum güçte beacon)
- Minimum ısıtma (pil koruma)

**Kesilen Yükler:**
- Tüm bilimsel sensörler
- Yüksek güçlü haberleşme (yalnızca beacon kalır)
- Planlayıcı ve replanning hesaplamaları
- Kamera, LiDAR (navigasyon için değil)
- Panel servo (son pozisyonda kilitlenir)

---

## 2. Durum Geçiş Koşulları

```
NOMINAL ──────────────────────► CAUTION
 │  enerji_uyarı OR nav_uyarı OR termal_uyarı OR link_uyarı
 │
 ├──────────────────────────────► RETURN_REQUIRED
 │  SoC < %15 OR link_kritik OR nav_kayıp_timeout OR yer_komutu
 │
 └──────────────────────────────► SURVIVAL
    SoC < %10 OR kritik_arıza OR hızlı_ısınma

CAUTION ──────────────────────► NOMINAL
 │  tüm parametreler nominal aralığa döndü
 │
 ├──────────────────────────────► RETURN_REQUIRED
 │  herhangi bir RETURN tetikleyicisi aktif
 │
 └──────────────────────────────► SURVIVAL
    herhangi bir SURVIVAL tetikleyicisi aktif

RETURN_REQUIRED ──────────────► SURVIVAL
 │  dönüş sırasında SURVIVAL tetikleyicisi aktif
 │
 └──────────────────────────────► NOMINAL  [yalnızca yer onayı ile]
    safe haven'a ulaşıldı AND enerji yeterli AND yer segmenti onayladı

SURVIVAL ─────────────────────► RETURN_REQUIRED [yalnızca yer onayı ile]
    temel sistem kurtarıldı AND enerji > %10 AND yer segmenti onayladı
```

> **Not:** SURVIVAL'dan doğrudan NOMINAL'e geçiş yoktur. Araç her zaman RETURN_REQUIRED üzerinden geçer ve yer segmentinin açık onayı gerekir.

### Sayısal Eşik Referans Tablosu

| Parametre | CAUTION Eşiği | RETURN_REQUIRED Eşiği | SURVIVAL Eşiği |
|-----------|--------------|----------------------|---------------|
| SoC | < %25 | < %15 | < %10 |
| Nav. Belirsizlik | 0.5–1.0 m RMS | > 1.0 m RMS kayıp | — |
| Link Kesintisi | > **TBD** dak (uyarı) | > **TBD** dak (kritik) | — |
| Sıcaklık | Nominal limitin %80'i | Nominal limitin dışı | Hızlı artış > **TBD** °C/dak |
| SoC Tahmin Marjı | < %20 dönüş marjı | < %15 dönüş marjı | < %10 toplam SoC |

---

## 3. Watchdog Tasarımı

### 3.1 Heartbeat Gönderen Modüller

Her kritik FreeRTOS görevi, FDIR watchdog kuyruğuna düzenli heartbeat mesajları gönderir:

| Modül | Heartbeat Periyodu | Timeout Eşiği | Timeout Sonucu |
|-------|-------------------|---------------|----------------|
| Navigasyon | 100 ms | 500 ms | CAUTION → nav heartbeat kaybı |
| Güç Yönetimi | 500 ms | 2 s | CAUTION → güç heartbeat kaybı |
| Termal Yönetimi | 1 s | 5 s | CAUTION → termal heartbeat kaybı |
| Hareket Kontrolü | 100 ms | 500 ms | CAUTION → hareket heartbeat kaybı |
| Mission Planner | 2 s | 10 s | CAUTION (planlayıcı donduruldu — FDIR bağımsız çalışır) |
| Haberleşme | 5 s | 30 s | CAUTION → haberleşme heartbeat kaybı |

**FDIR kendi watchdog döngüsü:**
- FDIR, ayrı bir donanım watchdog timer'a heartbeat gönderir
- FDIR kendisi donduğunda donanım watchdog sistemi yeniden başlatır
- Yeniden başlatma sonrası FDIR CAUTION'dan başlar, geçmişi değerlendirir

### 3.2 Watchdog Uygulaması

```
FDIR_Task (Priority: Highest)
│
├── Heartbeat monitor loop (her 50 ms kontrol)
│   └── Subsistem heartbeat kayıt tablosunu kontrol et
│       → Timeout var mı? → Durum geçişini tetikle
│
├── Durum makinesi değerlendirme
│   → Mevcut durum + tüm tetikleyici sinyalleri
│   → Geçiş tablosunu uygula
│   → Yeni durum aktivasyonu
│
└── Donanım watchdog kick (her 25 ms)
    → Kaçırılırsa: donanım reset → FDIR yeniden başlar
```

---

## 4. FDIR Bağımsızlık Gereksinimleri

FDIR, görev yürütme kararlarını Mission Planner'a bırakır; ancak güvenlik kararları FDIR'ın münhasır yetkisindedir.

### 4.1 FDIR ile Mission Planner Arasında Paylaşılmayanlar

| Kaynak / Veri | Neden Paylaşılmaz |
|---------------|-------------------|
| FDIR durum makinesi çalışma zamanı durumu | Planner hatası FDIR'ı etkilememeli |
| Watchdog timer kayıtları | Tamper riski; sadece FDIR okur |
| SURVIVAL modu güç kesim listesi | Planner devre dışıyken bile çalışmalı |
| Donanım watchdog kick sinyali | FDIR'ın kendi döngüsüne ait |
| Kesmesi zor olmayan kritik donanım arayüzleri | Planner komutuna gerek yok |

### 4.2 FDIR ile Mission Planner Arasında Paylaşılanlar (ICD ile)

| Veri | Yön | ICD | Açıklama |
|------|-----|-----|----------|
| `safety_status` | FDIR → Planner | ICD-004 | Mevcut güvenlik durumu |
| `abort_signal` | FDIR → Planner | ICD-004 | Planner tüm operasyonları dondurur |
| Planner heartbeat | Planner → FDIR | — | Planner sağlık bildirimi |
| `fdir_caution_event` | FDIR → Planner | ICD-004 | Planner kısıtlanan eylem listesini günceller |

### 4.3 Bağımsız Çalışma Senaryosu

Mission Planner donduğunda FDIR şunları bağımsız yapabilir:
- Durum geçişi (NOMINAL → RETURN_REQUIRED)
- Temel hareket durdurma komutu (Hareket Kontrolüne doğrudan)
- Güç kesme komutu (Güç Yönetimine doğrudan)
- Navigasyona minimum moda geçiş komutu
- Haberleşmeye acil beacon komutu

---

## 5. PlantUML Durum Diyagramı

```plantuml
@startuml LUNA-AI Safety State Machine

[*] --> NOMINAL : boot_complete AND subsystems_ok

state NOMINAL {
  NOMINAL : Tüm subsistemler nominal
  NOMINAL : PSR girişine izin verilir
  NOMINAL : Tam keşif operasyonu
  NOMINAL : İzlenen: SoC, nav, termal, link, heartbeat
}

state CAUTION {
  CAUTION : Erken uyarı durumu
  CAUTION : Yeni PSR girişi yasak
  CAUTION : Mevcut operasyon tamamlanır
  CAUTION : Dönüş rotası hazır tutulur
}

state RETURN_REQUIRED {
  RETURN_REQUIRED : Dönüş zorunlu
  RETURN_REQUIRED : Bilimsel operasyon donduruldu
  RETURN_REQUIRED : Safe haven rotası aktif
}

state SURVIVAL {
  SURVIVAL : Hayatta kalma modu
  SURVIVAL : Yalnızca nav + FDIR + beacon aktif
  SURVIVAL : Tüm opsiyonel yükler kesildi
}

NOMINAL --> CAUTION : enerji_uyarı OR nav_uyarı OR\ntermal_uyarı OR link_uyarı
NOMINAL --> RETURN_REQUIRED : SoC < 15% OR link_kritik OR\nnav_kayıp OR yer_komutu
NOMINAL --> SURVIVAL : SoC < 10% OR kritik_arıza OR\nhızlı_ısınma

CAUTION --> NOMINAL : tüm_parametreler_nominal\n[tüm_tetikleyiciler_temiz]
CAUTION --> RETURN_REQUIRED : RETURN tetikleyicisi aktif
CAUTION --> SURVIVAL : SURVIVAL tetikleyicisi aktif

RETURN_REQUIRED --> SURVIVAL : SURVIVAL tetikleyicisi aktif
RETURN_REQUIRED --> NOMINAL : safe_haven_ulaşıldı AND\nenerji_yeterli AND yer_onayı

SURVIVAL --> RETURN_REQUIRED : temel_sistem_kurtarıldı AND\nenerji > 10% AND yer_onayı

note right of SURVIVAL
  SURVIVAL'dan NOMINAL'e
  doğrudan geçiş yoktur.
  Yer segmenti onayı zorunludur.
end note

note right of FDIR
  FDIR her durumda çalışır.
  Mission Planner'dan bağımsızdır.
  Donanım watchdog: 25 ms kick.
end note

@enduml
```

---

## 6. Formal Doğrulama Kapsamı

Aşağıdaki özellikler TLA+ veya eşdeğer model checker ile doğrulanacaktır:

| Özellik | Açıklama | Test Türü |
|---------|----------|-----------|
| **Güvenlik (Safety)** | SURVIVAL'dan yer onayı olmadan çıkış yok | Invariant check |
| **Canlılık (Liveness)** | RETURN_REQUIRED tetiklendiğinde araç nihayetinde safe haven'a ulaşır | Liveness check |
| **Deterministik** | Aynı girdi seti her zaman aynı geçişi üretir | State space exhaustion |
| **Kilitlenme yok** | Hiçbir durum kombinasyonunda deadlock oluşmaz | Deadlock freedom check |
| **Çoklu tetikleyici tutarlılığı** | Eş zamanlı P1 tetikleyicileri her zaman en yüksek öncelikli duruma geçirir | Reachability check |

---

*Detaylı watchdog timer konfigürasyonu ve FreeRTOS görev öncelik tablosu sistem tasarımı aşamasında bu belgeye eklenecektir.*
