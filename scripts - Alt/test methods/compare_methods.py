#! python
# -*- coding: utf-8 -*-
"""Compare the different methods to create phase maps."""

import os

import time

import numpy as np
from numpy import pi

import pyramid
import pyramid.magcreator as mc
import pyramid.analytic as an
from pyramid.projector import SimpleProjector
from pyramid.phasemapper import PhaseMapperRDRC, PhaseMapperRDFC, PhaseMapperFDFC
from pyramid.kernel import Kernel
from pyramid.magdata import MagData
from pyramid import fft

import logging
import logging.config


LOGGING_CONF = os.path.join(os.path.dirname(os.path.realpath(pyramid.__file__)), 'logging.ini')


logging.config.fileConfig(LOGGING_CONF, disable_existing_loggers=False)

# Input parameters:
b_0 = 1.0    # in T
a = 1.0  # in nm
phi = pi/4
gain = 'auto'
dim = (128, 128, 128)  # in px (z, y, x)

# Create magnetic shape:
geometry = 'disc'
if geometry == 'slab':
    center = (dim[0]/2.-0.5, dim[1]/2.-0.5, dim[2]/2.-0.5)  # in px (z,y,x) index starts at 0!
    width = (dim[0]/2, dim[1]/2, dim[2]/2)  # in px (z, y, x)
    mag_shape = mc.Shapes.slab(dim, center, width)
    phase_map_ana = an.phase_mag_slab(dim, a, phi, center, width, b_0)
elif geometry == 'disc':
    center = (dim[0]/2.-0.5, dim[1]/2.-0.5, dim[2]/2.-0.5)  # in px (z,y,x) index starts at 0!
    radius = dim[1]/4  # in px
    height = dim[0]/2  # in px
    mag_shape = mc.Shapes.disc(dim, center, radius, height)
    phase_map_ana = an.phase_mag_disc(dim, a, phi, center, radius, height, b_0)
elif geometry == 'sphere':
    center = (dim[0]/2.-0.5, dim[1]/2.-0.5, dim[2]/2.-0.50)  # in px (z, y, x) index starts with 0!
    radius = dim[1]/4  # in px
    mag_shape = mc.Shapes.sphere(dim, center, radius)
    phase_map_ana = an.phase_mag_sphere(dim, a, phi, center, radius, b_0)

# Create MagData object and projector:
mag_data = MagData(a, mc.create_mag_dist_homog(mag_shape, phi))
projector = SimpleProjector(dim)
projection = projector(mag_data)

# RDRC no numcore:
pm_real_slow = PhaseMapperRDRC(Kernel(a, projector.dim_uv, b_0), numcore=False)
start_time = time.time()
phase_map_real = pm_real_slow(projection)
print 'Time for RDRC no numcore :', time.time() - start_time

# RDRC with numcore:
pm_real_fast = PhaseMapperRDRC(Kernel(a, projector.dim_uv, b_0), numcore=True)
start_time = time.time()
phase_map_real = pm_real_fast(projection)
print 'Time for RDRC    numcore :', time.time() - start_time

# RDFC numpy convolution:
fft.configure_backend('numpy')
pm_conv_slow = PhaseMapperRDFC(Kernel(a, projector.dim_uv, b_0))
start_time = time.time()
phase_map_conv = pm_conv_slow(projection)
print 'Time for RDFC numpy conv.:', time.time() - start_time

# RDFC FFTW convolution:
fft.configure_backend('fftw')
pm_conv_fast = PhaseMapperRDFC(Kernel(a, projector.dim_uv, b_0))
start_time = time.time()
phase_map_conv = pm_conv_fast(projection)
print 'Time for RDFC FFTW  conv.:', time.time() - start_time

# FDFC padding 0:
pm_four_pad0 = PhaseMapperFDFC(a, projector.dim_uv, b_0, padding=0)
start_time = time.time()
phase_map_four = pm_four_pad0(projection)
print 'Time for FDFC padding 0  :', time.time() - start_time

# FDFC padding 1:
pm_four_pad1 = PhaseMapperFDFC(a, projector.dim_uv, b_0, padding=1)
start_time = time.time()
phase_map_four = pm_four_pad1(projection)
print 'Time for FDFC padding 1  :', time.time() - start_time

# Display the combinated plots with phasemap and holography image:
phase_map_ana.display_combined('Analytic Solution', gain=gain)
phase_map_real.display_combined('RDRC', gain=gain)
phase_map_conv.display_combined('RDFC', gain=gain)
phase_map_four.display_combined('FDFC', gain=gain)

# Plot differences to the analytic solution:
phase_map_diff_real = phase_map_real - phase_map_ana
phase_map_diff_conv = phase_map_conv - phase_map_ana
phase_map_diff_four = phase_map_four - phase_map_ana
RMS_real = np.std(phase_map_diff_real.phase)
RMS_conv = np.std(phase_map_diff_conv.phase)
RMS_four = np.std(phase_map_diff_four.phase)
phase_map_diff_real.display_phase('RDRC difference (RMS = {:3.2e})'.format(RMS_real))
phase_map_diff_conv.display_phase('RDFC difference (RMS = {:3.2e})'.format(RMS_conv))
phase_map_diff_four.display_phase('FDFC difference (RMS = {:3.2e})'.format(RMS_four))