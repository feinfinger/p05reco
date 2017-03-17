import os
import errno


def mkdir(foldername):
    """
    Creates a folder at the given location. Parent paths are created as well, if necessary.

    :param foldername: <str>
        Name of the folder that is to be created
    """
    try:
        os.makedirs(foldername)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(foldername):
            pass
        else:
            raise
