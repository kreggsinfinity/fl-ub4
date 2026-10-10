"""
Idioms & Slang Decoded - Video Generator (9:16 Vertical Reel)
Explains popular idioms and slang: Literal vs Actual Meaning + Origin Story + Usage.
"""
import os, sys, json, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

BG_DARK = (15, 12, 32)
PURPLE_ACCENT = (147, 51, 234)
MAGENTA_ACCENT = (236, 72, 153)
CYAN_ACCENT = (6, 182, 212)
GOLD = (250, 204, 21)
WHITE = (255, 255, 255)
CARD_BG = (28, 22, 58)

VOICE_NATIVE = "en-US-AvaNeural"

IDIOMS = [
    {
        "idiom": "BITE THE BULLET",
        "literal": "Chewing on metal ammunition ❌",
        "meaning": "To bravely face a difficult situation you cannot avoid ✅",
        "origin": "Origin: Soldiers in battle bit on lead bullets to endure painful surgery before anesthesia!",
        "example": "I really hate dental visits, but tomorrow I just have to **bite the bullet**.",
        "script": [
            "What does the idiom 'Bite the bullet' actually mean in English?",
            "It does NOT mean chewing metal! It means bravely facing a hard situation you cannot avoid.",
            "Example: I hate dental visits, but tomorrow I just have to bite the bullet! Follow for daily idioms!"
        ]
    },
    {
        "idiom": "BREAK A LEG",
        "literal": "Fracturing your actual leg bones ❌",
        "meaning": "Wishing someone good luck before a big performance ✅",
        "origin": "Origin: Old theatre superstition that wishing good luck would invite bad spirits!",
        "example": "You are going to do great in your presentation today, **break a leg**!",
        "script": [
            "If someone tells you to 'Break a leg', do not be afraid!",
            "It is the theatrical way to wish someone good luck before a big speech or performance.",
            "Example: You will do great today Emma, break a leg! Save this reel!"
        ]
    }
]

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def render_idiom_frame(item, step_idx, total_steps, out_path):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(canvas)

    # Gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(18 + ratio * 20)
        g = int(12 + ratio * 15)
        b = int(35 + ratio * 45)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Top Pill
    draw.rounded_rectangle([(70, 90), (WIDTH - 70, 180)], radius=22, fill=(35, 25, 70), outline=MAGENTA_ACCENT, width=3)
    f_hdr = load_font(32, bold=True)
    draw.text((WIDTH // 2, 135), "🔥 SLANG & IDIOM DECODED", fill=MAGENTA_ACCENT, font=f_hdr, anchor="mm")

    # Big Idiom Banner
    draw.rounded_rectangle([(70, 220), (WIDTH - 70, 430)], radius=30, fill=(45, 30, 90), outline=GOLD, width=4)
    f_sub_lbl = load_font(28, bold=True)
    draw.text((WIDTH // 2, 270), "NATIVE EXPRESSION OF THE DAY:", fill=CYAN_ACCENT, font=f_sub_lbl, anchor="mm")
    f_idiom = load_font(68, bold=True)
    draw.text((WIDTH // 2, 350), f'"{item["idiom"]}"', fill=GOLD, font=f_idiom, anchor="mm")

    # Literal Meaning Card
    draw.rounded_rectangle([(70, 470), (WIDTH - 70, 680)], radius=25, fill=(40, 20, 35), outline=(239, 68, 68), width=3)
    f_tag = load_font(26, bold=True)
    draw.rounded_rectangle([(110, 495), (420, 545)], radius=12, fill=(239, 68, 68))
    draw.text((265, 520), "❌ LITERAL MEANING", fill=WHITE, font=f_tag, anchor="mm")
    f_lit = load_font(38, bold=True)
    draw.text((WIDTH // 2, 610), item["literal"], fill=(255, 180, 180), font=f_lit, anchor="mm")

    # True Meaning Card
    draw.rounded_rectangle([(70, 720), (WIDTH - 70, 1020)], radius=25, fill=(20, 45, 50), outline=(16, 185, 129), width=4)
    draw.rounded_rectangle([(110, 745), (450, 795)], radius=12, fill=(16, 185, 129))
    draw.text((280, 770), "✅ ACTUAL MEANING", fill=WHITE, font=f_tag, anchor="mm")
    f_true = load_font(42, bold=True)

    words = item["meaning"].split()
    lines = []
    c_line = []
    for w in words:
        tb = draw.textbbox((0, 0), " ".join(c_line + [w]), font=f_true)
        if tb[2] - tb[0] > (WIDTH - 240):
            lines.append(" ".join(c_line))
            c_line = [w]
        else:
            c_line.append(w)
    if c_line: lines.append(" ".join(c_line))
    for l_idx, l in enumerate(lines):
        draw.text((WIDTH // 2, 850 + l_idx * 55), l, fill=WHITE, font=f_true, anchor="mm")

    # Origin Story Box
    draw.rounded_rectangle([(70, 1060), (WIDTH - 70, 1340)], radius=25, fill=CARD_BG, outline=PURPLE_ACCENT, width=3)
    f_orig_lbl = load_font(28, bold=True)
    draw.text((110, 1105), "🧠 HISTORICAL ORIGIN & BACKSTORY:", fill=GOLD, font=f_orig_lbl, anchor="lm")
    f_orig_txt = load_font(34, bold=False)

    owords = item["origin"].split()
    olines = []
    col = []
    for ow in owords:
        tb = draw.textbbox((0, 0), " ".join(col + [ow]), font=f_orig_txt)
        if tb[2] - tb[0] > (WIDTH - 240):
            olines.append(" ".join(col))
            col = [ow]
        else:
            col = [ow]
    if col: olines.append(" ".join(col))
    for ol_idx, ol in enumerate(olines):
        draw.text((110, 1165 + ol_idx * 48), ol, fill=(225, 230, 245), font=f_orig_txt, anchor="lm")

    # Example Card
    draw.rounded_rectangle([(70, 1380), (WIDTH - 70, 1680)], radius=25, fill=(30, 36, 68), outline=CYAN_ACCENT, width=3)
    f_ex_lbl = load_font(28, bold=True)
    draw.text((110, 1425), "💬 NATIVE CONVERSATION USAGE:", fill=CYAN_ACCENT, font=f_ex_lbl, anchor="lm")

    f_ex = load_font(40, bold=True)
    ex_clean = item["example"].replace("**", "")
    ewords = ex_clean.split()
    elines = []
    ce = []
    for ew in ewords:
        tb = draw.textbbox((0, 0), " ".join(ce + [ew]), font=f_ex)
        if tb[2] - tb[0] > (WIDTH - 240):
            elines.append(" ".join(ce))
            ce = [ew]
        else:
            ce = [ew]
    if ce: elines.append(" ".join(ce))
    for el_idx, el in enumerate(elines):
        draw.text((WIDTH // 2, 1510 + el_idx * 55), f'"{el}"', fill=WHITE, font=f_ex, anchor="mm")

    # Footer
    f_cta = load_font(32, bold=True)
    draw.text((WIDTH // 2, 1780), "❤️ Double-Tap if you loved this expression!", fill=MAGENTA_ACCENT, font=f_cta, anchor="mm")
    f_sub = load_font(26, bold=False)
    draw.text((WIDTH // 2, 1835), "Follow Idioms & Slang Master for daily secrets!", fill=(148, 163, 184), font=f_sub, anchor="mm")

    canvas.convert("RGB").save(out_path, quality=95)

async def assemble_idiom_reel(item, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    audio_dir = run_dir / "audio"
    for d in [frames_dir, clips_dir, audio_dir]:
        d.mkdir(parents=True, exist_ok=True)

    clips = []
    total_steps = len(item["script"])

    for s_idx, text in enumerate(item["script"]):
        mp3_p = audio_dir / f"step_{s_idx}.mp3"
        await edge_tts.Communicate(text, VOICE_NATIVE, rate="-10%").save(str(mp3_p))

        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
            capture_output=True, text=True, check=True
        )
        dur = float(r.stdout.strip())

        frame_p = frames_dir / f"frame_{s_idx}.png"
        render_idiom_frame(item, s_idx, total_steps, str(frame_p))

        clip_p = clips_dir / f"clip_{s_idx}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(frame_p), "-i", str(mp3_p),
            "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-preset", "fast", "-t", f"{dur:.3f}", str(clip_p)
        ], check=True, capture_output=True)

        clips.append(clip_p)

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_v = run_dir / "idioms_slang_reel.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(final_v)], check=True, capture_output=True)
    return final_v

async def run_idiom_generation(idx=0):
    item = IDIOMS[idx % len(IDIOMS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Idioms & Slang] Generating Reel for: '{item['idiom']}'...")
    final_v = await assemble_idiom_reel(item, run_dir)

    meta = {
        "title": f"What does '{item['idiom']}' mean? 🔥 English Idioms Decoded",
        "description": f"Learn the real meaning, history, and natural usage of the English idiom '{item['idiom']}'. Follow for daily idioms and slang! 🧠📚",
        "idiom": item["idiom"]
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Idioms & Slang] Video saved: {final_v}")
    return final_v, meta
