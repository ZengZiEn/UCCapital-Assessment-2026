# `TASK-04` 實作過程與技術決策報告 (`implementation-process.md`)

> **所屬任務**：[`/tasks/TASK-04-Visual-PDF-And-Governance/task.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-04-Visual-PDF-And-Governance/task.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-04.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-04.md)  
> **更新規範**：嚴格遵守 `AGENTS.md`，僅以「追加（Append）」方式動態記錄實作演進路徑與技術決策。

---

## Implementation Process

### [2026-11-16 10:00] 初始架構決策：零外部套件依賴之純 Python SVG 向量圖表與實證數據驅動 PDF 引擎
* **技術背景與設計思路**：
  回應人類工程師（曾子恩）「建立圖文並茂並且有圖表的 PDF 來作為最終說明」以及「每一題做完之後，要實際跑過，然後才整理報告」之雙重要求，我們決定不採用靜態貼圖或依賴外部繪圖庫（如 `matplotlib`），而是以純 Python 直接生成高精度 **SVG 向量圖表（Vector Graphics）** 內嵌於 HTML5，再呼叫系統內建之 Chrome / Microsoft Edge 無頭模式（`--headless=new --print-to-pdf`）直接渲染為印刷級 A4 PDF。
* **強制實證綁定**：
  在 `build_report.py` 執行時，程式會即時透過 `subprocess` 呼叫題目一（Python + C11 `fast_scheduler.exe`）、題目二（C11 `benchmark_malloc.exe`）與題目三（Python + C11 `fast_monte_carlo.exe`），將當次實機跑出的最新奈秒/毫秒數據匯出為 `report_data.json`，再動態填入兩份 PDF 報告中，確保兩份報告之數據 100% 同源且真實。

### [2026-11-16 10:12] 追加紀錄（源於 Worklog 實機渲染除錯）：解決含空白與中文路徑之 URI 編碼與視覺分頁微調
* **實作演進與修正**：
  在沙箱內首次呼叫無頭瀏覽器列印 PDF 時，發現工作區路徑含有空白（`my datas`）與中文字元（`面試相關`），直接拼接 `file:///` 字串會導致 Chromium 核心解析路徑失敗。我們改用 Python 標準庫 `pathlib.Path(html_path).as_uri()` 自動轉換為符合 RFC 3986 的百分比編碼 URI，並加上 `--no-sandbox` 旗標，成功在沙箱內一鍵產出 PDF。隨後逐頁檢視 PDF 渲染截圖，修正了圖號順序與單行溢頁問題。

### [2026-11-16 11:30] 追加紀錄（源於人類工程師目錄收斂指令）：建立雙 PDF 架構與 `docs_and_tools/` 收斂分層
* **技術決策演進**：
  為讓審查者打開專案根目錄時能一目了然，我們將根目錄收斂為僅保留考題簡報、兩份最終 PDF 報告（《最終說明報告.pdf》與《實作思考與軟體工程流程報告.pdf》）、`README.md`、`AGENTS.md`、三層級管理目錄（`strategy/`, `tasks/`, `worklogs/`）及三個題目子專案，其餘輔助文件與 PDF 產生器統一收納於 `docs_and_tools/`，並在 `run_all_pipeline.bat` 結尾加入自動清除 `.obj` 與 `__pycache__` 的清理機制。

### [2026-11-16 14:05] 追加紀錄（源於人類工程師誠信指示）：核對完整對話紀錄，公開透明呈現 Human-AI Agent 協同研發
* **實作演進**：
  人類工程師明確指示：「*檢查全部文件目錄，應該要提到關於有使用 AI 協作、Agents 分析等等，而不是全部做得像是我自己一個人做一樣，請確認過我們之間的對話，重新全部整理一遍，不需要避免說有使用 AI*」。
  我們完整讀取並核對對話紀錄 `transcript.jsonl`（Step 0 ~ Step 466），於全部文件與兩份 PDF 報告中新增 **「Human-in-the-Loop AI Agent 協同研發與工程治理閉環架構圖」** 及 **「8 輪真實對話決策時間軸」**，詳實呈現人類工程師如何主導架構、強制實證測試與質疑語言效率瓶頸，並與 AI Agent 協同完成跨語言極致最佳化。

### [2026-11-16 14:30] 追加紀錄（源於人類工程師導入 Antigravity Rules）：全面落地「The Chain of Truth」三層級管理框架
* **技術決策演進**：
  人類工程師導入專屬之 **「The Chain of Truth（真實之鏈）」** 三層級管理規則（`AGENTS.md`），強制規範 `/strategy/`（策略層）、`/tasks/TASK-ID-Name/`（任務與實作演進層）與 `/worklogs/YYYY-MM-DD-TASK-ID.md`（包含 `Execution`、`Obstacles`、`Resolution` 之實機日誌層）之向下追溯與向上同步機制。已完成全專案三層級目錄建置，並同步更新至雙份 PDF 報告中。
