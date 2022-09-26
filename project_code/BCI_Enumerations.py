# -*- coding: utf-8 -*-
"""
This module is a header for the program's enumerated data types.

@author: Darren Vawter
"""

from enum import IntEnum; # Allow for integer enumeration types

###########################
#   Enumerate BCI Modes   #
###########################
class BCI_Mode(IntEnum):

    # Default overlay which mirrors the full screen onto the P300 interface
    OVERLAY_INTERFACE = 0;
    # Keyboard interface which displays a P300 keyboard to the user
    KEYBOARD_INTERFACE = 1;
    
    """
    Example specialty overlays for increased data throughput:
        SPECIAL_OVERLAY = N;
        DESKTOP_OVERLAY = 10;
        TASK_MANAGER_OVERLAY = 11;
        FILE_EXPLORER_OVERLAY = 12;
        CHESS_OVERLAY = 13;
        YOUTUBE_OVERLAY = 14;
    """    
    
#########################################
#   Enumerate BCI Interaction Options   #
#########################################
class BCI_Interaction(IntEnum):
    
    ##########################
    #   Mouse Interactions   #
    ##########################
    # Left-click the mouse at the center/selection of the current overlay
    CLICK = 0;
    # Doubl left-click the mouse at the center/selection of the current overlay
    DOUBLE_CLICK = 1;
    # Right-click the mouse at the center/selection of the current overlay
    RIGHT_CLICK = 2;
    
    #############################
    #   Keyboard Interactions   #
    #############################
    # Press the page up button
    PAGE_UP = 3;
    # Press the page down button
    PAGE_DOWN = 4;
    # Press the tab button
    TAB = 5;
    # Press enter
    ENTER = 6;
    
#############################################
#   Enumerate Overlay Interaction Options   #
#############################################
class Overlay_Interaction(IntEnum):
        
    #############################
    #   Overlay Interactions   #
    #############################
    # Revert to the previous level of magnification
    REVERT_MAGNIFICATION = 0;
    
#############################################
#   Enumerate Speller Interaction Options   #
#############################################
class Speller_Interaction(IntEnum):
    
    # Close keyboard
    CLOSE_KEYBOARD = 0;
       
#############################################
#   Enumerate Program Interaction Options   #
#############################################
class Program_Interaction(IntEnum):

    ############################
    #   Program Interactions   #
    ############################
    # Exit the program
    EXIT = 0;   
        
#####################################
#   Enumerate stimuli trial codes   #
#####################################
class Stimuli_Code(IntEnum):
    
    # Trial is not the start of a new classification and is a not a sync trial
    NON_SYNC = -1;
    # Trial is not the start of a new classification but is a sync trial
    SYNC = -2;
    # Trial is the start of a new classification but is a not a sync trial
    NON_SYNC_START = -3;
    # Trial is the start of a new classification and is a sync trial
    SYNC_START = -4;
    # Trial is a training trial
    # code --> target_id







































