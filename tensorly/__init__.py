__version__ = '0.4.3'
import sys

from .base import unfold, fold
from .base import tensor_to_vec, vec_to_tensor
from .base import partial_unfold, partial_fold
from .base import partial_tensor_to_vec, partial_vec_to_tensor

from .kruskal_tensor import kruskal_to_tensor, kruskal_to_unfolded, kruskal_to_vec
from .tucker_tensor import tucker_to_tensor, tucker_to_unfolded, tucker_to_vec
from .mps_tensor import mps_to_tensor, mps_to_unfolded, mps_to_vec

from .backend import (BackendManager, set_backend, get_backend,
                      backend_context, __getattr__)
from .backend import __dir__ as backend_dir

# We need to add the above methods to the backend dir
static_items = list(sys.modules[__name__].__dict__.keys())
def __dir__():
    return backend_dir() + static_items
