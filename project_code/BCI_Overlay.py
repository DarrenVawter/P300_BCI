# -*- coding: utf-8 -*-
"""
This module displays a screen overlay running a P300 speller to the user.

@author: Darren Vawter
"""

# External Modules
import time;
import numpy as np; # fast arrays&manipulation
import pygame; # display to the screen and play sounds
import d3dshot; # grab screen pixels
import pyautogui; # virtualize keyboard & mouse control
from math import floor, ceil;
import logging; # print pretty console logs

# Internal Modules
from BCI_Enumerations import Program_Interaction, PC_Interaction, Stimuli_Code, Processor_Code; # definitions for enumerated data types
from Logging_Formatter import Logging_Formatter; # custom format for pretty console logs
from BCI_Constants import BLACK, GRAY, WHITE, RED, SCREEN_WIDTH, SCREEN_HEIGHT, FRAMERATE_CAP, FLASH_DURATION, N_STREAM_ELEMENTS, N_TILE_ROWS, N_TILE_COLUMNS, N_TILES_PER_FLASH, N_BCI_CONTROLS, N_OVERLAY_CONTROLS; # pull constants from header

###########################################################
#   Dislpay the screen overlay and run the P300 Speller   #
###########################################################
def Run(UM232R, canvas, magnification_rect, stimuli_outlet, processor_inlet):
                    
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
        
        nonlocal flash_bucket, current_flash_group, exclude_bucket;
        
        # Check if the number of tiles available to flash is <= the tiles per flash
        if(len(flash_bucket) <= N_TILES_PER_FLASH):
            
            # Just flash the remaining available tiles 
            current_flash_group = flash_bucket;
            
            # Reset the bucket        
            flash_bucket = np.arange(N_TILES);
            
            # Remove the tiles to exclude
            flash_bucket = np.delete(flash_bucket, exclude_bucket);
            
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
        
    """
    
    Get_Tile_Rect()
    
        This function returns the bounding rect of a tile given its id. The
        bounding rect is defined as the portion of the screen being mirrored
        through that rect on the overlay.
    
        arguments:
            [tile_id]: int --> the id of the tile to return the rect of
        returns:
            [tile_rect]: [int, int, int, int] --> the left, top, right, & bottom of the tile's rect
        exceptions:
            [TypeError]: if tile_id is not an int
            [ValueError]: if tile_id is not within the range [0, N_TILES) or if the tile_id is not from a magnification tile
            
    
        --> Convert overlay tile dimensions to screen dimensions
        
        --> Calc the tile's column  
                
        --> Calculate tile's left relative to the screen by multiplying the column by the tile-to-screen conversion factor
        
        --> Calculate the tile's right by adding one tile-to-screen conversion factor to the left
        
        --> Calculate tile's top relative to the screen by multiplying the column by the tile-to-screen conversion factor
        
        --> Calculate the tile's bottom by adding one tile-to-screen conversion factor to the top
        
        --> Return the rect
            
    """
    def Get_Tile_Rect(tile_id):
        
        # Validate tile_id type
        if(type(tile_id) != int):
            raise TypeError("[tile_id] must be an integer.");
            
        # Validate tile_id value
        if(tile_id<0 or tile_id>=N_TILES):
            raise ValueError("[tile_id] must be in the range [0, N_TILES).")  
            
        # Calc the tile's column  
        col = tile_id % N_TILE_COLUMNS;
        
        # Calc the tile's row
        row = floor(tile_id / N_TILE_COLUMNS);
            
        # Verify that the tile id represents a magnification tile
        if(col == N_TILE_COLUMNS-1 or row == N_TILE_ROWS-1):
            raise ValueError("[tile_id] must be the id of a magnification tile.")
        
        # Convert overlay tile dimensions to screen dimensions
        tile_screen_width_conversion = (magnification_rect[2]-magnification_rect[0])/(N_TILE_COLUMNS-1);
        tile_screen_height_conversion = (magnification_rect[3]-magnification_rect[1])/(N_TILE_ROWS-1);
        
        # Calculate tile's left/right relative to the screen using the overlay's magnification rect
        left = floor(magnification_rect[0] + col * tile_screen_width_conversion);
        right = ceil(left + tile_screen_width_conversion);
        
        # Calculate tile's top/bottom relative to the screen using the overlay's magnification rect
        top = floor(magnification_rect[1] + row * tile_screen_height_conversion);
        bottom = ceil(top + tile_screen_height_conversion);
                    
        # Return the rect
        return [left, top, right, bottom];
        
        # End of Get_Tile_Rect()
        pass;
       
    """
    
    Handle_Click()
    
        This function handles a BCI-triggered mouse click.
        
        arguments:
            [click_type]: string --> The type of mouse click. (left/right/double)
        returns:
            [none]
        exceptions:
            [TypeError]: if click_type is not a string
            [ValueError]: if click_type is not "left", "right", or "double"
            
    """
    def Handle_Click(click_type):
        
        nonlocal magnification_rect;
        
        # Validate click_type type
        if(type(click_type) != str):
            raise TypeError("[click_type] must be a string.");
                    
        # Validate click_type value
        if(not(click_type=="left" or click_type=="right" or click_type=="double")):
            raise ValueError("[click_type] must be 'left', 'right', or 'double'.");  
            
        # Calculate the mouse coordinates
        mouse_x = round((magnification_rect[0]+magnification_rect[2])/2);
        mouse_y = round((magnification_rect[1]+magnification_rect[3])/2);

        # Click the appropriate location
        if(click_type=="double"):
            pyautogui.doubleClick(x=mouse_x, y=mouse_y);
        else:
            pyautogui.click(x=mouse_x, y=mouse_y, button=click_type);
            
        # Return the mouse to the center of the overlay
        pyautogui.moveTo(-SCREEN_WIDTH+OVERLAY_WIDTH//2,OVERLAY_HEIGHT/2);
        
        # Reset the magnification rect to the full screen
        magnification_rect = [0, 0, SCREEN_WIDTH, SCREEN_HEIGHT];

        # End of Handle_Click()
        pass; 
       
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

        nonlocal screen_grabber, overlay_running;

        console.debug("Shutting down interface...");
        
        # Announce that the overlay interface is shutting down
        console.info("Announcing shutdown.");
        shutdown_signal = np.empty(N_STREAM_ELEMENTS).astype(int);
        shutdown_signal[-1] = Stimuli_Code.INTERFACE_SHUTDOWN;
        stimuli_outlet.push_sample(shutdown_signal);

        #TODO: error catch more finely
        #TODO: maaayyybbbbeeee consider logging these
        del screen_grabber;
        overlay_running = False;        
        
        console.debug("Interface shutdown complete.");
        
        # End of Shutdown_Overlay()
        pass;
        
    ##############################
    #   Functional entry point   #
    ##############################
    
    ################################
    #   Define overlay constants   #
    ################################            
        
    # Number of flash images to pull from
    N_FLASH_IMAGES = 10;
    
    # Time, in seconds, per training target
    TARGET_TIME = 12;
    
    # Calculate the dimensions of the overlay portion of the screen
    OVERLAY_WIDTH = round(SCREEN_WIDTH*(1-1/N_TILE_COLUMNS));
    OVERLAY_HEIGHT = round(SCREEN_HEIGHT*(1-1/N_TILE_ROWS));
            
    # Calculate the dimensions of the BCI interaction option bars
    INTERACTIONS_WIDTH = SCREEN_WIDTH-OVERLAY_WIDTH;
    INTERACTIONS_HEIGHT = SCREEN_HEIGHT-OVERLAY_HEIGHT;
        
    # Tile dimensions are identical to the dimensions of the interaction bars
    TILE_WIDTH = INTERACTIONS_WIDTH;
    TILE_HEIGHT = INTERACTIONS_HEIGHT;
    
    # Number of tiles in the overlay interface
    N_TILES = N_TILE_ROWS*N_TILE_COLUMNS;
            
    # Load and scale flash images
    FLASH_IMAGES = [None] * N_FLASH_IMAGES
    for i in range(N_FLASH_IMAGES):
        FLASH_IMAGES[i] = pygame.image.load('league_icons/'+str(i)+'.jpg')
        FLASH_IMAGES[i] = pygame.transform.scale(FLASH_IMAGES[i], (TILE_WIDTH*3/4, TILE_HEIGHT*3/4));
        
    # Load and scale interaction icons
    BCI_INTERACTION_ICONS = [None] * N_BCI_CONTROLS
    BCI_ICON_HEIGHT = TILE_HEIGHT*np.array([0.75, 0.75, 0.75, 0.5, 0.5, 1, 0.7]);
    BCI_ICON_WIDTH = np.multiply(BCI_ICON_HEIGHT,[0.72, 0.72, 0.72, 0.85, 0.85, 1, 2]);
    for i in range(N_BCI_CONTROLS):
        BCI_INTERACTION_ICONS[i] = pygame.image.load('BCI_interaction_icons/'+str(i)+'.png')
        BCI_INTERACTION_ICONS[i] = pygame.transform.scale(BCI_INTERACTION_ICONS[i], (BCI_ICON_WIDTH[i], BCI_ICON_HEIGHT[i]));
        
    # Load and scale interaction icons
    OVERLAY_INTERACTION_ICONS = [None] * N_BCI_CONTROLS
    OVERLAY_ICON_HEIGHT = TILE_HEIGHT*np.array([0.75]);
    OVERLAY_ICON_WIDTH = np.multiply(OVERLAY_ICON_HEIGHT,[1]);
    for i in range(N_OVERLAY_CONTROLS):
        OVERLAY_INTERACTION_ICONS[i] = pygame.image.load('overlay_interaction_icons/'+str(i)+'.png')
        OVERLAY_INTERACTION_ICONS[i] = pygame.transform.scale(OVERLAY_INTERACTION_ICONS[i], (OVERLAY_ICON_WIDTH[i], OVERLAY_ICON_HEIGHT[i]));
        
    ##################################
    #   Initialize overlay objects   #
    ##################################
    
    # Initialize screen grabber object
    screen_grabber = d3dshot.create(capture_output="numpy", frame_buffer_size=1);    
    screen_grabber.display = screen_grabber.displays[0];
        
    # Move the mouse to the center of the mirror to show where a click would be
    pyautogui.moveTo(-SCREEN_WIDTH+OVERLAY_WIDTH//2,OVERLAY_HEIGHT/2);
    
    # Initialize game clock to cap fps
    clock = pygame.time.Clock();
    
    ####################################
    #   Initialize overlay variables   #
    ####################################
    
    # Initialize flash timer to track how long a group has been flashed for
    flash_timer = 0;
       
    # Most recent probability of each tile
    tile_probabilities = np.ones((N_TILES,1))/N_TILES;
        
    # Tiles that are currently being flashed
    current_flash_group = np.zeros((N_TILES_PER_FLASH,1));
    
    #TODO: change dynamically with a timer
    
    # Tiles that have not yet been flashed as part of the current set    
    flash_bucket = np.arange(N_TILES);
    
    # Initialize training target key ID
    target_tile = np.random.choice(flash_bucket);  
    
    # Set of tiles that are not used within the grid
    exclude_bucket = [];
    
    # Remove the exclude set from the flash bucket
    flash_bucket = np.delete(flash_bucket, exclude_bucket);
    
    # Randomized indices to reference the flash images
    flash_image_indices = np.arange(N_FLASH_IMAGES);
        
    # Track whether or not the current trial is the start of a new classification
    start_new_classification = False;
    
    ########################################
    #   Synchronize start with processor   #
    ########################################
    
    # Define start request signal to send until processor acknowledges receipt by signaling back to start
    start_request = np.empty(N_STREAM_ELEMENTS).astype(int);
    start_request[-1] = Stimuli_Code.REQUEST_START;
    
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
            if(processor_input[-1] == Processor_Code.START_TRAINING):
                            
                console.warning("Starting in training mode.");
                
                # Start the overlay in training mode
                training_mode = True;
                # Initialize the target timer to track how long the current target has been selected
                target_timer = 0;
                
                # Exit blocking loop
                break;
                
            elif(processor_input[-1] == Processor_Code.START_CLASSIFICATION):
                                
                console.warning("Starting in classification mode.");
                
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
                console.warning("Received processor code",Processor_Code(processor_input[-1]),"when start code was expected.");
            
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
    console.debug("Start signal received from processor.");  
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
            
            # Check if input is a probability update
            if(processor_code == Processor_Code.START_CLASSIFICATION):

                # Check if currently in training mode
                if(training_mode):
                    
                    console.warning("Switching to classification mode.");
                
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
                    #Handle this
                    raise RuntimeError("Start classification signal received while in classification mode.");
                
            # Check if input is a probability update
            elif(processor_code == Processor_Code.PROBABILITY_UPDATE):
                        
                # Update tile probabilities
                tile_probabilities = processor_input[:N_TILES]; 
                
                # Reset the bucket        
                flash_bucket = np.arange(N_TILES);
            
            # Check if processor_code is a tile classification
            elif(processor_code == Processor_Code.CLASSIFICATION):
                                                
                # Find the id of the classified tile
                classification_id = np.where(processor_input[:-1] == 1)[0][0];
                console.info(classification_id);
                
                # Check if classified tile is an overlay control option
                if(floor(classification_id/N_TILE_COLUMNS) == N_TILE_ROWS-1):
                
                    # Convert control to overlay interaction
                    program_interaction = Program_Interaction(classification_id%N_TILE_COLUMNS+10);
                    
                    # Check if the user zoomed out
                    if(program_interaction == Program_Interaction.REVERT_MAGNIFICATION):
                                            
                        # Revert magnification to full screen
                        #TODO: store the last zoom level and revert to that instead    
                        magnification_rect = [0, 0, SCREEN_WIDTH, SCREEN_HEIGHT];                       
                        
                # Check if classified tile is a BCI control option
                elif(classification_id%N_TILE_COLUMNS == N_TILE_COLUMNS-1):

                    # Convert control to BCI interaction
                    PC_interaction = PC_Interaction(floor(classification_id/N_TILE_COLUMNS));
                    
                    # Check if the user left clicked
                    if(PC_interaction == PC_Interaction.CLICK):
                        
                        # Handle the left click
                        Handle_Click("left");
                                                
                    # Check if the user double clicked
                    elif(PC_interaction == PC_Interaction.DOUBLE_CLICK):  
                        
                        # Handle the double click
                        Handle_Click("double");
                        
                    # Check if the user right clicked
                    elif(PC_interaction == PC_Interaction.RIGHT_CLICK):    
                        
                        # Handle the right click
                        Handle_Click("right");  
                        
                    # Check if the user pressed page up
                    elif(PC_interaction == PC_Interaction.PAGE_UP):  
                        
                        # Press the page up key
                        pyautogui.press("pageup");  
                        
                    # Check if the user pressed page down
                    elif(PC_interaction == PC_Interaction.PAGE_DOWN): 
                        
                        # Press the page down key
                        pyautogui.press("pagedown");  
                        
                    # Check if the user tabbed
                    elif(PC_interaction == PC_Interaction.TAB):  
                        
                        # Press the tab key
                        pyautogui.press("tab");  
                        
                    # Check if the user pressed enter
                    elif(PC_interaction == PC_Interaction.ENTER):   
                        
                        # Press the enter key 
                        pyautogui.press("enter");                                     
                    
                # Else, classified tile is a magnification tile
                else:

                    # Update the magnification rect
                    magnification_rect = Get_Tile_Rect(int(classification_id));
                    
                    #TODO: find a way less ghetto solution than this
                    # Force-refresh the main screen by quickly alt-tabbing
                    pyautogui.keyDown('alt');
                    pyautogui.keyDown('tab');
                    pyautogui.press('esc');
                    pyautogui.keyUp('tab');
                    pyautogui.keyUp('alt');
                    
                    # Move the mouse to the center of the mirror to show where a click would be
                    #TODO: add this back in later
                    #pyautogui.moveTo(-SCREEN_WIDTH+OVERLAY_WIDTH/2,OVERLAY_HEIGHT/2);
                    
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
                # Set excluded cells to -1
                stimuli_data[exclude_bucket] = -1;
                # Set flashed cells to 1
                stimuli_data[current_flash_group] = 1;
                # Check if the target key was flashed
                if(target_tile in current_flash_group):
                    stimuli_data[target_tile] = 3;
                    # Send the UM232R a sync pulse
                    UM232R.Send_Sync();
                else:
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
                # Set excluded cells to -1
                stimuli_data[exclude_bucket] = -1;
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
        #   Render the screen mirror   #
        ################################
        
        # Grab desired monitor area as np array
        screen_capture = np.transpose(screen_grabber.screenshot(region=magnification_rect),(1,0,2));

        # Convert np array to pygame surface
        screen_capture = pygame.surfarray.make_surface(screen_capture);
        
        # Scale the mirror surface to fit the overlay region
        screen_capture = pygame.transform.scale(screen_capture, (OVERLAY_WIDTH, OVERLAY_HEIGHT));
        
        # Render the mirror surface to the canvas
        canvas.blit(screen_capture, (0,0));
        
        ###############################
        #   Render the BCI controls   #
        ###############################
        
        # Iterate over the BCI control options
        for i in range(N_BCI_CONTROLS):

            #TODO: remove this when the icon for double click is fixed
            if(i==1):
                canvas.blit(BCI_INTERACTION_ICONS[i],[round((N_TILE_COLUMNS-0.5)*TILE_WIDTH-BCI_ICON_WIDTH[i]), round((i+0.5)*TILE_HEIGHT-BCI_ICON_HEIGHT[i]/2), BCI_ICON_WIDTH[i], BCI_ICON_HEIGHT[i]]);
                canvas.blit(BCI_INTERACTION_ICONS[i],[round((N_TILE_COLUMNS-0.5)*TILE_WIDTH), round((i+0.5)*TILE_HEIGHT-BCI_ICON_HEIGHT[i]/2), BCI_ICON_WIDTH[i], BCI_ICON_HEIGHT[i]]);
                continue;                
                
            # Renderthe appropriate BCI control icon
            canvas.blit(BCI_INTERACTION_ICONS[i],[round((N_TILE_COLUMNS-0.5)*TILE_WIDTH-BCI_ICON_WIDTH[i]/2), round((i+0.5)*TILE_HEIGHT-BCI_ICON_HEIGHT[i]/2), BCI_ICON_WIDTH[i], BCI_ICON_HEIGHT[i]]);
        
        ###################################
        #   Render the overlay controls   #
        ###################################
                
        # Iterate over the BCI control options
        for i in range(N_OVERLAY_CONTROLS):

            # Renderthe appropriate BCI control icon
            canvas.blit(OVERLAY_INTERACTION_ICONS[i],[round((i+0.5)*TILE_WIDTH-OVERLAY_ICON_WIDTH[i]/2), round((N_TILE_ROWS-0.5)*TILE_HEIGHT-OVERLAY_ICON_HEIGHT[i]/2), OVERLAY_ICON_WIDTH[i], OVERLAY_ICON_HEIGHT[i]]);       
        
        # Check the target timer
        
        if(time.time()-target_timer < TARGET_TIME):
        
            #################################
            #   Highlight the target tile   #
            #################################
                        
            if(target_tile >= 0):
                
                # Get the tile's row
                row = floor(target_tile / N_TILE_COLUMNS);
                
                # Get the tile's column
                col = target_tile % N_TILE_COLUMNS;
                
                # Render the flash images border
                pygame.draw.rect(canvas, RED, [col*TILE_WIDTH, row*TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT]);
                pygame.draw.rect(canvas, GRAY, [col*TILE_WIDTH+TILE_WIDTH/10, row*TILE_HEIGHT+TILE_HEIGHT/10, TILE_WIDTH*4/5, TILE_HEIGHT*4/5]);
                
            # Else, continually reset the target timer 
            else:
                target_timer = time.time();
                
            ######################################################
            #   Render flash images over the appropriate tiles   #
            ######################################################
            
            # Iterate over the tiles in the flash group
            for i in range(N_TILES_PER_FLASH):
                
                # Get the tile's row
                row = floor(current_flash_group[i] / N_TILE_COLUMNS);
                
                # Get the tile's column
                col = current_flash_group[i] % N_TILE_COLUMNS;
                
                # Render the flash images border
                pygame.draw.rect(canvas, WHITE, [col*TILE_WIDTH+TILE_WIDTH/10, row*TILE_HEIGHT+TILE_HEIGHT/10, TILE_WIDTH*4/5, TILE_HEIGHT*4/5]);
                
                # Render the corresponding flash image
                canvas.blit(FLASH_IMAGES[flash_image_indices[i]],[col*TILE_WIDTH+TILE_WIDTH/8, row*TILE_HEIGHT+TILE_HEIGHT/8, TILE_WIDTH*3/4, TILE_HEIGHT*3/4]);      
        
            ###################################
            #   Finalize and draw the frame   #
            ###################################
            
            # Render tile boundaries
            for i in range(N_TILE_COLUMNS):
                pygame.draw.line(canvas, GRAY, (round(SCREEN_WIDTH*i/N_TILE_COLUMNS),0), (round(SCREEN_WIDTH*i/N_TILE_COLUMNS),SCREEN_HEIGHT), width=3);
            for i in range(N_TILE_ROWS):
                pygame.draw.line(canvas, GRAY, (0,round(SCREEN_HEIGHT*i/N_TILE_ROWS)), (SCREEN_WIDTH,round(SCREEN_HEIGHT*i/N_TILE_ROWS)), width=3);
            
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
            
            if(target_tile >= 0):
                
                # Get the tile's row
                row = floor(target_tile / N_TILE_COLUMNS);
                
                # Get the tile's column
                col = target_tile % N_TILE_COLUMNS;
                
                # Render the flash images border
                pygame.draw.rect(canvas, RED, [col*TILE_WIDTH, row*TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT]);
                pygame.draw.rect(canvas, GRAY, [col*TILE_WIDTH+TILE_WIDTH/10, row*TILE_HEIGHT+TILE_HEIGHT/10, TILE_WIDTH*4/5, TILE_HEIGHT*4/5]);
                
            ###################################
            #   Finalize and draw the frame   #
            ###################################
            
            # Render tile boundaries
            for i in range(N_TILE_COLUMNS):
                pygame.draw.line(canvas, GRAY, (round(SCREEN_WIDTH*i/N_TILE_COLUMNS),0), (round(SCREEN_WIDTH*i/N_TILE_COLUMNS),SCREEN_HEIGHT), width=3);
            for i in range(N_TILE_ROWS):
                pygame.draw.line(canvas, GRAY, (0,round(SCREEN_HEIGHT*i/N_TILE_ROWS)), (SCREEN_WIDTH,round(SCREEN_HEIGHT*i/N_TILE_ROWS)), width=3);
            
            # Cap fps
            clock.tick(FRAMERATE_CAP);
                   
            # Display the buffered frame to the screen
            pygame.display.flip();
            
            # Pause for 0.5 seconds
            time.sleep(0.5);
            
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    