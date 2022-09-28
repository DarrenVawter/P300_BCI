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
from scipy import signal as Signal;
from scipy.io import loadmat as LoadMAT;
from scipy.stats import multivariate_normal as MVN;
from math import ceil;
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop; # communicating with BCI and Cyton
import logging; # print pretty console logs

# Internal Modules
from BCI_Enumerations import Stimuli_Code, Processor_Code;
from BCI_Constants import N_STREAM_ELEMENTS, DEFAULT_THRESHOLD, SAMPLING_FREQUENCY, FLASH_FREQUENCY, N_EEG_CHANNELS;
from Logging_Formatter import Logging_Formatter; # custom format for pretty console logs

#TODO: wrap this
# Create a console logger for pretty formatting
console = logging.getLogger("P300_Processor.py");
console.setLevel(logging.DEBUG);
if(console.hasHandlers()):
    console.handlers.clear();
ch = logging.StreamHandler();
ch.setFormatter(Logging_Formatter());
console.addHandler(ch);
    
#############################
#   Processor Entry point   #
#############################
def Run(processor_outlet, stimuli_inlet, EEG_inlet):
            
    
    #TODO: move this and make it dynamic (re-calc on classification)
    NON_TARGET_MULTIPLIER = 100/10 - 1;
    
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
                 
        nonlocal processor_running, stimuli_trial_data, stimuli_trial_index, total_trials_received, waiting_start_new_classification;
        
        # Grab the stimuli code
        stimuli_code = Stimuli_Code(stimulus_input[-1]);
        
        # Check if the stream data is a trial inquiry
        if(stimuli_code == Stimuli_Code.NON_SYNC
           or stimuli_code == Stimuli_Code.SYNC
           or stimuli_code == Stimuli_Code.NON_SYNC_START
           or stimuli_code == Stimuli_Code.SYNC_START):
            
            if(waiting_start_new_classification and (stimuli_code == Stimuli_Code.SYNC or stimuli_code == Stimuli_Code.SYNC)):
                # This data is outdated, waiting to receive new classification data
                pass;
                        
            # Append the stimulus input to the stimulus data
            stimuli_trial_data[stimuli_trial_index,:] = stimulus_input[:-1];
            
            # Increment the next stimulus index
            stimuli_trial_index += 1;        
            
            # Check if the stimulus index needs to roll over
            if(stimuli_trial_index >= STIMULI_TO_HOLD):
                
                # Roll the stimulus index over to the start  
                stimuli_trial_index = 0;
    
            # Increment the count of trials received    
            total_trials_received += 1;      
            
        # Check if the stream data is training data
        elif(stimuli_code == Stimuli_Code.TRAINING):
            #TODO: this
            pass;
            
        # Check if the stream data is a start request
        elif(stimuli_code == Stimuli_Code.START):
            #TODO: this probably shouldn't happen --> decide what to do
            pass;
            
        # Check if the stream data is a restart request
        elif(stimuli_code == Stimuli_Code.RESTART):
            #TODO: decide what to do when the interface is requesting a restart
            #(if this is even necessary)
            pass;
            
        # Check if the stream data is a program shutdown announcement
        elif(stimuli_code == Stimuli_Code.BCI_SHUTDOWN):
            #TODO: generate a different kind of interrupt here
            raise KeyboardInterrupt("BCI shutdown signal received.");
            
        # Check if the stream data is an interface shutdown announcement
        elif(stimuli_code == Stimuli_Code.INTERFACE_SHUTDOWN):
            #TODO: decide what to do when the interface shuts down
            # (this will happen whenever switching between the keyboard & overlay)
            pass;
            
        # Check if the stimuli code is something unexpected
        else:
            #TODO: be more specific with the error type
            raise RuntimeError("Unexpected stimulus code received.");
                                               
        # End of Handle_Incoming_Stimulus()
        pass;
        
    """
    
    Filter_Chunk()
    
        This function filters each EEG channel of the chunk, 1 at a time,
        using, in order, a 60Hz notch, a 120Hz notch, a 1Hz<->40Hz butterworth
        bandpass, and a FLASH_FREQUENCY Hz filter.
    
        arguments:
            [EEG_chunk]: Most recent chunk from the EEG_inlet 
        returns:
            [EEG_chunk]: The same chunk, but with its EEG channels filter
        exceptions:
            [none]
    
        --> For each EEG channel
                
            --> Apply the cascade filter to the chunk and track the filter states
            
        --> Return the EEG chunk
                    
    """
    def Filter_Chunk(EEG_chunk):
        
        nonlocal n60_b, n120_b, nf_b, bp_b, n60_a, n120_a, nf_a, bp_a, n60_z, n120_z, nf_z, bp_z;
        
        # Filter each channel of the chunk
        for channel in range(N_EEG_CHANNELS):
                        
            EEG_chunk[:, channel], n60_z[channel,:] = Signal.lfilter(n60_b, n60_a, EEG_chunk[:, channel], zi=n60_z[channel,:]);
            EEG_chunk[:, channel], n120_z[channel,:] = Signal.lfilter(n120_b, n120_a, EEG_chunk[:, channel], zi=n120_z[channel,:]);
            EEG_chunk[:, channel], nf_z[channel,:] = Signal.lfilter(nf_b, nf_a, EEG_chunk[:, channel], zi=nf_z[channel,:]);
            EEG_chunk[:, channel], bp_z[channel,:] = Signal.lfilter(bp_b, bp_a, EEG_chunk[:, channel], zi=bp_z[channel,:]);
            
        # End of Filter_Chunk
        return EEG_chunk;
                
    """
    
    Handle_Incoming_EEG_Chunk()
    
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
        
        nonlocal EEG_samples, EEG_sample_index, processor_running;#, live_EEG_index;
        
        # Filter the chunk
        EEG_chunk = Filter_Chunk(EEG_chunk);
                    
        # Grab the size of the chunk
        chunk_size = len(EEG_chunk);
            
        #TODO: remove
        #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Live view
        """
        if(live_EEG_index + chunk_size < N_LIVE_SAMPLES):
            live_EEG[live_EEG_index:live_EEG_index+chunk_size] = EEG_chunk[:,3];
            live_EEG_index = live_EEG_index+chunk_size;
        else:
            live_EEG[live_EEG_index:] = EEG_chunk[:N_LIVE_SAMPLES-live_EEG_index,3];
            live_EEG[:live_EEG_index+chunk_size-N_LIVE_SAMPLES] = EEG_chunk[N_LIVE_SAMPLES-live_EEG_index:,3];
            live_EEG_index = live_EEG_index+chunk_size-N_LIVE_SAMPLES-1;
            
        plt.ylim([np.min(live_EEG)-1,np.max(live_EEG)+1]);
        plt.xlim([0,5]);
        plt.plot(np.arange(0,5,1/SAMPLING_FREQUENCY), live_EEG);
        plt.show();
        """
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~}
        
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
        BCI_sync_code = (BCI_sync_code == Stimuli_Code.SYNC_START) or (BCI_sync_code == Stimuli_Code.NON_SYNC_START);
        
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
            print(stimuli_trial_data[EEG_epoch_index-4:EEG_epoch_index+5,-1]);
              
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

    """
    
    Start_New_Classification()
    
        This function handles the re-initialization of the relevant
        variables prior to beginning a new classification.
        
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [RuntimeError] --> if this function was called when a new
                               classification was not expected to begin
               
        --> Validate that a new char was expected
                    
        --> Update flag to show that classification data has started streaming
                    
        --> Reset cell probabilities
    
        --> Check if using NLP
                    
            --> Get updated threshold values 
            
        --> Else, not using NLP
        
            --> Use default threshold values
    
    """                  
    def Start_New_Classification():        
             
        nonlocal waiting_start_new_classification, cell_probabilities, cell_thresholds;
        
        # Validate that a new char was expected
        if(not waiting_start_new_classification):
            raise RuntimeError("Received new classification flag from the BCI stream when a new classification was not expected to begin.");
                    
        # Update flag to show that classification data has started streaming
        waiting_start_new_classification = False;
                    
        # Reset cell probabilities
        cell_probabilities = np.ones(N_STREAM_ELEMENTS-1);
        unused_cells = np.where(stimuli_trial_data[EEG_epoch_index,:] == -1);
        cell_probabilities[unused_cells] = 0;
        cell_probabilities[:] = cell_probabilities[:]/np.sum(cell_probabilities);
    
        #TODO: do this dynamically once the keyboard is added in
        using_NLP = False;
    
        # Check if using NLP
        if(using_NLP):            
        
            #TODO: do this dynamically once the keyboard is added in
            # Get updated threshold values 
            pass;
                
        # Else, not using NLP
        else:
    
            # Use default threshold values for used cells
            cell_thresholds = DEFAULT_THRESHOLD * np.ones(N_STREAM_ELEMENTS-1);
            
            # Use >100% threshold value for unused cells
            cell_thresholds[unused_cells] = 2;

        # End of Start_New_Classification();
        pass;
        
    #TODO: Calculate_Correlation_Coefficients() docstring
    def Calculate_Correlation_Coefficients(normalized_epoch):
        
        nonlocal mwms_classifer;
        
        correlation_coefficients = np.zeros(CORRELATION_DEGREE);
        
        last_tier_data = normalized_epoch;
        
        classifier_width = SAMPLES_PER_EPOCH;
        
        for degree in range(CORRELATION_DEGREE):
            
            tier_data = np.zeros((classifier_width*2-1,N_EEG_CHANNELS));
        
            correlation_coefficient = 0;
        
            for channel in range(N_EEG_CHANNELS):
                
                tier_data[:,channel] = np.correlate(mwms_classifer[degree,:classifier_width,channel],last_tier_data[:,channel],"full");
                
                correlation_coefficient += tier_data[classifier_width,channel];
        
            correlation_coefficients[degree] = correlation_coefficient / N_EEG_CHANNELS;
            
            classifier_width *= 2;
            classifier_width -= 1;
            
            last_tier_data = tier_data
            last_tier_data[:classifier_width,:] = last_tier_data[:classifier_width,:] / np.sum(last_tier_data[:classifier_width,:],0);
        
        return correlation_coefficients;
    
    #TODO: Calculate_Trial_Probability() docstring
    def Calculate_Trial_Probability(correlation_coefficients):         

        # Generate an independent probability that this trial was a non-target trial
        trial_non_target_probability = non_target_mvn.pdf(correlation_coefficients);
        trial_non_target_probability *= NON_TARGET_MULTIPLIER;
        
        # Generate an independent probability that this trial was a target trial
        trial_target_probability = target_mvn.pdf(correlation_coefficients);
        
        # Normalize the generated probabilities
        p_space = trial_target_probability + trial_non_target_probability;
        #trial_non_target_probability /= p_space; # = 1-target
        trial_target_probability /= p_space;
        
        return trial_target_probability;
    
    #TODO: Update_Probabilities docstring()
    def Update_Probabilities(trial_probability): 
        
        nonlocal cell_probabilities;
        
        # Update the cell probabilities according to the probability of this trial
        unused_cells = np.where(stimuli_trial_data[EEG_epoch_index,:-1] == -1);
        
        flashed = np.where(stimuli_trial_data[EEG_epoch_index,:-1] == 1)
        n_per_flash = len(flashed);
        
        not_flashed = np.where(stimuli_trial_data[EEG_epoch_index,:-1] == 0);
        n_not_flashed = len(not_flashed);
        
        cell_probabilities[unused_cells] = 0;
        
        old_probabilities = cell_probabilities[:];
        
        cell_probabilities[flashed] = cell_probabilities[flashed] * trial_probability/n_per_flash;
        cell_probabilities[not_flashed] = cell_probabilities[not_flashed] * (1-trial_probability)/n_not_flashed;
        cell_probabilities[:] = cell_probabilities[:]/np.sum(cell_probabilities);
        
        # Weight previous probabilities
        cell_probabilities[:] = old_probabilities[:] * 0.1 + cell_probabilities[:] * 0.9;
        
        pass;
        
    #TODO: Broadcast_Classification_Status() docstring
    def Broadcast_Classification_Status():
        
        nonlocal waiting_start_new_classification;
        
        # Find what is currently the most probable cell
        most_probable_cell = np.argmax(cell_probabilities);
        
        print(cell_probabilities[most_probable_cell]);
        
        # Check if the most probable cell is above its threshold
        if(cell_probabilities[most_probable_cell] >= cell_thresholds[most_probable_cell]):
                    
            # Flag that the processor is waiting for the BCI to start streaming current data
            waiting_start_new_classification = True;
            
            # Broadcast the classification result
            # (offset by 1 then multiply by -1 as per scheme)           
            res = np.zeros(N_STREAM_ELEMENTS); # processor code = 0 --> classification
            res[most_probable_cell] = 1;
            processor_outlet.push_sample(res);
        
        # Else, a classification is not ready
        else:
        
            # Broadcast the current probabilities    
            res = np.empty(N_STREAM_ELEMENTS);
            res [:-1] = cell_probabilities;
            res[-1] = Processor_Code.PROBABILITY_UPDATE;
            processor_outlet.push_sample(res);
                
        pass;
        
    ##########################
    #   Initialize Filters   #
    ##########################    

    # Create a 60Hz notch filter with -3dB attenuation @ +-1Hz (main line)
    n60_b, n60_a = Signal.iirnotch(60, 60, fs=SAMPLING_FREQUENCY);
    # Create a 120Hz notch filter with -3dB attenuation @ +-1Hz (maine line echo)
    n120_b, n120_a = Signal.iirnotch(120, 60, fs=SAMPLING_FREQUENCY);
    # Filter out flash frequency to remove SSVEP component from signal
    # Create a flash-frequency filter with -3dB at +-0.2Hz
    nf_b, nf_a = Signal.iirnotch(FLASH_FREQUENCY, 60, fs=SAMPLING_FREQUENCY);
    # Create a bandpass butterworth filter with corner frequencies @ 1Hz and 40Hz
    bp_b, bp_a = Signal.butter(N=2, Wn=[1, 40], btype="bandpass", fs=SAMPLING_FREQUENCY);

    # Track the respective filter states
    n60_z = np.zeros((N_EEG_CHANNELS, 2));
    n120_z = np.zeros((N_EEG_CHANNELS, 2));
    nf_z = np.zeros((N_EEG_CHANNELS, 2));
    bp_z = np.zeros((N_EEG_CHANNELS, 4));

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
    
    #TODO: remove this
    # Live view    
    """
    live_EEG_index = 0;
    N_LIVE_SAMPLES = SAMPLING_FREQUENCY*5;
    live_EEG = np.zeros(N_LIVE_SAMPLES);
    
    import matplotlib.pyplot as plt;    
    plt.ylim([np.min(live_EEG)-1,np.max(live_EEG)+1]);
    plt.xlim([0,5]);
    plt.plot(np.arange(0,5,1/SAMPLING_FREQUENCY), live_EEG);
    plt.show();
    """
    
    ####################################
    #   Initialize stimuli variables   #
    ####################################
    
    # Initialize the stimuli trial matrix
    stimuli_trial_data = np.zeros((STIMULI_TO_HOLD, N_STREAM_ELEMENTS-1));
    
    # Initialize the stimuli trial index to 0
    stimuli_trial_index = 0;
    
    # Count the total number of trials received from the BCI
    # (in order to compare with the total number of epochs received from the Cyton)
    total_trials_received = 0;
    #TODO: trim this in accordance with total_epochs_received to prevent them from becoming annoyingly large
    #TODO: detect large gaps between this and total_epochs_received (to allow one to catch up)
        
    #################################################
    #   Load pretrained classifier and statistics   #
    #################################################
    mat_dict = LoadMAT("classifier_data.mat");
    
    mwms_classifer = np.array(mat_dict['mwms_classifier']);
    non_target_means = np.reshape(np.array(mat_dict['non_target_means']),(CORRELATION_DEGREE));
    non_target_cov = np.array(mat_dict['non_target_cov']);
    target_means = np.reshape(np.array(mat_dict['target_means']),(CORRELATION_DEGREE));
    target_cov = np.array(mat_dict['target_cov']);
            
    # Initialize cell probabilities
    #TODO: make sure this is okay
    cell_probabilities = np.ones(N_STREAM_ELEMENTS-1)/(N_STREAM_ELEMENTS-1);
    
    # Initialize threshold values
    #TODO: initialize dynamically
    cell_thresholds = DEFAULT_THRESHOLD * np.ones(N_STREAM_ELEMENTS-1);
    
    # Define the non target and target distributions
    non_target_mvn = MVN(mean = non_target_means, cov = non_target_cov);
    target_mvn = MVN(mean = target_means, cov = target_cov);
    
    ##################################
    #   Synchronize start with BCI   #
    ##################################
    
    # Wait for BCI to connect and send a start request
    console.info("Waiting for BCI to request start...");
    while(True):
        
        # Check for new input from the BCI
        # (Waiting for input 100ms at most, then trying again to allow for interrupts) 
        stimulus_input, _ = stimuli_inlet.pull_sample(0.1);
        if(stimulus_input is not None):
            
            # Check if the received signal is the start request
            if(stimulus_input[-1] == Stimuli_Code.START):
                
                # Exit the blocking loop
                break;
            
            # Else, a different signal was received
            else:
                
                #TODO: implement raising/handling an error since we should only expect a start request here
                #TODO: ^----? maybe ?
                console.warning("Received stimuli code",Stimuli_Code(stimulus_input[-1]),"when start request was expected.");
  
    console.info("Start request received from BCI.");    
            
    #TODO: make this less ghetto
    # Let the Cyton Data Packager know a consumer is connecting
    EEG_inlet.pull_chunk();
    console.info("Forcing data packager to dump samples for a few seconds...");
    time.sleep(5);
    # Discard the setup chunk
    # (this setup chunk will contain the FTDI turning on prior to the pins stabalizing --> we want to throw this out)
    EEG_inlet.pull_chunk(0.0);

    # Send the start signal to the BCI
    console.info("Sending start signal to BCI.");
    start_signal = np.empty(N_STREAM_ELEMENTS);
    start_signal[-1] = Processor_Code.START;
    processor_outlet.push_sample(start_signal);
    
    ###########################
    #   Main Processor Loop   #
    ###########################
    console.debug("Processor running...");
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
                Start_New_Classification();
                
            # Check if data being streamed is for the current classification
            if(not waiting_start_new_classification):
                
                # Normalize the epoch by channel
                normalized_epoch = EEG_epoch_data[EEG_epoch_index,:,:]/np.sum(EEG_epoch_data[EEG_epoch_index,:,:], axis=0);
                
                # Calculate the correlation coefficients
                correlation_coefficients = Calculate_Correlation_Coefficients(normalized_epoch); 
                
                # Calculate trial probability
                trial_probability = Calculate_Trial_Probability(correlation_coefficients);
                
                # Update cell probabilities
                Update_Probabilities(trial_probability);
                
                #TODO: calculate the probability that the user was looking at the screen at all
                
                # Broadcast classification status
                Broadcast_Classification_Status();
                
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

# Initialize the processor outlet
console.info("Opening P300_Processor outlet...");
info = StreamInfo("P300_Processor", "P300_Processor", N_STREAM_ELEMENTS, FLASH_FREQUENCY, "float32","P300_Processor");
processor_outlet = StreamOutlet(info);
console.info("P300_Processor outlet open.");

# Grab an inlet to the BCI stream
console.info("Resolving P300_Stimuli stream...");
inlet_stream = resolve_byprop("source_id", "BCI_GUI");
stimuli_inlet = StreamInlet(inlet_stream[-1]);
console.info("P300_Stimuli stream resolved.");

# Grab an inlet to the EEG stream
#TODO: make this non blocking and probably put it after the BCI synchronization part
console.info("Resolving Packaged_EEG stream...");
inlet_stream = resolve_byprop("source_id", "Cyton_Data_Packager");
EEG_inlet = StreamInlet(inlet_stream[-1]);
console.info("Packaged_EEG stream resolved.");

try:
    
    # Launch the processor
    #TODO: when adding Start() make Run() argument-less
    Run(processor_outlet, stimuli_inlet, EEG_inlet);
    
except KeyboardInterrupt:
    
    #TODO: wrap all of this and add more appropriate error checking
    
    # Disconnect from inlets
    EEG_inlet.close_stream();
    stimuli_inlet.close_stream();
    
    # Send shutdown signal to any consumers of this outlet
    processor_shutdown_signal = np.empty(N_STREAM_ELEMENTS).astype(int);
    processor_shutdown_signal[-1] = Processor_Code.PROCESSOR_SHUTDOWN;
                
    # Wait for consumers to disconnect
    #TODO: consider setting a max timeout for this
    while(processor_outlet.have_consumers()):     
        processor_outlet.push_sample(processor_shutdown_signal);        
        # Wait for 100ms, then try again (instead of blocking)
        # (this brief pause between calls allows for interrupts)
        time.sleep(0.1);
                
    # Completely delete the stimuli outlet
    processor_outlet.__del__();
    
    # Close the program
    print("Killing kernel...");
    time.sleep(1);
    
except Exception as e:
    
    #TODO: wrap all of this and add more appropriate error checking
    
    # Disconnect from inlets
    EEG_inlet.close_stream();
    stimuli_inlet.close_stream();
    
    # Send shutdown signal to any consumers of this outlet
    processor_shutdown_signal = np.empty(N_STREAM_ELEMENTS).astype(int);
    processor_shutdown_signal[-1] = Processor_Code.PROCESSOR_SHUTDOWN;
                
    # Wait for consumers to disconnect
    #TODO: consider setting a max timeout for this
    while(processor_outlet.have_consumers()):     
        processor_outlet.push_sample(processor_shutdown_signal);        
        # Wait for 100ms, then try again (instead of blocking)
        # (this brief pause between calls allows for interrupts)
        time.sleep(0.1);
                
    # Completely delete the stimuli outlet
    processor_outlet.__del__();
    
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
    














