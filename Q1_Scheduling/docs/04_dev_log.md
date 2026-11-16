# 題目一：排班問題 — 人機協作（Human-AI Agent）開發、測試與極致最佳化完整日誌 (`04_dev_log.md`)

本文件完整記錄「題目一：員工排班與突發狀況動態應變系統」在 **Human-in-the-Loop AI Agent 協同研發模式** 下，由 **曾子恩（人類工程師：負責需求定義、軟體工程結構規劃、語言效率質疑與實證把關）** 與 **AI Agent（負責 PPTX 逆向解析、GitHub 開源文獻調研、Python/C11 雙軌編碼與自動化測試執行）** 共同推進的每一個步驟與修改動作。

---

## 完整時間軸與人機協作修改紀錄 (Chronological Human-AI Collaboration Log)

### [2026-11-16 09:15] 步驟 1：原始考題 PPTX 解構與需求提取（Human 指令 → Agent 逆向解析）
* **人類工程師指令**：要求檢查 `2026 Q4 面試前考題 V1.pptx` 並提供完整分析。
* **AI Agent 執行動作**：使用 Python `zipfile` 與 `xml.etree.ElementTree` 直接解析 `2026 Q4 面試前考題 V1.pptx` 內的 `ppt/slides/slide2.xml`。
* **提取規格**：
  * 員工 `A (Mon, Tue, Wed)`、`B (Mon, Thu, Fri)`、`C (Tue, Wed, Thu)`、`D (Tue, Fri)`。
  * 三大核心需求：(1) `Mon ~ Fri` 每天必有 1 人上班；(2) 每人每週最多上 2 天且限於有空的日子；(3) 排好班表後，某員工可能臨時說「這週某一天不能上了」，演算法需能動態應變。

### [2026-11-16 09:29] 步驟 2：國內外文獻與 GitHub 開源解法調研
* **執行動作**：檢索作業研究（Operations Research）與 GitHub 上針對 Nurse Scheduling Problem (NSP) / Employee Rostering 的開源專案（如 `google/or-tools` Network Flow 與 ALNS `Construct-Perturb-Repair` 架構）。
* **設計決策**：
  * 單純給出一個回溯解不足以體現量化交易機構對「執行效率」與「系統擴展性」的要求。
  * 決定採用**雙引擎求解器**：小規模與全解枚舉使用 **位元遮罩 + MRV（Minimum Remaining Values）啟發式回溯法**；大規模多項式時間保證使用 **Dinic 網路最大流演算法 $O(E\sqrt{V})$**。
  * 針對突發請假，決定採用 **殘餘二部圖 BFS 最短交替增廣鏈（Shortest Alternating Path）** 以保證最小化班表變動天數（Minimum Hamming Distance），並搭配 **$O(1)$ 預計算應變查找表 (`ContingencyTable`)**。

### [2026-11-16 09:33] 步驟 3：建立初版領域模型、雙求解器與突發應變引擎
* **新增檔案**：
  * `src/__init__.py`
  * `src/models.py`：實作 `Day(IntEnum)`、`Employee`（初始化時自動編譯 5-bit `availability_mask`）、`ScheduleConfig` 與 `Schedule.validate()`。
  * `src/solvers.py`：實作 `BitmaskMRVSolver` 與 `MaxFlowDinicSolver`。
  * `src/contingency.py`：實作 `IncrementalRepairEngine`、`RobustScheduleSelector` 與 `ContingencyTable`。
  * `src/main.py` 與 `tests/test_scheduling.py`。

### [2026-11-16 09:37] 步驟 4：首次實機執行與測試修正（修正全解空間數量與測試套件匯入）
* **執行動作**：於 `Q1_Scheduling` 目錄執行 `python -m src.main` 與 `unittest`。
* **發現問題與修正動作**：
  1. **問題 A（`unittest discover` 匯入錯誤）**：因為上層路徑含有空白（`my datas`），且 `tests/` 目錄缺少 `__init__.py`，導致 `unittest discover` 報 `Start directory is not importable`。
     * **修改動作**：新增 `tests/__init__.py`，並改以 `python -m unittest tests.test_scheduling -v` 執行。
  2. **問題 B（全解空間精確枚舉數量校正）**：初版手算預估為 18 組解，經由 `BitmaskMRVSolver.solve_all()` 嚴格枚舉並逐一通過 `Schedule.validate()` 驗證後，確認在題目範例條件下共有 **34 組完全合法的初始班表**，對應 $34 \times 11 = 374$ 種單日請假突發情境。
     * **修改動作**：同步更新 `tests/test_scheduling.py`、`docs/01_analysis.md`、`docs/03_implementation_plan.md` 中的枚舉總數為 **34 組班表 / 374 種突發測試案例**。
* **驗證結果**：6 大項自動化單元測試全數通過（`Ran 6 tests in 0.008s - OK`），且發現最佳基準班表 `Mon:A | Tue:C | Wed:A | Thu:B | Fri:D` 在遭遇任何一天的值班人員請假時，**5/5 (100%) 皆可透過 1-Hop 直接找空檔同仁代班解決（平均變動 1.00 天）**。

### [2026-11-16 10:16] 步驟 5：軟體工程目錄標準化（新增自動化執行腳本）
* **修改動作**：新增 `scripts/run_all.bat`，統一封裝主程式展示與單元測試執行流程，並更新 `README.md`。

### [2026-11-16 10:24] 步驟 6：語言選擇檢討與雙引擎極致最佳化（Python 平坦化 + C11 Bitboard/SWAR 原生引擎）
* **問題思考與國內外調研**：
  * 檢視程式語言選擇對執行效率的影響：Python 初版 `BitmaskMRVSolver.solve_one()` 耗時約 `27.50 us`，主要瓶頸在於遞迴函式內部每次呼叫 `sorted()` 並動態建立 `dict`。
  * 此外，參考 GitHub 上西洋棋引擎 `Stockfish` 的 **Bitboard** 技術與 `yb303/swar` 的 **SWAR（SIMD Within A Register）** 技術，若改以 C11 實作並將 4 位員工的工時上限計數打包進單一 32-bit 暫存器（每員工佔 4 bits），可完全消除陣列複製與堆積配置。
* **具體修改動作**：
  1. **最佳化 `src/solvers.py`（Python 引擎）**：
     * 將 `ordered_days` 與 `ordered_candidates` 在 `__init__` 階段預先編譯為不可變之定長 `Tuple[Tuple[int, ...], ...]`。
     * 移除遞迴熱路徑 `backtrack()` 內部的 `sorted()` 與 `dict` 操作，改用定長整數陣列 `chosen_emp_indices`，僅在抵達葉節點時建構 `Schedule` 物件。
     * **實測效果**：Python 單解平均耗時由 `27.50 us` 降至 **`11.90 ~ 13.50 us`（提速逾 50%）**！
  2. **新增 `src_native/fast_scheduler.c`（C11 暫存器級原生引擎）**：
     * 使用 `uint32_t` 位元遮罩表示每日候選員工，並以單一 `uint32_t` 暫存器每 4 bits 記錄一位員工的排班數（`c + (1U << (emp * 4))`），搭配完全展開之 5 層迴圈與 MSVC `/O2` 最佳化編譯為 `build/fast_scheduler.exe`。
     * **實測效果（重複 200,000 次取平均）**：
       * 單解搜尋 (`solve_one`)：**`20.62 ~ 26.79 ns`（約 `0.021 us`，比 Python 快逾 `440 ~ 655 倍`）**！
       * 全 34 解枚舉 (`solve_all`)：**`155.30 ~ 159.01 ns`（約 `0.155 us`，比 Python 快逾 `380 倍`）**！
       * 突發請假修復 (`repair`)：**`107.43 ns`（`0.107 us`）**！
  3. **更新 `scripts/run_all.bat` 與 `results/test_and_benchmark_report.md`**：整合 C11 原生引擎編譯、執行與 Python 測試，將跨語言實測數據完整寫入報告與最終 PDF。

### [2026-11-16 11:24] 步驟 7：新增一般化 $n$ 位員工大規模擴展性單元測試 (`test_07`)
* **修改動作**：對照考題投影片第 2 頁「某公司有 $n$ 位員工」，於 `tests/test_scheduling.py` 新增 `test_07_general_n_employees_scalability()`，模擬 $n = 50$ 位員工進行排班與突發請假修復測試，驗證 `BitmaskMRVSolver`、`MaxFlowDinicSolver` 與 `IncrementalRepairEngine` 在大型 $n$ 下 100% 正確且維持 1-Hop 最小變動修復（7 項單元測試全數通過）。

### [2026-11-16 11:42] 步驟 8：全專案回歸測試流水線驗證與暫存檔清理
* **執行動作**：透過 `docs_and_tools/run_all_pipeline.bat` 重新執行 C11 `fast_scheduler.exe`、Python `src.main` 與 7 項單元測試，數據同步寫入兩份最終 PDF 報告，並清除所有 `.obj` 與 `__pycache__` 暫存檔。

### [2026-11-16 14:05] 步驟 9：補入 Human-AI Agent 協同分析與工程治理紀錄
* **人類工程師指令**：明確指示專案文件應誠實、透明地呈現使用 AI Agent 協同分析、調研與實作的真實對話歷程，展現「人類主導架構與品質把關 + AI 賦能極速研發」之工程實踐。
* **修改動作**：同步更新本開發日誌、全域總日誌與雙份 PDF 報告，完整對照記錄人機互動之決策脈絡。
