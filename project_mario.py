import pygame
import sys
import math
import array

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Platformer - 10 Level Edition")

SKY_BLUE = (107, 140, 255)
GREEN = (34, 177, 76)
BROWN = (139, 69, 19)
YELLOW = (255, 215, 0)
WHITE = (255, 255, 255)
GOLD = (255, 223, 0)
RED = (220, 20, 60)
PURPLE = (128, 0, 128)
DARK_GRAY = (50, 50, 50)

clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.8

def generate_sound(freq, duration=0.1, wave_type="square"):
    sample_rate = 22050
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    amplitude = 4000
    for i in range(num_samples):
        t = float(i) / sample_rate
        if wave_type == "square":
            val = amplitude if (math.sin(2 * math.pi * freq * t) >= 0) else -amplitude
        else:
            val = int(amplitude * math.sin(2 * math.pi * freq * t))
        buf[i] = val
    return pygame.mixer.Sound(buffer=buf)

SND_JUMP = generate_sound(440, 0.1)
SND_COIN = generate_sound(880, 0.15)
SND_STOMP = generate_sound(150, 0.12)
SND_POWERUP = generate_sound(600, 0.25)
SND_HURT = generate_sound(100, 0.3)
def create_player_sprite(is_big=False):
    w, h = (36, 48) if is_big else (28, 36)
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    scale = 1.3 if is_big else 1.0
    
    pygame.draw.rect(surface, RED, (0, 0, int(28*scale), int(8*scale)))
    pygame.draw.rect(surface, (255, 205, 148), (int(4*scale), int(8*scale), int(18*scale), int(10*scale)))
    pygame.draw.rect(surface, (0, 0, 0), (int(16*scale), int(10*scale), int(3*scale), int(4*scale)))
    pygame.draw.rect(surface, (100, 50, 0), (int(12*scale), int(14*scale), int(8*scale), int(3*scale)))
    pygame.draw.rect(surface, RED, (int(2*scale), int(18*scale), int(22*scale), int(8*scale)))
    pygame.draw.rect(surface, (30, 80, 200), (int(4*scale), int(22*scale), int(18*scale), int(12*scale)))
    pygame.draw.rect(surface, YELLOW, (int(6*scale), int(24*scale), int(3*scale), int(3*scale)))
    pygame.draw.rect(surface, YELLOW, (int(16*scale), int(24*scale), int(3*scale), int(3*scale)))
    return surface

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.is_big = False
        self.image = create_player_sprite(self.is_big)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.invulnerable_timer = 0

    def grow(self):
        if not self.is_big:
            self.is_big = True
            bottom = self.rect.bottom
            self.image = create_player_sprite(True)
            self.rect = self.image.get_rect(midbottom=(self.rect.centerx, bottom))

    def shrink(self):
        if self.is_big:
            self.is_big = False
            bottom = self.rect.bottom
            self.image = create_player_sprite(False)
            self.rect = self.image.get_rect(midbottom=(self.rect.centerx, bottom))
            self.invulnerable_timer = 60  # 1 second invulnerability

    def update(self, platforms):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        self.rect.x += self.vel_x
        block_hit_list = pygame.sprite.spritecollide(self, platforms, False)
        for block in block_hit_list:
            if self.vel_x > 0:
                self.rect.right = block.rect.left
            elif self.vel_x < 0:
                self.rect.left = block.rect.right

        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        self.on_ground = False

        block_hit_list = pygame.sprite.spritecollide(self, platforms, False)
        for block in block_hit_list:
            if self.vel_y > 0:
                self.rect.bottom = block.rect.top
                self.vel_y = 0
                self.on_ground = True
                # Move with horizontal platform
                if hasattr(block, 'speed_x'):
                    self.rect.x += block.speed_x
            elif self.vel_y < 0:
                self.rect.top = block.rect.bottom
                self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def jump(self):
        if self.on_ground:
            self.vel_y = -18.5 if self.is_big else -17.0
            SND_JUMP.play()

    def bounce(self):
        self.vel_y = -11
        SND_STOMP.play()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=GREEN, move_x=0):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.move_x = move_x
        self.speed_x = 2 if move_x > 0 else 0

    def update(self):
        if self.move_x > 0:
            self.rect.x += self.speed_x
            if self.rect.x > self.start_x + self.move_x or self.rect.x < self.start_x:
                self.speed_x *= -1

class Mushroom(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, RED, (0, 0, 20, 14))
        pygame.draw.circle(self.image, WHITE, (5, 5), 2)
        pygame.draw.circle(self.image, WHITE, (14, 5), 2)
        pygame.draw.rect(self.image, (255, 220, 180), (5, 12, 10, 8))
        self.rect = self.image.get_rect(topleft=(x, y))

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (8, 8), 8)
        pygame.draw.circle(self.image, GOLD, (8, 8), 5)
        self.rect = self.image.get_rect(center=(x, y))

class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.image, WHITE, (0, 0, 6, 60))
        pygame.draw.polygon(self.image, RED, [(6, 5), (30, 17), (6, 30)])
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, distance, enemy_type="goomba"):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((30, 26), pygame.SRCALPHA)
        
        if enemy_type == "goomba":
            pygame.draw.ellipse(self.image, BROWN, (0, 0, 30, 24))
            pygame.draw.circle(self.image, WHITE, (8, 8), 4)
            pygame.draw.circle(self.image, WHITE, (22, 8), 4)
            pygame.draw.circle(self.image, (0, 0, 0), (8, 8), 2)
            pygame.draw.circle(self.image, (0, 0, 0), (22, 8), 2)
        elif enemy_type == "koopa":
            pygame.draw.ellipse(self.image, GREEN, (0, 0, 30, 24))
            pygame.draw.circle(self.image, WHITE, (22, 6), 5)
            pygame.draw.circle(self.image, (0, 0, 0), (22, 6), 2)
        elif enemy_type == "spiky":
            pygame.draw.ellipse(self.image, RED, (0, 6, 30, 20))
            # Spikes
            pygame.draw.polygon(self.image, WHITE, [(5, 6), (9, 0), (13, 6)])
            pygame.draw.polygon(self.image, WHITE, [(17, 6), (21, 0), (25, 6)])

        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.distance = distance
        self.speed = 3 if enemy_type == "koopa" else 2

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > self.start_x + self.distance or self.rect.x < self.start_x:
            self.speed *= -1

LEVELS = [
     # Level 1:
    {
        "platforms": [Platform(0, 550, 800, 50), Platform(200, 420, 160, 20, BROWN), Platform(450, 310, 160, 20, BROWN)],
        "coins": [(230, 380), (280, 380), (480, 270), (530, 270)],
        "mushrooms": [(490, 290)],
        "enemies": [Enemy(460, 284, 120, "goomba")],
        "flag_pos": (730, 490)
    },
    # Level 2:
    {
        "platforms": [
            Platform(0, 550, 250, 50), Platform(550, 550, 250, 50),
            Platform(270, 430, 100, 20, BROWN, move_x=160), Platform(150, 280, 140, 20, BROWN)
        ],
        "coins": [(180, 240), (220, 240), (600, 510), (650, 510)],
        "mushrooms": [(160, 260)],
        "enemies": [Enemy(570, 524, 180, "koopa")],
        "flag_pos": (720, 490)
    },
    # Level 3:
    {
        "platforms": [
            Platform(0, 550, 800, 50), Platform(150, 420, 130, 20, BROWN),
            Platform(350, 320, 130, 20, BROWN), Platform(550, 220, 130, 20, BROWN)
        ],
        "coins": [(180, 380), (380, 280), (580, 180)],
        "mushrooms": [],
        "enemies": [Enemy(360, 294, 100, "spiky"), Enemy(200, 524, 400, "goomba")],
        "flag_pos": (700, 490)
    },
    # Level 4:
    {
        "platforms": [
            Platform(0, 550, 150, 50), Platform(230, 450, 100, 20, BROWN),
            Platform(400, 350, 100, 20, BROWN), Platform(570, 250, 100, 20, BROWN),
            Platform(700, 180, 100, 20, GREEN)
        ],
        "coins": [(260, 410), (430, 310), (600, 210)],
        "mushrooms": [(240, 430)],
        "enemies": [Enemy(410, 324, 70, "goomba")],
        "flag_pos": (740, 120)
    },
    # Level 5:
    {
        "platforms": [
            Platform(0, 550, 200, 50), Platform(220, 420, 90, 20, BROWN, move_x=120),
            Platform(460, 300, 90, 20, BROWN, move_x=120), Platform(680, 200, 120, 20, GREEN)
        ],
        "coins": [(250, 370), (490, 250), (720, 150), (760, 150)],
        "mushrooms": [(700, 180)],
        "enemies": [Enemy(20, 524, 140, "koopa")],
        "flag_pos": (740, 140)
    },
    # Level 6:
    {
        "platforms": [
            Platform(0, 550, 800, 50), Platform(100, 400, 600, 20, DARK_GRAY)
        ],
        "coins": [(200, 360), (300, 360), (400, 360), (500, 360), (600, 360)],
        "mushrooms": [(120, 380)],
        "enemies": [Enemy(150, 374, 150, "spiky"), Enemy(400, 374, 150, "spiky"), Enemy(200, 524, 300, "koopa")],
        "flag_pos": (730, 490)
    },
    # Level 7:
    {
        "platforms": [
            Platform(0, 550, 120, 50), Platform(180, 460, 80, 20, BROWN),
            Platform(320, 370, 80, 20, BROWN), Platform(460, 280, 80, 20, BROWN),
            Platform(600, 190, 80, 20, BROWN), Platform(720, 120, 80, 20, GREEN)
        ],
        "coins": [(200, 420), (340, 330), (480, 240), (620, 150)],
        "mushrooms": [(330, 350)],
        "enemies": [Enemy(185, 434, 60, "goomba"), Enemy(465, 254, 60, "goomba")],
        "flag_pos": (740, 60)
    },
    # Level 8:
    {
        "platforms": [
            Platform(0, 550, 300, 50), Platform(380, 550, 420, 50),
            Platform(150, 380, 180, 20, BROWN), Platform(450, 380, 180, 20, BROWN)
        ],
        "coins": [(180, 340), (240, 340), (480, 340), (540, 340)],
        "mushrooms": [(160, 360)],
        "enemies": [Enemy(20, 524, 200, "koopa"), Enemy(400, 524, 250, "spiky"), Enemy(460, 354, 140, "goomba")],
        "flag_pos": (740, 490)
    },
    # Level 9:
    {
        "platforms": [
            Platform(0, 550, 150, 50), Platform(200, 450, 100, 20, PURPLE, move_x=100),
            Platform(420, 330, 100, 20, PURPLE, move_x=100), Platform(200, 210, 120, 20, BROWN),
            Platform(600, 150, 150, 20, GREEN)
        ],
        "coins": [(220, 170), (260, 170), (630, 110), (670, 110)],
        "mushrooms": [(210, 190)],
        "enemies": [Enemy(210, 184, 90, "spiky")],
        "flag_pos": (700, 90)
    },
    # Level 10:
    {
        "platforms": [
            Platform(0, 550, 120, 50), Platform(160, 450, 80, 20, BROWN, move_x=100),
            Platform(380, 360, 100, 20, DARK_GRAY), Platform(540, 260, 90, 20, BROWN, move_x=100),
            Platform(300, 170, 120, 20, PURPLE), Platform(700, 550, 100, 50, GREEN)
        ],
        "coins": [(400, 320), (430, 320), (330, 130), (360, 130)],
        "mushrooms": [(310, 150)],
        "enemies": [Enemy(390, 334, 70, "spiky"), Enemy(310, 144, 90, "koopa")],
        "flag_pos": (730, 490)
    }
]

current_level_idx = 0
score = 0
lives = 3
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 64)

all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()
coins = pygame.sprite.Group()
mushrooms = pygame.sprite.Group()
enemies = pygame.sprite.Group()
flags = pygame.sprite.Group()
player = Player(50, 450)

def load_level(level_idx):
    all_sprites.empty()
    platforms.empty()
    coins.empty()
    mushrooms.empty()
    enemies.empty()
    flags.empty()

    player.rect.topleft = (50, 450)
    player.vel_x = 0
    player.vel_y = 0
    all_sprites.add(player)

    data = LEVELS[level_idx]
    for p in data["platforms"]:
        platforms.add(p)
        all_sprites.add(p)

    for cx, cy in data["coins"]:
        c = Coin(cx, cy)
        coins.add(c)
        all_sprites.add(c)

    for mx, my in data.get("mushrooms", []):
        m = Mushroom(mx, my)
        mushrooms.add(m)
        all_sprites.add(m)

    for e in data["enemies"]:
        enemies.add(e)
        all_sprites.add(e)

    flag = Flag(*data["flag_pos"])
    flags.add(flag)
    all_sprites.add(flag)

load_level(current_level_idx)

running = True
game_won = False
game_over = False

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN and not game_won and not game_over:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                player.vel_x = -5
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                player.vel_x = 5
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                player.jump()

        if event.type == pygame.KEYUP and not game_won and not game_over:
            if event.key in (pygame.K_LEFT, pygame.K_a) and player.vel_x < 0:
                player.vel_x = 0
            if event.key in (pygame.K_RIGHT, pygame.K_d) and player.vel_x > 0:
                player.vel_x = 0
                
        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                lives = 3
                score = 0
                current_level_idx = 0
                game_over = False
                player.is_big = False
                player.image = create_player_sprite(False)
                load_level(current_level_idx)

    if not game_won and not game_over:
        player.update(platforms)
        platforms.update()
        enemies.update()

        for coin in pygame.sprite.spritecollide(player, coins, True):
            score += 10
            SND_COIN.play()

        for shroom in pygame.sprite.spritecollide(player, mushrooms, True):
            score += 50
            player.grow()
            SND_POWERUP.play()

        enemy_hits = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in enemy_hits:
            if player.vel_y > 0 and player.rect.bottom <= enemy.rect.top + 15 and enemy.enemy_type != "spiky":
                enemy.kill()
                player.bounce()
                score += 50
            elif player.invulnerable_timer == 0:
                # Player takes damage
                if player.is_big:
                    player.shrink()
                    SND_HURT.play()
                else:
                    lives -= 1
                    SND_HURT.play()
                    if lives <= 0:
                        game_over = True
                    else:
                        load_level(current_level_idx)
                break

        if pygame.sprite.spritecollide(player, flags, False):
            if current_level_idx + 1 < len(LEVELS):
                current_level_idx += 1
                load_level(current_level_idx)
            else:
                game_won = True

        if player.rect.top > SCREEN_HEIGHT:
            lives -= 1
            SND_HURT.play()
            if lives <= 0:
                game_over = True
            else:
                load_level(current_level_idx)

    screen.fill(SKY_BLUE)
    all_sprites.draw(screen)

    score_txt = font.render(f"Score: {score}", True, WHITE)
    level_txt = font.render(f"Level: {current_level_idx + 1}/{len(LEVELS)}", True, WHITE)
    lives_txt = font.render(f"Lives: {'<3 ' * lives}", True, RED)
    
    screen.blit(score_txt, (10, 10))
    screen.blit(level_txt, (10, 40))
    screen.blit(lives_txt, (10, 70))

    if game_won:
        win_txt = large_font.render("VICTORY! ALL 10 LEVELS CLEAR!", True, YELLOW)
        screen.blit(win_txt, (60, 260))
    elif game_over:
        over_txt = large_font.render("GAME OVER", True, RED)
        restart_txt = font.render("Press 'R' to Restart", True, WHITE)
        screen.blit(over_txt, (260, 240))
        screen.blit(restart_txt, (300, 310))

    pygame.display.flip()

pygame.quit()
sys.exit()