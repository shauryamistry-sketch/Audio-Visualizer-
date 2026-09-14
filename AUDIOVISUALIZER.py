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
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED | WS_EX_NOACTIVATE)

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

BG_COLOR = (0,0,0)
BEAM_CORE = (230, 255, 235)
BEAM_INNER = (50, 255, 100, 160)
BEAM_OUTER = (0, 200, 60, 45)
TEXT_COLOR = (80, 170, 110)

trail_surface = pygame.Surface((WIDTH, HEIGHT))
trail_surface.fill(BG_COLOR)

fade_mask = pygame.Surface((WIDTH, HEIGHT))
fade_mask.set_alpha(32)
fade_mask.fill(BG_COLOR)

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


    enforce_topmost()

    try:
        raw_data = stream.read(CHUNK, exception_on_overflow=False)
        audio_samples = np.frombuffer(raw_data, dtype=np.int16)
    except IOError:
        audio_samples = np.zeros(CHUNK)
    center_x = WIDTH//2
    center_y = HEIGHT//2
    points = []

    normalized = audio_samples/32768.0
    volume = np.sqrt(np.mean(normalized**2))

    SILENCE_THRESHOLD = 0.008

    if volume < SILENCE_THRESHOLD:
        jitter_x = np.random.uniform(-0.8, 0.8)
        jitter_y = np.random.uniform(-0.8, 0.8)
        points = [(int(center_x + jitter_x), int(center_y + jitter_y))]
    else:
        SPREAD_X = 210.0
        SPREAD_Y = 130.0

        step = 64
        sub_samples = normalized[::step]
        num_pts = len(sub_samples)
        
       
        delay = max(2, num_pts // 6)

        for i in range(num_pts - delay):
            raw_x = sub_samples[i]
            raw_y = sub_samples[i + delay]

            
            x_val = np.sign(raw_x) * (np.abs(raw_x) ** 0.65) * SPREAD_X
            y_val = np.sign(raw_y) * (np.abs(raw_y) ** 0.65) * SPREAD_Y

            pt_x = int(np.clip(center_x + x_val, 6, WIDTH - 6))
            pt_y = int(np.clip(center_y - y_val, 6, HEIGHT - 6))
            points.append((pt_x, pt_y))
            

    trail_surface.blit(fade_mask, (0,0))

    if len(points) == 1:
        spot = points[0]
        glow_outer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow_outer, BEAM_OUTER, spot, 8)
        trail_surface.blit(glow_outer, (0, 0))

        glow_inner = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow_inner, BEAM_INNER, spot, 4)
        trail_surface.blit(glow_inner, (0, 0))

        pygame.draw.circle(trail_surface, BEAM_CORE, spot, 1)

    elif len(points) > 1:
        glow_outer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.lines(glow_outer, BEAM_OUTER, False, points, 6)
        trail_surface.blit(glow_outer, (0, 0))

        glow_inner = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.lines(glow_inner, BEAM_INNER, False, points, 3)
        trail_surface.blit(glow_inner, (0, 0))

        pygame.draw.lines(trail_surface, BEAM_CORE, False, points, 1)

    screen.blit(trail_surface, (0,0))

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