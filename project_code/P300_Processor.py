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
from math import ceil;

# Internal Modules
from BCI_Constants import N_OUTPUTS, SAMPLING_FREQUENCY, FLASH_FREQUENCY, N_EEG_CHANNELS;

#############################
#   Processor Entry point   #
#############################
def Run(processor_outlet):
        
    ###############################
    #   Define Helper Functions   #
    ###############################
    
    """
    
    Handle_Incoming_Stimulus()
    
        This function properly adds the most recent stimulus trial codes from
        the stimuli inlet to the stimuli_trial_data matrix.
    
        arguments:
            [stimulus_input]: Most recent input from the stimuli_inlet 
        returns:
            [none]
        exceptions:
            [none]
    
        --> Check if stimulus_input is the shutdown signal
                
            --> Flag for shutdown
            
        --> Append the stimulus input to the stimulus data
        
        --> Increment the next stimulus index
                
        --> Check if the stimulus index needs to roll over
                    
            --> Roll the stimulus index over to the start  

        --> Increment the count of trials received  
        
    """
    def Handle_Incoming_Stimulus(stimulus_input):
                 
        nonlocal processor_running, stimuli_trial_data, stimuli_trial_index, total_trials_received;
        
        # Check if stimulus_input is the shutdown signal
        if(np.sum(stimulus_input) == -N_OUTPUTS*(N_OUTPUTS+1)):
            
            # Flag for shutdown
            processor_running = False;
                    
        # Append the stimulus input to the stimulus data
        stimuli_trial_data[stimuli_trial_index] = stimulus_input;
        
        # Increment the next stimulus index
        stimuli_trial_index += 1;        
        
        # Check if the stimulus index needs to roll over
        if(stimuli_trial_index > STIMULI_TO_HOLD):
            
            # Roll the stimulus index over to the start  
            stimuli_trial_index = 1;

        # Increment the count of trials received    
        total_trials_received += 1;       
           
        # End of Handle_Incoming_Stimulus()
        pass;
        
        
    """
    
    Handle_Incoming_Stimulus()
    
        This function properly trims and adds the most recent chunk of EEG
        samples from the EEG inlet to the EEG_samples matrix.
    
        arguments:
            [EEG_chunk]: Most recent chunk from the EEG_inlet 
        returns:
            [none]
        exceptions:
            [MemoryError]: if the chunk causes the EEG_samples matrix to overflow
    
        --> Format the chunk appropriately
            
        --> Filter the chunk
            
        --> Grab the size of the chunk
            
        --> Grab the indices of the first trial start, if any exist
            
        --> Check if this chunk causes data overflow
            
            --> Check if a trial is already ongoing
                
            --> Append the chunk to the EEG data
                    
            --> Update the next EEG sample index
                    
        --> Check if this chunk contains a trial start
                
            --> Add the trial-data portion of the chunk to the EEG data
                    
            --> Update the next EEG sample index
                
        --> Else, this chunk does not contain any trial information
                
            --> Throw away the chunk by doing nothing with it
            
        --> Else, this chunk causes data overflow
            
            --> Raise error
        
        
    """
    def Handle_Incoming_EEG_Chunk(EEG_chunk):
        
        nonlocal EEG_samples, EEG_sample_index;
        
        # Filter the chunk
        #TODO: this
            
        # Grab the size of the chunk
        chunk_size = len(EEG_chunk);
            
        # Grab the indices of the first trial start, if any exist
        trial_start_index = np.argmax(EEG_chunk[:][-1]!=-1);
                
        # Check that this chunk does not cause data overflow
        if(EEG_sample_index+chunk_size <= MAX_SAMPLES_TO_HOLD):  
        
            # Check if a trial is already ongoing
            if(EEG_sample_index > 0):
                
                # Append the chunk to the EEG data
                EEG_samples[EEG_sample_index:EEG_sample_index+chunk_size][:] = EEG_chunk[:][:];
                
                # Update the next EEG sample index
                EEG_sample_index += chunk_size;
                    
            # Check if this chunk contains a trial start
            elif(EEG_chunk[trial_start_index][-1] != 0):
                    
                # Add the trial-data portion of the chunk to the EEG data
                EEG_samples[EEG_sample_index:EEG_sample_index+chunk_size-trial_start_index][:] = EEG_chunk[trial_start_index:][:];                        
                
                # Update the next EEG sample index
                EEG_sample_index += chunk_size - trial_start_index;
                    
            # Else, this chunk does not contain any trial information
            else:
                
                # Throw away the chunk by doing nothing with it
                print("discarding chunk...");
                pass;
            
        # Else, this chunk causes data overflow
        else:
            
            # Raise error
            raise MemoryError("Ran out of pre-allocated RAM to store EEG samples.");
        
        # End of Handle_Incoming_EEG_Chunk()
        pass;
                
    """
    
    Shutdown_Processor()
    
        This function prepares the processor module to safely return.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
    
        --> Delete/destroy/close/disable relevant variable and objects
        
        --> Return
        
    """
    def Shutdown_Processor():
                
        stimuli_inlet.close_stream();
        EEG_inlet.close_stream();
        processor_outlet.__del__();
        print("[P300_Processor.py]:","Shutting down...");
    
    #############################
    #   Initialize LSL inlets   #
    #############################

    # Grab an inlet to the BCI stream
    print("[P300_Processor.py]:","Resolving P300_Stimuli stream...");
    inlet_stream = resolve_stream("type", "P300_Stimuli");
    stimuli_inlet = StreamInlet(inlet_stream[0]);
    print("[P300_Processor.py]:","P300_Stimuli stream resolved.");
    
    # Grab an inlet to the EEG stream
    print("[P300_Processor.py]:","Resolving Packaged_EEG stream...");
    inlet_stream = resolve_stream("type", "Packaged_EEG");
    EEG_inlet = StreamInlet(inlet_stream[0]);
    print("[P300_Processor.py]:","Packaged_EEG stream resolved.");
    
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
    
    # Define the maximum amount of parsed data, in seconds, to hold in RAM
    HOLDING_TIME = 120;
    
    # Define the time, in seconds, per epoch
    TIME_PER_EPOCH = 1;
        
    # Calculate the number of samples per epoch
    SAMPLES_PER_EPOCH = ceil(SAMPLING_FREQUENCY * TIME_PER_EPOCH);
    
    # Calculate the maximum number of EEG samples to hold
    MAX_SAMPLES_TO_HOLD = ceil(SAMPLING_FREQUENCY * HOLDING_TIME);
    
    # Calculate the number of EEG epochs to hold
    EPOCHS_TO_HOLD = ceil(FLASH_FREQUENCY * HOLDING_TIME);
    
    # Calculate the number of stimuli trials to hold
    STIMULI_TO_HOLD = EPOCHS_TO_HOLD;
        
    ######################################
    #   Initialize processor variables   #
    ######################################
    
    # Track whether the processor is waiting for the first trial of the new classification
    waiting_start_new_classification = True;
    
    ################################
    #   Initialize EEG variables   #
    ################################
    
    # Initialize EEG sample matrix
    EEG_samples = np.zeros((MAX_SAMPLES_TO_HOLD,N_EEG_CHANNELS+1));
    
    # Initialize current EEG sample index to 0
    EEG_sample_index = 0;
    
    # Initialize EEG epoch data (EEG samples neatly formatted into epochs)
    # (This technically contains repeated data, but it's programmatically convenient)
    EEG_epoch_data = np.zeros((EPOCHS_TO_HOLD, SAMPLES_PER_EPOCH, N_EEG_CHANNELS));
    
    # Initialize current EEG epoch index to 0
    EEG_epoch_index = 0;
    
    # Count the total number of epochs received from the Cyton
    # (in order to compare with the total number of trials received from the BCI)
    total_epochs_received = 0;
    #TODO: trim this in accordance with total_trials_received to prevent them from becoming annoyingly large
    
    ####################################
    #   Initialize stimuli variables   #
    ####################################
    
    # Initialize the stimuli trial matrix
    stimuli_trial_data = np.zeros((STIMULI_TO_HOLD, N_OUTPUTS+1));
    
    # Initialize the stimuli trial index to 0
    stimuli_trial_index = 0;
    
    # Count the total number of trials received from the BCI
    # (in order to compare with the total number of epochs received from the Cyton)
    total_trials_received = 0;
    #TODO: trim this in accordance with total_epochs_received to prevent them from becoming annoyingly large
    
    
    ########################################
    #   Initialize statistical variables   #
    ########################################
        
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
    restart_signal = np.zeros(N_OUTPUTS).astype(int);
    restart_signal[-1] = N_OUTPUTS;
    processor_outlet.push_sample(restart_signal);
    
    ###########################
    #   Main Processor Loop   #
    ###########################
    processor_running = True;
    while(processor_running):
        
        #############################
        #   Handle stimuli stream   #
        #############################
        
        # Check if stimulus input was received
        stimulus_input, _ = stimuli_inlet.pull_sample(0.0);
        if(stimulus_input is not None):
        
            # Appropriately handle the stimulus input
            Handle_Incoming_Stimulus(stimulus_input);
            
        #########################
        #   Handle EEG stream   #
        #########################
    
        # Check if a new chunk of EEG data was received
        EEG_chunk, _ = EEG_inlet.pull_chunk(0.0);
        if(len(EEG_chunk)>0):
            
            # Appropriately handle the chunk
            Handle_Incoming_EEG_Chunk(np.array(EEG_chunk));
    
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
        
    Shutdown_Processor();    
      
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
    














