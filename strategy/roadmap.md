# 專案發展路線圖與演進紀錄 (`roadmap.md`)

> **所屬層級**：Strategy 層 (`/strategy/roadmap.md`)  
> **治理框架**：The Chain of Truth（Strategy $\to$ Task $\to$ Worklog 三層級管理框架）

---

## 一、研發階段總覽 (Development Phases)

本路線圖定義本專案從初始考題解析至最終雙軌極致最佳化與三層級治理收斂之完整發展軌跡。所有計畫內任務與實作過程中由人類工程師（曾子恩）與 AI Agent 協同發起之**「計畫外升級功能（Unplanned Enhancements）」**均同步更新並記錄於此：

| 階段 | 對應 Task ID | 核心里程碑目標 | 狀態 |
| :--- | :---: | :--- | :---: |
| **Phase 1：考題逆向拆解與五階段 SDLC 建構** | `TASK-01` ~ `TASK-03` | 解析 PPTX 內部 XML 與無文字 PNG 圖檔，調研 GitHub 開源方案，建立三題對稱之軟體工程目錄。 | ✅ 已完成 |
| **Phase 2：初版核心演算法實作與實證測試除錯** | `TASK-01` ~ `TASK-03` | 完成 Q1 雙求解器与 BFS 修復、Q2 雙層混合記憶體池、Q3 純標準庫 PNG 解碼與六大規律統計證明，並全數通過實機測試。 | ✅ 已完成 |
| **Phase 3：【計畫外升級 1】跨語言 C11 奈秒級極致最佳化** | `TASK-01` ~ `TASK-03` | 回應人類工程師對「語言選擇是否影響執行效率」之關鍵質疑，增建 Q1 C11 Bitboard/SWAR 引擎、升級 Q2 為顯式雙向自由串列、增建 Q3 C11 Lemire 無除法百萬次蒙地卡羅引擎。 | ✅ 已完成 |
| **Phase 4：【計畫外升級 2】考題逐字核對與擴展預測功能** | `TASK-01`, `TASK-03`, `TASK-04` | 逐字核對 PPTX 簡報，新增 Q1 一般化 $n=50$ 位員工擴展測試 (`test_07`)、新增 Q3 下一列 (`Row 9`) 馬可夫規律生成預測器 (`test_06`) 與複雜度總表。 | ✅ 已完成 |
| **Phase 5：視覺化雙 PDF 報告、Human-AI 協作揭露與 The Chain of Truth 治理收斂** | `TASK-04` | 建立一鍵驗證流水線 `run_all_pipeline.bat`，產出 28 張 SVG 向量圖表之雙份 PDF 報告，並完整落地 `/strategy/`、`/tasks/`、`/worklogs/` 三層級管理框架。 | ✅ 已完成 |

---

## 二、計畫外新功能向上同步紀錄 (Upward Sync of Unplanned Enhancements)

依據 `AGENTS.md` 第 3 條「若 Task 實作中出現計畫外的新功能，必須主動更新 Strategy 中的 Roadmap」，以下記錄開發過程中經人類工程師與 AI Agent 協同決策所追加之四大關鍵升級：

1. **[2026-11-16 10:00] 新增零依賴 SVG 向量圖表與自動化實證 PDF 渲染管線（源於 `TASK-04`）**：
   * **升級原因**：為使量化交易團隊能直觀檢視最大流網路、Slab 記憶體佈局與蒙地卡羅分布，新增純 Python SVG 圖表產生器，並強制綁定實機測試輸出 JSON。
2. **[2026-11-16 10:22] 新增 C11 (`MSVC /O2`) 原生極速引擎與顯式自由串列升級（源於 `TASK-01`, `TASK-02`, `TASK-03`）**：
   * **升級原因**：初版 Python 雖具高可維護性，但為突破直譯器延遲極限，引進 `Stockfish` Bitboard/SWAR（將 Q1 單解推進至 `17.0 ~ 20.2 ns`）、`mattconte/tlsf` 侵入式顯式雙向自由串列（Q2 加速達 `25x ~ 36x`）與 Daniel Lemire 無除法乘法位移洗牌（Q3 百萬次模擬 `105 ~ 174 ms`）。
3. **[2026-11-16 11:24] 新增 Q1 $n=50$ 大規模員工擴展測試與 Q3 `Row 9` 馬可夫規律預測器（源於 `TASK-01`, `TASK-03`）**：
   * **升級原因**：經重新逐字核對原始考題簡報，為強化「某公司有 $n$ 位員工」之規模泛化證明與「圖形趨勢規則」之生成預測能力而追加實作。
4. **[2026-11-16 14:28] 導入 Human-AI Agent 協同透明揭露與「The Chain of Truth」三層級管理框架（源於 `TASK-04`）**：
   * **升級原因**：誠實且結構化地呈現人類工程師（曾子恩）如何透過 `/strategy/` $\to$ `/tasks/` $\to$ `/worklogs/` 三層級框架治理 AI Agent 協同研發。
