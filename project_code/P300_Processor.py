# -*- coding: utf-8 -*-
"""


@author: Darren Vawter
"""

# External Modules
import time;
import numpy as np;
from scipy import signal as Signal;
from scipy.stats import multivariate_normal as MVN;
from math import ceil as ceil;
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop; # communicating with BCI and Cyton
import logging; # print pretty console logs

# Internal Modules
from BCI_Enumerations import Stimuli_Code, Processor_Code, Processor_Mode;
from BCI_Constants import N_STREAM_ELEMENTS, DEFAULT_THRESHOLD, SAMPLING_FREQUENCY, FLASH_FREQUENCY, N_EEG_CHANNELS, N_TILES, N_TILES_PER_FLASH;
from Logging_Formatter import Logging_Formatter; # custom format for pretty console logs

def Start():

    #TODO: wrap this
    # Create a console logger for pretty formatting
    console = logging.getLogger("P300_Processor.py");
    console.setLevel(logging.DEBUG);
    if(console.hasHandlers()):
        console.handlers.clear();
    ch = logging.StreamHandler();
    ch.setFormatter(Logging_Formatter());
    console.addHandler(ch);
    
    # TODO: Shutdown_Processor() docstring
    def Shutdown_Processor():    
                                    
        console.critical("Shutting down processor...");
        
        #############################
        #   Destroy the EEG inlet   #
        #############################
                
        try:
            
            console.info("Destroying EEG inlet...");
            
            if(EEG_inlet is not None):
                
                # Safely close the inlet
                # (Also lets outlets know that this consumer has been removed)
                EEG_inlet.close_stream();
                
                # Completely delete the processor inlet
                EEG_inlet.__del__();
                
            else:
                
                console.warning("'EEG_inlet' is not defined.");
                
        except NameError:
            
            console.warning("'EEG_inlet' is not declared.");
            
        except Exception as e:
            raise e;
            
        #################################
        #   Destroy the stimuli inlet   #
        #################################
                
        try:
            
            console.info("Destroying stimuli inlet...");
            
            if(stimuli_inlet is not None):
                
                # Safely close the inlet
                # (Also lets outlets know that this consumer has been removed)
                stimuli_inlet.close_stream();
                
                # Completely delete the processor inlet
                stimuli_inlet.__del__();
                
            else:
                
                console.warning("'stimuli_inlet' is not defined.");
                
        except NameError:
            
            console.warning("'stimuli_inlet' is not declared.");
            
        except Exception as e:
            raise e;
                  
        ####################################
        #   Destroy the processor outlet   #
        ####################################  
        
        try:
            
            console.info("Destroying processor outlet...");
            
            if(processor_outlet is not None):
                
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
                
            else:
                
                console.warning("'processor_outlet' is not defined.");
                
        except NameError:
            
            console.warning("'processor_outlet' is not declared.");
            
        except Exception as e:
            
            raise e;
                          
        # End of Shutdown_Controller
        console.critical("Processor shutdown complete.");
        pass;
        
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
                stimuli_trial_data[stimuli_trial_index,:] = stimulus_input[:];
                
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
                
            # Check if the stream data is a start request
            elif(stimuli_code == Stimuli_Code.REQUEST_START):
                #TODO: this probably shouldn't happen --> decide what to do
                pass;
                
            # Check if the stream data is a restart request
            elif(stimuli_code == Stimuli_Code.REQUEST_RESTART):
                #TODO: decide what to do when the interface is requesting a restart
                #(if this is even necessary)
                pass;
                
            # Check if the stream data is a program shutdown announcement
            elif(stimuli_code == Stimuli_Code.BCI_SHUTDOWN):
                #TODO: generate a different kind of interrupt here
                raise Exception("BCI shutdown signal received.");
                
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
            
            nonlocal EEG_samples, EEG_sample_index, processor_running, live_EEG_index, plot_time;
            
            # Filter the chunk
            EEG_chunk = Filter_Chunk(EEG_chunk);
                        
            # Grab the size of the chunk
            chunk_size = len(EEG_chunk);
                
            #TODO: remove
            #{~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Live view
            """
            if(live_EEG_index + chunk_size < N_LIVE_SAMPLES):
                try:
                    live_EEG[live_EEG_index:live_EEG_index+chunk_size,:] = EEG_chunk[:,:-1];
                except Exception as e:
                    console.warning(live_EEG_index);      
                    console.warning(chunk_size);      
                    console.warning(N_LIVE_SAMPLES);      
                    console.warning(np.shape(live_EEG));                    
                    raise e;
                live_EEG_index = live_EEG_index+chunk_size;
            else:
                live_EEG[live_EEG_index:,:] = EEG_chunk[:N_LIVE_SAMPLES-live_EEG_index,:-1];
                live_EEG[:live_EEG_index+chunk_size-N_LIVE_SAMPLES,:] = EEG_chunk[N_LIVE_SAMPLES-live_EEG_index:,:-1];
                live_EEG_index = live_EEG_index+chunk_size-N_LIVE_SAMPLES;
                
            if(time.time()-plot_time >= 1):
                for ch in range(8):
                    plt.subplot(2,4,ch+1);
                    plt.ylim([np.min(live_EEG[:,ch]),np.max(live_EEG[:,ch])]);
                    plt.xlim([0,5]);
                    plt.plot(np.arange(0,5,1/SAMPLING_FREQUENCY), np.concatenate((live_EEG[live_EEG_index:,ch],live_EEG[:live_EEG_index,ch])));
                plt.show();
                plot_time = time.time();
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
            trial_stimuli_code = Stimuli_Code(stimuli_trial_data[EEG_epoch_index,-1]);
            
            # Check if the BCI sync flag is a non-sync code
            if(trial_stimuli_code == Stimuli_Code.NON_SYNC or trial_stimuli_code == Stimuli_Code.NON_SYNC_START):
                BCI_sync_code = False;
                
            # Check if the BCI sync flag is a sync code
            elif(trial_stimuli_code == Stimuli_Code.SYNC or trial_stimuli_code == Stimuli_Code.SYNC_START):
                BCI_sync_code = True;
    
            # Check if this is a training trial
            elif(trial_stimuli_code == Stimuli_Code.TRAINING):
                #TODO: enumerate this
                BCI_sync_code = (3 in stimuli_trial_data[EEG_epoch_index,:]);         
                
            # Else, an invalid sync flag was received from the BCI stream
            else:
                
                console.warning(trial_stimuli_code);
                console.warning(BCI_sync_code);
                
                raise ValueError("Invalid sync flag received from BCI stream.");
                
            # Check for desynchronization
            if(Cyton_sync_code != BCI_sync_code):
                                         
                print(EEG_epoch_index);
                print(EEG_samples[:200,-1]);
                print(stimuli_trial_data[EEG_epoch_index-10:EEG_epoch_index,-1]);
                print(stimuli_trial_data[EEG_epoch_index:EEG_epoch_index+10,-1]);
                  
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
        #TODO: docstring        
        """
        def Initialize_Classifier():
            
            nonlocal overlay_classifiers, overlay_target_means, overlay_target_cov, overlay_target_mvn, overlay_non_target_means, overlay_non_target_cov, overlay_non_target_mvn;
            
            console.info("Initializing classifier...");
                                 
            # Declare classifiers
            overlay_classifiers = np.zeros((CORRELATION_DEGREE,SAMPLES_PER_EPOCH,N_EEG_CHANNELS));
            
            # Declare correlation coefficients
            target_coefficients = np.empty((CORRELATION_DEGREE, N_TRAINING_TARGETS));
            non_target_coefficients = np.empty((CORRELATION_DEGREE, N_TRAINING_NON_TARGETS));
            
            # 0th degree classifier is just the average target signal
            overlay_classifiers[0,:,:] = np.sum(target_epochs, axis=0) / len(target_epochs);
    
            # 0th degree correlation data is the uncorrelated data                    
            target_data = target_epochs;
            non_target_data = non_target_epochs;
    
            # Initialize a classifier for each degree of correlation
            for order in range(CORRELATION_DEGREE):
            
                # Normalize the previous degree's correlation
                overlay_classifiers[order,:,:] /= np.linalg.norm(overlay_classifiers[order,:,:], axis=0, ord=3);
                
                # Initialize output of this degree's correlation per sample
                next_target_data = np.zeros((N_TRAINING_TARGETS,SAMPLES_PER_EPOCH,N_EEG_CHANNELS));
                next_non_target_data = np.zeros((N_TRAINING_NON_TARGETS,SAMPLES_PER_EPOCH,N_EEG_CHANNELS));
            
                # For each target trial
                for target_index in range(N_TRAINING_TARGETS):
                    
                    # Normalize the trial
                    target_data[target_index,:,:] /= np.linalg.norm(target_data[target_index,:,:], axis=0, ord=3);
            
                    # Initialize the correlation coefficient
                    coefficient = 0;
                    
                    # For each eeg channel
                    for channel in range(N_EEG_CHANNELS):
                    
                        # Increment the correlation coefficient by the result of the channel's correlation coefficient
                        coefficient += np.correlate(overlay_classifiers[order,:,channel],target_data[target_index,:,channel]);   
                        
                        # Calculate the cross correlation of the trial with the current degree of the classifier
                        corr = np.correlate(overlay_classifiers[order,:,channel],target_data[target_index,:,channel],"same");      
                        
                        # Store the cross correlation result for the next degree
                        next_target_data[target_index,:,channel] = corr;            
                        
                        # Increment the next degree's classifier by the cross correlation result
                        if(order+1<CORRELATION_DEGREE):
                            overlay_classifiers[order+1,:,channel] += corr;
                    
                    # Calculate the average per-channel correlation coefficient
                    target_coefficients[order,target_index] = coefficient/N_EEG_CHANNELS;
                    
                # Calculate the average per-target correlation result for this degree
                if(order+1<CORRELATION_DEGREE):
                    overlay_classifiers[order+1,:,:] /= N_TRAINING_TARGETS;                    
                
                # For each non-target trial
                for non_target_index in range(N_TRAINING_NON_TARGETS):
                    
                    # Normalize the trial
                    non_target_data[non_target_index,:,:] /= np.linalg.norm(non_target_data[non_target_index,:,:], axis=0, ord=3);
                    
                    # Initialize the correlation coefficient
                    coefficient = 0;
                    
                    # For each eeg channel
                    for channel in range(N_EEG_CHANNELS):
                        
                        # Increment the correlation coefficient by the result of the channel's correlation coefficient
                        coefficient += np.correlate(overlay_classifiers[order,:,channel],non_target_data[non_target_index,:,channel]);
                    
                        # Calculate the cross correlation of the trial with the current degree of the classifier
                        corr = np.correlate(overlay_classifiers[order,:,channel],non_target_data[non_target_index,:,channel],"same");   
                    
                        # Store the cross correlation result for the next degree
                        next_non_target_data[non_target_index,:,channel] = corr;
                            
                    # Calculate the average per-channel correlation coefficient
                    non_target_coefficients[order,non_target_index] = coefficient/N_EEG_CHANNELS;
                    
                # Plot a histogram for the non-target and target distributions
                plt.subplot(2,2,order+1);
                _, nt_bins, _ = plt.hist(non_target_coefficients[order,:], alpha=0.5);
                _, t_bins, _ = plt.hist(target_coefficients[order,:], alpha=0.5);    
                        
                # Generate x axis
                x = np.arange(np.min(non_target_coefficients[order,:]),np.max(target_coefficients[order,:]),0.01);
                
                # Plot a 1-d target pdf
                target_mvn = MVN(mean = np.mean(target_coefficients[order,:]), cov = np.std(target_coefficients[order,:])**2);
                plt.plot(x,target_mvn.pdf(x)*N_TRAINING_TARGETS*(t_bins[1]-t_bins[0]));  
                   
                # Plot a 1-d non-target pdf
                non_target_mvn = MVN(mean = np.mean(non_target_coefficients[order,:]), cov = np.std(non_target_coefficients[order,:])**2);
                plt.plot(x,non_target_mvn.pdf(x)*N_TRAINING_NON_TARGETS*(nt_bins[1]-nt_bins[0]));  
                   
                # Set the next degree's data as the output from this degree
                target_data = next_target_data;
                non_target_data = next_non_target_data;
                
            # Calculate the training statistics
            overlay_target_means = np.mean(target_coefficients, axis=1);
            overlay_target_cov = np.cov(target_coefficients);
            overlay_non_target_means = np.mean(non_target_coefficients, axis=1);
            overlay_non_target_cov = np.cov(non_target_coefficients);

            # Save the pre-trained classifier
        
            np.save("classifiers.npy", overlay_classifiers);
            np.save("target_means.npy", overlay_target_means);
            np.save("target_cov.npy", overlay_target_cov);
            np.save("non_target_means.npy", overlay_non_target_means);
            np.save("non_target_cov.npy", overlay_non_target_cov);

            # Generate normal distributions from the training statistics
            overlay_target_mvn = MVN(mean = overlay_target_means, cov = overlay_target_cov);
            overlay_non_target_mvn = MVN(mean = overlay_non_target_means, cov = overlay_non_target_cov);
       
            # End of Initialize_Classifier()
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
            unused_cells = np.where(stimuli_trial_data[EEG_epoch_index,:-1] == -1);
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
            
            
            #TODO: comments
            
            correlation_coefficients = np.zeros(CORRELATION_DEGREE);
            
            current_data = normalized_epoch;
            next_data = np.empty((SAMPLES_PER_EPOCH,N_EEG_CHANNELS));
                
            for order in range(CORRELATION_DEGREE):
                
                current_data[:,:] /= np.linalg.norm(current_data[:,:], axis=0, ord=3);
                
                for channel in range(N_EEG_CHANNELS):
                    
                    correlation_coefficients[order] += np.correlate(overlay_classifiers[order,:,channel],current_data[:,channel]);    
                    
                    next_data[:,channel] = np.correlate(overlay_classifiers[order,:,channel],current_data[:,channel], "same"); 

                correlation_coefficients[order] /= 8;
                
                current_data = next_data;
        
            return correlation_coefficients;
        
            # End of Calculate_Correlation_Coefficients()
            pass;
            
        #TODO: Calculate_Trial_Probability() docstring
        def Calculate_Trial_Probability(correlation_coefficients):         
            
            # Get the number per flash
            flashed = np.where(stimuli_trial_data[EEG_epoch_index,:-1] == 1);
            n_per_flash = len(flashed);  
            
            # Get the number not flashed
            not_flashed = np.where(stimuli_trial_data[EEG_epoch_index,:-1] == 0);
            n_not_flashed = len(not_flashed);
            
            # Get the number used
            n_used = n_per_flash + n_not_flashed;
            
            # Generate an independent probability (density) that this trial was a target trial
            trial_target_probability = overlay_target_mvn.pdf(correlation_coefficients)*n_per_flash/n_used;
            
            # Generate an independent probability (density) that this trial was a non-target trial
            trial_non_target_probability = overlay_non_target_mvn.pdf(correlation_coefficients)*n_not_flashed/n_used;
                                              
            # Normalize the generated probability densities
            p_space = trial_target_probability + trial_non_target_probability;
            
            # Return the normalized target probability
            return trial_target_probability/p_space;
        
            # End of Calculate_Trial_Probability()
            pass;
        
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
            #TODO: determine weighting coefficient
            cell_probabilities[:] = old_probabilities[:] * 0.15 + cell_probabilities[:] * 0.85;

            most_probable_cell = np.argmax(cell_probabilities);         
            #console.warning(str(most_probable_cell)+": "+str(np.amax(cell_probabilities))+"\n"+str(cell_probabilities));
            
            # End of Update_Probabilities()
            pass;
            
        #TODO: Broadcast_Classification_Status() docstring
        def Broadcast_Classification_Status():
            
            nonlocal waiting_start_new_classification;
            
            # Find what is currently the most probable cell
            most_probable_cell = np.argmax(cell_probabilities);         
            
            # Check if the most probable cell is above its threshold
            if(cell_probabilities[most_probable_cell] >= cell_thresholds[most_probable_cell]):
                
                # Flag that the processor is waiting for the BCI to start streaming current data
                waiting_start_new_classification = True;
                
                # Broadcast the classification result
                # (offset by 1 then multiply by -1 as per scheme)           
                res = np.zeros(N_STREAM_ELEMENTS); # processor code = 0 --> classification
                res[most_probable_cell] = 1;
                processor_outlet.push_sample(res);    
                
                console.debug(cell_probabilities);
                console.debug(most_probable_cell);
            
            # Else, a classification is not ready
            else:
            
                # Broadcast the current probabilities    
                res = np.empty(N_STREAM_ELEMENTS);
                #console.debug(cell_probabilities)
                res [:-1] = cell_probabilities;
                res[-1] = Processor_Code.PROBABILITY_UPDATE;
                
                
                #TODO: remove once probabilities actually calculate
                res [:-1] = 0.1*np.zeros(N_STREAM_ELEMENTS-1);
                
                
                processor_outlet.push_sample(res);
                    
            # End of Broadcast_Classification_Status()
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
        
        #TODO: comment these        
        N_TRAINING_TARGETS = 300;
        N_TRAINING_NON_TARGETS = ceil(N_TRAINING_TARGETS*((N_TILES/N_TILES_PER_FLASH)-1));
        CORRELATION_DEGREE = 4;        
        FILTER_SETTLING_TIME = 20;
        CYTON_SETTLING_TIME = 5;
        
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
        
        # Track the processor's current mode
        processor_mode = None;
        
        # Track whether the processor is waiting for the first trial of the new classification
        waiting_start_new_classification = False;
        
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
        live_EEG_index = 0;
        N_LIVE_SAMPLES = SAMPLING_FREQUENCY*5;
        live_EEG = np.zeros((N_LIVE_SAMPLES,N_EEG_CHANNELS));
        
        import matplotlib.pyplot as plt;    
        """
        plt.ylim([np.min(live_EEG),np.max(live_EEG)]);
        plt.xlim([0,5]);
        plt.plot(np.arange(0,5,1/SAMPLING_FREQUENCY), live_EEG);
        plt.show();
        """
        plot_time = time.time();
        
        ####################################
        #   Initialize stimuli variables   #
        ####################################
        
        # Initialize the stimuli trial matrix
        stimuli_trial_data = np.zeros((STIMULI_TO_HOLD, N_STREAM_ELEMENTS));
        
        # Initialize the stimuli trial index to 0
        stimuli_trial_index = 0;
        
        # Count the total number of trials received from the BCI
        # (in order to compare with the total number of epochs received from the Cyton)
        total_trials_received = 0;
        #TODO: trim this in accordance with total_epochs_received to prevent them from becoming annoyingly large
        #TODO: detect large gaps between this and total_epochs_received (to allow one to catch up)
                                    
        # Initialize cell probabilities
        #TODO: make sure this is okay
        cell_probabilities = np.ones(N_STREAM_ELEMENTS-1)/(N_STREAM_ELEMENTS-1);
        
        # Initialize threshold values
        #TODO: initialize dynamically
        cell_thresholds = DEFAULT_THRESHOLD * np.ones(N_STREAM_ELEMENTS-1);
                
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
                if(stimulus_input[-1] == Stimuli_Code.REQUEST_START):
                    
                    # Exit the blocking loop
                    break;
                
                # Else, a different signal was received
                else:
                    
                    #TODO: implement raising/handling an error since we should only expect a start request here
                    #TODO: ^----? maybe ?
                    console.warning("Received stimuli code",Stimuli_Code(stimulus_input[-1]),"when start request was expected.");
      
        console.info("Start request received from BCI.");    
                
        #TODO: make this less ghetto
        #TODO: make sure these chunks don't contain an early shutdown signal
        # Let the Cyton Data Packager know a consumer is connecting
        EEG_inlet.pull_chunk();
        console.info("Forcing data packager to dump samples for a few seconds...");
        time.sleep(5);
        # Discard the setup chunk
        # (this setup chunk will contain the FTDI turning on prior to the pins stabalizing --> we want to throw this out)
        EEG_inlet.pull_chunk(0.0);

        # Check to see if pre-trained data is available to initialize a classifier
        try:
        
            ###########################################
            #   Load pre-trained overlay classifier   #
            ###########################################
        
            overlay_classifiers = None;
            overlay_target_means = None;
            overlay_target_cov = None;
            overlay_target_mvn = None;
            overlay_non_target_means = None;
            overlay_non_target_cov = None;
            overlay_non_target_mvn = None;
        
            # Try to pull pre-trained overlay MWMS classifiers
            # (correlation_degree x n_samples_per_epoch x n_channels)
            overlay_classifiers = np.load("classifiers.npy");
            
            # If the pre-trained degree is less than the declared degree, treat these classifiers as insufficient
            if(len(overlay_classifiers) < CORRELATION_DEGREE):
                raise FileNotFoundError();
            # Else, trim off excess correlation degrees
            else:
                overlay_classifiers = overlay_classifiers[:CORRELATION_DEGREE,:,:];
            
            # Load the pre-trained statistics for the overlay classifier
            overlay_target_means = np.load("target_means.npy");
            overlay_target_cov = np.load("target_cov.npy");
            overlay_non_target_means = np.load("non_target_means.npy");
            overlay_non_target_cov = np.load("non_target_cov.npy");

            # Define the overlay non target and target distributions
            overlay_non_target_mvn = MVN(mean = overlay_non_target_means, cov = overlay_non_target_cov);
            overlay_target_mvn = MVN(mean = overlay_target_means, cov = overlay_target_cov);
        
            # Set the processor mode
            processor_mode = Processor_Mode.CLASSIFICATION_OVERLAY;
            
            # Send the BCI a signal to start in classification mode
            console.info("Sending classification-start signal to BCI.");
            start_signal = np.empty(N_STREAM_ELEMENTS);
            start_signal[-1] = Processor_Code.START_CLASSIFICATION;
            processor_outlet.push_sample(start_signal);
            
            # Start a timer to ensure the filter initializes before collecting data
            filter_start_time = time.time();
            
        # Else, there is no training data available; training is needed
        except FileNotFoundError:
            
            #####################################
            #   Initialize training variables   #
            #####################################
            
            # Initialize target training epoch array
            target_epochs = np.empty((N_TRAINING_TARGETS,SAMPLES_PER_EPOCH,N_EEG_CHANNELS));
            target_epochs_received = 0;
            
            # Initialize non-target training epoch array
            non_target_epochs = np.empty((N_TRAINING_NON_TARGETS,SAMPLES_PER_EPOCH,N_EEG_CHANNELS));
            non_target_epochs_received = 0;
        
            # Set the processor mode
            processor_mode = Processor_Mode.TRAINING_OVERLAY;
            
            # Send the BCI a signal to start in training mode
            console.info("Sending training-start signal to BCI.");
            start_signal = np.empty(N_STREAM_ELEMENTS);
            start_signal[-1] = Processor_Code.START_TRAINING;
            processor_outlet.push_sample(start_signal);
            
            # Start a timer to ensure the filter initializes before collecting data
            filter_start_time = time.time();
                    
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
                
                # Ensure that the streams have not de-synced
                Synchronize_Streams();
                
                # Pull the epoch from the EEG samples and trim the EEG samples appropriately
                Construct_Epoch();
        
                #############################
                #   Handle Training Epoch   #
                #############################
                                                       
                # Check if this epoch is a training epoch
                if(stimuli_trial_data[EEG_epoch_index,-1] == Stimuli_Code.TRAINING):
                                        
                    # Validate that training data was expected
                    if(processor_mode != Processor_Mode.TRAINING_KEYBOARD and processor_mode != Processor_Mode.TRAINING_OVERLAY):
                    
                        # Check if the program is still waiting for a new classification to start
                        if(not waiting_start_new_classification):
                            console.warning("Received training data when not expected.");              
                                                
                    # Validate that the filter is settled
                    elif(time.time()-filter_start_time > FILTER_SETTLING_TIME):
                    
                        # Normalize the epoch by channel
                        normalized_epoch = EEG_epoch_data[EEG_epoch_index,:,:]/np.linalg.norm(EEG_epoch_data[EEG_epoch_index,:,:], axis=0);
                        
                        # Check if target key was flashed (code = 3)
                        if(3 in stimuli_trial_data[EEG_epoch_index,:-1]):
                            
                            # Check if more target epochs are needed
                            if(target_epochs_received < N_TRAINING_TARGETS):
                                # Add this epoch to the target training set
                                target_epochs[target_epochs_received,:,:] = normalized_epoch;
                                target_epochs_received += 1;
                        
                        # Check if this epoch is a non-target epoch and more non-target epochs are needed
                        # Else, check if target key was not flashed (code = 2)
                        elif(2 in stimuli_trial_data[EEG_epoch_index,:-1]):
                            
                            # Check if more non-target epochs are needed
                            if(non_target_epochs_received<N_TRAINING_NON_TARGETS):
                                # Add this epoch to the non-target training set
                                non_target_epochs[non_target_epochs_received,:,:] = normalized_epoch;
                                non_target_epochs_received += 1;
                            
                        # Else, no target key was found in the training data
                        else:
                            
                            raise RuntimeError("No target key found in training data.");
                            
                        # Check if the training limit has been reached
                        if(target_epochs_received==N_TRAINING_TARGETS and non_target_epochs_received==N_TRAINING_NON_TARGETS):
                            
                            # Save training data (for testing purposes)
                            np.save("targets.npy", target_epochs);
                            np.save("non_targets.npy", non_target_epochs);
                            
                            # Initialize classifier
                            Initialize_Classifier();                            
                            
                            # Switch the processor to overlay classification mode
                            processor_mode = Processor_Mode.CLASSIFICATION_OVERLAY;
                            
                            # Flag that the processor is waiting for a new classification trial
                            waiting_start_new_classification = True;
                            
                            # Send the BCI a signal to start in classification mode
                            console.info("Sending classification-start signal to BCI.");
                            start_signal = np.empty(N_STREAM_ELEMENTS);
                            start_signal[-1] = Processor_Code.START_CLASSIFICATION;
                            processor_outlet.push_sample(start_signal);
                            
                        elif(target_epochs_received%(N_TRAINING_TARGETS/20) == 0 ):
                            
                            console.debug(100*target_epochs_received/N_TRAINING_TARGETS);
                            console.warning(100*non_target_epochs_received/N_TRAINING_NON_TARGETS);

                ###################################
                #   Handle Classification Epoch   #
                ###################################
        
                # Else, the epoch is a classification epoch
                else:
                                
                    # Validate that there is a classifier
                
                    # Check if this epoch is the first trial of a new classification
                    if(stimuli_trial_data[EEG_epoch_index,-1] == Stimuli_Code.NON_SYNC_START or stimuli_trial_data[EEG_epoch_index,-1] == Stimuli_Code.SYNC_START):
                                
                        # Handle classification start
                        Start_New_Classification();
                        
                    # Check if data being streamed is for the current classification
                    if(not waiting_start_new_classification):
                        
                        # Normalize the epoch by channel
                        normalized_epoch = EEG_epoch_data[EEG_epoch_index,:,:]/np.linalg.norm(EEG_epoch_data[EEG_epoch_index,:,:], axis=0);
                        
                        # Calculate the correlation coefficients
                        correlation_coefficients = Calculate_Correlation_Coefficients(normalized_epoch); 
                        
                        # Calculate trial probability
                        trial_probability = Calculate_Trial_Probability(correlation_coefficients);
                        
                        # Update cell probabilities
                        #TODO: un-ghetto-ify this
                        if(time.time()-filter_start_time > FILTER_SETTLING_TIME):
                           Update_Probabilities(trial_probability);
                           pass;
                        
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
        
    try:
    
        # Initialize the processor outlet
        console.info("Opening P300_Processor outlet...");
        info = StreamInfo("P300_Processor", "P300_Processor", N_STREAM_ELEMENTS, FLASH_FREQUENCY, "float32","P300_Processor");
        processor_outlet = StreamOutlet(info);
        console.info("P300_Processor outlet open.");
        
        # Grab an inlet to the BCI stream
        console.info("Resolving P300_Stimuli stream...");
        inlet_stream = [];
        while(len(inlet_stream) < 1):
            # Wait for 100ms, then try again (instead of blocking)
            # (this recycle between calls allows for interrupts)
            inlet_stream = resolve_byprop("source_id", "BCI_GUI",timeout=0.1);  
            
        # If multiple outlets were found, shut down and raise error
        # (shutdown dependancies are not functioning or multiple processors are running)
        if(len(inlet_stream) > 1):
            Shutdown_Processor();
            raise RuntimeError("Multiple streams broadcasting BCI_GUI")
            
        # Specify the inlet (resolve_byprop returns a list object of inlets)
        stimuli_inlet = StreamInlet(inlet_stream[0]);     
        console.info("P300_Stimuli stream resolved.");        
        
        # Grab an inlet to the EEG stream
        console.info("Resolving Packaged_EEG stream...");
        inlet_stream = [];
        while(len(inlet_stream) < 1):
            # Wait for 100ms, then try again (instead of blocking)
            # (this recycle between calls allows for interrupts)
            inlet_stream = resolve_byprop("source_id", "Cyton_Data_Packager",timeout=0.1);  
            
        # If multiple outlets were found, shut down and raise error
        # (shutdown dependancies are not functioning or multiple processors are running)
        if(len(inlet_stream) > 1):
            Shutdown_Processor();
            raise RuntimeError("Multiple streams broadcasting Cyton_Data_Packager")
                  
        # Specify the inlet (resolve_byprop returns a list object of inlets)
        EEG_inlet = StreamInlet(inlet_stream[0]);     
        console.info("Packaged_EEG stream resolved.");
    
        # Launch the processor
        #TODO: when adding Start() make Run() argument-less
        Run(processor_outlet, stimuli_inlet, EEG_inlet);
        
    except KeyboardInterrupt:
        
        console.warning("Keyboard interrupt detected.");
        Shutdown_Processor();
        
    except Exception as e:
                    
        console.error("Unhandled error raised.");
        Shutdown_Processor();        
        raise e;
        
    else:
        
        Shutdown_Processor();
        
    finally:
               
        import sys
        sys.exit(0);

    # End of Start()
    pass;
        
    

#TODO: call this from a file that independently starts all 3 processes          
Start();



