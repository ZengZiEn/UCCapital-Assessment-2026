# 題目一：排班問題 — 實作計畫與複雜度評估 (`03_implementation_plan.md`)

## 1. 開發階段劃分（Software Engineering Lifecycle）

| 階段 | 模組 / 檔案 | 實作重點 | 驗收指標 |
| :--- | :--- | :--- | :--- |
| **Phase 1：領域建模** | `src/models.py` | 定義 `Day`、`Employee`、`ScheduleConfig`、`Schedule`，實作 Bitmask 預編譯與班表合法性驗證器 | 100% 攔截非法指派（超時、無空檔、漏排） |
| **Phase 2：雙引擎求解器** | `src/solvers.py` | 實作 `BitmaskMRVSolver`（含 MRV 排序與位元遮罩剪枝）與 `MaxFlowDinicSolver`（Dinic 最大流） | 兩求解器結果一致，且能完整找出範例全部 34 組可行解 |
| **Phase 3：突發應變引擎** | `src/contingency.py` | 實作 BFS 最短增廣鏈局部修復、全解魯棒性評分器、以及 $O(1)$ 預計算應變查找表 | 變動天數（Hamming Distance）嚴格最小，查詢延遲 $< 1\ \mu\text{s}$ |
| **Phase 4：測試與基準驗證** | `tests/test_scheduling.py` | 撰寫單元測試（正常排班、全部 374 種突發請假、無解退化邊界、大規模壓力測試） | 所有測試 100% 通過，產出量化效能報告 |
| **Phase 5：C11 原生極速引擎** | `src_native/fast_scheduler.c` | 引進 Stockfish Bitboard 與 SWAR 單暫存器工時打包技術，消除直譯器開銷 | 單解耗時壓縮至 `~20 ns`，較 Python 提速逾 400~650 倍 |

---

## 2. 演算法時間與空間複雜度評估

設員工數為 $N$，一週工作天數為 $D$（本題 $D=5$），每位員工最多上班 $K$ 天（本題 $K=2$），可用關係邊數為 $E \le N \times D$：

| 演算法模組 | 時間複雜度 | 空間複雜度 | 工程特性說明 |
| :--- | :--- | :--- | :--- |
| **Dinic 最大流單次求解** | $O(E \sqrt{V}) = O(N D \sqrt{N + D})$ | $O(N + D + E)$ | 具備嚴格多項式時間上界，適合大規模排班 |
| **Bitmask + MRV 單解搜尋** | 最壞 $O(N^D)$，MRV 剪枝後實測僅展開 6 個節點 | $O(N + D)$ | 常數極小、Cache-friendly，微秒級完成 |
| **BFS 殘餘網路局部修復** | $O(V + E) = O(N \cdot D)$ | $O(N + D)$ | 保證找出變動人數最少（Shortest Alternating Path）的調度方案 |
| **預計算應變查找表查詢** | **$O(1)$** | $O(E \cdot D)$ | 空間換時間，線上零計算延遲 |
