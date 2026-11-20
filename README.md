AudViz is a simple audio visualizer.

It captures the system audio and displayes it as a live waveform in a pygame window.
The original inspiration for this project was an oscilloscope, which I have attempted to recreate.

System Audio
     ->
WASAPI Loopback
     ->
PyAudioWPatch
  ->   
NumPy
     ->
Pygame
     ->
Wave

Requirements:
Python 3.12 (It was made using 3.12)
Windows (Coded for windows functions)
NumPy
PyGame
PyAudiowPatch

To increase or decrease the waves change the GAIN variable according to liking. Default is 2.5

Suggestions and feedbacks welcome!
