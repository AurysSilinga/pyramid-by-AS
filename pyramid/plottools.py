# -*- coding: utf-8 -*-
# Copyright 2016 by Forschungszentrum Juelich GmbH
# Author: J. Caron
# Adapted from mpl_toolkits.axes_grid2
"""This module provides the useful plotting utilities."""

import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredOffsetbox, AuxTransformBox, VPacker, TextArea
from matplotlib.transforms import blended_transform_factory, IdentityTransform
from matplotlib.patches import Rectangle
from matplotlib import patheffects
from matplotlib.ticker import MaxNLocator, FuncFormatter

from mpl_toolkits.axes_grid1 import make_axes_locatable

import warnings

from . import colors

__all__ = ['format_axis', 'pretty_plots', 'add_scalebar',
           'add_annotation', 'add_colorwheel', 'add_cbar']

FIGSIZE_DEFAULT = (6.7, 5)
FONTSIZE_DEFAULT = 20
STROKE_DEFAULT = None


def pretty_plots(figsize=None, fontsize=None, stroke=None):
    """Set IPython formats (for interactive and PDF output) and set pretty matplotlib font."""
    from IPython.display import set_matplotlib_formats
    set_matplotlib_formats('png', 'pdf')  # png for interactive, pdf, for PDF output!
    mpl.rcParams['mathtext.fontset'] = 'stix'  # Mathtext in $...$!
    mpl.rcParams['font.family'] = 'STIXGeneral'  # Set normal text to look the same!
    mpl.rcParams['figure.max_open_warning'] = 0  # Disable Max Open Figure warning!
    if figsize is not None:
        global FIGSIZE_DEFAULT
        FIGSIZE_DEFAULT = figsize
    if fontsize is not None:
        global FONTSIZE_DEFAULT
        FONTSIZE_DEFAULT = fontsize
    global STROKE_DEFAULT
    STROKE_DEFAULT = stroke


def add_scalebar(axis, sampling=1, fontsize=None, stroke=None):
    """Add a scalebar to the axis.

    Parameters
    ----------
    axis : :class:`~matplotlib.axes.AxesSubplot`
        Axis to which the scalebar is added.
    sampling : float, optional
        The grid spacing in nm. If not given, 1 nm is assumed.
    fontsize : int, optional
        The fontsize which should be used for the label. Default is 16.
    stroke : None or color, optional
        If not None, a stroke will be applied to the text, e.g. to make it more visible.

    Returns
    -------
    aoffbox : :class:`~matplotlib.offsetbox.AnchoredOffsetbox`
        The box containing the scalebar.

    """
    if fontsize is None:
        fontsize = FONTSIZE_DEFAULT
    if stroke is None:
        stroke = STROKE_DEFAULT
    # Transform that scales the width along the data and leaves height constant at 8 pt (text):
    transform = blended_transform_factory(axis.transData, IdentityTransform())
    # Transform axis borders (1, 1) to data borders to get number of pixels in y and x:
    bb0 = axis.transLimits.inverted().transform((0, 0))
    bb1 = axis.transLimits.inverted().transform((1, 1))
    dim_uv = (int(abs(bb1[1] - bb0[1])), int(abs(bb1[0] - bb0[0])))
    # Calculate scale
    scale = np.max((dim_uv[1] / 4, 1)) * sampling
    thresholds = [1, 5, 10, 50, 100, 500, 1000]
    for t in thresholds:  # For larger grids (real images), multiples of threshold look better!
        if scale > t:
            scale = (scale // t) * t
    # Set dimensions:
    width = scale / sampling  # In data coordinate system!
    height = 8  # In display coordinate system!
    # Set label:
    if scale >= 1000:  # Use higher order instead!
        label = '{:.3g} µm'.format(scale/1000)
    else:
        label = '{:.3g} nm'.format(scale)
    # Create scalebar rectangle:
    bars = AuxTransformBox(transform)
    bars.add_artist(Rectangle((0, 0), width, height, fc='w', linewidth=1,
                    clip_box=axis.bbox, clip_on=True))
    # Create text:
    txtcolor = 'w' if stroke == 'k' else 'k'
    txt = TextArea(label, textprops={'color': txtcolor, 'fontsize': fontsize})
    txt.set_clip_box(axis.bbox)
    if stroke is not None:
        txt._text.set_path_effects([patheffects.withStroke(linewidth=2, foreground=stroke)])
    # Pack both together an create AnchoredOffsetBox:
    bars = VPacker(children=[txt, bars], align="center", pad=0.5, sep=5)
    aoffbox = AnchoredOffsetbox(loc=3, pad=0.5, borderpad=0.1, child=bars, frameon=False)
    axis.add_artist(aoffbox)
    # Return:
    return aoffbox


def add_annotation(axis, label, stroke=None, fontsize=None):
    """Add an annotation to the axis on the upper left corner.

    Parameters
    ----------
    axis : :class:`~matplotlib.axes.AxesSubplot`
        Axis to which the annotation is added.
    label : string
        The text of the annotation.
    fontsize : int, optional
        The fontsize which should be used for the annotation. Default is 16.
    stroke : None or color, optional
        If not None, a stroke will be applied to the text, e.g. to make it more visible.

    Returns
    -------
    aoffbox : :class:`~matplotlib.offsetbox.AnchoredOffsetbox`
        The box containing the annotation.

    """
    if fontsize is None:
        fontsize = FONTSIZE_DEFAULT
    if stroke is None:
        stroke = STROKE_DEFAULT
    # Create text:
    txtcolor = 'w' if stroke == 'k' else 'k'
    txt = TextArea(label, textprops={'color': txtcolor, 'fontsize': fontsize})
    txt.set_clip_box(axis.bbox)
    if stroke is not None:
        txt._text.set_path_effects([patheffects.withStroke(linewidth=2, foreground=stroke)])
    # Pack into and add AnchoredOffsetBox:
    aoffbox = AnchoredOffsetbox(loc=2, pad=0.5, borderpad=0.1, child=txt, frameon=False)
    axis.add_artist(aoffbox)
    return aoffbox


def add_colorwheel(axis):
    """Add a colorwheel to the axis on the upper right corner.

        Parameters
        ----------
        axis : :class:`~matplotlib.axes.AxesSubplot`
            Axis to which the colorwheel is added.

        Returns
        -------
        axis : :class:`~matplotlib.axes.AxesSubplot`
            The same axis which was given to this function is returned.

    """
    from mpl_toolkits.axes_grid.inset_locator import inset_axes
    inset_axes = inset_axes(axis, width=0.75, height=0.75, loc=1)
    inset_axes.axis('off')
    cmap = colors.CMAP_CIRCULAR_DEFAULT
    return cmap.plot_colorwheel(size=100, axis=inset_axes, alpha=0, arrows=True)


def add_cbar(axis, mappable, label='', fontsize=None):
    """Add a colorbar to the right of the given axis.

    Parameters
    ----------
    axis : :class:`~matplotlib.axes.AxesSubplot`
        Axis to which the colorbar is added.
    mappable : mappable pyplot
        If this is not None, a colorbar will be plotted on the right side of the axes,
    label : string, optional
        The label of the colorbar. If not set, no label is used.
    fontsize : int, optional
        The fontsize which should be used for the label. Default is 16.

    Returns
    -------
    cbar : :class:`~matplotlib.Colorbar`
        The created colorbar.

    """
    if fontsize is None:
        fontsize = FONTSIZE_DEFAULT
    divider = make_axes_locatable(axis)
    cbar_ax = divider.append_axes('right', size='5%', pad=0.1)
    cbar = plt.colorbar(mappable, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=fontsize)
    # Make sure labels don't stick out of tight bbox:
    labels = cbar.ax.get_yticklabels()
    delta = 0.03 * (cbar.vmax - cbar.vmin)
    lmin = float(labels[0]._text.replace(u'\u2212', '-').strip('$'))  # No unicode or latex!
    lmax = float(labels[-1]._text.replace(u'\u2212', '-').strip('$'))  # No unicode or latex!
    redo_max = True if cbar.vmax - lmax < delta else False
    redo_min = True if lmin - cbar.vmin < delta else False
    mappable.set_clim(cbar.vmin - delta * redo_min, cbar.vmax + delta * redo_max)
    # A lot of plotting magic to make plot width consistent (mostly):
    cbar.ax.set_yticklabels(labels, ha='right')
    renderer = plt.gcf().canvas.get_renderer()
    bbox_0 = labels[0].get_window_extent(renderer)
    bbox_1 = labels[-1].get_window_extent(renderer)
    cbar_pad = np.max((bbox_0.width, bbox_1.width)) + 5  # bit of padding left!
    cbar.ax.yaxis.set_tick_params(pad=cbar_pad)
    max_txt = plt.text(0, 0, u'\u22120.00', fontsize=fontsize)
    bbox_max = max_txt.get_window_extent(renderer)
    max_txt.remove()
    cbar_pad_max = bbox_max.width + 10  # bit of padding right!
    cbar.set_label(label, fontsize=fontsize, labelpad=max(cbar_pad_max - cbar_pad, 0))
    # Set focus back to axis and return cbar:
    plt.sca(axis)
    return cbar


def format_axis(axis, format_axis=True, title='', fontsize=None, stroke=None, scalebar=True,
                hideaxes=None, sampling=1, note=None,  colorwheel=False, cbar_mappable=None,
                cbar_label='', tight_layout=True, **_):
    """Format an axis and add a lot of nice features.

    Parameters
    ----------
    axis : :class:`~matplotlib.axes.AxesSubplot`
        Axis on which the graph is plotted.
    format_axis : bool, optional
        If False, the formatting will be skipped (the axis is still returned). Default is True.
    title : string, optional
        The title of the plot. The default is an empty string''.
    fontsize : int, optional
        The fontsize which should be used for labels and titles. Default is 16.
    stroke : None or color, optional
        If not None, a stroke will be applied to the text, e.g. to make it more visible.
    scalebar : bool, optional
        Defines if a scalebar should be plotted in the lower left corner (default: True). Axes
        are made invisible. If set to False, the axes are formatted to ook pretty, instead.
    hideaxes : True, optional
        If True, the axes will be turned invisible. If not specified (None), this is True if a
        scalebar is plotted, False otherwise.
    sampling : float, optional
        The grid spacing in nm. If not given, 1 nm is assumed.
    note: string or None, optional
        An annotation string which is displayed in the upper left
    colorwheel : bool, optional
        Defines if a colorwheel should be plotted in the upper right corner (default: False).
    cbar_mappable : mappable pyplot or None, optional
        If this is not None, a colorbar will be plotted on the right side of the axes,
        which uses this mappable object.
    cbar_label : string, optional
        The label of the colorbar. If `None`, no label is used.
    tight_layout : bool, optional
        If True, `plt.tight_layout()` is executed after the formatting. Default is True.

    Returns
    -------
    axis : :class:`~matplotlib.axes.AxesSubplot`
        The same axis which was given to this function is returned.

    """
    if not format_axis:  # Skip (sometimes useful if more than one plot is used on the same axis!
        return axis
    if fontsize is None:
        fontsize = FONTSIZE_DEFAULT
    if stroke is None:
        stroke = STROKE_DEFAULT
    # Get dimensions:
    bb0 = axis.transLimits.inverted().transform((0, 0))
    bb1 = axis.transLimits.inverted().transform((1, 1))
    dim_uv = (int(abs(bb1[1] - bb0[1])), int(abs(bb1[0] - bb0[0])))
    # Set the title and the axes labels:
    axis.set_xlim(0, dim_uv[1])
    axis.set_ylim(0, dim_uv[0])
    axis.set_title(title, fontsize=fontsize)
    # Add scalebar:
    if scalebar:
        add_scalebar(axis, sampling=sampling, fontsize=fontsize, stroke=stroke)
        if hideaxes is None:
            hideaxes = True
    # Determine major tick locations (useful for grid, even if ticks will not be used):
    if dim_uv[0] >= dim_uv[1]:
        u_bin, v_bin = np.max((2, np.floor(9 * dim_uv[1] / dim_uv[0]))), 9
    else:
        u_bin, v_bin = 9, np.max((2, np.floor(9 * dim_uv[0] / dim_uv[1])))
    axis.xaxis.set_major_locator(MaxNLocator(nbins=u_bin, integer=True))
    axis.yaxis.set_major_locator(MaxNLocator(nbins=v_bin, integer=True))
    # Hide axes label and ticks if wanted:
    if hideaxes:
        for tic in axis.xaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
            tic.label1On = tic.label2On = False
        for tic in axis.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
            tic.label1On = tic.label2On = False
    else:  # Set the axes ticks and labels:
        axis.set_xlabel('u-axis [nm]', fontsize=fontsize)
        axis.set_ylabel('v-axis [nm]', fontsize=fontsize)
        axis.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:.3g}'.format(x * sampling)))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:.3g}'.format(x * sampling)))
        axis.tick_params(axis='both', which='major', labelsize=fontsize)
    # Add annotation:
    if note:
        add_annotation(axis, label=note, fontsize=fontsize, stroke=stroke)
    # Add colorhweel:
    if colorwheel:
        add_colorwheel(axis)
    # Add colorbar:
    if cbar_mappable:
        # Construct colorbar:
        add_cbar(axis, mappable=cbar_mappable, label=cbar_label, fontsize=fontsize)
    # Tighten layout if axis was created here:
    if tight_layout:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout()
    # Return plotting axis:
    return axis