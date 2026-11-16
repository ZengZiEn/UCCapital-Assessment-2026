# 任務主檔：`TASK-02` C 語言 `malloc` 效能問題與自訂 `myMalloc` 配置器實作 (`task.md`)

> **所屬層級**：Task 層 (`/tasks/TASK-02-Memory-Allocator/task.md`)  
> **向下追溯來源**：[`/strategy/product_vision.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/product_vision.md) — 題目二核心目標（含 +10% 實作驗證加分）  
> **實作演進報告**：[`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-02-Memory-Allocator/implementation-process.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-02.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-02.md)  
> **對應程式碼目錄**：[`/Q2_MemoryAllocator/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q2_MemoryAllocator/)

---

## 一、任務背景與驗收條件

針對考題簡報第 3 頁「題目二：C 語言的 `malloc` 效能問題」：
1. 剖析為何在程式中大量反覆呼叫 `malloc(10000 * sizeof(int))`（`40,000 Bytes`）與 `free()` 時效能低落。
2. 提出完整的改善方案與 `myMalloc()` 設計思路。
3. **額外加分 +10% 要求**：以標準 C 語言實際撰寫 `myMalloc()` / `myFree()` 程式碼，並透過單元測試與高頻壓力 Benchmark 實際驗證效能提升。

---

## 二、任務進度追蹤 (Task Progress — 由 Worklog 向上同步更新)

- [x] **Subtask 2.1**：剖析標準 `malloc/free` 在 `40 KB` 反覆配置下之四大效能瓶頸（系統呼叫與分頁清零、自由串列搜尋、鎖競爭、快取失誤）(`Q2_MemoryAllocator/docs/01_analysis.md`)
- [x] **Subtask 2.2**：設計 32-Byte `MyBlockHeader`（含 16-Byte 對齊保證與 `MAGIC_ALLOCATED` / `MAGIC_FREED` 防重放標記）(`include/my_malloc.h`)
- [x] **Subtask 2.3**：實作 Tier-1 Fast-Path $O(1)$ 侵入式 LIFO Slab Pool（128 個 `40,960 B` Slots）與 Tier-2 通用 Arena (`src/my_malloc.c`)
- [x] **Subtask 2.4**：撰寫題目示範主程式 (`src/main_demo.c`)、5 大項單元測試 (`tests/test_my_malloc.c`) 與 214 萬次高精度計時 Benchmark (`tests/benchmark_malloc.c`)
- [x] **Subtask 2.5**：修復沙箱環境下 MSVC 批次編譯腳本 (`scripts/build_and_run.bat`) 與 `4 MB` OS Fallback 區塊經 `VirtualFree` 卸載之邊界測試問題
- [x] **Subtask 2.6**：【計畫外跨語言開源對標升級】參考 `dlmalloc` 與 GitHub `mattconte/tlsf`，將 Tier-2 Arena 由隱式線性掃描升級為 **侵入式顯式雙向自由串列 (`ArenaFreeNode`)**

---

## 三、最終實測驗收指標（MSVC x64 `/O2` 最佳化編譯）

* **場景 1（單一 `40 KB` 反覆配置與釋放 1,000,000 次）**：標準 `malloc` 耗時 `85.94 ~ 105.92 ms` $\to$ `myMalloc` 僅 **`3.35 ~ 4.37 ms`（提速 `24.2x ~ 25.7x`，節省 `96.1%` 時間）**
* **場景 2（批次同時配置 64 個 `40 KB` $\times$ 10,000 輪）**：標準 `malloc` 耗時 `103.44 ~ 147.00 ms` $\to$ `myMalloc` 僅 **`2.92 ~ 4.03 ms`（提速 `35.4x ~ 36.5x`，節省 `97.2%` 時間）**
* **場景 3（128B ~ 4KB 混合大小動態配置與雙向合併 500,000 次）**：提速 **`3.95x ~ 7.16x`**，外部碎片最終完全合併為 1 個完整空閒塊
* **自動化單元測試**：`5 / 5 PASS` (`100%`)
