# ASCII Art, GIF & Video Generator

A single-file web tool that converts images, GIF animations, and videos into ASCII art — entirely in the browser, with no backend and no external dependencies.

![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Vanilla JS](https://img.shields.io/badge/JavaScript-Vanilla-yellow)
![Single File](https://img.shields.io/badge/build-single%20HTML%20file-blue)

## Features

- **Images, GIFs, and video** — supports PNG/JPG/GIF/MP4/WEBM via drag-and-drop or file picker
- **Built-in GIF decoder** — a custom LZW decoder implementation with no third-party libraries (handles Graphic Control Extensions, local/global color tables, and frame disposal methods)
- **Flexible character palette** — 8 built-in presets (blocks, hearts, dots, "matrix" style, etc.) or a custom character set
- **Render controls**:
  - width/height in characters, with automatic aspect-ratio-based height
  - brightness and contrast
  - colored output (per-character `rgb()` in HTML) or monochrome
  - single-character fill mode (for a "pixel art" look)
- **Playback controls** for video and GIF: play/pause, looping, timestamp/frame counter
- **Export options**:
  - copy the current frame to the clipboard
  - save the current frame as `.txt`
  - export a **standalone Python script** that plays the animation in a terminal with ANSI colors (all frames are serialized to JSON, compressed with GZIP, and embedded as Base64 directly in the script)

## Usage

1. Open `index.html` in any modern browser (Chrome, Firefox, Edge).
2. Drag a file into the drop zone or click it to browse.
3. Adjust the settings: character set, dimensions, brightness/contrast, color.
4. For video/GIF, use the playback controls to start or stop the animation.
5. Export the result using the buttons below the controls.

No installation or build step required — it's a single self-contained `.html` file with CSS and JavaScript inline.

## Python export

The **"Download Python (ANSI)"** button generates a script that:

- for a static image — prints a single ASCII frame with ANSI true-color escape codes (`\x1b[38;2;R;G;Bm`);
- for GIF/video — runs every frame through a canvas, encodes them as JSON → GZIP → Base64, and embeds the result in the script. On launch, the script decompresses the data and plays the animation in the terminal at a frame rate derived from the source (for GIFs) or a fixed 15 FPS (for video).

Run it with:

```bash
python3 ascii_animation.py
```

The script relies only on the Python standard library (`gzip`, `base64`, `json`, `time`, `os`) — no extra packages needed.

## Technical details

| Component | Implementation |
|---|---|
| GIF decoding | Custom `EmbeddedGifDecoder` class (header parsing, LZW, color tables, frame disposal) |
| Video frame extraction | `HTMLVideoElement` + `seeked` events + `<canvas>` |
| ASCII rendering | Pixel sampling via `CanvasRenderingContext2D.getImageData`, brightness via the luma formula (`0.2126R + 0.7152G + 0.0722B`) |
| Data compression | `CompressionStream('gzip')` (Compression Streams API) |
| Terminal color | ANSI true-color escape sequences `\x1b[38;2;r;g;bm` |

## Browser requirements & limitations

- Exporting animations requires support for the **Compression Streams API** (Chrome/Edge 80+, Firefox 113+, Safari 16.4+).
- Clipboard copy uses `navigator.clipboard`, falling back to `document.execCommand('copy')` in non-secure contexts.
- Large videos are exported frame-by-frame via `seeked` events, which can take a while — progress is shown on the button itself.


