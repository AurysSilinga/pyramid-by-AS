#! python
# -*- coding: utf-8 -*-
"""Compare the different methods to create phase maps."""


import time
import pdb
import traceback
import sys

import numpy as np
from numpy import pi

import pyramid.magcreator as mc
import pyramid.projector as pj
import pyramid.phasemapper as pm
import pyramid.holoimage as hi
import pyramid.analytic as an
from pyramid.magdata import MagData
from pyramid.kernel import Kernel
from pyramid.phasemap import PhaseMap


def compare_methods():
    '''Calculate and display the phase map from a given magnetization.
    Arguments:
        None
    Returns:
        None

    '''
    # Input parameters:
    b_0 = 1.0    # in T
    a = 1.0  # in nm
    phi = pi/4
    padding = 3
    density = 10
    dim = (128, 128, 128)  # in px (z, y, x)
    # Create magnetic shape:
    geometry = 'sphere'
    if geometry == 'slab':
        center = (dim[0]/2.-0.5, dim[1]/2.-0.5, dim[2]/2.-0.5)  # in px (z,y,x) index starts at 0!
        width = (dim[0]/2, dim[1]/2, dim[2]/2)  # in px (z, y, x)
        mag_shape = mc.Shapes.slab(dim, center, width)
        phase_ana = an.phase_mag_slab(dim, a, phi, center, width, b_0)
    elif geometry == 'disc':
        center = (dim[0]/2.-0.5, dim[1]/2.-0.5, dim[2]/2.-0.5)  # in px (z,y,x) index starts at 0!
        radius = dim[1]/4  # in px
        height = dim[0]/2  # in px
        mag_shape = mc.Shapes.disc(dim, center, radius, height)
        phase_ana = an.phase_mag_disc(dim, a, phi, center, radius, height, b_0)
    elif geometry == 'sphere':
        center = (dim[0]/2.-0.5, dim[1]/2.-0.5, dim[2]/2.-0.50)  # in px (z, y, x) index starts with 0!
        radius = dim[1]/4  # in px
        mag_shape = mc.Shapes.sphere(dim, center, radius)
        phase_ana = an.phase_mag_sphere(dim, a, phi, center, radius, b_0)
    # Project the magnetization data:
    mag_data = MagData(a, mc.create_mag_dist_homog(mag_shape, phi))
    mag_data.quiver_plot(ax_slice=int(center[0]))
    projection = pj.simple_axis_projection(mag_data)
    # Construct phase maps:
    phase_map_ana = PhaseMap(a, phase_ana)
    start_time = time.time()
    phase_map_fft = PhaseMap(a, pm.phase_mag_fourier(a, projection, padding, b_0))
    print 'Time for Fourier space approach:               ', time.time() - start_time
    start_time = time.time()
    phase_map_slab = PhaseMap(a, pm.phase_mag_real(a, projection, b_0, 'slab'))
    print 'Time for real space approach (Slab):           ', time.time() - start_time
    start_time = time.time()
    phase_map_disc = PhaseMap(a, pm.phase_mag_real(a, projection, b_0, 'disc'))
    print 'Time for real space approach (Disc):           ', time.time() - start_time
    start_time = time.time()
    kernel = Kernel(np.shape(projection[0]), a, b_0, 'slab')
    phase_map_slab_conv = PhaseMap(a, pm.phase_mag(a, projection, b_0, kernel))
    print 'Time for real space approach (Slab Conv):      ', time.time() - start_time
    start_time = time.time()
    phase_map_disc_conv = PhaseMap(a, pm.phase_mag(a, projection, b_0))
    print 'Time for real space approach (Disc Conv):      ', time.time() - start_time
    start_time = time.time()
    kernel = Kernel(np.shape(projection[0]), a, b_0, 'slab')
    print 'Time for kernel (Slab):                        ', time.time() - start_time
    start_time = time.time()
    phase_map_slab_fast = PhaseMap(a, pm.phase_mag(a, projection, b_0, kernel))
    print 'Time for real space approach (Slab, no kernel):', time.time() - start_time
    start_time = time.time()
    kernel = Kernel(np.shape(projection[0]), a, b_0)
    print 'Time for kernel (Disc):                        ', time.time() - start_time
    start_time = time.time()
    phase_map_disc_fast = PhaseMap(a, pm.phase_mag(a, projection, b_0, kernel))
    print 'Time for real space approach (Disc, no kernel):', time.time() - start_time    
    # Display the combinated plots with phasemap and holography image:
    hi.display_combined(phase_map_ana, density, 'Analytic Solution')
    hi.display_combined(phase_map_fft, density, 'Fourier Space')
    hi.display_combined(phase_map_slab, density, 'Real Space (Slab)')
    hi.display_combined(phase_map_disc, density, 'Real Space (Disc)')
    hi.display_combined(phase_map_slab_conv, density, 'Real Space (Slab Convolve)')
    hi.display_combined(phase_map_disc_conv, density, 'Real Space (Disc Convolve)')
    hi.display_combined(phase_map_slab_fast, density, 'Real Space (Slab Fast)')
    hi.display_combined(phase_map_disc_fast, density, 'Real Space (Disc Disc)')
    # Plot differences to the analytic solution:
    phase_map_diff_fft = PhaseMap(a, phase_map_ana.phase-phase_map_fft.phase)
    phase_map_diff_slab = PhaseMap(a, phase_map_ana.phase-phase_map_slab.phase)
    phase_map_diff_disc = PhaseMap(a, phase_map_ana.phase-phase_map_disc.phase)
    phase_map_diff_slab_conv = PhaseMap(a, phase_map_ana.phase-phase_map_slab_conv.phase)
    phase_map_diff_disc_conv = PhaseMap(a, phase_map_ana.phase-phase_map_disc_conv.phase)
    RMS_fft = np.std(phase_map_diff_fft.phase)
    RMS_slab = np.std(phase_map_diff_slab.phase)
    RMS_disc = np.std(phase_map_diff_disc.phase)
    RMS_slab_conv = np.std(phase_map_diff_slab_conv.phase)
    RMS_disc_conv = np.std(phase_map_diff_disc_conv.phase)
    phase_map_diff_fft.display('Fourier Space (RMS = {:3.2e})'.format(RMS_fft))
    phase_map_diff_slab.display('Real Space (Slab) (RMS = {:3.2e})'.format(RMS_slab))
    phase_map_diff_disc.display('Real Space (Disc) (RMS = {:3.2e})'.format(RMS_disc))
    phase_map_diff_slab_conv.display('Real Conv. (Slab) (RMS = {:3.2e})'.format(RMS_slab_conv))
    phase_map_diff_disc_conv.display('Real Conv. (Disc) (RMS = {:3.2e})'.format(RMS_disc_conv))


if __name__ == "__main__":
    try:
        compare_methods()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)