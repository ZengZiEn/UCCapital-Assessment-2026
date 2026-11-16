"""
UC Capital 面試考題 — 題目三：色彩矩陣特徵、趨勢與規則之演算法分析歸納系統
套件初始化檔案
"""

from .png_decoder import DecodedGridImage, decode_grid_from_png
from .pattern_analyzer import GridPatternAnalyzer, PatternAnalysisReport
from .hypothesis_prover import HypothesisProver, ProofSummaryReport

__all__ = [
    "DecodedGridImage",
    "decode_grid_from_png",
    "GridPatternAnalyzer",
    "PatternAnalysisReport",
    "HypothesisProver",
    "ProofSummaryReport",
]

