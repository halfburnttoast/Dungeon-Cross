import os
import sys

def resource_path(relative_path):
    """
    Used for looking up assets inside of compiled binaries. If you want to
    add your own custom assets AND compile the program as a stand-alone 
    executable, you'll have to wrap your asset lookup call in this function.

    Note, that if you add a new directory of assets, you'll need to update the
    .spec file's added_files list to include that directory for compiling. 
    """

    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)