# -*- coding: utf-8 -*-
"""
This module displays a screen overlay running a P300 speller to the user.

@author: Darren Vawter
"""

# External Modules
import numpy as np; # fast arrays&manipulation
import math; # floor
import pygame; # display to the screen and play sounds
import d3dshot; # grab screen pixels

# Internal Modules
from BCI_Enumerations import BCI_Interaction; # definitions for enumerated data types
#from BCI_Constants import *; # pull constants from header
from BCI_Constants import BLACK, GRAY, SCREEN_WIDTH, SCREEN_HEIGHT, FRAMERATE_CAP, N_TILE_ROWS, N_TILE_COLUMNS, N_TILES_PER_FLASH; # pull constants from header

###########################################################
#   Dislpay the screen overlay and run the P300 Speller   #
###########################################################
def Run(canvas, magnification_rect, stimuli_outlet, processor_inlet):
        
    #TODO: remove this    
    # Track framerate/item performance
    import time;
    last_time = time.time();
    n_frames = 0;
    frame_time = 0;
    a_sum = 0;
    b_sum = 0;
    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    
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
        
        #TODO: handle if N_TILES is not a multiple of N_TILES_PER_FLASH
        
        nonlocal flash_bucket, current_flash_group;
        
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
        max_choice = np.random.choice(max_indices[0]);
        
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
            TypeError: if tile_id is not an int
            ValueError: if tile_id is not within the range [0, N_TILES) or if the tile_id is not from a magnification tile
            
    
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
        row = math.floor(tile_id / N_TILE_COLUMNS);
            
        # Verify that the tile id represents a magnification tile
        if(col == N_TILE_COLUMNS-1 or row == N_TILE_ROWS-1):
            raise ValueError("[tile_id] must be the id of a magnification tile.")
        
        # Convert overlay tile dimensions to screen dimensions
        tile_screen_width_conversion = (magnification_rect[2]-magnification_rect[0])/(N_TILE_COLUMNS-1);
        tile_screen_height_conversion = (magnification_rect[3]-magnification_rect[1])/(N_TILE_ROWS-1);
        
        # Calculate tile's left/right relative to the screen using the overlay's magnification rect
        left = math.floor(magnification_rect[0] + col * tile_screen_width_conversion);
        right = math.ceil(left + tile_screen_width_conversion);
        
        # Calculate tile's top/bottom relative to the screen using the overlay's magnification rect
        top = math.floor(magnification_rect[1] + row * tile_screen_height_conversion);
        bottom = math.ceil(top + tile_screen_height_conversion);
                    
        # Return the rect
        return [left, top, right, bottom];
        
        # End of Get_Tile_Rect()
        pass;
        
    ##############################
    #   Functional entry point   #
    ##############################
    
    ####################################
    #   Initialize overlay constants   #
    ####################################
            
    
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
    
    
    # Amount of time, in seconds, to flash each group for
    FLASH_DURATION = 0.1;
    
    # Number of flash images to pull from
    N_FLASH_IMAGES = 10;
    
    # Load and scale flash images
    FLASH_IMAGES = [None] * N_FLASH_IMAGES
    for i in range(10):
        FLASH_IMAGES[i] = pygame.image.load('league_icons/'+str(i)+'.jpg')
        FLASH_IMAGES[i] = pygame.transform.scale(FLASH_IMAGES[i], (TILE_WIDTH, TILE_HEIGHT));
        
    ##################################
    #   Initialize overlay objects   #
    ##################################
    
    # Initialize screen grabber object
    screen_grabber = d3dshot.create(capture_output="numpy", frame_buffer_size=1);
    screen_grabber.display = screen_grabber.displays[1];
    
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
    
    # Tiles that have not yet been flashed as part of the current set    
    flash_bucket = np.arange(N_TILES);
    
    # Randomized indices to reference the flash images
    flash_image_indices = np.arange(N_FLASH_IMAGES);
        
    # Track whether or not the current trial is the start of a new trial
    start_new_classification = False;
        
    #TODO: remove
    print(Get_Tile_Rect(88));
    
    #########################
    #   Main Overlay Loop   #
    #########################
    overlay_running = True;
    while(overlay_running): 
        
        #############################
        #   Handle external input   #
        #############################
        
        #TODO: this
        
        # Check LSL for input
        processor_input, _ = processor_inlet.pull_sample(0.0);
        if(processor_input is not None):
        
            # Convert the input to a np array
            processor_input = np.array(processor_input);
            
            # Grab the flag from the end of the array
            processor_flag = processor_input[-1];
                
            # Check if input is a tile classification
            if(processor_flag < 0):
            
                # Typecheck and convert the flag to the classification id
                if(processor_flag.is_integer()):
                    classification_id = int(-(processor_flag+1));
                else:
                    raise TypeError("Received non-integer classification ID from processor.");
                    
                # Check if classified tile is a BCI control option
                if(classification_id%N_TILE_COLUMNS == N_TILE_COLUMNS-1):

                    # Return appropriate BCI control interaction
                    pass;
                
                # Check if classified tile is an overlay control option
                elif(math.floor(classification_id/N_TILE_COLUMNS) == N_TILE_ROWS-1):
                
                    # Return appropriate BCI control interaction
                    pass;
                    
                # Else, classified tile is a magnification tile
                else:
                    
                    # Return appropriate BCI control interaction
                    return (BCI_Interaction.MAGNIFY_TILE, Get_Tile_Rect(classification_id));
                    
                # Flag to start a new classification
                start_new_classification = True;
                
            # Else, input is updated probabilities
            else:
            
                # Update tile probabilities
                tile_probabilities = processor_input;
                
        
        ##########################
        #   Handle flash group   #
        ##########################
        
        # Check if the current flash group's timer has expired
        if(time.time() > flash_timer + FLASH_DURATION):
        
            # Pick the next flash group
            Choose_Flash_Tiles();
                        
            # Send the flash data to the processor
            #TODO: this
            
            # Reset new classification flag
            start_new_classification = False;
            
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
        
        #TODO: this
        
        ###################################
        #   Render the overlay controls   #
        ###################################
                
        #TODO: this
                
        ######################################################
        #   Render flash images over the appropriate tiles   #
        ######################################################
        
        # Iterate over the tiles in the flash group
        for i in range(N_TILES_PER_FLASH):
            
            # Get the tile's row
            row = math.floor(current_flash_group[i] / N_TILE_COLUMNS);
            
            # Get the tile's column
            col = current_flash_group[i] % N_TILE_COLUMNS;
            
            # Render the corresponding flash image
            canvas.blit(FLASH_IMAGES[flash_image_indices[i]],[col*TILE_WIDTH, row*TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT])        
        
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
        
        ###############################
        #   Check for pygame events   #
        ###############################
        
        # Check to see if the program was closed through physical controls
        for event in pygame.event.get():
           if(event.type == pygame.QUIT):               
               overlay_running = False;
               return (BCI_Interaction.EXIT,None);
               
        #TODO: remove this   
        # calc & print framerate/item performance
        this_time = time.time();    
        frame_time += (this_time-last_time);
        n_frames += 1;
        last_time = this_time;
        if(n_frames%20 == 0):
            print(n_frames/frame_time);
            print(a_sum/n_frames);
            print(b_sum/n_frames);
            print("~~~~~~~~~~~~~~~~");
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # End of Main overlay loop
        pass;
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    