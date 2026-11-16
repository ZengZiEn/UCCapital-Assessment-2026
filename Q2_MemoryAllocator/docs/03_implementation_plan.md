# 題目二：`myMalloc()` 實作計畫與測試驗證規格 (`03_implementation_plan.md`)

## 1. 實作階段規劃

| 階段 | 目標檔案 | 實作內容 | 驗證標準 |
| :--- | :--- | :--- | :--- |
| **Phase 1：標頭與 API 定義** | `include/my_malloc.h` | 定義 `myMalloc`、`myFree`、`myCalloc`、`myRealloc`、`myMallocInit`、`myMallocDestroy` 及統計結構 `MyAllocatorStats` | 介面清晰、符合標準 C99/C11 規範 |
| **Phase 2：核心配置器實作** | `src/my_malloc.c` | 實作 Tier-1 O(1) Slab Pool（針對 `10,000 * sizeof(int)` 特化加速）與 Tier-2 Boundary-Tag Coalescing Arena | 零記憶體洩漏、支援區塊分割與雙向合併、攔截 Double-Free |
| **Phase 3：題目情境展示** | `src/main_demo.c` | 實作投影片第 3 頁之 `10,000 * sizeof(int)` 配置與釋放範例，並展示內部統計數據 | 正常讀寫 10,000 個整數且無任何錯誤 |
| **Phase 4：單元測試與極限驗證** | `tests/test_my_malloc.c` | 測試 16-Byte 對齊、讀寫完整性、Slab 池耗盡自動轉移 Arena、前後區塊合併、NULL 與 Double-Free 防護 | 全部斷言 (Assertions) 100% 通過 |
| **Phase 5：百萬次效能基準測試** | `tests/benchmark_malloc.c` | 對比系統 `malloc/free` 與 `myMalloc/myFree` 在 3 種工作負載下的真實耗時與吞吐量（使用 `QueryPerformanceCounter` 高精度計時） | 實測驗證加速倍率並產出量化報告（爭取 +10% 加分） |

---

## 2. 效能基準測試（Benchmark）三大場景設計

為了客觀且全面地證明 `myMalloc()` 的效能優勢，我們設計了三個測試場景：
1. **場景 A（題目核心場景：高頻率單一 `10,000 * sizeof(int)` 反覆配置與釋放）**：
   * 連續執行 $1,000,000$ 次 `malloc(10000 * sizeof(int))` + 首尾資料寫入 + `free()`。
2. **場景 B（批次高峰負載：同時配置 64 個 `10,000 * sizeof(int)` 陣列後批次釋放）**：
   * 模擬交易系統在瞬間行情爆發時同時建立多個大型計算緩衝區，重複 $10,000$ 輪（共 $640,000$ 次配置與釋放）。
3. **場景 C（混合大小動態配置：64B ~ 8192B 變動尺寸在 Arena 內分割與合併）**：
   * 驗證當請求不走固定 Slab 時，Tier-2 通用 Arena 依然顯著快於標準 `malloc/free`。

