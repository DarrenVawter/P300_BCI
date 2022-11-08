# [Name of the Team/Project?]

[Introduction and overview of capabilities.]

## Technical Description
[Has to include the pipeline picture and maybe description of it]

[!!! needs to show technological choices and should reflect your understanding of the project and underlying science]

### Innovative approaches
[part of the rubric]

## Reproducibility

### Requirements

#### BCI system hardware
  * EEG
    * OpenBCI 8-channel wet-electrode cap
      * OpenBCI electrode cap gel w/ applicator syringe
  * Sampling Hardware
    * OpenBCI Cyton biosensing board
      * Power Source (4 x AA batteries)
    * OpenBCI Bluetooth dongle
  * Triggering Hardware
    * UM232R FTDI
      * USB-A (M) to USB-B (M)
    * 2 x CNY17F-4 
    * 2 x 47 kOhm (+/- 1%)
    * 2 x 1 kOhm (+/- 1%)
    * 2 x 1 MOhm (+/- 1%)
    
  
#### Auxiliary hardware
  * Windows PC (w/ Python 3.10)
    * Test setup:
      * AMD FX-6300 CPU
      * Radeon RX-480 GPU
  * 2 x monitor (1080p)

### Step-by-step to reproduce the project
* Download source code
* Download Python dependencies
* Assemble external circuit 
  *[picture here]
* Connect OpenBCI EEG cap to Cyton board
  * Channels: 
    * White - REF
    * Black - GND
    * Gray (1) - O1
    * Purple (2) - O2
    * Blue (3) - P3
    * Green (4) - P4
    * Yellow (5) - PZ
    * Orange (6) - C3
    * Red (7) - C4
    * Brown (8) - CZ
 * Wear EEG cap
   * Ensure cap orientation matches the following image: 
    https://raw.githubusercontent.com/openbci-archive/Docs/master/assets/images/electrode%20cap%20nodes_1.png
   * Using applicator syringe, apply gel to REF, GND, O1, O2, P3, P4, PZ, C3, C4, and CZ.
     * If unfamiliar with gel application, download OpenBCI GUI and stream data. Change vertical scale to automatic and apply gel slowly until each channel's scale is minimized.
 * Launch program (TODO: package this with a launch script)
   * First, launch Cyton_Data_Packager.py in its own kernel.
   * Second, launch BCI_Controller.py in its own kernel.
     * (currently, the mouse must be hovering over monitor 1 when this module is launched to function correctly)
   * Last, launch P300_Processor.py in its own kernel.
 * The program will start in overlay mode.
 * If the program is launched without pre-trained data, it will automatically enter "overlay calibration" mode. 
   * Calibration mode takes ~5-6 minutes. 
 * Once calibrated, the program will continuously attempt to make classifications of which cell the user is looking at.
 * The first time the user opens up keyboard mode (i.e. without pre-trained data) it will enter "keyboard calibration" mode.
 * Once calibrated, the program will continuously attempt to make classifications of which key the user is looking at.
 * Upon closing the GUI, all modules will close.
 

## Discussion

*Limitations:*

*
*
*

*Future improvements:*

*
*
*
