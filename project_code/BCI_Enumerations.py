# -*- coding: utf-8 -*-
"""
This module is a header for the program's enumerated data types.

@author: Darren Vawter
"""

from enum import IntEnum; # Allow for integer enumeration types

###########################
#   Enumerate BCI modes   #
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
    
########################################
#   Enumerate PC interaction options   #
########################################
class PC_Interaction(IntEnum):
    
    ##########################
    #   Mouse interactions   #
    ##########################
    # Left-click the mouse at the center/selection of the current overlay
    CLICK = 0;
    # Doubl left-click the mouse at the center/selection of the current overlay
    DOUBLE_CLICK = 1;
    # Right-click the mouse at the center/selection of the current overlay
    RIGHT_CLICK = 2;
    
    #############################
    #   Keyboard interactions   #
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
#   Enumerate Program Interaction Options   #
#############################################
class Program_Interaction(IntEnum):

    # Exit the program
    EXIT = 0;   
    # Open the overlay interface
    LAUNCH_OVERLAY = 1;   
    
    # Revert the overlay to the previous level of magnification
    REVERT_MAGNIFICATION = 10;
    # Open the keyboard interface
    LAUNCH_KEYBOARD = 11;   
    
    # Close keyboard interface
    CLOSE_KEYBOARD = 20;
        
#################################
#   Enumerate processor modes   #
#################################
class Processor_Mode(IntEnum):
    
    # Processor is expecting overlay training data
    TRAINING_OVERLAY = 1;
    # Processor is expecting keyboard training data
    TRAINING_KEYBOARD = 2;
    # Processor is expecting overlay data to classify
    CLASSIFICATION_OVERLAY = 3;
    # Processor is expecting keyboard data to classify
    CLASSIFICATION_KEYBOARD = 4;
    
########################################
#   Enumerate processor stream codes   #
########################################
class Processor_Code(IntEnum):
    
    # Stream data is a cell classification, cell values are one hot as follows:
        # 0 --> cell is not the classification
        # 1 --> cell is the classification
    CLASSIFICATION = 0; 
    # Stream data is an update to cell probabilities, cell values are the current probabilities
    PROBABILITY_UPDATE = 1;
    
    # Stream data is telling the interface to start training mode
    START_OVERLAY_TRAINING = -1;
    # Stream data is telling the interface to start classification mode
    START_OVERLAY_CLASSIFICATION = -2;
    # Stream data is telling the interface to start training mode
    START_KEYBOARD_TRAINING = -3;
    # Stream data is telling the interface to start classification mode
    START_KEYBOARD_CLASSIFICATION = -4;
    # Stream data is telling the interface to restart
    RESTART = -5;
    # Stream data is announcing that the processor is shutting down
    PROCESSOR_SHUTDOWN = -6;

######################################
#   Enumerate stimuli stream codes   #
######################################
class Stimuli_Code(IntEnum):
    
    # Stream data is a training trial, cell values are as follows:  
        # -1 --> cell was not used at all
        # 0  --> cell was not flashed, cell is not the target of the trial
        # 1  --> cell was flashed, cell is not the target of the trial
        # 2  --> cell was not flashed, cell is the target of the trial
        # 3  --> cell was flashed, cell is the target of the trial  
    TRAINING = 0;
    
    # For all of the following 4 codes, cell values are one hot as follows:
        # -1 --> cell was not used at all
        # 0  --> cell was not flashed
        # 1  --> cell was flashed
    # Stream data is not the start of a new classification and is a not a sync trial
    NON_SYNC = 1;
    # Stream data is not the start of a new classification but is a sync trial
    SYNC = 2;
    # Stream data is the start of a new classification but is a not a sync trial
    NON_SYNC_START = 3;
    # Stream data is the start of a new classification and is a sync trial
    SYNC_START = 4;

    # Stream data is requesting overlay-start from the processor
    REQUEST_OVERLAY_START = -1;
    # Stream data is requesting overlay-start from the processor
    REQUEST_KEYBOARD_START = -2;    
    # Stream data is announcing that the BCI is shutting down
    BCI_SHUTDOWN = -3;
    # Stream data is announcing that the interface is shutting down
    INTERFACE_SHUTDOWN = -4;






































