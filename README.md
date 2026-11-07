# 🎬 Zero-Token Whisper CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Zero Token Cost](https://img.shields.io/badge/LLM%20Tokens-0-green.svg)](#)
[![Faster-Whisper](https://img.shields.io/badge/Engine-Faster--Whisper-orange.svg)](#)

> **Offline local video & audio subtitle generator. Produces karaoke-style ASS, standard SRT, and modern HTML5 WebVTT subtitles with keyword highlights without burning AI tokens.**

---

## ⚡ Quick Start

```bash
# Generate ASS subtitles with highlighted golden keywords
python3 subtitler.py video.mp4 --keywords "AI,token,viral,profit"

# Generate standard SRT subtitles
python3 subtitler.py video.mp4 -o output.srt

# Generate HTML5 WebVTT subtitles
python3 subtitler.py video.mp4 -o output.vtt

# Specify language and Whisper model size
python3 subtitler.py video.mp4 -l en --model small
```

---

## ⚙️ Options & Flags
- `--output`, `-o`: Output file path (`.ass`, `.srt`, or `.vtt`).
- `--format`, `-f`: Explicit format selection (`ass`, `srt`, or `vtt`, auto-detected by default).
- `--language`, `-l`: Force transcription language code (e.g. `en`, `id`).
- `--model`: Model size (`tiny`, `base`, `small`, `medium`).
- `--device`: Compute device (`cpu` or `cuda`).
- `--keywords`: Comma-separated words to highlight in karaoke ASS style.

---

## 📄 License
MIT License - Copyright (c) 2026 Fajar Indra Pradipta Gajah.

## 🧪 Testing

```bash
python3 -m unittest discover tests
```
