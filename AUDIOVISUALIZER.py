import numpy as np
import os
import pyaudiowpatch as pyaudio
import pygame
import sys

CHUNK = 1024
FORMAT = pyaudio.paInt16
GAIN = 2.5
p = pyaudio.PyAudio()
dev = p.get_default_wasapi_loopback()
RATE = int(dev["defaultSampleRate"])
CHANNELS = int(dev["maxInputChannels"])
stream=p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=dev["index"], frames_per_buffer = CHUNK)
os.environ['SDL_VIDEO_WINDOW_POS'] = "1100, 50"
pygame.init()
WIDTH,HEIGHT = 900,500
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("AudViz")
clock=pygame.time.Clock()
bgcol=(5, 12, 8)
grcol = (33, 64, 47)
glcol=(0,150, 70, 80)
trcol=(120, 255, 160)

def draw_grid():
    w,h = screen.get_size()
    grsize=50
    for x in range(0, w, grsize):
        pygame.draw.line(screen, grcol, (x, 0), (x, h), 1) 
    for y in range(0,h,grsize):
        pygame.draw.line(screen, grcol, (0, y), (w, y), 1)
running = True
while running:
    for event in pygame.event.get():
        if (event.type == pygame.QUIT) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    try:
        rawdat = stream.read(CHUNK, exception_on_overflow=False)
        audsam = np.frombuffer(rawdat, dtype=np.int16)
    except IOError:
        audsam = np.zeros(CHUNK*CHANNELS, dtype=np.int16)
    if CHANNELS>1:
        n = (len(audsam)//CHANNELS)*CHANNELS
        audsam = audsam[:n]
        audsam=audsam.reshape(-1, CHANNELS).mean(axis=1)
    screen.fill(bgcol)
    draw_grid()
    norm=np.clip((audsam/32768.0)*GAIN, -1.0, 1.0)
    w, h = screen.get_size()
    centy = h//2
    points=[]
    posx = np.linspace(0, w-1, len(norm))
    for x, sample in zip(posx, norm):
        y = int(centy - sample*(h//2 - 10))
        y = np.clip(y, 0, h-1)
        points.append((int(x), int(y)))
    if len(points)>1:
        glsurf=pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.lines(glsurf, glcol, False, points, 5)
        screen.blit(glsurf, (0,0))
        pygame.draw.lines(screen, trcol, False, points, 2)
        pygame.display.flip()
        clock.tick(60)
stream.stop_stream()
stream.close()
p.terminate()
pygame.quit()
sys.exit
