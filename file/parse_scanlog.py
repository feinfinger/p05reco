import re
import datetime
import numpy
import os
from io import open


def parse_scanlog(path):
    """
    Parses IDL generated scan.log files and stores the content into class variables and dictionaries:

    :param path: <string>
        full path to the scanlog file

    :return: scanlog_info: <dict> {'overview', 'imageinfo', 'petracurrent'}
        Dictionary, consisting of:
            * overview: scanparameters stored in the first part of the scan.log
            * imageinfo: Imagenumber, Imagename, Imagetype, corresponding angle and PETRA current and timestamps per image
            * petracurrent: PETRA current, timestamps for the whole scan.
    """

    overview = {}
    imageinfo = {}
    petracurrent = {}

    with open(path, encoding='latin-1') as f:
        log = f.readlines()

    # divide scanlog in 3 parts: - general overview - scan images - petra current
    skip = False
    part_imageinfo, part_overview = 0, 0
    for (linenumber, line) in enumerate(log):
        # if skip is False and 'p3current' in line:
        if skip is False and '/PETRA/Idc/Buffer-0/I.SCH' in line:
            part_overview = linenumber - 1
            skip = True
        if 'End of Scan' in line:
            part_imageinfo = linenumber - 1
            break
    assert(part_imageinfo or part_overview is not 0)

    # read part: general overview
    for line in log[:part_overview]:
        # replace : by =, since those are mixed in the scanlog
        line = line.replace(':', '=')
        if '=' in line:
            varname = line.strip().split('=')[0]
            varvalue = line.strip().split('=')[1]

            # try to convert to int - most demanding
            try:
                varvalue = numpy.int(varvalue)
            except ValueError:
                # if that fails try to onvert to float - less demanding
                try:
                    varvalue = numpy.float(varvalue)
                    # leave the value as string if conversions did not work
                except ValueError:
                    varvalue = varvalue
            # make a dict with varnames and varvalues
            overview[varname] = varvalue

    # read part: scan images
    block_start, block_end = None, None
    combinedinfo, imagetype, imagepath, imagenumber, imageangle, imagename = None, None, None, None, None, None
    t0_ss, t0_p3i, t0_tine, t1_ss, t1_p3i, t1_tine = None, None, None, None, None, None
    for line in log[part_overview:part_imageinfo]:
        # Two p3current or /PETRA/Idc/Buffer-0/I.SCH values need to be read out for one image, so we need to know if
        # we are in a 'block' in the log file
        if '*' in line:
            block_start = True
            block_end = False
            continue

        # Skip informationless line
        # if 'p3current' in line: continue
        if '/PETRA/Idc/Buffer-0/I.SCH' in line:
            continue

        # read p3 current
        if '@' in line:
            # extract words of this line (words may include '.')
            ss_values = re.findall(r"[\w.]+", line)
            # if this is the first readout in a block:
            if block_start:
                t0_ss = datetime.datetime.utcfromtimestamp(float(ss_values[0]) / 1e3)
                try:
                    t0_p3i = float(ss_values[1])
                except ValueError:
                    t0_p3i = None
                t0_tine = datetime.datetime.utcfromtimestamp(float(ss_values[2]) / 1e3)
                block_start = False
                # otherwise readout goes to these variables:
            else:
                t1_ss = datetime.datetime.utcfromtimestamp(float(ss_values[0]) / 1e3)
                try:
                    t1_p3i = float(ss_values[1])
                except ValueError:
                    t1_p3i = None
                t1_tine = datetime.datetime.utcfromtimestamp(float(ss_values[2]) / 1e3)
                block_end = True

        # if the line begins with any other than '*', '@' or 'p3current' / '/PETRA/Idc/Buffer-0/I.SCH'
        # it is a line containing the image Information
        else:
            combinedinfo = line.strip().split(' ')
            imagetype = combinedinfo[0]
            imagepath, imagename = os.path.split(combinedinfo[1])
            imagenumber = imagename.split('.')[0][-5:]
            if not imagetype == 'dark':
                imageangle = float(combinedinfo[-1])
            else:
                imageangle = None

        # store the data in a dict containing dicts
        if block_end:
            imageinfo[imagenumber] = {'imagenumber': imagenumber, 'imagename': imagename,
                                      'imageangle': imageangle, 'imagetype': imagetype,
                                      'imagepath': imagepath,
                                      't0_ss': t0_ss, 't0_p3i': t0_p3i, 't0_tine': t0_tine,
                                      't1_ss': t1_ss, 't1_p3i': t1_p3i, 't1_tine': t1_tine}

    # read part: p3current / /PETRA/Idc/Buffer-0/I.SCH
    t_ss, t_p3i, t_tine = [], [], []
    for line in log[part_imageinfo:]:
        if '@' in line:
            # extract words of this line (words may include '.')
            ss_values = re.findall(r"[\w.]+", line)
            t_ss.append(datetime.datetime.fromtimestamp(float(ss_values[0]) / 1e3))
            try:
                t_p3i.append(float(ss_values[1]))
            except ValueError:
                t_p3i.append(None)
            t_tine.append(datetime.datetime.fromtimestamp(float(ss_values[2]) / 1e3))

    petracurrent['t_ss'] = t_ss
    petracurrent['t_p3i'] = t_p3i
    petracurrent['t_tine'] = t_tine

    return {'overview': overview, 'imageinfo': imageinfo, 'petracurrent': petracurrent}
