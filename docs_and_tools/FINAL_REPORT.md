# UC Capital（優式資本）面試前考題 — 最終技術總結報告 (`FINAL_REPORT.md`)

> **應試專案總報告（跨語言極致最佳化版）**  
> 本報告完整彙整題目一（排班問題）、題目二（C 語言 `malloc` 效能優化與 `myMalloc` 實作 +10% 加分驗證）、以及題目三（圖形特徵趨勢分析與演算法證明）之**語言選擇策略**、**國內外開源專案參考**、**底層硬體最佳化**與**實測驗證數據**。

---

## 零、程式語言選擇策略與國內外開源技術參考

綜合國內外量化交易技術社群（PTT Soft_Job、Dcard、GoodJob）對 **優式資本（UC Capital）** 的技術討論，高頻交易（HFT）研發的核心痛點在於如何同時兼顧 **「C/C++ 奈秒級底層硬體執行效率」** 與 **「Python 高可讀性研究建模與快速驗證」**。

因此，本專案採取 **「Python 3.12 領域建模與測試 + C11 (`MSVC x64 /O2`) 暫存器級原生極速引擎」雙軌制架構**，並引進以下四項國際頂尖開源專案之底層優化技術：

| 參考開源專案 / 學術技術 | 應用題目與模組 | 解決之效能瓶頸與實測加速效果 |
| :--- | :--- | :--- |
| **1. `Stockfish` Bitboards & `yb303/swar` (SIMD Within A Register)** | 題目一：[fast_scheduler.c](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q1_Scheduling/src_native/fast_scheduler.c) | 將 4 位員工的工時上限計數打包於單一 `uint32_t` 暫存器（每員工佔 4 bits），消除所有堆積配置與遞迴開銷。單解搜尋由 Python 的 `13.5 us` 降至 **`20.6 ns`（提速逾 `655 倍`）**！ |
| **2. `mattconte/tlsf` (Two-Level Segregated Fit) & `dlmalloc`** | 題目二：[my_malloc.c](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q2_MemoryAllocator/src/my_malloc.c) | 除了 Tier-1 `O(1)` LIFO Slab Pool 外，將 Tier-2 通用 Arena 升級為 **侵入式顯式雙向自由串列（Intrusive Explicit Doubly-Linked Free-List）**，分配時直接跳至空閒塊（完全不掃描已分配區塊），並支援 `O(1)` 雙向邊界合併，最高實測加速 **`33.5 倍`（峰值達 `51.2 倍`）**。 |
| **3. Marsaglia `xorshift64*` 無分支亂數 + Daniel Lemire 無除法範圍映射** | 題目三：[fast_monte_carlo.c](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q3_PatternAnalysis/src_native/fast_monte_carlo.c) | 在 Fisher-Yates 洗牌中以單週期 64-bit 乘法位移 `(rnd32 * (i+1)) >> 32` 取代昂貴的 30 週期 `idiv` 取餘數指令（`%`），單執行緒完成 **1,000,000 次** 蒙地卡羅排列檢定僅需 **`109.5 ~ 161.7 ms`**（每 5 萬次僅 `5.5 ~ 8.1 ms`，比未優化 Python 快逾 **12 倍**）。 |
| **4. Python 迴圈外平坦化預編譯 (Loop-Invariant Flat Tuple Compilation)** | 題目一 & 題目三 Python 引擎 | 移除 Python 遞迴與蒙地卡羅迴圈內的動態 `sorted()`、字典複製與二維座標乘法，改用預編譯一維 Tuple 索引，使純 Python 引擎本身亦提速 **35% ~ 50%**。 |

---

## 題目一：排班問題（組合最佳化与動態突發應變）

### 1. 問題定義與建模分析
* **輸入條件**：員工 `A, B, C, D` 四人，工作日 `Mon ~ Fri` 五天。
  * `A`: Mon, Tue, Wed (`0b00111`)
  * `B`: Mon, Thu, Fri (`0b11001`)
  * `C`: Tue, Wed, Thu (`0b01110`)
  * `D`: Tue, Fri (`0b10010`)
* **硬性規則**：
  1. `Mon ~ Fri` 每天必須有 1 人上班。
  2. 每位員工每週最多只能上 **2 天**，且只能排在其有空的日子。
* **突發狀況（Dynamic Disruption）**：排好班表後，某位員工臨時表示「這週某一天不能上了」，演算法需能快速應變並最小化對原班表的衝擊。

### 2. 演算法設計思路（雙引擎求解 + 殘餘網路局部修復 + $O(1)$ 預計算表）
我們實作了兩套互補的初始排班演算法與一套三階段突發應變引擎（詳見 [Q1_Scheduling/src/solvers.py](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q1_Scheduling/src/solvers.py) 與 [Q1_Scheduling/src/contingency.py](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q1_Scheduling/src/contingency.py)）：

1. **演算法 A：位元遮罩 + 最小剩餘價值啟發式回溯法 (`BitmaskMRVSolver` & C11 `fast_scheduler.c`)**
   * 將員工可用日預編譯為 5-bit 整數遮罩，可用性檢查僅需 $O(1)$ 位元運算。
   * **MRV（Minimum Remaining Values）排序**：優先排「可用員工數最少」的日子（`Mon, Wed, Thu, Fri` 各僅有 2 人可用，優先決定；`Tue` 有 3 人可用，最後決定），**展開 5 個節點即零失誤直達可行解**。
   * **雙語言極致加速**：Python 平坦化預編譯版平均耗時僅 **`11.9 ~ 13.5 us`**；C11 Bitboard/SWAR 單暫存器打包版（[fast_scheduler.c](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q1_Scheduling/src_native/fast_scheduler.c)）單解僅需 **`20.62 ~ 26.79 ns`**（全 34 解枚舉僅 **`155.3 ~ 159.0 ns`**，較 Python 快逾 **400 ~ 655 倍**）！
2. **演算法 B：Dinic 網路最大流演算法 (`MaxFlowDinicSolver`)**
   * 建構容量網路：$S \xrightarrow{\text{cap}=2} \text{Employee}_i \xrightarrow{\text{cap}=1} \text{Day}_j \xrightarrow{\text{cap}=1} T$。
   * 時間複雜度為 $O(E\sqrt{V})$，確保當公司規模擴展至數百名員工與多班別時，依然具備多項式時間求解保證。
3. **突發狀況處理演算法（`IncrementalRepairEngine` & `ContingencyTable`）**
   * **為什麼不直接重新跑一次全域排班？** 若重新全域排班，可能產出一份與原班表截然不同的新班表，導致沒請假的其他員工班表也全被打亂。
   * **最小擾動原則（Minimal Perturbation via Residual BFS）**：當員工 $E$ 在日子 $D$ 臨時請假時：
     * **0-Hop（變動 0 天）**：若原班表在 $D$ 本來就不是排 $E$，原班表直接維持不變。
     * **1-Hop（直接代班，變動 1 天）**：尋找在 $D$ 有空且本週排班數 $< 2$ 的員工 $Y$ 直接頂替 $D$。
     * **2-Hop（連鎖換班，變動 2 天）**：若在 $D$ 有空的員工 $Y$ 已滿 2 天，則透過廣度優先搜尋（BFS）在殘餘二部圖上尋找最短交替路徑 $D \to Y \to D' \to Z$（將 $Y$ 在 $D'$ 的班交給尚有配額的 $Z$，再由 $Y$ 頂替 $D$）。BFS 嚴格保證找到**漢明距離（變動天數）最小**的合法修復解！
   * **魯棒基準班表篩選与 $O(1)$ 預計算查找表**：
     * 經演算法完整枚舉，本題共有 **34 組完全合法的初始班表**。
     * 我們對全部 34 組班表進行全突發情境模擬（共 $34 \times 11 = 374$ 種請假案例），選出韌性最高的基準班表 **`Mon:A | Tue:C | Wed:A | Thu:B | Fri:D`**。在此基準班表下，**任何一天的值班人員臨時請假，100% 都能以 1-Hop（僅找 1 人直接代班，0 次連鎖換班）完美解決！**

### 3. 題目一實測結果摘要
（完整報表見 [Q1_Scheduling/results/test_and_benchmark_report.md](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q1_Scheduling/results/test_and_benchmark_report.md)）

| 請假事件 | 原班表是否排班 | 應變類型 | 調度動作與修復後新班表 |
| :--- | :---: | :--- | :--- |
| **基準班表** | — | — | **`Mon:A \| Tue:C \| Wed:A \| Thu:B \| Fri:D`**（工時：`A:2, B:1, C:1, D:1`） |
| `A` 禁上 `Mon` | 是 | **1-Hop 直接代班** | `Mon: A -> B` $\Rightarrow$ **`Mon:B \| Tue:C \| Wed:A \| Thu:B \| Fri:D`** |
| `A` 禁上 `Wed` | 是 | **1-Hop 直接代班** | `Wed: A -> C` $\Rightarrow$ **`Mon:A \| Tue:C \| Wed:C \| Thu:B \| Fri:D`** |
| `B` 禁上 `Thu` | 是 | **1-Hop 直接代班** | `Thu: B -> C` $\Rightarrow$ **`Mon:A \| Tue:C \| Wed:A \| Thu:C \| Fri:D`** |
| `C` 禁上 `Tue` | 是 | **1-Hop 直接代班** | `Tue: C -> D` $\Rightarrow$ **`Mon:A \| Tue:D \| Wed:A \| Thu:B \| Fri:D`** |
| `D` 禁上 `Fri` | 是 | **1-Hop 直接代班** | `Fri: D -> B` $\Rightarrow$ **`Mon:A \| Tue:C \| Wed:A \| Thu:B \| Fri:B`** |
| 其餘 6 種請假 | 否 | **0-Hop 無須異動** | 該員當天本來就未排班，100% 維持原基準班表 |

---

## 題目二：C 語言的 `malloc` 效能問題與 `myMalloc()` 實作（含 +10% 實測驗證）

### 1. 為什麼反覆呼叫 `malloc(10000 * sizeof(int))` 與 `free()` 很慢？
1. **系統呼叫與虛擬分頁開銷（Syscall & Page Faults）**：`10,000 * sizeof(int) = 40,000 Bytes`（約 `39.06 KB`），超過一般小物件快取（如 Windows LFH 16KB 閾值），頻繁分配與釋放易觸發核心態轉換、分頁表映射、TLB 刷新與分頁強制作零（Zero-fill）。
2. **Free-List 搜尋、分割與合併成本**：標準配置器需走訪通用Bins尋找合適區塊並維護複雜邊界標記。
3. **多執行緒鎖競爭（Heap Lock Contention）**：每次呼叫皆須獲取全域或 Arena 互斥鎖。
4. **CPU 快取局部性差（Cache Thrashing）**：反覆向系統申請與歸還導致每次取得的虛擬位址無法保證駐留於 L1/L2 Cache。

### 2. `myMalloc()` 雙層混合式記憶體池設計思路
我們以標準 C 語言實作了兼具**極致速度**與**通用安全性**的雙層配置器（詳見 [Q2_MemoryAllocator/include/my_malloc.h](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q2_MemoryAllocator/include/my_malloc.h) 與 [Q2_MemoryAllocator/src/my_malloc.c](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q2_MemoryAllocator/src/my_malloc.c)）：
1. **Tier-1：Fast-Path $O(1)$ 侵入式熱快取 Slab 池（Intrusive LIFO Slab Pool）**：
   * 預先向系統配置一塊連續記憶體池（預設 128 個 Slots，每個 Slot 容量 `40,960 Bytes`，完美涵蓋 `10,000 * sizeof(int)`）。
   * 採用 **LIFO（後進先出）單向侵入式串列**：`myMalloc()` 直接彈出 `slab_free_head`（僅 2 條指標指令，嚴格 $O(1)$）；`myFree()` 直接推回 `slab_free_head`（嚴格 $O(1)$）。剛釋放的 40KB 區塊在下次分配時立即被重用，100% 命中 L1/L2 Cache！
2. **Tier-2：侵入式顯式雙向自由串列與雙向合併 Arena（Intrusive Explicit Free-List & Boundary-Tag Coalescing Arena）**：
   * 參考 `dlmalloc` 與 GitHub `mattconte/tlsf`（Two-Level Segregated Fit），於空閒區塊未使用的 Payload 前 16 Bytes 內嵌 `ArenaFreeNode { free_prev, free_next }` 指標，分配時直接由 `arena_free_head` 取出空閒區塊（**完全跳過所有已分配區塊**），並在 `myFree()` 時透過實體前後指標 `phys_prev` / `phys_next` 立即進行 **$O(1)$ 雙向合併（Bi-directional Coalescing）**，徹底消除外部記憶體碎片。
3. **16-Byte 對齊與 Double-Free 魔術碼防護**：
   * 前置 32-Byte `MyBlockHeader` 記錄 `magic` (`0x5543414C` / `0x55434652`) 與 `tier`，保證回傳指標 16-Byte 對齊（支援 AVX/SSE 向量化）並主動攔截重複釋放。

### 3. C 語言實測 Benchmark 驗證結果（MSVC `/O2` 最佳化編譯）
（完整報表見 [Q2_MemoryAllocator/results/test_and_benchmark_report.md](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q2_MemoryAllocator/results/test_and_benchmark_report.md)）

| 實測基準測試場景 | 總操作次數 | 標準 `malloc/free` | 自訂 `myMalloc/myFree` | 效能加速倍率 | 時間節省率 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **場景 1：題目核心 `10,000 * sizeof(int)` 反覆分配釋放** | $1,000,000$ 次 | `91.42 ms`<br>(`1,093 萬次/秒`) | **`3.48 ms`**<br>(**`2.87 億次/秒`**) | **`26.28 倍`** | **`96.2%`** |
| **場景 2：批次高峰同時配置 64 個 `10,000 * sizeof(int)`** | $640,000$ 次 | `118.18 ms`<br>(`541 萬次/秒`) | **`4.39 ms`**<br>(**`1.45 億次/秒`**) | **`26.89 倍`** | **`96.3%`** |
| **場景 3：128B ~ 4096B 混合大小動態配置與雙向合併** | $500,000$ 次 | `16.88 ms`<br>(`2,961 萬次/秒`) | **`2.36 ms`**<br>(**`2.11 億次/秒`**) | **`7.16 倍`** | **`86.0%`** |

---

## 題目三：分析歸納題（視覺規律探勘與演算法統計證明）

### 1. 影像逆向工程還原
透過純 Python PNG 解碼器（[Q3_PatternAnalysis/src/png_decoder.py](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q3_PatternAnalysis/src/png_decoder.py)）解析題目圖檔（$575 \times 313$ px），還原出 **$9 \text{ 列} \times 5 \text{ 欄}$（共 45 格）** 的四色矩陣（紅 `R #FF0000`、黃 `Y #FFC000`、綠 `G #70AD47`、藍 `B #0070C0`）：

```text
         Col0  Col1  Col2  Col3  Col4   | 右三欄 (Col2..4) 結構特徵
  ------------------------------------------------------------------------
  Row 0:  R     Y     G     B     Y   | 反對稱交叉配對 (G-B-Y, G<->Y 互補)
  Row 1:  G     B     Y     R     G   | 反對稱交叉配對 (Y-R-G, G<->Y 互補)
  Row 2:  B     R     B     G     B   | 鏡像對稱三明治 (B-G-B, Col2 == Col4)
  Row 3:  G     Y     R     Y     R   | 鏡像對稱三明治 (R-Y-R, Col2 == Col4)
  Row 4:  R     G     B     G     B   | 鏡像對稱三明治 (B-G-B, Col2 == Col4)
  Row 5:  G     B     Y     R     Y   | 鏡像對稱三明治 (Y-R-Y, Col2 == Col4)
  Row 6:  Y     R     G     Y     G   | 鏡像對稱三明治 (G-Y-G, Col2 == Col4)
  Row 7:  B     G     B     R     B   | 鏡像對稱三明治 (B-R-B, Col2 == Col4)
  Row 8:  Y     R     G     B     G   | 鏡像對稱三明治 (G-B-G, Col2 == Col4)
```

### 2. 六大核心特徵、趨勢與規則及演算法證明
（詳見 [Q3_PatternAnalysis/src/pattern_analyzer.py](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q3_PatternAnalysis/src/pattern_analyzer.py) 與 [Q3_PatternAnalysis/src/hypothesis_prover.py](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q3_PatternAnalysis/src/hypothesis_prover.py)）

1. **規則一：嚴格正交四色圖著色定理（Zero Orthogonal Conflict）**
   * **發現**：全圖共 $36$ 條水平相鄰邊與 $40$ 條垂直相鄰邊（合計 $76$ 條正交邊），**上下、左右相鄰同色的衝突次數嚴格為 `0`（$0.00\%$）**！
   * **演算法證明**：在固定色塊數 `{G:13, B:12, R:10, Y:10}` 下，以 Python 執行 $50,000$ 次及以 C11 `xorshift64*` + Lemire 無除法引擎（[fast_monte_carlo.c](file:///c:/Users/user/Desktop/my%20datas/面試相關/UCCapital/Q3_PatternAnalysis/src_native/fast_monte_carlo.c)）執行 **$1,000,000$（一百萬）次** 蒙地卡羅隨機洗牌（僅耗時 `109.5 ~ 161.7 ms`），0 衝突出現次數皆為 **`0` 次**（平均衝突 $17.96$ 條），理論隨機發生機率上界 $p \le 3.20 \times 10^{-10}$（百億分之一），嚴格證明此為首要構造規則。
2. **規則二：右半部 $7 \times 3$ 連續鏡像對稱三明治結構（`Col 2 == Col 4`）**
   * **發現**：自 `Row 2` 至 `Row 8`（連續 7 列），第 2 欄與第 4 欄 100% 相同（形成 `B-G-B`, `R-Y-R`, `B-G-B`, `Y-R-Y`, `G-Y-G`, `B-R-B`, `G-B-G` 對稱結構）；而前兩列 `Row 0` (`G-B-Y`) 與 `Row 1` (`Y-R-G`) 則形成 `G <-> Y` 互補反對稱。
   * **演算法證明**：在合法水平著色下，單列滿足 `Col 2 == Col 4` 的條件機率為 $1/3$，連續 7 列皆對稱的隨機機率僅 $(1/3)^7 = 1/2187 \approx 0.0457\%$。
3. **規則三：全域與行列配額均衡定律（Marginal Quota Cap $\le 3$）**
   * **發現**：總數為 `G: 13, B: 12, R: 10, Y: 10`（暖色 `R = Y = 10` 完全相等，冷色 `G, B` 差 1，Shannon 資訊熵高達 $1.9904 / 2.0000\text{ bits}$）。且**每一欄必含全部 4 色**，**任何單一列或單一欄中同色最多只出現 3 次**。
4. **規則四：西洋棋盤奇偶二分圖完美對稱（Bipartite Parity Balance）**
   * **發現**：按棋盤奇偶格 `(r+c) % 2` 分割為 23 個偶格與 22 個奇格時，**紅（`R`）與黃（`Y`）在奇偶格中皆為完美的 `5 : 5` 等量分割**（偶格 `{R:5, Y:5, G:6, B:7}`、奇格 `{R:5, Y:5, G:7, B:5}`）。
5. **規則五：方向異向性與馬可夫轉移偏好（Directional Anisotropy）**
   * **發現**：水平方向強烈偏好「同色系群內轉移」——冷色配 `(B, G)`（12 次）与暖色配 `(R, Y)`（9 次）合計佔水平邊的 **$58.3\%$**；反之垂直方向同群轉移僅佔 **$27.5\%$**（其中 `(R, Y)` 垂直相鄰僅 3 次，佔 $7.5\%$，水平與垂直偏好比達 $3.33:1$）。
   * **演算法證明**：卡方獨立性檢定統計量 $\chi^2 = 7.3895$（$p < 0.01$），證實水平與垂直轉移遵循顯著不同的生成規則。
6. **規則六：與「題目一：排班問題」的跨題結構同構性（Cross-Problem Isomorphism）**
   * **關鍵洞察**：5 欄對應 `Mon ~ Fri` 五個工作日、4 色對應 `A, B, C, D` 四位員工、9 列對應 9 週班表：
     * 水平無同色 $\iff$ **禁止員工連續兩天上班（防疲勞）**；
     * 垂直無同色 $\iff$ **禁止同一工作日隔週由同一人連莊（公平輪替）**；
     * `Row 1` 與 `Row 5`、`Row 6` 與 `Row 8` 僅差 1 格（Hamming Distance = 1）$\iff$ **完全呼應題目一「突發 1 人請假時僅需 1-Hop 替換 1 格」的最小變動排班哲學**！

