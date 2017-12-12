import numpy


def rebin(arr, factor):
    """
    Rebins 2d array by an integer factor.

    :param arr: <ndarray>
        2D array to be binned
    :param factor: <int>
        integer factor for binning

    :return: <ndarray>
        binned 2D array
    """
    new_shape = numpy.array(arr.shape) // factor
    # throws away right and/or bottom edge, if binning does not fit to array
    arr = arr[:factor*new_shape[0], :factor*new_shape[1]]
    shape = (new_shape[0], arr.shape[0] // new_shape[0],
             new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).mean(-1).mean(1)
