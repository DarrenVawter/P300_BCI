# -*- coding: utf-8 -*-
"""
This module is a header for the program's constant vars.

@author: Darren Vawter
"""

##############
#   Colors   #
##############
BLACK = (0, 0, 0);
GRAY = (128, 128, 128);
WHITE = (255, 255, 255);
RED = (255, 0, 0);
BLUE = (0, 255, 0);
GREEN = (0, 0, 255);

########################
#   SYSTEM CONSTANTS   #
########################

# Monitor parameters
from pyautogui import size;
SCREEN_WIDTH, SCREEN_HEIGHT = size();
SCREEN_DIMENSIONS = [SCREEN_WIDTH, SCREEN_HEIGHT];

# EEG parameters
N_EEG_CHANNELS = 8;
SAMPLING_FREQUENCY = 250;
    
########################
#   Pygame Constants   #
########################

# FPS to limit pygame engine to
FRAMERATE_CAP = 250;

#########################
#   Overlay Constants   #
#########################

# Number of tiles flashed with each stimulus
N_TILES_PER_FLASH = 10;

# Number of rows/cols to divide the overlay into
N_TILE_ROWS = 10;
N_TILE_COLUMNS = 10;

# Total number of tiles on the overlay interface
N_TILES = N_TILE_ROWS*N_TILE_COLUMNS;

# Number of BCI interactions in the overlay interface
N_BCI_CONTROLS = 7;
N_OVERLAY_CONTROLS = 1;

##########################
#   Keyboard Constants   #
##########################

# Number of keys on the keyboard interface
N_KEYS = 45;

# Number of keys flashed with each stimulus
N_KEYS = 7;

##########################
#   BCI-wide Constants   #
##########################

# Default call classification threshold
DEFAULT_THRESHOLD = 0.95;
    
# Caclulate number of outputs
N_OUTPUTS = max(N_TILES,N_KEYS);

# Amount of time, in seconds, to flash each group for
FLASH_DURATION = 0.1;

# Group flash frequency in Hz
FLASH_FREQUENCY = 1/FLASH_DURATION;











