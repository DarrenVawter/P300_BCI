# -*- coding: utf-8 -*-
"""
This module displays a virtual keyboard running a P300 speller to the user.

@author: Darren Vawter
"""

# External Modules
import time;
import numpy as np; # fast arrays&manipulation
import pygame; # display to the screen and play sounds
import pyautogui; # virtualize keyboard & mouse control
from math import floor, ceil;
import random;
import logging; # print pretty console logs

# Internal Modules
from BCI_Enumerations import Program_Interaction, PC_Interaction, Stimuli_Code, Processor_Code; # definitions for enumerated data types
from Logging_Formatter import Logging_Formatter; # custom format for pretty console logs
from BCI_Constants import BLACK, GRAY, WHITE, RED, SCREEN_WIDTH, SCREEN_HEIGHT, FRAMERATE_CAP, FLASH_DURATION, N_STREAM_ELEMENTS, KEY_LOCATIONS, KEY_CHARACTERS, N_TILES_PER_FLASH, N_BCI_CONTROLS, N_OVERLAY_CONTROLS; # pull constants from header

#############################################################
#   Dislpay the virtual keyboard and run the P300 Speller   #
#############################################################
def Run(UM232R, canvas, stimuli_outlet, processor_inlet):
                    
    #TODO: wrap this
    # Create a console logger for pretty formatting
    console = logging.getLogger("BCI_Overlay.py");
    console.setLevel(logging.DEBUG);
    if(console.hasHandlers()):
        console.handlers.clear();
    ch = logging.StreamHandler();
    ch.setFormatter(Logging_Formatter());
    console.addHandler(ch);
    
    ###############################
    #   Define Helper Functions   #
    ###############################
    
    """
    
    Choose_Flash_Tiles()
    
        This function chooses which tiles to flash with the current stimulus.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
    
        --> Check if the # of tiles remaining in the set are <= the # per flash
        
            --> If so, flash all of the tiles remaining in the set and reset the set
        
        --> Grab the tile with the highest probability remaining in the set
        
            --> If there are multiple with this max, pick one at random
        
        --> Put it in the group and remove it from the set
        
        --> Populate the rest of the group by repeating the last 2 steps
            (grabbing the lowest probability each time instead of the highest)
            
        --> The group now consists of one highly probable tile and several
            low probability tiles
            
        --> This will minimize the overlap of high probability tiles being in
            the same group, allowing for better discrimination between tiles    
            
    """
    def Choose_Flash_Tiles():
        
        #TODO: dynamically handle if N_TILES is not a multiple of N_TILES_PER_FLASH
        
        nonlocal flash_bucket, current_flash_group;
        
        for i in range(N_TILES_PER_FLASH):
            current_flash_colors[i] = (random.randint(0,255),random.randint(0,255),random.randint(0,255));
        
        # Check if the number of tiles available to flash is <= the tiles per flash
        if(len(flash_bucket) <= N_TILES_PER_FLASH):
            
            # Just flash the remaining available tiles 
            current_flash_group = flash_bucket;
            
            # Reset the bucket        
            flash_bucket = np.arange(N_TILES);
                        
            # Exit the call early
            return;
            
        # Find the highest probability amongst the tiles in the flash bucket
        max_probability = np.amax(tile_probabilities[flash_bucket]);
        
        # Grab the indices of all tiles with this max probability
        # Note: indices are relative to flash_bucket as we are slicing tile_probabilities by flash_bucket
        max_indices = np.where(tile_probabilities[flash_bucket]==max_probability);
        
        # Grab one of the available max-probability tiles at random
        try:
            max_choice = np.random.choice(max_indices[0]);
        except Exception as e:
            console.warning(tile_probabilities);
            console.warning(flash_bucket);
            console.warning(max_probability);
            console.warning(max_indices);
            raise e;

        
        # Init the flash group with this element and remove it from the flash bucket
        current_flash_group = np.array(flash_bucket[max_choice]);
        flash_bucket = np.delete(flash_bucket,max_choice);
                
        # Iterate until the flash group is populated
        while(np.size(current_flash_group) < N_TILES_PER_FLASH):
            
            # Find the lowest probability amongst the tiles in the flash bucket
            min_probability = np.amin(tile_probabilities[flash_bucket]);
            
            # Grab the indices of all tiles with this min probability
            # Note: indices are relative to flash_bucket as we are slicing tile_probabilities by flash_bucket
            min_indices = np.where(tile_probabilities[flash_bucket]==min_probability);
            
            # Grab one of the available min-probability tiles at random
            min_choice = np.random.choice(min_indices[0]);
            
            # Add this element to the flash group and remove it from the flash bucket
            current_flash_group = np.append(current_flash_group, flash_bucket[min_choice]);
            flash_bucket = np.delete(flash_bucket,min_choice);
        
        # End of Choose_Flash_Tiles()
        pass;    
               
    #TODO: Handle_Key_Classification() docstring
    def Handle_Key_Classification(classification_id):
        
        # Check if classified key is a normal char
        if(classification_id < 36):
            pyautogui.press(KEY_CHARACTERS[classification_id]);
        else:
            #TODO: handle others
            pass;
        
        # End of Handle_Key_Classification()
        pass;
    
    #TODO: change this to shutdown overlay
        
    """
    
    Shutdown_Overlay()
    
        This function prepares the overlay module to safely return.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
    
        --> Delete/destroy/close/disable relevant variables and objects
        
        --> Return
        
    """
    def Shutdown_Overlay():

        nonlocal overlay_running;

        console.debug("Shutting down interface...");
        
        # Announce that the overlay interface is shutting down
        console.info("Announcing shutdown.");
        shutdown_signal = np.empty(N_STREAM_ELEMENTS).astype(int);
        shutdown_signal[-1] = Stimuli_Code.INTERFACE_SHUTDOWN;
        stimuli_outlet.push_sample(shutdown_signal);

        #TODO: error catch more finely
        #TODO: maaayyybbbbeeee consider logging these
        overlay_running = False;        
        
        console.debug("Interface shutdown complete.");
        
        # End of Shutdown_Overlay()
        pass;
        
    ##############################
    #   Functional entry point   #
    ##############################
    
    #################################
    #   Define keyboard constants   #
    #################################            
        
    # Number of flash images to pull from
    N_FLASH_IMAGES = 10;
    
    # Time, in seconds, per training target
    TARGET_TIME = 12;
                        
    # Tile dimensions are identical to the dimensions of the interaction bars
    TILE_WIDTH = 100;
    TILE_HEIGHT = TILE_WIDTH;
    
    # Number of tiles in the keyboard interface
    N_TILES = 37;
            
    # Load and scale flash images
    FLASH_IMAGES = [None] * N_FLASH_IMAGES
    for i in range(N_FLASH_IMAGES):
        FLASH_IMAGES[i] = pygame.image.load('league_icons/'+str(i)+'.jpg')
        FLASH_IMAGES[i] = pygame.transform.scale(FLASH_IMAGES[i], (TILE_WIDTH, TILE_HEIGHT));
        
    ###################################
    #   Initialize keyboard objects   #
    ###################################
    
    # Initialize game clock to cap fps
    clock = pygame.time.Clock();
    
    # Initialize key font objects    
    font = pygame.font.SysFont('Calibri', 90, True, False)
    KEY_FONTS = [None] * len(KEY_CHARACTERS);
    KEY_SIZES = [None] * len(KEY_CHARACTERS);
    for key_index in range(len(KEY_CHARACTERS)): 
        KEY_FONTS[key_index] = font.render(KEY_CHARACTERS[key_index], True, WHITE);
        KEY_SIZES[key_index] = font.size(KEY_CHARACTERS[key_index]);
    
    #####################################
    #   Initialize keyboard variables   #
    #####################################
    
    # Initialize flash timer to track how long a group has been flashed for
    flash_timer = 0;
       
    # Most recent probability of each tile
    tile_probabilities = np.ones((N_TILES,1))/N_TILES;
        
    # Tiles that are currently being flashed
    current_flash_group = np.zeros((N_TILES_PER_FLASH,1));
    current_flash_colors = np.zeros((N_TILES_PER_FLASH,3));
    
    #TODO: change dynamically with a timer
    
    # Tiles that have not yet been flashed as part of the current set    
    flash_bucket = np.arange(N_TILES);
    
    # Initialize training target key ID
    target_tile = np.random.choice(flash_bucket);  
        
    # Randomized indices to reference the flash images
    flash_image_indices = np.arange(N_FLASH_IMAGES);
        
    # Track whether or not the current trial is the start of a new classification
    start_new_classification = False;
    
    ########################################
    #   Synchronize start with processor   #
    ########################################
    
    # Define start request signal to send until processor acknowledges receipt by signaling back to start
    start_request = np.empty(N_STREAM_ELEMENTS).astype(int);
    start_request[-1] = Stimuli_Code.REQUEST_KEYBOARD_START;
    
    # Initialize the mode to classification mode
    training_mode = False;
                
    # Wait for processor to acknowledge the connection by requesting start
    #TODO: consider adding a maximum timeout to this
    console.info("Waiting to receive start signal from processor...");
    while(True):
        
        # Broadcast the start request
        stimuli_outlet.push_sample(start_request);    
            
        # Check for new input from the processor
        # (Waiting for input 100ms at most, then trying again to allow for interrupts) 
        processor_input, _ = processor_inlet.pull_sample(0.1);
        if(processor_input is not None):

            # Verify that the input is a start signal
            if(processor_input[-1] == Processor_Code.START_KEYBOARD_TRAINING):
                            
                console.warning("Starting keyboard interface in training mode.");
                
                # Start the keyboard in training mode
                training_mode = True;
                # Initialize the target timer to track how long the current target has been selected
                target_timer = 0;
                
                # Exit blocking loop
                break;
                
            elif(processor_input[-1] == Processor_Code.START_KEYBOARD_CLASSIFICATION):
                                
                console.debug("Starting keyboard interface in classification mode.");
                
                # Set flag to show that next trial is the start of a new classification
                start_new_classification = False;
                
                # Remove the target key
                target_tile = -1;
                # Initialize the target timer to track how long the current target has been selected
                target_timer = time.time();
                
                # Exit blocking loop
                break;
                
            # Else, the received signal was not a start
            else:
                
                #TODO: implement raising/handling an error since we should only expect a start signal here
                #TODO: ^----? maybe ?
                console.debug("Received processor code",Processor_Code(processor_input[-1]),"when start code was expected.");
            
        # Else, attempt to again alert the processor that the BCI is ready & waiting
        else:
                        
            # Wait for 100ms to reserve resources
            #TODO: consider adding this to pull_sample as a 100ms block instead
            time.sleep(0.1);    
        
        
        
    #TODO: remove this    
    # Track framerate/item performance
    last_time = time.time();
    n_frames = 0;
    frame_time = 0;
    a_sum = 0;
    b_sum = 0;
    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    
    
    #########################
    #   Main Overlay Loop   #
    #########################
    overlay_running = True;
    while(overlay_running): 
        
        #############################
        #   Handle external input   #
        #############################
                        
        #TODO: wrap this
        #TODO: wrap this so hard
        
        # Check LSL for input
        processor_input, _ = processor_inlet.pull_sample(0.0);
        if(processor_input is not None):
                        
            # Convert the input to a np array
            processor_input = np.array(processor_input);
            
            # Grab the processor code from the end of the array
            processor_code = Processor_Code(processor_input[-1]);
            
            # Check if input is end of training
            if(processor_code == Processor_Code.START_KEYBOARD_CLASSIFICATION):

                # Check if currently in training mode
                if(training_mode):
                    
                    console.warning("Switching to keyboard classification mode.");
                
                    # Reset tile probabilities
                    tile_probabilities = np.ones((N_TILES,1))/N_TILES;
                    
                    # Reset the bucket        
                    flash_bucket = np.arange(N_TILES);
                
                    # Remove the target tile
                    target_tile = -1;
                
                    # Flag to start new tile classification
                    start_new_classification = True;
                    
                    # Exit training mode
                    training_mode = False;
                
                # Else, in classification mode
                else:
                    #TODO: Handle this
                    raise RuntimeError("Start classification signal received while in classification mode.");
                
            # Check if input is a probability update
            elif(processor_code == Processor_Code.PROBABILITY_UPDATE):
                        
                # Update tile probabilities
                tile_probabilities = processor_input[:N_TILES]; 
                            
            # Check if processor_code is a tile classification
            elif(processor_code == Processor_Code.CLASSIFICATION):
                                                
                # Find the id of the classified tile
                classification_id = np.where(processor_input[:-1] == 1)[0][0];
                console.info(classification_id);
                    
                # Handle key classification
                Handle_Key_Classification(classification_id);
                
                # Flag to start a new classification
                start_new_classification = True;
                
            # Check if input is a restart request
            elif(processor_code == Processor_Code.RESTART):
                                
                # Reset tile probabilities
                tile_probabilities = np.ones((N_TILES,1))/N_TILES;
                
                # Reset the bucket        
                flash_bucket = np.arange(N_TILES);
            
                # Flag to start a new classification
                start_new_classification = True;
                
            # Check if the processor is shutting down
            elif(processor_code == Processor_Code.PROCESSOR_SHUTDOWN):
           
                console.warning("Received shutdown signal from processor.");
                # Shutdown the overlay and flag the controller to close the BCI
                Shutdown_Overlay();
                #TODO: differentiate this interaction
                return (Program_Interaction.EXIT,None);
            
            # Else, input is updated probabilities
            else:
                
                #TODO: custom exception
                raise RuntimeError("Unexpected exception");
                        
        ##########################
        #   Handle flash group   #
        ##########################
        
        # Check if the current flash group's timer has expired
        if(time.time() > flash_timer + FLASH_DURATION):
        
            # Pick the next flash group
            Choose_Flash_Tiles();
            
            # Check if in training mode
            if(training_mode):
            
                # Form output array
                    # -1 --> cell was not used at all
                    # 0  --> cell was not flashed, cell is not the target of the trial
                    # 1  --> cell was flashed, cell is not the target of the trial
                    # 2  --> cell was not flashed, cell is the target of the trial
                    # 3  --> cell was flashed, cell is the target of the trial  
                    
                # Initialize output array to all zeros
                stimuli_data = np.zeros(N_STREAM_ELEMENTS).astype(int);
                
                # Set unused cells to -1
                stimuli_data[N_TILES:] = -1;
                
                # Set flashed cells to 1
                stimuli_data[current_flash_group] = 1;
                
                # Check if the target key was flashed
                if(target_tile in current_flash_group):
                    
                    # Set the target key to 3
                    stimuli_data[target_tile] = 3;
                    
                    # Send the UM232R a sync pulse
                    UM232R.Send_Sync();
                    
                # Else, the target key was not flashed
                else:
                    
                    # Set the target key to 2
                    stimuli_data[target_tile] = 2;   
                    
                    # Send the UM232R a sync pulse
                    UM232R.Send_Non_Sync();                 
            
                # Append the training stimuli code to the trial
                stimuli_data[-1] = Stimuli_Code.TRAINING;
                        
            # Else, in classification mode
            else:
                    
                # Form output array
                    # -1 --> unused cell
                    # 0 --> used cell, not flashed this trial
                    # 1 --> used cell, flashed this trial
                    
                # Initialize output array to all zeros
                stimuli_data = np.zeros(N_STREAM_ELEMENTS).astype(int);
                
                # Set unused cells to -1
                stimuli_data[N_TILES:] = -1;
                
                # Set flashed cells to 1
                stimuli_data[current_flash_group] = 1;
            
                #TODO: add DRBG back in to determine if the trial was a sync trial
                # For now, call any trial that flashes tile 0 a sync trial
                BCI_sync_code = stimuli_data[0];
                
                # Append the trial's sync code to the array and send relevant data to processor & UM232R
                            
                # Check if the trial is the first trial of a new classification
                if(start_new_classification):
                    
                    # Check if trial is a sync trial
                    if(BCI_sync_code):
                        
                        # Trial is the start of a new classification but is a not a sync trial
                        stimuli_data[-1] = Stimuli_Code.SYNC_START;
                        
                        # Send the UM232R a sync pulse
                        UM232R.Send_Sync();
                        
                    # Else, trial is not a sync trial
                    else:
                        
                        # Trial is the start of a new classification but is a not a sync trial
                        stimuli_data[-1] = Stimuli_Code.NON_SYNC_START;
                        
                        # Send the UM232R a non-sync pulse
                        UM232R.Send_Non_Sync();
                        
                    # Reset new classification flag
                    start_new_classification = False;
                    
                # Else, the trial is not the first trial of a new classification
                else:
                    
                    # Check if trial is a sync trial
                    if(BCI_sync_code):
                        
                        # Trial is not the start of a new classification but is a sync trial                
                        stimuli_data[-1] = Stimuli_Code.SYNC;
                        
                        # Send the UM232R a sync pulse
                        UM232R.Send_Sync();
                            
                    # Else, trial is not a sync trial
                    else:
                        
                        # Trial is not the start of a new classification and is a not a sync trial                
                        stimuli_data[-1] = Stimuli_Code.NON_SYNC;
                        
                        # Send the UM232R a non-sync pulse
                        UM232R.Send_Non_Sync();
                    
            # Send the flash data to the processor
            stimuli_outlet.push_sample(stimuli_data);
           
            # Randomize the order of the flash images
            np.random.shuffle(flash_image_indices);
            
            # Reset the flash timer for this group
            flash_timer = time.time();
            
        ##########################
        #   Clear frame buffer   #
        ##########################
    
        # Overwrite previous background with all black for the new frame
        canvas.fill(BLACK);
                
        ################################
        #   Render the keyboard keys   #
        ################################
        
        # For each key
        for key_index in range(len(KEY_CHARACTERS)):
            
            # Draw gray background
            pygame.draw.rect(canvas, GRAY, [KEY_LOCATIONS[key_index, 0], KEY_LOCATIONS[key_index, 1], TILE_WIDTH, TILE_HEIGHT]);
        
            # Draw key character
            canvas.blit(KEY_FONTS[key_index], [KEY_LOCATIONS[key_index, 0] + TILE_WIDTH/2 - KEY_SIZES[key_index][0]/2, KEY_LOCATIONS[key_index, 1] + TILE_HEIGHT/2 - KEY_SIZES[key_index][1]/2+5]);
        
            # Draw white border
            pygame.draw.rect(canvas, WHITE, [KEY_LOCATIONS[key_index, 0], KEY_LOCATIONS[key_index, 1], TILE_WIDTH, TILE_HEIGHT], 3)
            
        
        # Check the target timer
                
        if(time.time()-target_timer < TARGET_TIME):
        
            #################################
            #   Highlight the target tile   #
            #################################
                        
            if(target_tile >= 0):
                              
                # Draw target-key character
                target_font = font.render(KEY_CHARACTERS[target_tile], True, WHITE);
                target_w, _ = font.size(KEY_CHARACTERS[target_tile]);
                canvas.blit(target_font, [960-target_w/2,10]);
          
                #TODO: render "CALIBRATION MODE" at the top
                
            # Else, continually reset the target timer 
            else:
                target_timer = time.time();
                
            ######################################################
            #   Render flash images over the appropriate tiles   #
            ######################################################
            
            # Iterate over the tiles in the flash group
            for i in range(len(current_flash_group)):
                
                # Draw random color border
                pygame.draw.rect(canvas, current_flash_colors[i], [KEY_LOCATIONS[current_flash_group[i], 0]-16/2, KEY_LOCATIONS[current_flash_group[i], 1]-16/2, TILE_WIDTH+16, TILE_HEIGHT+16])
                    
                # Render the corresponding flash image
                canvas.blit(FLASH_IMAGES[flash_image_indices[i]],[KEY_LOCATIONS[current_flash_group[i], 0], KEY_LOCATIONS[current_flash_group[i], 1], TILE_WIDTH, TILE_HEIGHT]);
                        
            ###################################
            #   Finalize and draw the frame   #
            ###################################
            
            # Cap fps
            clock.tick(FRAMERATE_CAP);
                   
            # Display the buffered frame to the screen
            pygame.display.flip();
        
        # Else, reset the target
        else:
            
            ##############################
            #   Update the target tile   #
            ##############################
            
            # Tiles that have not yet been flashed as part of the current set    
            flash_bucket = np.arange(N_TILES);
            
            # Initialize training target key ID
            target_tile = np.random.choice(flash_bucket); 
                             
            # Draw target-key character
            target_font = font.render(KEY_CHARACTERS[target_tile], True, WHITE);
            target_w, _ = font.size(KEY_CHARACTERS[target_tile]);
            canvas.blit(target_font, [960-target_w/2,10]);
                            
            ###################################
            #   Finalize and draw the frame   #
            ###################################
            
            # Cap fps
            clock.tick(FRAMERATE_CAP);
                   
            # Display the buffered frame to the screen
            pygame.display.flip();
            
            # Pause for 1 second
            time.sleep(1);
            
            # Reset the target timer
            target_timer = time.time();
                
        ###############################
        #   Check for pygame events   #
        ###############################
        
        # Check to see if the program was closed through physical controls
        for event in pygame.event.get():
           if(event.type == pygame.QUIT):      
               console.warning("User closed the application.");
               Shutdown_Overlay();
               #TODO: differentiate this interaction
               return (Program_Interaction.EXIT,None);
               
        #TODO: remove this   
        # calc & print framerate/item performance
        this_time = time.time();    
        frame_time += (this_time-last_time);
        n_frames += 1;
        last_time = this_time;
        if(n_frames%20 == 0):
            console.info("fps: "+str(n_frames/frame_time));
#            print(a_sum/n_frames);
#            print(b_sum/n_frames);
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
    # End of Main overlay loop
    pass;
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    