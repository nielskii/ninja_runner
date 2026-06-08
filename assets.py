import os
import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TAMANHO_NINJA, TAMANHO_NINJA_ATK, TAMANHO_ORC, TAMANHO_DRAGON, TAMANHO_ARCHER, TAMANHO_MARTIAL

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def carregar_spritesheet(caminho, colunas, linhas, escala):
    frames = []
    caminho_real = resource_path(caminho)
    if not os.path.exists(caminho_real):
        return frames
    sheet = pygame.image.load(caminho_real).convert_alpha()
    largura_total = sheet.get_width()
    altura_total = sheet.get_height()
    largura_frame = largura_total // colunas
    altura_frame = altura_total // linhas
    for linha in range(linhas):
        for coluna in range(colunas):
            x = coluna * largura_frame
            y = linha * altura_frame
            rect = pygame.Rect(x, y, largura_frame, altura_frame)
            frame = sheet.subsurface(rect)
            frame = pygame.transform.scale(frame, escala)
            frames.append(frame)
    return frames

def carregar_animacao_pasta(caminho, escala):
    frames = []
    caminho_real = resource_path(caminho)
    if not os.path.exists(caminho_real):
        return frames
    for arquivo in sorted(os.listdir(caminho_real)):
        if arquivo.endswith('.png'):
            try:
                img = pygame.image.load(os.path.join(caminho_real, arquivo)).convert_alpha()
                img = pygame.transform.scale(img, escala)
                frames.append(img)
            except:
                pass
    return frames

def escalar_imagem(img, largura_max):
    proporcao = largura_max / img.get_width()
    novo_tamanho = (largura_max, int(img.get_height() * proporcao))
    return pygame.transform.scale(img, novo_tamanho)

def carregar_todas_assets():
    cache = {}

    def try_load(path, scale):
        try:
            img = pygame.image.load(resource_path(path)).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            return img
        except:
            return None

    def try_load_raw(path):
        try:
            return pygame.image.load(resource_path(path)).convert_alpha()
        except:
            return None

    def load_parallax(path, count):
        layers = []
        caminho_base = resource_path(path)
        if os.path.exists(caminho_base):
            for i in range(1, count + 1):
                for ext in ['.png', '.jpg']:
                    f = os.path.join(caminho_base, f"{i}{ext}")
                    if os.path.exists(f):
                        img = pygame.image.load(f).convert_alpha()
                        layers.append(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)))
                        break
        return layers

    def load_parallax_dark_forest():
        layers = []
        base = resource_path("assets/img/cenarios/dark_forest")
        for i in range(1, 6):
            f = os.path.join(base, f"dark_forest_{i}.png")
            if os.path.exists(f):
                img = pygame.image.load(f).convert_alpha()
                layers.append(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)))
        return layers

    def load_parallax_demon_woods():
        layers = []
        base = resource_path("assets/img/cenarios/parallax_demon_woods_pack/layers")
        nomes = [
            "parallax-demon-woods-bg.png",
            "parallax-demon-woods-far-trees.png",
            "parallax-demon-woods-mid-trees.png",
            "parallax-demon-woods-close-trees.png",
        ]
        if os.path.exists(base):
            for nome in nomes:
                f = os.path.join(base, nome)
                if os.path.exists(f):
                    img = pygame.image.load(f).convert_alpha()
                    layers.append(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)))
        return layers

    # Ninja
    cache['ninja_idle']         = carregar_animacao_pasta("assets/img/ninja/Idle", TAMANHO_NINJA)
    cache['ninja_run']          = carregar_animacao_pasta("assets/img/ninja/Move", TAMANHO_NINJA)
    cache['ninja_attack']       = carregar_animacao_pasta("assets/img/ninja/Attack1", TAMANHO_NINJA_ATK)
    cache['ninja_invisibility'] = carregar_animacao_pasta("assets/img/ninja/Invisibility", TAMANHO_NINJA)
    cache['ninja_teleport']     = carregar_animacao_pasta("assets/img/ninja/Teleport1", TAMANHO_NINJA)

    # Enemies
    cache['orc_run'] = carregar_spritesheet("assets/img/inimigo/orc/_Run.png", 10, 1, TAMANHO_ORC)
    cache['orc_attack'] = carregar_spritesheet("assets/img/inimigo/orc/_Attack.png", 4, 1, TAMANHO_ORC)

    dragon_frames = carregar_spritesheet("assets/img/inimigo/Baby Dragon 2D.png", 2, 2, TAMANHO_DRAGON)
    cache['dragon_walk']   = dragon_frames
    cache['dragon_attack'] = dragon_frames[2:]

    cache['martial_idle'] = carregar_spritesheet("assets/img/inimigo/Martial Hero/Sprites/Idle.png", 8, 1, TAMANHO_MARTIAL)
    cache['martial_run'] = carregar_spritesheet("assets/img/inimigo/Martial Hero/Sprites/Run.png", 8, 1, TAMANHO_MARTIAL)
    cache['martial_attack1'] = carregar_spritesheet("assets/img/inimigo/Martial Hero/Sprites/Attack1.png", 6, 1, TAMANHO_MARTIAL)
    cache['martial_attack2'] = carregar_spritesheet("assets/img/inimigo/Martial Hero/Sprites/Attack2.png", 6, 1, TAMANHO_MARTIAL)

    # Menu
    cache['menu_frames'] = carregar_animacao_pasta("assets/img/principal_hero", (SCREEN_WIDTH, SCREEN_HEIGHT))
    cache['game_over'] = try_load("assets/img/principal_hero/game_over/game_over.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    cache['vitoria'] = try_load("assets/img/principal_hero/win/vitoria.png", (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Controls
    cache['img_jogar'] = try_load("assets/img/principal_hero/controles/jogar-Photoroom.png", (300, 80))
    cache['img_mover'] = try_load("assets/img/principal_hero/controles/mover-Photoroom.png", None)
    cache['img_atacar'] = try_load("assets/img/principal_hero/controles/atacar-Photoroom.png", None)
    cache['img_espaco'] = try_load("assets/img/principal_hero/controles/espaço-Photoroom.png", None)

    # Environment
    spikes = try_load_raw("assets/img/desafios/traps/Spike Trap.png")
    if spikes:
        tw = spikes.get_width() // 14
        th = spikes.get_height()
        if tw > 0 and th > 0:
            cache['trap_spikes'] = pygame.transform.scale(spikes.subsurface(0, 0, tw, th), (40, 24))
    
    trees = []
    pasta_t = resource_path("assets/img/desafios/3 Objects/Trees")
    if os.path.exists(pasta_t):
        for arquivo in sorted(os.listdir(pasta_t)):
            if arquivo.endswith('.png'):
                img = pygame.image.load(os.path.join(pasta_t, arquivo)).convert_alpha()
                img = escalar_imagem(img, 200)
                trees.append(img)
    cache['trees'] = trees
    
    bushes = []
    pasta_b = resource_path("assets/img/desafios/3 Objects/Bushes")
    if os.path.exists(pasta_b):
        for arquivo in sorted(os.listdir(pasta_b)):
            if arquivo.endswith('.png'):
                img = pygame.image.load(os.path.join(pasta_b, arquivo)).convert_alpha()
                img = escalar_imagem(img, 100)
                bushes.append(img)
    cache['bushes'] = bushes

    # Parallax
    cache['bg_orc'] = load_parallax_dark_forest()
    cache['bg_archer'] = load_parallax_demon_woods()
    cache['bg_boss'] = load_parallax("assets/img/cenarios/NightForest/Layers", 6)

    # Audio
    def try_sound(path):
        try:
            return pygame.mixer.Sound(resource_path(path))
        except:
            return None
            
    cache['som_pulo'] = try_sound("assets/audio/pulo.wav")
    cache['som_espada'] = try_sound("assets/audio/espada.wav")
    cache['som_teleporte'] = try_sound("assets/audio/teleporte.wav")
    cache['musica'] = resource_path("assets/audio/Epic Japanese Battle-Shamisen Boss Battle 1.wav")

    # Chest
    cache['bau_frames'] = carregar_animacao_pasta("assets/img/premio/Chest/Open/NoDust", (192, 96))
    cache['bau_aberto'] = try_load("assets/img/premio/Chest/ChestOpen.png", (192, 96))
    cache['bau_fechado'] = try_load("assets/img/premio/Chest/Chest.png", (192, 96))

    # Coins
    coin_frames = []
    pasta_coins = resource_path("assets/img/premio/Animated Coins")
    if os.path.exists(pasta_coins):
        for arquivo in sorted(os.listdir(pasta_coins)):
            if arquivo.endswith('.png'):
                try:
                    img = pygame.image.load(os.path.join(pasta_coins, arquivo)).convert_alpha()
                    h = img.get_height()
                    cx = (img.get_width() - h) // 2
                    cx = max(0, cx)
                    frame = img.subsurface(pygame.Rect(cx, 0, h, h)).copy()
                    frame = pygame.transform.scale(frame, (32, 32))
                    coin_frames.append(frame)
                except:
                    pass
    cache['coin_frames'] = coin_frames

    # Polish: sounds
    cache['hover_sound'] = try_sound("assets/audio/UI_button11.wav")
    cache['attack_sound'] = try_sound("assets/audio/UI_button20.wav")
    cache['game_over_music'] = resource_path("assets/audio/Naruto_Soundtrack_Sadness_and_Sorrow.wav")
    cache['win_music'] = resource_path("assets/audio/Naruto_Main_Theme.wav")

    # Polish: settings / modal
    cache['settings_icon'] = try_load("assets/img/principal_hero/controles/settings-bg.png", (50, 50))
    cache['controls_bg'] = try_load("assets/img/principal_hero/controles/background.png", (540, 420))
    cache['img_invisibilidade'] = try_load("assets/img/principal_hero/controles/invisibilidade.png", None)
    cache['img_teletransporte'] = try_load("assets/img/principal_hero/controles/teletransporte.png", None)

    return cache