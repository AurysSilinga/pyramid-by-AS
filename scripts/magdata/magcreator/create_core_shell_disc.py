#! python
# -*- coding: utf-8 -*-
"""Create magnetic core shell disc."""


import numpy as np
import pyramid as py
import logging.config


logging.config.fileConfig(py.LOGGING_CONFIG, disable_existing_loggers=False)

# Parameters:
dim = (32, 32, 32)
a = 1.0  # in nm
center = (dim[0]//2-0.5, dim[1]//2-0.5, dim[2]//2-0.5)
radius_core = dim[1]//8
radius_shell = dim[1]//4
height = dim[0]//2
filename = 'magdata_mc_core_shell_disc.nc'

# Magnetic shape:
mag_shape_core = py.magcreator.Shapes.disc(dim, center, radius_core, height)
mag_shape_outer = py.magcreator.Shapes.disc(dim, center, radius_shell, height)
mag_shape_shell = np.logical_xor(mag_shape_outer, mag_shape_core)

# Create and save MagData object:
mag_data = py.MagData(a, py.magcreator.create_mag_dist_vortex(mag_shape_shell, magnitude=0.75))
mag_data += py.MagData(a, py.magcreator.create_mag_dist_homog(mag_shape_core, phi=0, theta=0))
mag_data.save_to_netcdf4(filename)