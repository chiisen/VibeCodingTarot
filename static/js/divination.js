// 占卜共用功能模組

const Divination = {
    // CSRF Token (從模板注入)
    csrfToken: null,

    // localStorage 鍵名
    STORAGE_KEY: 'vibe_tarot_readings',

    // HTML 轉義防護
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    // 渲染單張塔羅牌到容器元素
    renderCard(card, isReversed, container) {
        if (!card || !container) {
            console.warn('[Divination.renderCard] 缺少 card 或 container');
            return;
        }

        const spriteX = (card.sprite_x === undefined) ? 0
            : Math.min(Math.max(card.sprite_x, 0), 12);
        const spriteY = (card.sprite_y === undefined) ? 0
            : Math.min(Math.max(card.sprite_y, 0), 5);

        if (card.sprite_x !== undefined && (card.sprite_x < 0 || card.sprite_x > 12)) {
            console.warn('[tarot-sprite] 座標越界', card.id, card.sprite_x, card.sprite_y);
        }
        if (card.sprite_y !== undefined && (card.sprite_y < 0 || card.sprite_y > 5)) {
            console.warn('[tarot-sprite] 座標越界', card.id, card.sprite_x, card.sprite_y);
        }

        const fallback = () => {
            container.innerHTML = `
                <div class="tarot-card-fallback">
                    <div class="fallback-name">${this.escapeHtml(card.name)}</div>
                    <div class="fallback-suit">${this.escapeHtml(card.suit || '')}</div>
                </div>
            `;
        };

        if (card.sprite_x === undefined || card.sprite_y === undefined) {
            fallback();
            return;
        }

        const posX = -spriteX * 200;
        const posY = -spriteY * 340;
        container.innerHTML = `
            <div class="tarot-card-image loading"></div>
        `;
        const imgEl = container.querySelector('.tarot-card-image');
        imgEl.setAttribute('data-card', this.escapeHtml(card.id));
        imgEl.setAttribute('data-reversed', isReversed ? 'true' : 'false');
        imgEl.style.setProperty('--sprite-pos', `${posX}px ${posY}px`);

        const bgImg = new Image();
        bgImg.onload = () => imgEl.classList.remove('loading');
        bgImg.onerror = () => {
            console.warn('[tarot-sprite] 載入失敗,fallback 至文字版', card.id);
            fallback();
        };
        bgImg.src = '/static/img/tarot_sprite.jpg';
    },

    // 抽牌動畫版:先顯示牌背,延遲 60ms 觸發翻牌,翻完顯示牌面 sprite
    renderCardWithFlip(card, isReversed, container) {
        if (!card || !container) {
            console.warn('[Divination.renderCardWithFlip] 缺少 card 或 container');
            return;
        }

        container.innerHTML = `
            <div class="card-flip-container">
                <div class="card-flip-inner">
                    <div class="card-face card-face-back">
                        <img src="/static/img/tarot-card-back.svg" alt="塔羅牌背面" draggable="false">
                    </div>
                    <div class="card-face card-face-front"></div>
                </div>
            </div>
        `;

        const inner = container.querySelector('.card-flip-inner');
        const frontFace = container.querySelector('.card-face-front');

        this.renderCard(card, isReversed, frontFace);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                inner.classList.add('flipped');
            });
        });
    },

    // 初始化
    init(csrfToken) {

        this.csrfToken = csrfToken;
        this.setupInputEffects();
    },

    // 設置問題輸入框效果
    setupInputEffects() {
        const questionInput = document.getElementById('questionInput');
        if (questionInput) {
            questionInput.addEventListener('focus', function() {
                this.style.borderColor = '#6c5ce7';
                this.style.boxShadow = '0 0 0 3px rgba(108, 92, 231, 0.1)';
            });
            
            questionInput.addEventListener('blur', function() {
                this.style.borderColor = '#e0e0e0';
                this.style.boxShadow = 'none';
            });
        }
    },

    // 抽牌 API 呼叫
    async drawCards(type, question) {
        const endpoints = {
            'single': '/api/draw-single',
            'three': '/api/draw-three',
            'celtic-cross': '/api/draw-celtic-cross'
        };
        const endpoint = endpoints[type] || '/api/draw-single';
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': this.csrfToken
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message);
        }
        return data.data;
    },

    // 顯示載入狀態
    showLoading(show = true) {
        const loadingSection = document.getElementById('loadingSection');
        const resultSection = document.getElementById('resultSection');
        const drawButton = document.getElementById('drawButton');

        if (loadingSection) loadingSection.style.display = show ? 'block' : 'none';
        if (resultSection) resultSection.style.display = show ? 'none' : 'block';
        if (drawButton) drawButton.disabled = show;
    },

    // 顯示結果
    showResult(show = true) {
        const loadingSection = document.getElementById('loadingSection');
        const resultSection = document.getElementById('resultSection');
        const drawButton = document.getElementById('drawButton');

        if (loadingSection) loadingSection.style.display = 'none';
        if (resultSection) resultSection.style.display = show ? 'block' : 'none';
        if (drawButton) drawButton.disabled = false;
    },

    // 錯誤處理
    handleError(error, userMessage = '操作失敗，請稍後再試') {
        console.error('錯誤:', error);
        this.showLoading(false);
        this.showError(userMessage);
    },

    // 顯示錯誤訊息
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            font-family: 'Noto Sans TC', sans-serif;
        `;
        errorDiv.textContent = message;

        document.body.appendChild(errorDiv);

        const displayTime = window.CONSTANTS?.MESSAGE_DISPLAY_TIME || 3000;
        const animTime = window.CONSTANTS?.MESSAGE_ANIMATION_TIME || 300;

        setTimeout(() => {
            errorDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, animTime);
        }, displayTime);
    },

    // 顯示成功訊息
    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #51cf66;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            font-family: 'Noto Sans TC', sans-serif;
        `;
        successDiv.textContent = message;

        document.body.appendChild(successDiv);

        const displayTime = window.CONSTANTS?.MESSAGE_DISPLAY_TIME || 3000;
        const animTime = window.CONSTANTS?.MESSAGE_ANIMATION_TIME || 300;

        setTimeout(() => {
            successDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (successDiv.parentNode) {
                    successDiv.parentNode.removeChild(successDiv);
                }
            }, animTime);
        }, displayTime);
    },

    // ========== 占卜記錄持久化 ==========

    // 取得所有記錄
    getReadings() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('讀取占卜記錄失敗:', e);
            return [];
        }
    },

    // 儲存占卜記錄
    saveReading(reading) {
        try {
            const readings = this.getReadings();
            const newReading = {
                id: this.generateId(),
                timestamp: new Date().toISOString(),
                ...reading
            };
            readings.unshift(newReading); // 新記錄加在最前面
            
            // 最多保留 N 筆記錄
            const maxReadings = window.CONSTANTS?.MAX_READINGS || 100;
            if (readings.length > maxReadings) {
                readings.pop();
            }
            
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(readings));
            return newReading;
        } catch (e) {
            console.error('儲存占卜記錄失敗:', e);
            return null;
        }
    },

    // 刪除占卜記錄
    deleteReading(id) {
        try {
            const readings = this.getReadings();
            const filtered = readings.filter(r => r.id !== id);
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered));
            return true;
        } catch (e) {
            console.error('刪除占卜記錄失敗:', e);
            return false;
        }
    },

    // 新增/更新占卜記錄的個人筆記
    updateReadingNote(id, note) {
        try {
            const readings = this.getReadings();
            const reading = readings.find(r => r.id === id);
            if (!reading) return false;
            reading.note = note;
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(readings));
            return true;
        } catch (e) {
            console.error('更新占卜記錄筆記失敗:', e);
            return false;
        }
    },

    // 清空所有記錄
    clearReadings() {
        try {
            localStorage.removeItem(this.STORAGE_KEY);
            return true;
        } catch (e) {
            console.error('清空占卜記錄失敗:', e);
            return false;
        }
    },

    // 取得最近 N 筆記錄
    getRecentReadings(count = 10) {
        return this.getReadings().slice(0, count);
    },

    // 生成唯一 ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // 格式化時間
    formatTime(isoString) {
        const date = new Date(isoString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}/${month}/${day} ${hours}:${minutes}`;
    }
};

// 添加 CSS 動畫
const divinationStyle = document.createElement('style');
divinationStyle.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .error-message, .success-message {
        font-family: 'Noto Sans TC', sans-serif;
        font-weight: 500;
    }
`;
document.head.appendChild(divinationStyle);

// 導出
window.Divination = Divination;
