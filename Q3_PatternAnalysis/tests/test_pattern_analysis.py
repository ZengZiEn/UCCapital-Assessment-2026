"""
題目三完整單元測試套件 (test_pattern_analysis.py)
驗證項目：
1. PNG 底層解碼器準確還原 575x313 影像與 9x5 矩陣
2. 正交四色定理 (76 條邊 0 衝突) 驗證
3. 右側 7x3 鏡像對稱 (Row 2..8 Col2 == Col4) 與前兩列反對稱驗證
4. 全域與邊際配額上限 (<= 3) 與奇偶格 R/Y 5:5 完美對稱驗證
5. 方向異向性卡方檢定與蒙地卡羅顯著性證明驗證
"""

import os
import unittest
from src.png_decoder import ensure_image_extracted, decode_grid_from_png
from src.pattern_analyzer import GridPatternAnalyzer
from src.hypothesis_prover import HypothesisProver


class TestPatternAnalysis(unittest.TestCase):
    """題目三色彩矩陣規律探勘與演算法證明之單元測試。"""

    @classmethod
    def setUpClass(cls) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        png_path = os.path.join(base_dir, "assets", "slide4_image1.png")
        fallback_pptx = os.path.join(
            os.path.dirname(base_dir), "2026 Q4 面試前考題 V1.pptx"
        )
        ensure_image_extracted(png_path, fallback_pptx)
        cls.decoded = decode_grid_from_png(png_path)
        cls.report = GridPatternAnalyzer(cls.decoded.symbol_grid).analyze()
        cls.proof = HypothesisProver(cls.decoded.symbol_grid).prove_all(
            monte_carlo_trials=5000
        )

    def test_01_png_decoding_and_dimensions(self) -> None:
        """驗證 PNG 解碼尺寸 (575x313) 與 4 種標準 Excel 色票。"""
        self.assertEqual(self.decoded.width, 575)
        self.assertEqual(self.decoded.height, 313)
        self.assertEqual(self.decoded.rows, 9)
        self.assertEqual(self.decoded.cols, 5)
        self.assertEqual(self.decoded.palette_map["R"], "#FF0000")
        self.assertEqual(self.decoded.palette_map["Y"], "#FFC000")
        self.assertEqual(self.decoded.palette_map["G"], "#70AD47")
        self.assertEqual(self.decoded.palette_map["B"], "#0070C0")

    def test_02_zero_orthogonal_conflicts(self) -> None:
        """驗證全部 76 條正交相鄰邊 (36 水平 + 40 垂直) 同色衝突數嚴格為 0。"""
        self.assertEqual(self.report.total_horizontal_edges, 36)
        self.assertEqual(self.report.total_vertical_edges, 40)
        self.assertEqual(self.report.orthogonal_same_color_conflicts, 0)

    def test_03_quota_bounds_and_bipartite_parity(self) -> None:
        """驗證全域計數、單列單欄上限 (<=3) 以及奇偶格 R/Y 5:5 完美對稱。"""
        self.assertEqual(
            self.report.global_counts, {"G": 13, "B": 12, "R": 10, "Y": 10}
        )
        self.assertLessEqual(self.report.max_count_in_any_row, 3)
        self.assertLessEqual(self.report.max_count_in_any_col, 3)
        self.assertEqual(self.report.min_distinct_colors_in_col, 4)

        # 奇偶二分格中 R 與 Y 皆恰好各出現 5 次
        self.assertEqual(self.report.even_parity_counts["R"], 5)
        self.assertEqual(self.report.odd_parity_counts["R"], 5)
        self.assertEqual(self.report.even_parity_counts["Y"], 5)
        self.assertEqual(self.report.odd_parity_counts["Y"], 5)

    def test_04_right_3col_mirror_symmetry(self) -> None:
        """驗證第 2 列至第 8 列 (共 7 列) 右三欄皆滿足 Col 2 == Col 4 鏡像對稱。"""
        self.assertEqual(
            self.report.right_3col_symmetric_rows, (2, 3, 4, 5, 6, 7, 8)
        )

    def test_05_statistical_proofs_and_anisotropy(self) -> None:
        """驗證方向異向性卡方檢定與蒙地卡羅機率顯著性。"""
        self.assertEqual(self.proof.mc_zero_conflict_hits, 0)
        self.assertLess(self.proof.theoretical_ortho_zero_prob_upper_bound, 1e-9)
        self.assertGreater(self.proof.chi2_anisotropy_stat, 6.63)  # p < 0.01 閾值
        self.assertTrue(self.proof.is_valid_no_consecutive_day_roster)
        self.assertTrue(self.proof.is_valid_no_consecutive_week_same_day_roster)

    def test_06_rule_constrained_next_row_prediction(self) -> None:
        """驗證基於歸納規則與馬可夫轉移之下一列 (Row 9) 生成器完全滿足正交不衝突與鏡像對稱。"""
        self.assertEqual(len(self.proof.predicted_next_rows), 3)
        row8 = self.decoded.symbol_grid[8]
        for cand_row, score in self.proof.predicted_next_rows:
            self.assertGreater(score, 0.0)
            # 1. 水平無相鄰同色
            for c in range(4):
                self.assertNotEqual(cand_row[c], cand_row[c + 1])
            # 2. 與 Row 8 垂直無相鄰同色
            for c in range(5):
                self.assertNotEqual(cand_row[c], row8[c])
            # 3. 右三欄鏡像對稱 (Col 2 == Col 4)
            self.assertEqual(cand_row[2], cand_row[4])


if __name__ == "__main__":
    unittest.main(verbosity=2)

