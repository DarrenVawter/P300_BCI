# -*- coding: utf-8 -*-
"""
This module displays a screen overlay running a P300 speller to the user.

@author: Darren Vawter
"""

#TODO: calculate the appropriate overlay display area dynamically

# External Modules
import numpy as np;
import pygame; # Display to the screen and play sounds
import pyautogui; # Virtual monitor/mouse/keyboard
from mss import mss; # Grab raw bytes from virtual monitor
from PIL import Image; # Form images from virtual monitor raw bytes

import cv2;

# Internal Modules
from BCI_Enumerations import BCI_Mode, BCI_Interaction; # Definitions for enumerated data types
from BCI_Constants import SCREEN_WIDTH, SCREEN_HEIGHT, FRAMERATE_CAP, BLACK, GRAY;

###########################################################
#   Dislpay the screen overlay and run the P300 Speller   #
###########################################################
def Run(canvas, magnification_rect):
    
    #TODO: remove this    
    import time;
    last_time = time.time();
    n_frames = 0;
    frame_time = 0;
    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    ####################################
    #   Initialize overlay variables   #
    ####################################
    
    # Initialize screen grabber object
    screen_grabber = mss();
    
    # Offset magnification rect by the second monitor's offset
    magnification_rect['left'] += screen_grabber.monitors[2]['left'];
    magnification_rect['top'] += screen_grabber.monitors[2]['top'];
    
    # Initialize game clock to cap fps
    clock = pygame.time.Clock();
        
    # Calculate the dimensions of the overlay portion of the screen
    OVERLAY_WIDTH = round(SCREEN_WIDTH*0.9);
    OVERLAY_HEIGHT = round(SCREEN_HEIGHT*0.9);
    #TODO: calculate the appropriate overlay display area more dynamically
        
    # Calculate the dimensions of the BCI interface portion of the screen
    INTERFACE_WIDTH = SCREEN_WIDTH-OVERLAY_WIDTH;
    INTERFACE_HEIGHT = SCREEN_HEIGHT-OVERLAY_HEIGHT;
        
    #########################
    #   Main Overlay Loop   #
    #########################
    overlay_running = True;
    while(overlay_running): 
        
        ##########################
        #   Clear frame buffer   #
        ##########################
    
        # Overwrite previous background with all black for the new frame
        canvas.fill(BLACK);
        
        ################################
        #   Render the screen mirror   #
        ################################
        
        # Grab desired monitor area as raw bytes
        screen_capture = screen_grabber.grab(magnification_rect);
        
        # Count the number of bytes
        capture_size = screen_capture.size;
        
        # Convert byte format from bgra to bgr by removing every 4th byte
        temp = bytearray(screen_capture.bgra);
        del temp[3::4];
        
        # Load the bytes as a pygame image
        screen_capture = pygame.image.frombuffer(bytes(temp), capture_size, 'BGR');
 
        # Scale the mirror to fit the overlay region
        screen_capture = pygame.transform.scale(screen_capture, (OVERLAY_WIDTH, OVERLAY_HEIGHT));
        
        # Render the mirror to the canvas
        canvas.blit(screen_capture, (0,0));
        
        ###############################
        #   Render the BCI controls   #
        ###############################
        
        ###################################
        #   Render the overlay controls   #
        ###################################
                
        ###################################
        #   Flash the appropriate tiles   #
        ###################################
        
        ###################################
        #   Finalize and draw the frame   #
        ###################################
        
        # Render tile boundaries
        for i in range(1,10):
            pygame.draw.line(canvas, GRAY, (round(SCREEN_WIDTH*i/10),0), (round(SCREEN_WIDTH*i/10),1080), width=3);
            pygame.draw.line(canvas, GRAY, (0,round(SCREEN_HEIGHT*i/10)), (1920,round(SCREEN_HEIGHT*i/10)), width=3);
        
        # Cap fps
        clock.tick(FRAMERATE_CAP);
               
        # Display the buffered frame to the screen
        pygame.display.flip();
        
        # Check to see if the program was closed through physical controls
        for event in pygame.event.get():
           if(event.type == pygame.QUIT):               
               overlay_running = False;
               return BCI_Interaction.EXIT;
               
        #TODO: remove this   
        this_time = time.time();    
        frame_time += (this_time-last_time);
        n_frames += 1;
        last_time = this_time;
        print(n_frames/frame_time);
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    
    