# -*- coding: utf-8 -*-
"""


@author: Darren Vawter
"""

#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
#TODO: port MATLAB processor into Python
    
# External Modules
import numpy as np;
from pylsl import StreamInlet, resolve_stream; # communicating with BCI

# Internal Modules
from BCI_Constants import N_OUTPUTS;

#############################
#   Processor Entry point   #
#############################
def Run(processor_outlet):
    
    #####################################
    #   Initialize LSL inlet from BCI   #
    #####################################

    # Grab an inlet to the BCI stream
    print("[P300_Processor.py]: Resolving P300_Stimuli inlet...")
    inlet_stream = resolve_stream('type', 'P300_Stimuli');
    stimulus_inlet = StreamInlet(inlet_stream[0]);
    
    ##########################
    #   Initialize Filters   #
    ##########################
    
    # Filter out US main line noise (and first resonant echo)
    # Create a 60Hz notch filter with -3dB attenuation @ +-1Hz
    # Create a 120Hz notch filter with -3dB attenuation @ +-1Hz
    
    # Filter out flash frequency to remove SSVEP component from signal
    # Create a flash-frequency filter with -3dB at +-0.2Hz
    
    # Create a butterworth BP filter with edges @ 1Hz and 40Hz
    
    ######################################
    #   Initialize processor constants   #
    ######################################
    
    # Define the degree of iterative correlation to perform
    CORRELATION_DEGREE = 3;
    
    ######################################
    #   Initialize processor variables   #
    ######################################
    
    # Track whether the processor is waiting for the first trial of the new classification
    waiting_start_new_classification = True;
    
    # Declare the correlation statistics
    non_target_means = np.empty((CORRELATION_DEGREE,1));
    non_target_stds = np.empty((CORRELATION_DEGREE,1));
    non_target_cov = np.empty((CORRELATION_DEGREE,1));
    target_means = np.empty((CORRELATION_DEGREE,1));
    target_stds = np.empty((CORRELATION_DEGREE,1));
    target_cov = np.empty((CORRELATION_DEGREE,1));
    
    # Initialize cell probabilities
    cell_probabilities = np.empty(N_OUTPUTS);
    
    # Initialize threshold values
    #TODO: this
    
    ##################################
    #   Synchronize start with BCI   #
    ##################################
    
    # Send restart request to BCI
    restart_signal = np.zeros(N_OUTPUTS);
    restart_signal[-1] = N_OUTPUTS;
    processor_outlet.push_sample(restart_signal);
    
    #########################
    #   Main Overlay Loop   #
    #########################
    processor_running = True;
    while(processor_running):
        
        ###################################
        #   Check for new stimulus data   #
        ###################################
        
        # Check if stimulus input was received
        
            # handle incoming stimulus codes
            #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
            # Append the stimulus input to the stimulus data 
        
            # Increment the next stimulus index
            
            # Check if the stimulus index needs to roll over
                
                # Roll the stimulus index over to the start                
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
            
        ##############################
        #   Check for new EEG data   #
        ##############################
    
        # Check if a new chunk of EEG data was received
        
            # Handle incoming eeg chunk
            #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
            # Format the chunk appropriately
            
            # Filter the chunk
            
            # Grab the size of the chunk
            
            # Grab the indices of the first trial start, if any exist
            
            # Check if this chunk causes data overflow
            
                # Check if a trial is already ongoing
                
                    # Append the chunk to the EEG data
                    
                    # Update the next EEG sample index
                    
                # Check if this chunk contains a trial start
                
                    # Add the trial-data portion of the chunk to the EEG data
                    
                    # Update the next EEG sample index
                
                # Else, this chunk does not contain any trial information
                
                    # Throw away the chunk by doing nothing with it
            
            # Else, this chunk causes data overflow
            
                # Raise error
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
    
        ####################
        #   Handle Epoch   #
        ####################
        
        # Check if there are enough EEG samples to construct a complete epoch
        # and that the corresponding stimulus data has already been collected
    
            # Synchronize the epoch (wrap this probably)
            #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
            # Grab Cyton's sync code
            
            # Grab BCI's sync code
            
            # Check for desynchronization
            
                # Raise error
                #TODO: handle this by adding synchronizer back in
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
                        
            # Construct the epoch (wrap this probably)
            #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
            # Find the EEG sample index of the start of the next trial, if any
            
            # Check if a next-trial index was found
            
                # Set the next-trial index
                
                # Trim EEG samples up to the next-trial index
                
                # Update the EEG sample index according to the number of trials trimmed
                
            # Else, no next-trial index was found
            
                # Discard EEG samples
                
                # Reset EEG sample index
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
    
            #############################
            #   Handle Training Epoch   #
            #############################
            
            #TODO: this
            
            ###################################
            #   Handle Classification Epoch   #
            ###################################
    
            # Check if this epoch is the first trial of a new classification
            
                # Handle classification start
                #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                        
                # Validate that a new char was expected
                
                # Update flag to show that classification data has started streaming
                #waiting_start_new_classification = False;
                
                # Reset cell probabilities

                # Check if using NLP
                
                    # Get updated threshold values 
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
                                   
            # Check if data being streamed is for the current classification
            #if(!waiting_start_new_classification):
                
                # Normalize the epoch
                
                # Calculate the correlation coefficients
                #//np.correlate(x,y,"full");
                
                # Calculate trial probabilities
                #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                    
                # Generate an independent probability that this trial was a non-target trial
                
                # Generate an independent probability that this trial was a target trial
                
                # Normalize the generated probabilities
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
                
                # Update cell probabilities
                #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            
                # Update the cell probabilities according to the probability of this trial
                
                # Weight previous probabilities
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
                
                #TODO: calculate the probability that the user was looking at the screen at all
                
                # Broadcast classification status
                #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
                # Find what is currently the most probable cell
                
                # Check if the most probable cell is above its threshold
                
                    # Broadcast the classification result
                    # (offset by 1 then multiply by -1 as per scheme)                
                    
                    # Flag that the processor is waiting for the BCI to start streaming current data
                
                # Else, a classification is not ready
                
                    # Broadcast the current probabilities
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
                
            #######################################
            #   Update variables for next epoch   #
            #######################################
       
            # Increment next epoch index
            
            # Check if the epoch index needs to roll over
                
                # Roll the epoch index over to the start    
                
    
        pass;    
    
      
    #TODO: remove this
    """
    # Simulate faux classifications
    import time;
        
    # Simulate a tile magnification
    time.sleep(10);
    fake_classification = np.zeros(N_OUTPUTS).astype(int);
    fake_classification[-1] = -2;
    processor_outlet.push_sample(fake_classification);
    
    # Simulate a right click
    time.sleep(10);
    fake_classification[-1] = -30;
    processor_outlet.push_sample(fake_classification);
    """




#TODO: remove this
"""
from pylsl import StreamInfo, StreamOutlet;
# Initialize the processor outlet
info = StreamInfo("P300_Processor", "P300_Processor", max(N_TILES,N_KEYS), 125, "int16","P300_Processor");
processor_outlet = StreamOutlet(info);

Run(processor_outlet)

processor_outlet.__del__();
"""
    














