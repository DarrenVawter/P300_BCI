# CruX @ UCLA P300 BCI 

This P300-based BCI allows a user wearing an EEG to visually control a keyboard and mouse in a normal computer environment.

## Presentation and Demonstrations

* NeuroTechX Student Club Competition Presentation (including short demos of keyboard and overlay interfaces)
  * https://drive.google.com/file/d/1K0_7yf0yF9sV8O8vak3vLr-YgmjuWkfi/view?usp=share_link
* Keyboard interface demonstration using NLP and word suggestions (w/ intro)
  * https://drive.google.com/file/d/1oyYfFMhPj219BxCBmprONrwqLPeU8vo1/view?usp=share_link
* Overlay interface demonstration (no intro)
  * https://drive.google.com/file/d/1g3a3haj1WufKYOtaX_5pQ6jYdXAm_rGc/view?usp=share_link
  
## Technical Description

### Methods

#### P300

The P300 (or P3) response is an event related electrical potential measurable on the scalp, primarily detectable near the occipital, parietal, and central regions. The 'event' which triggers a P300 can be any unexpected or 'oddball' stimulus. The 'P' in P300 refers to the fact that inflection in potential is positive. The '300' in P300 refers to the fact that the P300 response is usually detectable ~300ms after onset of the oddball stimulus. What constititutes an oddball stimulus to the brain is non-trivial to parameterize. Examples include listening to a constant tone which is interrupted with sporadic beeps, staring at a red street light when it suddenly turns green, or looking at a static image which is sporadically 'flashed.' In this context, 'flashed' can mean having the brightness of the static image increase or having a different color or image abruptly appear over the original static image for a short period of time (10ms-30ms). For the remainder of this document, 'flash' will refer to abruptly and briefly covering up the static image with a different image.

![P300 Response Example](/Images/P300_Response_Sample.png) ![Target vs Non-target Response Example](/Images/Target_vs_Non_Target_Response.PNG)


#### Paradigm

In order to leverage the P300 response, a paradigm must be designed that can differentiate information by detecting responses to unexpected stimuli. The first, and now somewhat canonical, paradigm developed for this puprose was by Farwell and Donchin. It features N columns and N rows of characters. Each group of characters in a single row or column then his its brightness intensified. Ostensibly then, if the user is looking at that row/column, the intensification would generate a measurable P300 response. Since the detection of a P300 response is highly probabilistic due to both signal variance and the low SNR of EEG, this is performed repeatedly and the most probable row and most probable column are tracked until some threshold criteria is met. At that point, the character at the intersection of the most probable row and column is classified as the desired character.

![Farwell and Donchin Paradigm](/Images/Farwell_and_Donchin_Paradigm.png)

Through literature review and evaluation, three drawbacks that the team identified with this format were:
* Most individuals are not accustomed to typing on a keyboard in alpha-numeric order, which increases character aquisition time.
	* Although users typically improve rapidly if using this format, the team hypothesized that it would be unlikely for individuals accustomed to a lifetime of QWERTY format keyboards to match their QWERTY character aquisition time on an alphanumeric keyboard.
	* For users unaccustomed to QWERTY, either format would require training to improve character aquisition time regardless.
* Certain rows/columns are far more likely to be used for a given context.
	* For typing out an English novel, the row A-B-C-D-E-F contains 2 vowels and 4 frequently used consonants while the row 5-6-7-8-9-_ contains no letters at all, thus, the first row would contain the desired character far more frequently.
	* As a result, either the frequency of flashing of each row/column should be conditioned on the probability that it contains the desired character or the thresholding criteria must be adjusted to account for the unequal frequency of occurence of each row. This task is highly context-dependendant and non-trivial.
	* To circumvent this problem, the characters can instead be grouped randomly or based upon their current probabilities of being the desired character.
		* Context can still be used alongside this method in order to dynamically adjust character classification thresholds (i.e. make more likely characters 'easier' to click and less likely characters 'harder' to click).
* Simply intensifying the brightness of the character is not the most optimal elicitation of a characterizable response signal.
	* It has been shown that the facial detection response interferes constructively with the P300 response.
		* Thus, the response can be made more detectable and its SNR can be increased by instead flashing images of faces over the characters.
		* A 'face' can be an actual image of a human face, a drawn caricature of a face, or even 2 dots and a line oriented to look face-like.
	* The N100 and N200 responses are both responses to any abrupt changes in visual or auditory input.
		* (e.g. If an individual focused on a metronome, then, with each beat, there would be an abrupt auditory change, eliciting some N100 and N200 response. There would not be an oddball change, as the individual would be expecting the beat, thus, we would not expect a significant P300 response unless, for example, the beat sporadically changed pitch for a moment).
		* The N100 and N200 responses have been shown to be, to some extent, proportional to the perceived intensity of the abrupt change.
			* Thus, it is beneficial to attempt to maximize the change in stimulus between the static image and flash (e.g. if the static character is dark/dull/gray, the abrupt image covering it should be bright/vivid/colorful).
			
A variety of P300 paradigms exist in practice and in the literature, some of which are hybridized (auditory + visual P300, P300 + SSVEP, P300 + other signal), and an optimal paradigm is still an active area of research. Following are just a few example paradigms:

* Visual P300 w/ randomized character groups and flashing smiley faces of varying color

![Smiley Paradigm](/Images/P300_Smiley_Paradigm.png)

* Audiovisual P300 w/ group zooming (group classification followed by individual character classification)

![Audiovisual Paradigm](/Images/Audiovisual_P300_Paradigm.png)

* Negative expectation visual P300 response (expected response is a change, oddball response is a sudden lack of change)

![Inverted Oddball Paradigm](/Images/P300_Inverted_Oddball_Paradigm.png)

Per the above information and through literature review, the team designed the following two paradigms

![Keyboard Interface Sample](/Images/Keyboard_Interface.jpg)

* Paradigm for the keyboard interface (See video in Presentation and Demonstrations.)
	* Keyboard layout: QWERTY (plus some special characters and a row for word suggestions)
		* Pro(s)
			* Faster character aquisition time than alpha-numeric.
			* Easier to use for most users / less learning curve.
		* Con(s)
			* Rectangular: may force a sub-optimal distance between characters in order to fit to a more square screen
			* *May* not be the most optimal layout (dvorak, colemak, or other may be superior for average character aquisition time, despite the learning curve)
	* Flash image: League of Legends character faces
		* Pro(s)
			* Varying between one of several faces: more 'unexpected' oddball should elicit a stronger P300 response
			* Character faces are generally bright and colorful: perception of a more abrupt flash should elicit stronger N100 and N200 responses
				* Resulting note: The team did find a substantial N200 response, but the N100 response was generally non-characterizable.
			* The member(s) of the team using the BCI were all familiar with the characters and instinctively recognized the images as faces.
		* Con(s)
			* Unclear if a user unfamiliar with the characters would recognize the images as 'faces.'
				* Solution: find other faces to use. (unimplemented/future)
			* Probably best not to use copyrighted images in a full-release version.
				* Solution: find other faces to use. (unimplemented/future)
	* Flash image border: randomized color 
		* Pro(s)
			* Flashing a randomized color with the image should make the oddball more 'unexpected'
		* Con(s)
			* A random color means the border can blend with the character image or blend between the character and black background, lessening the perceived intensity of the abrupt change.
				* This can be alleviated by using a pseudo-random image border based upon the foreground & background color. (unimplemented/future)
	* Flash groups: flash the most probable character + N least probable characters, then remove those characters and repeat with the remaining characters until all have been flashed, then restart
		Pro(s)
			* Ensures that discriminatory information is gained between the most probable characters.
				* e.g. if 'A' is calculated to be a 50% chance of being the desired character and 'B' is calculated to be a 50% chance of being the desired character and all other characters are calculated to be 0%, then no information is gained if 'A' and 'B' are randomly flashed together; guaranteeing they are separate guarantees discriminatory information gain.
			* This method still flashes all characters with the same frequency, ensuring no bias is applied to any given character.
		Con(s)
			* Greedy algorithm: there may be a more optimal method of maximizing discriminatory information gained. (unimplemented/future)
	* Dynamically thresholding with NLP (i.e. decrease the threshold of more-likely characters to make them easier to click and increase the threshold of less-likely characters to make them harder to click) (currently implemented in legacy code only)
		* Pro(s)
			* When in the correct context, can substantially increase information transfer rate.
		* Con(s)
			* When in the incorrect context, (e.g. using English NLP while typing a username and password), can substantially decrease information transfer rate.
				* Currently alleviated by adding an NLP toggle to the keyboard to disable NLP when typing natural English sentences (tradeoff con: adding an extra key slightly increases error rate)
	* Future
		* 'Highlight' the character which is currently most probable or closest to its threshold value. If the user triggers a 'select,' instantly select the highlighted character regardless of whether or not it has exceeded its threshold.
			* This should substantially increase information transfer rate, but requires a successful hybridization scheme (i.e. a non-P300 signal must be utilized in order to detect the 'select' trigger).
			* Easy solutions would be to have the user blink/close their eyes/clench their jaw if they wanted to select the highlighted character, as these are all detectable by EEG.
				* The team felt this went against the spirit of the NTX competition, and also noted that it would not assist individuals with sufficient paralysis to make these tasks non-trivial.
			* Another proposal is to change the intensity of the highlighted character sinusoidally and use SSVEP analysis to detect if the user is looking at it.
				* This allows the keyboard to maintain a high number of keys, as only the proposed key is being sinusoidally intensified. (The number of discriminable options viable for use is a common challenge to SSVEP paradigms.)
				* This also requires nothing additional of the user, as they are already looking at the key.
			* Another proposal is to use a focus-based auditory stimulus or even an oddball auditory stimulus to have the user actively trigger the 'select.'
				* Such a paradigm may be more challenging or require more focus for the user to use the BCI, but it is still a potential alternative to the previous proposal in order to attempt to increase the information transfer rate.
		* Optimize the UI (character spacing, character sizing, character coloring, flash frequency, flash duration, etc.)
			* Each of these can only be optimized experimentally.
				* The current UI was generated after two days of testing and based primarily on user feedback.
				* Each UI variable must be individually varied, and the results analyzed, in order to determine the optimal UI.
				* (A theoretically optimal flash frequency can be determined analytically based upon the signature P300 response, but that would necessarily assume that the signature was independent of the flash frequency, which the team did not observe to be true.)

![Overlay Interface Sample](/Images/Overlay_Interface.jpg)

* Paradigm for the overlay (mouse/monitor) interface (See video in Presentation and Demonstrations.)
	* The team found no general-purpose mouse use interface. This lack of pre-existing literature means many of the design decisions for this interface are unjustified or based primarily on intuition/hypothesis.
		* The pre-existing paradigms the team found for mouse click interfaces were:
			* Application specific/highly tokenized
				* Only allowed for the user to click tokenized positions, which is not helpful when there are multiple applications running, a very high number of clickable tokens, or, most importantly, if the user wants to use an application which is not tokenizable by the BCI.
				* Notably, and fairly, application specific mouse clicking is optimal when possible
					* In the example of the chess game, it is optimal to only flash the moveable pieces, then where the piece can move (as well as an 'undo' button) instead of flashing the whole screen.
					* By analogy, what the team's BCI lacks in brevity, it makes up for with completeness.
			* Move mouse by selection
				* Offer the user up, down, left, right, up-right, up-left, down-right, down-left, and various click options.
				* The mouse jumps to the nearest token in the direction selected, the user can then register the appropriate click.
				* This suffers from all of the same problems as the previous method, but is generally worse given the slow rate token traversal (this method is akin to always tabbing through your web browser to navigate).
				* This method has the *ability* to be generalized by instead moving the mouse some amount, instead of snapping to a token. The team hypothesized that this method would be unacceptably slow.
	* The paradigm is fundamentally the same as the keyboard interface, with the following changes:
		* Layout:
			* Monitor A is live-mirrored onto a portion (the majority) of monitor B, the mouse always remains in the center of the mirror.
			* Extra options (left/right click, tab, enter, open keyboard, zoom out, etc.) are available on the edges of the screen.
			* The mirror on monitor B is overlaid with a grid to cut the screen up into cells.
			* The cells are then flashed using the same flash images/flash borders/grouping methods as described in the keyboard interface paradigm.
			* If a side-bar option (click, open keyboard, etc.) is selected, then the corresponding action is triggered as expected. If a tile from the mirror section is selected, the mirror zooms into that portion of the screen in order to effectively move the mouse.
			* Pro(s)
				* With a grid of 10x10 (the only currently tested schem) almost any position on the screen can be clicked within 2-4 interactions (1-3 zooms, 1 click).
			* Con(s)
				* Live-mirroring the screen elicits unintentional P300 responses (i.e. the screen may have movement on it).
					* This may be alleviated by presenting a static mirror and only updating it every N seconds, to minimize/remove unwanted P300 signals.
						* This may have unintended consequences.
						* This would necessitate that the user could look over both screens for a live view (i.e. harder to use for people with limited visual range).
				* By overlaying a thin grid, there is next-to-zero space between cells, meaning neighboring cells are highly probable to elicit undesired P300.
					* This *may* be alleviated/lessened with UI improvements (cell shading, thicker borders, border contrast coloring, etc.)
				* This layout is not conducive to click-and-drag.
	* Future
		* While the BCI excels in generality, it can be highly optimized in common application-specific instances.
			* Tokenize where possible.
				* (e.g. when playing chess, only flash the moveable pieces, then where they can move to, and a couple of special sidebar options.)
			* Special sidebar options.
				* (e.g. when Google Chrome is the focused window, have sidebar options for refresh, new tab, back, etc.)
		* Optimize the UI (same comments as keyboard interface).
		* Highlight the currently most probable cell (same comments as keyboard interface).
		
		
#### Classification

### Data Collection

- trigger synchronization
  - external circuit
  - DRBG algorithm
  
### Data Processing

- core python components
  - Cyton_Data_Packager.py
  - P300_Processor.py
  - BCI_Controller.py


### Data Pipeline

![Data pipeline](/Images/P300_BCI_Data_Pipeline.png)



This BCI allows a user wearing an EEG to visually control a keyboard and mouse in a normal computer environment.

The data listed in the report introduce and justify the core of the logic behind our BCI’s classification method. Not included (for the sake of length), however, are several methods for classification that were implemented, tested, and shown to be ineffective or not as effective as the chosen method. Also not included are details on how GPT-NEO was used as a causal language model to produce word suggestions, how character n-grams were used to produce dynamic character thresholds, how probabilities were dynamically weighted to reduce type-I errors, how the signal characteristics were updated while making live classifications, or technical details such as trigger and synchronization handling. Lastly, not included is the reasoning behind or explanation why iterative cross correlation reduces inter-trial interference, inter-stimulus interference, and training time.

The first figure in the report illustrates the difference between the average non-target response and target (P300) response over N≈15,000 total trials, (about 30 minutes worth of data). Given a high enough number of sample trials, ostensibly, the orange curve would be a flat line at 0uV, and the blue curve would exhibit an ideal N200 deflection and P300 inflection, followed by a refractory period before returning to a flat line. Because of interference from peripheral stimuli, we instead see a low-amplitude steady-state visually evoked potential at the flash frequency, ≈8.33Hz in this instance. This specific frequency can then be removed with a notch filter to improve signal discrimination. Noting that these two average responses are clearly distinct, the challenge, then, is demodulating individual trial signals and determining the likelihood that the trial was a target response or non-target response.

The second figure, (shown for N≈8,000 total trials), shows that the calculated central cross-correlation coefficients can be treated as random variables sampled from target and non-target distributions, both of which are highly normal. The left graph shows the target and non-target histograms for the central correlation coefficient of the cross correlation between each trial and the average target response. The right graph shows the target and non-target histograms for the central correlation coefficient of the cross correlation between the previously mentioned cross correlation for each trial and the average first cross correlation for target trials. Notably, the distributions become narrower and more normal as further iterations are performed (as a result of the central limit theorem). Each distribution set has a net resolution space (percent area under the net PDF which is not intersected by both distributions) of ≈75%. Thus, it is clear that either can be used as a valid demodulator. It is unclear from these graphs alone, however, whether or not the discriminatory information is independent between these two distribution sets (i.e. if any information is actually gained by performing more than one iteration of cross correlation).

The third figure shows that the probability estimates from the first and second cross correlations are non-linear, particularly in the region of p1 ≈ [50%, 90%], indicating that, so long as each of p1 and p2 are calculated from valid normally sampled distributions, information is gained. This analysis can be performed iteratively, and, so long as the new iteration’s prediction, pn, is calculated from a valid normally sampled distribution and the curve deviates from the n-1 dimensional line with a slope of 1 in all dimensions more than the previous curve, pn can be said to add new information to the trial estimate. The most notable drawback, particularly during live analysis, of performing more correlation iterations is the increased processing time. Also, diminishing returns seem to appear after only 4 or 5 iterations, (i.e. the net information gain appears to be logarithmic w.r.t. the number of iterations performed).

The fourth figure shows the bivariate histograms (drawn on the same plane to illustrate the separation of means), which can be used to generate bivariate normal statistics to estimate a probability that a given trial is a target trial given some 1st and 2nd correlation coefficients. We say that using n iterations of cross correlation to generate an estimate is using nth degree correlation. Thus, this is using 2nd degree correlation. Also verifying that new information is gained, the average magnitude of the ‘distance’ between two points from the two different distributions is greater in this 2-dimensional frame than in the 1 dimensional frame on the previous page. Much like parsing the light apart from two stars near to one another when viewed through a telescope, this increase in separation yields a greater ability to discriminate which sample came from which distribution.

The fifth figure validates that the analytically generated key probabilities, shown in blue, closely match the actual percentage of positive trials at that generated probability, shown in orange. This confirms the appropriateness of performing these statistical analyses on the correlation results to generate key probabilities. By then treating each of the stimuli as independent trials and compounding samples over time, the target key probability will eventually converge to 100% and all other keys to 0%. The optimization problem then becomes choosing key decision thresholds (displayed probabilities generated using 3rd degree correlation and corresponding trivariate normal distributions).

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

