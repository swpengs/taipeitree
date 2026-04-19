# 北市樹木地圖 (Taipei Street Tree Map) 專案指南

這個專案是一個用於展示台北市行道樹 Open Data 的互動式網頁工具。它使用 Leaflet.js 在地圖上標記超過 9 萬棵樹木的位置與資訊。

## 專案概覽

- **主要目標**：提供一個高效、流暢的界面，讓使用者搜尋、過濾並查看台北市行道樹的詳細資訊。
- **核心技術**：
    - **前端**：HTML5, CSS3 (Vanilla), JavaScript (Vanilla)。
    - **地圖庫**：Leaflet.js 1.9.4。
    - **資料來源**：台北市行道樹 Open Data (JSON/CSV)。
- **專案結構**：
    - `北市樹木地圖.html`：專案的主入口點，包含所有的 UI 邏輯與地圖渲染邏輯。
    - `data/tree-data.js`：核心資料檔，將數萬筆樹木資料以壓縮的字串與索引形式存儲，以優化瀏覽器載入速度。
    - `uploads/TaipeiTree.csv`：原始資料來源，包含 TreeID, 座標 (TWD97), 樹種, 調查日期等。

## 開發與運行

### 運行專案
由於這是一個靜態網頁專案，你可以直接在瀏覽器中開啟 `北市樹木地圖.html`。
建議使用本地伺服器（如 VS Code 的 Live Server 或 `npx serve`）以獲得最佳體驗。

### 資料更新流程
目前資料存放在 `data/tree-data.js`。你可以使用自動化腳本進行更新：
1. 執行 `python3 scripts/update_data.py`。
2. 此腳本會自動：
    - 備份目前的 `uploads/TaipeiTree.csv`（檔名附加時間戳記）。
    - 從資料源下載最新的 CSV 檔案。
    - 將 CSV 轉換為 `tree-data.js` 格式，並精確處理座標與數值。
    - *欄位對照*：`[lat, lon, specIdx, distIdx, regionIdx, remarkIdx, diameter, height, id, date]`

## 開發慣例

### 代碼風格
- **Vanilla JS**：保持不依賴現代框架（如 React/Vue）的設計，以確保輕量與速度。
- **效能優化**：由於點位高達 9 萬個，地圖繪製採用了自定義的 Canvas Layer (`TreeLayer`)，而非標準的 Leaflet Marker。
- **命名規範**：
    - 變數與函數：小駝峰式命名（如 `applyFilter`, `speciesSorted`）。
    - HTML 元素 ID：小駝峰式命名（如 `searchInput`, `speciesList`）。

### 功能模組
- **資料解析**：在 HTML 內部的 `<script>` 區塊開頭，處理 `TREE_ROWS_RAW` 的分割與型別轉換。
- **地圖渲染**：使用 `L.Layer.extend` 自定義 Canvas 渲染邏輯，根據縮放層級（Zoom Level）動態調整點的大小與描邊。
- **過濾機制**：使用 `Uint8Array` 作為遮罩（Mask），實現高效的資料篩選而不需重新建立物件。

## 待辦事項 (TODO)
- [ ] 實作自動化資料轉換工具（CSV to JS）。
- [ ] 增加樹木歷史資料對比。
- [ ] 優化行動裝置上的觸控操作。
- [ ] 增加更多行政區或路段的統計圖表。
