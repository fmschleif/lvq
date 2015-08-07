import theano
import numpy 

from blocks.bricks import Initializable
from blocks.utils import shared_floatx_nans
from blocks.bricks.base import application

import theano.tensor as tensor

class LVQ(Initializable):

    def __init__(self, n_classes, dim, n_protos=1, **kwargs):
        super(LVQ, self).__init__(**kwargs)
        self.n_classes = n_classes
        self.n_protos= n_protos
        self.dim = dim

    def _allocate(self):
        W = shared_floatx_nans((self.n_classes*self.n_protos, self.dim), name='prototypes')
        self.parameters.append(W)

    def _initialize(self):
        W, = self.parameters
        self.weights_init.initialize(W, self.rng)
        
    @application(inputs=['x', 'mask'], outputs=['cost', 'misclass'])
    def apply(self, x, mask):
        W, = self.parameters
        D = ((W**2).sum(axis=1, keepdims=True).T + (x**2).sum(axis=1, keepdims=True) - 2*tensor.dot(x, W.T))
        self.add_auxiliary_variable(D, name='D')
        d_correct = (D + (1-mask)*numpy.float32(2e25)).min(axis=1)
        d_incorrect = (D + mask*numpy.float32(2e25)).min(axis=1)
        
        c = (d_correct - d_incorrect)/(d_correct+d_incorrect)
        cost = c.mean()
        misclass = (tensor.switch(d_correct - d_incorrect < 0, 0.0, 1.0).sum())/mask.shape[0]
        return cost, misclass
        
    