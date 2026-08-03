# 變更日誌

本文件記錄 VibeCodingTarot 專案的所有重要變更。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，
版本號遵循 [語意化版本](https://semver.org/lang/zh-TW/)。

## [Unreleased]

### 新增
- 整合 Rider-Waite 古典 78 張塔羅牌 sprite sheet (`static/img/tarot_sprite.jpg`，2600×2040 px，Wikimedia Commons Public Domain 授權)
- 新增 `static/css/card-sprite.css` 卡面樣式表，含 `.tarot-card-image` 背景定位規則、`[data-reversed="true"]` 逆位 transform、`@keyframes tarot-sprite-pulse` 載入動畫、`.tarot-card-fallback` 文字降級版
- 新增 `Divination.renderCard(card, isReversed, container)` 方法，支援 sprite sheet 渲染、座標 clamp 防呆、缺座標 / sprite 404 自動降級為文字版
- 占卜頁 (`/single-card`、`/three-cards`、`/celtic-cross`) 加入 `<link rel="preload" as="image">` sprite sheet 預載提示
- `tools/build_sprite.py`：從 78 張個別牌圖組裝 sprite sheet 的工具腳本
- `tools/download_sources.py`：從 Wikimedia Commons 下載 78 張 Rider-Waite-Smith 牌圖的輔助腳本（含 HTTP 5xx 與 URLError 退避）
- 78 張塔羅牌 `data/tarot_cards.json` 新增 `sprite_x`、`sprite_y` 兩個欄位
- 塔羅卡面從純文字升級為 sprite sheet 背景圖渲染
- 整合 `graphify` 知識圖譜工具：建立 `graphify-out/` 知識圖譜（107 節點、148 邊、11 社群），含 `graph.html` 可互動視覺化與 `GRAPH_REPORT.md` 完整稽核報告
- 安裝 graphify `post-commit` 自動重建 hook（僅重建程式碼差異，無 LLM 呼叫）
- 安裝 graphify `post-checkout` 同步 hook
- 註冊 `graph.json` 專用 merge driver 至 `.gitattributes`
- 新增 `requirements-dev.txt`，宣告 sprite rebuild 工具鏈依賴 `Pillow==10.4.0`

### 變更
- `templates/base.html` 載入 `card-sprite.css`，全站生效
- `templates/single_card.html` / `three_cards.html` / `celtic_cross.html` 改用 `Divination.renderCard()` 取代 inline `.card-image` 字串渲染
- `templates/history.html` 維持 lazy load（不預載 sprite）
- `tests/test_tarot_sprite.py` 新增 30+ 個 sprite 相關測試（座標、CSS、JS、API 向後相容、build script fail-fast、download 退避）
- CHANGELOG 加入繁體中文條目（本 commit）
- `.gitignore` 新增 graphify-out 本機狀態與 workflow temp 排除規則（追蹤核心產物）
- `.gitignore` 新增 `.claude/` 排除（Claude Code 本機設定）
- `tools/download_sources.py`：`_http_get_bytes` 退避機制從僅 429 擴展到 HTTP 5xx (500/502/503/504) 與 `urllib.error.URLError`，仍採 2s→4s→8s→16s 指數退避
- `tools/download_sources.py`：User-Agent 由瀏覽器偽裝 (`Mozilla/5.0 ...`) 改為符合 Wikimedia User-Agent 政策的識別型 UA (`VibeCodingTarot/1.0 (https://github.com/chiisen/VibeCodingTarot; sprite rebuild tool)`)
- `tools/build_sprite.py`：缺圖時由 `print(WARN)` 改為 `sys.exit(1)`，並刪除任何已存在的 stale sprite，避免占卜頁使用半殘 sprite 出現黑色格子
- `tools/build_sprite.py`：docstring 新增 Pillow 依賴與 `requirements-dev.txt` 安裝說明
- 新開發者 clone 後執行 `python tools/build_sprite.py` 前需依 `requirements-dev.txt` 安裝 Pillow，避免 `ModuleNotFoundError`
- `download_sources.py` 對 Wikimedia 5xx 與網路錯誤採退避處理，避免直接 raise
- `build_sprite.py` 缺圖時停止產出 sprite，避免產生半殘 sprite 或測試誤判通過

## [1.0.2] - 2026-08-02

### 修復
- 於 `static/js/divination.js` 補回 `escapeHtml` 轉義防護函數，修復解牌結果畫面拋出 `Divination.escapeHtml is not a function` 錯誤。

## [1.0.1] - 2026-08-02


### 修復
- 註冊 Jinja2 `csrf_token` 全域函數，修復 `single_card` 等頁面 render_template 時拋出 `jinja2.exceptions.UndefinedError: 'csrf_token' is undefined` 錯誤
- 新增 `tests/test_app.py` 單元與迴歸測試，確保所有頁面與 CSRF API 端點運作正常

## [1.0.0] - 2026-08-02

### 新增
- 建立 `static/js/divination.js` 共用占卜模組
- 實作 localStorage 持久化占卜記錄（最多 100 筆）
- 建立 `AGENTS.md` - OpenCode Agent 協調規則
- 建立 `GEMINI.md` - Google Gemini 指令
- 建立 `ARCHITECTURE.md` - 架構文檔
- 建立 `CONTRIBUTING.md` - 貢獻指南
- 建立 `docs/API.md` - API 詳細文檔
- 建立 `docs/DECISIONS.md` - 架構決策紀錄
- 新增 Flask logging 記錄請求與錯誤
- 新增 Flask gzip 壓縮（flask-compress）
- 新增 HTML 頁面快取控制（1 小時）
- 新增字體 preconnect 優化載入速度
- 新增占卜歷史記錄頁面 `/history`
- 導航列新增「歷史記錄」連結
- 新增凱爾特十字占卜功能 `/celtic-cross`
- 新增 `/api/draw-celtic-cross` API 端點
- 新增 56 張 Minor Arcana 牌組資料
- 新增版本號顯示（頁面標題與頁腳）

### 重構
- 抽取共同 JS 邏輯到 `divination.js` 模組
- 簡化 `single_card.html` 和 `three_cards.html` 的腳本
- 使用 `Divination` 模組統一處理 API 呼叫、載入狀態、錯誤處理
- 清理 `main.js` 未使用代碼（escapeHtml, handleError, showSuccessMessage）
- 提取魔法數字為命名常數（CONSTANTS, APP_CONSTANTS）
- 移除假延遲動畫（setTimeout 2000/3000ms）

### 完整功能
- 單張牌占卜功能
- 三張牌（過去-現在-未來）占卜功能
- 凱爾特十字（10 張牌深度占卜）
- 完整 78 張塔羅牌（22 Major Arcana + 56 Minor Arcana）
- RESTful API 端點
- 紫色漸層主題 UI

### 修復
- 修復 SECRET_KEY 硬編碼安全問題
- 修復 XSS 風險
- 新增 CSRF 保護

### 新增
- 建立 `static/js/divination.js` 共用占卜模組
- 實作 localStorage 持久化占卜記錄（最多 100 筆）
- 建立 `AGENTS.md` - OpenCode Agent 協調規則
- 建立 `GEMINI.md` - Google Gemini 指令
- 建立 `ARCHITECTURE.md` - 架構文檔
- 建立 `CONTRIBUTING.md` - 貢獻指南
- 建立 `docs/API.md` - API 詳細文檔
- 建立 `docs/DECISIONS.md` - 架構決策紀錄
- 新增 Flask logging 記錄請求與錯誤
- 新增 Flask gzip 壓縮（flask-compress）
- 新增 HTML 頁面快取控制（1 小時）
- 新增字體 preconnect 優化載入速度
- 新增占卜歷史記錄頁面 `/history`
- 導航列新增「歷史記錄」連結
- 新增凱爾特十字占卜功能 `/celtic-cross`
- 新增 `/api/draw-celtic-cross` API 端點

### 重構
- 抽取共同 JS 邏輯到 `divination.js` 模組
- 簡化 `single_card.html` 和 `three_cards.html` 的腳本
- 使用 `Divination` 模組統一處理 API 呼叫、載入狀態、錯誤處理
- 清理 `main.js` 未使用代碼（escapeHtml, handleError, showSuccessMessage）
- 提取魔法數字為命名常數（CONSTANTS, APP_CONSTANTS）
- 移除假延遲動畫（setTimeout 2000/3000ms）

### 塔羅牌占卜網站初始版本
- 單張牌占卜功能
- 三張牌（過去-現在-未來）占卜功能
- 完整 78 張塔羅牌（22 Major Arcana + 56 Minor Arcana）
- RESTful API 端點
- 紫色漸層主題 UI

### 修復
- 修復 SECRET_KEY 硬編碼安全問題
- 修復 XSS 風險
- 新增 CSRF 保護

### 重構
- 模板繼承架構優化
- JavaScript 共用函數提取

## [0.1.0] - 2026-08-02

### 新增
- 初始版本發佈
- 基本占卜功能實作

---

本專案由 [chiisen] 維護。
