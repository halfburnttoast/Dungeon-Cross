import logging
from typing import Callable

def debug_timer(func: Callable) -> Callable:
    """Debug timer decorator. Outputs to log file."""
    def timer(*args):
        from time import time
        init_time = time()
        ret = func(*args)
        total_time = time() - init_time
        logging.debug(f"TIMER: {func.__name__} : {total_time}")
        return ret
    return timer