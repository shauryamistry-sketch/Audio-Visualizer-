import ctypes
from ctypes import wintypes
import os
import sys
import tkinter as tk
import numpy as np
import pyaudio
import pygame

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

root = tk.Tk()
screen_w = root.winfo_screenwidth()
root.destroy()

WIDTH, HEIGHT = 260, 120
MARGIN_X = 20
MARGIN_Y = 20
pos_x = screen_w - WIDTH - MARGIN_X
pos_y = MARGIN_Y
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{pos_x}, {pos_y}"

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Audio Visualizer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 10, bold=True)

hwnd = pygame.display.get_wm_info()["window"]

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0X00080000
ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED)

OPACITY = 175
ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, OPACITY, 0x00000002)

HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0X0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)


def enforce_topmost():
    ctypes.windll.user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
    )

WM_NCLBUTTONDOWN = 0x00A1
HTCAPTION = 0x0002

def start_native_drag():
    ctypes.windll.user32.ReleaseCapture()
    ctypes.windll.user32.SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)

BG_COLOR = (4,12,6)
GRID_COLOR = (12, 35, 18)
GLOW_COLOR = (0, 190, 75, 70)
TRACE_COLOR = (140, 255, 180)
TEXT_COLOR = (80, 170, 110)

def draw_grid():
    grid_size = 25
    for x in range(0, WIDTH, grid_size):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, grid_size):
        pygame.draw.line(screen, GRID_COLOR, (0,y), (WIDTH, y), 1)
    center_y = HEIGHT//2
    pygame.draw.line(screen, (22, 55, 30), (0, center_y), (WIDTH, center_y), 1)

is_locked = False
frame_counter = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            is_locked = not is_locked
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not is_locked:
                start_native_drag()
                enforce_topmost()

    frame_counter += 1
    if frame_counter % 30 == 0:
        enforce_topmost()
    try:
        raw_data = stream.read(CHUNK, exception_on_overflow=False)
        audio_samples = np.frombuffer(raw_data, dtype=np.int16)
    except IOError:
        audio_samples = np.zeros(CHUNK)
    GAIN = 5.0
    center_y = HEIGHT//2
    points = []

    step = len(audio_samples) / WIDTH
    for i in range(WIDTH):
        sample_idx = int(i * step)
        normalized_sample = audio_samples[sample_idx]/ 32768.0
        amplified_sample = normalized_sample*GAIN

        y_offset = amplified_sample * (HEIGHT /2)
        screen_y = int(np.clip(center_y - y_offset, 5, HEIGHT-5))
        points.append((i, screen_y))

    screen.fill(BG_COLOR)
    draw_grid()

    if len(points) > 1:
        glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.lines(glow_surf, GLOW_COLOR, False, points, 4)
        screen.blit(glow_surf, (0,0))
        pygame.draw.lines(screen, TRACE_COLOR, False, points, 1)

    status_label = "LOCKED" if is_locked else "DRAGGABLE"
    status_surf = font.render(status_label, True, TEXT_COLOR)
    screen.blit(status_surf, (6,5))

    pygame.display.flip()
    clock.tick(60)

stream.stop_stream()
stream.close()
p.terminate()
pygame.quit()
sys.exit()