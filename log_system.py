import os
import sys
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

def init_logging(log_level: int = logging.INFO):
    lfmt = "%(levelname)s [%(funcName)s]: %(message)s"
    log_file_name = 'dungeon_cross.log'
    log_file_path = ''
    if hasattr(sys, "_MEIPASS"):
        plat = sys.platform
        log_file_dir = ''
        if plat == "darwin":
            log_file_dir = os.path.expanduser('~/Library/Logs/')
        elif plat == "win32":
            log_file_dir = os.path.expanduser('~/APPDATA/LOCAL/')
        elif plat == "linux":
            log_file_dir = os.path.expanduser('~/.config/')
        else:
            raise OSError(f"Unsupported platform: {sys.platform}")
        log_file_path = os.path.join(log_file_dir, log_file_name)
    else:
        log_file_path = os.path.join(".", log_file_name)
    try:
        logging.basicConfig(filename=log_file_path, level=log_level, filemode='w', format=lfmt)
    except OSError as e:
        logging.basicConfig(level=logging.INFO, format=lfmt)
        logging.error(e)
    sys.excepthook = exception_handler_hook
    logging.info("LOG START")
    log_sys_info()


    #     try:
    #         # When compiled as .app file on Mac, sandboxing will have the logical working directory '/'
    #         # meaning creating logfiles in the same directory will fail. We'll need to redirect the 
    #         # log output to the standard logfile location for user apps.
    #         if sys.platform == 'darwin':
    #             log_dir = os.path.expanduser('~/Library/Logs/')
    #             log_path = log_dir + log_file_name
    #             logging.basicConfig(filename=log_path, level=log_level, filemode='w', format=lfmt)
    #         else:
    #             logging.basicConfig(filename=log_file_name, level=log_level, filemode='w', format=lfmt)
    #     except OSError as e:
    #         logging.basicConfig(level=logging.INFO, format=lfmt)
    #         logging.error(e)
    # else:
    #     logging.basicConfig(filename=log_file_name, level=log_level, filemode='w', format=lfmt)
    # logging.info("LOG START")
    # log_sys_info()
    # sys.excepthook = exception_handler_hook