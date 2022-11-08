# -*- coding: utf-8 -*-
"""
Created on Tue Nov  8 01:25:02 2022

@author: Darren
"""
import subprocess;
import time;

subprocess.Popen('start /wait python Cyton_Data_Packager.py', shell=True);
time.sleep(1);
subprocess.Popen('start /wait python BCI_Controller.py', shell=True);
time.sleep(1);
subprocess.Popen('start /wait python P300_Processor.py', shell=True);
