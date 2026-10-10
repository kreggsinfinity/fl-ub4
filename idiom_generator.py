"""
IDIOMS & SLANG PODCAST - 16:9 FULL HD (1920x1080) VIDEO GENERATOR
Theme: Neon Pop Late Night Radio Studio
Visuals: Neon Purple Shockmount Mic + 28-Bar Magenta/Cyan Dynamic Equalizer + Single-Line Highlighted Subtitles
"""
import os, sys, json, math, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts

if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

load_dotenv()

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
SUBFRAMES_PER_SEC = 2

NEON_MAGENTA = (236, 72, 153)
NEON_PURPLE = (168, 85, 247)
NEON_CYAN = (6, 182, 212)
NEON_LIME = (132, 204, 22)
NEON_YELLOW = (250, 204, 21)
WHITE = (255, 255, 255)
DARK_BG = (12, 10, 24)
CARD_BG = (22, 16, 42)
CARD_BORDER = (88, 48, 140)
MUTED_TEXT = (180, 165, 210)

EMMA_VOICE = "en-US-AvaNeural"
ANDREW_VOICE = "en-US-AndrewNeural"
VOICE_RATE = "-15%"

TOPICS = [
    {
        "topic": "The Story Behind 'Bite The Bullet' and How To Use It",
        "idiom": "BITE THE BULLET",
        "keyword": "BULLET",
        "sub": "FACE DIFFICULTIES WITH COURAGE"
    },
    {
        "topic": "Why Do Actors Say 'Break A Leg' Instead of Good Luck?",
        "idiom": "BREAK A LEG",
        "keyword": "LUCK",
        "sub": "POPULAR THEATRE SUPERSTITIONS"
    },
    {
        "topic": "Understanding 'Hit The Sack' and Daily Sleep Slang",
        "idiom": "HIT THE SACK",
        "keyword": "SLEEP",
        "sub": "CASUAL AMERICAN NIGHTTIME SLANG"
    },
    {
        "topic": "What Does 'Cut Corners' Mean in Work and Life?",
        "idiom": "CUT CORNERS",
        "keyword": "QUALITY",
        "sub": "BUSINESS AND EVERYDAY IDIOMS"
    }
]

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/trebucbd.ttf" if bold else "C:/Windows/Fonts/trebuc.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def clean_text(text):
    text = re.sub(r'\b(mm+|um+|uh+|ah+)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_script_ai(topic_item, target_turns=6):
    prompt = f"""Write {target_turns} turns of a slow, clear English podcast between Emma and Andrew.
Topic: {topic_item['topic']}
Idiom: {topic_item['idiom']}

RULES:
- Dialogue alternating between Host1 (Emma) and Host2 (Andrew)
- Each turn MUST be 2-3 short, clear sentences (18-28 words)
- Explain what the idiom really means, why the literal translation is funny or wrong, and provide a realistic conversational example
- Wrap exactly 1 key learning word per turn in **asterisks**
- Return as clean JSON array only:
[{{"speaker":"Host1","text":"..."}},{{"speaker":"Host2","text":"..."}}]"""

    key = os.getenv("POLLINATIONS_API_KEY")
    if key:
        try:
            resp = requests.post("https://gen.pollinations.ai/v1/chat/completions", json={
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You write engaging, natural English learning podcast dialogue about idioms and slang. Wrap 1 key word per turn in **asterisks**."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8
            }, headers={"Authorization": f"Bearer {key}"}, timeout=60)
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"].strip()
                if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
                script = json.loads(raw)
                if isinstance(script, list) and len(script) > 0:
                    for i, turn in enumerate(script):
                        turn["speaker"] = "Host1" if i % 2 == 0 else "Host2"
                        turn["text"] = clean_text(turn["text"])
                        if "**" not in turn["text"]:
                            words = turn["text"].split()
                            if len(words) > 2:
                                idx = len(words) // 2
                                words[idx] = f"**{words[idx]}**"
                                turn["text"] = " ".join(words)
                    return script[:target_turns]
        except Exception as e:
            print(f"[script] AI note: {e}, using curated fallback.")

    return [
        {"speaker": "Host1", "text": f"Welcome back everyone! Today we are decoding the popular idiom: **{topic_item['idiom']}**."},
        {"speaker": "Host2", "text": f"Don't translate it literally! It simply means to face an inevitable challenge with **bravery**."},
        {"speaker": "Host1", "text": f"For example, if you dislike going to the dentist, you just have to bite the **bullet** and go."},
        {"speaker": "Host2", "text": f"Using idioms like this in your conversations will instantly make you sound like a **native** speaker!"}
    ][:target_turns]

async def generate_audio_files(turns, run_dir):
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_list = []
    for i, turn in enumerate(turns):
        mp3_p = audio_dir / f"turn_{i:03d}.mp3"
        spoken = re.sub(r'\*\*(.*?)\*\*', r'\1', turn["text"])
        voice = EMMA_VOICE if turn["speaker"] == "Host1" else ANDREW_VOICE
        comm = edge_tts.Communicate(spoken, voice, rate=VOICE_RATE)
        await comm.save(str(mp3_p))

        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                capture_output=True, text=True, check=True
            )
            duration = float(r.stdout.strip())
        except:
            duration = 5.0
        audio_list.append({"path": str(mp3_p), "duration": duration, "speaker": turn["speaker"]})
    return audio_list

def draw_neon_mic_setup(draw, center_x, center_y, is_active, host_label):
    # Shockmount outer neon ring
    ring_color = NEON_MAGENTA if is_active else (60, 40, 80)
    draw.ellipse([(center_x - 75, center_y - 75), (center_x + 75, center_y + 75)], outline=ring_color, width=4)
    # Suspension elastic bands
    for angle in [30, 60, 120, 150, 210, 240, 300, 330]:
        rad = math.radians(angle)
        x1 = center_x + int(40 * math.cos(rad))
        y1 = center_y + int(40 * math.sin(rad))
        x2 = center_x + int(72 * math.cos(rad))
        y2 = center_y + int(72 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(120, 70, 150), width=2)

    # Microphone body
    mic_c = (35, 20, 50) if not is_active else (70, 25, 80)
    draw.rounded_rectangle([(center_x - 32, center_y - 90), (center_x + 32, center_y + 40)], radius=18, fill=mic_c, outline=NEON_PURPLE if is_active else (70, 50, 95), width=3)
    # Metal mesh texture
    for my in range(center_y - 80, center_y - 10, 10):
        draw.line([(center_x - 26, my), (center_x + 26, my)], fill=NEON_CYAN if is_active else (80, 65, 110), width=2)

    # Stem & Boom mount
    draw.rectangle([(center_x - 6, center_y + 75), (center_x + 6, center_y + 140)], fill=(45, 30, 65))
    draw.ellipse([(center_x - 50, center_y + 130), (center_x + 50, center_y + 155)], fill=(25, 16, 40), outline=ring_color, width=2)

    # Host Plate
    f_p = load_font(22, bold=True)
    plate_c = NEON_MAGENTA if is_active else (30, 20, 50)
    txt_c = WHITE if is_active else MUTED_TEXT
    draw.rounded_rectangle([(center_x - 85, center_y + 160), (center_x + 85, center_y + 195)], radius=10, fill=plate_c, outline=NEON_PURPLE, width=2)
    tag = f"🎙️ {host_label}" + (" (ON AIR)" if is_active else "")
    draw.text((center_x, center_y + 177), tag, fill=txt_c, font=f_p, anchor="mm")

def draw_neon_waveform(draw, center_x, center_y, width, height, sub_idx, is_speaking):
    num_bars = 28
    bar_w = 9
    gap = (width - (num_bars * bar_w)) // (num_bars - 1)

    # Deck Frame
    draw.rounded_rectangle([(center_x - width//2 - 20, center_y - height//2 - 12),
                            (center_x + width//2 + 20, center_y + height//2 + 12)],
                           radius=18, fill=(18, 12, 35), outline=NEON_PURPLE, width=2)

    f_hud = load_font(18, bold=True)
    draw.text((center_x, center_y - height//2 - 1), "⚡ NEON SPECTRUM AUDIO DECK ⚡", fill=NEON_CYAN, font=f_hud, anchor="mm")

    start_x = center_x - width//2
    for b in range(num_bars):
        if is_speaking:
            phase = sub_idx * 0.95 + b * 0.38
            wave = (math.sin(phase) + 1.0) * 0.5
            bar_h = int(14 + wave * (height - 28))
        else:
            bar_h = 10

        bx = start_x + b * (bar_w + gap)
        by = center_y + height//2 - 8 - bar_h

        # Magenta to Cyan gradient
        ratio = b / num_bars
        rc = int(NEON_MAGENTA[0] * (1 - ratio) + NEON_CYAN[0] * ratio)
        gc = int(NEON_MAGENTA[1] * (1 - ratio) + NEON_CYAN[1] * ratio)
        bc = int(NEON_MAGENTA[2] * (1 - ratio) + NEON_CYAN[2] * ratio)
        draw.rounded_rectangle([(bx, by), (bx + bar_w, center_y + height//2 - 8)], radius=4, fill=(rc, gc, bc))

def render_podcast_subframe(topic_item, turn, turn_idx, sub_idx, total_subframes, elapsed, total_dur, out_path):
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), DARK_BG)
    draw = ImageDraw.Draw(canvas)

    # Cyber Neon Studio gradient background
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        r = int(14 + ratio * 18)
        g = int(10 + ratio * 8)
        b = int(28 + ratio * 20)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b, 255))

    # Background neon geometric grid lines
    for gx in range(100, VIDEO_WIDTH, 180):
        draw.line([(gx, 120), (gx, 650)], fill=(32, 22, 58), width=1)
    for gy in range(150, 650, 100):
        draw.line([(80, gy), (1840, gy)], fill=(32, 22, 58), width=1)

    # Top Header Deck
    # Left: Channel badge
    draw.rounded_rectangle([(60, 36), (560, 106)], radius=16, fill=CARD_BG, outline=NEON_MAGENTA, width=2)
    f_brand = load_font(28, bold=True)
    draw.text((310, 71), "💥 IDIOMS & SLANG RADIO", fill=WHITE, font=f_brand, anchor="mm")

    # Center: Idiom Focus Pill
    draw.rounded_rectangle([(590, 36), (1450, 106)], radius=16, fill=(35, 18, 55), outline=NEON_CYAN, width=2)
    f_scen = load_font(26, bold=True)
    draw.text((1020, 71), f"🔥 IDIOM: \"{topic_item['idiom']}\"", fill=NEON_YELLOW, font=f_scen, anchor="mm")

    # Right: Live On Air Pill
    draw.rounded_rectangle([(1480, 36), (1860, 106)], radius=16, fill=(45, 12, 38), outline=NEON_MAGENTA, width=3)
    f_air = load_font(26, bold=True)
    dot_color = NEON_MAGENTA if (sub_idx % 2 == 0) else (100, 20, 60)
    draw.ellipse([(1515, 61), (1535, 81)], fill=dot_color)
    draw.text((1685, 71), "NEON PODCAST", fill=WHITE, font=f_air, anchor="mm")

    # Visual Studio Centerpiece: Dual Shockmount Mics & Center Neon Waveform
    is_emma = (turn["speaker"] == "Host1")
    is_andrew = not is_emma

    # Left Mic: Emma
    draw_neon_mic_setup(draw, center_x=340, center_y=360, is_active=is_emma, host_label="EMMA")

    # Center Equalizer Deck
    draw_neon_waveform(draw, center_x=960, center_y=350, width=560, height=140, sub_idx=sub_idx, is_speaking=True)

    # Center Idiom Explanation Card
    draw.rounded_rectangle([(680, 460), (1240, 540)], radius=14, fill=CARD_BG, outline=CARD_BORDER, width=2)
    f_top = load_font(24, bold=True)
    draw.text((960, 500), f"Meaning: {topic_item['sub']}", fill=NEON_CYAN, font=f_top, anchor="mm")

    # Right Mic: Andrew
    draw_neon_mic_setup(draw, center_x=1580, center_y=360, is_active=is_andrew, host_label="ANDREW")

    # LOWER THIRD: SLEEK SINGLE-LINE SUBTITLE DISPLAY WITH WORD-BY-WORD HIGHLIGHTING
    draw.rounded_rectangle([(100, 680), (1820, 930)], radius=24, fill=(18, 14, 34, 240), outline=NEON_MAGENTA, width=3)

    # Speaker Tag Pill
    active_name = "EMMA (Host)" if is_emma else "ANDREW (Host)"
    draw.rounded_rectangle([(140, 650), (450, 705)], radius=12, fill=NEON_MAGENTA)
    f_spk = load_font(26, bold=True)
    draw.text((295, 677), f"🎙️ {active_name}", fill=WHITE, font=f_spk, anchor="mm")

    # Sentence & Spoken Word Highlighting
    raw_text = turn["text"]
    words_clean = [re.sub(r'[\*\*\.]', '', w).strip() for w in raw_text.split() if w.strip()]
    if not words_clean:
        words_clean = ["Listen", "carefully"]

    active_word_idx = min(len(words_clean) - 1, int((sub_idx / max(1, total_subframes)) * len(words_clean)))

    f_sub = load_font(42, bold=True)
    rendered_words = raw_text.split()

    line_words = []
    lines = []
    max_w = 1600
    curr_w = 0

    for w_i, w in enumerate(rendered_words):
        clean_w = re.sub(r'\*\*(.*?)\*\*', r'\1', w)
        wb = draw.textbbox((0, 0), clean_w + " ", font=f_sub)
        w_len = wb[2] - wb[0]
        if curr_w + w_len > max_w and line_words:
            lines.append(line_words)
            line_words = [(w_i, w, clean_w, w_len)]
            curr_w = w_len
        else:
            line_words.append((w_i, w, clean_w, w_len))
            curr_w += w_len
    if line_words:
        lines.append(line_words)

    y_start = 740 if len(lines) == 1 else 725
    line_h = 55
    for l_idx, line in enumerate(lines[:2]):
        total_line_w = sum(item[3] for item in line)
        start_x = 960 - total_line_w // 2
        curr_x = start_x
        y_pos = y_start + l_idx * line_h

        for (w_i, raw_w, clean_w, w_len) in line:
            is_active_word = (w_i == active_word_idx)
            is_key_word = ("**" in raw_w)

            if is_active_word:
                # Fluorescent Yellow active karaoke pill
                draw.rounded_rectangle([(curr_x - 4, y_pos - 6), (curr_x + w_len - 2, y_pos + 46)], radius=8, fill=NEON_YELLOW)
                draw.text((curr_x, y_pos), clean_w, fill=(18, 12, 28), font=f_sub)
            elif is_key_word:
                draw.text((curr_x, y_pos), clean_w, fill=NEON_CYAN, font=f_sub)
            else:
                draw.text((curr_x, y_pos), clean_w, fill=WHITE, font=f_sub)
            curr_x += w_len

    # Tip Ribbon inside the Lower Third
    f_tip = load_font(22, bold=False)
    draw.text((960, 885), "💡 Native Secret: Idioms are used in casual business meetings, movies, and daily chat!", fill=MUTED_TEXT, font=f_tip, anchor="mm")

    # Bottom Progress Deck
    draw.line([(0, 1020), (VIDEO_WIDTH, 1020)], fill=(45, 28, 65), width=3)
    ratio = min(1.0, elapsed / max(1.0, total_dur))
    draw.line([(0, 1020), (int(VIDEO_WIDTH * ratio), 1020)], fill=NEON_CYAN, width=6)

    f_bot = load_font(24, bold=False)
    draw.text((70, 1050), "Idioms & Slang • Cultural English • Natural Everyday Speaking", fill=MUTED_TEXT, font=f_bot, anchor="lm")
    time_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d} / {int(total_dur // 60):02d}:{int(total_dur % 60):02d}"
    draw.text((1850, 1050), time_str, fill=NEON_MAGENTA, font=f_bot, anchor="rm")

    canvas.convert("RGB").save(out_path, quality=90)

def assemble_video(topic_item, turns, audio_list, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    frames_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    total_dur = sum(a["duration"] for a in audio_list)
    elapsed = 0.0
    clips = []

    for i, (turn, audio) in enumerate(zip(turns, audio_list)):
        dur = audio["duration"]
        subframes_count = max(8, int(dur * SUBFRAMES_PER_SEC))

        turn_frames_dir = frames_dir / f"turn_{i:03d}"
        turn_frames_dir.mkdir(parents=True, exist_ok=True)

        for s_idx in range(subframes_count):
            frame_p = turn_frames_dir / f"frame_{s_idx:04d}.png"
            sub_elapsed = elapsed + (s_idx / subframes_count) * dur
            render_podcast_subframe(
                topic_item, turn, i, s_idx, subframes_count,
                sub_elapsed, total_dur, str(frame_p)
            )

        clip_p = clips_dir / f"clip_{i:03d}.mp4"
        input_pattern = str(turn_frames_dir / "frame_%04d.png")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(SUBFRAMES_PER_SEC),
            "-i", input_pattern,
            "-i", audio["path"],
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-preset", "veryfast",
            str(clip_p)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        clips.append(clip_p)
        elapsed += dur

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_video = run_dir / "idioms_slang_podcast_final.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(final_video)], check=True, capture_output=True)
    return final_video, total_dur

async def run_idiom_generation(topic_idx=0, turns_count=4):
    topic_item = TOPICS[topic_idx % len(TOPICS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Idioms Podcast] Generating 16:9 Neon Studio: '{topic_item['idiom']}' ({turns_count} turns)...")
    turns = generate_script_ai(topic_item, target_turns=turns_count)
    audio_list = await generate_audio_files(turns, run_dir)
    video_p, dur = assemble_video(topic_item, turns, audio_list, run_dir)

    meta = {
        "title": f"Master English Idioms: {topic_item['idiom']} 🎙️ Slow English Podcast",
        "description": f"Learn the real meaning and origin of '{topic_item['idiom']}'! Speak like a native with our slow English podcast lessons. Like and follow for daily videos! 🔥🎧",
        "idiom": topic_item["idiom"],
        "duration_seconds": dur
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Idioms Podcast] Video ready: {video_p}")
    return video_p, meta

if __name__ == "__main__":
    asyncio.run(run_idiom_generation(topic_idx=0, turns_count=2))
