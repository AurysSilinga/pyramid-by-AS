#! python
# -*- coding: utf-8 -*-
"""Create magnetic core shell sphere."""


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
filename = 'magdata_mc_core_shell_sphere.nc'

# Magnetic shape:
mag_shape_sphere = py.magcreator.Shapes.sphere(dim, center, radius_shell)
mag_shape_disc = py.magcreator.Shapes.disc(dim, center, radius_core, height=dim[0])
mag_shape_core = np.logical_and(mag_shape_sphere, mag_shape_disc)
mag_shape_shell = np.logical_and(mag_shape_sphere, np.logical_not(mag_shape_core))

# Create and save MagData object:
mag_data = py.MagData(a, py.magcreator.create_mag_dist_vortex(mag_shape_shell, magnitude=0.75))
mag_data += py.MagData(a, py.magcreator.create_mag_dist_homog(mag_shape_core, phi=0, theta=0))
mag_data.save_to_netcdf4(filename)