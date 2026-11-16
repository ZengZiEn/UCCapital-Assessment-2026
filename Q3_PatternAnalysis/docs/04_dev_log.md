# 題目三：分析歸納題 — 人機協作（Human-AI Agent）研發探索、除錯與極致最佳化完整日誌 (`04_dev_log.md`)

本文件完整記錄「題目三：色彩矩陣特徵、趨勢與規則之演算法分析歸納」在 **Human-in-the-Loop AI Agent 協同研發模式** 下，由 **曾子恩（人類工程師：負責問題分解、要求實機跑通驗證、語言效率質疑與考題完備性核對）** 與 **AI Agent（負責無第三方套件下撰寫 RFC 2083 Paeth PNG 解碼器、自動化多假說特徵探勘、卡方動態統計修正與 C11 Lemire 無除法百萬次蒙地卡羅引擎實作）** 共同推進的每一個步驟與修改動作。

---

## 完整時間軸與人機協作修改紀錄 (Chronological Human-AI Collaboration Log)

### [2026-11-16 09:15] 步驟 1：從原始 PPTX 壓縮檔提取內嵌圖片與結構檢查
* **執行動作**：解析 `2026 Q4 面試前考題 V1.pptx`，發現第 4 頁（`ppt/slides/slide4.xml`）引用了 `ppt/media/image1.png`（檔案大小 `1,739 Bytes`），將其提取至 `Q3_PatternAnalysis/assets/slide4_image1.png`。
* **初步檢查**：嘗試載入 `PIL (Pillow)` 時發現環境為純標準庫 Python 3.12（未安裝第三方影像處理套件）。
* **工程決策**：不依賴任何外部套件，直接以 Python 標準庫 `struct` 與 `zlib` 撰寫符合 **RFC 2083 標準的純 Python PNG 底層解碼器 (`src/png_decoder.py`)**，實作 `None`, `Sub`, `Up`, `Average`, `Paeth` 五種掃描線濾波器還原演算法。

### [2026-11-16 09:22] 步驟 2：像素級逆向工程與 $9 \times 5$ 矩陣還原
* **執行動作**：解析 `IHDR` 與 `IDAT` 區塊，確認畫布尺寸為 `575 x 313 px`（8-bit RGBA），並於 $9 \times 5$ 網格中心取樣。
* **關鍵發現**：
  * 單格寬度 $575 / 5 = 115\text{ px}$、單格高度 $313 / 9 \approx 34.78\text{ px}$，且四種顏色 `#FF0000` (紅 `R`)、`#FFC000` (黃 `Y`)、`#70AD47` (綠 `G`)、`#0070C0` (藍 `B`) 完全吻合 Microsoft Excel 標準主題填滿色！證實原圖出自 Excel $9 \times 5$ 色塊表。

### [2026-11-16 09:47] 步驟 3：建立六大維度規律探勘引擎與統計證明器
* **新增檔案**：
  * `src/png_decoder.py`：PNG 底層解碼器。
  * `src/pattern_analyzer.py`：實作 `GridPatternAnalyzer`，自動分析：(1) 76 條正交邊同色衝突數；(2) 全域與行列配額上限及 Shannon 熵；(3) 西洋棋盤 `(r+c)%2` 奇偶二分平衡；(4) 右三欄 `Col 2 == Col 4` 鏡像三明治對稱；(5) 水平與垂直方向馬可夫轉移偏好；(6) 列與列之間的漢明距離演化矩陣。
  * `src/hypothesis_prover.py`：實作蒙地卡羅排列檢定、鏡像對稱條件機率、方向異向性卡方檢定與跨題排班同構驗證。
  * `src/main.py` 與 `tests/test_pattern_analysis.py`。

### [2026-11-16 10:00] 步驟 4：消除硬編碼常數 — 將卡方檢定改為由矩陣動態計算
* **自我程式碼審查發現問題**：
  * 初版 `src/hypothesis_prover.py` 在計算方向異向性卡方統計量 $\chi^2$ 時，直接使用前一步統計出的常數 `a, b = 21, 15; c, d = 11, 29`。雖然數值正確，但若未來替換輸入圖檔，寫死的常數將無法動態反映新圖檔的轉移分布。
* **修改動作**：
  * 修改 `src/hypothesis_prover.py` 第 97–125 行：改為直接遍歷 `self.grid` 動態統計水平同群邊數 `a`、水平跨群邊數 `b`、垂直同群邊數 `c`、垂直跨群邊數 `d`，以及水平/垂直紅黃配 `(R, Y)` 比例。
* **實機重跑驗證**：重新執行 `python -m unittest tests.test_pattern_analysis -v` 與 `python -m src.main`，確認動態計算出的 $\chi^2 = 7.3895$、水平 `(R,Y)` 佔比 $25.0\%$、垂直 `(R,Y)` 佔比 $7.5\%$ 與理論完全一致，5 項單元測試全數通過。

### [2026-11-16 10:27] 步驟 5：跨語言效能檢討與雙軌極致最佳化（Python 平坦邊表 + C11 百萬次無除法蒙地卡羅引擎）
* **效能瓶頸檢視**：
  1. 在 Python `hypothesis_prover.py` 中，50,000 次蒙地卡羅洗牌迴圈內部原本使用雙層 `for r ... for c ...` 並重複計算 `r * self.cols + c`，耗時約 `95 ms`。
  2. 若要將蒙地卡羅模擬次數提升 20 倍至 **1,000,000（一百萬）次** 以獲得更嚴格的統計信賴上界，Python 直譯器需耗時近 2 秒。
* **具體修改動作**：
  1. **最佳化 Python `src/hypothesis_prover.py`**：在進入蒙地卡羅迴圈前，預先將全部 76 條正交邊的端點一維索引對 `(u, v)` 編譯為不可變 `edges_tuple`，使 Python 50,000 次模擬耗時降至 `~68 ms`。
  2. **新增 C11 原生極速引擎 `src_native/fast_monte_carlo.c`**：
     * 採用 Marsaglia 的 **`xorshift64*` 無分支 64-bit 偽隨機數產生器**。
     * 初版 C11 引擎在 Fisher-Yates 洗牌中使用 `% (uint64_t)(i + 1)` 取餘數，實測 1,000,000 次耗時 `296.37 ms`（因為 x86_64 的 64-bit `div` 指令需 25~40 個 CPU 週期）。
     * **二次底層指令最佳化（10:29）**：引進 **Daniel Lemire 無除法範圍映射演算法（Fast Range without Division）**，將 `% (i + 1)` 替換為單週期乘法與右移 `((uint64_t)rnd32 * (uint64_t)(i + 1U)) >> 32`！
     * **實測效果**：C11 執行 **1,000,000 次** 蒙地卡羅洗牌與 76 條邊檢查總耗時由 `296.37 ms` 大幅降至 **`109.5 ~ 161.69 ms`（相當於每 50,000 次僅需 `5.5 ~ 8.08 ms`，比未優化 Python 快逾 `12 ~ 17 倍`）**，且 1,000,000 次隨機排列中達成 0 衝突的次數依然為 **`0 次`**！
  3. **修正批次檔特殊字元（10:29）**：將 `scripts/run_all.bat` 中 `echo` 訊息內的 `&` 改為 `and`，消除 Windows `cmd.exe` 將 `&` 誤判為指令連接符的警告。

### [2026-11-16 11:25] 步驟 6：新增「歸納規則生成與下一列 (`Row 9`) 預測演算法」(`predict_next_rows`)
* **修改動作**：於 `src/hypothesis_prover.py` 新增 `predict_next_rows()` 演算法，將歸納出的硬性規則（與 `Row 8` 正交無同色、右三欄 `Col 2 == Col 4` 鏡像三明治對稱、單列至少 3 色）與軟性趨勢（水平與垂直經驗馬可夫轉移機率）結合，自動推演最可能出現的 `Row 9` 前三名候選（Top 1 為 `['B', 'G', 'B', 'R', 'B']`，適合度分數 `1.8861`），並於 `tests/test_pattern_analysis.py` 新增 `test_06_rule_constrained_next_row_prediction` 驗證通過。

### [2026-11-16 11:42] 步驟 7：全專案回歸測試流水線驗證與暫存檔清理
* **執行動作**：透過 `docs_and_tools/run_all_pipeline.bat` 重新執行 C11 `fast_monte_carlo.exe`（1,000,000 次洗牌 0 衝突）、Python `src.main` 與 6 項單元測試，數據同步匯入兩份最終 PDF 報告，並清除所有 `.obj` 與 `__pycache__` 暫存檔。

### [2026-11-16 14:05] 步驟 8：補入 Human-AI Agent 協同分析與工程治理紀錄
* **人類工程師指令**：明確指示專案文件應誠實、透明地呈現使用 AI Agent 協同進行影像逆向工程、多假說規律探勘與 C11 極致最佳化的真實對話歷程。
* **修改動作**：同步更新本開發日誌、全域總日誌與雙份 PDF 報告，完整對照記錄人機互動之決策脈絡。
