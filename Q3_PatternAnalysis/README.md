# 題目三：色彩矩陣特徵、趨勢與規則之演算法分析歸納系統 (`Q3_PatternAnalysis`)

本目錄為 UC Capital 面試考題 **題目三：分析歸納題** 之完整軟體工程實作專案。

## 目錄結構
```text
Q3_PatternAnalysis/
├── README.md                          # 本說明文件
├── assets/
│   └── slide4_image1.png              # 原始簡報第 4 頁提取之色彩矩陣圖
├── docs/
│   ├── 01_analysis.md                 # 影像底層逆向工程與六大特徵/趨勢/規則詳解
│   ├── 02_architecture.md             # 規律探勘與統計證明管線架構設計
│   ├── 03_implementation_plan.md      # 開發與驗證階段劃分
│   └── 04_dev_log.md                  # 研發探索與跨題彩蛋發現日誌
├── src/
│   ├── __init__.py
│   ├── png_decoder.py                 # 零第三方套件依賴之純 Python PNG 像素解碼器
│   ├── pattern_analyzer.py            # 六大維度規律探勘引擎
│   ├── hypothesis_prover.py           # 蒙地卡羅檢定、卡方檢定與跨題排班同構性證明器
│   └── main.py                        # 分析與證明主程式入口
├── src_native/
│   └── fast_monte_carlo.c             # C11 xorshift64* + Lemire 無除法百萬次蒙地卡羅極速引擎
├── tests/
│   └── test_pattern_analysis.py       # 完整單元測試套件
├── scripts/
│   └── run_all.bat                    # 一鍵編譯 C11 引擎、執行規律分析與單元測試腳本
├── build/
│   └── fast_monte_carlo.exe           # 編譯產出之 C11 百萬次蒙地卡羅執行檔
└── results/
    └── analysis_and_proof_report.md   # 跨語言實測輸出與統計證明數據報告
```

## 快速執行指令
在 `Q3_PatternAnalysis` 目錄下執行：
```powershell
# 1. 執行完整影像解碼、規律分析與證明報表
python -m src.main

# 2. 執行單元測試套件
python -m unittest tests.test_pattern_analysis -v
```

