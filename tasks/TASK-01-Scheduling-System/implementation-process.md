# `TASK-01` 實作過程與技術決策報告 (`implementation-process.md`)

> **所屬任務**：[`/tasks/TASK-01-Scheduling-System/task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-01-Scheduling-System/task.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-01.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-01.md)  
> **更新規範**：嚴格遵守 `AGENTS.md`，僅以「追加（Append）」方式動態記錄實作演進路徑與技術決策。

---

## Implementation Process

### [2026-11-16 09:30] 初始架構決策：為什麼採用「MRV 位元回溯 + Dinic 最大流」雙求解器與殘餘圖 BFS 修復？
* **技術背景與問題分析**：
  在題目給定的範例中，4 位員工每人每週最多上 2 天（總供給上限 8 人日），需覆蓋週一至週五共 5 天（總需求 5 人日）。雖然表面上有 3 人日的緩衝餘裕，但 `Mon, Wed, Thu, Fri` 各僅有 2 位員工可用，屬於高度受限的二部圖多重匹配問題（Bipartite b-Matching）。
* **人類工程師與 AI Agent 協同技術決策**：
  1. **小規模枚舉與極速搜尋採用 `BitmaskMRVSolver`**：將每位員工的可用工作日預編譯為 5-bit 無號整數遮罩（例如 `A = 0b00111`），使可用性檢查僅需單一 CPU 週期的位元運算 `(mask >> day) & 1`。搭配人工智慧約束滿足問題（CSP）中的 **最小剩餘價值啟發式（MRV, Minimum Remaining Values）**，優先決定可選人數最少的日子，實測僅展開 **5 個節點** 即零回溯直達可行解。
  2. **大規模擴展性採用 `MaxFlowDinicSolver`**：建構有向容量網路 $S \xrightarrow{\text{cap}=2} \text{Emp}_i \xrightarrow{\text{cap}=1} \text{Day}_j \xrightarrow{\text{cap}=1} T$，利用 Dinic 分層網路與當前弧優化，提供 $O(E\sqrt{V})$ 的多項式時間複雜度保證。
  3. **突發請假應變採用「最小擾動原則（Minimal Perturbation via Residual BFS）」**：若某員工臨時請假時直接重跑全域排班，可能產出一份與原班表截然不同的新班表，導致沒請假的同事行程全數被打亂。因此我們在殘餘二部圖上以廣度優先搜尋（BFS）尋找從「空缺日」到「尚有配額餘裕之員工」的最短交替路徑（Shortest Alternating Path），在數學上嚴格保證修復後的班表與原班表之漢明距離（變動天數）最小，並搭配預計算雜湊表 `ContingencyTable` 達成線上 $O(1)$ 零延遲查表。

### [2026-11-16 09:38] 追加紀錄（源於 Worklog 實機測試回饋）：全解空間枚舉數量校正為 34 組
* **實作演進與修正**：
  初版文件手算預估合法班表為 18 組。在遵照人類工程師「先實機執行測試」之規定執行 `BitmaskMRVSolver.solve_all()` 並逐一通過 `Schedule.validate()` 嚴格檢驗後，實證確認合法初始班表共計 **34 組**，對應 $34 \times 11 = 374$ 種單日臨時請假突發情境。已同步更新測試斷言與全解韌性排行榜，確認全部 374 種情境 100% 可修復。

### [2026-11-16 10:24] 追加紀錄（源於人類工程師對語言效率之關鍵質疑）：升級雙軌制並引進 C11 Bitboard/SWAR 暫存器級引擎
* **技術決策演進**：
  人類工程師（曾子恩）於審查初版成果時主動提出質疑：「*做之前的語言選擇是否會影響到執行效率？確定效率已經是最好了嗎？*」經檢視發現：
  1. Python 初版 `BitmaskMRVSolver` 在遞迴函式內部動態呼叫 `sorted()` 並建立 `dict`，耗時約 `27.50 us`。我們先將候選順序與清單在 `__init__` 預編譯為平坦不可變 Tuple，使 Python 單解耗時降至 **`9.93 ~ 14.91 us`**。
  2. 為徹底突破直譯器限制並展現高頻交易（HFT）核心路徑之極限速度，我們參考 GitHub 上西洋棋引擎 `Stockfish` 的 **Bitboard** 與 `yb303/swar` 的 **SWAR（SIMD Within A Register）** 技術，新增標準 C11 原生引擎 `Q1_Scheduling/src_native/fast_scheduler.c`：
     * 將 4 位員工的已排班天數打包進單一 32-bit 暫存器 `uint32_t counts`（每位員工佔 4 bits），增加工時僅需單週期加法 `c + (1U << (emp * 4))`，檢查是否未滿 2 天僅需 `((c >> (emp * 4)) & 0xFU) < 2U`。
     * 以 `MSVC x64 /O2` 編譯實測，單解搜尋壓縮至 **`16.98 ~ 20.22 ns`（比 Python 快逾 585 ~ 800 倍）**，全 34 解枚舉僅需 **`95.10 ~ 122.54 ns`**！

### [2026-11-16 11:24] 追加紀錄（源於考題簡報逐字核對）：新增 $n=50$ 位員工大規模擴展性驗證
* **實作演進**：
  對照考題簡報第 2 頁「某公司有 $n$ 位員工」，於 `tests/test_scheduling.py` 追加第 7 項單元測試 `test_07_general_n_employees_scalability()`，建構 $n=50$ 位員工之排班與突發請假情境，實證驗證雙求解器與 BFS 局部修復引擎在大型 $n$ 下 100% 正確且維持 1-Hop 最小變動修復。
