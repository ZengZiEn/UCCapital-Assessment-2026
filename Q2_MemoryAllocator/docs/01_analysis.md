# 題目二：C 語言的 `malloc` 效能問題 — 深度分析與開源架構參考 (`01_analysis.md`)

## 1. 題目問題核心剖析

題目給出以下典型 C 語言程式碼片段：
```c
int *ptr = NULL;
ptr = (int *)malloc(10000 * sizeof(int));
// 當記憶體使用完畢，不再需要時，以 free() 將記憶體空間回收
if (NULL != ptr) {
    free(ptr);
    ptr = NULL;
}
```
當程式在熱路徑（Hot Path，例如高頻交易訊號計算迴圈、Order Book 更新或即時封包處理）中**大量反覆呼叫 `malloc()` 與 `free()`** 時，會產生嚴重的效能瓶頸與延遲抖動（Latency Jitter）。

---

## 2. 為什麼反覆呼叫標準 `malloc()` / `free()` 很慢？（五大底層原因）

### 2.1 作業系統核心態切換與虛擬記憶體映射開銷（Syscall & Page Fault Overhead）
* 每次請求 `10,000 * sizeof(int)`（約 `40,000 Bytes ≈ 39.06 KB`），若反覆申請與釋放，C 標準庫配置器（如 glibc `ptmalloc2` 或 Windows CRT Heap）在快取區閾值飽和時會頻繁呼叫作業系統底層 API（Linux 的 `brk()`/`mmap()` 或 Windows 的 `VirtualAlloc()`/`HeapAlloc()`）。
* 這不僅觸發 **User Mode $\leftrightarrow$ Kernel Mode 上下文切換（Context Switch）**，當作業系統重新分配虛擬分頁時，為了安全性必須將實體分頁清零（Zero-page Faults）並刷新 **TLB（Translation Lookaside Buffer）**，單次耗時高達數千個 CPU 週期。

### 2.2 自由串列搜尋、分割與合併成本（Free-List Search, Splitting & Coalescing）
* 通用型 `malloc()` 必須支援任意大小的記憶體請求（從 `1 Byte` 到數 `GB`）。
* 為了尋找合適的空閒區塊，配置器必須走訪內部的 Bins / Free Lists（First-fit 或 Best-fit 演算法），找到後進行區塊分割（Splitting），並在 `free()` 時檢查前後相鄰區塊以進行邊界合併（Boundary-Tag Coalescing），每次操作涉及大量條件分支與指標更新。

### 2.3 多執行緒鎖競爭（Mutex / Arena Lock Contention）
* 標準 `malloc()` 必須保證執行緒安全（Thread-Safety）。每次呼叫 `malloc()` 與 `free()` 時，執行緒必須獲取 Heap Arena 的互斥鎖（Mutex Lock 或 Atomic CAS 操作），在高併發環境下造成嚴重的鎖競爭與管線停頓。

### 2.4 記憶體碎裂化（Internal & External Fragmentation）
* 大量不同生命週期與不同大小的區塊交錯分配與釋放後，Heap 空間會碎裂成許多不連續的小空洞（外部碎裂），導致搜尋時間隨執行時間拉長而退化，且降低空間利用率。

### 2.5 CPU 快取局部性惡化（Poor Cache Locality）
* 標準 Heap 經過多次分配後，回傳的位址可能散落在不同的虛擬記憶體分頁，導致 **L1/L2/L3 Cache Miss** 與 **TLB Miss** 機率大幅攀升。

---

## 3. 如何改善？（工程實務與開源解決方案）

參考 Linux Kernel 的 **Slab Allocator**、Google 的 **`tcmalloc`**、Facebook 採用的 **`jemalloc`**，以及 GitHub 上經典的高頻交易記憶體池設計，改善策略可分為「應用程式層優化」與「自訂配置器 `myMalloc()` 設計」兩個層次：

### 3.1 應用程式層級改善策略（不改動 Allocator 時）
1. **記憶體重用 / 緩衝區預分配（Buffer Reuse / Pre-allocation）**：將 `malloc()` 移出迴圈外（Loop Hoisting），在初始化階段配置一次 `10,000 * sizeof(int)`，迴圈內重複覆寫使用（或搭配 `memset`），直到程式結束才 `free()`。
2. **Thread-Local Scratchpad / 靜態緩衝區**：若生命週期僅限單一函式或單一執行緒，且大小固定為 40 KB，可使用 `thread_local` 靜態陣列或預先配置的執行緒專屬緩衝區，達到零動態配置開銷。

### 3.2 重新設計 `myMalloc()` 的雙層混合式架構（Hybrid Memory Pool Architecture）
為了同時滿足 **「題目特定大小（`10,000 * sizeof(int)`）的極致 $O(1)$ 速度」** 與 **「支援任意大小的通用分配需求」**，我們的 `myMalloc()` 採用 **雙層混合式記憶體池（Dual-Tier Hybrid Memory Pool）**：

1. **第一層：Fast-Path 固定尺寸 Slab 物件池（Intrusive Free-List Slab Pool）**
   * 預先向 OS 一次性申請一大塊連續且對齊至 **64-byte Cache Line** 的記憶體池（Pre-allocated Slab Arena）。
   * 每個區塊（Slot）大小對齊以容納常用尺寸（如 `10,000 * sizeof(int) = 40,000 Bytes`）。
   * 利用 **侵入式單向自由串列（Intrusive Singly-Linked Free List）**：當區塊處於空閒狀態時，直接將區塊內部的前 8 Bytes 當作 `next` 指標指向下一個空閒區塊（零額外節點記憶體開銷）。
   * **`myMalloc()` 僅需 1 次指標讀取（Pop Head，嚴格 $O(1)$）**；**`myFree()` 僅需 1 次指標寫入（Push Head，嚴格 $O(1)$）**！且因為採取 LIFO（後進先出）順序回收，剛釋放的區塊仍熱騰騰地留在 CPU L1/L2 Cache 中（**極致 Cache Warmth**）！
2. **第二層：通用型 Arena 配置器（Boundary-Tag Coalescing Free-List Arena）**
   * 當請求大小不屬於固定 Slab 規格時，自動路由至預先分配的通用 Arena，支援動態區塊分割（Block Splitting）與釋放時的前後相鄰空閒塊即時合併（Immediate Bi-directional Coalescing），消除外部碎片。
   * 若請求超大記憶體或池已滿，則優雅降級（Graceful Fallback）至系統底層配置，並透過區塊標頭（Block Header）的 `tier_magic` 欄位自動識別歸屬，確保 `myFree()` 100% 安全回收。

