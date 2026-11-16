# 題目二：`myMalloc()` 人機協作（Human-AI Agent）開發、除錯與極致最佳化完整日誌 (`04_dev_log.md`)

本文件完整記錄「題目二：C 語言的 `malloc` 效能問題與自訂 `myMalloc()` 實作」在 **Human-in-the-Loop AI Agent 協同研發模式** 下，由 **曾子恩（人類工程師：負責軟體工程規範制定、強制實機執行驗證、開源效能極限質疑與品質把關）** 與 **AI Agent（負責本機 MSVC 工具鏈探測、GitHub `dlmalloc`/`tlsf` 架構檢索、C11 記憶體池編碼、VirtualFree 分頁邊界診斷與百萬次基準測試執行）** 共同推進的每一個步驟與修改動作。

---

## 完整時間軸與人機協作修改紀錄 (Chronological Human-AI Collaboration Log)

### [2026-11-16 09:15] 步驟 1：考題程式碼與效能痛點分析
* **執行動作**：解析 `2026 Q4 面試前考題 V1.pptx` 第 3 頁，目標為針對反覆呼叫 `malloc(10000 * sizeof(int))`（`40,000 Bytes`）與 `free()` 的效能低落問題提出改善方案、設計 `myMalloc()` 並實際撰寫 C 程式驗證（+10% 加分）。
* **問題觀察**：`40,000 Bytes` 超過一般小物件快取（如 Windows LFH 16KB 閾值），在標準配置器中反覆分配與釋放會觸發核心態切換、虛擬分頁清零（Zero-fill）、鎖競爭與 Cache Miss。

### [2026-11-16 09:30] 步驟 2：系統 C/C++ 編譯環境探測
* **執行動作**：掃描本機編譯工具鏈，確認安裝有 **Microsoft Visual Studio 2022 BuildTools (`MSVC 14.44.35207`)** 與 **Windows 10 SDK (`10.0.26100.0`)**。
* **工程決策**：採用標準 C11 撰寫，並以 `cl.exe /O2 /W4 /utf-8` 進行最高等級速度最佳化與第 4 級零警告嚴格編譯。

### [2026-11-16 09:42] 步驟 3：建立初版雙層混合式配置器、單元測試與百萬次 Benchmark
* **新增檔案**：
  * `include/my_malloc.h`：定義公開 API (`myMalloc`, `myFree`, `myCalloc`, `myRealloc`, `myMallocInit`, `myMallocDestroy`) 與內部統計結構 `MyAllocatorStats`。
  * `src/my_malloc.c`：實作 Tier-1 O(1) LIFO Slab Pool（Slot 容量 `40,960 Bytes`，預設 128 個 Slots）與 Tier-2 Boundary-Tag Coalescing Arena（預設 `8 MB`）。
  * `src/main_demo.c`：示範替換題目之 `10,000 * sizeof(int)` 配置與釋放。
  * `tests/test_my_malloc.c`：5 大項單元測試。
  * `tests/benchmark_malloc.c`：使用 Windows 高精度計時器 `QueryPerformanceCounter` 測試三大場景（共 2,140,000 次分配與釋放），並加入 `volatile long long g_sink_checksum` 防止 `/O2` 編譯器消除死程式碼。
  * `scripts/build_and_run.bat`：自動化編譯與測試腳本。

### [2026-11-16 09:45] 步驟 4：修正批次腳本編碼與沙箱環境變數問題
* **發現問題**：
  1. 在 Windows `cmd.exe` 中，於含中文字符的 `.bat` 檔內中途切換 `chcp 65001` 會導致 `cmd.exe` 位元組偏移解析錯誤。
  2. 沙箱環境下直接呼叫 `vcvars64.bat` 會因查詢註冊表受限而失敗。
* **修改動作**：
  * 修改 `scripts/build_and_run.bat`：直接顯式設定 `MSVC_DIR`、`SDK_INC`、`SDK_LIB` 至 `PATH`、`INCLUDE`、`LIB` 環境變數，並將 `.bat` 的 `echo` 訊息改為純 ASCII（C 執行檔本身則透過 `SetConsoleOutputCP(65001)` 完美輸出 UTF-8 繁體中文）。

### [2026-11-16 09:48] 步驟 5：偵測並修復超大區塊 OS Fallback 之 Double-Free 頁面卸載邊界問題
* **發現問題**：
  * 在 `tests/test_my_malloc.c` 的 `test_05_os_fallback_and_double_free_guard()` 中，原本對一個 `4 MB` 的 Tier-3 OS Fallback 區塊呼叫 `myFree(huge)` 後，又再次呼叫 `myFree(huge)` 測試 Double-Free 攔截。
  * 由於 `4 MB` 區塊走系統 `free(hdr)` 時，Windows CRT 會立即呼叫 `VirtualFree` 將該 `4 MB` 虛擬分頁從行程位址空間卸載（Unmap），因此第二次讀取 `hdr->magic` 時會觸發作業系統層級的 `Access Violation`！
* **修改動作**：
  * 修改 `tests/test_my_malloc.c`：將 `4 MB` 超大區塊正常釋放驗證與池內區塊（Tier-1 Slab / Tier-2 Arena，虛擬位址常駐於池中）之 Double-Free 攔截測試分離。
* **驗證結果**：全部 5 大項單元測試 100% 通過（`PASS`）！

### [2026-11-16 10:26] 步驟 6：參考 GitHub `mattconte/tlsf` 與 `dlmalloc` 升級 Tier-2 為顯式雙向自由串列
* **問題檢視與文獻調研**：
  * 檢視初版 `src/my_malloc.c` 的 Tier-2 Arena 搜尋邏輯：初版使用隱式串列（由 `arena_first_block` 開始沿著 `next` 逐一檢查所有區塊）。若前方有大量「已分配」區塊，尋找後方空閒區塊會退化為 $O(N)$ 線性掃描！
  * 調研 GitHub 著名即時系統配置器 `mattconte/tlsf`（Two-Level Segregated Fit）與 Doug Lea 的 `dlmalloc`，標準的高效做法是將「實體相鄰邊界指標 (`phys_prev` / `phys_next`)」與「顯式自由串列指標 (`free_prev` / `free_next`)」分離！
* **具體修改動作**：
  1. 在 `src/my_malloc.c` 中新增侵入式結構 `ArenaFreeNode { MyBlockHeader *free_prev; MyBlockHeader *free_next; }`，直接映射於空閒區塊未使用的 Payload 前 16 Bytes（零額外標頭空間開銷）。
  2. 新增 `arena_freelist_insert()` 與 `arena_freelist_remove()` 內聯函式（`__inline`），維護全域 `arena_free_head` 指標。
  3. 修改 `myMalloc()` 的 Tier-2 路徑：直接從 `g_ctx.arena_free_head` 取出空閒區塊，**完全跳過所有已分配區塊（達到 $O(1)$ 取塊）**！
  4. 修改 `arena_coalesce_and_insert()`：釋放區塊時透過 `phys_prev` 與 `phys_next` 在 $O(1)$ 時間內完成前後相鄰空閒區塊合併，並同步更新顯式自由串列。
* **重新編譯與實測結果**：
  * 執行 `scripts/build_and_run.bat`，`main_demo.exe` 與 `test_my_malloc.exe` 全數通過。
  * `benchmark_malloc.exe` 實測加速倍率：單一 40KB 百萬次達 **23.1× ~ 26.8×**，批次 64×40KB 高峰負載達 **33.5× ~ 51.2×**！

### [2026-11-16 11:42] 步驟 7：全專案回歸測試流水線驗證與暫存檔清理
* **執行動作**：透過 `docs_and_tools/run_all_pipeline.bat` 重新編譯並執行 `main_demo.exe`、`test_my_malloc.exe`（5 項單元測試全數通過）與 `benchmark_malloc.exe`（214 萬次分配釋放壓力測試），實測數據自動匯入兩份最終 PDF 報告，並清除 `build/*.obj` 中繼檔以保持目錄整潔。

### [2026-11-16 14:05] 步驟 8：補入 Human-AI Agent 協同分析與工程治理紀錄
* **人類工程師指令**：明確指示專案文件應誠實、透明地呈現使用 AI Agent 協同進行 GitHub 開源調研、邊界除錯與極致最佳化的真實對話歷程。
* **修改動作**：同步更新本開發日誌、全域總日誌與雙份 PDF 報告，完整對照記錄人機互動之決策脈絡。
