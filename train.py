######################
# Model 
######################

import theano.tensor as tensor
from lvq import LVQ
from blocks.bricks import MLP, Linear, Sequence
from blocks.bricks import Rectifier, Softmax, LinearMaxout
from blocks.bricks.cost import MisclassificationRate
from blocks.initialization import Uniform, Constant
from blocks.model import Model

x = tensor.tensor4('features')
x = x.reshape((x.shape[0], 784))
#mask = tensor.fmatrix('mask')
y = tensor.imatrix('targets')
y = y.flatten()

l1 = LinearMaxout(784, 200, 10, name='l1')
l1.weights_init = Uniform(0.0, 0.1)
l1.biases_init = Constant(0.0)
l1.initialize()
l2 = LinearMaxout(200, 200, 10, name='l2')
l2.weights_init = Uniform(0.0, 0.1)
l2.biases_init = Constant(0.0)
l2.initialize()
l3 = Linear(200, 10, name='l3')
l3.weights_init = Uniform(0.0, 0.1)
l3.biases_init = Constant(0.0)
l3.initialize()
out = l3.apply(l2.apply(l1.apply(x)))

#mlp = MLP(dims=[784, 1000, 1000, 1000, 10], activations=[Rectifier().apply, Rectifier().apply, Rectifier().apply, None])
#mlp.weights_init = Uniform(0, 0.01)
#mlp.biases_init = Constant(0.0)
#mlp.initialize()

#out = mlp.apply(x)

#lvq = LVQ(10, 50)
#lvq.weights_init = Uniform(0, 0.1)
#lvq.initialize()
#loss, misclass = lvq.apply(out, mask)

#loss.name = 'loss'
#misclass.name = 'misclass'

loss = Softmax().categorical_cross_entropy(y, out)
loss.name = 'nll'
misclass = MisclassificationRate().apply(y, out)
misclass.name = 'misclass'

model = Model(loss)

######################
# Data
######################
import numpy 
#from mnist import MNIST
from fuel.datasets.mnist import MNIST
from fuel.streams import DataStream
from fuel.schemes import ShuffledScheme
from fuel.transformers import Mapping, Rename

mnist_train = MNIST(['train'])
mnist_valid = MNIST(['test'])

batch_size = 500
num_protos = 10

def mask(x):
    y= x[1]
    mask = numpy.zeros((len(y), num_protos)).astype('float32')
    for i, label in enumerate(y):
        mask[i, label:label+1] = 1
    return (mask,)

train_stream = DataStream(mnist_train, iteration_scheme=ShuffledScheme(mnist_train.num_examples, batch_size))
#train_stream = Rename(train_stream, {'features': 'features', 'targets': 'targets'})
valid_stream = DataStream(mnist_valid, iteration_scheme=ShuffledScheme(mnist_valid.num_examples, batch_size))

######################
# Training
######################


from blocks.main_loop import MainLoop
from blocks.extensions import FinishAfter,Timing, Printing
from blocks.extensions.monitoring import DataStreamMonitoring
from blocks.algorithms import GradientDescent, Momentum, RMSProp

main_loop = MainLoop(
     model=model,
     data_stream=train_stream,
     algorithm=GradientDescent(
        cost=loss, params=model.parameters, step_rule=Momentum(1e-2, 0.95)),
     extensions=[FinishAfter(after_n_epochs=1000),
                 DataStreamMonitoring(
                    variables=[loss, misclass],
                    data_stream=train_stream,
                    prefix='train'),
                 DataStreamMonitoring(
                    variables=[loss, misclass],
                    data_stream=valid_stream,
                    prefix='valid'),
                 Timing(), 
                 Printing(after_epoch=True)])
main_loop.run()
