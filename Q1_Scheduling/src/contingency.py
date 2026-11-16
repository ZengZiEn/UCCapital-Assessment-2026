"""
突發狀況應變與容錯引擎 (contingency.py)
負責處理題目第 3 點：
「在排好班表後，可能會有一位員工臨時說：『這週我有某一天不能上了』」

包含三大核心元件：
1. IncrementalRepairEngine：基於殘餘網路 BFS 最短交替路徑之局部修復引擎（保證最小化班表變動天數）。
2. RobustScheduleSelector：對所有可行初始班表進行全情境壓力模擬，選出韌性最高（最容易修復）的推薦班表。
3. ContingencyTable：預先計算並快取所有突發請假情境的 O(1) 應變查找表。
"""

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .models import Day, Schedule, ScheduleConfig
from .solvers import BitmaskMRVSolver


@dataclass(frozen=True)
class RepairResult:
    """
    突發請假事件之修復結果封裝。
    """
    absent_employee: str
    absent_day: Day
    was_scheduled: bool
    is_recoverable: bool
    original_schedule: Schedule
    repaired_schedule: Optional[Schedule]
    perturbation_days: int
    repair_type: str
    action_steps: Tuple[str, ...]


class IncrementalRepairEngine:
    """
    增量式局部班表修復引擎 (Incremental Schedule Repair Engine)。

    演算法設計原理：
    當員工 E 在日期 D 臨時無法上班時：
    - Case 0 (0-Hop)：若原班表中日期 D 本來就不是排員工 E，則原班表完全不受影響（變動 0 天）。
    - Case 1 (1-Hop 直接代班)：在當天 D 有空的其他員工中，尋找目前排班天數 < 2 的員工 Y，
      直接由 Y 頂替 D（僅變動 1 天）。
    - Case 2 (k-Hop 殘餘網路最短增廣鏈換班)：若當天 D 有空的其他員工 Y 都已經排滿 2 天，
      則透過 BFS 搜尋一條最短交替路徑：
      「空缺日 D -> 當天有空但已滿額的員工 Y -> Y 原本排班的另一天 D' -> 在 D' 有空且未滿額的員工 Z」
      將 D' 交給 Z、並讓 Y 接手 D（變動 2 天，以此類推）。
    - 由於使用 BFS 搜尋交替路徑，數學上可嚴格保證找到的修復班表與原班表的漢明距離 (Hamming Distance) 最小！
    """

    def __init__(self, base_config: ScheduleConfig) -> None:
        self.base_config = base_config

    def repair(
        self,
        current_schedule: Schedule,
        absent_emp: str,
        absent_day: Day,
    ) -> RepairResult:
        """
        針對單一突發請假事件 (absent_emp 在 absent_day 不能上班) 進行最小變動修復。
        """
        updated_config = self.base_config.with_temporary_unavailable(absent_emp, absent_day)

        # Case 0：請假員工當天本來就沒有被排班 -> 無須變動
        scheduled_emp = current_schedule.get_employee(absent_day)
        if scheduled_emp != absent_emp:
            return RepairResult(
                absent_employee=absent_emp,
                absent_day=absent_day,
                was_scheduled=False,
                is_recoverable=True,
                original_schedule=current_schedule,
                repaired_schedule=current_schedule,
                perturbation_days=0,
                repair_type="0-Hop (原班表未排該員，無須異動)",
                action_steps=(
                    f"{absent_day.label} 原定由 {scheduled_emp} 值班（非 {absent_emp}），維持原班表不變。",
                ),
            )

        # 若該員當天有排班，啟動 BFS 尋找最短交替增廣路徑 (Shortest Alternating Path)
        repaired = self._bfs_shortest_augmenting_chain(
            current_schedule=current_schedule,
            updated_config=updated_config,
            vacant_day=absent_day,
        )

        # 若 BFS 局部增廣失敗（理論上在二部圖 b-matching 中 BFS 已完備，此處保留全域求解作為雙重保險）
        if repaired is None:
            repaired = BitmaskMRVSolver(updated_config).solve_one()

        if repaired is None:
            return RepairResult(
                absent_employee=absent_emp,
                absent_day=absent_day,
                was_scheduled=True,
                is_recoverable=False,
                original_schedule=current_schedule,
                repaired_schedule=None,
                perturbation_days=-1,
                repair_type="無可行解 (Unrecoverable)",
                action_steps=(
                    f"員工 {absent_emp} 在 {absent_day.label} 請假後，違反 Hall 婚姻定理容量限制，無法排出合法班表。",
                ),
            )

        dist = current_schedule.hamming_distance(repaired)
        diffs = tuple(current_schedule.diff_descriptions(repaired))
        if dist == 1:
            r_type = "1-Hop (直接找有空檔且未滿額同仁代班)"
        elif dist == 2:
            r_type = "2-Hop (兩階段連鎖換班代班)"
        else:
            r_type = f"{dist}-Hop (多階段連鎖調度)"

        return RepairResult(
            absent_employee=absent_emp,
            absent_day=absent_day,
            was_scheduled=True,
            is_recoverable=True,
            original_schedule=current_schedule,
            repaired_schedule=repaired,
            perturbation_days=dist,
            repair_type=r_type,
            action_steps=diffs,
        )

    def _bfs_shortest_augmenting_chain(
        self,
        current_schedule: Schedule,
        updated_config: ScheduleConfig,
        vacant_day: Day,
    ) -> Optional[Schedule]:
        """
        在殘餘二部圖上執行 BFS，尋找從 vacant_day 出發到任一「尚有配額餘裕 (workload < max_days)」員工的最短交替鏈。
        交替鏈結構：
          Day_0 (vacant_day) -> Emp_0 -> Day_1 -> Emp_1 -> ... -> Day_k -> Emp_k (free capacity!)
        意義：
          將 Day_0 指派給 Emp_0；若 Emp_0 已滿額，則將 Emp_0 原本負責的某個 Day_1 轉交給 Emp_1...
          直到 Emp_k 本身還有剩餘配額 (< max_days)，即可合法結束增廣！
        """
        emp_map = updated_config.employee_map
        max_days = updated_config.max_days_per_employee

        # 移除 vacant_day 的原指派後，計算每位員工目前的排班天數
        partial_assignments: Dict[Day, str] = {
            d: emp for d, emp in current_schedule.assignments.items() if d != vacant_day
        }
        workload: Dict[str, int] = {emp.name: 0 for emp in updated_config.employees}
        for _, emp_name in partial_assignments.items():
            workload[emp_name] += 1

        # BFS 佇列儲存：(當前待填補的日期, 路徑歷史 [(Day_0, Emp_0), (Day_1, Emp_1), ...])
        queue: deque[Tuple[Day, List[Tuple[Day, str]]]] = deque([(vacant_day, [])])
        visited_days = {vacant_day}
        visited_emps = set()

        while queue:
            curr_day, path = queue.popleft()

            # 找出在 curr_day 有空的所有候選員工（優先檢查尚有剩餘配額的員工以確保最短路徑）
            candidates = [
                emp.name
                for emp in updated_config.employees
                if emp.is_available(curr_day)
                and emp.name != partial_assignments.get(curr_day)
            ]
            candidates.sort(key=lambda name: (workload[name], name))

            for cand_name in candidates:
                new_path = path + [(curr_day, cand_name)]

                # 若該候選員工目前排班數 < 上限 (2天)，代表找到最短增廣路徑！
                if workload[cand_name] < max_days:
                    new_assignments = dict(partial_assignments)
                    for d_step, e_step in new_path:
                        new_assignments[d_step] = e_step
                    return Schedule(assignments=new_assignments)

                # 若該候選員工已滿額，且尚未在本次 BFS 中被展開過，則嘗試將他目前已排的其他日子釋出換人
                if cand_name not in visited_emps:
                    visited_emps.add(cand_name)
                    for assigned_day, owner in partial_assignments.items():
                        if owner == cand_name and assigned_day not in visited_days:
                            visited_days.add(assigned_day)
                            queue.append((assigned_day, new_path))

        return None


@dataclass(frozen=True)
class ScheduleRobustnessReport:
    """單一初始班表在面對所有可能請假事件時的韌性（Robustness）評估報告。"""
    schedule: Schedule
    total_active_assignments: int
    recoverable_count: int
    one_hop_count: int
    two_hop_count: int
    avg_perturbation_when_scheduled: float


class RobustScheduleSelector:
    """
    全解魯棒性評估與最佳初始班表選擇器。
    枚舉所有合法初始班表，模擬每一個「已排班員工臨時請假」的突發事件，
    優先選出：
    1. 突發請假 100% 可修復
    2. 平均變動天數（漢明距離）最小（1-Hop 直接代班比例最高）
    3. 員工工時分配最均衡
    的最佳初始班表。
    """

    def __init__(self, config: ScheduleConfig) -> None:
        self.config = config
        self.repair_engine = IncrementalRepairEngine(config)

    def evaluate_all_schedules(self) -> List[ScheduleRobustnessReport]:
        """評估所有合法班表並依魯棒性由高至低排序。"""
        all_schedules = BitmaskMRVSolver(self.config).solve_all()
        reports: List[ScheduleRobustnessReport] = []

        for sch in all_schedules:
            active_count = len(self.config.required_days)
            recoverable = 0
            one_hop = 0
            two_hop = 0
            total_perturbation = 0

            # 針對班表中每一天的值班人員模擬「臨時當天不能上」
            for day in self.config.required_days:
                emp_name = sch.get_employee(day)
                assert emp_name is not None
                res = self.repair_engine.repair(sch, emp_name, day)
                if res.is_recoverable:
                    recoverable += 1
                    total_perturbation += res.perturbation_days
                    if res.perturbation_days == 1:
                        one_hop += 1
                    elif res.perturbation_days == 2:
                        two_hop += 1

            avg_pert = (
                total_perturbation / recoverable if recoverable > 0 else float("inf")
            )
            reports.append(
                ScheduleRobustnessReport(
                    schedule=sch,
                    total_active_assignments=active_count,
                    recoverable_count=recoverable,
                    one_hop_count=one_hop,
                    two_hop_count=two_hop,
                    avg_perturbation_when_scheduled=avg_pert,
                )
            )

        # 排序準則：可修復數最多 -> 平均變動最小 -> 1-Hop 數最多
        reports.sort(
            key=lambda r: (
                -r.recoverable_count,
                r.avg_perturbation_when_scheduled,
                -r.one_hop_count,
                r.schedule.format_compact(),
            )
        )
        return reports


class ContingencyTable:
    """
    O(1) 預計算突發應變查找表 (Pre-computed Contingency Lookup Table)。
    在排定初始班表後，預先針對每位員工每一個「原本有空的日子」模擬請假並存入雜湊表。
    當線上發生臨時請假時，能以 O(1) 時間複雜度立即給出替代班表。
    """

    def __init__(self, config: ScheduleConfig, baseline_schedule: Schedule) -> None:
        self.config = config
        self.baseline = baseline_schedule
        self.engine = IncrementalRepairEngine(config)
        self._table: Dict[Tuple[str, Day], RepairResult] = {}
        self._precompute()

    def _precompute(self) -> None:
        """預先計算所有 (員工, 原本有空的日子) 之突發請假應變方案。"""
        for emp in self.config.employees:
            for day in emp.available_days:
                self._table[(emp.name, day)] = self.engine.repair(
                    self.baseline, emp.name, day
                )

    def lookup(self, emp_name: str, day: Day) -> RepairResult:
        """以 O(1) 時間複雜度查詢突發請假應變方案。"""
        key = (emp_name, day)
        if key not in self._table:
            raise KeyError(
                f"查詢失敗：員工 {emp_name} 在 {day.label} 原本就沒有空，不屬於有效請假情境。"
            )
        return self._table[key]

    @property
    def all_entries(self) -> List[RepairResult]:
        """回傳所有預計算之突發情境結果清單。"""
        return list(self._table.values())

