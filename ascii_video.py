#!/usr/bin/env python3
"""
ASCII Video to GreyHack Script Converter
Converts an MP4 video to ASCII art and outputs a .src GreyHack script file.

Usage: python ascii_video.py <video_file.mp4> [--width WIDTH] [--output OUTPUT]
"""

import cv2
import numpy as np
import sys
import os
import argparse

# ASCII characters from light to dark (so dark background = whitespace)
ASCII_CHARS_DETAILED = " .:-=+*#%@"
ASCII_CHARS_SIMPLE = " .,;:+*?%$#@"
ASCII_CHARS_BLOCKS = " ░▒▓█"

# Extended unicode character sets for more depth (no quotes, backslashes, or forward slashes)
ASCII_CHARS_UNICODE = " .'`^,:;Il!i><~+_-?][}{1)(|tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
ASCII_CHARS_UNICODE_EXTENDED = " .`'^,:;-~=+<>()[]{}|?!ilIjtfr1xnuvczJCLUYXZO0Qoahkbdpqwm*WM#%&@$█"
ASCII_CHARS_SHADING = " ·˙‥…⁘⁙░▒▓█▪▫▬▭▮▯"
ASCII_CHARS_DENSE = " .'`^,:;~-_+<>i!lI?|()1{}[]rcvunxzjftLCJUYXZO0QoahkbdpqwmMW*#%&@$▓█"


def resize_frame(frame, new_width):
    """Resize frame while maintaining aspect ratio adjusted for terminal characters."""
    height, width = frame.shape[:2]
    # Characters are typically ~2x taller than wide, so we adjust
    aspect_ratio = height / width
    new_height = int(new_width * aspect_ratio * 0.55)
    return cv2.resize(frame, (new_width, new_height))


def frame_to_ascii(frame, ascii_chars=ASCII_CHARS_DETAILED):
    """Convert a single frame to ASCII art."""
    # Convert to grayscale if needed
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    
    # Normalize pixel values to ASCII character indices
    num_chars = len(ascii_chars)
    ascii_indices = (gray / 256 * num_chars).astype(int)
    ascii_indices = np.clip(ascii_indices, 0, num_chars - 1)
    
    # Convert to ASCII string
    ascii_frame = "\n".join(
        "".join(ascii_chars[pixel] for pixel in row)
        for row in ascii_indices
    )
    
    return ascii_frame


def process_video(video_path, width, ascii_chars, skip=1):
    """Process all frames of the video into ASCII art."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Processing video: {total_frames} frames at {fps:.2f} FPS")
    print(f"Output width: {width} characters")
    print(f"Frame skip: every {skip} frame(s) (keeping ~{total_frames // skip} frames)")
    print()
    
    frames = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Skip frames based on skip parameter
        if frame_count % skip != 0:
            continue
        
        # Resize and convert to ASCII
        resized = resize_frame(frame, width)
        ascii_frame = frame_to_ascii(resized, ascii_chars)
        frames.append(ascii_frame)
        
        # Progress indicator
        progress = frame_count / total_frames * 100
        print(f"\rProcessing frames: {progress:.1f}% ({len(frames)} kept)", end="", flush=True)
    
    cap.release()
    print("\nFrame processing complete!")
    
    return frames, fps


def generate_greyhack_script(frames, output_path, wait_time=0.1):
    """Generate a GreyHack .src script file from ASCII frames."""
    print(f"\nGenerating GreyHack script...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Start the infinite loop
        f.write('while true\n')
        
        for i, frame in enumerate(frames):
            # Escape quotes by doubling them (MiniScript syntax)
            escaped_frame = frame.replace('"', '""')
            
            # Write the print statement with multiline string
            f.write(f'print("{escaped_frame}")\n')
            
            # Add wait and clear_screen after each frame
            f.write(f'wait({wait_time})\n')
            # f.write('clear_screen\n')
            
            # Progress indicator
            progress = (i + 1) / len(frames) * 100
            print(f"\rWriting script: {progress:.1f}% ({i+1}/{len(frames)})", end="", flush=True)
        
        # End the infinite loop
        f.write('end while\n')
    
    print("\nScript generation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Convert MP4 video to ASCII art GreyHack script (.src)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ascii_video.py video.mp4
  python ascii_video.py video.mp4 --width 80
  python ascii_video.py video.mp4 --skip 3                    # keep every 3rd frame
  python ascii_video.py video.mp4 --wait 0.05                 # faster playback
  python ascii_video.py video.mp4 --style extended            # max detail unicode
  python ascii_video.py video.mp4 -w 60 -k 5 -t 0.2 -o out.src

Styles (by detail level):
  simple    - 11 basic ASCII chars
  detailed  - 10 ASCII chars  
  blocks    - 5 block elements (░▒▓█)
  shading   - 17 shading/dot chars
  unicode   - 68 chars (recommended)
  extended  - 66 chars with blocks
  dense     - 68 chars (max detail)
        """
    )
    
    parser.add_argument("video", help="Path to the MP4 video file")
    parser.add_argument("--width", "-w", type=int, default=80,
                        help="Width in characters (default: 80)")
    parser.add_argument("--skip", "-k", type=int, default=1,
                        help="Process every Nth frame (default: 1, no skipping)")
    parser.add_argument("--wait", "-t", type=float, default=0.1,
                        help="Wait time between frames in seconds (default: 0.1)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output .src file path (default: <video_name>.src)")
    parser.add_argument("--style", "-s", 
                        choices=["detailed", "simple", "blocks", "unicode", "extended", "shading", "dense"],
                        default="unicode", help="Character style (default: unicode)")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.video):
        print(f"Error: File not found: {args.video}")
        sys.exit(1)
    
    # Set output path
    if args.output:
        output_path = args.output
    else:
        base_name = os.path.splitext(os.path.basename(args.video))[0]
        output_path = f"{base_name}.src"
    
    # Select ASCII character set
    ascii_styles = {
        "detailed": ASCII_CHARS_DETAILED,
        "simple": ASCII_CHARS_SIMPLE,
        "blocks": ASCII_CHARS_BLOCKS,
        "unicode": ASCII_CHARS_UNICODE,
        "extended": ASCII_CHARS_UNICODE_EXTENDED,
        "shading": ASCII_CHARS_SHADING,
        "dense": ASCII_CHARS_DENSE
    }
    ascii_chars = ascii_styles[args.style]
    
    print("=" * 50)
    print("  ASCII Video to GreyHack Script Converter")
    print("=" * 50)
    print(f"Video file: {args.video}")
    print(f"Output file: {output_path}")
    print(f"Width: {args.width} characters")
    print(f"Frame skip: {args.skip}")
    print(f"Wait time: {args.wait}s")
    print(f"Style: {args.style} ({len(ascii_chars)} characters)")
    print("=" * 50)
    print()
    
    # Process video
    frames, fps = process_video(args.video, args.width, ascii_chars, args.skip)
    
    if not frames:
        print("Error: No frames could be extracted from the video.")
        sys.exit(1)
    
    # Generate the GreyHack script
    generate_greyhack_script(frames, output_path, args.wait)
    
    # Summary
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print()
    print("=" * 50)
    print("  Done!")
    print("=" * 50)
    print(f"Frames: {len(frames)}")
    print(f"Output: {output_path}")
    print(f"Size: {file_size:.2f} MB")
    print("=" * 50)


if __name__ == "__main__":
    main()
