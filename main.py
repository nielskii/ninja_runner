import math
import pygame
import random
import sys
import os

# Função para resolver o caminho dos assets
def resource_path(relative_path):
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from settings import *
from settings import TAMANHO_NINJA_ATK
from assets import carregar_todas_assets
from player import Player
from enemies import Orc, Archer, MartialBoss, Coin, Trap, Chest

# --- Globals ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ninja Runner - Uninter")
clock = pygame.time.Clock()
assets = carregar_todas_assets()
font_score = pygame.font.SysFont("arial", 24)

current_state = STATE_MENU
running = True
transicao = False
transicao_timer = 0
nivel_anterior = LEVEL_ORC

# Gameplay objects
player = None
inimigos = []
coins = []
traps = []
decoracoes = []
bau = None
flechas_inimigas = []
posicoes_fundo = [0] * 6
score = 0
tempo_score = 0
coins_coletadas = 0
current_level = LEVEL_ORC
musica_tocando = False

# Menu
index_menu = 0
hover_botao = False
rect_jogar = pygame.Rect(0, 0, 300, 80)

# Polish: hover tracking
hovered_prev = False
hover_sound_cooldown = 0
settings_hovered = False
menu_elapsed = 0.0

# Polish: modal
show_modal = False
MODAL_W, MODAL_H = 540, 420
MODAL_X = (SCREEN_WIDTH - MODAL_W) // 2
MODAL_Y = (SCREEN_HEIGHT - MODAL_H) // 2
modal_rect = pygame.Rect(MODAL_X, MODAL_Y, MODAL_W, MODAL_H)
modal_close_rect = pygame.Rect(MODAL_X + MODAL_W - 32, MODAL_Y + 8, 24, 24)
modal_close_hovered = False

# Polish: music flags
game_over_music_played = False
win_music_played = False

# Polish: settings button
settings_rect = pygame.Rect(SCREEN_WIDTH - 65, 15, 50, 50)

# --- Audio ---
def play_music():
    global musica_tocando
    caminho = assets.get('musica')
    if caminho and not musica_tocando:
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play(-1)
            musica_tocando = True
        except:
            pass

def stop_music():
    global musica_tocando
    try:
        pygame.mixer.music.stop()
        musica_tocando = False
    except:
        pass

def play_sound(nome):
    som = assets.get(nome)
    if som:
        try: som.play()
        except: pass

def play_sound_vol(nome, vol=1.0):
    som = assets.get(nome)
    if som:
        try:
            som.set_volume(vol)
            som.play()
        except:
            pass

# --- Spawn ---
def spawn_enemy(level):
    global inimigos
    inimigos.clear()
    if level == LEVEL_ORC:
        inimigos.append(Orc(SCREEN_WIDTH + 100, GROUND_Y - TAMANHO_ORC[1]))
    elif level == LEVEL_ARCHER:
        inimigos.append(Archer(SCREEN_WIDTH + 200, GROUND_Y - TAMANHO_ARCHER[1]))
    elif level == LEVEL_BOSS:
        inimigos.append(MartialBoss(SCREEN_WIDTH + 100, GROUND_Y - TAMANHO_MARTIAL[1]))

def spawn_coins():
    global coins
    if len(coins) >= 3:
        return
    if random.random() > 0.005:
        return
    coin_frames = assets.get('coin_frames')
    if coin_frames:
        coins.append(Coin(SCREEN_WIDTH + 50, GROUND_Y - 100, coin_frames))

def spawn_traps(level):
    global traps
    if level == LEVEL_ORC:
        return
    if random.random() > 0.004:
        return
    img = assets.get('trap_spikes')
    if img:
        traps.append(Trap(SCREEN_WIDTH + 50, GROUND_Y - 24, img))

def spawn_decoracoes():
    global decoracoes
    if random.random() > 0.008:
        return
    arvores = assets.get('trees')
    arbustos = assets.get('bushes')
    if arvores and random.random() < 0.6:
        escolha = random.choice(arvores)
        decoracoes.append({'img': escolha, 'x': SCREEN_WIDTH + 50, 'y': GROUND_Y - escolha.get_height()})
    elif arbustos:
        escolha = random.choice(arbustos)
        decoracoes.append({'img': escolha, 'x': SCREEN_WIDTH + 50, 'y': GROUND_Y - escolha.get_height()})

def spawnar_bau(x):
    global bau
    bau = Chest(x, GROUND_Y - 96)  # altura do bau = 96px

def update_level(scr):
    if scr >= SCORE_BOSS:
        return LEVEL_BOSS
    elif scr >= SCORE_ARCHER:
        return LEVEL_ARCHER
    return LEVEL_ORC

def remover_fora_tela():
    global inimigos, coins, traps, decoracoes
    inimigos = [e for e in inimigos if e.x > -300]
    coins = [c for c in coins if c.x > -50]
    traps = [t for t in traps if t.x > -50]
    decoracoes = [d for d in decoracoes if d['x'] > -200]

def scroll_all(dx):
    for e in inimigos:
        e.x += dx
    for c in coins:
        c.x += dx
    for t in traps:
        t.x += dx
    for d in decoracoes:
        d['x'] += dx
    if bau:
        bau.x += dx

# --- Combat ---
def check_player_attack():
    if not player.atacando:
        return None
    frame_atual = player.ataque_frame_atual if player.invisivel else int(player.anim_idx)
    if not (1 <= frame_atual <= 3):
        return None
    atk_rect = player.get_ataque_rect()
    for inimigo in inimigos[:]:
        altura = inimigo.tamanho[1]
        largura = inimigo.tamanho[0]
        ini_rect = pygame.Rect(inimigo.x, GROUND_Y - altura, largura, altura)
        if atk_rect.colliderect(ini_rect):
            inimigo.tomar_dano()
            return inimigo
    return None

def check_enemy_melee(inimigo):
    altura = inimigo.tamanho[1]
    ini_rect = pygame.Rect(inimigo.x, GROUND_Y - altura, inimigo.tamanho[0], altura)
    n_rect = pygame.Rect(NINJA_TELA_X, player.y, 120, 120)
    return ini_rect.colliderect(n_rect)

# --- Game State ---
def set_state(state):
    global current_state, transicao
    current_state = state

def start_game():
    global player, inimigos, coins, traps, decoracoes, bau, flechas_inimigas
    global posicoes_fundo, score, tempo_score, coins_coletadas, transicao, transicao_timer, current_level
    global index_menu, hover_botao, game_over_music_played, win_music_played
    game_over_music_played = False
    win_music_played = False
    player = Player()
    spawn_enemy(current_level)
    flechas_inimigas = []
    coins = []
    traps = []
    decoracoes = []
    bau = None
    score = 0
    tempo_score = 0
    coins_coletadas = 0
    transicao = False
    transicao_timer = 0
    posicoes_fundo = [0] * 6
    current_level = LEVEL_ORC
    play_music()
    set_state(STATE_PLAYING)

# --- Event Handling ---
def handle_menu_events(event):
    global hover_botao, rect_jogar, hovered_prev, show_modal
    global settings_hovered, modal_close_hovered

    if show_modal:
        handle_modal_events(event)
        return

    if event.type == pygame.MOUSEMOTION:
        hover_botao = rect_jogar.collidepoint(event.pos)
        settings_hovered = settings_rect.collidepoint(event.pos)

        hovered_now = hover_botao or settings_hovered
        if hovered_now and not hovered_prev:
            play_sound_vol('hover_sound', 0.7)
        hovered_prev = hovered_now

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if hover_botao:
            start_game()
        if settings_rect.collidepoint(event.pos):
            show_modal = True
            hovered_prev = False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            start_game()

def handle_modal_events(event):
    global show_modal, hovered_prev, modal_close_hovered

    if event.type == pygame.MOUSEMOTION:
        modal_close_hovered = modal_close_rect.collidepoint(event.pos)
        if modal_close_hovered and not hovered_prev:
            play_sound_vol('hover_sound', 0.7)
        hovered_prev = modal_close_hovered

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mx, my = event.pos
        if modal_close_rect.collidepoint(mx, my):
            show_modal = False
            hovered_prev = False
        elif not modal_rect.collidepoint(mx, my):
            show_modal = False
            hovered_prev = False

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        show_modal = False
        hovered_prev = False

def handle_gameplay_events(event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            player.pular(assets.get('som_pulo'))
        if event.key == pygame.K_j:
            player.atacar()
            play_sound('som_espada')
            play_sound('attack_sound')
        if event.key == pygame.K_k:
            player.ativar_invisibilidade()
        if event.key == pygame.K_l:
            player.teleportar(assets.get('som_teleporte'))
            for i in range(len(posicoes_fundo)):
                posicoes_fundo[i] -= 150
            scroll_all(-150)
    if event.type == pygame.KEYUP:
        if event.key == pygame.K_l:
            player.teleportando = False

def handle_gameover_events(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        start_game()

def handle_win_events(event):
    global win_music_played
    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        stop_music()
        win_music_played = False
        set_state(STATE_MENU)

# --- Update ---
def update_menu():
    global index_menu
    frames = assets.get('menu_frames')
    if frames:
        index_menu += 0.2
        if index_menu >= len(frames):
            index_menu = 0

def update_gameplay():
    global current_level, nivel_anterior, transicao, transicao_timer
    global posicoes_fundo, score, tempo_score, coins_coletadas, bau
    global flechas_inimigas, coins, traps, decoracoes, inimigos
    if player is None:
        return
    if not player.vivo:
        stop_music()
        set_state(STATE_GAME_OVER)
        return

    teclas = pygame.key.get_pressed()

    # Level transition
    if not transicao:
        nivel_anterior = current_level
        novo = update_level(score)
        if novo != current_level:
            current_level = novo
            transicao = True
            transicao_timer = 90
            spawn_enemy(current_level)
            for i in range(len(posicoes_fundo)):
                posicoes_fundo[i] = 0
        else:
            current_level = novo

    if transicao:
        transicao_timer -= 1
        if transicao_timer <= 0:
            transicao = False

    # Movement
    player.movendo = False
    if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
        player.movendo = True
        for i in range(len(posicoes_fundo)):
            posicoes_fundo[i] -= (i + 1) * 1
        scroll_all(-VELOCIDADE_NINJA)
        for flecha in flechas_inimigas:
            flecha['x'] -= VELOCIDADE_NINJA
    if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
        player.movendo = True
        for i in range(len(posicoes_fundo)):
            posicoes_fundo[i] += (i + 1) * 1
        scroll_all(VELOCIDADE_NINJA)
        for flecha in flechas_inimigas:
            flecha['x'] += VELOCIDADE_NINJA

    # Physics
    player.update_fisica()
    player.update_invisibilidade()
    player.update_invencibilidade()

    # Score
    tempo_score += 1
    if tempo_score >= 30:
        score += 1
        tempo_score = 0

    # Spawn
    spawn_coins()
    spawn_traps(current_level)
    spawn_decoracoes()

    # Enemies
    vel_ini = 2 + score // 600
    if current_level == LEVEL_BOSS:
        vel_ini += 2
    for inimigo in inimigos[:]:
        dano = inimigo.update(1, vel_ini, NINJA_TELA_X, player.y, player.no_chao)
        if dano:
            player.tomar_dano(2 if inimigo.enemy_type == ENEMY_MARTIAL else 1)
            if not player.vivo:
                stop_music()
        if inimigo.enemy_type == ENEMY_ARCHER:
            for f in inimigo.flechas:
                flechas_inimigas.append(f)
            inimigo.flechas.clear()

    # Enemy arrows
    for flecha in flechas_inimigas[:]:
        flecha['x'] += flecha['vel']
        f_rect = pygame.Rect(flecha['x'], flecha['y'], 20, 10)
        n_rect = player.get_rect()
        if f_rect.colliderect(n_rect) and not player.invencivel and not player.invisivel:
            player.tomar_dano(1)
            flechas_inimigas.remove(flecha)
            if not player.vivo:
                stop_music()
            continue
        if flecha['x'] < -50:
            flechas_inimigas.remove(flecha)

    # Coins
    for coin in coins[:]:
        coin.update(1)
        c_rect = coin.get_rect()
        n_rect = pygame.Rect(NINJA_TELA_X, player.y, 120, 120)
        if c_rect.colliderect(n_rect):
            score += 25
            coins_coletadas += 1
            coins.remove(coin)
        elif coin.is_off_screen():
            coins.remove(coin)

    # Traps
    for trap in traps[:]:
        trap.x -= vel_ini
        t_rect = trap.get_rect()
        n_rect = pygame.Rect(NINJA_TELA_X, player.y, 120, 120)
        if t_rect.colliderect(n_rect) and not player.invencivel:
            player.tomar_dano(1)
            traps.remove(trap)
            if not player.vivo:
                stop_music()
            continue
        if trap.is_off_screen():
            traps.remove(trap)

    # Combat
    hit = check_player_attack()
    if hit:
        if hit.is_morto():
            score += hit.get_score_value()
            if hit.enemy_type == ENEMY_MARTIAL:
                spawnar_bau(hit.x)
                stop_music()
            inimigos.remove(hit)

    # Spawn enemies if none
    if len(inimigos) == 0 and not (current_level == LEVEL_BOSS and bau):
        spawn_enemy(current_level)

    remover_fora_tela()

    # Chest
    if bau:
        bau.update(1)
        if bau.animacao_finalizada():
            set_state(STATE_WIN)

    # Death check at end
    if not player.vivo:
        stop_music()
        set_state(STATE_GAME_OVER)

# --- Render ---
def render_menu():
    global rect_jogar, settings_rect
    frames = assets.get('menu_frames')
    if frames and len(frames) > 0:
        screen.blit(frames[int(index_menu)], (0, 0))
    else:
        screen.fill((20, 20, 20))
    img_jogar = assets.get('img_jogar')
    if img_jogar:
        pulse = 1.0 + (0.08 * abs(math.sin(menu_elapsed * 3.0)) if hover_botao else 0.0)
        base_w, base_h = 320, 90
        w = int(base_w * pulse)
        h = int(base_h * pulse)
        img_destaque = pygame.transform.scale(img_jogar, (w, h))
        rect_jogar = img_destaque.get_rect(center=(SCREEN_WIDTH // 2, 350))
        screen.blit(img_destaque, rect_jogar)

    # Settings button
    img_settings = assets.get('settings_icon')
    if img_settings:
        s_pulse = 1.0 + (0.05 * abs(math.sin(menu_elapsed * 3.0)) if settings_hovered else 0.0)
        sw = int(50 * s_pulse)
        sh = int(50 * s_pulse)
        s_img = pygame.transform.scale(img_settings, (sw, sh))
        s_rect = s_img.get_rect(center=(SCREEN_WIDTH - 40, 40))
        settings_rect = s_rect
        screen.blit(s_img, s_rect)

    if show_modal:
        render_modal()

def render_modal():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    bg = assets.get('controls_bg')
    if bg:
        screen.blit(bg, (MODAL_X, MODAL_Y))
    else:
        pygame.draw.rect(screen, (30, 30, 50), modal_rect, border_radius=8)
    # Title
    fonte_tit = pygame.font.SysFont("arial bold", 26)
    titulo = fonte_tit.render("CONTROLES", True, (255, 255, 255))
    screen.blit(titulo, (MODAL_X + (MODAL_W - titulo.get_width()) // 2, MODAL_Y + 18))
    # Control images
    control_items = [
        ('img_mover', 1),
        ('img_atacar', 2),
        ('img_espaco', 3),
        ('img_invisibilidade', 4),
        ('img_teletransporte', 5),
    ]
    MAX_CTRL_W = 260
    start_y = MODAL_Y + 58
    row_h = 62
    for key, row in control_items:
        img = assets.get(key)
        if img:
            proporcao = MAX_CTRL_W / img.get_width()
            w = MAX_CTRL_W
            h = int(img.get_height() * proporcao)
            img_scaled = pygame.transform.scale(img, (w, h))
            x = MODAL_X + (MODAL_W - w) // 2
            y = start_y + (row - 1) * row_h
            screen.blit(img_scaled, (x, y))
    # Close button (X)
    cx, cy = MODAL_X + MODAL_W - 30, MODAL_Y + 10
    close_r = pygame.Rect(cx, cy, 22, 22)
    global modal_close_rect
    modal_close_rect = close_r
    color = (180, 40, 40) if modal_close_hovered else (120, 30, 30)
    pygame.draw.rect(screen, color, close_r, border_radius=4)
    pygame.draw.line(screen, (255, 255, 255), (cx + 5, cy + 5), (cx + 17, cy + 17), 2)
    pygame.draw.line(screen, (255, 255, 255), (cx + 17, cy + 5), (cx + 5, cy + 17), 2)

def render_gameplay():
    # Background
    camadas = {
        LEVEL_ORC: assets.get('bg_orc'),
        LEVEL_ARCHER: assets.get('bg_archer'),
        LEVEL_BOSS: assets.get('bg_boss'),
    }.get(current_level, [])
    for i, img in enumerate(camadas):
        while i >= len(posicoes_fundo):
            posicoes_fundo.append(0)
        if posicoes_fundo[i] <= -SCREEN_WIDTH:
            posicoes_fundo[i] = 0
        elif posicoes_fundo[i] >= SCREEN_WIDTH:
            posicoes_fundo[i] = 0
        screen.blit(img, (posicoes_fundo[i], 0))
        screen.blit(img, (posicoes_fundo[i] + SCREEN_WIDTH, 0))

    # Decorations
    for decoracao in decoracoes:
        screen.blit(decoracao['img'], (int(decoracao['x']), int(decoracao['y'])))

    # Traps
    spike_img = assets.get('trap_spikes')
    if spike_img:
        for trap in traps:
            trap.render(screen)

    # Coins
    for coin in coins:
        coin.render(screen)

    # Enemies
    for inimigo in inimigos:
        inimigo.render(screen, assets)

    # Enemy arrows
    for flecha in flechas_inimigas:
        pygame.draw.rect(screen, (200, 50, 50), (flecha['x'], flecha['y'], 20, 5))
        pygame.draw.polygon(screen, (200, 200, 200), [(flecha['x'] + 20, flecha['y'] + 2), (flecha['x'] + 25, flecha['y'] + 5), (flecha['x'] + 20, flecha['y'] + 8)])

    # Player
    if player:
        p = player
        if p.atacando and not p.invisivel:
            frames_atuais = assets.get('ninja_attack')
        elif p.invisivel:
            frames_atuais = assets.get('ninja_invisibility')
        elif p.teleportando:
            frames_atuais = assets.get('ninja_teleport')
        elif p.movendo and p.no_chao:
            frames_atuais = assets.get('ninja_run')
        else:
            frames_atuais = assets.get('ninja_idle')

        if frames_atuais and len(frames_atuais) > 0:
            if p.invisivel:
                p.anim_idx += 0.12
                if p.atacando:
                    p.ataque_frame_atual += 0.2
                    if p.ataque_frame_atual >= 6:
                        p.atacando = False
                        p.ataque_frame_atual = 0
                        teclas = pygame.key.get_pressed()
                        if teclas[pygame.K_j]:
                            p.atacando = True
                if p.anim_idx >= 14:
                    p.anim_idx = 11
            else:
                p.anim_idx += 0.2
                if p.anim_idx >= len(frames_atuais):
                    p.anim_idx = 0
                    if p.atacando:
                        p.atacando = False
                        teclas = pygame.key.get_pressed()
                        if teclas[pygame.K_j]:
                            p.atacando = True
                            p.anim_idx = 0

            img = frames_atuais[int(p.anim_idx) % len(frames_atuais)]
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                img = pygame.transform.flip(img, True, False)

            # centralizar horizontalmente caso o frame de ataque seja mais largo
            w = img.get_width()
            blit_x = NINJA_TELA_X - (w - TAMANHO_NINJA[0]) // 2
            blit_y = int(p.y) + (TAMANHO_NINJA[1] - img.get_height())

            if not (p.invencivel and int(p.tempo_invencivel / 5) % 2 == 0):
                screen.blit(img, (int(blit_x), int(blit_y)))

    # Chest
    if bau:
        bau.render(screen, assets.get('bau_fechado'), assets.get('bau_frames'), assets.get('bau_aberto'))

    # HUD
    if player:
        largura_barra = 200
        altura_barra = 20
        bx, by = 15, 15
        pygame.draw.rect(screen, GRAY, (bx, by, largura_barra, altura_barra), border_radius=4)
        proporcao = max(0, player.vidas / player.max_vidas)
        cor = GREEN if proporcao > 0.5 else (YELLOW if proporcao > 0.25 else RED)
        pygame.draw.rect(screen, cor, (bx, by, int(largura_barra * proporcao), altura_barra), border_radius=4)
        pygame.draw.rect(screen, LIGHT_GRAY, (bx, by, largura_barra, altura_barra), width=2, border_radius=4)
        by2 = by + altura_barra + 6
        if player.invisivel:
            proporcao = player.invisivel_timer / 300
            pygame.draw.rect(screen, GRAY, (bx, by2, largura_barra, 12), border_radius=3)
            pygame.draw.rect(screen, BLUE_BAR, (bx, by2, int(largura_barra * proporcao), 12), border_radius=3)
        elif player.invisivel_cooldown > 0:
            proporcao = player.invisivel_cooldown / 600
            pygame.draw.rect(screen, GRAY, (bx, by2, largura_barra, 12), border_radius=3)
            pygame.draw.rect(screen, COOLDOWN_RED, (bx, by2, int(largura_barra * (1 - proporcao)), 12), border_radius=3)
            txt = pygame.font.SysFont("arial", 10).render("RECARREGANDO", True, (255, 200, 200))
            screen.blit(txt, (bx + 4, by2 + 1))

    # HUD canto superior direito — score / fase / moedas (sem sobreposição)
    texto_score = font_score.render(f"Score: {score}", True, (255, 255, 200))
    screen.blit(texto_score, (SCREEN_WIDTH - texto_score.get_width() - 15, 12))

    nomes = ["Floresta Sombria", "Bosque Demoníaco", "Floresta Noturna"]
    idx = [LEVEL_ORC, LEVEL_ARCHER, LEVEL_BOSS].index(current_level)
    texto_fase = pygame.font.SysFont("arial", 16).render(nomes[idx], True, (200, 200, 200))
    screen.blit(texto_fase, (SCREEN_WIDTH - texto_fase.get_width() - 15, 38))

    # Moedas: ícone + contador numa terceira linha
    coin_frames = assets.get('coin_frames')
    coin_icon = coin_frames[0] if coin_frames else None
    txt_coins = font_score.render(f"x {coins_coletadas}", True, (255, 220, 50))
    ix = SCREEN_WIDTH - txt_coins.get_width() - 15 - (36 if coin_icon else 0)
    if coin_icon:
        screen.blit(coin_icon, (ix - 4, 58))
    screen.blit(txt_coins, (ix + (32 if coin_icon else 0), 61))

    # Transition overlay
    if transicao:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        nomes_fase = {
            LEVEL_ORC: "FASE 1 — Floresta Sombria",
            LEVEL_ARCHER: "FASE 2 — Bosque Demoníaco",
            LEVEL_BOSS: "FASE 3 — Floresta Noturna",
        }
        texto_nome = nomes_fase.get(current_level, "")
        fonte = pygame.font.SysFont("arial", 48)
        txt = fonte.render(texto_nome, True, (255, 255, 255))
        screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT // 2 - 30))

def render_gameover():
    global game_over_music_played
    if not game_over_music_played:
        stop_music()
        music_path = assets.get('game_over_music')
        if music_path:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            except:
                pass
        game_over_music_played = True
    img = assets.get('game_over')
    if img:
        screen.blit(img, (0, 0))
    else:
        screen.fill((0, 0, 0))
        txt = pygame.font.SysFont("arial", 64).render("GAME OVER", True, (255, 50, 50))
        screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
    alpha = int(120 + 135 * abs(math.sin(menu_elapsed * 2.5)))
    fonte = pygame.font.SysFont("arial", 28)
    txt_enter = fonte.render("PRESS ENTER", True, (255, 255, 255))
    txt_enter.set_alpha(alpha)
    screen.blit(txt_enter, (SCREEN_WIDTH // 2 - txt_enter.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

def render_win():
    global win_music_played
    if not win_music_played:
        stop_music()
        music_path = assets.get('win_music')
        if music_path:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.7)
                pygame.mixer.music.play(-1)
            except:
                pass
        win_music_played = True
    img = assets.get('vitoria')
    if img:
        screen.blit(img, (0, 0))
    else:
        screen.fill((0, 0, 0))
        txt = pygame.font.SysFont("arial", 64).render("VITÓRIA!", True, (255, 215, 0))
        screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
    alpha = int(120 + 135 * abs(math.sin(menu_elapsed * 2.5)))
    fonte = pygame.font.SysFont("arial", 28)
    txt_enter = fonte.render("PRESS ENTER", True, (255, 255, 255))
    txt_enter.set_alpha(alpha)
    screen.blit(txt_enter, (SCREEN_WIDTH // 2 - txt_enter.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

# --- Main Loop ---
def main():
    global running, menu_elapsed
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if current_state == STATE_MENU:
                handle_menu_events(event)
            elif current_state == STATE_PLAYING:
                handle_gameplay_events(event)
            elif current_state == STATE_GAME_OVER:
                handle_gameover_events(event)
            elif current_state == STATE_WIN:
                handle_win_events(event)

        if current_state == STATE_MENU:
            update_menu()
        elif current_state == STATE_PLAYING:
            update_gameplay()

        menu_elapsed += 0.05

        screen.fill((0, 0, 0))
        if current_state == STATE_MENU:
            render_menu()
        elif current_state == STATE_PLAYING:
            render_gameplay()
        elif current_state == STATE_GAME_OVER:
            render_gameover()
        elif current_state == STATE_WIN:
            render_win()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
