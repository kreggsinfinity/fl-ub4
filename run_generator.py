import sys
import asyncio
from idiom_generator import run_idiom_generation

def main():
    print("Starting Idioms & Slang Decoded generator (9:16 Vertical Reel)...")
    video_p, meta = asyncio.run(run_idiom_generation(idx=0))
    print(f"Done! Final video generated: {video_p}")

if __name__ == "__main__":
    main()
