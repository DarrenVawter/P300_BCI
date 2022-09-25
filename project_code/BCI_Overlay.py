# -*- coding: utf-8 -*-
"""
This module displays a screen overlay running a P300 speller to the user.

@author: Darren Vawter
"""

#TODO: calculate the appropriate overlay display area dynamically

# External Modules
import numpy as np; # fast arrays&manipulation
import math; # floor
import pygame; # display to the screen and play sounds
import d3dshot; # grab screen pixels

# Internal Modules
from BCI_Enumerations import BCI_Interaction; # Definitions for enumerated data types
from BCI_Constants import SCREEN_WIDTH, SCREEN_HEIGHT, FRAMERATE_CAP, BLACK, GRAY;

###########################################################
#   Dislpay the screen overlay and run the P300 Speller   #
###########################################################
def Run(canvas, magnification_rect):
        
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
        
    ##############################
    #   Functional entry point   #
    ##############################
    
    ####################################
    #   Initialize overlay constants   #
    ####################################
            
    # Number of rows/cols to divide the overlay into
    N_TILE_ROWS = 10;
    N_TILE_COLUMNS = 10;
    
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
    
    # Number of tiles in each flash
    N_TILES_PER_FLASH = 10;
    
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
        
    #########################
    #   Main Overlay Loop   #
    #########################
    overlay_running = True;
    while(overlay_running): 
        
        ################################
        #   Check for external input   #
        ################################
        
        #TODO: this
        
        # Check LSL for input
        
            # Check if input is updated probabilities
            
                # Update tile probabilities
        
            # Check if input is tile classification
            
                # Check if classified tile is a BCI control option
                
                    # Return appropriate BCI control interaction
                
                # Check if classified tile is an overlay control option
                
                    # Return appropriate BCI control interaction
                
                # Else, classified tile is a magnification tile
                
                    # Return appropriate BCI control interaction
        
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
        
        ####################################
        #   Handle change of flash group   #
        ####################################
        
        # Check if the current flash group's timer has expired
        if(time.time() > flash_timer + FLASH_DURATION):
        
            # Pick the next flash group
            Choose_Flash_Tiles();
                        
            # Send the flash data to the processor
            #TODO: this
            
            # Randomize the order of the flash images
            np.random.shuffle(flash_image_indices);
            
            # Reset the flash timer for this group
            flash_timer = time.time();
        
        ####################################
        #   Render the appropriate tiles   #
        ####################################
        
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
            pygame.draw.line(canvas, GRAY, (round(SCREEN_WIDTH*i/10),0), (round(SCREEN_WIDTH*i/10),1080), width=3);
        for i in range(N_TILE_ROWS):
            pygame.draw.line(canvas, GRAY, (0,round(SCREEN_HEIGHT*i/10)), (1920,round(SCREEN_HEIGHT*i/10)), width=3);
        
        # Cap fps
        clock.tick(FRAMERATE_CAP);
               
        # Display the buffered frame to the screen
        pygame.display.flip();
        
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
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    