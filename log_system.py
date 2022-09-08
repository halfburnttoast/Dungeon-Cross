import os
import time
import logging
import traceback
import platform
from dungeon_cross import VERSION

def log_sys_info() -> None:
    """Logs system info."""
    logging.info(f"Build: {VERSION}")
    logging.info(time.ctime())
    logging.info(platform.platform())
    logging.info(f"Python Version: {platform.python_version()}")
    logging.info(f"Directory: {os.getcwd()}")


def exception_handler_hook(ex_type, ex_val, ex_tb):
    """Extend the exception handler to log unhandled exceptions"""
    logging.critical("Unhandled exception: ", exc_info = (ex_type, ex_val, ex_tb))
    print(''.join(traceback.format_exception(ex_type, ex_val, ex_tb)))
