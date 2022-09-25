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

# Monitor dimensions
from pyautogui import size;
SCREEN_WIDTH, SCREEN_HEIGHT = size();
SCREEN_DIMENSIONS = [SCREEN_WIDTH, SCREEN_HEIGHT];

########################
#   Pygame Constants   #
########################

# FPS to limit pygame engine to
FRAMERATE_CAP = 250;

#########################
#   Overlay Constants   #
#########################

# Number of rows/cols to divide the overlay into
N_TILE_ROWS = 10;
N_TILE_COLUMNS = 10;

# Total number of tiles on the overlay interface
N_TILES = N_TILE_ROWS*N_TILE_COLUMNS;

# Number of tiles flashed with each stimulus
N_TILES_PER_FLASH = 10;

##########################
#   Keyboard Constants   #
##########################

# Number of keys on the keyboard interface
N_KEYS = 45;

# Number of keys flashed with each stimulus
N_KEYS = 7;












