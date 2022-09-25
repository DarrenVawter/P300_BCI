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
    OVERLAY_INTERFACE = 1;
    # Keyboard interface which displays a P300 keyboard to the user
    KEYBOARD_INTERFACE = 2;
    
    """
    Example specialty overlays forincreased data throughput:
        SPECIAL_OVERLAY = N;
        DESKTOP_OVERLAY = 10;
        FILE_EXPLORER_OVERLAY = 11;
        CHESS_OVERLAY = 12;
        YOUTUBE_OVERLAY = 13;
    """
    
#########################################
#   Enumerate BCI Interaction Options   #
#########################################
class BCI_Interaction(IntEnum):
    
    ############################
    #   Program Interactions   #
    ############################
    # Exit the program
    EXIT = 0;
    
    ##########################
    #   Mouse Interactions   #
    ##########################
    # Left-click the mouse at the center/selection of the current overlay
    CLICK = 1;
    # Doubl left-click the mouse at the center/selection of the current overlay
    DOUBLE_CLICK = 2;
    # Right-click the mouse at the center/selection of the current overlay
    RIGHT_CLICK = 3;
    
    #############################
    #   Keyboard Interactions   #
    #############################
    # Press the page up button
    PAGE_UP = 10;
    # Press the page down button
    PAGE_DOWN = 11;
    # Press the tab button
    TAB = 12;
    # Close keyboard
    CLOSE_KEYBOARD = 13;
    
    #############################
    #   Overlay Interactions   #
    #############################
    # Revert to the previous level of magnification
    REVERT_MAGNIFICATION = 20;
    # Magnify overlay according to selected tile
    MAGNIFY_TILE = 21;
    
    """
    Example specialty interactions for increased throughput:
        
        ############################
        #   Browser Interactions   #
        ############################
        # Browser back button
        BROWSER_BACK = 30;
        # Browser address bar
        ADDRESS_BAR = 31;
        # Browser refresh button
        BROWSER_REFRESH = 32;  
                
    """