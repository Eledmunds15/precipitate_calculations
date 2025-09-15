# =============================================================
# LAMMPS Monopole Input Generation
# Author: Ethan L. Edmunds
# Version: v1.0
# Description: Python script to produce input for precipitate calculations.
# Note: Dislocation is aligned along X, glide plane along Y axis.
# Run: apptainer exec --nv 00_envs/lmp.sif python 03_pin_dislo/run.py
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

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '000_data')) # Master data directory
STAGE_DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '03_pin_dislo')) # Stage data directory

OUTPUT_DIR = os.path.join(STAGE_DATA_DIR, 'output') # Output folder
DUMP_DIR = os.path.join(STAGE_DATA_DIR, 'dump') # Dump folder
LOG_DIR = os.path.join(STAGE_DATA_DIR, 'logs') # Log folder
RESTART_DIR = os.path.join(STAGE_DATA_DIR, 'restarts') # Restarts folder

for directory in [OUTPUT_DIR, DUMP_DIR, LOG_DIR, RESTART_DIR]:
    os.makedirs(directory, exist_ok=True)

INPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, '02_minimize', 'output')) # Input directory
INPUT_FILE = os.path.join(INPUT_DIR, 'output.lmp') # Input file

POTENTIALS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '00_potentials')) # Potentials Directory
POTENTIAL_FILE = os.path.join(POTENTIALS_DIR, 'malerba.fs') # Potential file

# =============================================================
# SIMULATION PARAMETERS
# =============================================================

PRECIPITATE_RADIUS = 25
DISLOCATION_INITIAL_DISPLACEMENT = 10 # Distance from the precipitate in Angstroms
FIXED_SURFACE_DEPTH = 5 # Depth of the fixed surface in Angstroms

DT = 0.001
TEMPERATURE = 800
SHEAR_VELOCITY = 1

RUN_TIME = 100
THERMO_FREQ = 1000
DUMP_FREQ = 1000
RESTART_FREQ = 10000

# =============================================================
# MAIN FUNCTION
# =============================================================
def main():

    lmp = lammps(cmdargs=['-k', 'on', 'g', '1', '-sf', 'kk'])

    # ---------- Initialize Simulation ------------------------
    lmp.cmd.clear()
    lmp.cmd.log(os.path.join(LOG_DIR, 'log.lammps'))

    lmp.cmd.units('metal')
    lmp.cmd.dimension(3)
    lmp.cmd.boundary('p', 'f', 'p')

    lmp.cmd.read_data(INPUT_FILE)

    lmp.cmd.pair_style('eam/fs')
    lmp.cmd.pair_coeff('*', '*', POTENTIAL_FILE, 'Fe')

    # Find the box bounds
    boxBounds = lmp.extract_box()

    box_min = boxBounds[0]
    box_max = boxBounds[1]

    xmin, xmax = box_min[0], box_max[0]
    ymin, ymax = box_min[1], box_max[1]
    zmin, zmax = box_min[2], box_max[2]

    simBoxCenter = [np.mean([xmin, xmax]), np.mean([ymin, ymax]), np.mean([zmin, zmax])]

    # Displace atoms
    lmp.cmd.group('all', 'type', '1')
    lmp.cmd.displace_atoms('all', 'move', PRECIPITATE_RADIUS+DISLOCATION_INITIAL_DISPLACEMENT, 0, 0, 'units', 'box')

    # Create Regions
    lmp.cmd.region('precipitate_reg', 'sphere', simBoxCenter[0], simBoxCenter[1], simBoxCenter[2], PRECIPITATE_RADIUS)
    lmp.cmd.region('top_surface_reg', 'block', 'INF', 'INF', (ymax-FIXED_SURFACE_DEPTH), 'INF', 'INF', 'INF')
    lmp.cmd.region('bottom_surface_reg', 'block', 'INF', 'INF', 'INF', (ymin+FIXED_SURFACE_DEPTH), 'INF', 'INF')

    # Define Groups
    #--- Define Groups ---#
    lmp.cmd.group('top_surface', 'region', 'top_surface_reg')
    lmp.cmd.group('bottom_surface', 'region', 'bottom_surface_reg')
    lmp.cmd.group('precipitate', 'region', 'precipitate_reg')
    lmp.cmd.group('mobile_atoms', 'subtract', 'all', 'precipitate', 'top_surface', 'bottom_surface')

    #--- Define Computes ---#
    lmp.cmd.compute('peratom', 'all', 'pe/atom')
    lmp.cmd.compute('stress', 'all', 'stress/atom', 'NULL')
    lmp.cmd.compute('temp_compute', 'all', 'temp')
    lmp.cmd.compute('press_comp', 'all', 'pressure', 'temp_compute')

    #lmp.cmd.compute('precipitate_force_x', 'precipitate', 'reduce', 'sum', 'fx')
    #lmp.cmd.compute('precipitate_force_y', 'precipitate', 'reduce', 'sum', 'fy')
    #lmp.cmd.compute('precipitate_force_z', 'precipitate', 'reduce', 'sum', 'fz')

    #lmp.cmd.compute('precipitate_velocity_x', 'precipitate', 'reduce', 'sum', 'vx')
    #lmp.cmd.compute('precipitate_velocity_y', 'precipitate', 'reduce', 'sum', 'vy')
    #lmp.cmd.compute('precipitate_velocity_z', 'precipitate', 'reduce', 'sum', 'vz')

    #--- Define Fixes and Velocities ---#
    lmp.cmd.fix('1', 'all', 'nvt', 'temp', TEMPERATURE, TEMPERATURE, 100.0*DT)
    
    lmp.cmd.velocity('mobile_atoms', 'create', TEMPERATURE, 1234, 'mom', 'yes', 'rot', 'yes')

    # Define fixes and forces for the top and bottom surfaces
    lmp.cmd.fix('top_surface_freeze', 'top_surface', 'setforce', 0.0, 0.0, 0.0)
    lmp.cmd.fix('bottom_surface_freeze', 'bottom_surface', 'setforce', 0.0, 0.0, 0.0)
    lmp.cmd.velocity('top_surface', 'set', -(SHEAR_VELOCITY/2), 0.0, 0.0)
    lmp.cmd.velocity('bottom_surface', 'set', (SHEAR_VELOCITY/2), 0.0, 0.0)

    lmp.cmd.fix('precipitate_freeze', 'precipitate', 'setforce', 0.0, 0.0, 0.0)
    lmp.cmd.velocity('precipitate', 'set', 0.0, 0.0, 0.0)

    #--- Dump ID's for post-processing ---#
    lmp.cmd.write_dump('precipitate', 'custom', os.path.join(OUTPUT_DIR, 'precipitate_ID'), 'id')

    #--- Thermo ---#
    lmp.cmd.thermo_style('custom', 'step', 'temp', 'pe', 'etotal', 'c_press_comp[1]', 'c_press_comp[2]', 'c_press_comp[3]', 'c_press_comp[4]', 'c_press_comp[5]', 'c_press_comp[6]')
    lmp.cmd.thermo(THERMO_FREQ)

    #--- Dump Files ---#
    DUMP_PATH = os.path.join(DUMP_DIR, 'dump_*')
    lmp.cmd.dump('1', 'all', 'custom', DUMP_FREQ, DUMP_PATH, 'id', 'x', 'y', 'z', 'c_peratom', 'c_stress[4]')

    #--- Restart Files ---#
    RESTART_PATH = os.path.join(RESTART_DIR, 'restart_*')
    lmp.cmd.restart(RESTART_FREQ, RESTART_PATH)

    lmp.cmd.run(RUN_TIME)
    
    return None

# =============================================================
# FUNCTIONS
# =============================================================

# =============================================================
# ENTRY POINT
# =============================================================
if __name__ == "__main__":
    main()
