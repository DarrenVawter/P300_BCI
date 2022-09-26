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
import time; # sleep
import numpy as np; # fast arrays&manipulation
#import threading; # run processor in a separate thread 
#from multiprocessing import Process;
import pygame; # display to the screen and play sounds
import pyautogui; # virtual monitor/mouse/keyboard
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop; # communicating with P300 Processor

# Internal Modules
from BCI_Enumerations import BCI_Mode, Program_Interaction; # definitions for enumerated data types
from BCI_Constants import N_OUTPUTS; # pull constants from header
import BCI_Overlay; # run screen overlay using P300 speller
import BCI_Keyboard; # run keyboard using P300 speller 
#import P300_Processor; # run the P300 data processor
from FTDI_Handler import FTDI_Handler; # interact with UM232R FTDI device

###################################
#   Define Controller Constants   #
###################################
    
# Grab the monitor dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size();
SCREEN_DIMENSIONS = [SCREEN_WIDTH, SCREEN_HEIGHT];

#######################################
#   Initialize Controller Variables   #
#######################################

# Initialize the current BCI mode to the default overlay
current_BCI_mode = BCI_Mode.OVERLAY_INTERFACE;

# Initialize the overlay rect
magnification_rect = [0, 0, SCREEN_WIDTH, SCREEN_HEIGHT];

#####################################
#   Initialize Controller Objects   #
#####################################

# Initialize FTDI handler
UM232R = FTDI_Handler();

# Initialize the pygame gui engine
pygame.init();

# Get the pygame surface object as the monitor
canvas = pygame.display.set_mode(SCREEN_DIMENSIONS);

# Set the pygame window's name
pygame.display.set_caption("P300 BCI");

# Initialize the pygame audio mixer
pygame.mixer.init();

# Initialize the stimuli outlet
print("[BCI_Controller.py]:","Opening P300_Stimuli outlet...");
info = StreamInfo("P300_Stimuli", "P300_Stimuli", N_OUTPUTS+1, 125, "int16","BCI_GUI");
stimuli_outlet = StreamOutlet(info);
print("[BCI_Controller.py]:","P300_Stimuli outlet open.");

###################################################
#   Launch P300 processor as a parallel process   #
###################################################

"""
# Run the P300 processor in a new stream
print("[BCI_Controller.py]:","Launching P300_Processor.py...");
processor_thread = Process(target=P300_Processor.Run, args=(processor_outlet,stimuli_inlet,EEG_inlet,));
processor_thread.daemon = True;    
processor_thread.start();
print("[BCI_Controller.py]:","P300_Processor.py launched.");
"""

# Wait for the processor to broadcast its stream and open an inlet to it
print("[BCI_Controller.py]:","Resolving P300_Processor stream...");
inlet_stream = resolve_byprop("source_id", "P300_Processor");
processor_inlet = StreamInlet(inlet_stream[-1]);
print("[BCI_Controller.py]:","P300_Processor stream resolved.");

##################################
#   Launch Cyton Data Packager   #
##################################

#print("[BCI_Controller.py]:","Launching Cyton_Data_Packager.py...");
#TODO: add this in when packaging the complete solution
#time.sleep(.1);
#print("[BCI_Controller.py]:","Cyton_Data_Packager.py launched.");

############################
#   Main Controller Loop   #
############################
print("[BCI_Controller.py]:","BCI initialized. Running...");
BCI_running = True;
while(BCI_running):
    
    #######################
    #   Handle BCI mode   #
    #######################
    
    # Check if the BCI is currently in overlay mode
    if(current_BCI_mode == BCI_Mode.OVERLAY_INTERFACE):   
        
        # Launch the BCI screen overlay
        (program_interaction, data) = BCI_Overlay.Run(UM232R, canvas, magnification_rect, stimuli_outlet, processor_inlet);    
        
    # Check if the BCI is currently in keyboard mode
    elif(current_BCI_mode == BCI_Mode.KEYBOARD_INTERFACE):   
        
        # Launch the BCI keyboard
        (program_interaction, data) = BCI_Keyboard.Run(UM232R, stimuli_outlet, processor_inlet);    
    
    ####################################
    #   Handle Program interactions    #
    ####################################
    
    # Check if the program was closed through the BCI controls
    if(program_interaction == Program_Interaction.EXIT):
       #TODO: wrap this
       
       processor_inlet.close_stream();
       
       stimuli_outlet.push_sample(-N_OUTPUTS*np.ones(N_OUTPUTS+1).astype(int));
       stimuli_outlet.__del__();
       
       pygame.quit();
       
       UM232R.Release();
       
       BCI_running = False;
       
       print("[BCI_Controller.py]:","Shutting down...");
       
       break;
    
    ###############################
    #   Check for pygame events   #
    ###############################
    
    # Check if the program was closed through physical controls
    for event in pygame.event.get():
       if(event.type == pygame.QUIT):
           #TODO: wrap this
                  
           processor_inlet.close_stream();
              
           stimuli_outlet.push_sample(-N_OUTPUTS*np.ones(N_OUTPUTS+1).astype(int));
           stimuli_outlet.__del__();
           
           pygame.quit();
           
           UM232R.Release();
           
           BCI_running = False;
           
           print("[BCI_Controller.py]:","Shutting down...");
       
           break;
           











