import tomopy
import numpy
import logging
from datetime import date
import sys
from p05tools.file import read_dat

logging.basicConfig(level=logging.INFO)

def rebin_stack(arr, factor):
    """
    Binning of the 2nd and 3rd dimension of a 3d array

    :param arr: <ndarray>
        3d input array
    :param factor: <int>
        binning factor

    :return: 3d ndarray of binned input array
    """
    new_shape = numpy.array(arr.shape) // factor
    # throws away right and/or bottom edge, if binning does not fit to array
    arr = arr[:, :factor * new_shape[1], :factor * new_shape[2]]
    shape = (arr.shape[0], new_shape[1], factor, new_shape[2], factor)
    return arr.reshape(shape).mean(-1).mean(-2)


def _chunk_list(listobj, chunksize):
    """
    Splits first dimension of a list into chunks.

    :param listobj: <list>
        input list
    :param chunksize: <int>
        number of item in one chunk

    :return: <list>
        chunked list
    """
    split_list = list()
    nchunks = len(listobj) // chunksize + 1
    for i in range(nchunks):
        split_list.append(listobj[i * chunksize:(i + 1) * chunksize])
    return split_list


def get_paths(scanname, foldername=None, year=date.today().year, application_number=None, commissioning=None):
    """
    Function to build filepaths to rawdata and processed data. This function works for the gpfs filesystem of the 
    DESY Maxwell-core cluster. Returns paths to raw an processed data as strings.

    :param scanname: <string>
        name on the scan (defined by raw data)
    :param foldername: <string> (optional)
        name of folder, where the processed data should go
    :param year: <int> (optional)
        year in which the raw data was taken (defaults to current year)
    :param application_number: <int> or <None>
        application number of the beamtime in which the scan was taken (set None if commissioning beamtime)
    :param commissioning: <string> or <None>
        Name of the commissioning beamtime (set None if regular beamtime)

    :return: <tuple> (string, string)
        raw_dir, reco_dir
    """

    basepath = '/asap3/petra3/gpfs/p05/' + str(year) + '/'
    reco_dir, raw_dir = None, None

    if application_number:
        raw_dir = basepath + 'data/' + str(application_number) + '/raw/' + scanname + '/'
        if foldername:
            reco_dir = basepath + 'data/' + str(application_number) + '/processed/' + foldername + '/'
        else:
            reco_dir = basepath + 'data/' + str(application_number) + '/processed/' + scanname + '/'
    if commissioning:
        raw_dir = basepath + 'commissioning/' + commissioning + '/raw/' + scanname + '/'
        if foldername:
            reco_dir = basepath + 'commissioning/' + commissioning + '/processed/' + foldername + '/'
        else:
            reco_dir = basepath + 'commissioning/' + commissioning + '/processed/' + scanname + '/'

    logging.info('raw_dir : %s' % raw_dir)
    logging.info('reco_dir : %s' % reco_dir)

    return raw_dir, reco_dir


def get_rawdata(scanlog_content, raw_dir, verbose=False):
    """
    Load raw data from gpfs filesystem in to python variables.

    :param scanlog_content: <dict>
        content of the scanlog (output of parse_scanlog)
    :param raw_dir: <string>
        path to the raw data
    :param verbose: <boolean> (optional)
        print progress in percent if True (default: False)

    :return: <tuple> (3D ndarray,  3D ndarray, 3D ndarray, 1D ndarray)
        proj, flat, dark, as 3D uint16 ndarrays
        theta as 3D float32 array
    """

    imageinfo = scanlog_content['imageinfo']
    counter = float(0)
    projlist, flatlist, darklist = list(), list(), list()
    proj_metadata = list()

    for image_number, logcontent in sorted(imageinfo.items()):
        if verbose:
            counter += 1
            sys.stdout.write('\r%4.1f%% done. Reading file: %s\n' % (100 * counter/len(imageinfo.items()),
                                                                   logcontent['imagename']))
        data = read_dat(raw_dir + logcontent['imagename'])
        if logcontent['imagetype'] == 'img':
            if logcontent['imageangle'] != 'nan':
                projlist.append(data)
                proj_metadata.append(logcontent)
        if logcontent['imagetype'] == 'ref':
            flatlist.append(data)
        if logcontent['imagetype'] == 'dark':
            darklist.append(data)
        logging.info(' read file %s.' % logcontent['imagename'])
    if verbose:
        sys.stdout.write('\n')

    proj = numpy.asarray(projlist, dtype=numpy.uint16)
    flat = numpy.asarray(flatlist, dtype=numpy.uint16)
    dark = numpy.asarray(darklist, dtype=numpy.uint16)
    theta = numpy.asarray([float(item['imageangle']) * numpy.pi / 180.0 for item in proj_metadata],
                          dtype=numpy.float32)

    return proj, flat, dark, theta


def get_metadata(scanlog_content):
    """
    Creates lists with metadata corresponding to the proj, flat and dark arrays.

    :param scanlog_content: <dict>
        content of the scanlog (output of parse_scanlog)

    :return: <tuple> (list, list, list)
        proj_metadata, flat_metadata, dark_metadata
    """

    scanimages = scanlog_content['scanimages']
    proj_metadata, flat_metadata, dark_metadata = list(), list(), list()

    for logcontent in sorted(scanimages.items()):
        if logcontent['imagetype'].decode('utf-8', errors='strict') == 'img':
            if logcontent['imageangle'] != 'nan':
                proj_metadata.append(logcontent)
        if logcontent['imagetype'].decode('utf-8', errors='strict') == 'ref':
            flat_metadata.append(logcontent)
        if logcontent['imagetype'].decode('utf-8', errors='strict') == 'dark':
            dark_metadata.append(logcontent)

    return proj_metadata, flat_metadata, dark_metadata


def correrlate_flat(proj, flat, verbose=False):
    """
    Normalize raw projection data based on best correlation between projections and flat field images.

    :param proj: <ndarray>
        3D stack of projections
    :param flat: <ndarray>
        3D flat field data
    :param verbose: <boolean> (optional)
        print progress in percent if True (default: False)

    :return: ndarray
        Normalized 3D tomographic data
    """

    proj = numpy.asarray(proj, numpy.float32)
    flat = numpy.asarray(flat, numpy.float32)
    flat_with_min = numpy.empty(proj.shape[0], dtype=numpy.uint32)
    flat_min = numpy.empty(proj.shape[0], dtype=numpy.float32)

    counter = 0

    for proj_num, single_proj in enumerate(proj):
        for flat_num, single_flat in enumerate(flat):
            # subtract flat from projection
            diff = single_proj - single_flat
            # calculate stddev along vertical axis
            min_stddev = numpy.min(numpy.std(diff, axis = 0))
            # sort out min stddev for each projection
            if flat_min[proj_num] > min_stddev or flat_num == 0:
                flat_with_min[proj_num] = flat_num
                flat_min[proj_num] = min_stddev
        if verbose:
            counter += 1
            sys.stdout.write('\r%4.1f%% done. Matching projection %g to flat %g.' % (
            100.0 * counter / proj.shape[0], proj_num, flat_with_min[proj_num]))
    if verbose:
        sys.stdout.write('\n')

    return flat_with_min


def normalize_corr(proj, flat, dark, flat_with_min, cutoff=None, ncore=None, out=None):
    """
    Normalize raw projection data based on best correlation between projections and flat field images
    :param proj: <ndarray>
        3D stack of projections
    :param flat: <ndarray>
        3D flat field data
    :param dark: <ndarray>
        3D dark field data
    :param flat_with_min: <list>
        list with position of best matching flat fields, output of correlate_flat()
    :param cutoff: <float> (optional)
        Permitted maximum vaue for the normalized data
    :param ncore: <int> (optional)
        Number of cores that will be assigned to jobs
    :param out: <ndarray> (optional)
        Output array for result.  If same as arr, process will be done in-place.

    :return: <ndarray>
        Normalized 3D tomographic data
    """
    import tomopy.util.mproc

    mean_dark = numpy.mean(dark, axis=0, dtype=numpy.float32)
    proj = numpy.asarray(proj, numpy.float32)
    flat = numpy.asarray(flat, numpy.float32)

    corresponding_flat = flat[flat_with_min]

    denom = numpy.subtract(corresponding_flat, mean_dark, corresponding_flat)
    denom[denom < 1e-6] = 1e-6
    proj -= mean_dark
    numpy.true_divide(proj, denom, proj)
    if cutoff:
        proj[proj > cutoff] = cutoff
    return proj

def chunk_reconstruct(chunksize, *args, **kwargs):
    """
    wrapper to tompy.recon. Reconstructs data in chunks using tomopy.recon.

    :param chunksize: <int>
        number of slices tha should be processed in one chunk
    :param args: <*>
        arguments of tomopy.recon
    :param kwargs: <**>
        kwargs of tomopy.recon

    :return: <ndarray>
        reconstructuted 3D object
    """
    proj = args[0]
    stacksize = proj.shape
    chunks = _chunk_list(numpy.arange(stacksize[1]), chunksize)
    rec = numpy.zeros([stacksize[1], stacksize[1], stacksize[2]], dtype=numpy.float32)
    for chunk in chunks:
        a, b = chunk[0], chunk[-1] + 1
        args[0] = proj[:,a,b]
        rec[a:b, :] = tomopy.recon(proj[:, a:b], *args, **kwargs)

    return rec
