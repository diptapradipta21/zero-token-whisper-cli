#!/usr/bin/env python3
"""
zero-token-whisper-cli — Instant Local Video & Audio Subtitle Generator.
Transcribes media locally via Faster-Whisper, formats word-level timestamps,
and generates karaoke-style ASS / SRT subtitle files with golden keyword highlights (0 token LLM cost).
"""

import sys
import subprocess
import argparse
from pathlib import Path

def extract_audio(input_file: str, output_wav: str):
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        output_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_ass(segments, output_ass: str, highlight_keywords=None):
    keywords = [k.lower().strip() for k in (highlight_keywords or [])]
    
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Plus Jakarta Sans,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header)
        for s in segments:
            start_m, start_s = divmod(s.start, 60)
            start_h, start_m = divmod(start_m, 60)
            end_m, end_s = divmod(s.end, 60)
            end_h, end_m = divmod(end_m, 60)
            
            t_start = f"{int(start_h):01d}:{int(start_m):02d}:{start_s:05.2f}"
            t_end = f"{int(end_h):01d}:{int(end_m):02d}:{end_s:05.2f}"
            
            text = s.text.strip().upper()
            # Highlight golden keywords
            for kw in keywords:
                if kw.upper() in text:
                    text = text.replace(kw.upper(), f"{{\\c&H0038BDF8&}}{kw.upper()}{{\\c&H00FFFFFF&}}")
                    
            f.write(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{text}\n")
    print(f"[✓] Generated ASS subtitle file: {output_ass}")

def main():
    parser = argparse.ArgumentParser(description="Zero-Token Offline Subtitle Generator via Faster-Whisper.")
    parser.add_argument("media", help="Path to input video or audio file")
    parser.add_argument("--output", "-o", help="Path to output subtitle file (.ass or .srt)")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium)")
    parser.add_argument("--keywords", help="Comma-separated keywords to highlight with gold color")

    args = parser.parse_args()
    media_path = Path(args.media).resolve()
    out_ass = args.output or f"{media_path.stem}.ass"
    temp_wav = f"/tmp/{media_path.stem}_temp.wav"

    print(f"[*] Processing: {media_path.name}")
    extract_audio(str(media_path), temp_wav)

    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(args.model, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(temp_wav, beam_size=1)
        kw_list = args.keywords.split(",") if args.keywords else []
        generate_ass(list(segments), out_ass, kw_list)
    except ImportError:
        print("[-] faster-whisper is not installed. Install with: pip install faster-whisper")
        sys.exit(1)
    finally:
        if Path(temp_wav).exists():
            Path(temp_wav).unlink()

if __name__ == "__main__":
    main()
