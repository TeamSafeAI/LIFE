# Vision Server

Image capture and viewing. No database, no state.

## Tools
- **see** — capture from webcam (cv2). Saves to VISUAL/world_current.jpg, returns image.
- **screen** — capture screenshot (PIL ImageGrab). Saves to VISUAL/screen_current.jpg, returns image.
- **view** — read an image file by path. Supported: jpg, jpeg, png, gif, webp, bmp.

## How It Works
- All captures saved to VISUAL directory, returned as base64 image content blocks.
- Images over 800KB are auto-resized via PIL JPEG quality reduction (85 → 20 in steps of 10).
- cv2 and PIL are optional imports — graceful error if not installed.

## Dependencies
- `_paths.py` — VISUAL
- `cv2` (optional) — webcam capture
- `PIL` (optional) — screenshot + resize
