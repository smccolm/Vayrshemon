"""Verify the four shipped font assets without installing or modifying anything."""
import argparse
import json
from pathlib import Path
from vayrshemon.bundled_fonts import verify


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    print(json.dumps(verify(args.root),indent=2))
