# CruX @ UCLA P300 BCI 

## Presentation and Demonstrations

* NeuroTechX Student Club Competition Presentation (including short demos of keyboard and overlay interfaces)
  * https://drive.google.com/file/d/1K0_7yf0yF9sV8O8vak3vLr-YgmjuWkfi/view?usp=share_link
* Keyboard interface demonstration (w/ intro)
  * https://drive.google.com/file/d/1oyYfFMhPj219BxCBmprONrwqLPeU8vo1/view?usp=share_link
* Overlay interface demonstration (no intro)
  * https://drive.google.com/file/d/1g3a3haj1WufKYOtaX_5pQ6jYdXAm_rGc/view?usp=share_link
  
## Technical Description

This BCI allows a user wearing an EEG to visually control a keyboard and mouse in a normal computer environment.

[!!! needs to show technological choices and should reflect your understanding of the project and underlying science]

### Data pipeline

[Has to include the *current* pipeline picture and maybe description of it]
[Also include software pipeline]

![Data pipeline](/Images/P300_Data_Flow_V3_Outdated.png)

### User experience

-TODO

### Innovative approaches

[Talk about iterative cross correlation, DRBG algo, and mouse click method]

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
 * Run Launch_BCI.py
   * (Currently, when launching, the mouse must be hovering over monitor 2 to open the overlay on the correct screen.)
   * TODO: Attach Launch_BCI.py to a startup script so the program launches as soon as the PC boots
 * The program will start in overlay mode.
 * If the program is launched without pre-trained data, it will automatically enter "overlay calibration" mode. 
   * Calibration mode takes ~5-6 minutes. 
 * Once calibrated, the program will continuously attempt to make classifications of which cell the user is looking at.
 * The first time the user opens up keyboard mode (i.e. without pre-trained data) it will enter "keyboard calibration" mode.
 * Once calibrated, the program will continuously attempt to make classifications of which key the user is looking at.
 * Upon closing the GUI, all modules will close.
 

## Discussion

[Flesh this out]

*Notable Challenges:*

* Using pre-existing solutions may be suboptimal
  * Novel experimentation
* Asynchronous hardware and software streams
  * Programmatically controlling external hardware to synchronize EEG data stream with BCI GUI
    * Developing Deterministic Random Bit Generator synchronization algorithm
* Misleading data
  * Running more trials with varying settings/hyperparameters to validate data
* Need of a live participant to run EEG trials
  * Simulate or stream pre-recorded data

*Limitations:*

* Requires eye control over the span of 1 or 2 monitor(s)
* User has to wear EEG headset 
  * Current version uses wet EEG 
  * Price: $1,700 setup
* Inherent tradeoff between speed and accuracy
* Tradeoff between fatigue and speed/accuracy


*Future improvements:*

* Passive use detection
* User-specific optimization of classifier hyperparameters
* Real-time update of the P300 signal
* Researching and designing optimal user interface

