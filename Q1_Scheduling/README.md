# 題目一：員工排班與突發狀況動態應變系統 (`Q1_Scheduling`)

本目錄為 UC Capital 面試考題 **題目一：排班問題** 之完整軟體工程實作專案。

## 目錄結構
```text
Q1_Scheduling/
├── README.md                          # 本說明文件
├── docs/
│   ├── 01_analysis.md                 # 需求分析、數學建模與文獻/開源方法參考
│   ├── 02_architecture.md             # 系統架構、資料結構與模組互動設計
│   ├── 03_implementation_plan.md      # 開發階段劃分與時間/空間複雜度評估
│   └── 04_dev_log.md                  # 開發與優化權衡日誌
├── src/
│   ├── __init__.py
│   ├── models.py                      # 領域資料模型（Bitmask 可用性編碼與合法性驗證器）
│   ├── solvers.py                     # 雙引擎排班求解器（平坦化預編譯 MRV 回溯法 / Dinic 最大流）
│   ├── contingency.py                 # 突發請假修復引擎（BFS 最小變動增廣鏈 + O(1) 預計算查找表）
│   └── main.py                        # 完整流程展示主程式
├── src_native/
│   └── fast_scheduler.c               # C11 Bitboard / SWAR 暫存器級奈秒極速引擎 (MSVC /O2)
├── tests/
│   └── test_scheduling.py             # 單元測試與 374 種突發情境窮舉驗證套件
├── scripts/
│   └── run_all.bat                    # 一鍵編譯 C11 引擎、執行 Python 主程式與單元測試腳本
├── build/
│   └── fast_scheduler.exe             # 編譯產出之 C11 極速排班基準測試執行檔
└── results/
    └── test_and_benchmark_report.md   # 跨語言實測輸出結果與效能報告
```

## 快速執行指令
在 `Q1_Scheduling` 目錄下執行：
```powershell
# 1. 執行主程式展示
python -m src.main

# 2. 執行完整單元測試套件
python -m unittest tests.test_scheduling -v
```

