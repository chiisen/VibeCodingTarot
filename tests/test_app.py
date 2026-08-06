import json
from pathlib import Path
import sys
import os
import unittest

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app


class TestTarotApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_page(self):
        """測試首頁渲染"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('VibeCodingTarot'.encode('utf-8'), response.data)

    def test_single_card_page(self):
        """測試單張牌頁面渲染（包含 csrf_token）"""
        response = self.app.get('/single-card')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Divination.init('.encode('utf-8'), response.data)

    def test_three_cards_page(self):
        """測試三張牌頁面渲染"""
        response = self.app.get('/three-cards')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Divination.init('.encode('utf-8'), response.data)

    def test_celtic_cross_page(self):
        """測試凱爾特十字牌面渲染"""
        response = self.app.get('/celtic-cross')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Divination.init('.encode('utf-8'), response.data)

    def test_history_page(self):
        """測試歷史記錄頁面渲染"""
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)

    def test_guide_page(self):
        """測試占卜指南頁面渲染"""
        response = self.app.get('/guide')
        self.assertEqual(response.status_code, 200)
        self.assertIn('如何提問'.encode('utf-8'), response.data)
        self.assertIn('牌陣'.encode('utf-8'), response.data)

    def test_tarot_cards_have_sprite_coordinates(self):
        """每張牌都應包含 13 欄 6 列 sprite 座標。"""
        cards_path = Path(__file__).parents[1] / 'data' / 'tarot_cards.json'
        with cards_path.open(encoding='utf-8') as cards_file:
            cards = json.load(cards_file)

        self.assertEqual(len(cards), 78)
        for index, card in enumerate(cards):
            self.assertEqual(card['sprite_x'], index % 13)
            self.assertEqual(card['sprite_y'], index // 13)

    def test_tarot_cards_follow_sprite_order(self):
        """牌面順序應為 Major 後接四組 Minor。"""
        cards_path = Path(__file__).parents[1] / 'data' / 'tarot_cards.json'
        with cards_path.open(encoding='utf-8') as cards_file:
            cards = json.load(cards_file)

        self.assertEqual([card['number'] for card in cards[:22]], list(range(22)))
        expected_suits = ['權杖', '聖杯', '寶劍', '錢幣']
        self.assertEqual(
            [card['suit'] for card in cards[22:]],
            [suit for suit in expected_suits for _ in range(14)],
        )

    def test_api_draw_single_without_csrf(self):
        """測試無 CSRF Token 的請求應被拒絕 (403)"""
        response = self.app.post('/api/draw-single', json={'question': '測試問題'})
        self.assertEqual(response.status_code, 403)

    def test_api_draw_single_valid_csrf(self):
        """測試合法 CSRF Token 的抽牌 API"""
        with self.app.session_transaction() as sess:
            sess['_csrf_token'] = 'valid_test_token'
        response = self.app.post(
            '/api/draw-single',
            json={'question': '測試問題'},
            headers={'X-CSRF-Token': 'valid_test_token'}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['success'])
        self.assertIn('card', json_data['data'])


if __name__ == '__main__':
    unittest.main()
