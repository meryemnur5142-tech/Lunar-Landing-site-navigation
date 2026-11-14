# status: draft
# owner: Agent C
# depends_on: [docs/architecture/ICD_TEMPLATES.md, docs/architecture/SAFETY_STATE_MACHINE.md, docs/adr/FMEA_KRITIK_MODULLER.md, autonomy/autonomy_matrix.md]
# open_items: [ICD referansları ICD_TEMPLATES.md v1.0 ile tutarlı; TBD parametreler diyagramlarda not olarak işaretlendi]

# LUNA-AI PlantUML Diyagramları — v1.0

**Belge ID:** LUNA-AI-ARCH-004  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı Belgeler:** LUNA-AI-ARCH-001 (Güvenlik Durum Makinesi), LUNA-AI-ARCH-002 (ICD Şablonları), LUNA-AI-FMEA-001

---

## Diyagram 1 — Bileşen Diyagramı

Tüm modüller, arayüzler ve segment grupları. Yer segmenti / uçuş segmenti / simülasyon paketleri ayrı. Her arayüz üzerinde ICD referansı.

```plantuml
@startuml LUNA-AI Component Diagram

' =====================================================
' LUNA-AI Bileşen Diyagramı v1.0
' Belge: LUNA-AI-ARCH-004
' Bağlı: ICD-001..ICD-006 (LUNA-AI-ARCH-002)
' =====================================================

skinparam componentStyle rectangle
skinparam packageStyle frame
skinparam backgroundColor #FAFAFA
skinparam component {
  BackgroundColor #E8F4FD
  BorderColor #2980B9
}

' =====================================================
' YER SEGMENTİ
' =====================================================
package "Yer Segmenti (Ground Segment)" #EAF7EA {

  package "Bilimsel Analiz & Görev Tasarımı" #D5F0D5 {
    [Mission Intelligence\n(Hedef Puanlama &\nKısıt Kontrolü)] as MI
    [Ground Control UI\n(apps/ground-control)] as GC
    [Data Platform\n(Telemetri İşleme &\nArşiv)] as DP
  }

  package "Görev Planlama Altyapısı" #D5F0D5 {
    [Mission Planner\n(Rota & Kaynak Planlama)] as GMP
    [Orbital Geometry\n(Güneş/Dünya Penceresi)] as OG
  }
}

' =====================================================
' UÇUŞ SEGMENTİ (Araç)
' =====================================================
package "Uçuş Segmenti (Flight Segment — Araç)" #FFF3E0 {

  package "Otonomi & Yürütme" #FFE0B2 {
    [Mission Executive\n(Görev Yürütücü)] as ME
    [Global Planner\n(Rota Planlama)] as GP
    [Local Planner\n(Engel Kaçınma)] as LP
    [Replanner\n(Yeniden Planlama)] as RP
  }

  package "Algı & Navigasyon" #FFE0B2 {
    [Localization\n(EKF + IMU + Landmark)] as LOC
    [Terrain Analyzer\n(LiDAR + Kamera)] as TA
  }

  package "Kaynak Yönetimi" #FFE0B2 {
    [Power Management\n(SoC, Bütçe)] as PM
    [Thermal Management\n(Isıtıcı Kontrolü)] as TM
  }

  package "Güvenlik" #FFE0B2 {
    [FDIR\n(Arıza Tespit & Kurtarma)] as FDIR
    [Safety State Machine\n(NOMINAL/CAUTION/\nRETURN_REQUIRED/SURVIVAL)] as SSM
  }

  package "Donanım Arayüzleri" #FFE0B2 {
    [Motion Control\n(Motor Sürücüleri)] as MC
    [Communication\n(RF Alıcı-Verici)] as COM
    [OBC\n(Ana Bilgisayar)] as OBC
  }
}

' =====================================================
' SİMÜLASYON & DOĞRULAMA SEGMENTİ
' =====================================================
package "Simülasyon & Doğrulama (Simulation Segment)" #F3E5F5 {
  [Digital Twin\n(Araç Simülasyonu)] as DT
  [Environment Model\n(Ay Yüzey Ortamı)] as EM
  [Scenario Runner\n(YAML Senaryo Motoru)] as SR
  [Fault Injector\n(Hata Enjeksiyon)] as FI
  [SIL/HIL Bridge] as HIL
}

' =====================================================
' ARAYÜZLER (ICD referansları ile)
' =====================================================

' ICD-001: Power Mgmt → Mission Planner (uçuşta) / Ground Planner (aşağı yansıma)
PM -right-> ME : ICD-001\nenergy_state\n(1 Hz / 10 Hz CAUTION)
PM -right-> GMP : ICD-001\nenergy_state\n(telemetri yansıması)

' ICD-002: Thermal Mgmt → Mission Executive
TM -right-> ME : ICD-002\nthermal_state\n(1 Hz / 10 Hz CAUTION)

' ICD-003: Navigation → Local Planner
LOC -right-> LP : ICD-003\nvehicle_pose\n(≥10 Hz hareket)
LOC -right-> GP : ICD-003\nvehicle_pose\n(1 Hz nominal)

' ICD-004: FDIR → Mission Executive
FDIR -right-> ME : ICD-004\nsafety_status\n(event-driven + 1 Hz)
SSM --> FDIR : durum geçiş\nkararı

' ICD-005: Ground → Flight (Uplink — CCSDS TC)
GMP -down-> COM : ICD-005\nTC Uplink\n(CCSDS)
GC -down-> COM : ICD-005\nTC_IMMEDIATE\n(P1 Komut)

' ICD-006: Flight → Ground (Downlink — CCSDS TM)
COM -up-> DP : ICD-006\nTM Downlink\n(CCSDS)
COM -up-> GC : ICD-006\nTelemetri\n(1 Hz / 10 Hz)

' Araç iç bağlantılar
ME --> GP : görev adımı\nuygula
GP --> LP : waypoint\nlistesi
LP --> MC : hareket\nkomutu
TA --> LOC : nokta bulutu\n+ görüntü
MC --> LOC : enkoder\ngeri beslemesi
FDIR --> PM : güç kesim\nkomutu (SURVIVAL)
FDIR --> TM : ısıtıcı öncelik\nkomut (CAUTION+)
FDIR --> MC : dur komutu\n(RETURN_REQUIRED)
FDIR --> COM : acil beacon\n(SURVIVAL)
RP --> GP : yeni rota\nplanı

' Simülasyon bağlantıları
DT --> LOC : simüle\ntelemetri
EM --> DT : ortam\nkoşulları
SR --> FI : senaryo\nolayları
FI --> DT : hata enjeksiyonu\n(sensör/motor/güç)
HIL --> OBC : HIL\narayüzü

' Yer iç bağlantılar
MI --> GMP : hedef sıralaması\n+ kısıt listesi
OG --> GMP : pencere\nkısıtları
DP --> MI : işlenmiş\ntelemetri

@enduml
```

---

## Diyagram 2 — PSR Operasyon Sekans Diyagramı

PSR (Permanently Shadowed Region) giriş kararından bilimsel görev bitimine ve safe haven dönüşüne. Kritik mesaj alışverişleri, hata dalları, abort trigger'lar dahil.

```plantuml
@startuml LUNA-AI PSR Operation Sequence

' =====================================================
' PSR Operasyon Sekans Diyagramı v1.0
' Senaryo: PSR giriş kararı → bilimsel görev → dönüş
' Bağlı: SC-003 (operational_scenarios.md), ICD-001..004
' =====================================================

skinparam sequenceArrowThickness 2
skinparam sequenceGroupBackgroundColor #FFF8E1
skinparam sequenceLifeLineBorderColor #666666

actor "Ground\nControl" as GC
participant "Mission\nPlanner" as MP
participant "Power\nMgmt" as PWR
participant "Thermal\nMgmt" as THM
participant "Navigation" as NAV
participant "FDIR" as FDIR
participant "Mission\nExecutive" as ME

== Faz: PSR Giriş Kararı ==

GC -> MP : TC_PLAN_UPLOAD\nPSR waypoint + enerji bütçesi\n[ICD-005]
MP -> PWR : PSR giriş için\nenerji rezerv sorgusu\n[ICD-001]
PWR --> MP : energy_state\nsoc_percent=TBD%\nestimated_return_soc=TBD%\n[ICD-001]
MP -> THM : termal durum\nsorgusu\n[ICD-002]
THM --> MP : thermal_state\ncritical_component_ok=true\n[ICD-002]
MP -> NAV : konum belirsizliği\nsorgusu\n[ICD-003]
NAV --> MP : vehicle_pose\nuncertainty_m < 0.5m\n[ICD-003]

alt PSR Giriş Koşulları Sağlandı\n(SoC yeterli, termal ok, nav güvenilir)
  MP -> ME : PSR_ENTRY_AUTHORIZED\nwaypoint_list, return_reserve_wh
  ME -> FDIR : PSR giriş bildirimi\n(izleme artırıldı)
  FDIR --> ME : safety_state=NOMINAL\nabort_signal=false\n[ICD-004]
  ME -> GC : TC ACK — PSR giriş onaylandı\n[ICD-006]
else PSR Giriş Koşulları Sağlanamadı
  MP -> GC : PSR giriş reddedildi\n(sebep: SoC < eşik veya termal uyarı)\n[ICD-006]
  note right of GC: Yeni pencere bekle\nveya plan revizyonu
end

== Faz: PSR İçi Bilimsel Operasyon ==

ME -> NAV : bilimsel waypoint'e\nhareket başlat
NAV -> FDIR : heartbeat\n(her 100 ms)\n[SAFETY_STATE_MACHINE]
PWR -> FDIR : heartbeat + energy_state\n(her 500 ms)\n[ICD-001]
THM -> FDIR : heartbeat + thermal_state\n(her 1 s)\n[ICD-002]

loop Bilimsel Veri Toplama Döngüsü
  ME -> NAV : sonraki waypoint
  NAV --> ME : waypoint ulaşıldı
  ME -> ME : bilimsel sensör\naktifleştir
  ME -> PWR : güç durumu kontrol\n(return_reserve_wh ≥ eşik?)
  PWR --> ME : energy_state güncel\n[ICD-001]
end

== Abort Senaryoları (Hata Dalları) ==

group ABORT-1: HC-006 Dönüş Rezervi İhlali [ABT-001]
  PWR -> FDIR : ANOMALY\nreturn_reserve_wh < HC-006_threshold\n[ICD-001 status=WARN]
  FDIR -> ME : safety_status\nsafety_state=RETURN_REQUIRED\nabort_signal=true\n[ICD-004]
  ME -> NAV : TÜM OPERASYONLAR DONDURULDU\ndönüş rotası iste
  note right of FDIR: abort_trigger=ABT-001\nHC-006 ihlali
  ME -> GC : HC-006 ihlali bildirimi\nkonum + beklenen dönüş süresi\n[ICD-006]
end

group ABORT-2: Termal Kritik İhlali [SC-006]
  THM -> FDIR : ANOMALY\nthermal_mode=CRITICAL\n[ICD-002 status=ERROR]
  FDIR -> ME : safety_status\nsafety_state=RETURN_REQUIRED\nabort_signal=true\n[ICD-004]
  FDIR -> THM : tüm ısıtıcılar MAX öncelik
  ME -> NAV : acil dönüş rotası başlat
  ME -> GC : termal kritik bildirimi\n[ICD-006]
end

group ABORT-3: Link Kaybı (PSR içi) [SC-002, ABT-004]
  note over ME, FDIR: Link > TBD(source: §10) dakika kesik
  FDIR -> ME : safety_status\nsafety_state=RETURN_REQUIRED\n(pre-planned ACL tetiklendi)\n[ICD-004]
  ME -> NAV : pre-planned safe haven'a dön\n(yer onayı beklenmez — ACL)
end

== Faz: Safe Haven Dönüşü ==

NAV -> ME : safe haven rotası\nhazır
ME -> PWR : dönüş boyunca\nenerji koruma modu
PWR -> THM : minimum ısıtıcı\ntalebi ilet
ME -> GC : dönüş başladı\nETA: TBD dakika\n[ICD-006]

loop Dönüş İzleme
  PWR -> FDIR : return_reserve_wh güncellendi
  NAV -> FDIR : konum + belirsizlik
  FDIR -> ME : safety_status (1 Hz)\n[ICD-004]
end

ME -> GC : safe haven ulaşıldı\n[ICD-006]
GC -> MP : RETURN_REQUIRED → NOMINAL onayı\n[ICD-005 TC_CONDITIONAL]
MP -> FDIR : yer onayı alındı
FDIR -> ME : safety_state=NOMINAL\n[ICD-004]

@enduml
```

---

## Diyagram 3 — Arıza Yönetimi Sekans Diyagramı

Senaryo: Lokalizasyon belirsizliği aşıldı → FDIR kararı → replanning → dönüş veya kurtarma. Bağlı: SC-004 (operational_scenarios.md).

```plantuml
@startuml LUNA-AI Fault Management Sequence

' =====================================================
' Arıza Yönetimi Sekans Diyagramı v1.0
' Senaryo: Lokalizasyon belirsizliği aşımı → FDIR → replanning → dönüş
' Bağlı: SC-004, QAR-NAV-002, FMEA-RPN-NAV-001 (RPN:24)
' =====================================================

skinparam sequenceArrowThickness 2
skinparam sequenceGroupBorderColor #CC0000
skinparam sequenceGroupBackgroundColor #FFF0F0

participant "Local\nPlanner" as LP
participant "Navigation\n(EKF + IMU)" as NAV
participant "FDIR" as FDIR
participant "Mission\nExecutive" as ME
participant "Global\nPlanner" as GP
participant "Replanner" as RP
participant "Ground\nControl" as GC

== Detection: Lokalizasyon Belirsizliği Tespiti ==

NAV -> NAV : EKF kovaryans izleme\nsürekli (10 Hz)
NAV -> LP : vehicle_pose\nuncertainty_m = 0.6m\n[ICD-003 status=DEGRADED]
LP -> LP : uncertainty_m > 0.5m →\nengel yaklaşım hızını\nyarıya indir

NAV -> FDIR : ANOMALY EVENT\nuncertainty_m > QAR-NAV-002_threshold\n(> 1.0m)
FDIR -> ME : safety_status\nsafety_state=CAUTION\nabort_signal=false\n[ICD-004]
ME -> LP : DUR komutu\n(hareket durduruldu)
ME -> GC : CAUTION bildirimi\nlokalizasyon belirsizlik aşımı\n[ICD-006]

== Isolation: Arızalı Sensör Tespiti ==

FDIR -> NAV : sensör izolasyon\ntesti başlat
NAV -> NAV : IMU tutarsızlık testi
NAV -> NAV : odometry / IMU\nkarşılaştırması
NAV -> NAV : son landmark\neşleşme kalitesi

alt IMU Arızası Tespit Edildi
  NAV -> FDIR : IMU_FAULT\n(hatalı sensör izole edildi)
  FDIR -> NAV : IMU devre dışı\nordometry-only moda geç
  note right of NAV: Degraded mode:\nordometry + visual landmark
else Sensör Kombinasyonu Tutarsız
  NAV -> FDIR : FUSION_ANOMALY\n(kaynak belirlenemedi)
  note right of FDIR: En muhtemel: IMU drift\n(FMEA-RPN-NAV-001)
end

== Recovery: Landmark Yeniden Lokalizasyon ==

FDIR -> NAV : landmark arama\ngirişimi başlat (N deneme)
loop Landmark Arama Döngüsü (maks N deneme — TBD)
  NAV -> NAV : yerinde dön\norbital harita ile eşleştir
  alt Landmark Eşleşmesi Başarılı
    NAV -> FDIR : RECOVERY_SUCCESS\nuncertainty_m < 0.5m
    FDIR -> ME : safety_status\nsafety_state=NOMINAL\n[ICD-004]
    ME -> LP : hareket devam\n(normal hız)
    ME -> GC : recovery başarılı\n[ICD-006]
  else Eşleşme Başarısız — Devam
    NAV -> FDIR : LANDMARK_NO_MATCH\n(deneme i/N)
  end
end

== Recovery Başarısız → Replanning ==

FDIR -> ME : RECOVERY_FAILED\nsafety_state=RETURN_REQUIRED\nabort_signal=true\n[ICD-004]
ME -> RP : replanning talebi\nmevcut konum (degraded σ_pos)\nhedef: safe haven
RP -> GP : degraded nav modunda\nIMU-only güzergah üret

alt PSR İçinde
  GP -> ME : PSR çıkış rotası\n(enerji kritik kontrol)
  ME -> FDIR : rota onay
  FDIR -> ME : onaylandı
  note right of FDIR: Degraded nav ile PSR çıkışı:\nhata birikimi kabul mesafesiyle sınırlandırıldı
else SURFACE_EXPLORATION
  GP -> ME : pre-planned safe haven\nkoordinatlarına IMU-only rota
end

ME -> LP : yeni rota uygula\n(degraded mode — düşük hız)
ME -> GC : RETURN_REQUIRED\nsensör arızası + degraded nav\nbeklenen dönüş süresi\n[ICD-006]

== Dönüş ve Kurtarma ==

LP -> ME : safe haven yaklaştı
ME -> FDIR : safe haven ulaşımı
FDIR -> GC : safe haven ulaşıldı\nyer onayı bekleniyor\n[ICD-006]
GC -> ME : yer onayı\n(TC_CONDITIONAL)\n[ICD-005]
FDIR -> ME : safety_state=NOMINAL\n(yer onaylı geçiş)\n[ICD-004]

note right of FDIR
  Sensör kalibrasyonu:\n
  - IMU yeniden kalibrasyon prosedürü
  - Yer segmentinden parametre güncellemesi
  - Yeni görev planı gelmeden operasyon yok
end note

@enduml
```

---

## Diyagram 4 — Dağıtım Diyagramı

Araç üzerindeki donanım ve üzerlerinde çalışan yazılım bileşenleri. Yer segmenti sunucuları ve bağlantı tipi.

```plantuml
@startuml LUNA-AI Deployment Diagram

' =====================================================
' Dağıtım Diyagramı v1.0
' Araç donanımı + yer segmenti sunucuları + bağlantı
' =====================================================

skinparam nodeStyle rectangle
skinparam componentStyle rectangle
skinparam backgroundColor #FAFAFA

' =====================================================
' ARAÇ (Flight Hardware)
' =====================================================
node "Araç (Rover)" as ROVER #FFE0B2 {

  node "Ana Bilgisayar (OBC)\n[FreeRTOS, COTS Rad-Hard CPU\nTBD-SNS-001]" as OBC #FFCC80 {
    component [FDIR Task\n(Priority: Highest)] as FDIR_SW
    component [Mission Executive] as ME_SW
    component [Global Planner] as GP_SW
    component [Local Planner] as LP_SW
    component [Replanner] as RP_SW
    component [Power Mgmt Task] as PM_SW
    component [Thermal Mgmt Task] as TM_SW
    component [Communication Task] as COM_SW
  }

  node "Navigasyon İşlemcisi\n[TBD — ayrı SoC veya OBC\nüzerinde ayrı core]" as NAV_CPU #FFCC80 {
    component [EKF Localization] as EKF_SW
    component [Terrain Analyzer] as TA_SW
    component [Sensor Fusion] as SF_SW
  }

  node "IMU Modülü\n[TBD-SNS-001/002]" as IMU_HW #FFD54F {
    component [İvmeölçer + Jiroskop] as IMU_SENS
  }

  node "LiDAR\n[TBD-SNS-001]" as LIDAR_HW #FFD54F {
    component [Nokta Bulutu\nÜretici] as LIDAR_SW
  }

  node "Kamera Sistemi\n[TBD-SNS-001]" as CAM_HW #FFD54F {
    component [Stereo Görüntü\nİşleme] as CAM_SW
  }

  node "RF Modülü\n[TBD-COM-001]" as RF_HW #FFD54F {
    component [Yüksek Kazançlı Anten\n(HGA)] as HGA
    component [UHF Omni Anten\n(Yedek)] as UHF
  }

  node "Güç Sistemi\n[TBD-BAT-001/002, TBD-SOL-001]" as PWR_HW #FFD54F {
    component [Güneş Paneli\n+ Şarj Regülatörü] as SOLAR
    component [Batarya Modülü\n(Dual — TBD-RED-003)] as BAT
    component [PDU\n(Çift Kanal)] as PDU
  }

  node "Termal Sistem\n[TBD-THM-001]" as THM_HW #FFD54F {
    component [Isıtıcılar\n(Birincil + Fallback)] as HEATER
    component [Sıcaklık Sensörleri\n(≥2 bağımsız/nokta)] as TEMP_SENS
  }

  node "Hareket Sistemi" as MOT_HW #FFD54F {
    component [Motor Sürücüleri\n(4+ tekerlekli)] as MOTOR_DRV
    component [Tekerlek Enkoderleri] as ENC
  }

  node "Donanım Watchdog\n[Bağımsız HW Timer]" as HW_WD #EF9A9A {
    component [FDIR HW Watchdog\n(25 ms kick)] as WD_HW
  }
}

' =====================================================
' YER SEGMENTİ
' =====================================================
node "Yer Kontrol Merkezi\n(Ground Segment Sunucu)" as GROUND #E8F5E9 {

  node "Görev Kontrol Sunucusu" as MCS #C8E6C9 {
    component [Ground Control UI\n(apps/ground-control)] as GC_UI
    component [Mission Planner\n(Rota & Kaynak)] as GMP_SW
    component [Mission Intelligence\n(Hedef & Kısıt)] as MI_SW
  }

  node "Veri İşleme Sunucusu" as DPS #C8E6C9 {
    component [Data Platform\n(İngestion + Catalog)] as DP_SW
    component [Telemetri Arşivi] as TM_ARCH
    component [Bilimsel Veri Deposu] as SCI_DATA
  }

  node "Simülasyon Sunucusu" as SIM_SRV #C8E6C9 {
    component [Digital Twin] as DT_SW
    component [Environment Model] as EM_SW
    component [Scenario Runner] as SR_SW
    component [Fault Injector] as FI_SW
  }

  node "Derin Uzay Ağı\n(DSN Anteni)" as DSN #A5D6A7 {
    component [RF Uplink/Downlink\n(CCSDS)] as DSN_RF
  }
}

' =====================================================
' BAĞLANTILAR
' =====================================================

' Araç donanım bağlantıları
OBC --> RF_HW : UART/SPI\nhaberleşme komutu
OBC --> PWR_HW : I2C/CAN\ngüç kontrol
OBC --> THM_HW : GPIO / I2C\nısıtıcı kontrol
OBC --> MOT_HW : CAN Bus\nmotor komutu
OBC --> HW_WD : FDIR HW kick\n(25 ms)
NAV_CPU --> IMU_HW : SPI\nörnekleme (200+ Hz)
NAV_CPU --> LIDAR_HW : Ethernet/PCIe\nnokta bulutu
NAV_CPU --> CAM_HW : USB3/Ethernet\ngörüntü akışı
OBC --> NAV_CPU : IPC / Shared Memory\nvehicle_pose [ICD-003]

' Yer-araç bağlantısı
DSN_RF --> RF_HW : CCSDS TC/TM\n(ICD-005 Uplink / ICD-006 Downlink)\n[TBD-COM-001: frekans, bant]

' Yer iç bağlantılar
GC_UI --> MCS : HTTP/gRPC
GMP_SW --> MI_SW : hedef listesi
DP_SW --> TM_ARCH : telemetri depo
DSN_RF --> DP_SW : ham TM\nalım
SIM_SRV --> DPS : simülasyon\ntelemetrisi
SIM_SRV --> MCS : SIL test\narayüzü

@enduml
```

---

## Diyagram 5 — Güvenlik Durum Makinesi

Nominal / Caution / Return_Required / Survival. Geçiş koşulları ve guard ifadeleri. LUNA-AI-ARCH-001 ile tutarlı.

```plantuml
@startuml LUNA-AI Safety State Machine

' =====================================================
' Güvenlik Durum Makinesi v1.0
' Belge: LUNA-AI-ARCH-004 (Diyagram 5)
' Kaynak: LUNA-AI-ARCH-001 (SAFETY_STATE_MACHINE.md)
' Bağlı: ADR-005, QAR FDIR-001/002/004/005
' =====================================================

skinparam state {
  BackgroundColor #E8F4FD
  BorderColor #2980B9
  ArrowColor #333333
}
skinparam state<<NOMINAL>> {
  BackgroundColor #E8F5E9
  BorderColor #27AE60
}
skinparam state<<CAUTION>> {
  BackgroundColor #FFF9C4
  BorderColor #F39C12
}
skinparam state<<RETURN_REQUIRED>> {
  BackgroundColor #FFE0B2
  BorderColor #E67E22
}
skinparam state<<SURVIVAL>> {
  BackgroundColor #FFCDD2
  BorderColor #C0392B
}

' Başlangıç
[*] --> NOMINAL : boot_complete\nAND subsystems_ok\nAND fdir_heartbeat_ok

' =====================================================
' NOMINAL
' =====================================================
state NOMINAL<<NOMINAL>> {
  NOMINAL : entry / tüm subsistemler izlemeye alındı
  NOMINAL : do / tam keşif operasyonu; PSR girişine izin
  NOMINAL : izlenen: SoC > eşik+marj, nav σ < 0.5m RMS
  NOMINAL : izlenen: tüm bileşen sıcaklıkları nominal
  NOMINAL : izlenen: link_timeout < uyarı eşiği
  NOMINAL : izlenen: tüm FDIR heartbeat'leri zamanında
}

' =====================================================
' CAUTION
' =====================================================
state CAUTION<<CAUTION>> {
  CAUTION : entry / yer segmentine CAUTION flag gönder
  CAUTION : do / mevcut operasyonu güvenli son noktaya tamamla
  CAUTION : do / dönüş rotası hazır tut; yeni PSR girişi yasak
  CAUTION : izlenen: SoC < %25 veya dönüş marjı < %20
  CAUTION : izlenen: nav belirsizliği 0.5–1.0 m RMS
  CAUTION : izlenen: bileşen sıcaklığı nominal limitin %80'i
}

' =====================================================
' RETURN_REQUIRED
' =====================================================
state RETURN_REQUIRED<<RETURN_REQUIRED>> {
  RETURN_REQUIRED : entry / abort_signal=true → Mission Exec donduruldu
  RETURN_REQUIRED : entry / bilimsel operasyon tamamen durduruldu
  RETURN_REQUIRED : do / safe haven dönüş rotası aktif
  RETURN_REQUIRED : do / navigasyon + FDIR tam çalışır
  RETURN_REQUIRED : do / periyodik haberleşme girişimi devam
  RETURN_REQUIRED : exit / safe_haven_ulaşıldı AND yer_onayı
}

' =====================================================
' SURVIVAL
' =====================================================
state SURVIVAL<<SURVIVAL>> {
  SURVIVAL : entry / tüm bilimsel sensörler kesildi
  SURVIVAL : entry / yüksek güçlü haberleşme kesildi (beacon kalır)
  SURVIVAL : entry / planlayıcı ve replanning durduruldu
  SURVIVAL : do / navigasyon (IMU + dead-reckoning minimum)
  SURVIVAL : do / FDIR çekirdek işlevi aktif
  SURVIVAL : do / minimum ısıtıcı güç (pil koruma)
  SURVIVAL : do / periyodik beacon yayını
}

' =====================================================
' GEÇİŞLER — NOMINAL'den çıkış
' =====================================================
NOMINAL --> CAUTION : [SoC < %25\nOR dönüş_marjı < %20\nOR nav_belirsizlik 0.5-1.0m RMS\nOR bileşen_sıcaklık nominal_%80\nOR link_timeout > uyarı_eşiği (TBD)\nOR planner_heartbeat_gecikmeli]

NOMINAL --> RETURN_REQUIRED : [SoC < %15\nOR link_timeout > kritik_eşik (TBD)\nOR nav_lokalizasyon_kayıp_timeout > TBD_s\nOR yer_komutu=TC_IMMEDIATE_RETURN\nOR termal_kritik AND lokal_müdahale_başarısız]

NOMINAL --> SURVIVAL : [SoC < %10\nOR kritik_donanım_arızası\nOR hızlı_ısınma > TBD_derece/dak\nOR FDIR_self_watchdog_kaybı\nOR çoklu_eşzamanlı_P1_arıza]

' =====================================================
' GEÇİŞLER — CAUTION'dan çıkış
' =====================================================
CAUTION --> NOMINAL : [tüm_tetikleyiciler_temiz\nAND tüm_parametreler_nominal_aralıkta]

CAUTION --> RETURN_REQUIRED : [SoC < %15\nOR link_timeout > kritik_eşik\nOR nav_recovery_başarısız\nOR termal_kritik\nOR yer_komutu=TC_IMMEDIATE_RETURN]

CAUTION --> SURVIVAL : [SoC < %10\nOR kritik_donanım_arızası\nOR FDIR_self_watchdog_kaybı\nOR hızlı_ısınma > TBD]

' =====================================================
' GEÇİŞLER — RETURN_REQUIRED'dan çıkış
' =====================================================
RETURN_REQUIRED --> SURVIVAL : [dönüş_sırasında_SURVIVAL_tetikleyicisi_aktif]

RETURN_REQUIRED --> NOMINAL : [safe_haven_ulaşıldı\nAND enerji_yeterli\nAND yer_segmenti_onayladı]\n{guard: yalnızca yer onayı ile}

' =====================================================
' GEÇİŞLER — SURVIVAL'dan çıkış
' =====================================================
SURVIVAL --> RETURN_REQUIRED : [temel_sistem_kurtarıldı\nAND enerji > %10\nAND yer_segmenti_onayladı]\n{guard: yalnızca yer onayı ile}

note right of SURVIVAL
  SURVIVAL'dan doğrudan NOMINAL'e
  geçiş YOKTUR.
  Zorunlu: SURVIVAL → RETURN_REQUIRED → NOMINAL
  Her ikisi de yer onayı gerektirir.
  FDIR her durumda çalışmaya devam eder.
  Donanım watchdog: 25 ms kick periyodu.
end note

note right of RETURN_REQUIRED
  Mission Executive abort_signal=true
  alınca tüm operasyonları dondurur.
  Hareket Kontrolüne "dur" komutu gönderilir.
  Bu kısıt yazılım mimarisinde zorunludur.
  (ICD-004 — bloklu mesaj kuyruğu)
end note

note bottom of CAUTION
  CAUTION → NOMINAL geçişi:
  TÜM tetikleyiciler aynı anda temiz olmalı.
  Histerezis: gürültü filtresi uygulanır
  (10 ardışık ölçüm nominal aralıkta).
end note

@enduml
```

---

## Diyagram Referans Tablosu

| # | Diyagram | PlantUML Tipi | Kaynak Belgeler | Amaç |
|---|----------|--------------|-----------------|------|
| 1 | Bileşen Diyagramı | Component | ICD-001..006, ADR-005 | Tüm modüller ve arayüzler; segment grupları |
| 2 | PSR Operasyon Sekans | Sequence | SC-003, ICD-001..005, HC-006 | PSR giriş kararı → görev → dönüş; abort dalları |
| 3 | Arıza Yönetimi Sekans | Sequence | SC-004, FMEA-RPN-NAV-001, QAR-NAV-002 | Lokalizasyon kaybı → FDIR → replanning → dönüş |
| 4 | Dağıtım Diyagramı | Deployment | ADR-003, ICD-005/006, TBD-SNS/BAT/COM | Donanım düğümleri, yazılım dağıtımı, bağlantı tipleri |
| 5 | Güvenlik Durum Makinesi | State | LUNA-AI-ARCH-001, ADR-005, QAR FDIR-001..005 | 4 güvenlik durumu, geçiş guard'ları, FDIR bağımsızlığı |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent C, C2 görevi; 5 diyagram |
