# UC Capital（優式資本）面試前考題 — 軟體工程專案總覽 (`README.md`)

本倉庫為 **UC Capital 優式資本面試前考題** 之完整軟體工程實作專案。全專案嚴格遵循高頻／量化交易系統研發標準，採用 **「Python 3.12 領域建模（高可維護性）+ C11 (`MSVC x64 /O2`) 暫存器級原生極速引擎（極致執行效率）」雙軌制架構**。

---

## 一、核心交付報告（建議優先開啟）

1. **[UCCapital_面試考題_最終說明報告.pdf](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/UCCapital_面試考題_最終說明報告.pdf)**（A4 共 14 頁，內嵌 **17 張高解析向量圖表**，完整涵蓋三題演算法設計、複雜度對照表与即時實測數據）
2. **[UCCapital_實作思考與軟體工程流程報告.pdf](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/UCCapital_實作思考與軟體工程流程報告.pdf)**（A4 共 5 頁，內嵌 **6 張視覺化流程圖與演進軌跡圖**，完整梳理本專案從拆解題目、開源調研、實證測試到跨語言最佳化的思考脈絡與決策順序）

---

## 二、專案目錄結構（乾淨分層設計）

根目錄僅保留最核心的考題簡報、兩份最終 PDF 報告與三個題目子專案，所有整合性 Markdown 文件與 PDF 自動化建置工具統一收納於 `docs_and_tools/`：

```text
UCCapital/
├── 2026 Q4 面試前考題 V1.pptx                   # 原始考題簡報
├── UCCapital_面試考題_最終說明報告.pdf           # 【最終報告 1】三題演算法、架構圖與 17 張實測圖表總報告
├── UCCapital_實作思考與軟體工程流程報告.pdf       # 【最終報告 2】實作思考脈絡、決策順序與軟體工程流程報告
├── README.md                                   # 專案總覽與快速執行指南（本文件）
├── .gitignore                                  # 版本控制忽略規則
│
├── Q1_Scheduling/                              # 【題目一：員工排班與突發狀況動態應變系統 (Python + C11)】
│   ├── README.md
│   ├── docs/         (01_analysis.md, 02_architecture.md, 03_implementation_plan.md, 04_dev_log.md)
│   ├── src/          (__init__.py, models.py, solvers.py, contingency.py, main.py)
│   ├── src_native/   (fast_scheduler.c — C11 Bitboard/SWAR 21.8ns 暫存器級極速引擎)
│   ├── tests/        (test_scheduling.py — 7 大項單元測試，含 374 種請假窮舉與 n=50 擴展測試)
│   ├── scripts/      (run_all.bat)
│   ├── build/        (fast_scheduler.exe)
│   └── results/      (test_and_benchmark_report.md)
│
├── Q2_MemoryAllocator/                         # 【題目二：C 語言 malloc 優化與 myMalloc 實作 (C11, +10% 加分)】
│   ├── README.md
│   ├── docs/         (01_analysis.md, 02_architecture.md, 03_implementation_plan.md, 04_dev_log.md)
│   ├── include/      (my_malloc.h — 16-Byte 對齊、統計介面與 Magic 防護定義)
│   ├── src/          (my_malloc.c — Tier-1 O(1) Slab + Tier-2 顯式雙向自由串列 Arena, main_demo.c)
│   ├── tests/        (test_my_malloc.c — 5 項測試, benchmark_malloc.c — 214 萬次壓力基準測試)
│   ├── scripts/      (build_and_run.bat)
│   ├── build/        (main_demo.exe, test_my_malloc.exe, benchmark_malloc.exe)
│   └── results/      (test_and_benchmark_report.md)
│
├── Q3_PatternAnalysis/                         # 【題目三：色彩矩陣特徵、趨勢與規則分析歸納 (Python + C11)】
│   ├── README.md
│   ├── assets/       (slide4_image1.png — 原始 575x313 圖檔)
│   ├── docs/         (01_analysis.md, 02_architecture.md, 03_implementation_plan.md, 04_dev_log.md)
│   ├── src/          (png_decoder.py, pattern_analyzer.py, hypothesis_prover.py, main.py)
│   ├── src_native/   (fast_monte_carlo.c — C11 xorshift64* + Lemire 無除法百萬次洗牌引擎)
│   ├── tests/        (test_pattern_analysis.py — 6 項測試，含 Row 9 馬可夫規律預測驗證)
│   ├── scripts/      (run_all.bat)
│   ├── build/        (fast_monte_carlo.exe)
│   └── results/      (analysis_and_proof_report.md)
│
└── docs_and_tools/                             # 【整合技術文件、全域開發日誌與 PDF 自動化建置工具】
    ├── FINAL_REPORT.md                         # 三題完整技術總結報告 (Markdown 版)
    ├── WORKFLOW_AND_THOUGHT_PROCESS.md         # 實作思考脈絡與軟體工程流程說明 (Markdown 版)
    ├── PROJECT_ARCHITECTURE.md                 # 軟體工程流程規範與低延遲設計哲學
    ├── DEVELOPMENT_LOG.md                      # 全專案完整時間軸開發、除錯與最佳化總日誌
    ├── run_all_pipeline.bat                    # 全專案一鍵自動化驗證與雙 PDF 報告建置流水線
    └── pdf_generator/                          # 純 Python SVG 圖表與 PDF 渲染引擎
        ├── README.md
        ├── build_report.py                     # 產出 UCCapital_面試考題_最終說明報告.pdf
        ├── build_workflow_pdf.py               # 產出 UCCapital_實作思考與軟體工程流程報告.pdf
        └── build/                              # 建置輸出之 HTML 與即時實測 JSON 數據
```

---

## 三、一鍵重現與驗證指南

於專案根目錄 `UCCapital/` 執行：
```powershell
cmd.exe /c docs_and_tools\run_all_pipeline.bat
```
此指令會依序編譯並實跑題目一、題目二、題目三的所有 C11 原生引擎與 Python 測試套件、自動更新兩份 PDF 報告，並在結束時自動清理所有中繼 `.obj` 與 `__pycache__` 暫存檔，保持工作區乾淨整潔。
