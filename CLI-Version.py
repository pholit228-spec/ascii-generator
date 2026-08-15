#It's Python version ASCII-Generator'@
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import gzip
import base64
import json
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

FONT_ASPECT_RATIO = 0.5

PRESETS = {
    '1': ('blocks', '█'),
    '2': ('hearts', '♥'),
    '3': ('dots', '●'),
    '4': ('squares', '■'),
    '5': ('standard', '@%#*+=-:. '),
    '6': ('dense', '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrft/\\|()1{}[]?-_+~<>i!lI;:,"^`\'. '),
    '7': ('binary', '10 '),
    '8': ('minimal', '#.- ')
}

def calculate_contrast_factor(contrast):
    return (259 * (contrast + 255)) / (255 * (259 - contrast))

def apply_brightness_contrast(val, brightness, contrast_factor):
    n = val + brightness
    n = contrast_factor * (n - 128) + 128
    return max(0, min(255, int(round(n))))

def pil_image_to_ansi_frame(img, width, height, chars, brightness, contrast, single_char):
    # Using LANCZOS for smoothing or NEAREST for sharp pixel art style
    img = img.convert('RGB').resize((width, height), Image.Resampling.LANCZOS)
    pixels = img.load()
    contrast_factor = calculate_contrast_factor(contrast)
    char_list = list(chars)
    char_len = len(char_list)

    lines = []
    for y in range(height):
        line = ""
        cur_color = None
        buf = ""

        for x in range(width):
            r, g, b = pixels[x, y]
            r = apply_brightness_contrast(r, brightness, contrast_factor)
            g = apply_brightness_contrast(g, brightness, contrast_factor)
            b = apply_brightness_contrast(b, brightness, contrast_factor)

            if single_char:
                ch = char_list[0] if char_list else '█'
            else:
                br = 0.2126 * r + 0.7152 * g + 0.0722 * b
                idx = min(char_len - 1, int((br / 256.0) * char_len))
                ch = char_list[idx]

            color_key = f"{r};{g};{b}"
            if color_key != cur_color:
                if cur_color is not None:
                    line += f"\x1b[38;2;{cur_color}m{buf}"
                cur_color = color_key
                buf = ch
            else:
                buf += ch

        if cur_color is not None:
            line += f"\x1b[38;2;{cur_color}m{buf}"
        line += "\x1b[0m"
        lines.append(line)

    return lines

def compress_frames(all_frames):
    json_bytes = json.dumps(all_frames).encode('utf-8')
    compressed = gzip.compress(json_bytes)
    return base64.b64encode(compressed).decode('ascii')

def build_static_script(ansi_lines):
    lines_repr = ",\n".join([f"    {repr(l)}" for l in ansi_lines])
    return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

lines = [
{lines_repr}
]

def main():
    import sys, os
    if sys.platform == "win32":
        os.system('')
    for l in lines:
        print(l)

if __name__ == "__main__":
    main()
"""

def build_anim_script(b64_data, fps):
    return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, sys, os, gzip, base64, json

FPS = {fps}
FRAME_DELAY = 1.0 / FPS
DATA = "{b64_data}"

def load_frames():
    raw_gzip = base64.b64decode(DATA)
    json_bytes = gzip.decompress(raw_gzip)
    return json.loads(json_bytes.decode('utf-8'))

def main():
    if sys.platform == "win32":
        os.system('')
    sys.stdout.write("Unpacking frames...\\r")
    sys.stdout.flush()
    frames = load_frames()
    sys.stdout.write("\\033[2J\\033[H\\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            for frame in frames:
                t0 = time.time()
                output = "\\033[H\\033[0J" + "\\n".join(frame) + "\\033[0m\\n"
                sys.stdout.write(output)
                sys.stdout.flush()
                delta = time.time() - t0
                time.sleep(max(0.0, FRAME_DELAY - delta))
    except KeyboardInterrupt:
        sys.stdout.write("\\033[?25h\\033[0m\\n")
        sys.stdout.flush()
        print("Playback stopped.")

if __name__ == "__main__":
    main()
"""

def main():
    print("=" * 50)
    print("      ASCII / ANSI Generator (Interactive CLI)")
    print("=" * 50)

    # 1. File Input (cleans quotes if drag-and-dropped into terminal)
    file_input = input("\n📁 Enter file path (or drag and drop here): ").strip("'\" ")
    if not file_input or not os.path.exists(file_input):
        print("❌ Error: File not found!")
        return

    # 2. Width Input
    width_val = input("📐 Width in characters [default 80]: ").strip()
    width = int(width_val) if width_val.isdigit() else 80

    # 3. Preset Selection
    print("\nSelect character preset:")
    print("  1 — █ (Solid Block, default)")
    print("  2 — ♥ (Hearts)")
    print("  3 — ● (Dots)")
    print("  4 — ■ (Squares)")
    print("  5 — @%#*+=-:.  (Standard ASCII)")
    print("  6 — Detailed ASCII (70 characters)")
    print("  7 — 10 (Matrix / Binary)")
    print("  8 — #.- (Minimalist)")
    print("  C — Enter custom character set")
    
    preset_choice = input("Preset [1-8/C, default 1]: ").strip().lower()
    
    single_char = False
    if preset_choice == 'c':
        chars = input("Enter custom characters: ") or '█'
    elif preset_choice in PRESETS:
        chars = PRESETS[preset_choice][1]
        if preset_choice in ['1', '2', '3', '4']:
            single_char = True
    else:
        chars = '█'
        single_char = True

    # 4. Image Corrections & Settings
    br_val = input("💡 Brightness (-100...100) [0]: ").strip()
    brightness = int(br_val) if br_val.replace('-', '').isdigit() else 0

    ct_val = input("☯️ Contrast (-100...100) [0]: ").strip()
    contrast = int(ct_val) if ct_val.replace('-', '').isdigit() else 0

    # Format Detection
    ext = os.path.splitext(file_input)[1].lower()
    is_video = ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    is_gif = ext == '.gif'

    fps = 15
    if is_video or is_gif:
        fps_val = input("⏱ Animation FPS [15]: ").strip()
        if fps_val.isdigit():
            fps = int(fps_val)

    # Resolution Calculation preserving Aspect Ratio
    if is_video:
        if not HAS_OPENCV:
            print("❌ Error: Please install opencv-python for video support: pip install opencv-python")
            return
        cap = cv2.VideoCapture(file_input)
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
    else:
        with Image.open(file_input) as img:
            orig_w, orig_h = img.size

    ratio = orig_h / orig_w
    height = max(1, int(round(width * ratio * FONT_ASPECT_RATIO)))

    out_name = f"ascii_{os.path.splitext(os.path.basename(file_input))[0]}.py"
    out_path = os.path.join(os.path.dirname(os.path.abspath(file_input)), out_name)

    print(f"\n⚙️ Processing file... ({orig_w}x{orig_h} -> {width}x{height} chars)")

    # Frame Generation
    if is_video:
        cap = cv2.VideoCapture(file_input)
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        step = max(1, int(orig_fps / fps))

        frames = []
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % step == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                ansi_frame = pil_image_to_ansi_frame(pil_img, width, height, chars, brightness, contrast, single_char)
                frames.append(ansi_frame)
                print(f"Frame {len(frames)}...", end="\r")
            frame_idx += 1
        cap.release()
        print(f"\n📦 Compressing {len(frames)} frames...")
        b64 = compress_frames(frames)
        code = build_anim_script(b64, fps)

    elif is_gif:
        frames = []
        with Image.open(file_input) as img:
            for i in range(img.n_frames):
                img.seek(i)
                ansi_frame = pil_image_to_ansi_frame(img, width, height, chars, brightness, contrast, single_char)
                frames.append(ansi_frame)
                print(f"Frame {i+1}/{img.n_frames}...", end="\r")
        print(f"\n📦 Compressing {len(frames)} frames...")
        b64 = compress_frames(frames)
        code = build_anim_script(b64, fps)

    else:
        with Image.open(file_input) as img:
            ansi_lines = pil_image_to_ansi_frame(img, width, height, chars, brightness, contrast, single_char)
        code = build_static_script(ansi_lines)

    # Output Saving
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code)

    os.chmod(out_path, 0o755)
    print(f"\n✅ Done! File saved to: {out_path}")

if __name__ == "__main__":
    main()
