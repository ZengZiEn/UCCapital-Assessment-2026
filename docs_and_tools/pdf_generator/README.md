# 自動化圖文 PDF 報告建置系統 (`report_pdf/`)

本目錄負責將三題的即時執行結果、統計數據與架構圖自動渲染為高品質 A4 向量圖表 PDF 報告（輸出至根目錄 `../UCCapital_面試考題_最終說明報告.pdf`）。

## 目錄結構
```text
report_pdf/
├── README.md                  # 本說明文件
├── build_report.py            # 純 Python 零依賴 SVG 圖表與 PDF 自動化產生器
└── build/
    ├── report_data.json       # 建置時即時執行三題程式所收集之完整實測數據
    ├── report.html            # 內嵌 17 張 SVG 向量圖表與 A4 印刷樣式之 HTML 報告
    └── report.pdf             # 建置輸出之 PDF 副本
```

## 執行方式
於專案根目錄 `UCCapital/` 執行：
```powershell
python report_pdf\build_report.py
```

