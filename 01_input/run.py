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
import pandas as pd
import matplotlib.pyplot as plt

import ase
from ase import io

import atomman as am
import atomman.unitconvert as uc
from matscipy.calculators.eam import EAM
from matscipy.dislocation import get_elastic_constants

# =============================================================
# PATH SETTINGS
# =============================================================
# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '000_data'))
INPUT_DIR = os.path.join(BASE_DIR, '01_input')
POTENTIALS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '00_potentials'))
OUTPUT_DIR = os.path.join(INPUT_DIR, 'Output')
DUMP_DIR = os.path.join(INPUT_DIR, 'Dump')
LOG_DIR = os.path.join(INPUT_DIR, 'Logs')

# Ensure output directories exist
for directory in [OUTPUT_DIR, DUMP_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Input potential file
POTENTIAL_FILE = os.path.join(POTENTIALS_DIR, 'malerba.fs')

# =============================================================
# SIMULATION PARAMETERS
# =============================================================
# Lattice dimensions (angstrom)
A_MIN = 300  # LENGTH ALONG X
B_MIN = 300  # LENGTH ALONG Y
C_MIN = 300  # LENGTH ALONG Z

BURGERS = [0.5, 0.5, 0.5]  # BCC a/2 <111>
SLIP = [1, -1, 0]          # Glide plane
LINE_DIR = [0.5, 0.5, 0.5] # Line direction

# =============================================================
# MAIN FUNCTION
# =============================================================
def main():
    # ---------------------------
    # Load EAM potential
    # ---------------------------
    eam_calc = EAM(POTENTIAL_FILE)

    # Get lattice constant and elastic constants for Fe
    alat, C11, C12, C44 = get_elastic_constants(calculator=eam_calc, symbol="Fe", verbose=True)

    # Convert units
    alat = uc.set_in_units(alat, 'angstrom')
    C11 = uc.set_in_units(C11, 'GPa')
    C12 = uc.set_in_units(C12, 'GPa')
    C44 = uc.set_in_units(C44, 'GPa')

    # Create ElasticConstants object
    C = am.ElasticConstants(C11=C11, C12=C12, C44=C44)

    # ---------------------------
    # Define dislocation
    # ---------------------------

    conventional_setting = 'i'
    ucell = am.load('prototype', id='A2--W--bcc', a=alat, symbols='Fe')

    shift = np.array([0.0, 0.0, 0.66666666666667])  # Normalize shift
    shiftscale = True

    bcc_disl = am.defect.Dislocation(
        ucell, C, burgers=np.array(BURGERS), ξ_uvw=np.array(LINE_DIR), slip_hkl=np.array(SLIP),
        conventional_setting=conventional_setting,
        shift=shift, shiftscale=shiftscale,
        m='x', n='y'
    )

    # ---------------------------
    # Generate periodic dislocation array
    # ---------------------------
    disl_system = bcc_disl.periodicarray(
        amin=A_MIN, bmin=B_MIN, cmin=C_MIN,
        boundarywidth=3, boundaryscale=True,
        return_base_system=False
    )

    # ---------------------------
    # Export to LAMMPS data via ASE
    # ---------------------------
    ase_atoms, ase_props = disl_system.dump('ase_Atoms', return_prop=True)
    output_file = os.path.join(OUTPUT_DIR, 'input.lmp')
    ase.io.write(output_file, ase_atoms, 'lammps-data')
    print(f"LAMMPS input file saved to: {output_file}")

# =============================================================
# FUNCTIONS
# =============================================================

# =============================================================
# ENTRY POINT
# =============================================================
if __name__ == "__main__":
    main()
