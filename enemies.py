import random
import pygame
from settings import GROUND_Y, TAMANHO_ORC, TAMANHO_DRAGON, TAMANHO_ARCHER, TAMANHO_MARTIAL, TAMANHO_NINJA_ATK, NINJA_TELA_X, SCREEN_WIDTH as LARGURA, ENEMY_WALKING, ENEMY_ATTACKING, ENEMY_RETREATING, ENEMY_ORC, ENEMY_ARCHER, ENEMY_MARTIAL

# --- Base Enemy ---

class Enemy:
    def __init__(self, x, y, vida, tamanho, enemy_type):
        self.x = x
        self.y = y
        self.vida = vida
        self.tamanho = tamanho
        self.enemy_type = enemy_type
        self.state = ENEMY_WALKING
        self.anim_idx = random.random() * 4
        self.attack_timer = 0
        self.hit_cooldown = 0
        self.atacou_frame = False

    def update(self, dt, vel_ini, player_x, player_y, no_chao):
        self.hit_cooldown = max(0, self.hit_cooldown - 1)

    def tomar_dano(self):
        self.vida -= 1

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.tamanho[0], self.tamanho[1])

    def is_morto(self):
        return self.vida <= 0

    def get_score_value(self):
        if self.enemy_type == ENEMY_ORC:
            return 50
        elif self.enemy_type == ENEMY_ARCHER:
            return 100
        elif self.enemy_type == ENEMY_MARTIAL:
            return 500
        return 0

    def render_health_bar(self, screen, y_offset=10, bar_width=60, bar_height=6):
        proporcao = max(0, self.vida / self.get_max_vida())
        pygame.draw.rect(screen, (60, 0, 0), (self.x + 10, self.y - y_offset, bar_width, bar_height))
        pygame.draw.rect(screen, (255, 0, 0), (self.x + 10, self.y - y_offset, int(bar_width * proporcao), bar_height))

    def get_max_vida(self):
        if self.enemy_type == ENEMY_ORC:
            return 2
        elif self.enemy_type == ENEMY_ARCHER:
            return 3
        elif self.enemy_type == ENEMY_MARTIAL:
            return 20
        return 1

# --- Orc ---

class Orc(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 2, TAMANHO_ORC, ENEMY_ORC)
        self.state = ENEMY_WALKING
        self.anim_idx = 0

    def update(self, dt, vel_ini, player_x, player_y, no_chao):
        super().update(dt, vel_ini, player_x, player_y, no_chao)
        if self.state == ENEMY_WALKING:
            self.x -= vel_ini
            self.anim_idx += 0.15
            dist = abs(self.x - NINJA_TELA_X)
            if dist < 120 and no_chao:
                self.state = ENEMY_ATTACKING
                self.anim_idx = 0
                self.atacou_frame = False
        elif self.state == ENEMY_ATTACKING:
            self.anim_idx += 0.15
            if 1 <= int(self.anim_idx) <= 2 and not self.atacou_frame:
                self.atacou_frame = True
                e_rect = pygame.Rect(self.x, GROUND_Y - TAMANHO_ORC[1], TAMANHO_ORC[0], TAMANHO_ORC[1])
                n_rect = pygame.Rect(NINJA_TELA_X, player_y, 120, 120)
                return e_rect.colliderect(n_rect)
            if self.anim_idx >= 4:
                self.state = ENEMY_WALKING
                self.anim_idx = 0
        return False

    def render(self, screen, assets):
        if self.state == ENEMY_ATTACKING:
            frames = assets.get('orc_attack')
        else:
            frames = assets.get('orc_run')
        idx = int(self.anim_idx) % max(len(frames), 1)
        img = frames[idx] if len(frames) > 0 else None
        if img:
            img = pygame.transform.flip(img, True, False)
            screen.blit(img, (int(self.x), GROUND_Y - TAMANHO_ORC[1]))
        if self.vida < 2:
            self.render_health_bar(screen, 10, 60, 6)

# --- Baby Dragon (substitui Archer) ---

class BabyDragon(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 5, TAMANHO_DRAGON, ENEMY_ARCHER)
        self.state = ENEMY_WALKING
        self.anim_idx = 0
        self.attack_timer = 90
        self.flechas = []   # bolas de fogo reutilizam a lista de flechas

    def update(self, dt, vel_ini, player_x, player_y, no_chao):
        super().update(dt, vel_ini, player_x, player_y, no_chao)
        dano = False
        if self.state == ENEMY_WALKING:
            self.x -= vel_ini * 0.6
            self.anim_idx = (self.anim_idx + 0.12) % 4   # cicla 0-3
            self.attack_timer = max(0, self.attack_timer - 1)
            dist = abs(self.x - NINJA_TELA_X)
            if 100 < dist < 380 and no_chao and self.attack_timer == 0:
                self.state = ENEMY_ATTACKING
                self.anim_idx = 0
                self.atacou_frame = False
                self.attack_timer = 50   # duração do ataque (frames)
        elif self.state == ENEMY_ATTACKING:
            self.anim_idx = (self.anim_idx + 0.18) % 2   # cicla 0-1 (2 frames de ataque)
            if int(self.anim_idx) == 1 and not self.atacou_frame:
                self.atacou_frame = True
                self.flechas.append({
                    'x': self.x - 30,
                    'y': GROUND_Y - TAMANHO_DRAGON[1] + 80,
                    'vel': -9,
                })
            # contar ciclos com attack_timer
            self.attack_timer = max(0, self.attack_timer - 1)
            if self.attack_timer == 0 and self.atacou_frame:
                self.state = ENEMY_WALKING
                self.anim_idx = 0
                self.attack_timer = 90
        return dano

    def render(self, screen, assets):
        if self.state == ENEMY_ATTACKING:
            frames = assets.get('dragon_attack') or []
        else:
            frames = assets.get('dragon_walk') or []
        if not frames:
            return
        idx = int(self.anim_idx) % len(frames)
        img = frames[idx]
        # dragon já está virado para esquerda no spritesheet — sem flip
        screen.blit(img, (int(self.x), GROUND_Y - TAMANHO_DRAGON[1]))
        self.render_health_bar(screen, 10, 80, 7)

# Alias para não quebrar o import em main.py
Archer = BabyDragon

# --- Martial Boss ---

class MartialBoss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 20, TAMANHO_MARTIAL, ENEMY_MARTIAL)
        self.state = ENEMY_WALKING
        self.anim_idx = 0
        self.attack_timer = 60
        self.pattern_timer = 0
        self.attack_pattern = 0

    def update(self, dt, vel_ini, player_x, player_y, no_chao):
        super().update(dt, vel_ini, player_x, player_y, no_chao)
        self.pattern_timer += 1
        dano = False
        if self.state == ENEMY_WALKING:
            self.anim_idx += 0.12
            target_x = NINJA_TELA_X + 150
            if self.x > target_x:
                self.x -= vel_ini * 1.5
            elif self.x < target_x - 50:
                self.x += 1
            if self.x < -300:
                self.x = LARGURA + 50
            self.attack_timer = max(0, self.attack_timer - 1)
            dist = abs(self.x - NINJA_TELA_X)
            if dist < 200 and no_chao and self.attack_timer == 0:
                if random.random() < 0.4:
                    self.state = ENEMY_ATTACKING
                    self.anim_idx = 0
                    self.atacou_frame = False
                    self.attack_pattern = random.randint(0, 1)
                else:
                    self.state = ENEMY_RETREATING
                    self.anim_idx = 0
        elif self.state == ENEMY_RETREATING:
            self.x += vel_ini * 2
            self.anim_idx += 0.12
            if self.x > LARGURA + 100:
                self.state = ENEMY_WALKING
                self.attack_timer = 30
        elif self.state == ENEMY_ATTACKING:
            speed = 0.15 if self.attack_pattern == 0 else 0.2
            self.anim_idx += speed
            frames_ataque = 6
            if 2 <= int(self.anim_idx) <= 4 and not self.atacou_frame:
                self.atacou_frame = True
                e_rect = pygame.Rect(self.x - 60, GROUND_Y - TAMANHO_MARTIAL[1], TAMANHO_MARTIAL[0] + 60, TAMANHO_MARTIAL[1])
                n_rect = pygame.Rect(NINJA_TELA_X, player_y, 120, 120)
                if e_rect.colliderect(n_rect):
                    dano = True
            if self.anim_idx >= frames_ataque:
                if random.random() < 0.5:
                    self.state = ENEMY_RETREATING
                else:
                    self.state = ENEMY_WALKING
                self.anim_idx = 0
                self.attack_timer = 60
        return dano

    def render(self, screen, assets):
        if self.state == ENEMY_ATTACKING:
            frames = assets.get('martial_attack1') if self.attack_pattern == 0 else assets.get('martial_attack2')
        elif self.state == ENEMY_RETREATING:
            frames = assets.get('martial_run')
        else:
            frames = assets.get('martial_run')
        idx = int(self.anim_idx) % max(len(frames), 1)
        img = frames[idx] if len(frames) > 0 else None
        if img:
            img = pygame.transform.flip(img, True, False)
            screen.blit(img, (int(self.x), GROUND_Y - TAMANHO_MARTIAL[1]))
        self.render_health_bar(screen, 14, 120, 10)

# --- Coin ---

class Coin:
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.anim_idx = 0
        self.frames = frames

    def update(self, dt):
        self.anim_idx += 0.15
        if self.anim_idx >= max(len(self.frames), 1):
            self.anim_idx = 0

    def render(self, screen):
        if len(self.frames) > 0:
            screen.blit(self.frames[int(self.anim_idx) % len(self.frames)], (int(self.x), int(self.y)))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 24, 24)

    def is_off_screen(self):
        return self.x < -50

# --- Trap ---

class Trap:
    def __init__(self, x, y, imagem):
        self.x = x
        self.y = y
        self.img = imagem

    def render(self, screen):
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 40, 24)

    def is_off_screen(self):
        return self.x < -50

# --- Chest ---

class Chest:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.aberto = False
        self.anim_idx = 0
        self.abrir_timer = 0

    def update(self, dt):
        if not self.aberto:
            self.abrir_timer += 1
            if self.abrir_timer >= 90:
                self.aberto = True
                self.anim_idx = 0
        else:
            self.anim_idx += 0.15

    def render(self, screen, bau_fechado, bau_frames, bau_aberto):
        if not self.aberto:
            if bau_fechado:
                screen.blit(bau_fechado, (int(self.x), int(self.y)))
        else:
            if bau_frames and int(self.anim_idx) < len(bau_frames):
                screen.blit(bau_frames[int(self.anim_idx)], (int(self.x), int(self.y)))
            elif bau_aberto:
                screen.blit(bau_aberto, (int(self.x), int(self.y)))

    def animacao_finalizada(self):
        return self.aberto and self.anim_idx >= 8
