# Antigravity Rules (本專案開發規則 — The Chain of Truth)

作為 Antigravity AI Agent，在協同處理本專案時必須嚴格遵守以下「The Chain of Truth（真實之鏈）」的三層級管理框架。任何開發與檔案修改都不應脫離此框架。

## 1. 目錄架構強制規範
- **Strategy 層**: 存放於 `/strategy/`。包含專案主體目標 (`product_vision.md`)、技術架構 (`app_architecture.md`) 與發展路線圖 (`roadmap.md`)。**【注意：此層級所有檔案之撰寫與更新，必須完全使用繁體中文（台灣）】**。
- **Task 層**: 存放於 `/tasks/TASK-ID-Name/`。每個任務必須有獨立資料夾。**【注意：任務主檔與相關說明必須使用繁體中文（台灣）】**。
- **Worklog 層**: 存放於 `/worklogs/`。命名格式緊扣 Task ID：`YYYY-MM-DD-TASK-ID.md`。**【注意：日誌內文必須完全使用繁體中文（台灣）】**。

## 2. 檔案內容細節標準
- **Worklogs 必須包含**: **【嚴重強調：以下所有章節的說明、分析與文字敘述，必須 100% 嚴格使用繁體中文（台灣）撰寫】**
  - `## Execution`: 紀錄當天使用的關鍵 CLI 指令（如編譯、單元測試、基準測試、流水線腳本等）。
  - `## Obstacles`: 紀錄遇到的報錯訊息（Error Logs/Exceptions）與邏輯困難處。
  - `## Resolution`: 紀錄如何修復問題、查閱的文檔連結或程式碼改動思路。
- **TaskReport (`implementation-process.md`) 必須包含**:
  - `## Implementation Process`: 動態紀錄該功能的實作演進路徑與技術決策。**【嚴重強調：此處的實作過程與技術決策紀錄，必須完全使用繁體中文（台灣），並採用台灣技術習慣用語】**。

## 3. 三層關聯邏輯 (The Chain of Truth)
- **向下追溯**: 所有 Task 的建立與發起，都必須源於 Strategy 層定下的大方向。
- **向上同步 (Essential)**: 
  - 建立 Worklog 後，必須自動更新對應的 Task 主檔任務進度。**【注意：更新之內文必須保持使用繁體中文（台灣）】**。
  - 建立 Worklog 後，必須自動更新該 Task 的 TaskReport (`implementation-process.md`) 中的實作過程。**【注意：追加之內文必須完全使用繁體中文（台灣）】**。
  - 若 Task 實作中出現計畫外的新功能，必須主動提議更新 Strategy 中的 Roadmap。**【注意：與使用者的提議對話及後續更新，務必一律使用繁體中文（台灣）】**。

## 4. 嚴格禁止事項
- [禁止] 在沒有對應 Task 結構的情況下隨意建立 Worklog。
- [禁止] 在大幅度更新代碼或解除 Bug 後忘了生成/更新 Worklog。
- [禁止] 覆蓋/刪除過去的 TaskReport 紀錄，僅能以「追加 (Append)」下筆方式進行紀錄更新。
- **[禁止] 在撰寫、更新上述任何檔案或與使用者對話時使用非繁體中文（台灣）的語系（代碼、報錯 Log 與既有英文專有名詞除外）。**
