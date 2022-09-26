# -*- coding: utf-8 -*-
"""

This program accomplishes 3 primary tasks.

    Task 1:
        Pull data from Cyton board using PyOpenBCI.
    Task 2:
        Detect the trial starts and determine if the trial is a sync trial
        or not using the flash and sync triggers.
    Task 3:
        Stamp and broadcast the 8-channel EEG data over LSL. Each sample is
        stamped with a 0, n, or -n
            0 ==> this sample is not the start of a trial
            n ==> this sample is the start of non-sync trial #n.
            -n ==> this sample is the start of sync trial #n.

CruX UCLA 2022

@author: Darren Vawter

"""

def main():
    
    import time;
    import math;
    import numpy as np;
    from pyOpenBCI import OpenBCICyton;
    from pylsl import StreamInfo, StreamOutlet;
    
    #TODO: search for suspiciously large time gaps between samples
    #TODO: check if any illegal trigger data is still being received
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    # The amount of time the P300 flashes a single trial for
    GUI_stimulus_time = 0.12;
      
    # The sampling rate of the Cyton board, in Hz
    sampling_rate = 250;
    
    # Declare cyton board
    cyton = [];
    
    # Initialize LSL stream
    stream_info = StreamInfo("Packaged_EEG", "Packaged_EEG", 9, 250, "float32");
    stream_outlet = StreamOutlet(stream_info);

    # Sample scaling    
    SCALE_FACTOR_EEG = (4500000)/24/(2**23-1) #uV/count
    SCALE_FACTOR_AUX = 0.002 / (2**4)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    def start():
    
        nonlocal cyton;   
        nonlocal sampling_rate;
            
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
        # A chunk of several data samples waiting to be sent
        chunk_to_send = np.empty([1,9]);
        
        # The time at which the last chunk was broadcasted over LSL
        # Initialized to start time start chunk timer from the start
        last_chunk_broadcast_time = time.time();
        
        # Minimum delay, in seconds, between consecutive chunk broadcasts
        chunk_broadcast_delay = 0.25;
        
        def send_chunk():
            
            nonlocal chunk_to_send;
            nonlocal last_chunk_broadcast_time;
            
            # Broadcast chunk over LSL            
            stream_outlet.push_chunk(chunk_to_send[1:,:].tolist());
            
            # Update last chunk broadcast time for next chunk
            last_chunk_broadcast_time = time.time();
        
            # Reset chunk back to empty-state
            chunk_to_send = np.empty([1,9])

            print("Chunk sent~~~~~~~~~~~~");

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
        # The most recent EEG sample pulled from the Cyton
        current_sample_EEG = np.zeros([1,8]);
        
        # The most recent trigger sample pulled from the Cyton
        current_sample_triggers = np.zeros(2);
        
        # The previous trigger sample pulled from the cyton
        # This is used to detect trigger changes between samples
        last_sample_triggers = np.zeros(2);
        
        # The number of samples gather since the last trigger flip
        n_samples_since_last_trial = 0;
        
        # Maximum amount of sample to wait for trigger to charge/discharge
        # (Currently using half of the intended samples)
        #TODO : investigate if there is a better threshold to use
        trigger_delay_threshold = math.floor(sampling_rate*GUI_stimulus_time/2);
        
        # Index of the current flash trial
        # (1-indexed for Matlab)
        trial_index = 1;
        
            
        # Packages 1 sample of EEG/trigger data and adds it to the pending chunk
        def package_sample(sample):
            
            nonlocal chunk_to_send;
            nonlocal last_chunk_broadcast_time;
            
            nonlocal current_sample_EEG;
            
            nonlocal current_sample_triggers;
            nonlocal last_sample_triggers;
            
            nonlocal n_samples_since_last_trial;
            nonlocal trigger_delay_threshold;
            
            nonlocal trial_index;
                
            # Pull sample from the 8 EEG channels
            current_sample_EEG = np.array(sample.channels_data)*SCALE_FACTOR_EEG;
            
            # Pull sample from the digital pins (this is a 1-byte value)
            pins = sample.aux_data[0];
            
            # Grab pin d11's sample (d11 is the MSB)
            # This is the flash trigger
            d11 = 1 if pins>=256 else 0;
            
            # Grab pin d12's sample (d12 is the LSB)
            # This is the sync trigger
            d12 = pins % 2;
            
            #TODO: remove this after satisfied
            if(pins!=0 and pins!=1 and pins!=256 and pins!=257):
                print("error");
                exit;
                quit;
                    
            # Set trigger sample
            current_sample_triggers = np.array([d11, d12]);
            
            # Prepare stamp and initialize it to an error flag
            stamp = 'e';
            
            # Check if the triggers have changed between now and the last sample            
            if(current_sample_triggers[0]==last_sample_triggers[0] and current_sample_triggers[1]==last_sample_triggers[1]):
                
                # Neither trigger changed (sample *isn't* start of a trial)
                
                # Stamp the sample with a 0
                stamp = 0;
                
                # Increment the number of samples collected since the last flip
                n_samples_since_last_trial += 1;
                
            elif(current_sample_triggers[0]!=last_sample_triggers[0] and current_sample_triggers[1]!=last_sample_triggers[1]):
        
                # Both triggers flipped
                
                # Stamp as sync trial
                stamp = -trial_index;
                print("Both flipped", trial_index, "sync",n_samples_since_last_trial);
                
                # Increment trial #
                trial_index += 1;
                                
                # Reset the number of samples seen since this is a new trial
                n_samples_since_last_trial = 1;
                
            elif(current_sample_triggers[0]!=last_sample_triggers[0]):
                
                # The flash trigger flipped
                
                # Check if trigger was just delayed due to charging time
                if(n_samples_since_last_trial < trigger_delay_threshold):
                    
                    # This flip is not the true start, the previous flip was
                    
                    # Stamp the sample with a 0
                    stamp = 0;
                
                    # The previous flip was already marked as a sync trial
                    pass;
                    
                else:
                    
                    # This flip appears to be the start of a non-sync trial
                    stamp = trial_index; 
                    print("Flash flipped", trial_index, "non-sync",n_samples_since_last_trial);
                    
                    # Increment trial #
                    trial_index += 1;                                  
                    
                    # Reset the number of samples seen since this is a new trial
                    n_samples_since_last_trial = 1;
                
            elif(current_sample_triggers[1]!=last_sample_triggers[1]):               
                                
                # The sync trigger flipped
                
                # Check if trigger was just delayed due to charging time
                if(n_samples_since_last_trial < trigger_delay_threshold):
                    
                    # This flip is not the true start, the previous flip was
                    
                    # Stamp the sample with a 0
                    stamp = 0;
                    print("Sync flipped", trial_index-1, "sync",n_samples_since_last_trial);
                    print("Went back and fixed previous trial.");
                
                    # The previous flip was marked wrong; fix it
                    bad_stamp_ind = np.argmax(chunk_to_send[:,8]);
                    chunk_to_send[bad_stamp_ind,8] *= -1;
                    
                else:
                    
                    # This flip appears to be the start of a sync trial
                    stamp = -trial_index;
                    print("Sync flipped", trial_index, "sync",n_samples_since_last_trial);
                    
                    # Increment trial #
                    trial_index += 1;    
                                        
                    # Reset the number of samples seen since this is a new trial
                    n_samples_since_last_trial = 1;
                                
            # Set last trigger for next sample
            last_sample_triggers = current_sample_triggers;  
                    
            # Stamp the sample to complete its packaging
            packaged_sample = np.hstack((current_sample_EEG,np.atleast_1d(stamp)));
    
            # Append the packaged sample to the current chunk
            chunk_to_send = np.vstack((chunk_to_send, packaged_sample));
                        
            # Check if enough time has elapsed to send the chunk
            # (This is in case the sync trigger was charge-delayed)
            # (This would cause incorrect stamping of the previous trial)
            if(n_samples_since_last_trial > trigger_delay_threshold and time.time()-last_chunk_broadcast_time > chunk_broadcast_delay):
                    
                # Trigger has had enough time
                  
                # Send the chunk
                send_chunk();
                
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                
        # Connect to bluetooth dongle on COM port 3
        cyton = OpenBCICyton(port='COM3')
              
        # Configure the board into digital read mode
        cyton.write_command('/3');
        
        # Start the board stream with callback
        cyton.start_stream(package_sample);
    
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
    try:
        start();
    except KeyboardInterrupt:
        
        # Disconnect the Cyton to release the COM port
        if(not isinstance(cyton, list)):
            cyton.disconnect();
        print("Disconnected from COM port.");
        
        # Close the stream so that it is not discoverable
        stream_outlet.__del__();
        print("Stream outlet destroyed.");
        
        # Close the program
        print("Killing kernel...");
        time.sleep(1);
        exit;
        quit;       
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


main();

























