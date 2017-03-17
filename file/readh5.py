import h5py
import numpy

def readh5(filepath, rows=None):
    if rows:
        if isinstance(rows, list):
            rows = rows
        else:
            rows = [rows]
    else:
        rows = None

    with h5py.File(filepath, "r") as f:
        # This works only if there is only one dataset in the file. (First is taken, other are ignored).
        dsetname = list(f.keys())[0]
        h5dset = f.get(dsetname)
        if rows:
            data = numpy.array(h5dset)[rows]
        else:
            data = numpy.array(h5dset)
        attrs_keys = h5dset.attrs.keys()
        attrs_values = h5dset.attrs.values()
        metadata = dict(zip(attrs_keys, attrs_values))
    return data, metadata