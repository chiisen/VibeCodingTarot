import sys
import os
import unittest
import json
import shutil
import tempfile
import urllib.error
from unittest import mock

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


class TestSpriteSheetAsset(unittest.TestCase):

    SPRITE_PATH = os.path.join(os.path.dirname(__file__), '..',
                               'static', 'img', 'tarot_sprite.jpg')

    def test_sprite_jpg_exists(self):
        self.assertTrue(os.path.exists(self.SPRITE_PATH),
                        f"找不到 sprite sheet: {self.SPRITE_PATH}")

    def test_sprite_jpg_dimensions(self):
        from PIL import Image
        with Image.open(self.SPRITE_PATH) as img:
            self.assertEqual(img.size, (2600, 2040),
                             f"sprite 尺寸錯誤: {img.size}, 預期 (2600, 2040)")


class TestBuildSpriteFailFast(unittest.TestCase):
    """驗證 build_sprite.py 在缺圖時 fail-fast。

    需求:
      - sys.exit(1)
      - 不產出 sprite(若已存在 stale sprite 應被刪除)
      - 錯誤訊息送往 stderr 且列出缺漏牌 id
    """

    def setUp(self):
        # 用 tempfile 隔離 SOURCE_DIR / OUTPUT_PATH / DATA_PATH,避免污染 repo
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.tmp_root = mock.MagicMock()
        # __file__/.parent.parent → 模擬專案根目錄
        self.project_root = self.tmp
        self.source_dir = os.path.join(self.tmp, 'tools', 'source_cards')
        self.output_path = os.path.join(self.tmp, 'static', 'img', 'tarot_sprite.jpg')
        self.data_path = os.path.join(self.tmp, 'data', 'tarot_cards.json')
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

        # 寫入最小的 tarot_cards.json:3 張牌,故意缺 1 張
        self.cards = [
            {'id': 'present', 'sprite_x': 0, 'sprite_y': 0},
            {'id': 'missing_one', 'sprite_x': 1, 'sprite_y': 0},
            {'id': 'also_present', 'sprite_x': 2, 'sprite_y': 0},
        ]
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.cards, f)

        # 為 present 與 also_present 產出 1x1 黑色 jpg
        from PIL import Image
        for cid in ('present', 'also_present'):
            img = Image.new('RGB', (10, 10), (0, 0, 0))
            img.save(os.path.join(self.source_dir, f'{cid}.jpg'), 'JPEG')

    def _import_build_sprite(self):
        """以 patch 過的常數重新 import build_sprite。"""
        import importlib
        if 'tools.build_sprite' in sys.modules:
            del sys.modules['tools.build_sprite']
        import tools.build_sprite as bs
        bs.SOURCE_DIR.__class__ = type(os.path.join)  # 觸發 reload 不影響 mock
        return bs

    def test_missing_image_exits_with_code_1(self):
        # 用 subprocess 跑 build_sprite,並 monkey patch 它的常數
        import subprocess
        # 寫一個 wrapper script,複寫 SOURCE_DIR/OUTPUT_PATH/DATA_PATH 後呼叫 main()
        wrapper = os.path.join(self.tmp, 'run_build_sprite.py')
        with open(wrapper, 'w', encoding='utf-8') as f:
            f.write(
                "import sys, os\n"
                "sys.path.insert(0, %r)\n"
                "import tools.build_sprite as bs\n"
                "from pathlib import Path\n"
                "bs.SOURCE_DIR = Path(%r)\n"
                "bs.OUTPUT_PATH = Path(%r)\n"
                "bs.DATA_PATH = Path(%r)\n"
                "bs.main()\n"
                % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   self.source_dir, self.output_path, self.data_path)
            )
        # 確保 tools package 可 import
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            [sys.executable, wrapper],
            capture_output=True, text=True, env=env, timeout=30
        )
        self.assertNotEqual(result.returncode, 0,
                            f"build_sprite 應以非零退出,實際 {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}")
        self.assertIn('missing_one', result.stderr,
                      f"stderr 應列出缺漏牌 id,實際 stderr:\n{result.stderr}")

    def test_missing_image_does_not_produce_sprite_and_deletes_stale(self):
        # 先放一個舊的 stale sprite
        with open(self.output_path, 'wb') as f:
            f.write(b'old stale sprite bytes')
        self.assertTrue(os.path.exists(self.output_path))

        import subprocess
        wrapper = os.path.join(self.tmp, 'run_build_sprite.py')
        with open(wrapper, 'w', encoding='utf-8') as f:
            f.write(
                "import sys, os\n"
                "sys.path.insert(0, %r)\n"
                "import tools.build_sprite as bs\n"
                "from pathlib import Path\n"
                "bs.SOURCE_DIR = Path(%r)\n"
                "bs.OUTPUT_PATH = Path(%r)\n"
                "bs.DATA_PATH = Path(%r)\n"
                "bs.main()\n"
                % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   self.source_dir, self.output_path, self.data_path)
            )
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            [sys.executable, wrapper],
            capture_output=True, text=True, env=env, timeout=30
        )
        self.assertNotEqual(result.returncode, 0)
        # stale sprite 必須被刪除(避免下游繼續使用半殘檔案)
        self.assertFalse(os.path.exists(self.output_path),
                         f"缺圖時應刪除 stale sprite,但 {self.output_path} 仍存在")


class TestDownloadSourcesBackoff(unittest.TestCase):
    """驗證 _http_get_bytes 在 HTTP 5xx 與 URLError 上會退避重試。"""

    def test_retries_on_http_5xx_then_succeeds(self):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tools import download_sources as ds

        call_count = {'n': 0}

        def fake_urlopen(req, timeout=60):
            call_count['n'] += 1
            if call_count['n'] == 1:
                raise urllib.error.HTTPError(req.full_url, 503, 'Service Unavailable',
                                             {}, None)
            # 第二次成功
            resp = mock.MagicMock()
            resp.read = mock.MagicMock(return_value=b'OK')
            resp.__enter__ = mock.MagicMock(return_value=resp)
            resp.__exit__ = mock.MagicMock(return_value=False)
            return resp

        with mock.patch.object(ds.time, 'sleep') as fake_sleep:
            with mock.patch.object(ds.urllib.request, 'urlopen', side_effect=fake_urlopen):
                data = ds._http_get_bytes('http://example.test/img.jpg')

        self.assertEqual(data, b'OK')
        self.assertEqual(call_count['n'], 2, "503 應觸發至少 1 次重試")
        fake_sleep.assert_called()  # 退避 sleep 應至少被呼叫一次

    def test_retries_on_urlerror_then_succeeds(self):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tools import download_sources as ds

        call_count = {'n': 0}

        def fake_urlopen(req, timeout=60):
            call_count['n'] += 1
            if call_count['n'] == 1:
                raise urllib.error.URLError('temporary DNS failure')
            resp = mock.MagicMock()
            resp.read = mock.MagicMock(return_value=b'OK')
            resp.__enter__ = mock.MagicMock(return_value=resp)
            resp.__exit__ = mock.MagicMock(return_value=False)
            return resp

        with mock.patch.object(ds.time, 'sleep') as fake_sleep:
            with mock.patch.object(ds.urllib.request, 'urlopen', side_effect=fake_urlopen):
                data = ds._http_get_bytes('http://example.test/img.jpg')

        self.assertEqual(data, b'OK')
        self.assertEqual(call_count['n'], 2, "URLError 應觸發至少 1 次重試")
        fake_sleep.assert_called()

    def test_does_not_retry_on_4xx_non_429(self):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tools import download_sources as ds

        call_count = {'n': 0}

        def fake_urlopen(req, timeout=60):
            call_count['n'] += 1
            raise urllib.error.HTTPError(req.full_url, 404, 'Not Found', {}, None)

        with mock.patch.object(ds.time, 'sleep') as fake_sleep:
            with mock.patch.object(ds.urllib.request, 'urlopen', side_effect=fake_urlopen):
                with self.assertRaises(urllib.error.HTTPError):
                    ds._http_get_bytes('http://example.test/img.jpg')

        self.assertEqual(call_count['n'], 1, "404 不應重試,應立即 raise")
        fake_sleep.assert_not_called()

    def test_user_agent_identifies_tool(self):
        """驗證 User-Agent 符合 Wikimedia User-Agent 政策(識別型,不偽裝瀏覽器)。"""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tools import download_sources as ds
        ua = ds.HEADERS['User-Agent']
        self.assertNotIn('Mozilla', ua, "User-Agent 不應偽裝成 Mozilla")
        self.assertNotIn('AppleWebKit', ua, "User-Agent 不應偽裝成瀏覽器")
        self.assertIn('VibeCodingTarot', ua, "User-Agent 應包含工具名稱")
        self.assertIn('https://', ua, "User-Agent 應包含聯絡管道")


class TestCardSpriteCss(unittest.TestCase):

    CSS_PATH = os.path.join(os.path.dirname(__file__), '..',
                            'static', 'css', 'card-sprite.css')

    def test_css_file_exists(self):
        self.assertTrue(os.path.exists(self.CSS_PATH),
                        f"找不到 CSS: {self.CSS_PATH}")

    def test_css_contains_base_rule(self):
        with open(self.CSS_PATH, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('.tarot-card-image', content)
        self.assertIn('--sprite-pos', content)
        self.assertIn('background-image', content)

    def test_css_contains_reversed_rule(self):
        with open(self.CSS_PATH, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('[data-reversed="true"]', content)
        self.assertIn('rotate(180deg)', content)

    def test_css_contains_pulse_animation(self):
        with open(self.CSS_PATH, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('@keyframes', content)
        self.assertIn('pulse', content)


if __name__ == '__main__':
    unittest.main()
