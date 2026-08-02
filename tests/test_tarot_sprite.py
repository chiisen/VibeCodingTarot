import sys
import os
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from app import app


class TestSpriteCoordinates(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'tarot_cards.json'),
                  encoding='utf-8') as f:
            cls.cards = json.load(f)

    def test_all_78_cards_exist(self):
        self.assertEqual(len(self.cards), 78, "必須有 78 張牌")

    def test_every_card_has_sprite_coords(self):
        missing = [c['id'] for c in self.cards
                   if 'sprite_x' not in c or 'sprite_y' not in c]
        self.assertEqual(missing, [], f"缺少 sprite 座標: {missing}")

    def test_sprite_coords_in_range(self):
        bad = [(c['id'], c['sprite_x'], c['sprite_y'])
               for c in self.cards
               if not (0 <= c['sprite_x'] <= 12 and 0 <= c['sprite_y'] <= 5)]
        self.assertEqual(bad, [], f"座標越界: {bad}")

    def test_sprite_coords_unique(self):
        seen = set()
        duplicates = []
        for c in self.cards:
            key = (c['sprite_x'], c['sprite_y'])
            if key in seen:
                duplicates.append((c['id'], key))
            seen.add(key)
        self.assertEqual(duplicates, [], f"座標重複: {duplicates}")


if __name__ == '__main__':
    unittest.main()
