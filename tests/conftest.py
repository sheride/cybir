"""Shared pytest fixtures for cybir tests."""

import numpy as np
import pytest

from cybir.core.types import CalabiYauLite


@pytest.fixture
def sample_int_nums():
    """A simple 2x2x2 symmetric intersection-number tensor for h11=2."""
    return np.array([[[0, 1], [1, 0]], [[1, 0], [0, 2]]])


@pytest.fixture
def sample_c2():
    """Typical second Chern class values for h11=2."""
    return np.array([24, 44])


@pytest.fixture
def sample_cyl(sample_int_nums, sample_c2):
    """A CalabiYauLite constructed with sample data."""
    return CalabiYauLite(
        int_nums=sample_int_nums,
        c2=sample_c2,
        label="phase_0",
    )
