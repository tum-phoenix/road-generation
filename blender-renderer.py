#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd())

from blender.renderer.blender import generate_blend
import argparse, sys, os

OUTPUT_DIR = 'blender-output'
FORCE_OUTPUT = True
ADD_VEHICLE = True
INPUT_FILE = 'driving-scenario.xml'
GAZEBO_WORLDS_PATH = '../drive_gazebo_worlds'
GAZEBO_SIM_PATH = '../drive_gazebo_sim/meshes'

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.listdir(OUTPUT_DIR) != [] and not FORCE_OUTPUT:
        print("Output directory is not empty.")
        print("Use --force")
        sys.exit(1)

    with open(INPUT_FILE) as input_file:
        xml = input_file.read()

    generate_blend(xml, OUTPUT_DIR, ADD_VEHICLE, OUTPUT_DIR, GAZEBO_WORLDS_PATH, GAZEBO_SIM_PATH)
