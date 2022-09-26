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
import time;
import numpy as np;
from math import ceil;
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop; # communicating with BCI and Cyton


# Internal Modules
from BCI_Enumerations import Stimuli_Code;
from BCI_Constants import N_OUTPUTS, SAMPLING_FREQUENCY, FLASH_FREQUENCY, N_EEG_CHANNELS;

#############################
#   Processor Entry point   #
#############################
def Run(processor_outlet, stimuli_inlet, EEG_inlet):
        
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

            #TODO: Re-wrap this, lol            
            # Flag for shutdown
            processor_running = False;
            print("[P300_Processor.py]:","Shutting down...");  
            
                    
        # Append the stimulus input to the stimulus data
        stimuli_trial_data[stimuli_trial_index,:] = stimulus_input[:];
        
        # Increment the next stimulus index
        stimuli_trial_index += 1;        
        
        # Check if the stimulus index needs to roll over
        if(stimuli_trial_index >= STIMULI_TO_HOLD):
            
            # Roll the stimulus index over to the start  
            stimuli_trial_index = 0;

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
        
        nonlocal EEG_samples, EEG_sample_index, processor_running;
        
        # Filter the chunk
        #TODO: this
            
        # Grab the size of the chunk
        chunk_size = len(EEG_chunk);
            
        # Grab the indices of the first trial start, if any exist
        trial_start_index = np.argmax(EEG_chunk[:,-1]!=0);
                
        # Check that this chunk does not cause data overflow
        if(EEG_sample_index+chunk_size <= MAX_SAMPLES_TO_HOLD):  
        
            # Check if a trial is already ongoing
            if(EEG_sample_index > 0):
                
                # Append the chunk to the EEG data
                EEG_samples[EEG_sample_index:EEG_sample_index+chunk_size,:] = EEG_chunk[:,:];
                
                # Update the next EEG sample index
                EEG_sample_index += chunk_size;
                                    
            # Check if this chunk contains a trial start
            elif(EEG_chunk[trial_start_index,-1] != 0):
                    
                # Add the trial-data portion of the chunk to the EEG data
                EEG_samples[EEG_sample_index:EEG_sample_index+chunk_size-trial_start_index,:] = EEG_chunk[trial_start_index:,:];                        
                
                # Update the next EEG sample index
                EEG_sample_index += chunk_size - trial_start_index;
                
            # Else, this chunk does not contain any trial information
            else:
                
                # Throw away the chunk by doing nothing with it
                #print("discarding chunk...");
                pass;
            
        # Else, this chunk causes data overflow
        else:
            
            # Raise error
            raise MemoryError("Ran out of pre-allocated RAM to store EEG samples.");
        
        
        # End of Handle_Incoming_EEG_Chunk()
        pass;
                
    """
    
    Synchronize_Streams()
    
        This function checks if the streams are already synchronized. If they
        are not, it synchronizes them using DRBG resynchronization. #TODO
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [ValueError]: if the BCI sync flag is an invalid sync code
    
        --> Grab Cyton's sync code
            
        --> Grab BCI's sync code
            
        --> Check for desynchronization
            
            --> Resynchronize streams #this is a big fat TODO
                
    
    """
    def Synchronize_Streams():  
               
        nonlocal processor_running;
        
        # Grab Cyton's sync code
        # (negative trial stamp indicates a sync trial)
        
        Cyton_sync_code = (EEG_samples[0,-1] < 0);    
        
        # Grab BCI's sync flag
        BCI_sync_code = stimuli_trial_data[EEG_epoch_index,-1];
                
        # >=0 --> training mode, check the cell code at that index
        if(BCI_sync_code >= 0):
            BCI_sync_code = stimuli_trial_data[EEG_epoch_index,BCI_sync_code];
            
        # Check if the BCI sync flag is a non-sync code
        elif(BCI_sync_code == Stimuli_Code.NON_SYNC or BCI_sync_code == Stimuli_Code.NON_SYNC_START):
            BCI_sync_code = False;
            
        # Check if the BCI sync flag is a sync code
        elif(BCI_sync_code == Stimuli_Code.SYNC or BCI_sync_code == Stimuli_Code.SYNC_START):
            BCI_sync_code = True;
            
        # Else, an invalid sync flag was received from the BCI stream
        else:
            raise ValueError("Invalid sync flag received from BCI stream.");
            
        # Check for desynchronization
        if(Cyton_sync_code != BCI_sync_code):
                                     
            print(EEG_epoch_index);
            print(EEG_samples[:200,-1]);
            print(stimuli_trial_data[:30,-1]);
              
            # Raise error
            raise RuntimeError("Cyton/BCI desynchronization detected.");
            #TODO: handle this by adding synchronizer back in
            
        # End of Synchronize_Streams()
        pass;
            
    """
    
    Construct_Epoch()
    
        This function constructs an epoch using the first epoch's-worth of
        samples from EEG_samples and the stimulus codes at epoch_index.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
               
        --> Find the EEG sample index of the start of the next trial, if any
            
        --> Check if a next-trial index was found
            
            --> Set the next-trial index
                
            --> Trim EEG samples up to the next-trial index
                
            --> Update the EEG sample index according to the number of trials trimmed
                
        --> Else, no next-trial index was found
            
            --> Discard all EEG samples
                
            --> Reset EEG sample index to 0
                
    
    """
    def Construct_Epoch():   
        
        nonlocal EEG_epoch_data, EEG_epoch_index, EEG_samples, EEG_sample_index, total_epochs_received;
        
        # Create the epoch
        EEG_epoch_data[EEG_epoch_index,:,:] = EEG_samples[:SAMPLES_PER_EPOCH,:N_EEG_CHANNELS];
                         
        # Find the EEG sample index of the start of the next trial, if any
        trial_start_index = np.argmax(EEG_samples[1:,-1]!=0)+1;
            
        # Check if a next-trial index was found
        if(EEG_samples[trial_start_index,-1] != 0):
                            
            # Trim EEG samples up to the next-trial index and append zeros
            EEG_samples[:,:] = np.concatenate((EEG_samples[trial_start_index:,:],np.zeros((trial_start_index,N_EEG_CHANNELS+1))));
            
            # Decrement the EEG sample index by the number of samples trimmed
            EEG_sample_index -= trial_start_index;
                
        # Else, no next-trial index was found
        else:
            
            # Discard EEG samples
            EEG_samples = np.zeros((MAX_SAMPLES_TO_HOLD,N_EEG_CHANNELS+1));
                
            # Reset EEG sample index to 0
            EEG_sample_index = 0;
               
        # End of Construct_Epoch()
        pass;
                    
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
    #TODO: detect large gaps between this and total_trials_received (to allow one to catch up)
    
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
    #TODO: detect large gaps between this and total_epochs_received (to allow one to catch up)
    
    
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
    print("[P300_Processor.py]:","Processor running...");
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
        if(EEG_sample_index > SAMPLES_PER_EPOCH and total_trials_received > total_epochs_received):
    
            Synchronize_Streams();
            
            Construct_Epoch();
    
            #############################
            #   Handle Training Epoch   #
            #############################
            
            #TODO: this
            
            ###################################
            #   Handle Classification Epoch   #
            ###################################
    
            # Check if this epoch is the first trial of a new classification
            if(stimuli_trial_data[EEG_epoch_index,-1] == Stimuli_Code.NON_SYNC_START or stimuli_trial_data[EEG_epoch_index,-1] == Stimuli_Code.SYNC_START):
            
                # Handle classification start
                #Start_New_Classification();
                #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                        
                # Validate that a new char was expected
                
                # Update flag to show that classification data has started streaming
                #waiting_start_new_classification = False;
                
                # Reset cell probabilities

                # Check if using NLP
                
                    # Get updated threshold values 
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
                pass;               
                
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
       
            # Increment the number of epochs received
            total_epochs_received += 1;
             
            # Increment the next EEG epoch index
            EEG_epoch_index += 1;
            
            # Check if the next EEG epoch index needs to roll over
            if(EEG_epoch_index >= EPOCHS_TO_HOLD):
                
                # Roll the EEG epoch index back over to the start
                EEG_epoch_index = 0;
                
    
        pass;    

# Grab an inlet to the EEG stream
print("[P300_Processor.py]:","Resolving Packaged_EEG stream...");
inlet_stream = resolve_byprop("source_id", "Cyton_Data_Packager");
EEG_inlet = StreamInlet(inlet_stream[-1]);
print("[P300_Processor.py]:","Packaged_EEG stream resolved.");
#TODO: make this less ghetto
# Let the Cyton Data Packager know a consumer is connecting
EEG_inlet.pull_chunk(0.0);
time.sleep(5);
# Discard the setup chunk
EEG_inlet.pull_chunk(0.0);

# Initialize the processor outlet
print("[P300_Processor.py]:","Opening P300_Processor outlet...");
info = StreamInfo("P300_Processor", "P300_Processor", N_OUTPUTS, 125, "int16","P300_Processor");
processor_outlet = StreamOutlet(info);
print("[P300_Processor.py]:","P300_Processor outlet open.");

# Grab an inlet to the BCI stream
print("[P300_Processor.py]:","Resolving P300_Stimuli stream...");
inlet_stream = resolve_byprop("source_id", "BCI_GUI");
stimuli_inlet = StreamInlet(inlet_stream[-1]);
print("[P300_Processor.py]:","P300_Stimuli stream resolved.");

try:
    
    # Launch the processor
    Run(processor_outlet, stimuli_inlet, EEG_inlet);
    
except KeyboardInterrupt:
    
    # Disconnect from inlets
    EEG_inlet.close_stream();
    stimuli_inlet.close_stream();
    
    # Close the outlet so that it is not discoverable
    processor_outlet.__del__();
    print("[P300_Processor]:","Processor outlet destroyed.");
    
    # Close the program
    print("Killing kernel...");
    time.sleep(1);
    
except Exception as e:
    
    # Disconnect from inlets
    EEG_inlet.close_stream();
    stimuli_inlet.close_stream();
    
    # Close the outlet so that it is not discoverable
    processor_outlet.__del__();
    print("[P300_Processor]:","Processor outlet destroyed.");
    
    # Close the program
    print("Killing kernel...");
    time.sleep(1);
    
    raise e;
        
#TODO: remove this
"""
from pylsl import StreamInfo, StreamOutlet;
# Initialize the processor outlet
info = StreamInfo("P300_Processor", "P300_Processor", max(N_TILES,N_KEYS), 125, "int16","P300_Processor");
processor_outlet = StreamOutlet(info);

Run(processor_outlet)

processor_outlet.__del__();
"""
    














