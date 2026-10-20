import numpy as np
from satproc.indices import normalized_difference_arrays

def test_normalized_difference():
    a = np.array([[3.0, 1.0]], dtype=np.float32)
    b = np.array([[1.0, 1.0]], dtype=np.float32)
    out = normalized_difference_arrays(a, b)
    np.testing.assert_allclose(out[0, 0], 0.5)
    np.testing.assert_allclose(out[0, 1], 0.0)

def test_zero_denominator_becomes_nan():
    a = np.array([[1.0]], dtype=np.float32)
    b = np.array([[-1.0]], dtype=np.float32)
    out = normalized_difference_arrays(a, b)
    assert np.isnan(out[0, 0])
