# -*- coding: utf-8 -*-
"""
#TODO: write this

"""

import logging

class Logging_Formatter(logging.Formatter):

    # Normal text colors
    green = "\x1b[32;1m";
    blue = "\x1b[34;1m";
    yellow = "\x1b[33;1m";
    red = "\x1b[31;1m";
    
    # Critical text format
    cyan = "\x1b[36;1m";
    magenta_bg = "\x1b[45;1m";
    magenta_underline = "\x1b[4m";
        
    reset = "\x1b[0m";
    format = "\n\t%(asctime)s @ (%(lineno)d) | [%(name)s]:\n%(message)s";

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: cyan + magenta_bg + magenta_underline + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno);
        formatter = logging.Formatter(log_fmt);
        return formatter.format(record);
    
    
    """
    console.debug("debug message")
    console.info("info message")
    console.warning("warning message")
    console.error("error message")
    console.critical("critical message")
    """