# -*- coding: utf-8 -*-
"""
This script is the primary controller for the BCI. It handles which mode the
BCI is currently in as well as mode transitions. It also contains the core
pygame objects necessary to display the screen or play sounds.

#TODO: create and add link to visualization of this controller

@author: Darren Vawter
"""

###############################
#   BCI Program Entry point   #
###############################

# External Modules
import pygame; # Display to the screen and play sounds
import pyautogui; # Virtual monitor/mouse/keyboard
# Internal Modules
from BCI_Enumerations import BCI_Mode, BCI_Interaction; # Definitions for enumerated data types
import BCI_Overlay; # Run screen overlay using P300 speller
import BCI_Keyboard; # Run keyboard using P300 speller 

#######################################
#   Initialize Controller Variables   #
#######################################

# Initialize the current BCI mode to the default overlay
current_BCI_mode = BCI_Mode.OVERLAY_INTERFACE;
    
# Grab the monitor dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size();
SCREEN_DIMENSIONS = [SCREEN_WIDTH, SCREEN_HEIGHT];

# Initialize the pygame gui engine
pygame.init();

# Get the pygame screen object as the surface of the monitor
screen = pygame.display.set_mode(SCREEN_DIMENSIONS);

# Set the pygame window's name
pygame.display.set_caption("P300 BCI");

# Initialize the pygame audio mixer
pygame.mixer.init();

############################
#   Main Controller Loop   #
############################

BCI_running = True;
while(BCI_running):
    
    # Check if the BCI is currently overlay mode
    if(current_BCI_mode == BCI_Mode.OVERLAY_INTERFACE):    
        interaction = BCI_Overlay.Run(screen,[0,0,SCREEN_WIDTH,SCREEN_HEIGHT]);    
        #interaction = BCI_Overlay.Run(screen,[100,100,500,500]);    
    
    # Check if the program was closed through the BCI controls
    if(interaction == BCI_Interaction.EXIT):
       pygame.quit();
       BCI_running = False;
       break;
    
    # Check if the program was closed through physical controls
    for event in pygame.event.get():
       if(event.type == pygame.QUIT):
           pygame.quit();
           BCI_running = False;
           break;
           











