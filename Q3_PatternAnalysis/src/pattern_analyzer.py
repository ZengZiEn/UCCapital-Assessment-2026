"""
多維度規律探勘與特徵分析引擎 (pattern_analyzer.py)
針對題目三的 9x5 四色矩陣進行六大維度之演算法分析：
1. 圖論正交四色著色檢驗 (Orthogonal Proper 4-Coloring Verification)
2. 全域與邊際配額均衡與資訊熵分析 (Global/Marginal Quota Bounds & Shannon Entropy)
3. 西洋棋盤二分圖奇偶對稱性檢驗 (Chessboard Bipartite Parity Balance)
4. 右半部 7x3 局部鏡像對稱與雙色交替鏈探勘 (Local Mirror Symmetry & Alternating Chains)
5. 方向異向性與水平/垂直馬可夫轉移矩陣 (Directional Anisotropy & Markov Transition Matrix)
6. 列間漢明距離與演化軌跡分析 (Row-to-Row Hamming Distance & Trajectory)
"""

from collections import Counter
from dataclasses import dataclass
import math
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class PatternAnalysisReport:
    """六大維度特徵與規律分析完整報告結構。"""
    rows: int
    cols: int
    grid: Tuple[Tuple[str, ...], ...]
    # 1. 圖論正交與對角邊統計
    total_horizontal_edges: int
    total_vertical_edges: int
    orthogonal_same_color_conflicts: int
    diagonal_same_color_matches: int
    # 2. 全域與行列配額統計
    global_counts: Dict[str, int]
    global_entropy_bits: float
    row_counts: Tuple[Dict[str, int], ...]
    col_counts: Tuple[Dict[str, int], ...]
    max_count_in_any_row: int
    max_count_in_any_col: int
    min_distinct_colors_in_row: int
    min_distinct_colors_in_col: int
    # 3. 棋盤奇偶二分統計
    even_parity_counts: Dict[str, int]
    odd_parity_counts: Dict[str, int]
    # 4. 鏡像對稱與交替鏈
    right_3col_symmetric_rows: Tuple[int, ...]
    alternating_last4_rows: Tuple[int, ...]
    # 5. 水平與垂直邊配對分布
    horizontal_pair_counts: Dict[Tuple[str, str], int]
    vertical_pair_counts: Dict[Tuple[str, str], int]
    horizontal_warm_cool_within_ratio: float
    vertical_warm_cool_within_ratio: float
    # 6. 列間高相似度配對 (Hamming Distance <= 1)
    near_identical_row_pairs: Tuple[Tuple[int, int, int], ...]


class GridPatternAnalyzer:
    """9x5 四色矩陣之演算法特徵萃取器。"""

    WARM_COLORS = {"R", "Y"}
    COOL_COLORS = {"G", "B"}

    def __init__(self, symbol_grid: Tuple[Tuple[str, ...], ...]) -> None:
        self.grid = symbol_grid
        self.rows = len(symbol_grid)
        self.cols = len(symbol_grid[0]) if self.rows > 0 else 0

    @staticmethod
    def _shannon_entropy(counts: Dict[str, int]) -> float:
        """計算離散分布之資訊熵 (Shannon Entropy, 單位 bits，最大為 log2(4) = 2.0 bits)。"""
        total = sum(counts.values())
        if total == 0:
            return 0.0
        ent = 0.0
        for c in counts.values():
            if c > 0:
                p = c / total
                ent -= p * math.log2(p)
        return ent

    def analyze(self) -> PatternAnalysisReport:
        """執行完整多維度規律探勘並回傳結構化報告。"""
        # 1. 正交與對角相鄰衝突檢驗 + 方向配對統計
        h_edges = 0
        v_edges = 0
        ortho_conflicts = 0
        diag_matches = 0
        h_pairs: Counter[Tuple[str, str]] = Counter()
        v_pairs: Counter[Tuple[str, str]] = Counter()

        for r in range(self.rows):
            for c in range(self.cols):
                curr = self.grid[r][c]
                # 水平相鄰 (r, c) <-> (r, c+1)
                if c + 1 < self.cols:
                    h_edges += 1
                    right = self.grid[r][c + 1]
                    if curr == right:
                        ortho_conflicts += 1
                    pair = (curr, right) if curr <= right else (right, curr)
                    h_pairs[pair] += 1

                # 垂直相鄰 (r, c) <-> (r+1, c)
                if r + 1 < self.rows:
                    v_edges += 1
                    down = self.grid[r + 1][c]
                    if curr == down:
                        ortho_conflicts += 1
                    pair = (curr, down) if curr <= down else (down, curr)
                    v_pairs[pair] += 1

                # 對角相鄰
                if r + 1 < self.rows and c + 1 < self.cols:
                    if curr == self.grid[r + 1][c + 1]:
                        diag_matches += 1
                if r + 1 < self.rows and c - 1 >= 0:
                    if curr == self.grid[r + 1][c - 1]:
                        diag_matches += 1

        # 2. 全域與邊際配額統計
        flat = [self.grid[r][c] for r in range(self.rows) for c in range(self.cols)]
        global_counts = dict(Counter(flat))
        global_ent = self._shannon_entropy(global_counts)

        row_counts_list: List[Dict[str, int]] = []
        max_in_row = 0
        min_distinct_row = 4
        for r in range(self.rows):
            rc = dict(Counter(self.grid[r]))
            row_counts_list.append(rc)
            max_in_row = max(max_in_row, max(rc.values()))
            min_distinct_row = min(min_distinct_row, len(rc))

        col_counts_list: List[Dict[str, int]] = []
        max_in_col = 0
        min_distinct_col = 4
        for c in range(self.cols):
            col_vals = [self.grid[r][c] for r in range(self.rows)]
            cc = dict(Counter(col_vals))
            col_counts_list.append(cc)
            max_in_col = max(max_in_col, max(cc.values()))
            min_distinct_col = min(min_distinct_col, len(cc))

        # 3. 西洋棋盤奇偶二分圖平衡檢驗
        even_counter: Counter[str] = Counter()
        odd_counter: Counter[str] = Counter()
        for r in range(self.rows):
            for c in range(self.cols):
                if (r + c) % 2 == 0:
                    even_counter[self.grid[r][c]] += 1
                else:
                    odd_counter[self.grid[r][c]] += 1

        # 4. 右半部 3 欄 (Col 2, 3, 4) 鏡像對稱性與後 4 格交替鏈檢測
        sym_rows: List[int] = []
        alt_rows: List[int] = []
        for r in range(self.rows):
            if self.grid[r][2] == self.grid[r][4]:
                sym_rows.append(r)
            # 檢查後 4 格 (c=1,2,3,4) 或全列是否只由 2 種顏色交錯構成
            last4_distinct = len(set(self.grid[r][1:]))
            if last4_distinct == 2:
                alt_rows.append(r)

        # 5. 計算同色系群內轉移比例 (冷色群 {B, G} 與暖色群 {R, Y})
        h_within = h_pairs.get(("B", "G"), 0) + h_pairs.get(("R", "Y"), 0)
        v_within = v_pairs.get(("B", "G"), 0) + v_pairs.get(("R", "Y"), 0)
        h_within_ratio = h_within / h_edges if h_edges > 0 else 0.0
        v_within_ratio = v_within / v_edges if v_edges > 0 else 0.0

        # 6. 列與列之間的漢明距離 (找出僅差 1 格的高相似度演化列對)
        near_pairs: List[Tuple[int, int, int]] = []
        for r1 in range(self.rows):
            for r2 in range(r1 + 1, self.rows):
                diff = sum(
                    1 for c in range(self.cols) if self.grid[r1][c] != self.grid[r2][c]
                )
                if diff <= 2:
                    near_pairs.append((r1, r2, diff))

        return PatternAnalysisReport(
            rows=self.rows,
            cols=self.cols,
            grid=self.grid,
            total_horizontal_edges=h_edges,
            total_vertical_edges=v_edges,
            orthogonal_same_color_conflicts=ortho_conflicts,
            diagonal_same_color_matches=diag_matches,
            global_counts=global_counts,
            global_entropy_bits=global_ent,
            row_counts=tuple(row_counts_list),
            col_counts=tuple(col_counts_list),
            max_count_in_any_row=max_in_row,
            max_count_in_any_col=max_in_col,
            min_distinct_colors_in_row=min_distinct_row,
            min_distinct_colors_in_col=min_distinct_col,
            even_parity_counts=dict(even_counter),
            odd_parity_counts=dict(odd_counter),
            right_3col_symmetric_rows=tuple(sym_rows),
            alternating_last4_rows=tuple(alt_rows),
            horizontal_pair_counts=dict(h_pairs),
            vertical_pair_counts=dict(v_pairs),
            horizontal_warm_cool_within_ratio=h_within_ratio,
            vertical_warm_cool_within_ratio=v_within_ratio,
            near_identical_row_pairs=tuple(near_pairs),
        )

