# 任務主檔：`TASK-04` 視覺化向量圖表雙 PDF 報告、實證流水線與三層級工程治理 (`task.md`)

> **所屬層級**：Task 層 (`/tasks/TASK-04-Visual-PDF-And-Governance/task.md`)  
> **向下追溯來源**：[`/strategy/product_vision.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/product_vision.md) — 跨題整合與工程治理目標  
> **實作演進報告**：[`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-04-Visual-PDF-And-Governance/implementation-process.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-04.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-04.md)  
> **對應程式碼目錄**：[`/docs_and_tools/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/docs_and_tools/)、[`/strategy/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/)、[`/tasks/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/)、[`/worklogs/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/)

---

## 一、任務背景與驗收條件

1. 建立零外部套件依賴之純 Python SVG 向量圖表與無頭瀏覽器 PDF 自動化渲染引擎，產出圖文並茂之《最終說明報告 PDF》與《實作思考與軟體工程流程報告 PDF》。
2. 建立全專案一鍵自動化實證流水線 (`docs_and_tools/run_all_pipeline.bat`)，確保「先實機跑通三題測試與 Benchmark，再將最新數據寫入報告」。
3. 誠實、透明地揭露 **Human-in-the-Loop AI Agent 協同研發流程**，並全面落實 `AGENTS.md` 所定義之 **「The Chain of Truth」三層級管理框架（Strategy $\to$ Task $\to$ Worklog）**。

---

## 二、任務進度追蹤 (Task Progress — 由 Worklog 向上同步更新)

- [x] **Subtask 4.1**：撰寫主技術報告產生器 (`docs_and_tools/pdf_generator/build_report.py`)，內嵌 17 張高解析 SVG 向量圖表並即時執行三題 C11/Python 擷取實測 JSON
- [x] **Subtask 4.2**：修復含空白 (`my datas`) 與中文路徑下 Chrome/Edge 無頭模式 `file:///` 載入失敗問題（改用 `pathlib.Path.as_uri()`），並逐頁視覺檢查消除溢頁
- [x] **Subtask 4.3**：撰寫思考與軟體工程流程報告產生器 (`docs_and_tools/pdf_generator/build_workflow_pdf.py`)，內嵌 11 張流程圖、時間軸與多代加速對比圖
- [x] **Subtask 4.4**：收斂專案根目錄結構，建立一鍵驗證與清理流水線 (`docs_and_tools/run_all_pipeline.bat`)，並部署至 GitHub (`ZengZiEn/UCCapital-Assessment-2026`)
- [x] **Subtask 4.5**：核對完整對話紀錄 (`transcript.jsonl`)，於全部文件與雙份 PDF 報告中誠實揭露 **Human-AI Agent 協同研發閉環與 8 輪對話決策脈絡**
- [x] **Subtask 4.6**：建立 `AGENTS.md` 與 **The Chain of Truth 三層級目錄 (`/strategy/`, `/tasks/`, `/worklogs/`)**，完成向下追溯與向上同步

---

## 三、最終實測驗收指標

* **核心 PDF 報告 1**：[`UCCapital_面試考題_最終說明報告.pdf`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/UCCapital_面試考題_最終說明報告.pdf)（共 14 頁整，17 張 SVG 圖表，零溢頁）
* **核心 PDF 報告 2**：[`UCCapital_實作思考與軟體工程流程報告.pdf`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/UCCapital_實作思考與軟體工程流程報告.pdf)（共 5 頁整，11 張 SVG 圖表，含 Human-AI 閉環與 The Chain of Truth 架構）
* **The Chain of Truth 三層級檔案完整性**：`/strategy/` (3 檔)、`/tasks/` (4 個任務資料夾共 8 檔)、`/worklogs/` (4 份標準格式日誌) 100% 齊備且雙向關聯
