# 任務主檔：`TASK-03` 色彩矩陣特徵、趨勢與規則之演算法分析歸納 (`task.md`)

> **所屬層級**：Task 層 (`/tasks/TASK-03-Pattern-Analysis/task.md`)  
> **向下追溯來源**：[`/strategy/product_vision.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/strategy/product_vision.md) — 題目三核心目標  
> **實作演進報告**：[`implementation-process.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/tasks/TASK-03-Pattern-Analysis/implementation-process.md)  
> **關聯執行日誌**：[`/worklogs/2026-11-16-TASK-03.md`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/worklogs/2026-11-16-TASK-03.md)  
> **對應程式碼目錄**：[`/Q3_PatternAnalysis/`](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q3_PatternAnalysis/)

---

## 一、任務背景與驗收條件

針對考題簡報第 4 頁「題目三：分析歸納題」：
1. 解析內嵌之無數值色塊圖 (`slide4_image1.png`)，找出其特徵、趨勢與規則。
2. 利用演算法與程式分析，嚴格證明所提出的想法與有趣的發現。

---

## 二、任務進度追蹤 (Task Progress — 由 Worklog 向上同步更新)

- [x] **Subtask 3.1**：自 PPTX 壓縮包提取 `ppt/media/image1.png`，並在無第三方影像套件 (`PIL`) 環境下，以純標準庫 `struct` + `zlib` 手寫符合 RFC 2083 規範之 Paeth PNG 解碼器 (`src/png_decoder.py`)
- [x] **Subtask 3.2**：由 AI Agent 執行多假說統計探勘腳本，還原 $9 \times 5$ Excel 四色矩陣並歸納出六大核心規律 (`src/pattern_analyzer.py`)
- [x] **Subtask 3.3**：實作蒙地卡羅排列檢定、右三欄鏡像對稱條件機率、方向異向性卡方檢定與跨題排班同構證明器 (`src/hypothesis_prover.py`)
- [x] **Subtask 3.4**：【程式碼審查修正】消除卡方檢定中之硬編碼常數，改為直接遍歷 `self.grid` 動態統計 2×2 列聯表
- [x] **Subtask 3.5**：【計畫外跨語言極致最佳化】預編譯 Python 76 條邊一維索引 Tuple，並增建 C11 `xorshift64*` + Daniel Lemire 無除法百萬次蒙地卡羅引擎 (`src_native/fast_monte_carlo.c`)
- [x] **Subtask 3.6**：【計畫外擴展功能】新增基於歸納規則與馬可夫轉移機率之下一列 (`Row 9`) 自動預測生成器 (`predict_next_rows` 與 `test_06`)

---

## 三、最終實測驗收指標

* **影像逆向工程**：100% 精確還原 `575x313` 畫布為 $9 \times 5$ 四色矩陣（`#FF0000` 紅、`#FFC000` 黃、`#70AD47` 綠、`#0070C0` 藍）
* **規則一（正交零衝突）**：全圖 76 條正交邊同色衝突數 = **`0`**；C11 無除法引擎執行 **1,000,000 次** 隨機洗牌耗時僅 **`105.2 ~ 174.3 ms`**，達成 0 衝突次數為 **`0 次`**（$p < 3 \times 10^{-6}$）
* **規則二（右三欄鏡像對稱）**：`Row 2` 至 `Row 8` 連續 7 列 100% 滿足 `Col 2 == Col 4`（隨機發生機率 $(1/3)^7 \approx 0.000457$）
* **規則五（方向異向性卡方檢定）**：動態計算 $\chi^2 = 7.3895 > 6.635$（$p < 0.01$）
* **規則六（跨題同構與 `Row 9` 預測）**：自動推演最可能之下一列 `Row 9` Top 1 為 **`['R', 'G', 'B', 'G', 'B']`**（適合度 `1.9611`）
* **自動化單元測試**：`6 / 6 PASS` (`100%`)
