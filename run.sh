#!/bin/bash
#SBATCH --job-name=LUCY_SIMulation
#SBATCH --mail-user=eledmunds1@sheffield.ac.uk
#SBATCH --time=02:00:00
#SBATCH --mem-per-cpu=500MB
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=128

module load OpenMPI/4.1.4-GCC-12.2.0
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

HOST_MPI_PATH=/opt/apps/testapps/el7/software/staging/OpenMPI/4.1.4-GCC-12.2.0

CONTAINER_PATH=00_HPC/lmp_CPU_22Jul2025.sif

INPUT=03_pin_dislo/run.py

srun --export=ALL \
     apptainer exec \
     --bind $HOST_MPI_PATH:$HOST_MPI_PATH \
     $CONTAINER_PATH \
     python $INPUT
