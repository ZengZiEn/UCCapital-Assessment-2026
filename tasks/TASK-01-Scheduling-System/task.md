# 任務主檔：`TASK-01` 員工排班與突發狀況動態應變系統 (`task.md`)

> **所屬層級**：Task 層 (`/tasks/TASK-01-Scheduling-System/task.md`)  
> **向下追溯來源**：[`/strategy/product_vision.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/product_vision.md) — 題目一核心目標  
> **實作演進報告**：[`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-01-Scheduling-System/implementation-process.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-01.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-01.md)  
> **對應程式碼目錄**：[`/Q1_Scheduling/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q1_Scheduling/)

---

## 一、任務背景與驗收條件

針對考題簡報第 2 頁「題目一：排班問題」，設計並實作支援 $n$ 位員工（範例為 `A, B, C, D`）、一週五天（`Mon ~ Fri`）之排班與突發請假動態應變系統：
1. `Mon ~ Fri` 每天必須恰有 1 人上班（不可開天窗）。
2. 每位員工每週最多只能上班 2 天，且僅能排在其「有空的日子」。
3. 排好班表後，若某位員工臨時表示「這週某一天不能上了」，演算法須能快速應變並最小化對原班表的變動衝擊。

---

## 二、任務進度追蹤 (Task Progress — 由 Worklog 向上同步更新)

- [x] **Subtask 1.1**：解構 PPTX 題目規格並完成作業研究（OR）與 GitHub 開源文獻調研 (`Q1_Scheduling/docs/01_analysis.md`)
- [x] **Subtask 1.2**：建立 Python 領域模型層 (`src/models.py`)，實作 5-bit `availability_mask` 位元遮罩預編譯與 `Schedule.validate()` 不變量檢查器
- [x] **Subtask 1.3**：實作雙引擎初始排班求解器 (`src/solvers.py`)：`BitmaskMRVSolver`（MRV 啟發式回溯法）與 `MaxFlowDinicSolver`（Dinic 網路最大流 $O(E\sqrt{V})$）
- [x] **Subtask 1.4**：實作突發請假應變層 (`src/contingency.py`)：殘餘二部圖 BFS 最短交替增廣鏈修復、全 34 解韌性評分器與 $O(1)$ 預計算查找表 (`ContingencyTable`)
- [x] **Subtask 1.5**：【計畫外跨語言升級】平坦化 Python 預編譯 Tuple，並參考 `Stockfish` Bitboard/SWAR 實作 C11 暫存器級原生極速引擎 (`src_native/fast_scheduler.c`)
- [x] **Subtask 1.6**：【計畫外擴展驗證】新增一般化 $n=50$ 位員工大規模擴展與 1-Hop 修復單元測試 (`test_07_general_n_employees_scalability`)
- [x] **Subtask 1.7**：通過全部 7 大項單元測試（含 $34 \times 11 = 374$ 種請假窮舉驗證）並產出量化基準報告 (`results/test_and_benchmark_report.md`)

---

## 三、最終實測驗收指標

* **C11 Bitboard/SWAR 單解搜尋耗時**：`16.98 ~ 20.22 ns`（比 Python 快逾 `585 ~ 800 倍`）
* **C11 全 34 解枚舉耗時**：`95.10 ~ 122.54 ns`
* **最佳基準班表 (`Mon:A | Tue:C | Wed:A | Thu:B | Fri:D`)**：面對任何值班者臨時請假，**100% (5/5) 皆可以 1-Hop（僅找 1 人直接代班，0 次連鎖換班）解決**
* **自動化單元測試**：`7 / 7 PASS` (`100%`)
