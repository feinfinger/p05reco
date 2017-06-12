import re
import datetime
import numpy
import os
from io import open
import logging

logger = logging.getLogger('reco_logger')

def parse_kit_scanlog(path):
    """
    Parses IDL generated scan.log files from kit scan script and returns
    content as a dictionary.

    :param path: <string>
        full path to the scanlog file

    :return: <dict>
    """


    with open(path, encoding='latin-1') as f:
        log = f.readlines()

    log_dict = {}
    for line in log:
        # remove newline and slpit at =
        log_item = line.strip("\n").split('=')
        log_key = log_item[0]
        # an array can start with a comma - strip that
        if log_item[1][0] == ',':
            log_item[1] = log_item[1][1::]
        try:
            log_value = float(log_item[1])
            log_dict[log_key] = log_value
        except ValueError:
            try:
                log_value = numpy.fromstring(log_item[1], sep=',')
                # strings are read in as empty arrays withe numpy.fromstring
                if log_value.size == 0:
                    raise ValueError
                log_dict[log_key] = log_value
            except ValueError:
                try:
                    log_value = str(log_item[1])
                    log_dict[log_key] = log_value
                except ValueError:
                    raise ValueError("couldn't convert log file line {}".format(log_item))

    logger.info('raw scanlog: {}'.format(path))

    return log_dict
