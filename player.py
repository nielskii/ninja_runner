import pygame
from settings import NINJA_TELA_X, GROUND_Y, TAMANHO_NINJA, FORCA_PULO, GRAVIDADE

class Player:
    def __init__(self):
        self.x = NINJA_TELA_X
        self.y = GROUND_Y - TAMANHO_NINJA[1]
        self.velocity_y = 0
        self.no_chao = False
        self.vidas = 8
        self.max_vidas = 8
        self.atacando = False
        self.invisivel = False
        self.teleportando = False
        self.invencivel = False
        self.tempo_invencivel = 0
        self.invisivel_timer = 0
        self.invisivel_cooldown = 0
        self.anim_idx = 0
        self.ataque_frame_atual = 0
        self.movendo = False
        self.vivo = True

    def pular(self, som_pulo=None):
        if self.no_chao:
            self.velocity_y = FORCA_PULO
            self.no_chao = False
            if som_pulo:
                try: som_pulo.play()
                except: pass

    def atacar(self):
        if not self.atacando:
            self.atacando = True
            if self.invisivel:
                self.ataque_frame_atual = 0
            else:
                self.anim_idx = 0

    def ativar_invisibilidade(self):
        if not self.invisivel and self.invisivel_cooldown <= 0:
            self.invisivel = True
            self.invisivel_timer = 300
            self.anim_idx = 0

    def teleportar(self, som_tp=None):
        self.teleportando = True
        self.anim_idx = 0
        if som_tp:
            try: som_tp.play()
            except: pass

    def update_fisica(self):
        self.velocity_y += GRAVIDADE
        self.y += self.velocity_y
        if self.y >= GROUND_Y - TAMANHO_NINJA[1]:
            self.y = GROUND_Y - TAMANHO_NINJA[1]
            self.velocity_y = 0
            self.no_chao = True

    def update_invisibilidade(self):
        if self.invisivel:
            self.invisivel_timer -= 1
            if self.invisivel_timer <= 0:
                self.invisivel = False
                self.invisivel_cooldown = 600
        if self.invisivel_cooldown > 0 and not self.invisivel:
            self.invisivel_cooldown -= 1

    def update_invencibilidade(self):
        if self.invencivel:
            self.tempo_invencivel -= 1
            if self.tempo_invencivel <= 0:
                self.invencivel = False

    def tomar_dano(self, dano):
        if not self.invencivel and not self.invisivel:
            self.vidas -= dano
            self.invencivel = True
            self.tempo_invencivel = 60
            if self.vidas <= 0:
                self.vivo = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, TAMANHO_NINJA[0], TAMANHO_NINJA[1])

    def get_ataque_rect(self):
        return pygame.Rect(self.x + 50, self.y, 70, TAMANHO_NINJA[1])
