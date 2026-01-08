#!/usr/bin/env python3
"""
ASCII Video to GreyHack Script Converter
Converts an MP4 video to ASCII art and outputs .src GreyHack script files.
Automatically splits into multiple files if over 160,000 character limit.

Usage: python ascii_video.py <video_file.mp4> [--width WIDTH] [--output OUTPUT]
"""

import cv2
import numpy as np
import sys
import os
import argparse

# Character limit per .src file in GreyHack
MAX_CHARS_PER_FILE = 160000

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


def frame_to_variable(frame_index, frame_content):
    """Convert a frame to a MiniScript variable assignment."""
    # Escape quotes by doubling them (MiniScript syntax)
    escaped = frame_content.replace('"', '""')
    return f'f{frame_index} = "{escaped}"\n'


def split_frames_into_files(frames):
    """
    Split frames into groups that fit within the character limit.
    Returns a list of lists, where each inner list contains (frame_index, frame_content) tuples.
    """
    files = []
    current_file = []
    current_chars = 0
    
    for i, frame in enumerate(frames):
        var_str = frame_to_variable(i, frame)
        var_len = len(var_str)
        
        # Check if adding this frame would exceed the limit
        if current_chars + var_len > MAX_CHARS_PER_FILE and current_file:
            # Save current file and start a new one
            files.append(current_file)
            current_file = []
            current_chars = 0
        
        current_file.append((i, frame))
        current_chars += var_len
    
    # Don't forget the last file
    if current_file:
        files.append(current_file)
    
    return files


def generate_greyhack_scripts(frames, output_folder, video_name, wait_time=0.1, greyhack_path="/home/user"):
    """Generate GreyHack .src script files, splitting if necessary."""
    print(f"\nGenerating GreyHack scripts...")
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Split frames into files
    file_groups = split_frames_into_files(frames)
    num_files = len(file_groups)
    
    print(f"Splitting into {num_files} data file(s)...")
    
    # Generate data files
    data_files = []
    total_chars = 0
    
    for file_idx, frame_group in enumerate(file_groups):
        data_filename = f"data{file_idx}.src"
        data_path = os.path.join(output_folder, data_filename)
        data_files.append(data_filename)
        
        with open(data_path, 'w', encoding='utf-8') as f:
            file_chars = 0
            for frame_idx, frame_content in frame_group:
                var_str = frame_to_variable(frame_idx, frame_content)
                f.write(var_str)
                file_chars += len(var_str)
            
            total_chars += file_chars
            print(f"  {data_filename}: {len(frame_group)} frames, {file_chars:,} chars")
    
    # Generate main script that imports and plays
    main_path = os.path.join(output_folder, f"{video_name}.src")
    
    with open(main_path, 'w', encoding='utf-8') as f:
        # Import all data files
        f.write(f"// ASCII Video Player - {video_name}\n")
        f.write(f"// Generated with {len(frames)} frames across {num_files} data file(s)\n")
        f.write(f"// IMPORTANT: Update the path below to match your GreyHack location!\n\n")
        
        for data_file in data_files:
            f.write(f'import_code("{greyhack_path}/{video_name}/{data_file}")\n')
        
        f.write("\n")
        
        # Build the frames list
        f.write("// Build frames list\n")
        f.write("frames = []\n")
        for i in range(len(frames)):
            f.write(f"frames.push(f{i})\n")
        
        f.write("\n")
        
        # Play loop
        f.write("// Play animation\n")
        f.write("while true\n")
        f.write("  for frame in frames\n")
        f.write("    print(frame)\n")
        f.write(f"    wait({wait_time})\n")
        # f.write("    clear_screen\n") # This bugs it all out, isn't needed 
        f.write("  end for\n")
        f.write("end while\n")
    
    main_chars = os.path.getsize(main_path)
    print(f"  {video_name}.src: main player, {main_chars:,} chars")
    
    return data_files, total_chars


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
  python ascii_video.py video.mp4 -w 60 -k 5 -t 0.2 -o myvideo
  python ascii_video.py video.mp4 --path /home/me/Videos      # set GreyHack import path

Styles (by detail level):
  simple    - 11 basic ASCII chars
  detailed  - 10 ASCII chars  
  blocks    - 5 block elements (░▒▓█)
  shading   - 17 shading/dot chars
  unicode   - 68 chars (recommended)
  extended  - 66 chars with blocks
  dense     - 68 chars (max detail)

Output Structure:
  <output_folder>/
    ├── <video_name>.src    (main player - compile and run this)
    ├── data0.src           (frame data)
    ├── data1.src           (more frames if needed)
    └── ...
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
                        help="Output folder name (default: <video_name>)")
    parser.add_argument("--path", "-p", type=str, default="/home/alex",
                        help="GreyHack path prefix for import_code (default: /home/alex)")
    parser.add_argument("--style", "-s", 
                        choices=["detailed", "simple", "blocks", "unicode", "extended", "shading", "dense"],
                        default="unicode", help="Character style (default: unicode)")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.video):
        print(f"Error: File not found: {args.video}")
        sys.exit(1)
    
    # Set output folder name
    base_name = os.path.splitext(os.path.basename(args.video))[0]
    output_folder = args.output if args.output else base_name
    
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
    print(f"Output folder: {output_folder}/")
    print(f"Width: {args.width} characters")
    print(f"Frame skip: {args.skip}")
    print(f"Wait time: {args.wait}s")
    print(f"Style: {args.style} ({len(ascii_chars)} characters)")
    print(f"GreyHack path: {args.path}/{output_folder}/")
    print(f"Max chars/file: {MAX_CHARS_PER_FILE:,}")
    print("=" * 50)
    print()
    
    # Process video
    frames, fps = process_video(args.video, args.width, ascii_chars, args.skip)
    
    if not frames:
        print("Error: No frames could be extracted from the video.")
        sys.exit(1)
    
    # Generate the GreyHack scripts
    data_files, total_chars = generate_greyhack_scripts(
        frames, output_folder, base_name, args.wait, args.path
    )
    
    # Summary
    print()
    print("=" * 50)
    print("  Done!")
    print("=" * 50)
    print(f"Frames: {len(frames)}")
    print(f"Output folder: {output_folder}/")
    print(f"Data files: {len(data_files)}")
    print(f"Total size: {total_chars / (1024*1024):.2f} MB ({total_chars:,} chars)")
    print()
    print(f"To use in GreyHack:")
    print(f"  1. Copy the '{output_folder}' folder to your GreyHack computer")
    print(f"  2. Update the import paths in {base_name}.src if needed")
    print(f"  3. Compile and run {base_name}.src")
    print("=" * 50)


if __name__ == "__main__":
    main()
