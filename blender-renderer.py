#!/usr/bin/env python3
from blender.renderer.blender import generate_blend
import argparse, sys, os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate .blend files from CommonRoad XML")
    parser.add_argument("input", nargs="?", type=argparse.FileType("r"),
        default=sys.stdin)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--force", "-f", action="store_true")
    parser.add_argument("--add_vehicle", "-av", action="store_true")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    if os.listdir(args.output) != [] and not args.force:
        print("Output directory is not empty.")
        print("Use --force")
        sys.exit(1)

    with args.input as input_file:
        xml = input_file.read()

    generate_blend(xml, args.output, args.add_vehicle)
