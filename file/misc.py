import os
import errno
import glob


def mkdir(foldername):
    """
    Creates a folder at the given location. Parent paths are created as well,
    if necessary.

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

def find(pattern):
    return glob.glob(pattern)

def gpfsFindIdentifier(identifier, basepath='/asap3/petra3/gpfs/p05/'):
    """
    Searches the gpfs p05 folder for the filepath of a given application ID
    or commissioning tag. Returns full path if application ID or commissioning
    tag was found.

    :param identifier: <int> or <str>
        (any part of) application ID or commissiong identifier of the current
        project
    :param basepath: <str> (optional)
        path to the p05 data folder
        defaults to: /asap3/petra3/gpfs/p05/

    :return <str>
        absolute path to the application or commissioning folder
    """

    # first make a list of all the year subfolders in the gpfs p05 folder
    years_dirs = [name for name in os.listdir(basepath) if
            os.path.isdir(basepath + name)]

    # make one list of all subfolders in data and commissioning folder in all
    # years
    result = []
    for year in years_dirs:
        for beamtime_type in ['data', 'commissioning']:
            lookup_path = basepath + os.sep + year + os.sep + beamtime_type + os.sep
            appid_dirs = [lookup_path + name for name in
                    os.listdir(lookup_path) if os.path.isdir(lookup_path +
                        name)]
            for item in appid_dirs:
                result.append(item)

    # find identifier and return result or raise error if none / too many
    # instances were found
    num_occur = 0
    for item in result:
        if item.find(str(identifier)) > -1:
            result_path = item + os.sep
            num_occur +=1

    if num_occur != 1:
        raise ValueError('found {} ocurrences of identifier or' +
                'Commissioning Tag {}'.format(num_occur, identifier))

    return result_path
