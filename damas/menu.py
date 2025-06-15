from jogo import WIDTH, HEIGHT
import pygame
import sys
import math
import time 
# bibliotecas e constantes inportadas

menu_bg = pygame.image.load('assets/menu_background.jpg')
menu_bg = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))
# carrega a imagem de fundo

pygame.init() # inicia a janela do menu

WIDTH, HEIGHT = 800, 600
display = pygame.display.set_mode((WIDTH, HEIGHT)) # define altura e largura
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
LIGHT_RED = (255, 50, 50) # define cores


# fontes
title_font = pygame.font.Font('fonts/MinhaFonte.ttf', 60)
small_font = pygame.font.Font('fonts/FonteDamas.ttf', 14)

def text_objects(text, font, color):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()
# cria a superfície de texto com fonte e cor

# desenha um botão retangular na tela.
def create_button(msg, rect, color, hover_color, text_color):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)
    pygame.draw.rect(display, hover_color if is_hovered else color, rect, border_radius=10)

    lines = msg.split('\n')
    total_height = len(lines) * small_font.get_height()
    y_offset = rect.centery - total_height // 2

    for line in lines:
        text_surf = small_font.render(line, True, text_color)
        text_rect = text_surf.get_rect(center=(rect.centerx, y_offset + small_font.get_height() // 2))
        display.blit(text_surf, text_rect)
        y_offset += small_font.get_height()

# desenha o título do jogo letra por letra com o efeito de onda
def draw_wave_text_with_outline_centered(text, font, text_color, outline_color, x_center, y, surface, offset):
    spacing = 5 
    letters = []
    
    
    for i, char in enumerate(text):
        surf = font.render(char, True, text_color)
        outline_surf = font.render(char, True, outline_color)
        wave_y = int(10 * math.sin(offset + i * 0.5))  
        letters.append((surf, outline_surf, wave_y))

    total_width = sum(s.get_width() for s, _, _ in letters) + spacing * (len(letters) - 1)
    start_x = x_center - total_width // 2
    
    x = start_x
    for surf, outline_surf, wave_y in letters:
        char_rect = surf.get_rect(topleft=(x, y + wave_y))
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline_rect = char_rect.move(dx, dy)
                    surface.blit(outline_surf, outline_rect)
        
        surface.blit(surf, char_rect)
        x += surf.get_width() + spacing

# aplica do efeito de onda
def draw_wave_title(text, font, base_y, time, x_center, color):
    spacing = 5  
    amplitude = 12
    frequency = 0.25
    letters = []
    
    for i, char in enumerate(text):
        offset = math.sin(time * 0.1 + i * frequency) * amplitude
        surf = font.render(char, True, color)
        letters.append((surf, offset))

    total_width = sum(s.get_width() for s, _ in letters) + spacing * (len(letters) - 1)
    start_x = x_center - total_width // 2
    x = start_x

    for surf, offset in letters:
        display.blit(surf, (x, base_y + offset))
        x += surf.get_width() + spacing

# controla todo o menu principal do jogo
def main_menu():
    button_width = 200
    button_height = 50
    spacing = 20

    total_width_top = button_width * 2 + spacing
    start_x_top = (WIDTH - total_width_top) // 2
    y_top = HEIGHT // 2 - button_height - 10

    play_rect = pygame.Rect(start_x_top, y_top, button_width, button_height)
    play_comp_rect = pygame.Rect(start_x_top + button_width + spacing, y_top, button_width, button_height)

    total_width_bottom = button_width * 3 + spacing * 2
    start_x_bottom = (WIDTH - total_width_bottom) // 2
    y_bottom = y_top + button_height + 30

    rules_rect = pygame.Rect(start_x_bottom, y_bottom, button_width, button_height)
    credits_rect = pygame.Rect(start_x_bottom + button_width + spacing, y_bottom, button_width, button_height)
    quit_rect = pygame.Rect(start_x_bottom + 2 * (button_width + spacing), y_bottom, button_width, button_height)

    time_counter = 0
    start_time = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if play_rect.collidepoint(mouse_pos):
                    return "2players"
                elif play_comp_rect.collidepoint(mouse_pos):
                    return "vscomp"
                elif rules_rect.collidepoint(mouse_pos):
                    return "rules"
                elif credits_rect.collidepoint(mouse_pos):
                    return "credits"
                elif quit_rect.collidepoint(mouse_pos):
                    return "quit"

        display.blit(menu_bg, (0, 0))

        create_button("Jogar\n2 Jogadores", play_rect, BLACK, (30,30,30), WHITE)
        create_button("Jogar vs\nComputador", play_comp_rect, BLACK, (30,30,30), WHITE)
        create_button("Regras", rules_rect, BLACK, (30,30,30), WHITE)
        create_button("Créditos", credits_rect, BLACK, (30,30,30), WHITE)
        create_button("Sair", quit_rect, LIGHT_RED, RED, BLACK)

        offset = (time.time() - start_time) * 4
        draw_wave_text_with_outline_centered(
            "Jogo de Damas", title_font, WHITE, BLACK, WIDTH // 2, HEIGHT // 4, display, offset
        )

        pygame.display.update() # atualiza a tela e controla o FPS
        clock.tick(60)
        time_counter += 0.6