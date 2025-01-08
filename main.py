import asyncio
import pygame
import time
import math
import random
from enum import Enum
from os.path import join
from random import randint, uniform
from math import sin, cos

class AnimatedText:
    def __init__(self, text, font, color, pos, size, animation_type='pulse'):
        self.font = pygame.font.Font(font, size)
        self.text = text
        self.color = color
        self.pos = pos
        self.scale = 1.0
        self.growing = True
        self.animation_type = animation_type
        self.angle = 0

    def update(self, dt):
        if self.animation_type == 'pulse':
            if self.growing:
                self.scale += dt
                if self.scale >= 1.1:
                    self.growing = False
            else:
                self.scale -= dt
                if self.scale <= 0.9:
                    self.growing = True
        elif self.animation_type == 'wave':
            self.angle += dt * 5
            self.scale = 1.0 + sin(self.angle) * 0.1

    def draw(self, surface):
        text_surface = self.font.render(self.text, True, self.color)
        scaled_surface = pygame.transform.rotozoom(text_surface, 0, self.scale)
        rect = scaled_surface.get_rect(center=self.pos)
        surface.blit(scaled_surface, rect)

class InstructionText:
    def __init__(self, text, font_path, color, pos, size=20):
        self.font = pygame.font.Font(font_path, size)
        self.text = text
        self.color = color
        self.pos = pos
        self.alpha = 255
        self.surface = self.font.render(text, True, color)
        self.rect = self.surface.get_rect(center=pos)
        
    def draw(self, surface):
        surface.blit(self.surface, self.rect)
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

class PowerUpType(Enum):
    INVINCIBILITY = 1
    RAPID_FIRE = 2
    SPEED_BOOST = 3

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.Vector2()
        self.base_speed = 300
        self.speed = self.base_speed
        self.original_image = self.image
        self.visible = True

        self.invincible = False
        self.rapid_fire = False
        self.speed_boosted = False
        self.power_up_end_time = {
            PowerUpType.INVINCIBILITY: 0,
            PowerUpType.RAPID_FIRE: 0,
            PowerUpType.SPEED_BOOST: 0
        }
        self.original_cooldown = 400
        self.rapid_fire_cooldown = 200

        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = self.original_cooldown

        self.angle = 0
        self.hover_offset = 0
        self.mask = pygame.mask.from_surface(self.image)

    def apply_power_up(self, power_up_type):
        duration = 5
        if power_up_type == PowerUpType.INVINCIBILITY:
            self.invincible = True
            self.power_up_end_time[PowerUpType.INVINCIBILITY] = time.time() + duration
        elif power_up_type == PowerUpType.RAPID_FIRE:
            self.rapid_fire = True
            self.cooldown_duration = self.rapid_fire_cooldown
            self.power_up_end_time[PowerUpType.RAPID_FIRE] = time.time() + duration
        elif power_up_type == PowerUpType.SPEED_BOOST:
            self.speed_boosted = True
            self.speed = self.base_speed * 2
            self.power_up_end_time[PowerUpType.SPEED_BOOST] = time.time() + duration

    def update_power_ups(self):
        current_time = time.time()
        if self.invincible and current_time > self.power_up_end_time[PowerUpType.INVINCIBILITY]:
            self.invincible = False
        if self.rapid_fire and current_time > self.power_up_end_time[PowerUpType.RAPID_FIRE]:
            self.rapid_fire = False
            self.cooldown_duration = self.original_cooldown
        if self.speed_boosted and current_time > self.power_up_end_time[PowerUpType.SPEED_BOOST]:
            self.speed_boosted = False
            self.speed = self.base_speed

    def animate_menu(self, dt):
        self.hover_offset = math.sin(time.time() * 5) * 10
        self.rect.centery = WINDOW_HEIGHT // 2 + self.hover_offset
        self.angle += 30 * dt
        self.image = pygame.transform.rotozoom(self.original_image, math.sin(self.angle * 0.5) * 5, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        if not self.visible:
            self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
            return

        self.update_power_ups()
        if self.invincible:
            if int(time.time() * 10) % 2:
                self.image = self.original_image
            else:
                self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
        else:
            self.image = self.original_image

        if game_state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            if self.direction.length() > 0:
                self.direction = self.direction.normalize()

            new_x = self.rect.centerx + self.direction.x * self.speed * dt
            new_y = self.rect.centery + self.direction.y * self.speed * dt

            new_x = max(self.rect.width // 2, min(WINDOW_WIDTH - self.rect.width // 2, new_x))
            new_y = max(self.rect.height // 2, min(WINDOW_HEIGHT - self.rect.height // 2, new_y))

            self.rect.center = (new_x, new_y)

            if keys[pygame.K_SPACE] and self.can_shoot:
                Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
                self.can_shoot = False
                self.laser_shoot_time = pygame.time.get_ticks()
                laser_sound.play()

            if not self.can_shoot:
                current_time = pygame.time.get_ticks()
                if current_time - self.laser_shoot_time >= self.cooldown_duration:
                    self.can_shoot = True

        elif game_state == GameState.MENU:
            self.animate_menu(dt)

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom=pos)
        self.speed = 400

    def update(self, dt):
        self.rect.centery -= self.speed * dt
        if self.rect.bottom < 0:
            self.kill()

class EnemyLaser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.image = pygame.transform.rotate(self.image, 180)
        self.rect = self.image.get_rect(midtop=pos)
        self.speed = 400

    def update(self, dt):
        self.rect.centery += self.speed * dt
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation_speed = randint(40, 80)
        self.rotation = 0
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
        
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

class EnemyShip(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'enemy.png')).convert_alpha()
        self.image = pygame.transform.rotate(self.image, 180)
        self.rect = self.image.get_rect(center=(randint(100, WINDOW_WIDTH - 100), -50))
        self.speed = 150
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.direction = self.direction.normalize()
        self.mask = pygame.mask.from_surface(self.image)
        
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 2000
        self.health = 2

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            AnimatedExplosion(explosion_frames, self.rect.center, all_sprites)
            self.kill()
            return True
        return False

    def shoot(self):
        if self.can_shoot:
            EnemyLaser(enemylaser_surf, self.rect.midbottom, (all_sprites, enemy_laser_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            laser_sound.play()

    def update(self, dt):
        if game_state == GameState.PLAYING:
            self.rect.center += self.direction * self.speed * dt
            
            if self.rect.left < 0 or self.rect.right > WINDOW_WIDTH:
                self.direction.x *= -1
            
            if self.rect.top > WINDOW_HEIGHT:
                self.kill()
            
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True
                self.shoot()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, power_type, groups):
        super().__init__(groups)
        self.type = power_type
        
        if power_type == PowerUpType.SPEED_BOOST:
            self.frames = get_frames(speed_boost_sheet)
        elif power_type == PowerUpType.RAPID_FIRE:
            self.frames = get_frames(rapid_fire_sheet)
        elif power_type == PowerUpType.INVINCIBILITY:
            self.frames = get_frames(invincibility_sheet)
        
        self.frame_index = 0
        self.animation_speed = 10
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        
        self.speed = 200
        self.mask = pygame.mask.from_surface(self.image)
    
    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
        self.mask = pygame.mask.from_surface(self.image)
    
    def update(self, dt):
        self.rect.y += self.speed * dt
        self.animate(dt)
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        explosion_sound.play()

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

class AnimatedText:
    def __init__(self, text, font, color, pos, size, animation_type):

        self.font = pygame.font.Font(font, size)
        self.text = text
        self.color = color
        self.pos = pos
        self.scale = 1.0
        self.growing = True
        
    def update(self, dt):
        if self.growing:
            self.scale += dt
            if self.scale >= 1.1:
                self.growing = False
        else:
            self.scale -= dt
            if self.scale <= 0.9:
                self.growing = True
                
    def draw(self, surface):
        text_surface = self.font.render(self.text, True, self.color)
        scaled_surface = pygame.transform.rotozoom(text_surface, 0, self.scale)
        rect = scaled_surface.get_rect(center=self.pos)
        surface.blit(scaled_surface, rect)

def get_frames(sprite_sheet, frame_count=4, scale=2):
    frame_width = sprite_sheet.get_width() // frame_count
    frame_height = sprite_sheet.get_height()
    frames = []
    
    for i in range(frame_count):
        surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        surface.blit(sprite_sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
        scaled_surface = pygame.transform.scale(surface, (frame_width * scale, frame_height * scale))
        frames.append(scaled_surface)
    
    return frames

def display_score(surface, score):
    text_surf = font.render(f"Score: {score}", True, (240, 240, 240))
    text_rect = text_surf.get_rect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    surface.blit(text_surf, text_rect)
    pygame.draw.rect(surface, (240, 240, 240), text_rect.inflate(20, 10).move(0, -8), 5, 10)

def draw_menu(surface):
    surface.fill('#3a2e3f')
    title_text.draw(surface)
    start_text.draw(surface)
    for instruction in menu_instructions:
        instruction.draw(surface)
    all_sprites.draw(surface)
    version_text.draw(surface)

def init_menu_text():
    global title_text, start_text, menu_instructions, version_text
    
    title_text = AnimatedText(
        "SPACE SHOOTER",
        join('fonts', 'PixelOperator8-Bold.ttf'),
        (240, 240, 240),
        (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4),
        80,
        'pulse'
    )

    
    start_text = AnimatedText(
        "Press ENTER to Start",
        join('fonts', 'PixelOperator8.ttf'),
        (200, 200, 200),
        (WINDOW_WIDTH // 2, WINDOW_HEIGHT * 4 // 5),
        40,
        'wave'
    )

    
    instructions = [
        "CONTROLS:",
        "Arrow Keys - Move Ship",
        "SPACE - Shoot Lasers",
        "",
        "POWER-UPS:",
        " Speed Boost",
        " Invincibility",
        " Rapid Fire"
    ]
    
    menu_instructions = []
    start_y = WINDOW_HEIGHT * 2 // 5
    for i, text in enumerate(instructions):
        instruction = InstructionText(
            text,
            join('fonts', 'PixelOperator8.ttf'),
            (200, 200, 200) if i == 0 or i == 4 else (180, 180, 180),
            (WINDOW_WIDTH // 2, start_y + i * 30)
        )
        menu_instructions.append(instruction)
    
    version_text = InstructionText(
        "v1.0",
        join('fonts', 'PixelOperator8.ttf'),
        (140, 140, 140),
        (WINDOW_WIDTH - 50, WINDOW_HEIGHT - 30),
        16
    )

def draw_game_over(surface):
    surface.fill('#3a2e3f')
    game_over_text.draw(surface)
    final_score_text = font.render(f"Final Score: {final_score}", True, (240, 240, 240))
    final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    surface.blit(final_score_text, final_score_rect)
    restart_text.draw(surface)
    all_sprites.draw(surface)

def reset_game():
    global all_sprites, meteor_sprites, laser_sprites, enemy_sprites, enemy_laser_sprites
    global power_up_sprites, player, final_score, score, game_state
    
    all_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()
    enemy_sprites = pygame.sprite.Group()
    enemy_laser_sprites = pygame.sprite.Group()
    power_up_sprites = pygame.sprite.Group()
    
    for i in range(20):
        Star(all_sprites, star_surf)
    player = Player(all_sprites)
    player.visible = True
    final_score = 0
    score = 0
    game_state = GameState.PLAYING
    return True

def game_over():
    global game_state, final_score
    player.visible = False
    final_score = score
    game_state = GameState.GAME_OVER

def collisions():
    global score, game_state

    power_up_hits = pygame.sprite.spritecollide(player, power_up_sprites, True, pygame.sprite.collide_mask)
    for power_up in power_up_hits:
        player.apply_power_up(power_up.type)

    if not player.invincible:
        if pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask):
            game_over()

        if pygame.sprite.spritecollide(player, enemy_sprites, True, pygame.sprite.collide_mask):
            game_over()

        if pygame.sprite.spritecollide(player, enemy_laser_sprites, True, pygame.sprite.collide_mask):
            game_over()

    for laser in laser_sprites:
        meteor_hits = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if meteor_hits:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            score += 50

        enemy_hits = pygame.sprite.spritecollide(laser, enemy_sprites, False)
        for enemy in enemy_hits:
            if enemy.take_damage(1):
                score += 100
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)

    for meteor in meteor_sprites:
        enemy_hits = pygame.sprite.spritecollide(meteor, enemy_sprites, False)
        for enemy in enemy_hits:
            if enemy.take_damage(1):
                AnimatedExplosion(explosion_frames, enemy.rect.center, all_sprites)
            meteor.kill()
            AnimatedExplosion(explosion_frames, meteor.rect.center, all_sprites)

async def main():
    global WINDOW_WIDTH, WINDOW_HEIGHT, display_surface, clock, font, font_Bold
    global title_text, start_text, game_over_text, restart_text
    global speed_boost_sheet, rapid_fire_sheet, invincibility_sheet
    global star_surf, meteor_surf, laser_surf, enemylaser_surf, explosion_frames
    global laser_sound, explosion_sound, game_music
    global all_sprites, meteor_sprites, laser_sprites, enemy_sprites
    global enemy_laser_sprites, power_up_sprites, player
    global game_state, score, final_score

    pygame.init()
    WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
    display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Space shooter')
    clock = pygame.time.Clock()

    font = pygame.font.Font(join('fonts', 'PixelOperator8.ttf'), 40)
    font_Bold = pygame.font.Font(join('fonts', 'PixelOperator8-Bold.ttf'), 30)

    title_text = AnimatedText("SPACE SHOOTER", join('fonts', 'PixelOperator8-Bold.ttf'),
                             (240, 240, 240), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3), 80,
                             'pulse')
    
    start_text = AnimatedText("Press ENTER to Start", join('fonts', 'PixelOperator8.ttf'),
                             (200, 200, 200), (WINDOW_WIDTH // 2, WINDOW_HEIGHT * 2 // 3), 40,
                             'wave')

    game_over_text = AnimatedText("GAME OVER", join('fonts', 'PixelOperator8-Bold.ttf'),
                                 (240, 240, 240), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3), 80,
                                 'pulse')

    restart_text = AnimatedText("Press ENTER to Restart", join('fonts', 'PixelOperator8.ttf'),
                               (200, 200, 200), (WINDOW_WIDTH // 2, WINDOW_HEIGHT * 3 // 4), 40,
                               'wave')

    speed_boost_sheet = pygame.image.load(join('images', 'speed_boost.png')).convert_alpha()
    rapid_fire_sheet = pygame.image.load(join('images', 'rapid_fire.png')).convert_alpha()
    invincibility_sheet = pygame.image.load(join('images', 'invincibility.png')).convert_alpha()
    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
    laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
    enemylaser_surf = pygame.image.load(join('images', 'enemylaser.png')).convert_alpha()
    explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

    laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
    laser_sound.set_volume(0.5)
    explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
    game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
    game_music.set_volume(0.4)
    game_music.play(-1)

    game_state = GameState.MENU
    score = 0
    final_score = 0
    reset_game()
    init_menu_text()

    enemy_spawn_event = pygame.event.custom_type()
    meteor_event = pygame.event.custom_type()
    power_up_event = pygame.event.custom_type()

    pygame.time.set_timer(enemy_spawn_event, 3000)
    pygame.time.set_timer(meteor_event, 1000)
    pygame.time.set_timer(power_up_event, 5000)

    running = True
    last_time = time.time()

    while running:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if game_state == GameState.MENU:
                        game_state = GameState.PLAYING
                    elif game_state == GameState.GAME_OVER:
                        game_state = GameState.PLAYING
                        reset_game()
            if game_state == GameState.PLAYING:
                if event.type == meteor_event:
                    if len(meteor_sprites) < 5:
                        x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                        Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))
                if event.type == enemy_spawn_event:
                    if len(enemy_sprites) < 3:
                        EnemyShip((all_sprites, enemy_sprites))
                if event.type == power_up_event:
                    if len(power_up_sprites) < 2:
                        power_type = random.choice(list(PowerUpType))
                        x = randint(50, WINDOW_WIDTH - 50)
                        PowerUp((x, -50), power_type, (all_sprites, power_up_sprites))

        
        if game_state == GameState.MENU:
            title_text.update(dt)
            start_text.update(dt)
            all_sprites.update(dt)
            draw_menu(display_surface)

        elif game_state == GameState.PLAYING:
            all_sprites.update(dt)
            collisions()
            display_surface.fill('#3a2e3f')
            display_score(display_surface, score)
            all_sprites.draw(display_surface)

        elif game_state == GameState.GAME_OVER:
            game_over_text.update(dt)
            restart_text.update(dt)
            all_sprites.update(dt)
            draw_game_over(display_surface)

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == '__main__':
    asyncio.run(main())