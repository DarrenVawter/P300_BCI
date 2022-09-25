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
from BCI_Constants import N_TILES, N_KEYS;

#############################
#   Processor Entry point   #
#############################
def Run(processor_outlet):
    
    # Caclulate number of outputs
    N_OUTPUTS = max(N_TILES,N_KEYS);
    
    # Grab an inlet to the BCI stream
    inlet_stream = resolve_stream('type', 'P300_Stimuli');
    BCI_inlet = StreamInlet(inlet_stream[0]);
    
    # Simulate a fake classification
    import time;
    time.sleep(10);
        
    fake_classification = np.zeros(N_OUTPUTS).astype(int);
    fake_classification[-1] = -12;
    processor_outlet.push_sample(fake_classification);




#TODO: remove this
"""
from pylsl import StreamInfo, StreamOutlet;
# Initialize the processor outlet
info = StreamInfo("P300_Processor", "P300_Processor", max(N_TILES,N_KEYS), 125, "int16","P300_Processor");
processor_outlet = StreamOutlet(info);

Run(processor_outlet)

processor_outlet.__del__();
"""
    














