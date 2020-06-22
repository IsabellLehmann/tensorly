import numpy as np
import pytest

import tensorly as tl
from ..candecomp_parafac import (
    parafac, non_negative_parafac, initialize_factors,
    sample_khatri_rao, randomised_parafac)
from ...kruskal_tensor import kruskal_to_tensor
from ...random import check_random_state, random_kruskal
from ...tenalg import khatri_rao
from ... import backend as T
from ...testing import assert_array_equal, assert_


def test_parafac():
    """Test for the CANDECOMP-PARAFAC decomposition
    """
    rng = check_random_state(1234)
    tol_norm_2 = 10e-2
    tol_max_abs = 10e-2
    tensor = T.tensor(rng.random_sample((3, 4, 2)))
    rec_svd = parafac(tensor, rank=4, n_iter_max=200, init='svd', tol=10e-5)
    rec_random = parafac(tensor, rank=4, n_iter_max=200, init='random', tol=10e-5, random_state=1234, verbose=0)
    rec_svd = kruskal_to_tensor(rec_svd)
    rec_random = kruskal_to_tensor(rec_random)
    error = T.norm(rec_svd - tensor, 2)
    error /= T.norm(tensor, 2)
    assert_(error < tol_norm_2,
            'norm 2 of reconstruction higher than tol')
    # Test the max abs difference between the reconstruction and the tensor
    assert_(T.max(T.abs(rec_svd - tensor)) < tol_max_abs,
            'abs norm of reconstruction error higher than tol')

    # Test fixing mode 0 or 1 with given init
    fixed_tensor = random_kruskal((3, 4, 2), rank=2)
    rec_svd_fixed_mode_0 = parafac(tensor, rank=2, n_iter_max=2, init=fixed_tensor, fixed_modes=[0])
    rec_svd_fixed_mode_1 = parafac(tensor, rank=2, n_iter_max=2, init=fixed_tensor, fixed_modes=[1])
    # Check if modified after 2 iterations
    tol_fixed = 1e-16
    assert_(T.norm(rec_svd_fixed_mode_0.factors[0] - fixed_tensor.factors[0]) < tol_fixed,
            'Fixed mode 0 was modified in candecomp_parafac')
   assert_array_equal(rec_svd_fixed_mode_1.factors[1], fixed_tensor.factors[1]) 
            'Fixed mode 1 was modified in candecomp_parafac')

    rec_orthogonal = parafac(tensor, rank=4, n_iter_max=100, init='svd', tol=10e-5, random_state=1234, orthogonalise=True, verbose=0)
    rec_orthogonal = kruskal_to_tensor(rec_orthogonal)
    tol_norm_2 = 10e-2
    tol_max_abs = 10e-2
    error = T.norm(rec_orthogonal - tensor, 2)
    error /= T.norm(tensor, 2)
    assert_(error < tol_norm_2,
            'l2 Reconstruction error for orthogonalise=True too high')
    assert_(T.max(T.abs(rec_svd - rec_random)) < tol_max_abs,
            'abs Reconstruction error for orthogonalise=True too high')
    
    
    rec_sparse, sparse_component = parafac(tensor, rank=4, n_iter_max=200, init='svd', tol=10e-5, sparsity = 0.9)
    rec_sparse = kruskal_to_tensor(rec_sparse) + sparse_component
    tol_norm_2 = 10e-2
    tol_max_abs = 10e-2
    error = T.norm(rec_sparse - tensor, 2)
    error /= T.norm(tensor, 2)
    assert_(error < tol_norm_2,
            'l2 Reconstruction error for sparsity!=None too high')
    assert_(T.max(T.abs(rec_sparse - tensor)) < tol_max_abs,
            'abs Reconstruction error for sparsity!=None too high')

    # Should also converge with orthogonolise = True
    tol_norm_2 = 10e-1
    tol_max_abs = 10e-1
    error = T.norm(rec_svd - rec_random, 2)
    error /= T.norm(rec_svd, 2)
    assert_(error < tol_norm_2,
            'norm 2 of difference between svd and random init too high')
    assert_(T.max(T.abs(rec_svd - rec_random)) < tol_max_abs,
            'abs norm of difference between svd and random init too high')

    with np.testing.assert_raises(ValueError):
        rank = 4
        _ = initialize_factors(tensor, rank, init='bogus init type')

    # Test with rank-1 decomposition
    tol = 10e-3
    tensor = random_kruskal((3, 4, 2), rank=1, full=True) 
    rec = kruskal_to_tensor(parafac(tensor, rank=1))
    error = T.norm(tensor - rec, 2)/T.norm(tensor)
    assert_(error < tol)


def test_masked_parafac():
    """Test for the masked CANDECOMP-PARAFAC decomposition.
    This checks that a mask of 1's is identical to the unmasked case.
    """
    rng = check_random_state(1234)
    tensor = T.tensor(rng.random_sample((3, 3, 3)))
    mask = T.tensor(np.ones((3, 3, 3)))

    mask_fact = parafac(tensor, rank=2, mask=mask)
    fact = parafac(tensor, rank=2)
    diff = kruskal_to_tensor(mask_fact) - kruskal_to_tensor(fact)
    assert_(T.norm(diff) < 0.01, 'norm 2 of reconstruction higher than 0.01')


def test_non_negative_parafac():
    """Test for non-negative PARAFAC

    TODO: more rigorous test
    """
    tol_norm_2 = 10e-1
    tol_max_abs = 1
    rng = check_random_state(1234)
    tensor = T.tensor(rng.random_sample((3, 3, 3))+1)
    res = parafac(tensor, rank=3, n_iter_max=120)
    nn_res = non_negative_parafac(tensor, rank=3, n_iter_max=100, tol=10e-4, init='svd', verbose=0)

    # Make sure all components are positive
    _, nn_factors = nn_res
    for factor in nn_factors:
        assert_(T.all(factor >= 0))

    reconstructed_tensor = kruskal_to_tensor(res)
    nn_reconstructed_tensor = kruskal_to_tensor(nn_res)
    error = T.norm(reconstructed_tensor - nn_reconstructed_tensor, 2)
    error /= T.norm(reconstructed_tensor, 2)
    assert_(error < tol_norm_2,
            'norm 2 of reconstruction higher than tol')

    # Test the max abs difference between the reconstruction and the tensor
    assert_(T.max(T.abs(reconstructed_tensor - nn_reconstructed_tensor)) < tol_max_abs,
            'abs norm of reconstruction error higher than tol')

    # Test fixing mode 0 or 1 with given init
    fixed_tensor = random_kruskal((3, 3, 3), rank=2)
    for factor in fixed_tensor[1]:
        factor = T.abs(factor)
    rec_svd_fixed_mode_0 = non_negative_parafac(tensor, rank=2, n_iter_max=2, init=fixed_tensor, fixed_modes=[0])
    rec_svd_fixed_mode_1 = non_negative_parafac(tensor, rank=2, n_iter_max=2, init=fixed_tensor, fixed_modes=[1])
    # Check if modified after 2 iterations
    tol_fixed = 1e-16
    assert_(T.norm(rec_svd_fixed_mode_0.factors[0] - fixed_tensor.factors[0]) < tol_fixed,
            'Fixed mode 0 was modified in candecomp_parafac')
    assert_(T.norm(rec_svd_fixed_mode_1.factors[1] - fixed_tensor.factors[1]) < tol_fixed,
            'Fixed mode 1 was modified in candecomp_parafac')

    res_svd = non_negative_parafac(tensor, rank=3, n_iter_max=100,
                                       tol=10e-4, init='svd')
    res_random = non_negative_parafac(tensor, rank=3, n_iter_max=100, tol=10e-4,
                                          init='random', random_state=1234, verbose=0)
    rec_svd = kruskal_to_tensor(res_svd)
    rec_random = kruskal_to_tensor(res_random)
    error = T.norm(rec_svd - rec_random, 2)
    error /= T.norm(rec_svd, 2)
    assert_(error < tol_norm_2,
            'norm 2 of difference between svd and random init too high')
    assert_(T.max(T.abs(rec_svd - rec_random)) < tol_max_abs,
            'abs norm of difference between svd and random init too high')


@pytest.mark.xfail(tl.get_backend() == 'tensorflow', reason='Fails on tensorflow')
def test_sample_khatri_rao():
    """ Test for sample_khatri_rao
    """

    rng = check_random_state(1234)
    t_shape = (8, 9, 10)
    rank = 3
    tensor = T.tensor(rng.random_sample(t_shape)+1)
    weights, factors = parafac(tensor, rank=rank, n_iter_max=120)
    num_samples = 4
    skip_matrix = 1
    sampled_kr, sampled_indices, sampled_rows = sample_khatri_rao(factors, num_samples, skip_matrix=skip_matrix,
                                                                  return_sampled_rows=True)
    assert_(T.shape(sampled_kr) == (num_samples, rank),
              'Sampled shape of khatri-rao product is inconsistent')
    assert_(np.max(sampled_rows) < (t_shape[0] * t_shape[2]),
              'Largest sampled row index is bigger than number of columns of'
              'unfolded matrix')
    assert_(np.min(sampled_rows) >= 0,
              'Smallest sampled row index index is smaller than 0')
    true_kr = khatri_rao(factors, skip_matrix=skip_matrix)
    for ix, j in enumerate(sampled_rows):
        assert_array_equal(true_kr[j], sampled_kr[int(ix)], err_msg='Sampled khatri_rao product doesnt correspond to product')


@pytest.mark.xfail(tl.get_backend() == 'tensorflow', reason='Fails on tensorflow')
def test_randomised_parafac():
    """ Test for randomised_parafac
    """
    rng = check_random_state(1234)
    t_shape = (10, 10, 10)
    n_samples = 8
    tensor = T.tensor(rng.random_sample(t_shape))
    rank = 4
    _, factors_svd = randomised_parafac(tensor, rank, n_samples, n_iter_max=1000,
                                     init='svd', tol=10e-5, verbose=True)
    for i, f in enumerate(factors_svd):
        assert_(T.shape(f) == (t_shape[i], rank),
                  'Factors are of incorrect size')

    # test tensor reconstructed properly
    tolerance = 0.05
    tensor = random_kruskal(shape=(10, 10, 10), rank=4, full=True)
    kruskal_tensor = randomised_parafac(tensor, rank=5, n_samples=100, max_stagnation=20, n_iter_max=100, tol=0, verbose=0)
    reconstruction = kruskal_to_tensor(kruskal_tensor)
    error = float(T.norm(reconstruction - tensor, 2)/T.norm(tensor, 2))
    assert_(error < tolerance, msg='reconstruction of {} (higher than tolerance of {})'.format(error, tolerance))
