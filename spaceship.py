import pygame
import random

# Initialize Pygame
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()
FPS = 60

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)    # Fallback for spread shot
CYAN = (0, 255, 255)  # Fallback for shield

# Load images with error handling
try:
    player_img = pygame.image.load("D:\\python\\spaceship.png")
    player_img = pygame.transform.scale(player_img, (50, 50))
    print("Player spaceship image loaded successfully")
except pygame.error as e:
    print(f"Error loading spaceship.png: {e}. Using rectangle fallback.")
    player_img = None

try:
    blast_img = pygame.image.load("D:\\python\\blast.png")
    blast_img = pygame.transform.scale(blast_img, (60, 60))
    print("Blast image loaded successfully")
except pygame.error as e:
    print(f"Error loading blast.png: {e}. Using yellow rectangle fallback.")
    blast_img = None

try:
    background = pygame.image.load("D:\\python\\space.png")
    background = pygame.transform.scale(background, (screen_width, screen_height))
    print("Background image loaded successfully")
except pygame.error:
    print("Error: space.png not found. Using black background.")
    background = None

try:
    power_imgs = {
        "spread_shot": pygame.image.load("D:\\python\\spread.png"),
        "shield": pygame.image.load("D:\\python\\shield.png")
    }
    power_imgs = {k: pygame.transform.scale(v, (30, 30)) for k, v in power_imgs.items()}
    print("Power-up images loaded successfully")
except pygame.error as e:
    print(f"Error loading power-up images: {e}. Using rectangle fallback.")
    power_imgs = None

# Optional: Enemy and bullet images
try:
    enemy_img = pygame.image.load("D:\\python\\enemy.png")
    enemy_img = pygame.transform.scale(enemy_img, (60, 60))
    print("Enemy image loaded successfully")
except pygame.error:
    print("Error: enemy.png not found. Using rectangle fallback.")
    enemy_img = None

try:
    bullet_img = pygame.image.load("D:\\python\\bullet.png")
    bullet_img = pygame.transform.scale(bullet_img, (15, 25))
    print("Bullet image loaded successfully")
except pygame.error:
    print("Error: bullet.png not found. Using rectangle fallback.")
    bullet_img = None

# Load sounds
try:
    shoot_sound = pygame.mixer.Sound("D:\\python\\shoot.wav")
    explosion_sound = pygame.mixer.Sound("D:\\python\\explosion.wav")
    power_sound = pygame.mixer.Sound("D:\\python\\power.wav")
    gameover_sound = pygame.mixer.Sound("D:\\python\\gameover.wav")
    print("Sound effects loaded successfully")
except pygame.error as e:
    print(f"Error loading sound effects: {e}. Sounds disabled.")
    shoot_sound = explosion_sound = power_sound = gameover_sound = None

try:
    pygame.mixer.music.load("D:\\python\\bgm.wav")
    pygame.mixer.music.set_volume(0.3)  # Lower volume to balance with sound effects
    print("Background music loaded successfully")
except pygame.error as e:
    print(f"Error loading bgm.wav: {e}. Background music disabled.")
    pygame.mixer.music = None

# Player setup
player_width, player_height = 50, 50
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - 70
player_speed = 5
player = pygame.Rect(player_x, player_y, player_width, player_height)
player_blink = False
blink_interval = 200  # ms

# Bullet setup
bullet_width, bullet_height = 15, 25
bullet_speed = 7
bullets = []
bullet_state = "ready"
bullet_cooldown = 500  # ms between shots
last_shot_time = 0

# Enemy setup
enemy_width, enemy_height = 60, 60
enemy_speed = 3
enemies = []
enemy_spawn_rate = 0.05
max_enemies = 6

# Power-up setup
power_up_width, power_up_height = 30, 30
power_ups = []
power_up_spawn_interval = 15000  # 15 seconds
last_power_up_spawn = 0
power_up_speed = 2
power_up_duration = 10000  # 10 seconds
active_power = None
power_activation_time = 0

# Power-up types
POWER_TYPES = [
    "spread_shot",  # 4 bullets in fan
    "shield"       # Invincibility
]

# Game variables
game_over = False
game_state = "menu"
font = pygame.font.SysFont("arial", 36)
hit_effects = []
hit_count = 0

def draw_background():
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.fill(BLACK)

def draw_player():
    if player_blink and (pygame.time.get_ticks() // blink_interval) % 2 == 0:
        return  # Skip drawing for blink effect
    if player_img:
        screen.blit(player_img, (player.x, player.y))
    else:
        pygame.draw.rect(screen, GREEN, player)

def draw_bullet(bullet):
    if bullet_img:
        screen.blit(bullet_img, (bullet["rect"].x, bullet["rect"].y))
    else:
        pygame.draw.rect(screen, WHITE, bullet["rect"])

def draw_enemy(enemy):
    if enemy_img:
        screen.blit(enemy_img, (enemy.x, enemy.y))
    else:
        pygame.draw.rect(screen, RED, enemy)

def draw_hit_effect(x, y):
    if blast_img:
        screen.blit(blast_img, (x, y))
    else:
        pygame.draw.rect(screen, YELLOW, (x, y, enemy_width, enemy_height))

def draw_power_up(power_up, power_type):
    if power_imgs:
        screen.blit(power_imgs[power_type], (power_up.x, power_up.y))
    else:
        color = {
            "spread_shot": BLUE,
            "shield": CYAN
        }[power_type]
        pygame.draw.rect(screen, color, power_up)

def is_collision(rect1, rect2):
    return rect1.colliderect(rect2)

def spawn_enemy():
    if len(enemies) < max_enemies and random.random() < enemy_spawn_rate:
        x = random.randint(0, screen_width - enemy_width)
        enemies.append(pygame.Rect(x, 0, enemy_width, enemy_height))
        print(f"Enemy spawned at x={x}, y=0")

def spawn_power_up(current_time):
    global last_power_up_spawn
    if current_time - last_power_up_spawn > power_up_spawn_interval:
        x = random.randint(0, screen_width - power_up_width)
        power_type = random.choice(POWER_TYPES)
        power_ups.append((pygame.Rect(x, 0, power_up_width, power_up_height), power_type))
        last_power_up_spawn = current_time
        print(f"Power-up spawned: {power_type} at x={x}, y=0")

def activate_power(power_type):
    global active_power, power_activation_time, player_blink
    active_power = power_type
    power_activation_time = pygame.time.get_ticks()
    player_blink = True
    if power_sound:
        power_sound.play()
    print(f"Activated power: {power_type}")

def deactivate_power():
    global active_power, player_blink
    active_power = None
    player_blink = False
    print("Power deactivated")

def shoot_bullets():
    global last_shot_time
    current_time = pygame.time.get_ticks()
    if current_time - last_shot_time > bullet_cooldown:
        if active_power == "spread_shot":
            for angle in [-15, -5, 5, 15]:
                bullet = {
                    "rect": pygame.Rect(player.x + player_width // 2 - bullet_width // 2, player.y - bullet_height, bullet_width, bullet_height),
                    "angle": angle
                }
                bullets.append(bullet)
        else:
            bullet = {
                "rect": pygame.Rect(player.x + player_width // 2 - bullet_width // 2, player.y - bullet_height, bullet_width, bullet_height),
                "angle": None
            }
            bullets.append(bullet)
        last_shot_time = current_time
        print(f"Bullet fired at x={bullet['rect'].x}, y={bullet['rect'].y}")
        if shoot_sound:
            shoot_sound.play()

def display_text(text, x, y, color=WHITE):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def setup():
    global player, bullets, enemies, game_over, hit_effects, game_state, hit_count, active_power, power_ups, last_power_up_spawn, player_blink
    player = pygame.Rect(screen_width // 2 - player_width // 2, screen_height - 70, player_width, player_height)
    bullets = []
    enemies = []
    power_ups = []
    hit_effects = []
    hit_count = 0
    game_over = False
    game_state = "playing"
    active_power = None
    player_blink = False
    last_power_up_spawn = pygame.time.get_ticks()
    print("Game reset")
    if pygame.mixer.music:
        pygame.mixer.music.play(-1)  # Start background music
        print("Background music started")

def main():
    global bullet_state, game_over, hit_count, game_state, active_power, power_activation_time, last_power_up_spawn
    setup()
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        if game_state == "menu":
            draw_background()
            display_text("Space Shooter", screen_width // 2 - 100, screen_height // 2 - 50)
            display_text("Press S to Start", screen_width // 2 - 100, screen_height // 2)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    if pygame.mixer.music:
                        pygame.mixer.music.stop()
                        print("Background music stopped (quit)")
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        setup()
            pygame.display.flip()
            clock.tick(FPS)
            continue

        if not game_over:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    if pygame.mixer.music:
                        pygame.mixer.music.stop()
                        print("Background music stopped (quit)")
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and bullet_state == "ready":
                        shoot_bullets()

            # Player movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player.x > 0:
                player.x -= player_speed
            if keys[pygame.K_RIGHT] and player.x < screen_width - player_width:
                player.x += player_speed

            # Update bullets
            for bullet in bullets[:]:
                if bullet["angle"] is not None:
                    dx = bullet["angle"] * 0.1
                    bullet["rect"].x += dx
                    bullet["rect"].y -= bullet_speed
                else:
                    bullet["rect"].y -= bullet_speed
                if bullet["rect"].y < 0:
                    bullets.remove(bullet)
                    print("Bullet removed (off-screen)")
            if not bullets:
                bullet_state = "ready"

            # Spawn and update enemies
            spawn_enemy()
            for enemy in enemies[:]:
                enemy.y += enemy_speed
                if enemy.y > screen_height:
                    enemies.remove(enemy)
                    print("Enemy reached bottom (no score)")
                if is_collision(player, enemy) and active_power != "shield":
                    game_over = True
                    print("Game Over: Player hit by enemy")
                    if pygame.mixer.music:
                        pygame.mixer.music.stop()
                        print("Background music stopped (game over)")
                    if gameover_sound:
                        gameover_sound.play()
                        print("Game over sound played")

            # Spawn and update power-ups
            spawn_power_up(current_time)
            for power_up, power_type in power_ups[:]:
                power_up.y += power_up_speed
                if power_up.y > screen_height:
                    power_ups.remove((power_up, power_type))
                if is_collision(player, power_up):
                    power_ups.remove((power_up, power_type))
                    activate_power(power_type)

            # Check power duration
            if active_power and current_time - power_activation_time > power_up_duration:
                deactivate_power()

            # Check bullet-enemy collisions
            bullets_to_remove = []
            enemies_to_remove = []
            for bullet in bullets:
                for enemy in enemies:
                    if is_collision(bullet["rect"], enemy):
                        print(f"Hit! Bullet at x={bullet['rect'].x}, y={bullet['rect'].y} hit enemy at x={enemy.x}, y={enemy.y}")
                        bullets_to_remove.append(bullet)
                        enemies_to_remove.append(enemy)
                        hit_count += 1
                        hit_effects.append({"x": enemy.x, "y": enemy.y, "timer": 10})
                        print(f"Score after hit: {hit_count}")
                        if explosion_sound:
                            explosion_sound.play()
                        break
            for bullet in bullets_to_remove:
                if bullet in bullets:
                    bullets.remove(bullet)
            for enemy in enemies_to_remove:
                if enemy in enemies:
                    enemies.remove(enemy)

            # Update hit effects
            for effect in hit_effects[:]:
                effect["timer"] -= 1
                if effect["timer"] <= 0:
                    hit_effects.remove(effect)

            # Draw everything
            draw_background()
            draw_player()
            for bullet in bullets:
                draw_bullet(bullet)
            for enemy in enemies:
                draw_enemy(enemy)
            for power_up, power_type in power_ups:
                draw_power_up(power_up, power_type)
            for effect in hit_effects:
                draw_hit_effect(effect["x"], effect["y"])
            display_text(f"Score: {hit_count}", 10, 10, YELLOW)
            if active_power:
                display_text(f"Power: {active_power}", 10, 50, YELLOW)
        else:
            draw_background()
            display_text("Game Over!", screen_width // 2 - 100, screen_height // 2 - 50, RED)
            display_text(f"Final Score: {hit_count}", screen_width // 2 - 100, screen_height // 2)
            display_text("Press R to Restart", screen_width // 2 - 100, screen_height // 2 + 50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    if pygame.mixer.music:
                        pygame.mixer.music.stop()
                        print("Background music stopped (quit)")
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        setup()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
