import os
import shutil
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitler import generate_ass, generate_srt, generate_vtt


@dataclass
class DummySegment:
    start: float
    end: float
    text: str


class TestSubtitler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.segments = [
            DummySegment(start=1.25, end=4.50, text="Hello and welcome to the show"),
            DummySegment(start=5.00, end=8.75, text="Today we discuss zero-token AI agents"),
        ]

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_srt(self):
        out_srt = Path(self.test_dir) / "output.srt"
        generate_srt(self.segments, str(out_srt))
        self.assertTrue(out_srt.exists())

        content = out_srt.read_text(encoding="utf-8")
        self.assertIn("1\n00:00:01,250 --> 00:00:04,500\nHello and welcome to the show", content)
        self.assertIn("2\n00:00:05,000 --> 00:00:08,750\nToday we discuss zero-token AI agents", content)

    def test_generate_vtt(self):
        out_vtt = Path(self.test_dir) / "output.vtt"
        generate_vtt(self.segments, str(out_vtt))
        self.assertTrue(out_vtt.exists())

        content = out_vtt.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("WEBVTT\n\n"))
        self.assertIn("00:00:01.250 --> 00:00:04.500", content)
        self.assertIn("Hello and welcome to the show", content)

    def test_generate_ass_with_keyword_highlight(self):
        out_ass = Path(self.test_dir) / "output.ass"
        generate_ass(self.segments, str(out_ass), highlight_keywords=["zero-token", "show"])
        self.assertTrue(out_ass.exists())

        content = out_ass.read_text(encoding="utf-8")
        self.assertIn("[Script Info]", content)
        self.assertIn("PlayResX: 1080", content)
        # Check keyword color override
        self.assertIn(r"{\c&H0038BDF8&}SHOW{\c&H00FFFFFF&}", content)
        self.assertIn(r"{\c&H0038BDF8&}ZERO-TOKEN{\c&H00FFFFFF&}", content)


if __name__ == "__main__":
    unittest.main()
