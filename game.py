import cv2
import mediapipe as mp
import pygame
import numpy as np
import random
import time
import os
from tkinter import Tk, filedialog

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

pygame.init()
WIDTH, HEIGHT = 1000,650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DINO GAME")
clock = pygame.time.Clock()

ground_y = HEIGHT - 80
player_y = ground_y
velocity = 0
gravity = 1
jump_strength = -18
jump = False

obstacles = []
obstacle_speed = 7
min_gap = 250
max_gap = 1000
next_gap = random.randint(min_gap, max_gap)

game_started = False
start_triggered = False
start_time_delay = 0
score = 0
score_start_time = None

start_btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 40, 200, 80)

_root = Tk()
_root.withdraw()  


def ask_image(title="Select Image"):

    path = filedialog.askopenfilename(title=title,filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
    return path if path and os.path.isfile(path) else None

def load_and_scale(path, size):
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        img = pygame.image.load(path).convert()  
    return pygame.transform.smoothscale(img, size)

player_img = None
obstacle_img = None
bg_img = None

print("Optional: choose custom images. Press Cancel to keep defaults.")

p = ask_image("Select Player Image (optional)")
if p:
    player_img = load_and_scale(p, (60, 60))

o = ask_image("Select Obstacle Image (optional)")
if o:
    obstacle_img = load_and_scale(o, (60, 40))

b = ask_image("Select Background Image (optional)")
if b:
    bg_img = load_and_scale(b, (WIDTH, HEIGHT))

def cv_to_pygame(frame):
    """Convert OpenCV BGR frame → pygame surface (RGB and rotated to match orientation)."""
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    surf = pygame.surfarray.make_surface(frame)
    return surf

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                path = ask_image("Select Player Image")
                if path:
                    player_img = load_and_scale(path, (60, 60))
                    print("Player image changed.")
            elif event.key == pygame.K_o:
                path = ask_image("Select Obstacle Image")
                if path:
                    obstacle_img = load_and_scale(path, (60, 40))
                    print("Obstacle image changed.")
            elif event.key == pygame.K_b:
                path = ask_image("Select Background Image")
                if path:
                    bg_img = load_and_scale(path, (WIDTH, HEIGHT))
                    print("Background image changed.")

    ret, cam_frame = cap.read()

    cam_frame = cv2.flip(cam_frame, 1)
    resized_frame = cv2.resize(cam_frame, (WIDTH, HEIGHT))

    rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    finger_x = finger_y = None
    gesture = "none"

    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0].landmark
        finger_x = int(lm[8].x * WIDTH)
        finger_y = int(lm[8].y * HEIGHT)

        tips = [8, 12, 16, 20]
        fingers_open = sum(lm[t].y < lm[t - 2].y for t in tips)
        if fingers_open == 4:
            gesture = "open"


    if not game_started:
        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            surface_bg = cv_to_pygame(resized_frame)
            screen.blit(surface_bg, (0, 0))

        pygame.draw.rect(screen, (100, 100, 255), start_btn_rect, border_radius=15)
        font = pygame.font.SysFont(None, 50)
        text = font.render("START", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))

        if finger_x and finger_y:
            pygame.draw.circle(screen, (255, 255, 255), (finger_x, finger_y), 8)

            if start_btn_rect.collidepoint(finger_x, finger_y):
                if not start_triggered:
                    start_triggered = True
                    start_time_delay = time.time()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not start_triggered:
            start_triggered = True
            start_time_delay = time.time()

        if start_triggered and time.time() - start_time_delay >= 1:
            game_started = True
            score_start_time = time.time()

        pygame.display.flip()
        clock.tick(30)
        continue

    score = int(time.time() - score_start_time) if score_start_time else 0

    if gesture == "open" and not jump:
        jump = True
        velocity = jump_strength

    if jump:
        player_y += velocity
        velocity += gravity
        if player_y >= ground_y:
            player_y = ground_y
            jump = False

    if not obstacles or obstacles[-1]["x"] < WIDTH - next_gap:
        w = random.randint(40, 70)
        obstacles.append({"x": WIDTH, "w": w})
        next_gap = random.randint(min_gap, max_gap)

    for o in obstacles:
        o["x"] -= obstacle_speed

    obstacles = [o for o in obstacles if o["x"] > -200]

    screen.fill((10, 10, 10))

    if not bg_img:
        surface_bg = cv_to_pygame(resized_frame)
        surface_bg.set_alpha(180)  # semi-transparent background
        screen.blit(surface_bg, (0, 0))
    else:
        screen.blit(bg_img, (0, 0))

    player_rect = pygame.Rect(100, player_y - 60, 60, 60)
    if player_img:
        screen.blit(player_img, player_rect.topleft)
    else:
        pygame.draw.rect(screen, (0, 255, 0), player_rect, border_radius=8)

    for o in obstacles:
        obs_rect = pygame.Rect(int(o["x"]), ground_y - 40, int(o["w"]), 40)
        if obstacle_img:
            # scale obstacle_img to current obstacle width while keeping height 40
            img = pygame.transform.smoothscale(obstacle_img, (max(1, int(o["w"])), 40))
            screen.blit(img, obs_rect.topleft)
        else:
            pygame.draw.rect(screen, (255, 0, 0), obs_rect)

    # Score
    font = pygame.font.SysFont(None, 40)
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    # Finger cursor (optional)
    if finger_x and finger_y:
        pygame.draw.circle(screen, (255, 255, 255), (finger_x, finger_y), 6)

    # Collision detection (rect-based)
    for o in obstacles:
        obs_rect = pygame.Rect(int(o["x"]), ground_y - 40, int(o["w"]), 40)
        if player_rect.colliderect(obs_rect):
            # Game over
            print(f"Game Over! Score: {score}")
            running = False
            break

    pygame.display.flip()
    clock.tick(30)

cap.release()
pygame.quit()
cv2.destroyAllWindows()
# Destroy tkinter root
try:
    _root.destroy()
except Exception:
    pass
