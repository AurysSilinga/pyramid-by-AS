# coding=utf-8
"""Convert vector fields.

The :mod:`~.fieldconverter` provides methods for converting a magnetization distribution `M` into
a vector potential `A` and convert this in turn into a magnetic field `B`. The direct way is also
possible.

"""

import logging

import numpy as np

from pyramid import fft
from pyramid.fielddata import VectorData

__all__ = ['convert_M_to_A', 'convert_A_to_B', 'convert_M_to_B']
_log = logging.getLogger(__name__)


def convert_M_to_A(mag_data, b_0=1.0):
    """Convert a magnetic vector distribution into a vector potential `A`.

    Parameters
    ----------
    mag_data: :class:`~pyramid.magdata.VectorData` object
        The magnetic vector field from which the A-field is calculated.
    b_0: float, optional
        The saturation magnetization which is used in the calculation.

    Returns
    -------
    b_data: :class:`~pyramid.magdata.VectorData` object
        The calculated B-field.

    """
    _log.debug('Calling convert_M_to_A')
    # Preparations of variables:
    assert isinstance(mag_data, VectorData), 'Only VectorData objects can be mapped!'
    dim = mag_data.dim
    dim_kern = tuple(2 * np.array(dim) - 1)  # Dimensions of the kernel
    if fft.BACKEND == 'pyfftw':
        dim_pad = tuple(2 * np.array(dim))  # is at least even (not neccessary a power of 2)
    elif fft.BACKEND == 'numpy':
        dim_pad = tuple(2 ** np.ceil(np.log2(2 * np.array(dim))).astype(int))  # pow(2)
    else:
        raise ValueError('Backend of the fft module is not correctly initiated!')
    slice_B = (slice(dim[0] - 1, dim_kern[0]),  # Shift because kernel center
               slice(dim[1] - 1, dim_kern[1]),  # is not at (0, 0, 0)!
               slice(dim[2] - 1, dim_kern[2]))
    slice_M = (slice(0, dim[0]),  # Magnetization is padded on the far end!
               slice(0, dim[1]),  # B-field cutout is shifted as listed above
               slice(0, dim[2]))  # because of the kernel center!
    # Set up kernels
    coeff = mag_data.a * b_0 / (4 * np.pi)
    zzz, yyy, xxx = np.indices(dim_kern)
    xxx -= dim[2] - 1
    yyy -= dim[1] - 1
    zzz -= dim[0] - 1
    k_x = fft.empty(dim_kern, dtype=fft.FLOAT)
    k_y = fft.empty(dim_kern, dtype=fft.FLOAT)
    k_z = fft.empty(dim_kern, dtype=fft.FLOAT)
    k_x[...] = coeff * xxx / np.abs(xxx ** 2 + yyy ** 2 + zzz ** 2 + 1E-30) ** 3
    k_y[...] = coeff * yyy / np.abs(xxx ** 2 + yyy ** 2 + zzz ** 2 + 1E-30) ** 3
    k_z[...] = coeff * zzz / np.abs(xxx ** 2 + yyy ** 2 + zzz ** 2 + 1E-30) ** 3
    # Calculate Fourier trafo of kernel components:
    k_x_fft = fft.rfftn(k_x, dim_pad)
    k_y_fft = fft.rfftn(k_y, dim_pad)
    k_z_fft = fft.rfftn(k_z, dim_pad)
    # Prepare magnetization:
    x_mag = fft.zeros(dim_pad, dtype=fft.FLOAT)
    y_mag = fft.zeros(dim_pad, dtype=fft.FLOAT)
    z_mag = fft.zeros(dim_pad, dtype=fft.FLOAT)
    x_mag[slice_M] = mag_data.field[0, ...]
    y_mag[slice_M] = mag_data.field[1, ...]
    z_mag[slice_M] = mag_data.field[2, ...]
    # Calculate Fourier trafo of magnetization components:
    x_mag_fft = fft.rfftn(x_mag)
    y_mag_fft = fft.rfftn(y_mag)
    z_mag_fft = fft.rfftn(z_mag)
    # Convolve:
    a_x_fft = y_mag_fft * k_z_fft - z_mag_fft * k_y_fft
    a_y_fft = z_mag_fft * k_x_fft - x_mag_fft * k_z_fft
    a_z_fft = x_mag_fft * k_y_fft - y_mag_fft * k_x_fft
    a_x = fft.irfftn(a_x_fft)[slice_B]
    a_y = fft.irfftn(a_y_fft)[slice_B]
    a_z = fft.irfftn(a_z_fft)[slice_B]
    # Return A-field:
    return VectorData(mag_data.a, np.asarray((a_x, a_y, a_z)))


def convert_A_to_B(a_data):
    """Convert a vector potential `A` into a B-field distribution.

    Parameters
    ----------
    a_data: :class:`~pyramid.magdata.VectorData` object
        The vector potential field from which the A-field is calculated.

    Returns
    -------
    b_data: :class:`~pyramid.magdata.VectorData` object
        The calculated B-field.

    """
    _log.debug('Calling convert_A_to_B')
    assert isinstance(a_data, VectorData), 'Only VectorData objects can be mapped!'
    #
    axis = tuple([i for i in range(3) if a_data.dim[i] > 1])
    #
    x_grads = np.gradient(a_data.field[0, ...], axis=axis) #/ a_data.a
    y_grads = np.gradient(a_data.field[1, ...], axis=axis) #/ a_data.a
    z_grads = np.gradient(a_data.field[2, ...], axis=axis) #/ a_data.a
    #
    x_gradii = np.zeros(a_data.shape)
    y_gradii = np.zeros(a_data.shape)
    z_gradii = np.zeros(a_data.shape)
    #
    for i, axis in enumerate(axis):
        x_gradii[axis] = x_grads[i]
        y_gradii[axis] = y_grads[i]
        z_gradii[axis] = z_grads[i]
    #
    x_grad_z, x_grad_y, x_grad_x = x_gradii
    y_grad_z, y_grad_y, y_grad_x = y_gradii
    z_grad_z, z_grad_y, z_grad_x = z_gradii
    # Calculate cross product:
    b_x = (z_grad_y - y_grad_z)
    b_y = (x_grad_z - z_grad_x)
    b_z = (y_grad_x - x_grad_y)
    # Return B-field:
    return VectorData(a_data.a, np.asarray((b_x, b_y, b_z)))




    # Calculate gradients:
    x_mag, y_mag, z_mag = a_data.field
    x_grad_z, x_grad_y, x_grad_x = np.gradient(x_mag)
    y_grad_z, y_grad_y, y_grad_x = np.gradient(y_mag)
    z_grad_z, z_grad_y, z_grad_x = np.gradient(z_mag)
    # Calculate cross product:
    b_x = (z_grad_y - y_grad_z)
    b_y = (x_grad_z - z_grad_x)
    b_z = (y_grad_x - x_grad_y)
    # Return B-field:
    return VectorData(a_data.a, np.asarray((b_x, b_y, b_z)))


def convert_M_to_B(mag_data, b_0=1.0):
    """Convert a magnetic vector distribution into a B-field distribution.

    Parameters
    ----------
    mag_data: :class:`~pyramid.magdata.VectorData` object
        The magnetic vector field from which the B-field is calculated.
    b_0: float, optional
        The saturation magnetization which is used in the calculation.

    Returns
    -------
    b_data: :class:`~pyramid.magdata.VectorData` object
        The calculated B-field.

    """
    _log.debug('Calling convert_M_to_B')
    assert isinstance(mag_data, VectorData), 'Only VectorData objects can be mapped!'
    return convert_A_to_B(convert_M_to_A(mag_data, b_0=b_0))