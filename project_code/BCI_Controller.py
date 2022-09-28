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
import pygame; # display to the screen and play sounds
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop; # communicating with P300 Processor
import logging; # print pretty console logs

# Internal Modules
from BCI_Enumerations import BCI_Mode, Program_Interaction, Stimuli_Code; # pull definitions for enumerated data types
from BCI_Constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_DIMENSIONS, N_GUI_OUTPUTS, FLASH_FREQUENCY; # pull constants from header
import BCI_Overlay; # run screen overlay using P300 speller
import BCI_Keyboard; # run keyboard using P300 speller 
from FTDI_Handler import FTDI_Handler; # interact with UM232R FTDI device
from Logging_Formatter import Logging_Formatter; # custom format for pretty console logs

def Start():    

###############################
#   Define Helper Functions   #
###############################

    # TODO: Shutdown_Controller() docstring
    def Shutdown_Controller():    
                    
        ###################################
        #   Destroy the processor inlet   #
        ###################################
        
        console.debug("Shutting down...");
        
        try:
            
            console.info("Destroying processor inlet...");
            
            if(processor_inlet is not None):
                
                # Safely close the inlet
                # (Also lets outlets know that this consumer has been removed)
                processor_inlet.close_stream();
                
                # Completely delete the processor inlet
                processor_inlet.__del__();
                
            else:
                
                console.warning("'processor_inlet' is not defined.");
                
        except NameError:
            
            console.warning("'processor_inlet' is not declared.");
            
        except Exception as e:
            raise e;
                  
        ##################################
        #   Destroy the stimuli outlet   #
        ##################################  
        
        try:
            
            console.info("Destroying stimuli outlet...");
            
            if(stimuli_outlet is not None):
                
                # Send shutdown signal to any consumers of this outlet
                BCI_shutdown_signal = np.zeros(N_OUTPUTS+1).astype(int);
                BCI_shutdown_signal[-1] = Stimuli_Code.BCI_SHUTDOWN;
                stimuli_outlet.push_sample(BCI_shutdown_signal);
                
                # Wait for consumers to disconnect
                #TODO: consider setting a max timeout for this
                while(stimuli_outlet.have_consumers()):             
                    # Wait for 100ms, then try again (instead of blocking)
                    # (this brief pause between calls allows for interrupts)
                    time.sleep(0.1);
                
                # Completely delete the stimuli outlet
                stimuli_outlet.__del__();
                
            else:
                
                console.warning("'stimuli_outlet' is not defined.");
                
        except NameError:
            
            console.warning("'stimuli_outlet' is not declared.");
            
        except Exception as e:
            
            raise e;
            
        ########################################
        #   Destroy the pygame engine object   #
        ########################################
        
        try:
            
            console.info("Destroying the pygame engine object...");
            
            if(stimuli_outlet is not None):
                
                # Safely stop the pygame engine
                pygame.quit();
                
            else:
                
                console.warning("'pygame' is not defined.");
                
        except NameError:
            
            console.warning("'pygame' is not declared.");
            
        except Exception as e:
            
            raise e;
                       
        ######################################
        #   Destroy the UM232R FTDI object   #
        ######################################
        
        try:
            
            console.info("Destroying UM232R FTDI object...");
            
            if(stimuli_outlet is not None):
                
                # Release the device from its port to make it discoverable again
                UM232R.Release(); 
                
            else:
                
                console.warning("'UM232R' is not defined.");
                
        except NameError:
            
            console.warning("'UM232R' is not declared.");
            
        except Exception as e:
            
            raise e;
            
        console.critical("Shutdown complete.");
        
        # End of Shutdown_Controller
        pass;
        
    #TODO: Run() docstring
    def Run():
            
        nonlocal processor_inlet, stimuli_outlet, UM232R;
        
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
        #TODO: to minimize the amount of data that is being streamed, package the
        #      flash array into as few bytes as possible insteading each bit as an int16
        console.info("Opening P300_Stimuli outlet...");
        info = StreamInfo("P300_Stimuli", "P300_Stimuli", N_GUI_OUTPUTS, FLASH_FREQUENCY, "int16","BCI_GUI");
        stimuli_outlet = StreamOutlet(info);
        console.info("P300_Stimuli outlet opened.");
        
        ##################################
        #   Initialize processor inlet   #
        ##################################
        
        console.info("Resolving P300_Processor stream...");
        
        # Wait for the processor to broadcast its stream, then open an inlet to it
        inlet_stream = [];
        while(len(inlet_stream) < 1):
            # Wait for 500ms, then try again (instead of blocking)
            # (this recycle between calls allows for interrupts)
            inlet_stream = resolve_byprop("source_id", "P300_Processor", timeout = 0.5);
            
        # If multiple outlets were found, shut down and raise error
        # (shutdown dependancies are not functioning or multiple processors are running)
        if(len(inlet_stream) > 1):
            Shutdown_Controller();
            raise RuntimeError("Multiple streams broadcasting P300_Processor")
            
        # Specify the inlet (resolve_byprop returns a list object of inlets)
        processor_inlet = StreamInlet(inlet_stream[0]);
        
        console.info("P300_Processor stream resolved.");
        
        ############################
        #   Main controller loop   #
        ############################
        console.debug("BCI initialized. Running...");
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
            #   Handle program interactions    #
            ####################################
            
            # Check if the program was closed through the BCI controls
            if(program_interaction == Program_Interaction.EXIT):
                BCI_running = False;
                continue;
            
            ###############################
            #   Check for pygame events   #
            ###############################
            
            # Check if the program was closed through physical controls
            for event in pygame.event.get():
               if(event.type == pygame.QUIT):
                   BCI_running = False;
                   continue;
                 
            # End of main controller loop
            pass;
        
    ################################################
    #   BCI_Controller.py functional entry point   #
    ################################################
    
    processor_inlet = None;
    stimuli_outlet = None;
    UM232R = None;
    
    #TODO: wrap this
    # Create a console logger for pretty formatting
    console = logging.getLogger("BCI_Controller.py");
    console.setLevel(logging.DEBUG);
    if(console.hasHandlers()):
        console.handlers.clear();
    ch = logging.StreamHandler();
    ch.setFormatter(Logging_Formatter());
    console.addHandler(ch);
        
    try:
            
        # Start running the BCI
        Run();
    
    except KeyboardInterrupt:
        
        console.warning("Keyboard interrupt detected.");
        
        # An exception was raised, properly shutdown the BCI
        Shutdown_Controller();
    
    except (Exception, SystemExit, GeneratorExit) as e:
    
        console.error("Unhandled error raised.");
        
        # An exception was raised, properly shutdown the BCI
        Shutdown_Controller();
    
        # Re-raise the exception
        raise e;
    
    else:
    
        # Main controller loop has exited, properly shutdown the BCI
        Shutdown_Controller();
        






#TODO: call this from a file that independently starts all 3 processes          
Start();
    










