# 專案主體目標與產品願景 (`product_vision.md`)

> **所屬層級**：Strategy 層 (`/strategy/product_vision.md`)  
> **治理框架**：The Chain of Truth（Strategy $\to$ Task $\to$ Worklog 三層級管理框架）

---

## 一、專案背景與核心願景

本專案為針對台灣頂尖量化與高頻交易機構——**優式資本（UC Capital）** 之面試前考題（`2026 Q4 面試前考題 V1.pptx`）所建置的企業級軟體工程與演算法實證專案。

優式資本 AI 部門負責人翁嘉頎（Phantom Weng）前輩於考題邀請信中明確闡述了量化交易系統的三大核心挑戰與探索方向：
1. **極端執行效率（Microsecond / Nanosecond Performance）**：「一個自動化交易系統不只是把程式穩定寫出來，而且要在程式效率上斤斤計較到微秒等級。」
2. **高可維護性與易修改性（Maintainability & Adaptability）**：「隨著交易策略應用市場不斷調整，程式必須易於修改及維護。一個程式有效運行在超大資料量 + 極端效能下，這本身就是非常困難的挑戰。」
3. **AI 賦能交易系統研發（AI-Augmented Engineering）**：「如何應用 AI 的分析能力去輔助目前交易系統，是我們正在探索的方向。」

因此，本專案的主體願景並非僅交付「能跑出答案的單一腳本」，而是打造一套 **「同時具備 Python 高抽象可維護領域模型與 C11 奈秒級底層原生引擎之雙軌制系統」**，並以 **「The Chain of Truth（真實之鏈）」三層級管理框架** 嚴格治理 **Human-in-the-Loop AI Agent 協同研發流程**。

---

## 二、三大考題交付目標與量化驗收指標 (OKRs)

所有向下拆解之 Task（`TASK-01` 至 `TASK-04`）均須嚴格對齊以下主體目標：

| 對應任務 ID | 考題領域與核心命題 | 效能目標 (Performance Target) | 可維護性與工程品質目標 (Maintainability Target) |
| :--- | :--- | :--- | :--- |
| **`TASK-01`**<br>(`Q1_Scheduling`) | **題目一：員工排班與突發狀況動態應變系統**<br>支援 $n$ 位員工、每週上限 2 天、每日必有 1 人值班，並處理臨時請假突發狀況。 | • C11 暫存器級引擎單解搜尋 **$< 30\text{ ns}$**<br>• 全 34 解枚舉 **$< 200\text{ ns}$**<br>• 線上突發請假應變查表 **$O(1) < 1\ \mu\text{s}$** | • 雙求解器架構（Bitmask+MRV 回溯 + Dinic 最大流 $O(E\sqrt{V})$）<br>• 殘餘二部圖 BFS 保證變動天數（漢明距離）最小<br>• 通過 374 種請假窮舉與 $n=50$ 人擴展單元測試 |
| **`TASK-02`**<br>(`Q2_MemoryAllocator`) | **題目二：C 語言 `malloc` 效能優化與自訂 `myMalloc` 實作**<br>解決反覆呼叫 `malloc(10000 * sizeof(int))` 與 `free()` 之效能瓶頸（含 +10% 實作驗證加分）。 | • 單一 `40 KB` 百萬次配置釋放較標準 `malloc` **加速 $> 20\times$**<br>• 批次 $64 \times 40\text{ KB}$ 高峰負載 **加速 $> 30\times$**<br>• 分配與釋放皆達嚴格 **$O(1)$** | • Tier-1 侵入式 LIFO Slab 池 + Tier-2 顯式雙向自由串列 Arena（參考 `dlmalloc`/`TLSF`）<br>• 保證 16-Byte 記憶體對齊<br>• 內建 Magic Number 狀態標記主動攔截 Double-Free |
| **`TASK-03`**<br>(`Q3_PatternAnalysis`) | **題目三：色彩矩陣特徵、趨勢與規則之演算法分析歸納**<br>挖掘無數值色塊圖之隱藏規律並以演算法與統計檢定證明。 | • C11 無除法百萬次（$1,000,000$ 次）蒙地卡羅洗牌檢定總耗時 **$< 200\text{ ms}$** | • 零第三方影像套件依賴，純手寫 RFC 2083 Paeth PNG 解碼器<br>• 完整證明六大規律（正交 0 衝突、右三欄鏡像對稱、最大熵、奇偶平衡、方向異向性 $\chi^2$、跨題排班同構與 `Row 9` 馬可夫預測器） |
| **`TASK-04`**<br>(`docs_and_tools` & 治理) | **跨題整合：實證測試流水線、視覺化向量圖表雙 PDF 報告與三層級工程治理** | • 一鍵自動化完成三題 C11 編譯、18 項單元測試、214 萬次基準測試與雙 PDF 渲染 | • 嚴格執行 **The Chain of Truth**（`/strategy/` $\leftrightarrow$ `/tasks/` $\leftrightarrow$ `/worklogs/`）三層級可追溯管理，誠實揭露 Human-AI Agent 協同研發脈絡 |
