__author__ = 'Alexander Weigl'

# for uifile in *.ui; do pyuic4 -x -o ui_$(basename ${uifile%.ui}).py $uifile &; done

from .ui_editor import *
from .ui_frame import *
from .ui_helpdock import *
from .ui_overviewdock import *
from .ui_problemdock import *