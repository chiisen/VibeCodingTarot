# 塔羅牌 Sprite Sheet 視覺驗證 Checklist

> 此檔案用於 Task 11 手動視覺驗證,需要瀏覽器互動執行。
> PR: https://github.com/chiisen/VibeCodingTarot/pull/26

## 環境準備

```powershell
Set-Location 'D:\github\chiisen\VibeCodingTarot\.worktrees\feat-tarot-sprite-redesign'
python app.py
```

瀏覽器開啟 `http://localhost:5000`

---

## 驗證項目

### A. 首頁 `/`

- [ ] 頁面正常渲染
- [ ] 開 DevTools Network,確認 **tarot_sprite.jpg 不在初始載入** (lazy load 生效)
- [ ] 確認 .worktrees/ 工作目錄正常運作

### B. 單張牌 `/single-card`

- [ ] **抽 22 次覆蓋 22 Major Arcana**
  - 每次抽完截圖,確認 sprite 圖像對應正確(對照 Wikimedia Rider-Waite 原圖)
  - 確認抽到 The Fool (index 0) 顯示正確
  - 確認抽到 The World (index 21) 顯示正確
- [ ] 確認預載生效:DevTools Network 看到 `<link rel="preload" as="image">` 標籤
- [ ] 確認逆位 5+ 次:`rotate(180deg)` 視覺正確、無裁切溢出
- [ ] 確認 hover 翻牌動畫流暢(若既有 CSS 有定義)

### C. 三張牌 `/three-cards`

- [ ] **抽 20 次以上**, 覆蓋 56 Minor Arcana 各 suit:
  - Wands 14 張(權杖)
  - Cups 14 張(聖杯)
  - Swords 14 張(寶劍)
  - Pentacles 14 張(錢幣)
- [ ] 三張牌並排顯示,各自 sprite 正確
- [ ] 確認 index 22 (Wands 1) 在 sprite sheet 第 1 列最後 4 格,顯示正確
- [ ] 確認 index 77 (Pentacles 14/King) 在 sprite sheet 第 6 列最後 1 格,顯示正確

### D. 凱爾特十字 `/celtic-cross`

- [ ] **抽 5 次以上**, 確認 10 張牌各自 sprite 正確
- [ ] 10 張牌版面配置未壞

### E. 歷史記錄 `/history`

- [ ] 確認**沒有** sprite preload (DevTools Network 看不到 preload)
- [ ] 點擊任一既有記錄還原, sprite 圖像正確顯示

### F. 行動裝置測試

DevTools 切到:

- [ ] iPhone SE (375px)
- [ ] iPad (768px)
- [ ] 確認 sprite 縮放清晰
- [ ] 確認卡面不超出 viewport

### G. 網路節流測試

DevTools Network throttle:

- [ ] Slow 3G:首次抽牌時 sprite 載入期間,pulse 動畫連貫,無白屏閃爍

### H. Fallback 測試 (sprite 缺失)

```powershell
# 暫時改名 sprite JPG
Move-Item static/img/tarot_sprite.jpg static/img/tarot_sprite.jpg.bak

# 重啟 server
python app.py
```

- [ ] 開 `/single-card` 抽牌, 應顯示 `.tarot-card-fallback` 文字版卡面
- [ ] 文字版含牌名與花色,卡框仍存在
- [ ] DevTools Console 看到 `[tarot-sprite] 載入失敗, fallback 至文字版` 警告

```powershell
# 還原 sprite JPG
Move-Item static/img/tarot_sprite.jpg.bak static/img/tarot_sprite.jpg
```

### I. 截圖存檔

```powershell
New-Item -ItemType Directory -Force -Path tests/visual_baseline | Out-Null
```

將以下截圖存至 `tests/visual_baseline/`:

- [ ] 22 Major 各一張 → `major_00_fool.jpg` ~ `major_21_world.jpg`
- [ ] 56 Minor 各一張 → `minor_22_wands_ace.jpg` ~ `minor_77_pentacles_king.jpg`
- [ ] 逆位範例 3 張 → `reversed_example_1.jpg`, `reversed_example_2.jpg`, `reversed_example_3.jpg`
- [ ] Fallback 文字版範例 → `fallback_text_version.jpg`
- [ ] 首頁(無 sprite 載入)→ `homepage_no_sprite_load.png`
- [ ] 行動裝置 375px → `mobile_375px.png`
- [ ] 行動裝置 768px → `tablet_768px.png`

### J. Accessibility 簡測

- [ ] Tab 鍵可聚焦到抽牌按鈕
- [ ] 螢幕閱讀器(NVDA/VoiceOver)可讀到卡名

---

## 已知問題(若發現,記錄於此)

(填寫空間)

---

## 驗證結果

- [ ] 全部通過,可合併 PR
- [ ] 發現 issue,記錄後請作者修補

驗證者簽名:_____________ 日期:_____________

---

## 合併後清理

合併 PR #26 後,記得:

1. 切回 main:`git checkout main`
2. 拉取最新:`git pull`
3. 移除 worktree:`git worktree remove .worktrees/feat-tarot-sprite-redesign`
4. 刪除分支:`git branch -d feat/tarot-sprite-redesign`
5. 更新本機 .gitignore 不需修改(.worktrees/ 持續忽略)