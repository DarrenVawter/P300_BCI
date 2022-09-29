# -*- coding: utf-8 -*-
"""

@author: Darren Vawter
"""

import ftd2xx as ftd; # Communicating the the UM232R FTDI chip for triggering

class FTDI_Handler:
    
    def __init__(self):
        
        # Attempt to grab the FTDI device
        self.device = ftd.open(0);
        print("[FTDI_Handler.py]:",self.device.getDeviceInfo());

        # Bit mask for pins D0, D1, & D2
        OP = 0x07;           
        
        # Set pins as output & async bitbang mode (1)
        self.device.setBitMode(OP, 1);  
    
        # Init state: 0 0 1
        self.state = 0x01
        self.device.write(str(self.state));      
        
        # End of constructor
        pass;
        
    """
    
    Send_Sync()
    
        This function flips the flash triggers and the sync trigger so that
        the Cyton may detect a sync trial.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
    
        --> Invert all 3 triggers
                        
            --> 001 inverts to 110
            
            --> 011 inverts to 100
            
            --> 100 inverts to 011
            
            --> 110 inverts to 001
        
        --> Write the new state to the device
        
    """
    def Send_Sync(self):
        
        # Invert all 3 triggers       
        
        # 001 --> 110
        if (self.state == 0x01):
            self.state = 0x06;
            
        # 011 --> 100
        elif (self.state == 0x03):
            self.state = 0x04;
            
        # 100 --> 011
        elif (self.state == 0x04):
            self.state = 0x03;
            
        # 110 --> 001
        elif (self.state == 0x06):
            self.state = 0x01;
        
        # Write the new state to the device
        self.device.write(str(self.state));
        
        # End of Send_Sync()
        pass;
        
        
    """
    
    Send_Non_Sync()
    
        This function flips the flash triggers and the sync trigger so that
        the Cyton may detect a sync trial.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
    
        --> Invert the first and third triggers  
                        
            --> 001 inverts to 100
            
            --> 011 inverts to 110
            
            --> 100 inverts to 001
            
            --> 110 inverts to 011
        
        --> Write the new state to the device
        
    """
    def Send_Non_Sync(self):
        
        # Invert the first and third triggers    
                            
        # 001 --> 100
        if (self.state == 0x01):
            self.state = 0x04;
            
        # 011 --> 110
        elif (self.state == 0x03):
            self.state = 0x06
            
        # 100 --> 001
        elif (self.state == 0x04):
            self.state = 0x01
            
        # 110 --> 011
        elif (self.state == 0x06):
            self.state = 0x03
        
        # Write the new state to the device
        self.device.write(str(self.state));
        
        # End of Send_Non_Sync()
        pass;
        
    """
    
    Release()
    
        This function releases the FTDI device so it can be opened elsewhere.
    
        arguments:
            [none]
        returns:
            [none]
        exceptions:
            [none]
    
        --> Release the FTDI device's port
        
    """
    def Release(self):
        
        # Release the FTDI device's port
        self.device.close();
        
        # End of Release()
        pass;
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        