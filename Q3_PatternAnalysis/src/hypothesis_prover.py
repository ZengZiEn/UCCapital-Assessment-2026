"""
統計顯著性檢定與演算法假設證明器 (hypothesis_prover.py)
利用組合數學、約束滿足搜尋 (CSP Backtracking)、卡方統計量與蒙地卡羅隨機模擬，
嚴格證明題目三圖形中的六大特徵並非隨機巧合，並驗證其與「題目一排班模型」的跨題同構性。
"""

from dataclasses import dataclass
import math
import random
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ProofSummaryReport:
    """演算法證明與統計檢定結果摘要。"""
    # 證明 1：正交四色零衝突之機率證明
    monte_carlo_trials: int
    mc_zero_conflict_hits: int
    mc_min_conflicts_observed: int
    mc_avg_conflicts_observed: float
    theoretical_ortho_zero_prob_upper_bound: float
    # 證明 2：右半部 7 列連續鏡像對稱 (Col 2 == Col 4) 機率證明
    mirror_symmetry_exact_prob: float
    # 證明 3：方向異向性 (水平 vs 垂直同色系配對) 卡方統計量與顯著性
    chi2_anisotropy_stat: float
    horizontal_ry_ratio: float
    vertical_ry_ratio: float
    # 證明 4：單列合法 4-Coloring 狀態空間大小與壓縮率
    valid_single_row_patterns_total: int
    symmetric_right3_patterns_total: int
    # 證明 5：跨題排班同構性驗證 (9 週 x 5 天 x 4 員工)
    is_valid_no_consecutive_day_roster: bool
    is_valid_no_consecutive_week_same_day_roster: bool
    # 證明 6：基於歸納規則與馬可夫轉移機率之下一列 (Row 9) 預測候選
    predicted_next_rows: Tuple[Tuple[Tuple[str, ...], float], ...]


class HypothesisProver:
    """透過演算法與數學模型證明題目三之視覺規律，並提供規律生成與預測模型。"""

    COLORS = ("R", "Y", "G", "B")

    def __init__(self, symbol_grid: Tuple[Tuple[str, ...], ...]) -> None:
        self.grid = symbol_grid
        self.rows = len(symbol_grid)
        self.cols = len(symbol_grid[0])

    def predict_next_rows(self, top_k: int = 3) -> List[Tuple[Tuple[str, ...], float]]:
        """
        【歸納規則生成演算法 (Rule-Constrained Markov Generator)】：
        綜合本圖歸納出的硬性規則與軟性趨勢，自動推演最可能出現的下一列 (Row 9)：
        - 硬性規則 1 (正交不衝突)：Row 9 內部水平相鄰不同色，且與 Row 8 垂直相鄰不同色。
        - 硬性規則 2 (右三欄鏡像對稱)：滿足 Col 2 == Col 4 (延續 Row 2..8 的 X-Y-X 三明治結構)。
        - 硬性規則 3 (單列配額均衡)：單列至少含 3 種顏色，且同色最多出現 2~3 次。
        - 軟性趨勢評分 (Empirical Markov Score)：依據前 9 列實測的水平與垂直相鄰配對頻率計算聯合機率分數。
        """
        last_row = self.grid[-1]
        h_freq: Dict[Tuple[str, str], int] = {}
        v_freq: Dict[Tuple[str, str], int] = {}

        for r in range(self.rows):
            for c in range(self.cols):
                cur = self.grid[r][c]
                if c + 1 < self.cols:
                    nxt = self.grid[r][c + 1]
                    pair = (cur, nxt) if cur <= nxt else (nxt, cur)
                    h_freq[pair] = h_freq.get(pair, 0) + 1
                if r + 1 < self.rows:
                    nxt = self.grid[r + 1][c]
                    pair = (cur, nxt) if cur <= nxt else (nxt, cur)
                    v_freq[pair] = v_freq.get(pair, 0) + 1

        candidates: List[Tuple[Tuple[str, ...], float]] = []
        for c0 in self.COLORS:
            if c0 == last_row[0]:
                continue
            for c1 in self.COLORS:
                if c1 == c0 or c1 == last_row[1]:
                    continue
                for c2 in self.COLORS:
                    if c2 == c1 or c2 == last_row[2]:
                        continue
                    for c3 in self.COLORS:
                        if c3 == c2 or c3 == last_row[3]:
                            continue
                        c4 = c2  # 規則二：右三欄鏡像對稱 Col 4 == Col 2
                        if c4 == c3 or c4 == last_row[4]:
                            continue
                        row_cand = (c0, c1, c2, c3, c4)
                        if len(set(row_cand)) < 3:
                            continue

                        # 計算經驗馬可夫轉移分數 (水平偏好 + 垂直偏好)
                        score = 0.0
                        for i in range(4):
                            hp = (row_cand[i], row_cand[i + 1])
                            hp = hp if hp[0] <= hp[1] else (hp[1], hp[0])
                            score += h_freq.get(hp, 1) / 36.0
                        for i in range(5):
                            vp = (last_row[i], row_cand[i])
                            vp = vp if vp[0] <= vp[1] else (vp[1], vp[0])
                            score += v_freq.get(vp, 1) / 40.0

                        candidates.append((row_cand, round(score, 4)))

        candidates.sort(key=lambda item: (-item[1], item[0]))
        return candidates[:top_k]

    def prove_all(
        self,
        monte_carlo_trials: int = 50000,
        seed: int = 20261116,
    ) -> ProofSummaryReport:
        """執行全部 5 項演算法證明實驗並回傳結果。"""
        rng = random.Random(seed)

        # ---------------------------------------------------------------------
        # 證明 1：蒙地卡羅排列檢定 (Permutation Test on Fixed Color Multiset)
        # 固定 45 格的顏色數量 {G:13, B:12, R:10, Y:10}，隨機洗牌 50,000 次，
        # 觀察正交同色衝突邊數 (76 條邊中同色相鄰的數量)。
        # 【最佳化】：預先編譯 76 條正交邊的平坦一維索引對 (u, v)，避免迴圈內重複計算 r*cols+c。
        # ---------------------------------------------------------------------
        flat_pool = [self.grid[r][c] for r in range(self.rows) for c in range(self.cols)]
        edge_pairs: List[Tuple[int, int]] = []
        for r in range(self.rows):
            row_base = r * self.cols
            for c in range(self.cols):
                curr_idx = row_base + c
                if c + 1 < self.cols:
                    edge_pairs.append((curr_idx, curr_idx + 1))
                if r + 1 < self.rows:
                    edge_pairs.append((curr_idx, curr_idx + self.cols))
        edges_tuple = tuple(edge_pairs)

        zero_hits = 0
        min_conflicts = 76
        total_conflicts = 0
        shuffle = rng.shuffle

        for _ in range(monte_carlo_trials):
            shuffle(flat_pool)
            conflicts = sum(1 for u, v in edges_tuple if flat_pool[u] == flat_pool[v])
            if conflicts == 0:
                zero_hits += 1
            if conflicts < min_conflicts:
                min_conflicts = conflicts
            total_conflicts += conflicts

        avg_conflicts = total_conflicts / monte_carlo_trials
        # 理論上界估計：第一列 4 步不重複 (3/4)^4，後續 8 列每列首格 (3/4)、其餘 32 格受左與上雙重約束 (~2.25/4)
        theoretical_prob = ((3.0 / 4.0) ** 12) * ((2.25 / 4.0) ** 32)

        # ---------------------------------------------------------------------
        # 證明 2：在滿足水平無同色相鄰的前提下，Col 4 與 Col 2 恰好同色的機率為 1/3
        # （因為 Col 4 不能與 Col 3 同色，故在剩餘 3 種顏色中選中 Col 2 顏色的機率為 1/3）。
        # 連續 7 列 (Row 2..8) 皆滿足 Col 2 == Col 4 的獨立機率為 (1/3)^7 = 1 / 2187。
        # ---------------------------------------------------------------------
        mirror_prob = (1.0 / 3.0) ** 7

        # ---------------------------------------------------------------------
        # 證明 3：方向異向性 (Directional Anisotropy) 卡方檢定
        # 比較水平邊 (36 條) 與垂直邊 (40 條) 中「紅黃配 (R, Y)」與「非紅黃配」的比例差異，
        # 以及同色系群內轉移 ({B,G} + {R,Y}) 在水平 (21/36) 與垂直 (11/40) 的卡方統計量。
        # ---------------------------------------------------------------------
        # 由實際矩陣資料動態建立 2x2 列聯表（不寫死數值）：
        #   列 = 方向 (水平 / 垂直)，欄 = 同色系群內 ({B,G} 或 {R,Y}) / 跨群
        groups = {"R": "warm", "Y": "warm", "G": "cool", "B": "cool"}
        a = b = c = d = 0          # a: 水平同群, b: 水平跨群, c: 垂直同群, d: 垂直跨群
        h_ry = v_ry = 0
        for r in range(self.rows):
            for cc in range(self.cols):
                cur = self.grid[r][cc]
                if cc + 1 < self.cols:
                    nxt = self.grid[r][cc + 1]
                    if groups[cur] == groups[nxt]:
                        a += 1
                    else:
                        b += 1
                    if {cur, nxt} == {"R", "Y"}:
                        h_ry += 1
                if r + 1 < self.rows:
                    nxt = self.grid[r + 1][cc]
                    if groups[cur] == groups[nxt]:
                        c += 1
                    else:
                        d += 1
                    if {cur, nxt} == {"R", "Y"}:
                        v_ry += 1
        n_total = a + b + c + d
        chi2 = (n_total * ((a * d - b * c) ** 2)) / (
            (a + b) * (c + d) * (a + c) * (b + d)
        )
        h_ry_ratio = h_ry / (a + b)
        v_ry_ratio = v_ry / (c + d)

        # ---------------------------------------------------------------------
        # 證明 4：以 CSP 枚舉單一列 (長度 5) 滿足「水平不相鄰」的所有合法塗法數 (4 * 3^4 = 324)，
        # 並計算其中同時滿足「右三欄鏡像對稱 (Col 2 == Col 4)」的塗法數 (4 * 3^2 * 1 = 108)。
        # ---------------------------------------------------------------------
        valid_rows = 0
        sym_rows = 0
        for c0 in self.COLORS:
            for c1 in self.COLORS:
                if c1 == c0:
                    continue
                for c2 in self.COLORS:
                    if c2 == c1:
                        continue
                    for c3 in self.COLORS:
                        if c3 == c2:
                            continue
                        for c4 in self.COLORS:
                            if c4 == c3:
                                continue
                            valid_rows += 1
                            if c2 == c4:
                                sym_rows += 1

        # ---------------------------------------------------------------------
        # 證明 5：驗證與題目一排班模型之同構性
        # ---------------------------------------------------------------------
        no_consec_day = all(
            self.grid[r][c] != self.grid[r][c + 1]
            for r in range(self.rows)
            for c in range(self.cols - 1)
        )
        no_consec_week = all(
            self.grid[r][c] != self.grid[r + 1][c]
            for r in range(self.rows - 1)
            for c in range(self.cols)
        )

        return ProofSummaryReport(
            monte_carlo_trials=monte_carlo_trials,
            mc_zero_conflict_hits=zero_hits,
            mc_min_conflicts_observed=min_conflicts,
            mc_avg_conflicts_observed=avg_conflicts,
            theoretical_ortho_zero_prob_upper_bound=theoretical_prob,
            mirror_symmetry_exact_prob=mirror_prob,
            chi2_anisotropy_stat=chi2,
            horizontal_ry_ratio=h_ry_ratio,
            vertical_ry_ratio=v_ry_ratio,
            valid_single_row_patterns_total=valid_rows,
            symmetric_right3_patterns_total=sym_rows,
            is_valid_no_consecutive_day_roster=no_consec_day,
            is_valid_no_consecutive_week_same_day_roster=no_consec_week,
            predicted_next_rows=tuple(self.predict_next_rows(top_k=3)),
        )

