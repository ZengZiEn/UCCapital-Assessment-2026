# `TASK-02` 實作過程與技術決策報告 (`implementation-process.md`)

> **所屬任務**：[`/tasks/TASK-02-Memory-Allocator/task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-02-Memory-Allocator/task.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-02.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-02.md)  
> **更新規範**：嚴格遵守 `AGENTS.md`，僅以「追加（Append）」方式動態記錄實作演進路徑與技術決策。

---

## Implementation Process

### [2026-11-16 09:40] 初始架構決策：針對 `10,000 * sizeof(int)` (40 KB) 之三層混合式記憶體池設計
* **問題本質剖析**：
  題目給定之 `10,000 * sizeof(int) = 40,000 Bytes`（約 `39.06 KB`）超過了一般系統配置器的小物件快速路徑閾值（例如 Windows CRT Low Fragmentation Heap 上限為 `16 KB`）。當程式在熱迴圈中反覆呼叫 `malloc(40000)` 與 `free()` 時，標準配置器容易觸發作業系統虛擬記憶體分頁系統呼叫（`VirtualAlloc`/`VirtualFree` 或 `mmap`）、核心態切換、TLB 刷新與強制分頁清零（Zero-fill），同時造成嚴重的 L1/L2 快取失誤（Cache Miss）。
* **技術決策**：
  我們決定以標準 C11 (`MSVC 14.44 /O2`) 設計三層混合式配置器：
  1. **Tier-1：Fast-Path $O(1)$ 侵入式 LIFO Slab Pool（處理 $8\text{ KB} \sim 40\text{ KB}$）**：預先向作業系統申請一塊連續記憶體池（預設 128 個 Slots，每 Slot 含 32-Byte Header 與 `40,960 Bytes` Payload）。空閒 Slot 直接利用未使用的 Payload 前 8 Bytes 存放 `next` 指標構成 **LIFO（後進先出）單向侵入式串列**。分配與釋放皆只需 2 條指標指令（嚴格 $O(1)$），且剛釋放的 40KB 區塊仍溫熱地駐留於 CPU L1/L2 Cache 中即被下一次 `myMalloc` 重用。
  2. **Tier-2：Boundary-Tag Coalescing Arena（處理一般變長配置）**：預配置 `8 MB` 連續區塊，支援動態分割（Splitting）與前後相鄰空閒塊雙向立即合併（Coalescing）。
  3. **Tier-3：OS Fallback 與 Magic 安全防護**：超大區塊（如 `4 MB`）自動轉發系統配置；所有區塊前置 32-Byte `MyBlockHeader`，保證回傳位址 **16-Byte 對齊（支援 AVX/SSE 向量指令）**，並透過 `MAGIC_ALLOCATED (0x5543414C)` 與 `MAGIC_FREED (0x55434652)` 攔截重複釋放（Double-Free）。

### [2026-11-16 09:48] 追加紀錄（源於 Worklog 實機除錯）：修復 Windows 批次環境變數與 4MB `VirtualFree` 分頁卸載邊界
* **實作演進與除錯決策**：
  1. **批次腳本無註冊表依賴化**：在沙箱環境執行 `vcvars64.bat` 會因註冊表查詢受限而失敗；我們改為在 `scripts/build_and_run.bat` 中直接顯式注入 `MSVC_DIR` 與 `Windows 10 SDK` 之 `INCLUDE`、`LIB`、`PATH`，實現零外部依賴一鍵編譯。
  2. **診斷並分離 `4 MB` OS Fallback 與池內常駐塊之 Double-Free 測試**：在實機執行 `test_my_malloc.exe` 時，發現對 `4 MB` Tier-3 區塊呼叫 `myFree(huge)` 後，Windows CRT 會立即呼叫 `VirtualFree` 將該虛擬分頁從行程位址空間卸載（Unmap），若緊接著對同一指標做第二次讀取檢查 `hdr->magic` 會觸發作業系統層級的 `Access Violation`。因此我們在單元測試中將「超大區塊正常釋放驗證」與「池內常駐區塊（Tier-1/Tier-2）之 Double-Free 魔術碼攔截驗證」明確分離，使 5 項單元測試 100% 穩定通過。

### [2026-11-16 10:26] 追加紀錄（源於人類工程師要求對標 GitHub 開源最佳化）：將 Tier-2 Arena 升級為侵入式顯式雙向自由串列
* **技術決策演進**：
  回應人類工程師（曾子恩）「檢索國內外與 GitHub 類似討論並全面最佳化」之指令，我們檢視發現初版 Tier-2 Arena 在尋找空閒區塊時是由 `arena_first_block` 沿著實體相鄰指標線性掃描（若前方有大量已分配區塊會退化為 $O(N)$）。
  參考 Doug Lea 之 `dlmalloc` 與 GitHub 著名即時系統配置器 `mattconte/tlsf`（Two-Level Segregated Fit），我們將 Tier-2 升級為 **侵入式顯式雙向自由串列（Intrusive Explicit Doubly-Linked Free-List）**：
  * 於空閒區塊未使用的 Payload 前 16 Bytes 內嵌 `ArenaFreeNode { MyBlockHeader *free_prev; MyBlockHeader *free_next; }`（零額外 Header 空間開銷）。
  * 分配時直接由 `g_ctx.arena_free_head` 取出空閒區塊，**100% 跳過所有已分配區塊**；釋放時透過實體指標 `phys_prev` / `phys_next` 完成 $O(1)$ 雙向合併並同步維護自由串列。
