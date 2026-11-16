"""
核心排班求解層 (solvers.py) — 極致最佳化版
提供兩種演算法實作：
1. BitmaskMRVSolver：
   位元遮罩狀態壓縮 + 最小剩餘價值啟發式 (MRV) 回溯法。
   【最佳化重點】：
   - 將遞迴熱路徑 (Hot Loop) 中的所有狀態轉換為預編譯之定長整數陣列 (Flat Integer Arrays)，
     消除遞迴內部的動態排序 (sorted) 與字典配置 (dict copy)，在 Python 中達到微秒級極速。
2. MaxFlowDinicSolver：
   基於 Dinic 演算法之有向網路最大流求解器，具備 O(E * sqrt(V)) 多項式時間保證。
"""

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .models import Day, Schedule, ScheduleConfig


class BitmaskMRVSolver:
    """
    位元遮罩 + 最小剩餘價值 (MRV, Minimum Remaining Values) 啟發式回溯求解器。
    """

    def __init__(self, config: ScheduleConfig) -> None:
        self.config = config
        self.employees = config.employees
        self.num_employees = len(self.employees)
        self.required_days = config.required_days
        self.max_days = config.max_days_per_employee
        self.emp_names: Tuple[str, ...] = tuple(e.name for e in self.employees)

        # 建立每一天的可用員工索引清單
        self.day_candidates: Dict[Day, Tuple[int, ...]] = {}
        for day in self.required_days:
            candidates = tuple(
                idx
                for idx, emp in enumerate(self.employees)
                if emp.is_available(day)
            )
            self.day_candidates[day] = candidates

        # MRV 啟發式排序：優先排可用員工數最少的日子（預先轉為 Tuple 避免熱迴圈額外開銷）
        self.ordered_days: Tuple[Day, ...] = tuple(
            sorted(
                self.required_days,
                key=lambda d: (len(self.day_candidates[d]), int(d)),
            )
        )
        self.ordered_candidates: Tuple[Tuple[int, ...], ...] = tuple(
            self.day_candidates[d] for d in self.ordered_days
        )

        # 紀錄最近一次求解所展開的搜尋節點數
        self.last_nodes_explored: int = 0

    def solve_one(self) -> Optional[Schedule]:
        """快速找出一組合法班表。若無解則回傳 None。"""
        results: List[Schedule] = []
        self._search(limit=1, results=results)
        return results[0] if results else None

    def solve_all(self, max_solutions: int = 10000) -> List[Schedule]:
        """枚舉所有合法的排班表（最多回傳 max_solutions 組）。"""
        results: List[Schedule] = []
        self._search(limit=max_solutions, results=results)
        return results

    def _search(self, limit: int, results: List[Schedule]) -> None:
        """
        內部回溯搜尋核心（零動態容器配置最佳化版）。
        在遞迴過程中僅操作定長整數 List，只在到達葉節點（找到合法解）時才建構 Schedule 物件。
        """
        self.last_nodes_explored = 0
        ordered_days = self.ordered_days
        ordered_candidates = self.ordered_candidates
        num_days = len(ordered_days)
        max_days = self.max_days
        emp_names = self.emp_names

        for cands in ordered_candidates:
            if not cands:
                return

        work_counts = [0] * self.num_employees
        chosen_emp_indices = [0] * num_days
        nodes = 0

        def backtrack(step_idx: int) -> bool:
            nonlocal nodes
            if step_idx == num_days:
                assignments = {
                    ordered_days[i]: emp_names[chosen_emp_indices[i]]
                    for i in range(num_days)
                }
                results.append(Schedule(assignments=assignments))
                return len(results) >= limit

            nodes += 1
            for emp_idx in ordered_candidates[step_idx]:
                cnt = work_counts[emp_idx]
                if cnt < max_days:
                    work_counts[emp_idx] = cnt + 1
                    chosen_emp_indices[step_idx] = emp_idx

                    if backtrack(step_idx + 1):
                        return True

                    work_counts[emp_idx] = cnt

            return False

        backtrack(0)
        self.last_nodes_explored = nodes


@dataclass
class _FlowEdge:
    """Dinic 最大流演算法之有向邊結構。"""
    to: int
    rev: int
    cap: int
    flow: int = 0


class MaxFlowDinicSolver:
    """
    基於 Dinic 演算法之網路最大流排班求解器。
    時間複雜度：O(E * sqrt(V))，具備優異的多項式時間擴展性。
    """

    def __init__(self, config: ScheduleConfig) -> None:
        self.config = config
        self.employees = config.employees
        self.required_days = config.required_days
        self.num_emp = len(self.employees)
        self.num_days = len(self.required_days)

        self.source = 0
        self.emp_offset = 1
        self.day_offset = 1 + self.num_emp
        self.sink = 1 + self.num_emp + self.num_days
        self.total_nodes = self.sink + 1

        self.graph: List[List[_FlowEdge]] = [[] for _ in range(self.total_nodes)]
        self._build_network()

    def _add_edge(self, u: int, v: int, cap: int) -> None:
        forward = _FlowEdge(to=v, rev=len(self.graph[v]), cap=cap, flow=0)
        backward = _FlowEdge(to=u, rev=len(self.graph[u]), cap=0, flow=0)
        self.graph[u].append(forward)
        self.graph[v].append(backward)

    def _build_network(self) -> None:
        for i in range(self.num_emp):
            self._add_edge(self.source, self.emp_offset + i, self.config.max_days_per_employee)

        for i, emp in enumerate(self.employees):
            u = self.emp_offset + i
            for j, day in enumerate(self.required_days):
                if emp.is_available(day):
                    v = self.day_offset + j
                    self._add_edge(u, v, 1)

        for j in range(self.num_days):
            self._add_edge(self.day_offset + j, self.sink, 1)

    def _bfs_level_graph(self, level: List[int]) -> bool:
        for i in range(self.total_nodes):
            level[i] = -1
        level[self.source] = 0
        queue: deque[int] = deque([self.source])

        while queue:
            u = queue.popleft()
            for edge in self.graph[u]:
                if edge.cap - edge.flow > 0 and level[edge.to] < 0:
                    level[edge.to] = level[u] + 1
                    queue.append(edge.to)

        return level[self.sink] >= 0

    def _dfs_augment(self, u: int, pushed: int, level: List[int], ptr: List[int]) -> int:
        if pushed == 0 or u == self.sink:
            return pushed

        while ptr[u] < len(self.graph[u]):
            cid = ptr[u]
            edge = self.graph[u][cid]
            tr = edge.to
            if level[u] + 1 == level[tr] and edge.cap - edge.flow > 0:
                tr_pushed = self._dfs_augment(
                    tr, min(pushed, edge.cap - edge.flow), level, ptr
                )
                if tr_pushed > 0:
                    edge.flow += tr_pushed
                    self.graph[tr][edge.rev].flow -= tr_pushed
                    return tr_pushed
            ptr[u] += 1

        return 0

    def solve(self) -> Optional[Schedule]:
        max_flow = 0
        level = [-1] * self.total_nodes

        while self._bfs_level_graph(level):
            ptr = [0] * self.total_nodes
            while True:
                pushed = self._dfs_augment(self.source, 10**9, level, ptr)
                if pushed == 0:
                    break
                max_flow += pushed

        if max_flow < self.num_days:
            return None

        assignments: Dict[Day, str] = {}
        for i, emp in enumerate(self.employees):
            u = self.emp_offset + i
            for edge in self.graph[u]:
                if self.day_offset <= edge.to < self.sink and edge.flow == 1:
                    day_idx = edge.to - self.day_offset
                    day = self.required_days[day_idx]
                    assignments[day] = emp.name

        return Schedule(assignments=assignments)
