# ASCII Video to GreyHack Script Converter

Convert MP4 videos into ASCII art animations that can be played inside GreyHack. 

## What is this?

This tool converts video files (MP4) into ASCII art frame-by-frame and generates GreyHack-compatible `.src` script files. The resulting scripts can be compiled and run inside GreyHack to display animated ASCII videos on in-game terminals.

## Features

- Converts MP4 videos to ASCII art animations
- Multiple ASCII character styles (from simple to high-detail unicode)
- Automatic file splitting (GreyHack has a 160,000 character limit per file)
- Configurable frame skipping for performance optimization
- Adjustable playback speed
- Customizable output width

## Requirements

- Python 3.x
- OpenCV (`cv2`)
- NumPy

## Basic Usage

```bash
python ascii_video.py video.mp4
```

This will create a folder named after your video containing:
- `video.src` - Main player script (compile and run this)

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--width` | `-w` | Width in characters | 80 |
| `--skip` | `-k` | Process every Nth frame | 1 (no skipping) |
| `--wait` | `-t` | Wait time between frames (seconds) | 0.1 |
| `--output` | `-o` | Output folder name | `<video_name>` |
| `--path` | `-p` | GreyHack path prefix for imports | `/home/alex` |
| `--style` | `-s` | Character style (see below) | `unicode` |

## Character Styles

Choose a style based on desired detail level and performance:

| Style | Characters | Description |
|-------|-----------|-------------|
| `simple` | 11 | Basic ASCII chars: ` .,;:+*?%$#@` |
| `detailed` | 10 | Classic ASCII: ` .:-=+*#%@` |
| `blocks` | 5 | Block elements: ` ░▒▓█` |
| `shading` | 17 | Shading/dot chars with unicode symbols |
| `unicode` | 68 | Recommended - good balance of detail |
| `extended` | 66 | Unicode with blocks |
| `dense` | 68 | Maximum detail |

## Output Structure

After running the script, you'll get a folder like this:

```
myvideo/
├── myvideo.src     # Main player script - RUN THIS
├── data0.src       # Frame data (first chunk)
├── data1.src       # Frame data (second chunk, if needed)
└── ...
```

