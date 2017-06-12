import re
import datetime
import numpy
import os
from io import open
import logging
import pdb

logger = logging.getLogger('reco_logger')

def parse_kit_scanlog(path):
    """
    Parses IDL generated scan.log files frim kit scan script and returns
    content as a dictionary:

    :param path: <string>
        full path to the scanlog file

    :return: scanlog_info: <dict>
    """


    with open(path, encoding='latin-1') as f:
        log = f.readlines()
    
    pdb.set_trace()
    log_dict = {}
    for line in log:
        log_item = line.strip("\n").split('=')
        log_key = log_item[0]
        if log_item[1][0] == ',':
            log_item[1] = log_item[1][1::]
        try:
            log_value = float(log_item[1])
            log_dict[log_key] = log_value
        except ValueError:
            try:
                log_value = numpy.fromstring(log_item[1], sep=',')
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
