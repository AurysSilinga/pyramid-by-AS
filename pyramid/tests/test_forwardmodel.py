# -*- coding: utf-8 -*-
"""Testcase for the forwardmodel module"""

import os
import unittest

import numpy as np
from numpy.testing import assert_allclose

from pyramid.dataset import DataSet
from pyramid.forwardmodel import ForwardModel
from pyramid.phasemap import PhaseMap
from pyramid.projector import SimpleProjector


class TestCaseForwardModel(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_forwardmodel')
        self.a = 10.
        self.dim = (4, 5, 6)
        self.mask = np.zeros(self.dim, dtype=bool)
        self.mask[1:-1, 1:-1, 1:-1] = True
        self.data = DataSet(self.a, self.dim, mask=self.mask)
        self.projector = SimpleProjector(self.dim)
        self.phase_map = PhaseMap.load_from_hdf5(os.path.join(self.path, 'phase_map_ref.hdf5'))
        self.data.append(self.phase_map, self.projector)
        self.data.append(self.phase_map, self.projector)
        self.fwd_model = ForwardModel(self.data)

    def tearDown(self):
        self.path = None
        self.a = None
        self.dim = None
        self.mask = None
        self.data = None
        self.projector = None
        self.phase_map = None
        self.fwdmodel = None

    def test_call(self):
        n = self.fwd_model.n
        result = self.fwd_model(np.ones(n))
        hp = self.data.hook_points
        assert_allclose(result[hp[0]:hp[1]], self.phase_map.phase.flatten(), atol=1E-7,
                        err_msg='Unexpected behavior in __call__()!')
        assert_allclose(result[hp[1]:hp[2]], self.phase_map.phase.flatten(), atol=1E-7,
                        err_msg='Unexpected behavior in __call__()!')

    def test_jac_dot(self):
        n = self.fwd_model.n
        vector = np.ones(n)
        result = self.fwd_model(vector)
        result_jac = self.fwd_model.jac_dot(None, vector)
        assert_allclose(result, result_jac, atol=1E-7,
                        err_msg='Inconsistency between __call__() and jac_dot()!')
        jac = np.array([self.fwd_model.jac_dot(None, np.eye(n)[:, i]) for i in range(n)]).T
        hp = self.data.hook_points
        assert_allclose(jac[hp[0]:hp[1], :], jac[hp[1]:hp[2], :], atol=1E-7,
                        err_msg='Unexpected behaviour in the the jacobi matrix!')
        jac_ref = np.load(os.path.join(self.path, 'jac.npy'))
        assert_allclose(jac, jac_ref, atol=1E-7,
                        err_msg='Unexpected behaviour in the the jacobi matrix!')

    def test_jac_T_dot(self):
        m = self.fwd_model.m
        jac_T = np.array([self.fwd_model.jac_T_dot(None, np.eye(m)[:, i]) for i in range(m)]).T
        jac_T_ref = np.load(os.path.join(self.path, 'jac.npy')).T
        assert_allclose(jac_T, jac_T_ref, atol=1E-7,
                        err_msg='Unexpected behaviour in the the transposed jacobi matrix!')


if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)