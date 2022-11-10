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

The data listed in the report introduce and justify the core of the logic behind our BCI’s classification method. Not included (for the sake of length), however, are several methods for classification that were implemented, tested, and shown to be ineffective or not as effective as the chosen method. Also not included are details on how GPT-NEO was used as a causal language model to produce word suggestions, how character n-grams were used to produce dynamic character thresholds, how probabilities were dynamically weighted to reduce type-I errors, how the signal characteristics were updated while making live classifications, or technical details such as trigger and synchronization handling. Lastly, not included is the reasoning behind or explanation why iterative cross correlation reduces inter-trial interference, inter-stimulus interference, and training time.

The first figure in the report illustrates the difference between the average non-target response and target (P300) response over N≈15,000 total trials, (about 30 minutes worth of data). Given a high enough number of sample trials, ostensibly, the orange curve would be a flat line at 0uV, and the blue curve would exhibit an ideal N200 deflection and P300 inflection, followed by a refractory period before returning to a flat line. Because of interference from peripheral stimuli, we instead see a low-amplitude steady-state visually evoked potential at the flash frequency, ≈8.33Hz in this instance. This specific frequency can then be removed with a notch filter to improve signal discrimination. Noting that these two average responses are clearly distinct, the challenge, then, is demodulating individual trial signals and determining the likelihood that the trial was a target response or non-target response.

The second figure, (shown for N≈8,000 total trials), shows that the calculated central cross-correlation coefficients can be treated as random variables sampled from target and non-target distributions, both of which are highly normal. The left graph shows the target and non-target histograms for the central correlation coefficient of the cross correlation between each trial and the average target response. The right graph shows the target and non-target histograms for the central correlation coefficient of the cross correlation between the previously mentioned cross correlation for each trial and the average first cross correlation for target trials. Notably, the distributions become narrower and more normal as further iterations are performed (as a result of the central limit theorem). Each distribution set has a net resolution space (percent area under the net PDF which is not intersected by both distributions) of ≈75%. Thus, it is clear that either can be used as a valid demodulator. It is unclear from these graphs alone, however, whether or not the discriminatory information is independent between these two distribution sets (i.e. if any information is actually gained by performing more than one iteration of cross correlation).

The third figure shows that the probability estimates from the first and second cross correlations are non-linear, particularly in the region of p1 ≈ [50%, 90%], indicating that, so long as each of p1 and p2 are calculated from valid normally sampled distributions, information is gained. This analysis can be performed iteratively, and, so long as the new iteration’s prediction, pn, is calculated from a valid normally sampled distribution and the curve deviates from the n-1 dimensional line with a slope of 1 in all dimensions more than the previous curve, pn can be said to add new information to the trial estimate. The most notable drawback, particularly during live analysis, of performing more correlation iterations is the increased processing time. Also, diminishing returns seem to appear after only 4 or 5 iterations, (i.e. the net information gain appears to be logarithmic w.r.t. the number of iterations performed).

The fourth figure shows the bivariate histograms (drawn on the same plane to illustrate the separation of means), which can be used to generate bivariate normal statistics to estimate a probability that a given trial is a target trial given some 1st and 2nd correlation coefficients. We say that using n iterations of cross correlation to generate an estimate is using nth degree correlation. Thus, this is using 2nd degree correlation. Also verifying that new information is gained, the average magnitude of the ‘distance’ between two points from the two different distributions is greater in this 2-dimensional frame than in the 1 dimensional frame on the previous page. Much like parsing the light apart from two stars near to one another when viewed through a telescope, this increase in separation yields a greater ability to discriminate which sample came from which distribution.

The fifth figure validates that the analytically generated key probabilities, shown in blue, closely match the actual percentage of positive trials at that generated probability, shown in orange. This confirms the appropriateness of performing these statistical analyses on the correlation results to generate key probabilities. By then treating each of the stimuli as independent trials and compounding samples over time, the target key probability will eventually converge to 100% and all other keys to 0%. The optimization problem then becomes choosing key decision thresholds (displayed probabilities generated using 3rd degree correlation and corresponding trivariate normal distributions).

### Data pipeline

![Data pipeline](/Images/P300_BCI_Data_Pipeline.png)

### User experience

* User has to wear an EEG headset
* Current version uses wet EEG, which requires some time to set up since gel has to be injected into each electrode and also requires the user to wash their hair afterwards. However, the gel is water-based and can be removed with water only.
* User needs to be able to move their eyes over 1 to 2 monitors
* Using our BCI can get tiring after a while since focus is required at all times. However, if the user zones out and selects a wrong input, our platform allows them to go back either by  zooming out for the mouse or by pressing the backspace key for the keyboard.

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
* ![External Triggering Circuit](/Images/circuit.png)
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

*Notable Challenges:*

* Using pre-existing solutions may be suboptimal; we initially used methods that have been proven to work in the literature but this was a challenge we needed to address in order to conduct novel research and advance the field by doing better than the current state-of-the-art.
  * Solution: Novel experimentation, trying many methods that have never been tried before to detemrine which one yields the best performance.
* Asynchronous hardware and software streams; there was a lag between the hardware EEG data stream and the software BCI GUI. This was a big challenge since the issue was caused by the hardware EEG headset, so we were unable to troobleshoot it this problem by editing our software.
  * Solution: Programmatically controlling external hardware to synchronize EEG data stream with BCI GUI
    * Developing Deterministic Random Bit Generator (DRBG) synchronization algorithm
* Misleading data
  * Solution: Running more trials with varying settings/hyperparameters to validate data
* Need of a live participant to run EEG trials
  * Solution: Simulate or stream pre-recorded data

*Limitations:*

* Requires eye control over the span of 1 monitor to control the keyboard or 2 monitors to control the mouse
* User has to wear EEG headset 
  * Current version uses wet EEG, which requires gel injected into each electrode and requires subject to wash hair afterwards
  * Price: $1,700 setup
* Inherent tradeoff between speed and accuracy
* Tradeoff between fatigue and speed/accuracy


*Future improvements:*

* Passive use detection
* User-specific optimization of classifier hyperparameters
* Real-time update of the P300 signal
* Researching and designing optimal user interface

