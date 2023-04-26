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

import time;
import math;
import numpy as np;
from pyOpenBCI import OpenBCICyton;
from pylsl import StreamInfo, StreamOutlet;
import logging;

from Logging_Formatter import Logging_Formatter;

#TODO: search for suspiciously large time gaps between samples
#TODO: check if any illegal trigger data is still being received

def Start():
  
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #TODO: wrap this
    # Create a console logger for pretty formatting
    console = logging.getLogger("BCI_Controller.py");
    console.setLevel(logging.DEBUG);
    if(console.hasHandlers()):
        console.handlers.clear();
    ch = logging.StreamHandler();
    ch.setFormatter(Logging_Formatter());
    console.addHandler(ch);
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    # The amount of time the P300 flashes a single trial for
    GUI_stimulus_time = 0.12;
      
    # The sampling rate of the Cyton board, in Hz
    sampling_rate = 250;
        
    # Sample scaling    
    SCALE_FACTOR_EEG = (4500000)/24/(2**23-1); #uV/count
    SCALE_FACTOR_AUX = 0.002 / (2**4);
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    def Shutdown_Cyton_Data_Packager():
        
        console.critical("Shutting down Cyton data packager...");
        
        ######################################
        #   Destroy the UM232R FTDI object   #
        ######################################
        
        try:
            
            console.info("Destroying Cyton's OpenBCICyton object...");
            
            if(cyton is not None):
                
                # Disconnect the Cyton to release the COM port
                cyton.disconnect();
                
            else:
                
                console.warning("'cyton' is not defined.");
                
        except NameError:
            
            console.warning("'cyton' is not declared.");
            
        except Exception as e:
            
            raise e;
                    
        ##############################
        #   Destroy the EEG outlet   #
        ##############################  
        
        try:
            
            console.info("Destroying EEG outlet...");
            
            if(stream_outlet is not None):
                
                # Send shutdown signal to any consumers of this outlet
                #TODO: define this
                Data_Packager_shutdown_signal = np.empty(9);
                
                # Wait for consumers to disconnect
                #TODO: consider setting a max timeout for this
                while(stream_outlet.have_consumers()):    
                    stream_outlet.push_sample(Data_Packager_shutdown_signal);         
                    # Wait for 100ms, then try again (instead of blocking)
                    # (this brief pause between calls allows for interrupts)
                    time.sleep(0.1);
                
                # Completely delete the stimuli outlet
                stream_outlet.__del__();
                
            else:
                
                console.warning("'stream_outlet' is not defined.");
                
        except NameError:
            
            console.warning("'stream_outlet' is not declared.");
            
        except Exception as e:
            
            raise e;
                         
        # End of Shutdown_Cyton_Data_Packager
        console.critical("Cyton data packager shut down.");

        #TODO: remove
        try:
            
            while(True):
                time.sleep(.1);
                
        except KeyboardInterrupt:
            
            pass;
            
        pass;
    
    def Run():
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
        # A chunk of several data samples waiting to be sent
        chunk_to_send = np.zeros([1,9]);
        
        # The time at which the last chunk was broadcasted over LSL
        # Initialized to start time start chunk timer from the start
        last_chunk_broadcast_time = time.time();
        
        # Minimum delay, in seconds, between consecutive chunk broadcasts
        chunk_broadcast_delay = 0.25;
        
        def send_chunk():
            
            nonlocal chunk_to_send;
            nonlocal last_chunk_broadcast_time;
            
            out = np.array(np.where(chunk_to_send[1:,8]>0));
            out = out+1;
            print(np.shape(out))
            print(np.shape(out)[1])
            if(np.shape(out)[1]>0):
                print(chunk_to_send[out,8]);
            
            # Broadcast chunk over LSL outlet
            stream_outlet.push_chunk(chunk_to_send[1:,:].tolist());
            print("Chunk sent~~~~~~~~~~~~");
            
            # Update last chunk broadcast time for next chunk
            last_chunk_broadcast_time = time.time();
        
            # Reset chunk back to empty-state
            chunk_to_send = np.zeros([1,9])
    
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
        # The most recent EEG sample pulled from the Cyton
        current_sample_EEG = np.zeros([1,8]);
        
        # The most recent trigger sample pulled from the Cyton
        current_sample_triggers = np.zeros(2);
        
        # The previous trigger sample pulled from the cyton
        # This is used to detect trigger changes between samples
        last_sample_triggers = np.zeros(2);
        
        # The number of samples gathered since the last trigger flip
        n_samples_since_last_trial = 0;
        
        # Maximum amount of sample to wait for trigger to charge/discharge
        # (Currently using half of the intended samples)
        #TODO : investigate if there is a better threshold to use
        trigger_delay_threshold = math.floor(sampling_rate*GUI_stimulus_time/2);
        
        # Index of the current flash trial
        trial_index = 1;
        
        waiting_for_consumer = True;    
        
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
            
            nonlocal waiting_for_consumer;
                
            # If there is currently a consumer
            if(stream_outlet.have_consumers()):
                
                # If this is the first consumer that has been found
                if(waiting_for_consumer):
                    print("Consumer joined.");
                    
                # Unblock data storage
                waiting_for_consumer = False;
                
            # Check if there are currently no consumers, but there previously was
            elif(not waiting_for_consumer):
                
                # Init shutdown            
                console.warning("Processor disconnected unexpectedly.");
                raise Exception("Consumer disconnected");
                            
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
                
                    # The previous flip was marked wrong; fix it
                    bad_stamp_ind = np.where(chunk_to_send[:,8]==trial_index-1);
                    chunk_to_send[bad_stamp_ind,8] *= -1;
                    print("Went back and fixed previous trial.");
                    
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
    
            # If waiting for consumer
            if(waiting_for_consumer):
                
                # Block chunk building
                
                # Reset trial index
                trial_index = 1;
                
                # Reset sample count
                n_samples_since_last_trial = 0;
                
                # A chunk of several data samples waiting to be sent
                chunk_to_send = np.zeros([1,9]);
                
                time.sleep(0.1);
                
                # The time at which the last chunk was broadcasted over LSL
                # Initialized to start time start chunk timer from the start
                last_chunk_broadcast_time = time.time();
                
                return;            
                
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
        # Start the board stream with callback
        cyton.start_stream(package_sample);
            
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
    cyton = None;
    stream_outlet = None;
    
    try:
        
        # Connect to bluetooth dongle on COM port 3
        console.info("Connecting to Cyton...");
        cyton = OpenBCICyton(port='COM3');
                  
        # Configure the board into digital read mode
        console.info("Configuring Cyton...");
        cyton.write_command('/3');
        console.info("Cyton ready.");
        
        # Initialize LSL stream
        console.info("Opening EEG outlet...");
        stream_info = StreamInfo("Packaged_EEG", "Packaged_EEG", 9, 250, "float32", "Cyton_Data_Packager");
        stream_outlet = StreamOutlet(stream_info);
        console.info("EEG outlet opened.");
    
        Run();
        
    except KeyboardInterrupt:
        
        console.warning("Keyboard interrupt detected");
        Shutdown_Cyton_Data_Packager();
    
    except Exception as e:
        
        Shutdown_Cyton_Data_Packager();    
        raise e;
    
    else:
        
        Shutdown_Cyton_Data_Packager();
        
    finally:
        
        import sys;
        sys.exit(0);    
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#




#TODO: call this from a file that independently starts all 3 processes          
Start();  



















