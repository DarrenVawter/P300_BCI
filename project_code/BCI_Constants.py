# -*- coding: utf-8 -*-
"""
This module is a header for the program's constant vars.

@author: Darren Vawter
"""

import numpy as np;

##############
#   Colors   #
##############
BLACK = (0, 0, 0);
GRAY = (128, 128, 128);
WHITE = (255, 255, 255);
RED = (255, 0, 0);
BLUE = (0, 255, 0);
GREEN = (0, 0, 255);

#########################
#   Overlay constants   #
#########################

# Number of tiles flashed with each stimulus
N_TILES_PER_FLASH = 7;

# Number of rows/cols to divide the overlay into
N_TILE_ROWS = 7;
N_TILE_COLUMNS = 7;

# Total number of tiles on the overlay interface
N_TILES = N_TILE_ROWS*N_TILE_COLUMNS;

# Number of BCI interactions in the overlay interface
N_BCI_CONTROLS = 7;
N_OVERLAY_CONTROLS = 2;

##########################
#   Keyboard constants   #
##########################

# Number of keys flashed with each stimulus
N_KEYS_PER_FLASH = 7;

# Define the keyboard layout
KEY_CHARACTERS = "1234567890QWERTYUIOPASDFGHJKLZXCVBNM_se";

# Number of keys on the keyboard interface
N_KEYS = len(KEY_CHARACTERS);
KEY_LOCATIONS = np.zeros((N_KEYS,2));

key_offset = 170;

# Row 0 --> ['1','2','3','4','5','6','7','8','9','0']
row_x_offset = 100;
row_y = 390;
for i in range(10):
    KEY_LOCATIONS[i,0] = row_x_offset + key_offset*i;
    KEY_LOCATIONS[i,1] = row_y;
    
# Row 1
row_x_offset = 100;
row_y = 560;
for i in range(10):
    KEY_LOCATIONS[i+10,0] = row_x_offset + key_offset*i;
    KEY_LOCATIONS[i+10,1] = row_y;
    
# Row 2
row_x_offset = 145;
row_y = 730;
for i in range(9):
    KEY_LOCATIONS[i+20,0] = row_x_offset + key_offset*i;
    KEY_LOCATIONS[i+20,1] = row_y;
    
# Row 3
row_x_offset = 220;
row_y = 910;
for i in range(10):
    KEY_LOCATIONS[i+29,0] = row_x_offset + key_offset*i;
    KEY_LOCATIONS[i+29,1] = row_y;

###################################
#   BCI-wide physical constants   #
###################################

# Monitor parameters
#TDOO: ensure this matches the desired monitor + if there is a better library
from pyautogui import size;
SCREEN_WIDTH, SCREEN_HEIGHT = size();
SCREEN_DIMENSIONS = [SCREEN_WIDTH, SCREEN_HEIGHT];

# EEG parameters
N_EEG_CHANNELS = 8;
SAMPLING_FREQUENCY = 250;

##################################
#   BCI-wide program constants   #
##################################

# Default cell classification threshold
DEFAULT_THRESHOLD = 0.95;
    
# Caclulate the number of outlets in the processor and stimuli streams
N_STREAM_ELEMENTS = max(N_TILES,N_KEYS) + 1;

# Amount of time, in seconds, to present each stimulus for
FLASH_DURATION = 0.1;

# Stimulus presentation frequency, in Hz
FLASH_FREQUENCY = 1/FLASH_DURATION;

# FPS to limit pygame engine to
FRAMERATE_CAP = 250;


