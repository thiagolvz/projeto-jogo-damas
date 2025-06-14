
from jogo import WIDTH, HEIGHT
import pygame
import sys
menu_bg = pygame.image.load('assets/menu_background.jpg')
menu_bg = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))  # Redimensiona

from jogo import (
    game_loop, show_rules, show_credits,
    WIDTH, HEIGHT, display, clock,
    BG_COLOR, title_font, small_font,
    DARK_GREEN, LIGHT_GREEN, BLUE, BLACK, DARK_GRAY,
    LIGHT_RED, RED, WHITE
)


def text_objects(text, font, color):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()

def create_button(msg, rect, color, hover_color, text_color):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect[0] <= mouse_pos[0] <= rect[0] + rect[2] and \
                 rect[1] <= mouse_pos[1] <= rect[1] + rect[3]

    pygame.draw.rect(display, hover_color if is_hovered else color, rect, border_radius=15)
    text_surf, text_rect = text_objects(msg, small_font, text_color)
    text_rect.center = (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
    display.blit(text_surf, text_rect)

def draw_text_with_outline(text, font, text_color, outline_color, x, y, surface):
    outline = font.render(text, True, outline_color)
    text_surface = font.render(text, True, text_color)

    # Desenha o contorno em 8 direções ao redor do texto
    for dx in [-2, 0, 2]:
        for dy in [-2, 0, 2]:
            if dx != 0 or dy != 0:
                rect = outline.get_rect(center=(x + dx, y + dy))
                surface.blit(outline, rect)

    # Desenha o texto principal
    rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, rect)

def create_button(msg, rect, color, hover_color, text_color):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)

    pygame.draw.rect(display, hover_color if is_hovered else color, rect, border_radius=15)

    # Divide o texto em linhas, usando '\n' como separador
    lines = msg.split('\n')

    # Altura de cada linha (considerando a fonte pequena)
    line_height = small_font.get_height()

    # Calcula o topo para centralizar verticalmente todas as linhas
    total_text_height = line_height * len(lines)
    start_y = rect.y + (rect.height - total_text_height) // 2

    for i, line in enumerate(lines):
        text_surf = small_font.render(line, True, text_color)
        text_rect = text_surf.get_rect()
        # Centraliza horizontalmente dentro do botão
        text_rect.centerx = rect.x + rect.width // 2
        # Posiciona verticalmente a linha
        text_rect.y = start_y + i * line_height
        display.blit(text_surf, text_rect)


def main_menu():
    menu_running = True

    button_width = 200
    button_height = 50
    spacing = 20  # Espaço entre os botões

    # LINHA DE CIMA – 2 botões
    total_width_top = button_width * 2 + spacing
    start_x_top = (WIDTH - total_width_top) // 2
    y_top = HEIGHT // 2 - button_height - 10  # ajustado para ficar mais próximo dos de baixo

    play_rect = pygame.Rect(start_x_top, y_top, button_width, button_height)
    play_comp_rect = pygame.Rect(start_x_top + button_width + spacing, y_top, button_width, button_height)

    # LINHA DE BAIXO – 3 botões
    total_width_bottom = button_width * 3 + spacing * 2
    start_x_bottom = (WIDTH - total_width_bottom) // 2
    y_bottom = y_top + button_height + 30  # usa y_top corretamente

    rules_rect = pygame.Rect(start_x_bottom, y_bottom, button_width, button_height)
    credits_rect = pygame.Rect(start_x_bottom + button_width + spacing, y_bottom, button_width, button_height)
    quit_rect = pygame.Rect(start_x_bottom + 2 * (button_width + spacing), y_bottom, button_width, button_height)

    # ... o resto do código permanece igual

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos

                if play_rect.collidepoint(mouse_pos):
                    if game_loop(False) == 'quit':
                        pygame.quit(); sys.exit()
                elif play_comp_rect.collidepoint(mouse_pos):
                    if game_loop(True) == 'quit':
                        pygame.quit(); sys.exit()
                elif rules_rect.collidepoint(mouse_pos):
                    if show_rules() == 'quit':
                        pygame.quit(); sys.exit()
                elif credits_rect.collidepoint(mouse_pos):
                    if show_credits() == 'quit':
                        pygame.quit(); sys.exit()
                elif quit_rect.collidepoint(mouse_pos):
                    pygame.quit(); sys.exit()

        display.blit(menu_bg, (0, 0))
        draw_text_with_outline("Jogo de Damas", title_font, WHITE, (0, 0, 0), WIDTH // 2, HEIGHT // 4, display)
        create_button("Jogar\n(2 Jogadores)", play_rect, BLACK, DARK_GRAY, WHITE)
        create_button("Jogar \n(vs Computador)", play_comp_rect, BLACK, DARK_GRAY, WHITE)
        create_button("Regras", rules_rect, BLACK, DARK_GRAY, WHITE)
        create_button("Créditos", credits_rect, BLACK, DARK_GRAY, WHITE)


# Botão sair vermelho como antes
        create_button("Sair", quit_rect, LIGHT_RED, RED, BLACK)
        pygame.display.update()
        title_surf, title_rect = text_objects("Jogo de Damas", title_font, WHITE)
        clock.tick(15)
