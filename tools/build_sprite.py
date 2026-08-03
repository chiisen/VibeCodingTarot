"""從 tools/source_cards/ 內 78 張個別牌圖組裝 sprite sheet。

輸入檔名約定: <card_id>.jpg (例 fool.jpg)
輸入尺寸:任意,但會被縮放至 200x340
輸出:static/img/tarot_sprite.jpg (2600x2040, 13 欄 x 6 列)
"""
import json
import os
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / 'tools' / 'source_cards'
OUTPUT_PATH = ROOT / 'static' / 'img' / 'tarot_sprite.jpg'
DATA_PATH = ROOT / 'data' / 'tarot_cards.json'

COLS = 13
ROWS = 6
CELL_W = 200
CELL_H = 340
JPEG_QUALITY = 85


def main():
    cards = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    sprite = Image.new('RGB', (COLS * CELL_W, ROWS * CELL_H), (10, 10, 18))

    missing = []
    for card in cards:
        src = SOURCE_DIR / f"{card['id']}.jpg"
        if not src.exists():
            missing.append(card['id'])
            continue
        cell = Image.open(src).convert('RGB').resize((CELL_W, CELL_H), Image.LANCZOS)
        x = card['sprite_x'] * CELL_W
        y = card['sprite_y'] * CELL_H
        sprite.paste(cell, (x, y))

    if missing:
        print(f"[WARN] 缺少 {len(missing)} 張牌圖: {missing}", file=sys.stderr)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sprite.save(OUTPUT_PATH, 'JPEG', quality=JPEG_QUALITY, optimize=True)
    print(f"[OK] sprite sheet 已產出: {OUTPUT_PATH} ({sprite.size})")


if __name__ == '__main__':
    main()
