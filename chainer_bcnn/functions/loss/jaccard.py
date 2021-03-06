from __future__ import absolute_import

from chainer import backends
from chainer import functions

from ._helper import to_onehot


def jaccard(y, t, normalize=True, class_weight=None,
            ignore_label=-1, reduce='mean', eps=1e-08):
    """ Differentable Jaccard index.

    Args:
        y (~chainer.Variable): Probability
        t (~numpy.ndarray or ~cupy.ndarray): Ground-truth label
        normalize (bool, optional): If True, calculate the jaccard indices for each class and take the average. Defaults to True.
        class_weight (list or ndarray, optional): Defaults to None.
        ignore_label (int, optional): Defaults to -1.
        reduce (str, optional): Defaults to 'mean'.
        eps (float, optional): Defaults to 1e-08.
    """
    xp = backends.cuda.get_array_module(y)

    if class_weight is not None:
        class_weight = xp.asarray(class_weight, y.dtype)

    b, c = y.shape[:2]
    t_onehot = to_onehot(t, n_class=c)

    y = y.reshape(b, c, -1)
    t_onehot = t_onehot.reshape(b, c, -1)

    if ignore_label != -1:
        t_onehot = functions.concat( (t_onehot[:, :ignore_label], t_onehot[:, ignore_label + 1:]), axis=1)
        y = functions.concat( (y[:, :ignore_label], y[:, ignore_label + 1:]), axis=1)

    intersection = y * t_onehot
    cardinality = y + t_onehot

    # NOTE: Another masking way
    # mask = (t != ignore_label).astype(y.dtype)
    # mask = xp.tile(xp.expand_dims(mask, axis=1), (1, c, 1))
    # mask = mask.reshape(b, c, -1)

    # intersection *= mask
    # cardinality *= mask

    if normalize:  # NOTE: channel-wise
        intersection = functions.sum(intersection, axis=-1)
        cardinality = functions.sum(cardinality, axis=-1)
        union = cardinality - intersection
        ret = (2. * intersection / (union + eps))
        if class_weight is not None:
            ret *= class_weight
        ret = xp.mean(ret, axis=1)

    else:
        intersection = functions.sum(intersection, axis=(0, 2))
        cardinality = functions.sum(cardinality, axis=(0, 2))
        union = cardinality - intersection
        ret = (2. * intersection / (union + eps))
        if class_weight is not None:
            ret *= class_weight

    if reduce == 'mean':
        ret = functions.mean(ret)
    else:
        raise NotImplementedError('unsupported reduce type..')

    return ret


def softmax_jaccard(y, t, normalize=True, class_weight=None,
                   ignore_label=-1, reduce='mean', eps=1e-08):
    """ Differentable Jaccard index with Softmax pre-activates.

    Args:
        y (~chainer.Variable): Logits
        t (~numpy.ndarray or ~cupy.ndarray): Ground-truth label
        normalize (bool, optional): If True, calculate the jaccard indices for each class and take the average. Defaults to True.
        class_weight (list or ndarray, optional): Defaults to None.
        ignore_label (int, optional): Defaults to -1.
        reduce (str, optional): Defaults to 'mean'.
        eps (float, optional): Defaults to 1e-08.
    """
    y = functions.softmax(y, axis=1)
    return jaccard(y, t, normalize, class_weight,
                   ignore_label, reduce, eps)


def softmax_jaccard_loss(y, t, normalize=True, class_weight=None,
                         ignore_label=-1, reduce='mean', eps=1e-08):
    """ Differentable Jaccard-index loss with Softmax pre-activates.

    Args:
        y (~chainer.Variable): Logits
        t (~numpy.ndarray or ~cupy.ndarray): Ground-truth label
        normalize (bool, optional): If True, calculate the jaccard indices for each class and take the average. Defaults to True.
        class_weight (list or ndarray, optional): Defaults to None.
        ignore_label (int, optional): Defaults to -1.
        reduce (str, optional): Defaults to 'mean'.
        eps (float, optional): Defaults to 1e-08.
    """
    return 1.0 - softmax_jaccard(y, t, normalize, class_weight,
                                 ignore_label, reduce, eps)


def sigmoid_jaccard(y, t, *args, **kwards):
    raise NotImplementedError()


def sigmoid_jaccard_loss(y, t, *args, **kwards):
    raise NotImplementedError()
