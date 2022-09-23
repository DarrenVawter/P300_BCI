def Start_GUI(outlet):
    """
    
    This program displays a P300 GUI for trial performance. It also opens
    an LSL stream which streams (currently) 37 stimuli keys indicating
    whether or not a given key was chosen when a group stimulus was
    initiated (bool) as well as 1 target key which the trial user was
    instructed to focus on (0-36) and a local-clock timestamp, in seconds.
    
    The state of this code is highly disorganized and not appropriately
    commented in some areas. This commit is to ensure the group has some
    working-level copy of this program on the github repo.
    
    CruX UCLA Fall 2021
    Darren Vawter
    
    """
    
    
    
    """
    Major things to change/add (some of them...):
        -currently, stimuli are selected at random <-- change this to bucketing
            (each key has an X% chance of being displayed during each stimulation)
        -word prediction
            (offer words on the top row as alternatives to typing one character)
        -letter prediction
            (calculate PMF of next letter given previous letters)
            (use to aid stimuli selection)
        -choice offering (maybe?)
            (not for training phase?)
            (offer a potential selection to the user)
                (if user performs X, then accept offered selection)
                (e.g. X = close-eyes/move-eyes/clench/other)
        -create backspace (maybe)
            (to reduce error, allow user to X to erase their last selection)
            (e.g. X = stare-at-backspace/hold eyes closed/clench)
        -reconsider paradigm (much of this depends on the competition demands)
            (how long should each stimulus be presented)
            (how to stimulate? --> images/colors/hide vs show letter/random/etc.)
            (breaks between stimulus (y/n)? --> if yes, how long?)
            (character and key sizes)
            (for training: how long should each character be requested as focus)
            (should sound be incorporated?)
        -cleanup
            (reduce hardcoding)-->(there's a lot rn...)
            (review+add comments/explanations)
            (optimize some of the lazier portions of the code (might not need to))
    
    """
    
    #TODO: if not in training mode, send DRBG sync codes instead of target chars
    """
    import numpy as np
    np.random.seed(2);
    x = np.random.rand(1);
    print(x)
    x = np.random.rand(1);
    print(x);
    x = np.random.rand(1);
    print(x);
    x = np.random.rand(1);
    print(x);
    x = np.random.rand(1);
    print(x);
    sys.exit();
    """
    
    #TODO: remove these or put them in more appropriate places
    waiting_for_next_char = False;
    typed_text = "";
    last_entry_length = [0, 0, 0];
    suggested_words = [];
    
    # # of keys on the screen
    N_KEYBOARD_CHARS = 45;
    # # of max word suggestions
    N_WORD_KEYS = 5;
    # # of keys to flash with each stimulus
    N_KEYS_PER_FLASH = 7;
    # Duration of time to present each stimulus for
    FLASH_DURATION = 0.1;  
    # Duration of time between training chars (to allow user to find new char)
    TRAINING_PAUSE_DURATION = 1.69;
    # Duration of time to spend on a single training target
    TARGET_CHAR_DURATION = 10;
    # FPS to cap pygame to
    FRAMERATE_CAP = 250;
    # Key dimension
    KEY_WIDTH = 100;
    KEY_HEIGHT = 100;
    WORD_KEY_WIDTH = 300;
    
    import math;
    import time;
    import random;
    import numpy as np;
    import pygame;  # Displyaing screen and playing sounds
    from gtts import gTTS; # Generating text-to-speech (TTS)
    from io import BytesIO; # Converting TTS to playable audio
    import _thread as threading; # Playing TTS without halting main program
    from pylsl import StreamInlet, resolve_stream; # Communicating with processor
    
    # Attempt to grab the FTDI device
    import ftd2xx as ftd; # Communicating the the UM232R FTDI chip for triggering
    d = ftd.open(0);
    print(d.getDeviceInfo());
    OP = 0x07;           # Bit mask for output D0
    d.setBitMode(OP, 1);  # Set pin as output, and async bitbang mode
    
    state = 0x01
    d.write(str(state));      # Init state: 0 0 1
    
    # Initialize nlp model
    from P300_NLP import NLP_Model;
    NLP_model = NLP_Model();
    
    # Enumerate
    from enum import IntEnum;
    
    class Mode(IntEnum):
        MENU = 1
        TRAINING = 2
        CLASSIFYING = 3
        TRAINING_PAUSED = 4
        CLASSIFYING_PAUSED = 5
        
    class Processor_Flag(IntEnum):
        TRAINING_OVER = -1
        UPDATE_PROBABILITIES = -2
    
    # Generate and play text to speech
    def Generate_TTS(text):
        speech = BytesIO()
        tts = gTTS(text, lang='en')
        tts.write_to_fp(speech)
        pygame.mixer.music.load(speech, 'mp3')
        pygame.mixer.music.play()
        
    # Set initial value for all keys
    def Init_Keys():
    
        #TODO: replace this with loops so it's less hideous    
    
        # Row heights
        rs = 220
        r0 = 390
        r1 = 560
        r2 = 730
        r3 = 910
        
        # word suggestion row
        a = 100
        txt = font.render("-----", True, WHITE)
        txt_size = font.size("-----");        
        keys[40] = (txt,[a+350*0,rs],False,[a+350*0+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2])
        keys[41] = (txt,[a+350*1,rs],False,[a+350*1+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2])
        keys[42] = (txt,[a+350*2,rs],False,[a+350*2+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2])
        keys[43] = (txt,[a+350*3,rs],False,[a+350*3+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2])
        keys[44] = (txt,[a+350*4,rs],False,[a+350*4+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2])
        
        # row 0
        a = 100
        txt = font.render("1", True, WHITE)
        txt_size = font.size("1");        
        keys[27] = (txt,[a+170*0,r0],False,[a+170*0+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("2", True, WHITE)
        txt_size = font.size("2");        
        keys[28] = (txt,[a+170*1,r0],False,[a+170*1+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("3", True, WHITE)
        txt_size = font.size("3");        
        keys[29] = (txt,[a+170*2,r0],False,[a+170*2+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("4", True, WHITE)
        txt_size = font.size("4");        
        keys[30] = (txt,[a+170*3,r0],False,[a+170*3+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("5", True, WHITE)
        txt_size = font.size("5");        
        keys[31] = (txt,[a+170*4,r0],False,[a+170*4+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("6", True, WHITE)
        txt_size = font.size("6");        
        keys[32] = (txt,[a+170*5,r0],False,[a+170*5+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("7", True, WHITE)
        txt_size = font.size("7");        
        keys[33] = (txt,[a+170*6,r0],False,[a+170*6+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("8", True, WHITE)
        txt_size = font.size("8");        
        keys[34] = (txt,[a+170*7,r0],False,[a+170*7+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("9", True, WHITE)
        txt_size = font.size("9");        
        keys[35] = (txt,[a+170*8,r0],False,[a+170*8+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("0", True, WHITE)
        txt_size = font.size("0");        
        keys[36] = (txt,[a+170*9,r0],False,[a+170*9+(KEY_WIDTH-txt_size[0])/2,r0+5+(KEY_HEIGHT-txt_size[1])/2])
        #backspace key
        txt_size = [65,72];      
        keys[37] = (bkspc,[a+170*10,r0],False,[a+170*10+(KEY_WIDTH-txt_size[0])/2,r0+(KEY_HEIGHT-txt_size[1])/2])
    
        # row 1
        a = 100
        txt = font.render("Q", True, WHITE)
        txt_size = font.size("Q");        
        keys[0] = (txt,[a+170*0,r1],False,[a+170*0+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("W", True, WHITE)
        txt_size = font.size("W");        
        keys[1] = (txt,[a+170*1,r1],False,[a+170*1+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("E", True, WHITE)
        txt_size = font.size("E");        
        keys[2] = (txt,[a+170*2,r1],False,[a+170*2+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("R", True, WHITE)
        txt_size = font.size("R");        
        keys[3] = (txt,[a+170*3,r1],False,[a+170*3+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("T", True, WHITE)
        txt_size = font.size("T");        
        keys[4] = (txt,[a+170*4,r1],False,[a+170*4+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("Y", True, WHITE)
        txt_size = font.size("Y");        
        keys[5] = (txt,[a+170*5,r1],False,[a+170*5+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("U", True, WHITE)
        txt_size = font.size("U");        
        keys[6] = (txt,[a+170*6,r1],False,[a+170*6+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("I", True, WHITE)
        txt_size = font.size("I");        
        keys[7] = (txt,[a+170*7,r1],False,[a+170*7+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("O", True, WHITE)
        txt_size = font.size("O");        
        keys[8] = (txt,[a+170*8,r1],False,[a+170*8+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("P", True, WHITE)
        txt_size = font.size("P");        
        keys[9] = (txt,[a+170*9,r1],False,[a+170*9+(KEY_WIDTH-txt_size[0])/2,r1+5+(KEY_HEIGHT-txt_size[1])/2])
        
        # row 2
        a = 145
        txt = font.render("A", True, WHITE)
        txt_size = font.size("A");        
        keys[10] = (txt,[a+170*0,r2],False,[a+170*0+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("S", True, WHITE)
        txt_size = font.size("S");        
        keys[11] = (txt,[a+170*1,r2],False,[a+170*1+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("D", True, WHITE)
        txt_size = font.size("D");        
        keys[12] = (txt,[a+170*2,r2],False,[a+170*2+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("F", True, WHITE)
        txt_size = font.size("F");        
        keys[13] = (txt,[a+170*3,r2],False,[a+170*3+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("G", True, WHITE)
        txt_size = font.size("G");        
        keys[14] = (txt,[a+170*4,r2],False,[a+170*4+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("H", True, WHITE)
        txt_size = font.size("H");        
        keys[15] = (txt,[a+170*5,r2],False,[a+170*5+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("J", True, WHITE)
        txt_size = font.size("J");        
        keys[16] = (txt,[a+170*6,r2],False,[a+170*6+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("K", True, WHITE)
        txt_size = font.size("K");        
        keys[17] = (txt,[a+170*7,r2],False,[a+170*7+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("L", True, WHITE)
        txt_size = font.size("L");        
        keys[18] = (txt,[a+170*8,r2],False,[a+170*8+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        #the quick brown fox key
        f = pygame.font.SysFont('Calibri', 45, True, False)
        txt = f.render("FOX", True, WHITE)
        txt_size = f.size("FOX");   
        keys[38] = (txt,[100+170*10,r2],False,[100+170*10+(KEY_WIDTH-txt_size[0])/2,r2+5+(KEY_HEIGHT-txt_size[1])/2])
        
        # row 3
        a = 220
        txt = font.render("Z", True, WHITE)
        txt_size = font.size("Z");        
        keys[19] = (txt,[a+170*0,r3],False,[a+170*0+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("X", True, WHITE)
        txt_size = font.size("X");        
        keys[20] = (txt,[a+170*1,r3],False,[a+170*1+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("C", True, WHITE)
        txt_size = font.size("C");        
        keys[21] = (txt,[a+170*2,r3],False,[a+170*2+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("V", True, WHITE)
        txt_size = font.size("V");        
        keys[22] = (txt,[a+170*3,r3],False,[a+170*3+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("B", True, WHITE)
        txt_size = font.size("B");        
        keys[23] = (txt,[a+170*4,r3],False,[a+170*4+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("N", True, WHITE)
        txt_size = font.size("N");        
        keys[24] = (txt,[a+170*5,r3],False,[a+170*5+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("M", True, WHITE)
        txt_size = font.size("M");        
        keys[25] = (txt,[a+170*6,r3],False,[a+170*6+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        txt = font.render("[ ]", True, WHITE)
        txt_size = font.size("[ ]");        
        keys[26] = (txt,[a+170*7,r3],False,[a+170*7+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
        #the nlp toggle key
        f = pygame.font.SysFont('Calibri', 45, True, False)
        txt = f.render("NLP", True, WHITE)
        txt_size = f.size("NLP");   
        keys[39] = (txt,[100+170*10,r3],False,[100+170*10+(KEY_WIDTH-txt_size[0])/2,r3+5+(KEY_HEIGHT-txt_size[1])/2])
    
    
    flash_bucket = [None] * (N_KEYBOARD_CHARS-N_WORD_KEYS+len(suggested_words))
    for i in range(len(flash_bucket)):
        flash_bucket[i] = i
    
    # classification mode
    key_probs = random.sample(range(1, 100), N_KEYBOARD_CHARS);
    
    # training mode
    key_corrs = np.zeros([N_KEYBOARD_CHARS,N_KEYBOARD_CHARS]);
    key_timers = np.zeros([N_KEYBOARD_CHARS,1]);
    
    # Update dynamic keys
    def Update_Keys():   
        
        nonlocal flash_bucket;
        nonlocal key_probs;        
        
        # Init keys to false
        for i in range (len(keys)):
            keys[i] = (keys[i][0],keys[i][1],False,keys[i][3])
            
        # Set of 7* key codes to flash
        sel = [];
            
        # Randomize probs if in training mode since probs are not sent over
        if(mode == Mode.CLASSIFYING):
               
            # Pull minimally correlated key codes from the flash_bucket until 7 are in the set
            while(len(sel) < N_KEYS_PER_FLASH):
                
                # Check if flash_bucket is empty and refill if needed
                if(len(flash_bucket)==0):
                    flash_bucket = [None] * (N_KEYBOARD_CHARS-N_WORD_KEYS+len(suggested_words))
                    for i in range(len(flash_bucket)):
                        flash_bucket[i] = i
                        
                # Check if sel has grabbed at least 1 char
                if(len(sel)>=1):
                    # Grab the LEAST probable key from the bucket as the next code                
                    min_p_key_code = -1;
                    min_p = 999;
                    for code in flash_bucket:
                        if(key_probs[code] < min_p):
                            min_p = key_probs[code];
                            min_p_key_code = code;
                    sel.append(min_p_key_code);
                    flash_bucket.remove(min_p_key_code);     
                else:
                    # Get the MOST probable key from the bucket as the first code
                    max_p_key_code = -1;
                    max_p = -1;
                    for code in flash_bucket:
                        if(key_probs[code] > max_p):
                            max_p = key_probs[code];
                            max_p_key_code = code;
                    sel.append(max_p_key_code);
                    flash_bucket.remove(max_p_key_code);
               
            # Set those 7 key codes to true so they flash for this round
            for c in sel:
                keys[c] = (keys[c][0],keys[c][1],True,keys[c][3])
                
        elif(mode == Mode.TRAINING):
            
            # Pull minimally correlated key codes from the flash_bucket until 7 are in the set
            while(len(sel) < N_KEYS_PER_FLASH):
                # Check if flash_bucket is empty
                if(len(flash_bucket)==0):
                    flash_bucket = [None] * (N_KEYBOARD_CHARS-N_WORD_KEYS+len(suggested_words))
                    for i in range(len(flash_bucket)):
                        flash_bucket[i] = i
                # Check if sel has grabbed at least 1 char
                if(len(sel)>=1):
                    # Get flash correlations between selected and available chars
                    corrs = np.sum(key_corrs[flash_bucket,:][:,sel],1);
                    # Get indices of minimum correlations
                    eligible = np.where(corrs == np.min(corrs))[0];
                    # Remove recently flashed chars
                    recently_flashed = eligible;
                    for td in reversed(range(1,N_KEYS_PER_FLASH+1)):          
                        t = time.time()-td*FLASH_DURATION;
                        recently_flashed = np.intersect1d(np.where(key_timers>t)[0],eligible);
                        if(len(recently_flashed)<len(eligible)):
                            # At least 1 has not been flashed within this threshold
                            eligible = np.setdiff1d(eligible,recently_flashed);
                            break;
                        else:
                            recently_flashed = eligible;
                    # Pull a random index from the eligible ones
                    r = random.randint(0,len(eligible)-1);
                    sel.append(flash_bucket[eligible[r]]);
                    del flash_bucket[eligible[r]];            
                else:
                    # Get the oldest char code from flash_bucket as the first code
                    max_t_key_code = -1;
                    max_t = time.time();
                    for code in flash_bucket:
                        if(key_timers[code] < max_t):
                            max_t = key_timers[code];
                            max_t_key_code = code;
                    sel.append(max_t_key_code);
                    flash_bucket.remove(max_t_key_code);
                    
            # Set those 7 key codes to true so they flash for this round
            for c in sel:
                keys[c] = (keys[c][0],keys[c][1],True,keys[c][3])
            
            # Update flash correlation matrix
            for ele in sel:
                key_corrs[ele,sel] += 1;
                
            # Reset flash timers for the 7 flashed
            key_timers[sel] = time.time();
           
    def Update_Word_Keys():

        nonlocal suggested_words;
        suggested_words = NLP_model.Suggest_Words(typed_text);

        # word suggestion row
        a = 100
        rs = 220
        font = pygame.font.SysFont('Calibri', 90, True, False)
        for i in range(1,5+1):
            if(i>len(suggested_words)):
                txt = font.render("-----", True, WHITE)
                txt_size = font.size("-----");    
                keys[39+i] = (txt,[a+350*(i-1),rs],keys[39+i][2],[a+350*(i-1)+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2]);
            else:
                n_chars = len(suggested_words[i-1]);
                char_width = (WORD_KEY_WIDTH-20)/n_chars;
                font_size = min([math.ceil(char_width/0.9),90]);
                font = pygame.font.SysFont('Calibri', font_size, True, False)
                txt = font.render(suggested_words[i-1].upper(), True, WHITE)
                txt_size = font.size(suggested_words[i-1].upper());
                keys[39+i] = (txt,[a+350*(i-1),rs],keys[39+i][2],[a+350*(i-1)+(WORD_KEY_WIDTH-txt_size[0])/2,rs+5+(KEY_HEIGHT-txt_size[1])/2]);
                
    def Display_Keys():      
                    
        if (mode == Mode.TRAINING):
            
            # In training mode
            
            # Display current target
            font = pygame.font.SysFont('Calibri', 250, True, False)
            if (currentTarget == 'd'):
                txt = font.render('del', True, WHITE)
                screen.blit(txt, [740,10])
            elif (currentTarget == 'b'):
                txt = font.render('fox', True, WHITE)
                screen.blit(txt, [740,10])
            elif (currentTarget == 'n'):
                txt = font.render('nlp', True, WHITE)
                screen.blit(txt, [740,10])
            else:
                txt = font.render(currentTarget, True, WHITE)
                screen.blit(txt, [835,10])
            # Display training mode text
            font = pygame.font.SysFont('Calibri', 30, True, False)
            text_w = font.size("Calibtation Mode")[0];
            txt = font.render('Calibration Mode', True, WHITE)
            screen.blit(txt, [1920-15-text_w,15])
            
        elif(mode == Mode.CLASSIFYING):
            
            # In classification mode
            
            # Display typed text
            font = pygame.font.SysFont('Calibri', 100, True, False)
            text_w = font.size(typed_text)[0];
            row_width = 1820;
            row_height = 80;
            n_rows_text = math.ceil(text_w/row_width);
            next_text_ind = 0;
            
            for row_ind in range(n_rows_text):
                for char_ind in reversed(range(next_text_ind,len(typed_text))):
                    if(typed_text[char_ind]==" " or char_ind==len(typed_text)-1):
                        text_w = font.size(typed_text[next_text_ind:char_ind+1])[0];
                        if(text_w < row_width):
                            txt = font.render(typed_text[next_text_ind:char_ind+1], True, WHITE);
                            screen.blit(txt, [50,10+row_height*row_ind]);
                            next_text_ind = char_ind+1;
                            break;
    
        img_id = random.randint(0,9)
        # Display keys
        for key in keys:
            
            # Check if key is word suggestion
            # (by checking if row height is the word suggestion row's height)
            if(key[1][1] != 220):
                
                # Key is not a word suggestion
                
                # Check if key is being stimulated
                if(key[2] == True):
                    # Draw random color border
                    pygame.draw.rect(screen,(random.randint(0,255),random.randint(0,255),random.randint(0,255)), [key[1][0]-8, key[1][1]-8, KEY_WIDTH+6*2, KEY_HEIGHT+8*2])
                    # Draw face image
                    screen.blit(face[img_id%10],[key[1][0], key[1][1], KEY_WIDTH, KEY_HEIGHT])
                    # Inc face id for next stimulated key
                    img_id += 1
        
                # Else, key is not being stimulated
                else:
                    # Draw gray background
                    pygame.draw.rect(screen,(55,55,55), [key[1][0], key[1][1], KEY_WIDTH, KEY_HEIGHT])
                    # Draw text
                    screen.blit(key[0], key[3]+[0,10])
                    # Draw white border
                    pygame.draw.rect(screen, WHITE, [key[1][0], key[1][1], KEY_WIDTH, KEY_HEIGHT], 3)
                
            elif(mode == Mode.CLASSIFYING):
                                
                # Check if key is being stimulated
                if(key[2] == True):
                    # Draw random color border
                    pygame.draw.rect(screen,(random.randint(0,255),random.randint(0,255),random.randint(0,255)), [key[1][0]-6, key[1][1]-6, WORD_KEY_WIDTH+6*2, KEY_HEIGHT+6*2])
                    # Draw (brighter) gray background
                    pygame.draw.rect(screen,(100,100,100), [key[1][0], key[1][1], WORD_KEY_WIDTH, KEY_HEIGHT])
                    # Draw face images
                    screen.blit(face[img_id%10],[key[1][0]+WORD_KEY_WIDTH/2-KEY_WIDTH, key[1][1], KEY_WIDTH, KEY_HEIGHT])
                    screen.blit(face[img_id%10],[key[1][0]+WORD_KEY_WIDTH/2, key[1][1], KEY_WIDTH, KEY_HEIGHT])
                    # Inc face id for next stimulated key
                    img_id += 1
        
                # Else, key is not being stimulated
                else:            
                    # Draw gray background
                    pygame.draw.rect(screen,(55,55,55), [key[1][0], key[1][1], WORD_KEY_WIDTH, KEY_HEIGHT])
                    # Draw text
                    screen.blit(key[0], key[3])
                    # Draw white border
                    pygame.draw.rect(screen, WHITE, [key[1][0], key[1][1], WORD_KEY_WIDTH, KEY_HEIGHT], 3)
    
    def Pick_Target(target_list):
        
        if(not target_list):
            target_list = [char for char in panogram]
        
        currentTarget = random.choice(target_list)
        target_list.remove(currentTarget)
        return currentTarget
    
    def Announce_Key(key_code, pre_text="", post_text=""):
       
        if(key_code==26):
            threading.start_new_thread( Generate_TTS, (pre_text+" "+"spacebar"+" "+post_text,) );
        elif(key_code==37):
            threading.start_new_thread( Generate_TTS, (pre_text+" "+"backspace"+" "+post_text,) );
        elif(key_code==38):
            threading.start_new_thread( Generate_TTS, (pre_text+" "+"the quick brown fox jumps over the lazy dog"+" "+post_text,) );
        elif(key_code==39):
            threading.start_new_thread( Generate_TTS, (pre_text+" "+"NLP toggled"+" "+post_text,) );
        elif(key_code>=40 and key_code<=44):
            threading.start_new_thread( Generate_TTS, (pre_text+" "+suggested_words[key_code-40]+" "+post_text,) );
        else:
            threading.start_new_thread( Generate_TTS, (pre_text+" "+panogram[key_code]+" "+post_text,) );
                        
    def Menu_Screen():
        
            # Overwrite the screen with a background color
            screen.fill(BLACK)
            
            # Write instruction sentences
            a = 235
            txt = font.render("Press '1' to enter training mode.", True, WHITE)
            screen.blit(txt, [390, a])
            txt = font.render("Press '2' to enter user mode.", True, WHITE)
            screen.blit(txt, [390, a+150*1])
            txt = font.render("Press '0' to return to this menu.", True, WHITE)
            screen.blit(txt, [390, a+150*2])
            txt = font.render("Press space bar to pause.", True, WHITE)
            screen.blit(txt, [390, a+150*3])
            
            # Render menu screen
            pygame.display.flip()
            
    print("Initializing GUI...")
    # Initialize the gui engine
    pygame.init();
    # Initialize the audio mixer
    pygame.mixer.init();
                    
    print("Opening classification inlet...")
    # Init inlet to recieve classifications from processor
    inlet_stream = resolve_stream('type', 'CLASSIFICATION');
    inlet = StreamInlet(inlet_stream[0]);
    
    # Define the colors we will use in RGB format
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    #BLUE = (0, 0, 255)
    #GREEN = (0, 255, 0)
    #RED = (255, 0, 0)
    
    #define faces
    face = [None] * 10
    for i in range(10):
        face[i] = pygame.image.load('league_icons/'+str(i)+'.jpg')
    bkspc = pygame.image.load('backspace_image.png')
    #tqbfjotld = pygame.image.load('tqbfjotld_image.png')
    #nlp_toggle = pygame.image.load('nlp_image.png')
     
    # Set the height and width of the screen
    #SCREEN_DIMENSIONS = [1152/2,648/2]
    SCREEN_DIMENSIONS = [1920,1080]
    screen = pygame.display.set_mode(SCREEN_DIMENSIONS)
     
    pygame.display.set_caption("P300 GUI")
    
    # Define key font
    font = pygame.font.SysFont('Calibri', 90, True, False)
    
    # Define key list
    # each key --> (label-string,location-tuple,isTarget-bool)
    keys = [None] * N_KEYBOARD_CHARS;
    Init_Keys()
    
    # Init timers
    stimTime = -1;
    targetTime = -1;
    
    print("Starting...")
    # Open in menu mode
    mode = Mode.MENU;
    Menu_Screen()
    
    # Panogram of all keys on the keyboard
    panogram = "QWERTYUIOPASDFGHJKLZXCVBNM_1234567890dbnqwert"
    
    # Possible training targets
    # (Exclude word suggestions from training)
    target_list = [char for char in panogram[:-5]]
    
    # For tracking pause requests
    spaceDown = False;
        
    # Init pygame clock to cap framerate
    clock = pygame.time.Clock()
    
    # Loop until the user closes out.
    while (mode != -999):
     
        # check if any flags were received from the processor (0.0==>non-blocking)
        classification_input, _ = inlet.pull_sample(0.0);
        
        #TODO: check if in training mode --> switch if classification received
        #TODO: check for other flags besides classifications (desync, restart, error, etc.)
        if(classification_input is not None):
            
            processor_flag = int(classification_input[N_KEYBOARD_CHARS]);
                
            # Update key probabilities if there is no classification result
            if(processor_flag == int(Processor_Flag.UPDATE_PROBABILITIES)):
                
                key_probs = classification_input[:N_KEYBOARD_CHARS];
                
            # Check for training-over flag
            elif(processor_flag == int(Processor_Flag.TRAINING_OVER)):
                
                # Training-over flag from processor has been received
                Generate_TTS("Exiting calibration mode");
                
                # Change mode to classification mode
                mode = Mode.CLASSIFYING
                            
                # Set flag to note that the processor is waiting for next char flag
                waiting_for_next_char = True; 
                
                # Logging time
                time_of_last_result = time.time();       
    
            # Else, check for classification result      
            else:
    
                # Name conversion
                classification_result = processor_flag;

                # Set flag to note that the processor is waiting for next char flag
                waiting_for_next_char = True;
    
                # Logging
                print("time&res:",time.time()-time_of_last_result,":",panogram[classification_result]);
                time_of_last_result = time.time();
        
                # Handle classification result
                Announce_Key(classification_result);
    
                if(classification_result==26):
                    typed_text += " ";
                    last_entry_length = [1, last_entry_length[0], last_entry_length[1]];
                elif(classification_result==37):                    
                    if(last_entry_length[0] > 0):
                        if(len(typed_text)>=1):
                            typed_text = typed_text[0:-last_entry_length[0]];
                            last_entry_length = [last_entry_length[1], last_entry_length[2], 0];
                    elif(len(typed_text)>=1):
                            typed_text = typed_text[0:-1];
                elif(classification_result==38):
                    #TODO: type the meme, bb
                    pass;
                elif(classification_result==39):
                    #TODO: toggle NLP on/off
                    pass;
                elif(classification_result>=40 and classification_result<=44):
                    prev_text = typed_text;
                    typed_text,_,_ = typed_text.rpartition(" ");
                    if(len(typed_text)!=0):
                        typed_text += (" "+suggested_words[classification_result-40]+" ").upper();
                    else:
                        typed_text += (suggested_words[classification_result-40]+" ").upper();
                    last_entry_length = [len(typed_text)-len(prev_text), last_entry_length[0], last_entry_length[1]];
                else:
                    typed_text += panogram[classification_result];
                    last_entry_length = [1, last_entry_length[0], last_entry_length[1]];
        
        # Check if window closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mode = -999
                
        # Exit when esc is pressed
        pressed_keys = pygame.key.get_pressed()
        if(pressed_keys[pygame.K_ESCAPE]):
            threading.start_new_thread( Generate_TTS, ("Closing",) );
            time.sleep(2);
            d.close();
            pygame.quit()
            return
            
        # Pause when space is pressed
        if(pressed_keys[pygame.K_SPACE] and not spaceDown):
        
            # Track spacebar press
            spaceDown = True
            
            # Reset timers
            end = time.time()
            stimTime = end - stimTime
            targetTime = end - targetTime
    
            if(mode == Mode.TRAINING):
                mode = Mode.TRAINING_PAUSED;
                
            elif(mode == Mode.CLASSIFYING):
                mode = Mode.CLASSIFYING_PAUSED;
    
            elif(mode == Mode.TRAINING_PAUSED):
                mode = Mode.TRAINING;
    
            elif(mode == Mode.CLASSIFYING_PAUSED):
                mode = Mode.CLASSIFYING;
    
        # detect lifting of space bar
        elif(not pressed_keys[pygame.K_SPACE]):
            # Track spacebar press
            spaceDown = False       
                        
        # if in menu
        if(mode == Mode.MENU):
            
            # If user pressed '1'        
            if(pressed_keys[pygame.K_1]):
                
                # Entering training mode
                mode = Mode.TRAINING;   
                
                # Announce training mode
                threading.start_new_thread( Generate_TTS, ("Initializing short calibration mode",) );
                                
                # Init key correlation matrix
                key_corrs = np.zeros([N_KEYBOARD_CHARS,N_KEYBOARD_CHARS]);
                
                # Let matlab catch up
                time.sleep(5)            
                
                # Pick and announce a new target
                currentTarget = Pick_Target(target_list)
                Announce_Key(panogram.find(currentTarget),pre_text="focus");
                
                # Reset target timer for new target
                targetTime = time.time();
                
                # Send processor the start flag
                outlet.push_sample([-1] * (N_KEYBOARD_CHARS+1))
                
                # Overwrite the screen with a background color
                screen.fill(BLACK)
                
                # Display keys
                Display_Keys()
                
                # Render screen
                pygame.display.flip()
                
                # Allow the user a moment to find the target char
                time.sleep(TRAINING_PAUSE_DURATION)
                
                # Init timer to a time greater than flash_duration seconds ago
                # This ensures flashes will reset on the very first frame
                stimTime = time.time()-(FLASH_DURATION+.001);
                
            # If user pressed '2'      
            if(pressed_keys[pygame.K_2]):
                
                #TODO: implement direct entry to clssification mode
                
                # Entering classification mode
                mode = Mode.CLASSIFYING;   
                
                # Let matlab catch up
                time.sleep(5)
                
                # Init timer to a time greater than flash_duration seconds ago
                # This ensures flashes will reset on the very first frame
                stimTime = time.time()-(FLASH_DURATION+.001);
                
        # If in keyboard mode
        if(mode == Mode.TRAINING or mode == Mode.CLASSIFYING):
            
            # Return to menu if 0 is pressed
            if(pressed_keys[pygame.K_0]):
                mode = Mode.MENU;
                Menu_Screen();
                
            # Check timers
            end = time.time()        
            
            # Check stimuli timer
            if(end-stimTime > FLASH_DURATION):
                            
                # If classifying or if training & on same target, update flashes
                if( (mode == Mode.TRAINING and end-targetTime < TARGET_CHAR_DURATION) or mode == Mode.CLASSIFYING):
                    
                    # Overwrite the screen with a background color
                    screen.fill(BLACK)
                    
                    # Reset flash timer
                    stimTime = end
                                
                    # Update key status
                    Update_Keys()
                    
                    # Display keys
                    Display_Keys()
                    
                    # If this is a sync/target trial
                    #TODO: currently only checking target; also check sync
                    if(keys[panogram.find(currentTarget)][2]==True):
                        
                        # Invert all 3 triggers
                        
                        # 001 --> 110
                        # 011 --> 100
                        # 100 --> 011
                        # 110 --> 001
                        
                        if (state == 0x01):
                            state = 0x06
                        elif (state == 0x03):
                            state = 0x04
                        elif (state == 0x04):
                            state = 0x03
                        elif (state == 0x06):
                            state = 0x01
                            
                    # Else, this is not a target
                    else:
                        
                        # Invert the first and third triggers
                        
                        # 001 --> 100
                        # 011 --> 110
                        # 100 --> 001
                        # 110 --> 011
                        
                        if (state == 0x01):
                            state = 0x04
                        elif (state == 0x03):
                            state = 0x06
                        elif (state == 0x04):
                            state = 0x01
                        elif (state == 0x06):
                            state = 0x03
                            
                    # Send ftdi new trigger state
                    d.write(str(state))  
                                
                    # Send stim codes after keys have been displayed
                    mysample = [0] * (N_KEYBOARD_CHARS+1)
                    for i in range(len(keys)):
                        if(keys[i][2]):
                            mysample[i] = 1
                        else:
                            mysample[i] = 0
                        if(i >= N_KEYBOARD_CHARS-N_WORD_KEYS and i-(N_KEYBOARD_CHARS-N_WORD_KEYS) >= len(suggested_words)):
                            mysample[i] = -1
                            
                    # Send stim flag at end of the array
                    # If in classification mode
                    if(mode == Mode.CLASSIFYING):
                        
                        # Check if this is the first trial since last classification was received
                        if(not waiting_for_next_char):
                            
                            # Check if this is a sync trial
                            #TODO: use DRBGs to sync trial data
                            if(keys[panogram.find(currentTarget)][2]==True):
                                mysample[N_KEYBOARD_CHARS] = -1;
                            else:
                                mysample[N_KEYBOARD_CHARS] = 0;
                            
                        else:
                            
                            #print("Time to get here:", time_of_last_result-time.time());
                            
                            # Update word suggestions on GUI
                            #t = time.time();
                            #TODO: speed this up substantially
                            Update_Word_Keys();                 
                            #print("Time to update word keys:",time.time()-t)
                            
                            # Send char probs to processor
                            #t = time.time();
                            char_probs = NLP_model.Get_Char_Probs(typed_text);
                            #print("Time to update char probs:",time.time()-t)
                            
                            #t = time.time();
                            # Convert one-hot from 0/1 to +/-
                            # Use magnitude to send key probability
                            # Convert probability from 0-1 float to signed 16 bit int
                            # Note: only for 26 letters & the space bar
                            for ch in char_probs:
                                key_code = -1;
                                if(ch==" "):
                                    key_code = panogram.index("_");
                                else:
                                    key_code = panogram.index(ch.upper());
                                key_prob = 0.01;
                                if(char_probs[ch] > 0.01):
                                    key_prob = char_probs[ch]
                                if(mysample[key_code] == 1):
                                    mysample[key_code] = -round(key_prob*32767);
                                else:
                                    mysample[key_code] = round(key_prob*32767);
                            
                            # Check if this is a sync trial
                            #TODO: use DRBGs to sync trial data
                            if(keys[panogram.find(currentTarget)][2]==True):
                                mysample[N_KEYBOARD_CHARS] = -3;
                            else:
                                mysample[N_KEYBOARD_CHARS] = -2;
                            # First trial of next char has been sent
                            waiting_for_next_char = False;
                            #print("Time to update reform stim codes:",time.time()-t)
    
                    # If in training mode
                    elif(mode == Mode.TRAINING):
                        
                        # Send target label
                        mysample[N_KEYBOARD_CHARS] = panogram.index(currentTarget)+1
                    
                    # Push the data over LSL
                    outlet.push_sample(mysample)
                                    
                # Check target char timer if in training mode
                elif(mode == Mode.TRAINING and end-targetTime >= TARGET_CHAR_DURATION):
                    
                    # Overwrite the screen with a background color
                    screen.fill(BLACK)
                    
                    # Pick and announce a new target
                    currentTarget = Pick_Target(target_list)
                    Announce_Key(panogram.find(currentTarget),pre_text="focus");
                    
                    # Reset target timer for new target
                    targetTime = end
                                                          
                    # Classification received, reset flash correlations
                    key_corrs = np.zeros([N_KEYBOARD_CHARS,N_KEYBOARD_CHARS]);
                
                    # Do not stimulate any keys this frame
                    for i in range(len(keys)):
                        keys[i] = (keys[i][0],keys[i][1],False,keys[i][3])
                    
                    # Display keys
                    Display_Keys()  
                    
                    # Render the screen
                    pygame.display.flip()
                    
                    # Pause and allow user time to find the next target key
                    time.sleep(TRAINING_PAUSE_DURATION)
                    
                    # Reset flash timer for first flash of new target
                    stimTime = time.time()-FLASH_DURATION
                
            # Go ahead and update the screen with what we've drawn.
            # This MUST happen after all the other drawing commands.
            pygame.display.flip()
         
            # This limits the while loop to a max of 10 times per second.
            # Leave this out and we will use all CPU we can.
            clock.tick(FRAMERATE_CAP)
                
    # Be IDLE friendly
    pygame.quit()
