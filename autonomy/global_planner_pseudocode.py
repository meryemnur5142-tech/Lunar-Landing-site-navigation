"""
LUNA-AI Kaynak-Kısıtlı Global Planlayıcı — Python Pseudocode
Belge: autonomy/mission_planner.md §2–§5
Durum: draft | Sahip: Agent D
Tarih: 2026-11-14

NOT: Bu dosya gerçek implementasyon değildir. Algoritma yapısını ve
     modül arayüzlerini göstermek için tasarlanmış pseudocode iskeletidir.
     Gerçek parametreler config/tbd_register.md TBD'leri kapandıktan sonra
     doldurulacaktır.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict
import heapq
import math


# ---------------------------------------------------------------------------
# Enum Tanımları
# ---------------------------------------------------------------------------

class ThermalState(Enum):
    NOMINAL = auto()
    CAUTION = auto()
    CRITICAL = auto()


class SafetyLevel(Enum):
    NOMINAL = auto()
    CAUTION = auto()
    RETURN_REQUIRED = auto()
    SURVIVAL = auto()


class PlanDecision(Enum):
    LOCAL_CORRECTION = auto()   # Küçük sapma: lokal kaçınma manevrası
    FULL_REPLAN = auto()        # Tam yeniden plan gerekli
    DIRECTED_REPLAN = auto()    # Dönüş odaklı yeniden plan (enerji uyarısı)
    ABORT_RETURN = auto()       # ACL acil dönüş tetiklendi


# ---------------------------------------------------------------------------
# PlannerState — 6-boyutlu durum vektörü
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlannerState:
    """
    6-boyutlu planlayıcı durum vektörü.
    Ref: autonomy/mission_planner.md §1.1

    frozen=True: State nesneleri hash'lenebilir; A* kapalı set'e eklenebilir.
    """
    konum_x: float          # metre, yerel harita çerçevesi
    konum_y: float          # metre, yerel harita çerçevesi
    zaman: float            # saniye, görev başından itibaren
    enerji_wh: float        # Wh, mevcut batarya şarj düzeyi
    termal_durum: ThermalState = ThermalState.NOMINAL
    guvenlik_seviyesi: SafetyLevel = SafetyLevel.NOMINAL

    def to_grid(self, resolution: float = 1.0) -> Tuple[int, int]:
        """Metrik koordinatı ızgara indeksine çevir."""
        return (int(self.konum_x / resolution), int(self.konum_y / resolution))

    def distance_to(self, other: "PlannerState") -> float:
        return math.sqrt((self.konum_x - other.konum_x) ** 2 +
                         (self.konum_y - other.konum_y) ** 2)

    def is_energy_critical(self, hc006_threshold_wh: float) -> bool:
        """HC-006: dönüş rezervi kritik mi?"""
        return self.enerji_wh < hc006_threshold_wh

    def is_safe_to_plan(self) -> bool:
        """Planlayıcının yeni görev adımı ekleyip ekleyemeyeceğini döner."""
        return self.guvenlik_seviyesi in (SafetyLevel.NOMINAL, SafetyLevel.CAUTION)


@dataclass
class EnergyBudget:
    """
    Güç Yönetimi modülünce hesaplanır ve ICD-002 üzerinden planlayıcıya bildirilir.
    Planlayıcı bu yapıyı bağımsız hesaplamaz (HC-006 Uyum Notu 3).
    """
    return_reserve_wh: float     # Dönüş için gereken minimum enerji (HC-006)
    current_soc_wh: float        # Mevcut batarya enerjisi (Wh)
    energy_per_meter: float      # Araç enerji tüketim modeli (Wh/m); TBD-PLAN-003


@dataclass
class WaypointPlan:
    """Global planlayıcı çıktısı: waypoint listesi ve enerji profili."""
    waypoints: List[Tuple[float, float]]
    estimated_energy_wh: List[float]   # her adım için tahmini tüketim
    total_distance_m: float
    planning_time_s: float             # QAR-PLAN-001: < 60 s hedefi


# ---------------------------------------------------------------------------
# CostModel — Maliyet fonksiyonu bileşenleri
# ---------------------------------------------------------------------------

class CostModel:
    """
    Birleşik maliyet fonksiyonu.
    Ref: autonomy/mission_planner.md §2.3

    cost = w_dist  × dist(i,j)
         + w_energy × energy_cost(i,j)
         + w_thermal × thermal_cost(i,j)
         + w_risk   × risk_cost(i,j)
    """

    def __init__(
        self,
        w_dist: float = 1.0,
        w_energy: float = 2.0,
        w_thermal: float = 1.5,
        w_risk: float = 3.0,
        energy_per_meter: float = None,   # TBD-PLAN-003
        thermal_coeff: float = None,       # TBD-PLAN-004
        risk_coeff: float = None,          # TBD-PLAN-005
    ):
        self.w_dist = w_dist
        self.w_energy = w_energy
        self.w_thermal = w_thermal
        self.w_risk = w_risk
        # TBD: §10 araç verisi gelince aşağıdaki yer tutucular gerçek değerle değiştirilir
        self._energy_per_m = energy_per_meter   # TBD-PLAN-003
        self._thermal_coeff = thermal_coeff     # TBD-PLAN-004
        self._risk_coeff = risk_coeff           # TBD-PLAN-005

    def edge_cost(
        self,
        from_state: PlannerState,
        to_state: PlannerState,
        terrain_slope_deg: float,
        obstacle_fraction: float,  # HC-003: ≤ 0.20
    ) -> float:
        """
        İki durum arasındaki birleşik maliyet.
        HC-003 hard constraint ihlali: sonsuz maliyet döner (engel yoğunluğu > 0.20).
        """
        if obstacle_fraction > 0.20:  # HC-003 hard constraint
            return math.inf

        dist = from_state.distance_to(to_state)

        # Enerji maliyet: eğim açısını hesaba katan basitleştirilmiş model
        # Gerçek model: Güç Yönetimi tarafından sağlanır (TBD-PLAN-003)
        slope_factor = 1.0 + abs(math.sin(math.radians(terrain_slope_deg)))
        energy_cost = dist * slope_factor  # Wh/m × mesafe; katsayı TBD-PLAN-003

        # Termal maliyet: PSR içinde artan baskı (TBD-PLAN-004)
        thermal_cost = 0.0
        if to_state.termal_durum == ThermalState.CAUTION:
            thermal_cost = dist * 0.5   # placeholder; TBD-PLAN-004
        elif to_state.termal_durum == ThermalState.CRITICAL:
            thermal_cost = dist * 5.0   # yüksek ceza; TBD-PLAN-004

        # Risk maliyet: eğim ve engel yakınlığı (TBD-PLAN-005)
        risk_cost = obstacle_fraction * dist  # placeholder; TBD-PLAN-005

        return (self.w_dist * dist
                + self.w_energy * energy_cost
                + self.w_thermal * thermal_cost
                + self.w_risk * risk_cost)

    def heuristic(self, state: PlannerState, goal: PlannerState, w: float = 1.0) -> float:
        """
        Weighted A* heuristiği: Öklid mesafesi × ağırlık.
        w > 1 ile suboptimal ama hızlı arama; QAR-PLAN-001 (< 60 s) uyumu.
        w = TBD-PLAN-001.
        """
        return w * state.distance_to(goal)


# ---------------------------------------------------------------------------
# ResourceConstrainedAStar — Kaynak-Kısıtlı A* Temel Yapısı
# ---------------------------------------------------------------------------

class ResourceConstrainedAStar:
    """
    Kaynak-kısıtlı A* planlayıcı.
    Ref: autonomy/mission_planner.md §2, ADR-001

    Temel fark klasik A*'dan: her düğümde enerji ve termal durumu ileri
    simülasyonla takip eder; dönüş rezervi kısıtını erken budama olarak uygular.
    """

    def __init__(
        self,
        cost_model: CostModel,
        energy_budget: EnergyBudget,
        heuristic_weight: float = 1.0,  # TBD-PLAN-001
        grid_resolution_m: float = 1.0,
    ):
        self.cost_model = cost_model
        self.energy_budget = energy_budget
        self.w = heuristic_weight  # TBD-PLAN-001
        self.resolution = grid_resolution_m

    def plan(
        self,
        start: PlannerState,
        goal: Tuple[float, float],
        occupancy_grid: Dict[Tuple[int, int], float],  # (ix, iy) → obstacle_fraction
        terrain_slope_grid: Dict[Tuple[int, int], float],  # (ix, iy) → slope_deg
        safe_haven_coords: List[Tuple[float, float]],
    ) -> Optional[WaypointPlan]:
        """
        A* araması. Dönüş rezervi kısıtı her genişleme adımında kontrol edilir.

        Returns:
            WaypointPlan veya None (çözüm bulunamadıysa)
        """
        import time
        t_start = time.time()

        goal_state = PlannerState(goal[0], goal[1], 0, 0)  # saptama için

        # Öncelik kuyruğu: (f_score, state)
        open_set: list = []
        heapq.heappush(open_set, (0.0, id(start), start))

        came_from: Dict[PlannerState, Optional[PlannerState]] = {start: None}
        g_score: Dict[PlannerState, float] = {start: 0.0}

        while open_set:
            _, _, current = heapq.heappop(open_set)

            # Hedef kontrolü
            if current.distance_to(goal_state) < self.resolution:
                plan = self._reconstruct_path(came_from, current)
                plan.planning_time_s = time.time() - t_start
                return plan  # QAR-PLAN-001: süre < 60 s olmalı

            for neighbor, slope, obstacle_frac in self._get_neighbors(
                current, occupancy_grid, terrain_slope_grid
            ):
                # --- Dönüş rezervi kısıtı (HC-006) ---
                return_energy = self._estimate_return_energy(
                    neighbor, safe_haven_coords
                )
                if neighbor.enerji_wh - return_energy < self.energy_budget.return_reserve_wh:
                    # Bu düğüme gidersek dönüş enerjisi yetersiz kalır → eleme
                    continue

                tentative_g = g_score[current] + self.cost_model.edge_cost(
                    current, neighbor, slope, obstacle_frac
                )

                if tentative_g < g_score.get(neighbor, math.inf):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.cost_model.heuristic(neighbor, goal_state, self.w)
                    heapq.heappush(open_set, (f, id(neighbor), neighbor))

        return None  # Çözüm bulunamadı

    def _get_neighbors(
        self,
        state: PlannerState,
        occupancy_grid: Dict,
        slope_grid: Dict,
    ):
        """
        Komşu düğümleri üret (8-bağlantılı ızgara).
        Her komşu için (PlannerState, slope_deg, obstacle_fraction) tuple döner.
        Gerçek implementasyonda kinematik kısıtlar ve tekerlek açısı limitleri eklenir.
        """
        # Pseudocode: gerçek grid traversal burada yer alır
        neighbors = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx = state.konum_x + dx * self.resolution
            ny = state.konum_y + dy * self.resolution
            grid_key = (int(nx / self.resolution), int(ny / self.resolution))
            slope = slope_grid.get(grid_key, 0.0)
            obs_frac = occupancy_grid.get(grid_key, 0.0)

            # HC-005: eğim limiti kontrolü (threshold: TBD-TRV-002)
            # if slope > TBD_TRV_002_max_slope: continue

            dist = math.sqrt(dx**2 + dy**2) * self.resolution
            energy_consumed = dist * self.energy_budget.energy_per_meter
            new_energy = state.enerji_wh - energy_consumed

            neighbor = PlannerState(
                konum_x=nx,
                konum_y=ny,
                zaman=state.zaman + dist / 0.1,  # TBD-TRV-001: nominal hız
                enerji_wh=new_energy,
                termal_durum=state.termal_durum,  # Gerçek modelde termal simülasyon
                guvenlik_seviyesi=state.guvenlik_seviyesi,
            )
            neighbors.append((neighbor, slope, obs_frac))
        return neighbors

    def _estimate_return_energy(
        self,
        state: PlannerState,
        safe_haven_coords: List[Tuple[float, float]],
    ) -> float:
        """
        Verilen konumdan en yakın safe haven'a olan minimum enerji tahmini.
        Güç Yönetimi modeli kullanılır (Uyum Notu 3: bağımsız hesaplanmaz).
        Bu pseudocode basitleştirilmiş Öklid tahminini gösterir.
        """
        if not safe_haven_coords:
            return math.inf
        min_dist = min(
            math.sqrt((state.konum_x - sx)**2 + (state.konum_y - sy)**2)
            for sx, sy in safe_haven_coords
        )
        # Gerçek implementasyon: Güç Yönetimi'nden return_reserve_wh alır (ICD-002)
        return min_dist * self.energy_budget.energy_per_meter

    def _reconstruct_path(
        self,
        came_from: Dict,
        current: PlannerState,
    ) -> WaypointPlan:
        """Geriye takip ederek waypoint listesi oluştur."""
        path = []
        node = current
        while node is not None:
            path.append((node.konum_x, node.konum_y))
            node = came_from.get(node)
        path.reverse()
        # Enerji profili: pseudocode placeholder
        return WaypointPlan(
            waypoints=path,
            estimated_energy_wh=[0.0] * len(path),
            total_distance_m=sum(
                math.sqrt((path[i][0]-path[i-1][0])**2 + (path[i][1]-path[i-1][1])**2)
                for i in range(1, len(path))
            ),
            planning_time_s=0.0,
        )

    def evaluate_replan_decision(
        self,
        current_state: PlannerState,
        blocked_waypoints: int,
        safety_transition: bool,
        return_margin_ratio: float,
    ) -> PlanDecision:
        """
        Tam yeniden plan mı, lokal düzeltme mi?
        Ref: autonomy/mission_planner.md §4.1
        """
        if safety_transition:
            # FDIR güvenlik durumu değişti → zorunlu tam yeniden plan
            if current_state.guvenlik_seviyesi == SafetyLevel.RETURN_REQUIRED:
                return PlanDecision.ABORT_RETURN
            return PlanDecision.FULL_REPLAN

        if return_margin_ratio <= 1.1:
            # Dönüş marjı %110 erken uyarı eşiği → dönüş odaklı yeniden plan
            return PlanDecision.DIRECTED_REPLAN

        if blocked_waypoints > 2:
            # Birden fazla ardışık engel → tam yeniden plan
            return PlanDecision.FULL_REPLAN

        # Tek engel → lokal düzeltme
        return PlanDecision.LOCAL_CORRECTION


# ---------------------------------------------------------------------------
# SafeHavenSelector — Safe Haven Puanlama Fonksiyonu
# ---------------------------------------------------------------------------

@dataclass
class SafeHavenCandidate:
    """Aday safe haven konumu ve ham metrik değerleri."""
    coord: Tuple[float, float]
    illumination_hr: float            # HC-009: TBD-PLAN-006
    max_darkness_hr: float            # HC-010
    recharge_wh_per_sol: float        # HC-011: TBD-PLAN-007
    return_distance_m: float          # HC-012: mesafe × energy_per_m + marj
    thermal_safe: bool                # HC-013
    comm_visibility_min_per_sol: float  # HC-014
    emergency_route_distance_m: float  # HC-015


class SafeHavenSelector:
    """
    Safe haven seçici: HC-009..HC-015 hard constraint eleme + ağırlıklı puanlama.
    Ref: autonomy/mission_planner.md §5

    Önemli: HC kümesi geçilmeyen adaylar puanlamaya alınmaz (HC katalog preamble).
    """

    # HC eşikleri: §10 araç verisi geldikçe TBD'ler kapanır
    HC009_MIN_ILLUMINATION_HR = None     # TBD-PLAN-006 / SHV-001
    HC010_MAX_DARKNESS_HR = None         # TBD §10 termal
    HC011_MIN_RECHARGE_WH_SOL = None     # TBD-PLAN-007
    HC013_THERMAL_SAFE_REQUIRED = True   # boolean hard constraint
    HC014_MIN_COMM_MIN_SOL = None        # TBD §10 iletişim
    HC015_MAX_EMERGENCY_DIST_M = None    # TBD §10

    # Puanlama ağırlıkları (toplam 1.0)
    W1_ILLUMINATION = 0.20
    W2_RECHARGE = 0.20
    W3_RETURN_ENERGY = 0.20
    W4_THERMAL = 0.15
    W5_COMM = 0.15
    W6_EMERGENCY_ROUTE = 0.05
    W7_DARKNESS_PENALTY = 0.05

    def __init__(self, energy_budget: EnergyBudget):
        self.energy_budget = energy_budget

    def _passes_hard_constraints(self, candidate: SafeHavenCandidate) -> bool:
        """
        HC-009..HC-015 hard constraint pass/fail kontrolü.
        Herhangi bir HC başarısız olursa False döner; aday elenir.
        """
        # HC-009: minimum kesintisiz aydınlanma
        if (self.HC009_MIN_ILLUMINATION_HR is not None and
                candidate.illumination_hr < self.HC009_MIN_ILLUMINATION_HR):
            return False

        # HC-010: maksimum karanlık aralığı
        if (self.HC010_MAX_DARKNESS_HR is not None and
                candidate.max_darkness_hr > self.HC010_MAX_DARKNESS_HR):
            return False

        # HC-011: yeniden şarj kapasitesi
        if (self.HC011_MIN_RECHARGE_WH_SOL is not None and
                candidate.recharge_wh_per_sol < self.HC011_MIN_RECHARGE_WH_SOL):
            return False

        # HC-012: dönüş enerjisi yeterliliği
        required_return_energy = (candidate.return_distance_m *
                                   self.energy_budget.energy_per_meter +
                                   self.energy_budget.return_reserve_wh)
        if self.energy_budget.current_soc_wh < required_return_energy:
            return False

        # HC-013: termal güvenlik
        if self.HC013_THERMAL_SAFE_REQUIRED and not candidate.thermal_safe:
            return False

        # HC-014: haberleşme görüş olanağı
        if (self.HC014_MIN_COMM_MIN_SOL is not None and
                candidate.comm_visibility_min_per_sol < self.HC014_MIN_COMM_MIN_SOL):
            return False

        # HC-015: acil erişim mesafesi
        if (self.HC015_MAX_EMERGENCY_DIST_M is not None and
                candidate.emergency_route_distance_m > self.HC015_MAX_EMERGENCY_DIST_M):
            return False

        return True

    def _score(self, candidate: SafeHavenCandidate, max_values: Dict) -> float:
        """
        Normalize edilmiş ağırlıklı puan hesabı.
        Tüm bileşenler [0, 1] aralığına normalize edilir.
        """
        # Normalize: yüksek aydınlanma → yüksek puan
        s_illumination = min(1.0, candidate.illumination_hr /
                             max(max_values.get("illumination_hr", 1), 1))

        # Normalize: yüksek şarj kapasitesi → yüksek puan
        s_recharge = min(1.0, candidate.recharge_wh_per_sol /
                         max(max_values.get("recharge_wh_per_sol", 1), 1))

        # Normalize: kısa dönüş mesafesi → yüksek puan
        s_return = 1.0 - min(1.0, candidate.return_distance_m /
                             max(max_values.get("return_distance_m", 1), 1))

        # Termal güvenlik: boolean → 1.0 veya 0.0
        s_thermal = 1.0 if candidate.thermal_safe else 0.0

        # Normalize: yüksek haberleşme penceresi → yüksek puan
        s_comm = min(1.0, candidate.comm_visibility_min_per_sol /
                     max(max_values.get("comm_visibility_min_per_sol", 1), 1))

        # Normalize: kısa acil rota → yüksek puan
        s_emergency = 1.0 - min(1.0, candidate.emergency_route_distance_m /
                                max(max_values.get("emergency_route_distance_m", 1), 1))

        # Karanlık cezası: düşük karanlık → yüksek puan
        s_darkness = 1.0 - min(1.0, candidate.max_darkness_hr /
                               max(max_values.get("max_darkness_hr", 1), 1))

        return (self.W1_ILLUMINATION * s_illumination
                + self.W2_RECHARGE * s_recharge
                + self.W3_RETURN_ENERGY * s_return
                + self.W4_THERMAL * s_thermal
                + self.W5_COMM * s_comm
                + self.W6_EMERGENCY_ROUTE * s_emergency
                + self.W7_DARKNESS_PENALTY * s_darkness)

    def select(
        self,
        candidates: List[SafeHavenCandidate],
    ) -> Optional[SafeHavenCandidate]:
        """
        1. HC-009..HC-015 hard constraint eleme
        2. Geçenler arasında ağırlıklı puanlama
        3. En yüksek puanlı adayı döner; geçen yoksa None

        Returns:
            En iyi SafeHavenCandidate veya None
        """
        qualifying = [c for c in candidates if self._passes_hard_constraints(c)]

        if not qualifying:
            return None  # Kritik durum: safe haven bulunamadı → FDIR'a bildir

        # Normalize için maksimum değerleri hesapla
        max_values = {
            "illumination_hr": max(c.illumination_hr for c in qualifying),
            "recharge_wh_per_sol": max(c.recharge_wh_per_sol for c in qualifying),
            "return_distance_m": max(c.return_distance_m for c in qualifying),
            "comm_visibility_min_per_sol": max(c.comm_visibility_min_per_sol for c in qualifying),
            "emergency_route_distance_m": max(c.emergency_route_distance_m for c in qualifying),
            "max_darkness_hr": max(c.max_darkness_hr for c in qualifying),
        }

        scored = [(self._score(c, max_values), c) for c in qualifying]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]


# ---------------------------------------------------------------------------
# ReplanningDecisionModule — Tetikleyici ve Karar Modülü
# ---------------------------------------------------------------------------

class ReplanningDecisionModule:
    """
    Replanning tetikleyicileri ve lokal/global karar mantığı.
    Ref: autonomy/mission_planner.md §4
    QAR-PLAN-002: replanning süresi < 30 s
    """

    # QAR-PLAN-002: replanning süresi hedefi
    REPLAN_TIME_TARGET_S = 30.0

    # QAR-PLAN-005: dönüş marjı izleme frekansı
    RETURN_MARGIN_CHECK_HZ = 1.0

    # Lokal kaçınma mesafesi eşiği (TBD-PLAN-002 ile ilişkili)
    LOCAL_DEVIATION_MAX_M = 20.0  # placeholder; TBD

    def check_triggers(
        self,
        current_state: PlannerState,
        blocked_waypoints: int,
        hc006_threshold_wh: float,
        return_energy_wh: float,
        safety_transition: bool,
        safe_haven_changed: bool,
    ) -> PlanDecision:
        """
        Replanning tetikleyici koşullarını değerlendir.
        Ref: autonomy/mission_planner.md §4.1

        ABT serisi abort trigger'ları (otonomi matrisi) kontrol edilir:
        - ABT-001: return_reserve_wh < HC-006
        - ABT-002: position_uncertainty > QAR-NAV-004 eşiği
        """
        # ABT-001: dönüş rezervi kritik → zorunlu dönüş
        available_energy = current_state.enerji_wh - return_energy_wh
        if available_energy < hc006_threshold_wh:
            return PlanDecision.ABORT_RETURN

        # Güvenlik durumu geçişi → plan geçersiz
        if safety_transition:
            if current_state.guvenlik_seviyesi == SafetyLevel.RETURN_REQUIRED:
                return PlanDecision.ABORT_RETURN
            return PlanDecision.FULL_REPLAN

        # Safe haven koordinatı değişti
        if safe_haven_changed:
            return PlanDecision.FULL_REPLAN

        # Dönüş marjı %110 erken uyarı
        return_margin_ratio = current_state.enerji_wh / max(hc006_threshold_wh, 1e-9)
        if return_margin_ratio <= 1.1:
            return PlanDecision.DIRECTED_REPLAN

        # Birden fazla ardışık engel
        if blocked_waypoints > 2:
            return PlanDecision.FULL_REPLAN

        # Tek engel → lokal düzeltme
        if blocked_waypoints > 0:
            return PlanDecision.LOCAL_CORRECTION

        return PlanDecision.LOCAL_CORRECTION  # Nominal: değişiklik yok


# ---------------------------------------------------------------------------
# ScienceScheduler — Bilimsel Hedef vs Kaynak Dengesi
# ---------------------------------------------------------------------------

@dataclass
class ScienceTask:
    """Tek bir bilimsel görev."""
    task_id: str
    priority: int           # 1 = en düşük, 4 = asla otomatik iptal (numune)
    energy_cost_wh: float
    is_optional: bool


class ScienceScheduler:
    """
    Bilimsel görev sıralama ve iptal mantığı.
    Ref: autonomy/mission_planner.md §7
    TBD-PLAN-009: öncelik ağırlıkları yer segmenti görev paketinden belirlenir.
    """

    def filter_executable_tasks(
        self,
        tasks: List[ScienceTask],
        current_state: PlannerState,
        available_energy_wh: float,
    ) -> List[ScienceTask]:
        """
        Mevcut güvenlik durumu ve enerji bütçesine göre çalıştırılabilir görev listesi.
        Ref: autonomy/mission_planner.md §7.2 iptal kuralları
        """
        if current_state.guvenlik_seviyesi == SafetyLevel.RETURN_REQUIRED:
            # Tüm bilim operasyonları dondurulur
            return []

        if current_state.guvenlik_seviyesi == SafetyLevel.SURVIVAL:
            # Hiçbir bilim görevi çalışmaz
            return []

        eligible = []
        for task in tasks:
            # Güvenlik durumu CAUTION: yüksek güçlü bilim sensörü başlatılamaz
            if (current_state.guvenlik_seviyesi == SafetyLevel.CAUTION
                    and task.energy_cost_wh > 10.0):  # eşik: TBD-PLAN-009
                continue

            # Enerji bütçesi kontrolü
            if task.energy_cost_wh > available_energy_wh:
                continue

            # Öncelik 4 (numune): asla otomatik iptal
            if task.priority == 4:
                eligible.append(task)
                continue

            # Diğer görevler: enerji ve durum uygunsa ekle
            eligible.append(task)

        # Öncelik sıralaması: yüksek öncelik önce
        eligible.sort(key=lambda t: t.priority, reverse=True)
        return eligible
