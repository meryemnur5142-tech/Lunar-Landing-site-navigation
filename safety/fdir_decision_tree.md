# status: draft
# owner: Agent D
# depends_on:
#   - safety/fdir_implementation.md
#   - docs/architecture/SAFETY_STATE_MACHINE.md
#   - docs/qar/QAR_TABLE.md
# open_items:
#   - TBD-FDIR-001..008 eşikleri kapatıldıkça diyagram sayısal değerler güncellenir

# FDIR Karar Ağaçları — LUNA-AI

**Belge ID:** LUNA-AI-SAF-D2-002
**Versiyon:** 0.1-draft
**Tarih:** 2026-11-14
**Sahip:** Agent D

Mermaid flowchart diyagramları. Her diyagram `flowchart TD` formatındadır.
Tespit → İzolasyon → Recovery adımlarını gösterir.

---

## 1. Sensör Tutarsızlığı

```mermaid
flowchart TD
    A([BAŞLA: Sensör Tutarsızlığı Şüphesi]) --> B{IMU vs VO\nfark > TBD-FDIR-001?}
    B -- HAYIR --> C{Wheel vs IMU\nfark > σ_wheel?}
    C -- HAYIR --> Z([NOMINAL: Tutarsızlık Yok])
    C -- EVET --> D1[Kayma tespiti\nTekerlek güvenilmez]
    B -- EVET --> D2{3-sensör\noy sayımı}

    D2 -- VO=Wheel,\nIMU farklı --> E1[IMU güvenilmez\nilan et]
    D2 -- IMU=Wheel,\nVO farklı --> E2[VO güvenilmez\nilan et]
    D2 -- IMU=VO,\nWheel farklı --> D1
    D2 -- Üçü de farklı --> LOC[Lokalizasyon\nKaybı §5]

    E1 --> F[CAUTION tetikle\nICD-004 bildir]
    E2 --> F
    D1 --> F

    F --> G[Degraded nav modu\nhız %50 azalt]
    G --> H{σ < 0.5 m?}
    H -- EVET --> I[CAUTION kaldır\nNominal devam]
    H -- HAYIR --> J{σ > 2.0 m?}
    J -- EVET --> LOC
    J -- HAYIR --> K{CAUTION süresi\n> 60 s?}
    K -- EVET --> RR[RETURN_REQUIRED\nDönüş başlat]
    K -- HAYIR --> G
```

---

## 2. Motor Sıkışması / Tekerlek Hatası

```mermaid
flowchart TD
    A([BAŞLA: Motor / Tekerlek Hatası Şüphesi]) --> B{Encoder fark\n> TBD-FDIR-002?}
    B -- HAYIR --> C{Akım > rated×1.5\nveya < rated×0.1?}
    C -- HAYIR --> Z([NOMINAL: Hata Yok])
    C -- EVET --> D[Akım anomalisi\nMotor sürücü hatası]
    B -- EVET --> E[Encoder sapma\nSıkışma şüphesi]

    D --> F[Hangi tekerlek N?]
    E --> F

    F --> G{Kaç tekerlek\netkilendi?}
    G -- 1 tekerlek --> H[Tekerlek N sürücüsüne\nsıfır komut]
    G -- 2+ tekerlek --> CRIT[Araç durdur\nFDIR RETURN_REQUIRED]

    H --> I{3-tekerlek\nmobilite OK?}
    I -- EVET --> J[Hız %60'a düş\nEğim limiti azalt\nReplanning talebi]
    I -- HAYIR --> CRIT

    J --> K[Dönüş rotası\nönceliklendir]
    K --> L[Acil haberleşme\npaketi gönder]
    L --> RET([RETURN_REQUIRED\nDönüş başlat])

    CRIT --> SURV{Dönüş enerjisi\nyeterli?}
    SURV -- EVET --> RR2([RETURN_REQUIRED\nDönüş başlat])
    SURV -- HAYIR --> SV([SURVIVAL\nDead-reckoning\nSafe haven yönü])
```

---

## 3. Batarya/Panel Anomalisi

```mermaid
flowchart TD
    A([BAŞLA: Batarya / Panel Anomalisi Şüphesi]) --> B{SoC sapma\n> TBD-FDIR-003?}
    B -- HAYIR --> C{Panel gücü\n< beklenen×0.7?}
    C -- HAYIR --> D{Hücre dengesizlik\n> TBD-FDIR-004 mV?}
    D -- HAYIR --> Z([NOMINAL: Anomali Yok])
    C -- EVET --> P1[Panel anomalisi\nServo açı doğrula]
    D -- EVET --> CB[Hücre grubu\ndengesizliği]
    B -- EVET --> SoC[SoC sapma\nHücre tarama yap]

    P1 --> P2{Servo açı\ndoğru mu?}
    P2 -- HAYIR --> P3[Panel yeniden\nyönlendir]
    P2 -- EVET --> P4[Panel hasar\nveya kir şüphesi]
    P3 --> P5[Panel gücü\nizle — 30 s]
    P4 --> LOAD1

    SoC --> CB
    CB --> ISO{BMS izolasyon\ndestekli?}
    ISO -- EVET --> ISO2[Hatalı hücre grubu\ndevre dışı\nKapasite düşür]
    ISO -- HAYIR --> LOAD1[Yük kesme başlat\nAdım 1: Bilim yükleri]

    ISO2 --> BUDG[Enerji bütçesi\ngüncelle]
    BUDG --> CHK{Yeterli kapasite\ndönüş için?}
    CHK -- EVET --> CAU[CAUTION tetikle\nAzaltılmış görev]
    CHK -- HAYIR --> LOAD1

    LOAD1 --> LOAD2{SoC < %15?}
    LOAD2 -- EVET --> RR([RETURN_REQUIRED\nDönüş başlat])
    LOAD2 -- HAYIR --> LOAD3{SoC < %10?}
    LOAD3 -- EVET --> SV([SURVIVAL\nYalnızca yaşam destek])
    LOAD3 -- HAYIR --> CAU
```

---

## 4. Haberleşme Kesintisi

```mermaid
flowchart TD
    A([BAŞLA: Link Timeout Tetiklendi]) --> B{Araç haberleşme\nmodülü heartbeat OK?}
    B -- HAYIR --> HW[Araç dahili\nhaberleşme arızası]
    HW --> HW2[FDIR: donanım arızası\nişle + CAUTION]
    B -- EVET --> C{Lunar relay\nüzerinden bağlan?}
    C -- BAŞARILI --> D[Relay üzerinden\nbağlantı kuruldu]
    D --> E[Yer sorunu\nveya orbital geometri\nOTN devam]
    C -- BAŞARISIZ --> F{Timeout süresi\nkarşılaştır}

    F --> G{timeout < TBD-FDIR-006\nuyarı eşiği?}
    G -- EVET --> H[CAUTION tetikle\nRetry başlat]
    H --> I{PSR içinde mi?}
    I -- HAYIR --> J[Görev planı\nOTN devam]
    I -- EVET --> K[PSR içi OTN rota\nenerjiye dikkat]

    G -- HAYIR --> L{timeout > COM-004\nkritik eşik?}
    L -- EVET --> M{PSR içi +\nenerji kritik?}
    M -- EVET --> ABT[ABT-004 tetikle\nACL acil dönüş]
    M -- HAYIR --> RR([RETURN_REQUIRED\nSafe haven dön])
    L -- HAYIR --> H

    ABT --> RR
    HW2 --> RR
```

---

## 5. Lokalizasyon Kaybı

```mermaid
flowchart TD
    A([BAŞLA: Lokalizasyon Kaybı Şüphesi]) --> B{EKF inovasyon\nχ² > eşik?}
    B -- HAYIR --> C{σ_pos > 0.5 m?}
    C -- HAYIR --> Z([NOMINAL: Lokalizasyon OK])
    C -- EVET --> CAUT[CAUTION: σ 0.5-2.0 m\nHız azalt]
    B -- EVET --> D[EKF uyumsuz\nLokalizasyon kaybı]

    D --> E[Araç DUR\nFDIR CAUTION]
    E --> F[Son bilinen iyi\npozisyon kaydet]
    F --> G[Kaynak belirleme]

    G --> H{IMU drift\nşüphesi?}
    H -- EVET --> I[Statik IMU testi\nDrift hesapla]
    G --> J{VO çalışmıyor\nmu?}
    J -- EVET --> K[VO kaybı: PSR veya\naydınlatma sorunu]
    G --> L{DEM-LiDAR\nbüyük sapma?}
    L -- EVET --> M[Harita uyuşmazlığı\nDEM güncelleme gerekli]

    I --> REC[Recovery girişimi\nTBD-FDIR-008 s]
    K --> REC
    M --> REC

    REC --> N{σ < 0.5 m\ngeri geldi?}
    N -- EVET --> O[CAUTION kaldır\nHarekete devam]
    N -- HAYIR --> P{TBD-FDIR-008 s\ngeçti mi?}
    P -- HAYIR --> REC
    P -- EVET --> RR[RETURN_REQUIRED\nLast-known-good\nüzerinden dön]

    RR --> Q{Dönüş sırasında\nσ < 0.5 m?}
    Q -- EVET --> O
    Q -- HAYIR --> SV([SURVIVAL\nDead-reckoning\nSafe haven yönü])

    CAUT --> C2{σ > 2.0 m?}
    C2 -- EVET --> D
    C2 -- HAYIR --> CAUT
```

---

*Diyagramlar Mermaid 10.x flowchart TD söz dizimiyle oluşturulmuştur.*
*TBD değerleri `config/tbd_register.md`'de kayıtlıdır; §10 verisi gelince güncellenir.*
