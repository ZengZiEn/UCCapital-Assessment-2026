# UC Capital（優式資本）面試前考題 — 軟體工程與 Human-AI Agent 協同研發專案總覽 (`README.md`)

本倉庫為 **UC Capital 優式資本面試前考題** 之完整軟體工程實作專案。全專案嚴格遵循高頻／量化交易系統研發標準，採用 **「Python 3.12 領域建模（高可維護性）+ C11 (`MSVC x64 /O2`) 暫存器級原生極速引擎（奈秒級執行效率）」雙軌制架構**，並公開透明地展示 **Human-in-the-Loop AI Agent 協同工程模式** 與 **「The Chain of Truth（Strategy $\to$ Task $\to$ Worklog）」三層級管理框架** 之完整實踐。

---

## 一、核心交付報告（建議優先開啟）

1. **[UCCapital_面試考題_最終說明報告.pdf](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/UCCapital_面試考題_最終說明報告.pdf)**（A4 共 14 頁，內嵌 **17 張高解析向量圖表**，完整涵蓋三題演算法設計、複雜度對照表、開源技術引進與即時實測數據）
2. **[UCCapital_實作思考與軟體工程流程報告.pdf](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/UCCapital_實作思考與軟體工程流程報告.pdf)**（A4 共 5 頁，內嵌 **11 張視覺化流程圖與演進軌跡圖**，完整梳理本專案在 **Human-AI Agent 協同研發** 與 **The Chain of Truth 三層級治理** 下，從拆解題目、開源調研、實證測試、語言效率質疑到跨語言最佳化的真實對話脈絡與決策順序）

---

## 二、The Chain of Truth 三層級管理框架與 Human-AI Agent 協同治理

呼應優式資本探索 **「如何應用 AI 的分析能力去輔助目前交易系統與工程化」** 之核心方向，本專案透過 [`AGENTS.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/AGENTS.md) 強制實施 **「The Chain of Truth（真實之鏈）」三層級管理框架**，將人類工程師（曾子恩）的架構治理與 AI Agent 的協同分析實作建立嚴格的雙向追溯：

1. **第一層：Strategy 層 ([`/strategy/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/))** — 定義專案主體目標与頂層架構：
   * [`strategy/product_vision.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/product_vision.md)：專案主體願景與四大任務量化驗收指標（OKRs）。
   * [`strategy/app_architecture.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/app_architecture.md)：Python 3.12 + C11 (`/O2`) 雙軌技術架構與三層級關聯圖。
   * [`strategy/roadmap.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/roadmap.md)：五階段發展路線圖與「計畫外新功能（如 C11 原生引擎、$n=50$ 擴展測試、`Row 9` 馬可夫預測器）」向上同步紀錄。
2. **第二層：Task 層 ([`/tasks/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/))** — 向下追溯自 Strategy，以「追加（Append）」方式動態記錄實作演進與技術決策 (`implementation-process.md`)：
   * [`tasks/TASK-01-Scheduling-System/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-01-Scheduling-System/)：題目一排班與突發狀況動態應變系統（[`task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-01-Scheduling-System/task.md) / [`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-01-Scheduling-System/implementation-process.md)）。
   * [`tasks/TASK-02-Memory-Allocator/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-02-Memory-Allocator/)：題目二 C 語言 `malloc` 效能問題與自訂 `myMalloc` 配置器（[`task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-02-Memory-Allocator/task.md) / [`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-02-Memory-Allocator/implementation-process.md)）。
   * [`tasks/TASK-03-Pattern-Analysis/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-03-Pattern-Analysis/)：題目三色彩矩陣特徵、趨勢與規則分析歸納（[`task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-03-Pattern-Analysis/task.md) / [`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-03-Pattern-Analysis/implementation-process.md)）。
   * [`tasks/TASK-04-Visual-PDF-And-Governance/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-04-Visual-PDF-And-Governance/)：視覺化向量圖表雙 PDF 報告、實證流水線與三層級治理（[`task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-04-Visual-PDF-And-Governance/task.md) / [`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-04-Visual-PDF-And-Governance/implementation-process.md)）。
3. **第三層：Worklog 層 ([`/worklogs/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/))** — 緊扣 Task ID，詳實記錄實機 CLI 指令 (`## Execution`)、報錯與邏輯阻礙 (`## Obstacles`) 及修復方案 (`## Resolution`)，並向上同步至 Task 層：
   * [`worklogs/2026-11-16-TASK-01.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-01.md)
   * [`worklogs/2026-11-16-TASK-02.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-02.md)
   * [`worklogs/2026-11-16-TASK-03.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-03.md)
   * [`worklogs/2026-11-16-TASK-04.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-04.md)

---

## 三、專案目錄結構（乾淨分層設計）

```text
UCCapital/
├── 2026 Q4 面試前考題 V1.pptx                   # 原始考題簡報
├── UCCapital_面試考題_最終說明報告.pdf           # 【最終報告 1】三題演算法、架構圖與 17 張實測圖表總報告 (14頁)
├── UCCapital_實作思考與軟體工程流程報告.pdf       # 【最終報告 2】Human-AI 協作、The Chain of Truth 與流程報告 (5頁)
├── AGENTS.md                                   # Antigravity 專案開發規則 (The Chain of Truth 三層級強制規範)
├── README.md                                   # 專案總覽與快速執行指南（本文件）
├── .gitignore                                  # 版本控制忽略規則
│
├── strategy/                                   # 【The Chain of Truth 第 1 層：Strategy 策略層】
│   ├── product_vision.md                       # 專案主體目標與量化驗收指標
│   ├── app_architecture.md                     # C11/Python 雙軌技術架構與三層級關聯圖
│   └── roadmap.md                              # 研發階段路線圖與計畫外功能向上同步紀錄
│
├── tasks/                                      # 【The Chain of Truth 第 2 層：Task 任務與實作演進層】
│   ├── TASK-01-Scheduling-System/              # (task.md, implementation-process.md)
│   ├── TASK-02-Memory-Allocator/               # (task.md, implementation-process.md)
│   ├── TASK-03-Pattern-Analysis/               # (task.md, implementation-process.md)
│   └── TASK-04-Visual-PDF-And-Governance/      # (task.md, implementation-process.md)
│
├── worklogs/                                   # 【The Chain of Truth 第 3 層：Worklog 實機執行與除錯日誌層】
│   ├── 2026-11-16-TASK-01.md                   # 含 ## Execution / ## Obstacles / ## Resolution
│   ├── 2026-11-16-TASK-02.md                   # 含 ## Execution / ## Obstacles / ## Resolution
│   ├── 2026-11-16-TASK-03.md                   # 含 ## Execution / ## Obstacles / ## Resolution
│   └── 2026-11-16-TASK-04.md                   # 含 ## Execution / ## Obstacles / ## Resolution
│
├── Q1_Scheduling/                              # 【題目一實作區：docs(01~04), src, src_native(C11), tests(7項), results】
├── Q2_MemoryAllocator/                         # 【題目二實作區：docs(01~04), include, src(C11), tests(5項+基準), results】
├── Q3_PatternAnalysis/                         # 【題目三實作區：docs(01~04), assets, src, src_native(C11), tests(6項), results】
└── docs_and_tools/                             # 【整合文件與自動化 PDF 建置流水線工具區】
    ├── FINAL_REPORT.md                         # 三題完整技術總結報告 (Markdown 版)
    ├── WORKFLOW_AND_THOUGHT_PROCESS.md         # Human-AI 協作、思考脈絡與軟體工程流程說明 (Markdown 版)
    ├── PROJECT_ARCHITECTURE.md                 # 軟體工程流程規範、Agent 治理與低延遲設計哲學
    ├── DEVELOPMENT_LOG.md                      # 全專案完整時間軸人機協作開發、除錯與最佳化總日誌
    ├── run_all_pipeline.bat                    # 全專案一鍵自動化驗證與雙 PDF 報告建置流水線
    └── pdf_generator/                          # 純 Python SVG 圖表與 PDF 渲染引擎 (build_report.py, build_workflow_pdf.py)
```

---

## 四、一鍵重現與驗證指南

於專案根目錄 `UCCapital/` 執行：
```powershell
cmd.exe /c docs_and_tools\run_all_pipeline.bat
```
此指令會依序編譯並實跑題目一、題目二、題目三的所有 C11 原生引擎與 Python 測試套件、自動更新兩份 PDF 報告，並在結束時自動清理所有中繼 `.obj` 與 `__pycache__` 暫存檔，保持工作區乾淨整潔。
