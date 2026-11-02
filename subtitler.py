#!/usr/bin/env python3
"""
zero-token-whisper-cli — Instant Local Video & Audio Subtitle Generator.
Transcribes media locally via Faster-Whisper, formats timestamps,
and generates karaoke-style ASS or standard SRT subtitle files with keyword highlights (0 token LLM cost).
"""

import sys
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """Verify required system tools are present."""
    if not shutil.which("ffmpeg"):
        print("[-] ffmpeg is not found on PATH. Please install ffmpeg to extract media audio.")
        sys.exit(1)

def extract_audio(input_file: str, output_wav: str):
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        output_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_ass(segments, output_ass: str, highlight_keywords=None):
    keywords = [k.lower().strip() for k in (highlight_keywords or []) if k.strip()]
    
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
            for kw in keywords:
                if kw.upper() in text:
                    text = text.replace(kw.upper(), f"{{\\c&H0038BDF8&}}{kw.upper()}{{\\c&H00FFFFFF&}}")
                    
            f.write(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{text}\n")
    print(f"[✓] Generated ASS subtitle file: {output_ass}")

def generate_srt(segments, output_srt: str):
    with open(output_srt, "w", encoding="utf-8") as f:
        for idx, s in enumerate(segments, start=1):
            start_m, start_s = divmod(s.start, 60)
            start_h, start_m = divmod(start_m, 60)
            start_s_int = int(start_s)
            start_ms = int(round((start_s - start_s_int) * 1000))
            if start_ms >= 1000:
                start_s_int += 1
                start_ms = 0
            
            end_m, end_s = divmod(s.end, 60)
            end_h, end_m = divmod(end_m, 60)
            end_s_int = int(end_s)
            end_ms = int(round((end_s - end_s_int) * 1000))
            if end_ms >= 1000:
                end_s_int += 1
                end_ms = 0

            t_start = f"{int(start_h):02d}:{int(start_m):02d}:{start_s_int:02d},{start_ms:03d}"
            t_end = f"{int(end_h):02d}:{int(end_m):02d}:{end_s_int:02d},{end_ms:03d}"
            f.write(f"{idx}\n{t_start} --> {t_end}\n{s.text.strip()}\n\n")
    print(f"[✓] Generated SRT subtitle file: {output_srt}")

def main():
    parser = argparse.ArgumentParser(description="Zero-Token Offline Subtitle Generator via Faster-Whisper.")
    parser.add_argument("media", help="Path to input video or audio file")
    parser.add_argument("--output", "-o", help="Path to output subtitle file (.ass or .srt)")
    parser.add_argument("--format", "-f", choices=["ass", "srt"], help="Subtitle format (default: auto from extension, or ass)")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium, default: base)")
    parser.add_argument("--language", "-l", help="Language code (e.g. 'en', 'id'). Omit for auto-detection.")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Inference device (cpu, cuda, default: cpu)")
    parser.add_argument("--keywords", help="Comma-separated keywords to highlight with gold color in ASS subtitles")

    args = parser.parse_args()
    check_dependencies()

    media_path = Path(args.media).resolve()
    if not media_path.exists():
        print(f"[-] Input file not found: {media_path}")
        sys.exit(1)

    # Determine output format and path
    target_format = args.format
    if not target_format:
        if args.output and args.output.lower().endswith(".srt"):
            target_format = "srt"
        else:
            target_format = "ass"

    out_file = args.output or f"{media_path.stem}.{target_format}"

    # Safe temp wav allocation
    temp_wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_wav = temp_wav_file.name
    temp_wav_file.close()

    try:
        print(f"[*] Extracting audio from: {media_path.name}")
        extract_audio(str(media_path), temp_wav)

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("[-] faster-whisper is not installed. Install with: pip install faster-whisper")
            sys.exit(1)

        compute_type = "float16" if args.device == "cuda" else "int8"
        print(f"[*] Loading model '{args.model}' on {args.device} ({compute_type})...")
        model = WhisperModel(args.model, device=args.device, compute_type=compute_type)

        transcribe_kwargs = {"beam_size": 1}
        if args.language:
            transcribe_kwargs["language"] = args.language

        print(f"[*] Transcribing audio...")
        segments, info = model.transcribe(temp_wav, **transcribe_kwargs)
        segments_list = list(segments)
        print(f"[✓] Transcription finished: detected language '{info.language}' (prob: {info.language_probability:.2f})")

        if target_format == "srt":
            generate_srt(segments_list, out_file)
        else:
            kw_list = args.keywords.split(",") if args.keywords else []
            generate_ass(segments_list, out_file, kw_list)

    finally:
        if Path(temp_wav).exists():
            Path(temp_wav).unlink()

if __name__ == "__main__":
    main()
