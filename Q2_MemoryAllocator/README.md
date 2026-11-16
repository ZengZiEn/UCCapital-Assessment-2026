# 題目二：C 語言的 `malloc` 效能問題與 `myMalloc()` 實作 (`Q2_MemoryAllocator`)

本目錄為 UC Capital 面試考題 **題目二：C 語言的 `malloc` 效能問題與自訂 `myMalloc()` 設計與實測驗證（含額外 +10% 加分實作）** 之完整軟體工程專案。

## 目錄結構
```text
Q2_MemoryAllocator/
├── README.md                          # 本說明文件
├── docs/
│   ├── 01_analysis.md                 # malloc 慢速原因剖析與 Slab/tcmalloc 開源參考
│   ├── 02_architecture.md             # myMalloc 雙層混合式記憶體池架構與 BlockHeader 設計
│   ├── 03_implementation_plan.md      # 開發階段規劃與三大 Benchmark 驗證規格
│   └── 04_dev_log.md                  # 開發與編譯器最佳化調校日誌
├── include/
│   └── my_malloc.h                    # myMalloc 公開 API 與統計結構定義
├── src/
│   ├── my_malloc.c                    # 核心實作：O(1) Slab Pool + 雙向合併 Coalescing Arena
│   └── main_demo.c                    # 題目 10,000 * sizeof(int) 替換示範主程式
├── tests/
│   ├── test_my_malloc.c               # 5 大項嚴格單元測試套件
│   └── benchmark_malloc.c             # 百萬次高精度效能基準測試套件
├── scripts/
│   └── build_and_run.bat              # 一鍵編譯與執行腳本 (MSVC x64 /O2)
└── results/
    └── test_and_benchmark_report.md   # 實測輸出與 26.89 倍加速數據報告
```

## 快速編譯與執行指令
在 `Q2_MemoryAllocator` 目錄下執行：
```powershell
cmd.exe /c scripts\build_and_run.bat
```

