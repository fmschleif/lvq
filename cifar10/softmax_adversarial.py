import numpy
import lasagne
from lasagne_train_softmax import build_model, load_data, iterate_minibatches
import theano
import theano.tensor as tensor

x = tensor.tensor4('x')
y = tensor.imatrix('y')
flat_y = tensor.flatten(y, outdim=1)

network = build_model(x)

test_out = lasagne.layers.get_output(network, deterministic=True)
test_prob = lasagne.nonlinearities.softmax(test_out)
test_nll = lasagne.objectives.categorical_crossentropy(test_prob, flat_y).mean()
test_misclass = 1.0 - lasagne.objectives.categorical_accuracy(test_prob, flat_y).mean()

with numpy.load('/Tmp/devries/softmax.npz') as f:
    param_values = [f['arr_%d' % i] for i in range(len(f.files))]
    lasagne.layers.set_all_param_values(network, param_values)

X_train, y_train, X_val, y_val, X_test, y_test = load_data()
    
val_fn = theano.function([x, y], [test_nll, test_misclass])

val_nll = 0.0
val_err = 0.0
val_batches = 0
for batch in iterate_minibatches(X_test, y_test, 500, shuffle=False):
    inputs, targets = batch
    nll, err = val_fn(inputs, targets)
    val_nll += nll
    val_err += err 
    val_batches += 1

print("  validation loss:\t\t{:.6f}".format(val_nll / val_batches))
print("  validation error:\t\t{:.6f} %".format(val_err*100 / val_batches))

from scipy.optimize import fmin_l_bfgs_b, minimize

prototypes = numpy.random.uniform(low=0.0, high=1.0, size=(10, 32, 32, 3))
for j in range(10):
    g_D = theano.grad(test_prob[0, j], x)
    f_conf = theano.function([x], [test_prob[0, j], g_D])
    
    #def f_wrap(x):
        #x_reshaped = x.reshape((1, 3, 32, 32))
        #v, g = f_conf(x_reshaped)
        #return v, g.reshape((3072,))
    ##start_x = numpy.ones((1, 1, 28, 28)).astype('float32')
    ##start_x = numpy.random.uniform(low=-1.0, high=1.0, size=(1, 3, 32, 32)).astype('float32')
    start_x = numpy.float32(X_test[0, :, :, :].reshape((1, 3, 32, 32)))
    init_x = start_x
    #print start_x.shape
    #print numpy.linalg.norm(f_wrap(start_x)[1])
    #r = minimize(f_wrap, start_x, jac=True, method='BFGS', options={'disp': True, 'ftol': 1e-15, 'gtol': 1e-15})
    #print r.fun
    #print r.nit
    mom = numpy.zeros((1, 3, 32, 32)) 
    for i in range(1000):
        conf, g = f_conf(start_x)
        if conf > 0.99:
            print i
            break
        mom = 1.0e5 * g + 0.9*mom
        start_x += numpy.float32(mom)
        start_x = numpy.maximum(numpy.maximum(start_x, init_x-3.0), 0.0)
        start_x = numpy.minimum(numpy.minimum(start_x, init_x+3.0), 255.0)
    print conf
    prototypes[j, :, :, :] = start_x.transpose([0, 2, 3, 1]).reshape((32, 32, 3))
    
  
def dispims_color(M, border=0, bordercolor=[0.0, 0.0, 0.0], *imshow_args, **imshow_keyargs):
    """ Display an array of rgb images. 

    The input array is assumed to have the shape numimages x numpixelsY x numpixelsX x 3
    """
    import pylab
    bordercolor = numpy.array(bordercolor)[None, None, :]
    numimages = len(M)
    M = M.copy()
    for i in range(M.shape[0]):
        M[i] -= M[i].flatten().min()
        M[i] /= M[i].flatten().max()
    height, width, three = M[0].shape
    assert three == 3
    n0 = 5#numpy.int(numpy.ceil(numpy.sqrt(numimages)))
    n1 = 2#numpy.int(numpy.ceil(numpy.sqrt(numimages)))
    im = numpy.array(bordercolor)*numpy.ones(
                             ((height+border)*n1+border,(width+border)*n0+border, 1),dtype='<f8')
    for i in range(n0):
        for j in range(n1):
            if i*n1+j < numimages:
                im[j*(height+border)+border:(j+1)*(height+border)+border,
                   i*(width+border)+border:(i+1)*(width+border)+border,:] = numpy.concatenate((
                  numpy.concatenate((M[i*n1+j,:,:,:],
                         bordercolor*numpy.ones((height,border,3),dtype=float)), 1),
                  bordercolor*numpy.ones((border,width+border,3),dtype=float)
                  ), 0)
    imshow_keyargs["interpolation"]="nearest"
    pylab.imshow(im, *imshow_args, **imshow_keyargs)
    pylab.savefig('softmax_adversarial.png', bbox_inches='tight')
    
dispims_color(prototypes)
