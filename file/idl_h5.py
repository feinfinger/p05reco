from p05tools.file.read_dat import read_dat
from p05tools.file.parse_scanlog import parse_scanlog
import h5py
import os
import errno
import datetime


class Idl2H5:
    '''Creates a h5 file from a IDL .img, .ref, .dar file. Full path to a file and the scanlog must be supplied.
    The scanlog will be parsed and the information is added as metadata to the h5 file. A file generated with Idl2H5
    can be read out with the class ReadH5.'''
    def __init__(self, scanlogpath=None, rawdatapath = None, h5path=None):
        self.scanlogpath = scanlogpath
        self.rawdatapath = rawdatapath
        self.h5path = h5path
        self.scanlog = None
        if scanlogpath:
            self.scanlog = parse_scanlog(self.scanlogpath)

    def convertscan2h5(self):
        for image in sorted(self.scanlog.scanimages):
            data = read_dat(self.rawdatapath + self.scanlog.scanimages[image]['imagename']).data
            metadata = self.scanlog.scanimages[image]
            self.createh5dataset(data, metadata)

    def createh5dataset(self, data, metadata):
        try:
            os.mkdir(self.h5path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(self.h5path):
                pass
            else:
                raise
        h5filename = metadata['imagename'].split('.')[0] + '.h5'
        with h5py.File(self.h5path + h5filename, "w") as f:
            h5dset = f.create_dataset(metadata['imagename'], (data.shape), data=data)
            for attribute in sorted(metadata):
                if isinstance(metadata[attribute], datetime.datetime):
                    metadata[attribute] = (metadata[attribute] - datetime.datetime(1970, 1, 1)).total_seconds()
                if not metadata[attribute]:
                    metadata[attribute] = 'nan'.encode('utf-8', errors='strict')
                if isinstance(metadata[attribute], str):
                    metadata[attribute] = metadata[attribute].encode('utf-8', errors='strict')
                h5dset.attrs.create(attribute, metadata[attribute])
