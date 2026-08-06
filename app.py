# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, make_response
from flask_compress import Compress
import json
import random
import logging
from datetime import datetime
import os
import secrets

app = Flask(__name__)

# 配置：SECRET_KEY 從環境變數讀取，未設定時自動生成隨機密鑰
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['JSON_AS_ASCII'] = False  # 支援中文JSON

# 啟用 gzip 壓縮
app.config['COMPRESS_MIMETYPES'] = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript',
    'text/javascript'
]
app.config['COMPRESS_MIN_SIZE'] = 500
Compress(app)

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 應用常數
APP_CONSTANTS = {
    'THREE_CARDS_COUNT': 3,
    'CELTIC_CROSS_COUNT': 10,
    'DEFAULT_PORT': 5000,
    'MAX_READINGS': 100,
    'STATIC_CACHE_MAX_AGE': 31536000,  # 1 年
    'HTML_CACHE_MAX_AGE': 3600  # 1 小時
}

# 凱爾特十字牌陣位置定義
CELTIC_CROSS_POSITIONS = [
    {'index': 0, 'name': '現狀', 'name_en': 'Present', 'description': '目前的情況和核心問題'},
    {'index': 1, 'name': '挑戰', 'name_en': 'Challenge', 'description': '面臨的障礙和對立面'},
    {'index': 2, 'name': '根源', 'name_en': 'Root', 'description': '事件的根源和深層原因'},
    {'index': 3, 'name': '過去', 'name_en': 'Past', 'description': '近期的過去和已發生的事'},
    {'index': 4, 'name': '可能', 'name_en': 'Possible', 'description': '可能的結果和發展方向'},
    {'index': 5, 'name': '未來', 'name_en': 'Future', 'description': '近期的未來發展'},
    {'index': 6, 'name': '自我', 'name_en': 'Self', 'description': '對此事的態度和看法'},
    {'index': 7, 'name': '環境', 'name_en': 'Environment', 'description': '外在環境和他人影響'},
    {'index': 8, 'name': '希望', 'name_en': 'Hope', 'description': '內心的期望或恐懼'},
    {'index': 9, 'name': '結果', 'name_en': 'Outcome', 'description': '最終的結果和結論'}
]


# 讀取版本號
def get_version():
    """讀取版本號"""
    try:
        with open('VERSION', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return '0.0.0'

APP_VERSION = get_version()


def generate_csrf_token():
    """生成 CSRF token 並存入 session"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


# 註冊 Jinja2 全域函數，模板中可使用 {{ csrf_token() }}
app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['version'] = APP_VERSION


def validate_csrf_token():
    """驗證 CSRF token，失败時回傳 False"""
    token = request.headers.get('X-CSRF-Token') or (request.get_json() or {}).get('_csrf_token')
    return token and token == session.get('_csrf_token')

# 載入塔羅牌數據
def load_tarot_cards():
    """載入塔羅牌數據"""
    try:
        with open('data/tarot_cards.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# 全局變量存儲塔羅牌數據
tarot_cards = load_tarot_cards()

@app.route('/')
def index():
    """主頁"""
    logger.info('訪問首頁')
    response = make_response(render_template('index.html', active_page='index', version=APP_VERSION))
    response.headers['Cache-Control'] = f'public, max-age={APP_CONSTANTS["HTML_CACHE_MAX_AGE"]}'
    return response

@app.route('/single-card')
def single_card():
    """單張牌占卜頁面"""
    logger.info('訪問單張牌占卜頁面')
    response = make_response(render_template('single_card.html', active_page='single', version=APP_VERSION))
    response.headers['Cache-Control'] = f'public, max-age={APP_CONSTANTS["HTML_CACHE_MAX_AGE"]}'
    return response

@app.route('/three-cards')
def three_cards():
    """三張牌占卜頁面"""
    logger.info('訪問三張牌占卜頁面')
    response = make_response(render_template('three_cards.html', active_page='three', version=APP_VERSION))
    response.headers['Cache-Control'] = f'public, max-age={APP_CONSTANTS["HTML_CACHE_MAX_AGE"]}'
    return response

@app.route('/guide')
def guide():
    """占卜指南頁面：如何提問與牌陣說明"""
    logger.info('訪問占卜指南頁面')
    response = make_response(render_template('guide.html', active_page='guide', version=APP_VERSION))
    response.headers['Cache-Control'] = f'public, max-age={APP_CONSTANTS["HTML_CACHE_MAX_AGE"]}'
    return response

@app.route('/history')
def history():
    """占卜歷史記錄頁面"""
    logger.info('訪問占卜歷史記錄頁面')
    response = make_response(render_template('history.html', active_page='history', version=APP_VERSION))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/celtic-cross')
def celtic_cross():
    """凱爾特十字占卜頁面"""
    logger.info('訪問凱爾特十字占卜頁面')
    response = make_response(render_template('celtic_cross.html', active_page='celtic', version=APP_VERSION))
    response.headers['Cache-Control'] = f'public, max-age={APP_CONSTANTS["HTML_CACHE_MAX_AGE"]}'
    return response

@app.route('/api/draw-single', methods=['POST'])
def draw_single_card():
    """抽取單張牌API"""
    if not validate_csrf_token():
        logger.warning('CSRF 驗證失敗')
        return jsonify({'success': False, 'message': 'CSRF 驗證失敗'}), 403
    try:
        data = request.get_json()
        question = data.get('question', '')

        # 隨機選擇一張牌
        card = random.choice(tarot_cards)

        # 隨機決定正位或逆位
        is_reversed = random.choice([True, False])

        result = {
            'card': card,
            'is_reversed': is_reversed,
            'question': question,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f'單張牌抽取成功: {card["name"]}')
        return jsonify({
            'success': True,
            'data': result,
            'message': '抽牌成功'
        })
    except Exception as e:
        logger.error(f'單張牌抽取失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'抽牌失敗: {str(e)}'
        }), 500

@app.route('/api/draw-three', methods=['POST'])
def draw_three_cards():
    """抽取三張牌API"""
    if not validate_csrf_token():
        logger.warning('CSRF 驗證失敗')
        return jsonify({'success': False, 'message': 'CSRF 驗證失敗'}), 403
    try:
        data = request.get_json()
        question = data.get('question', '')

        # 隨機選擇三張不同的牌
        selected_cards = random.sample(tarot_cards, APP_CONSTANTS['THREE_CARDS_COUNT'])

        # 為每張牌隨機決定正位或逆位
        positions = ['過去', '現在', '未來']
        cards_with_position = []
        for i, card in enumerate(selected_cards):
            is_reversed = random.choice([True, False])
            cards_with_position.append({
                'card': card,
                'is_reversed': is_reversed,
                'position': positions[i]
            })

        result = {
            'cards': cards_with_position,
            'question': question,
            'timestamp': datetime.now().isoformat()
        }

        card_names = [c['card']['name'] for c in cards_with_position]
        logger.info(f'三張牌抽取成功: {", ".join(card_names)}')
        return jsonify({
            'success': True,
            'data': result,
            'message': '抽牌成功'
        })
    except Exception as e:
        logger.error(f'三張牌抽取失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'抽牌失敗: {str(e)}'
        }), 500

@app.route('/api/draw-celtic-cross', methods=['POST'])
def draw_celtic_cross():
    """抽取凱爾特十字牌陣API"""
    if not validate_csrf_token():
        logger.warning('CSRF 驗證失敗')
        return jsonify({'success': False, 'message': 'CSRF 驗證失敗'}), 403
    try:
        data = request.get_json()
        question = data.get('question', '')

        # 隨機選擇十張不同的牌
        selected_cards = random.sample(tarot_cards, APP_CONSTANTS['CELTIC_CROSS_COUNT'])

        # 為每張牌隨機決定正位或逆位
        cards_with_position = []
        for i, card in enumerate(selected_cards):
            is_reversed = random.choice([True, False])
            position_info = CELTIC_CROSS_POSITIONS[i]
            cards_with_position.append({
                'card': card,
                'is_reversed': is_reversed,
                'position': position_info['name'],
                'position_en': position_info['name_en'],
                'position_description': position_info['description']
            })

        result = {
            'cards': cards_with_position,
            'question': question,
            'spread_type': 'celtic_cross',
            'timestamp': datetime.now().isoformat()
        }

        card_names = [c['card']['name'] for c in cards_with_position]
        logger.info(f'凱爾特十字抽取成功: {", ".join(card_names)}')
        return jsonify({
            'success': True,
            'data': result,
            'message': '抽牌成功'
        })
    except Exception as e:
        logger.error(f'凱爾特十字抽取失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'抽牌失敗: {str(e)}'
        }), 500

@app.route('/api/card/<card_id>')
def get_card_info(card_id):
    """獲取特定牌的信息API"""
    try:
        card = next((c for c in tarot_cards if c['id'] == card_id), None)
        if card:
            logger.info(f'查詢牌資訊: {card["name"]}')
            return jsonify({
                'success': True,
                'data': card,
                'message': '獲取牌信息成功'
            })
        else:
            logger.warning(f'找不到牌: {card_id}')
            return jsonify({
                'success': False,
                'message': '找不到指定的牌'
            }), 404
    except Exception as e:
        logger.error(f'獲取牌信息失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'獲取牌信息失敗: {str(e)}'
        }), 500

@app.route('/api/save-reading', methods=['POST'])
def save_reading():
    """保存占卜記錄API"""
    if not validate_csrf_token():
        logger.warning('CSRF 驗證失敗')
        return jsonify({'success': False, 'message': 'CSRF 驗證失敗'}), 403
    try:
        data = request.get_json()

        # 這裡可以實現保存到數據庫的邏輯
        # 目前只是簡單返回成功
        reading_id = f"reading_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f'占卜記錄保存成功: {reading_id}')
        return jsonify({
            'success': True,
            'data': {'reading_id': reading_id},
            'message': '占卜記錄保存成功'
        })
    except Exception as e:
        logger.error(f'保存占卜記錄失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'保存占卜記錄失敗: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 確保必要的目錄存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images/cards', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    logger.info('VibeCodingTarot 應用啟動')
    app.run(debug=True, host='0.0.0.0', port=APP_CONSTANTS['DEFAULT_PORT'], use_reloader=False)
