#!/usr/bin/bash

export LD_LIBRARY_PATH=/home/vaibhav/MIST/software/fftw/fftw3
/home/vaibhav/MIST/software/openmpi/openmpi/bin/mpirun -n 1
/home/vaibhav/MIST/software/MIST/Default/mist -i $1
