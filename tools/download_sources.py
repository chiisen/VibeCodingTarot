"""從 Wikimedia Commons 下載 78 張塔羅牌原圖至 tools/source_cards/。

資料來源: Category:Rider-Waite-Smith tarot deck (TaionWC)
  https://commons.wikimedia.org/wiki/Category:Rider-Waite-Smith_tarot_deck_(TaionWC)
所有檔案為 .jpg,檔名約定:
  - 大阿爾克那: RWS Tarot NN <Name>.jpg  (例 RWS Tarot 00 Fool.jpg)
  - 小阿爾克那: <Suit><NN>.jpg  (例 Cups01.jpg, Wands14.jpg)

下載後檔名一律重新命名為 <card_id>.jpg 對應 data/tarot_cards.json 的 id。
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / 'tools' / 'source_cards'
DATA_PATH = ROOT / 'data' / 'tarot_cards.json'

# Wikimedia User-Agent 政策:必須明確識別工具與聯絡管道,
# 不接受偽裝成瀏覽器的 UA(會被視為違反 policy)。
# https://meta.wikimedia.org/wiki/User-Agent_policy
HEADERS = {
    'User-Agent': 'VibeCodingTarot/1.0 (https://github.com/chiisen/VibeCodingTarot; sprite rebuild tool)',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
}

# 退避觸發條件:429 (rate limit) 與 5xx (server 端錯誤)
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 2.0

# 大阿爾克那英文名 (對應 name_en 去除 "The " 前綴後的單字)
MAJOR_ARCANA_NAMES = {
    0: 'Fool',
    1: 'Magician',
    2: 'High Priestess',
    3: 'Empress',
    4: 'Emperor',
    5: 'Hierophant',
    6: 'Lovers',
    7: 'Chariot',
    8: 'Strength',
    9: 'Hermit',
    10: 'Wheel of Fortune',
    11: 'Justice',
    12: 'Hanged Man',
    13: 'Death',
    14: 'Temperance',
    15: 'Devil',
    16: 'Tower',
    17: 'Star',
    18: 'Moon',
    19: 'Sun',
    20: 'Judgement',
    21: 'World',
}

# 我們 card_id -> Wikimedia 牌名片段
SUIT_TO_WIKI = {
    'wands': 'Wands',
    'cups': 'Cups',
    'swords': 'Swords',
    'pentacles': 'Pents',
}

RANK_TO_NUM = {
    'ace': '01',
    '2': '02', '3': '03', '4': '04', '5': '05',
    '6': '06', '7': '07', '8': '08', '9': '09', '10': '10',
    'page': '11', 'knight': '12', 'queen': '13', 'king': '14',
}


def make_major_arcana_filename(number: int) -> str:
    return f'RWS Tarot {number:02d} {MAJOR_ARCANA_NAMES[number]}.jpg'


def make_minor_arcana_filename(card_id: str) -> str:
    # e.g. wands_ace, cups_2, swords_king
    suit, rank = card_id.split('_', 1)
    return f'{SUIT_TO_WIKI[suit]}{RANK_TO_NUM[rank]}.jpg'


def resolve_url(filename: str) -> str:
    """透過 MediaWiki API 查詢檔案實際 URL。"""
    title = f'File:{filename}'
    title_q = urllib.parse.quote(title)
    api_url = (
        'https://commons.wikimedia.org/w/api.php'
        f'?action=query&format=json&titles={title_q}&prop=imageinfo&iiprop=url'
    )
    req = urllib.request.Request(api_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    pages = data['query']['pages']
    page = list(pages.values())[0]
    if 'imageinfo' not in page:
        raise FileNotFoundError(f'Wikimedia 找不到 {filename}')
    return page['imageinfo'][0]['url']


def _http_get_bytes(url: str, timeout: int = 60) -> bytes:
    """GET with exponential backoff on retryable HTTP errors and URLError.

    Retryable conditions:
      - HTTP 429 (rate limit)
      - HTTP 5xx (server 端錯誤: 500 / 502 / 503 / 504)
      - urllib.error.URLError (DNS 解析失敗、連線被拒、timeout 等)

    退避策略: 2s → 4s → 8s → 16s(最多 MAX_RETRIES 次嘗試)
    """
    delay = INITIAL_BACKOFF_SECONDS
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE_HTTP_CODES and attempt < MAX_RETRIES - 1:
                print(f'    (HTTP {e.code} 等候 {delay:.0f}s ...)', file=sys.stderr, end=' ', flush=True)
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError as e:
            # DNS 失敗、連線被拒、timeout 等
            if attempt < MAX_RETRIES - 1:
                reason = getattr(e, 'reason', e)
                print(f'    (URLError {reason!r} 等候 {delay:.0f}s ...)', file=sys.stderr, end=' ', flush=True)
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError(f'過多重試後仍失敗: {url}')


def download(url: str, dest: Path) -> None:
    data = _http_get_bytes(url, timeout=60)
    with open(dest, 'wb') as f:
        f.write(data)


def main():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    cards = json.loads(DATA_PATH.read_text(encoding='utf-8'))

    failed = []
    skipped = 0
    for card in cards:
        cid = card['id']
        dest = SOURCE_DIR / f'{cid}.jpg'
        if dest.exists() and dest.stat().st_size > 1000:
            skipped += 1
            continue

        if card['arcana'] == 'major':
            wiki_filename = make_major_arcana_filename(card['number'])
        else:
            wiki_filename = make_minor_arcana_filename(cid)

        try:
            url = resolve_url(wiki_filename)
            download(url, dest)
            size = dest.stat().st_size
            print(f'  [OK]  {cid:<22} <- {wiki_filename:<40} ({size//1024} KB)')
        except Exception as e:
            print(f'  [FAIL] {cid:<22} <- {wiki_filename}: {e}', file=sys.stderr)
            failed.append((cid, wiki_filename, str(e)))

        # 禮貌等待,避免觸發 rate limit
        time.sleep(1.5)

    print()
    print(f'略過已存在: {skipped}')
    print(f'下載成功:   {len(cards) - skipped - len(failed)}')
    if failed:
        print(f'下載失敗:   {len(failed)}')
        for cid, fn, err in failed:
            print(f'  - {cid} ({fn}): {err}')
        sys.exit(1)


if __name__ == '__main__':
    main()
