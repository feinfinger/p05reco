import numpy
from io import open


def _readfile(path, dtype, dimsize):
    """
    Helper routine for p05tools.file.read_dat. Reads out binary file

    :param path: <str>
        Path to the data file
    :param dtype: <str>
        numpy dtype of the data
    :param dimsize: <list>
        list of the data dimensions

    :return: <ndarray>
        Data from the file
    """
    with open(path, 'rb') as f:
        # Now seek forward until beginning of file or we get a \n
        # ch = 0
        # while ch != '\n':
        #     ch = f.read(1)
        next(f)
        # load data
        data = numpy.frombuffer(f.read(), numpy.dtype(dtype))
        # shape new array on Fortran column major order (used by IDL)
        # data = numpy.reshape(data, dimsize, order='F')
        data = numpy.flipud(numpy.reshape(data, dimsize[::-1]))

    return data


def _checkheader(path):
    """
    Helper routine for p05tools.file.read_dat. Reads header and returns file info to class variables.

    :param path: <str>
        Path to the data file

    :return: <tuple >(str, list)
        Returns the numpy.dtype of the data as string and a list with the data dimensions.
    """
    with open(path, 'r', encoding="latin-1") as f:
        # read first 100 characters of the file (header).
        # f_100 = f.read(100)  # TAG
        # read first 100 characters, split EOL
        # first100char = f_100.split('\r\n')
        # header = first100char[0]
        header = f.readline()
        # split header at underscores
        headerlist = header.split('_')
        # get header information
        dimensions = int(headerlist[1])
        idldtype = headerlist[2]
        # get data dimensions
        dimsize = [0] * dimensions
        for i in range(dimensions):
            dimsize[i] = int(headerlist[3 + i])
        # convert idl data type to python dtype
        dtype_idl2numpy = {'B': 'uint8', 'I': 'int16', 'U': 'uint16',
                           'L': 'int32', 'F': 'float32', 'D': 'float64',
                           'C': 'complex64'}
        dtype = dtype_idl2numpy[idldtype]
    return dtype, dimsize


def read_dat(path):
    """
    Load IDL tomo binary image data from file into a python ndarray.

    :param path: <str>
        Path to the data file

    :return: <ndarray>
        Data from the file
    """
    dtype, dimsize = _checkheader(path)
    return _readfile(path, dtype, dimsize)
