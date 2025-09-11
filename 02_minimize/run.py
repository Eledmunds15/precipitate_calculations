# =============================================================
# LAMMPS Monopole Input Generation
# Author: Ethan L. Edmunds
# Version: v1.0
# Description: Python script to produce input for precipitate calculations.
# Note: Dislocation is aligned along X, glide plane along Y axis.
# Run: apptainer exec --nv 00_envs/lmp.sif python 01_input/run.py
# =============================================================

# ---------------------------
# IMPORT LIBRARIES
# ---------------------------
import os
import numpy as np
import subprocess

from lammps import lammps

# =============================================================
# PATH SETTINGS
# =============================================================
# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '000_data'))
INPUT_DIR = os.path.join(BASE_DIR, '01_input', 'Outputs')
POTENTIALS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '00_potentials'))
STAGE_DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '02_minimize'))
OUTPUT_DIR = os.path.join(STAGE_DATA_DIR, 'output')
DUMP_DIR = os.path.join(STAGE_DATA_DIR, 'dump')
LOG_DIR = os.path.join(STAGE_DATA_DIR, 'logs')

# Ensure output directories exist
for directory in [OUTPUT_DIR, DUMP_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Input potential file
POTENTIAL_FILE = os.path.join(POTENTIALS_DIR, 'malerba.fs')

# =============================================================
# SIMULATION PARAMETERS
# =============================================================

# =============================================================
# MAIN FUNCTION
# =============================================================
def main():

    lmp = lammps()

    # ---------- Initialize Simulation ------------------------
    lmp.cmd.clear()
    lmp.cmd.log(os.path.join(LOG_DIR, 'log.lammps'))

    lmp.cmd.units('metal')
    lmp.cmd.dimension(3)
    lmp.cmd.boundary('p', 'f', 'p')

    lmp.cmd.read_data(os.path.join(INPUT_DIR))





    return None

# =============================================================
# FUNCTIONS
# =============================================================

# =============================================================
# ENTRY POINT
# =============================================================
if __name__ == "__main__":
    main()
