import threading
import pygame
from pygame.locals import *
import random
import time
import copy
import sys
# bibliotecas importadas

# inicializa Pygame
pygame.init()



# constantes
WIDTH = 800
HEIGHT = 600
SQUARE_SIZE = 75 
BOARD_WIDTH_PX = SQUARE_SIZE * 8 
SIDE_PANEL_WIDTH = WIDTH - BOARD_WIDTH_PX 

# adiciona a imagem ao lado direito do tabuleiro
painel_lateral_img = pygame.image.load("assets/tabuleiro.png")
painel_lateral_img = pygame.transform.scale(painel_lateral_img, (SIDE_PANEL_WIDTH, HEIGHT))

# cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
PINK = (255, 105, 180)    # Rosa para as peças 'x'
BLUE = (0, 191, 255)      # Azul para as peças 'o'
RED = (255, 0, 0)         # Vermelho para botões
DARK_GREEN = (0, 120, 0)
LIGHT_GREEN = (0, 255, 0)
LIGHT_RED = (255, 100, 100)
BLACK = (0, 0, 0)
DARK_GRAY = (40, 40, 40)
BG_COLOR = (54, 54, 54)
BOARD_WHITE = (255, 255, 255)  # Branco para o tabuleiro
BOARD_BLACK = (0, 0, 0)       # Preto para o tabuleiro
YELLOW = (255, 255, 0)        # Amarelo para destacar jogadas obrigatórias

# inicializa a janela do jogo
display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Jogo de Damas')
clock = pygame.time.Clock()

# inicializa as fontes
small_font = pygame.font.Font('fonts/FonteDamas.ttf', 14)
medium_font = pygame.font.Font('fonts/FonteDamas.ttf', 13)
large_font = pygame.font.Font('fonts/FonteDamas.ttf', 18)
title_font = pygame.font.Font('fonts/MinhaFonte.ttf', 70)
vencedor_font = pygame.font.Font('fonts/MinhaFonte.ttf', 50)
rules_font = pygame.font.Font('fonts/FonteDamas.ttf', 18)

# define o deplay da IA
AI_DELAY_MS = 1000 

# carrega a imagem das coroas 
def load_crown_image(path, target_height):
    try:
        img = pygame.image.load(path)
        aspect_ratio = img.get_width() / img.get_height()
        target_width = int(target_height * aspect_ratio)
        return pygame.transform.scale(img, (target_width, target_height))
    except pygame.error as e:
        print(f"Erro ao carregar imagem: {path}. Verifique o caminho e a existência do arquivo. Erro: {e}")
        return None

# Load crown images globally once
CROWN_HEIGHT = int(SQUARE_SIZE * 0.45) # Alterado de 0.6 para 0.45 para coroas menores
CROWN_BLUE_IMAGE = load_crown_image('assets/crown_blue.png', CROWN_HEIGHT)
CROWN_PINK_IMAGE = load_crown_image('assets/crown_pink.png', CROWN_HEIGHT)


# converte coordenadas de pixel em coordenadas de placa
def clicked_row(pos):
    return pos[1] // SQUARE_SIZE

def clicked_col(pos):
    return pos[0] // SQUARE_SIZE

class Game: # representa o estado atual do jogo
    def __init__(self, vs_computer=False): # cria o tabuleiro inicial
        self.status = 'Playing'
        self.turn = 0  # Começa com o jogador humano (azul)
        self.players = ('o', 'x')  # Azul primeiro depois rosa
        self.selected_piece = None
        self.jumping = False # Flag para indicar se um salto múltiplo está em andamento
        self.board = [
            ['-', 'x', '-', 'x', '-', 'x', '-', 'x'],
            ['x', '-', 'x', '-', 'x', '-', 'x', '-'],
            ['-', 'x', '-', 'x', '-', 'x', '-', 'x'],
            ['-', '-', '-', '-', '-', '-', '-', '-'],
            ['-', '-', '-', '-', '-', '-', '-', '-'],
            ['o', '-', 'o', '-', 'o', '-', 'o', '-'],
            ['-', 'o', '-', 'o', '-', 'o', '-', 'o'],
            ['o', '-', 'o', '-', 'o', '-', 'o', '-']
        ]
        
        self.mandatory_moves = {}
        self.update_mandatory_moves()
        self.vs_computer = vs_computer
        self.computer_player = 'x'  # O computador joga com as peças rosas ('x')
        self._current_player_char = self.players[self.turn % 2] # Inicializa como atributo de instância
        self.computer_turn_active = False
        self.lock = threading.Lock()
        self.ai_thread = None # Nova flag para controlar o turno do computador
        self.ai_move_timer = None # Timer para a jogada da IA
        
# Atualiza o dicionário mandatory_moves com capturas e movimentos normais
    def update_mandatory_moves(self):
       
        self.mandatory_moves = {}
        current_player_char = self.players[self.turn % 2]
        has_captures_overall = False

       
        all_possible_captures = [] 
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece.lower() == current_player_char:
                    piece_captures = self._get_capture_moves((row, col), self.board, current_player_char)
                    if piece_captures:
                        all_possible_captures.extend(piece_captures)
                        has_captures_overall = True

        if has_captures_overall:
            for dest_pos, jumped_pos, start_pos in all_possible_captures:
                if start_pos not in self.mandatory_moves:
                    self.mandatory_moves[start_pos] = []
                self.mandatory_moves[start_pos].append((dest_pos, jumped_pos))
        else:
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece.lower() == current_player_char:
                        normal_moves = self._get_normal_moves((row, col), self.board, current_player_char)
                        if normal_moves:
                            if (row, col) not in self.mandatory_moves:
                                self.mandatory_moves[(row, col)] = []
                            for move in normal_moves:
                                self.mandatory_moves[(row, col)].append((move, None))

# detecta peças para possíveis capturas
    def _get_capture_moves(self, piece_pos, board, player_to_check):
        
        capture_list = []
        row, col = piece_pos
        piece_type = board[row][col]
        opponent_char = 'x' if player_to_check == 'o' else 'o'

        if piece_type.islower(): 
            directions = []
            if player_to_check == 'o': 
                directions = [(-1, -1), (-1, 1)]
            else: 
                directions = [(1, -1), (1, 1)]

            for dr, dc in directions:
                
                new_row, new_col = row + dr, col + dc
                jump_row, jump_col = row + 2 * dr, col + 2 * dc

                if (0 <= new_row < 8 and 0 <= new_col < 8 and
                    board[new_row][new_col].lower() == opponent_char and
                    0 <= jump_row < 8 and 0 <= jump_col < 8 and
                    board[jump_row][jump_col] == '-'):
                    capture_list.append(([jump_row, jump_col], (new_row, new_col), piece_pos))
        else: 
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] 
            for dr, dc in directions:
                r, c = row + dr, col + dc
                potential_captured_piece_pos = None
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c].lower() == player_to_check:
                        break 
                    if board[r][c].lower() == opponent_char:
                        if potential_captured_piece_pos: 
                            break #
                        potential_captured_piece_pos = (r, c)
                    elif board[r][c] == '-' and potential_captured_piece_pos:
                        capture_list.append(([r, c], potential_captured_piece_pos, piece_pos))
                    elif board[r][c] == '-' and not potential_captured_piece_pos:
                        pass 
                    else: 
                        break
                    r += dr
                    c += dc
        return capture_list

# detecta possíveis movimentos sem captura
    def _get_normal_moves(self, piece_pos, board, player_to_check):
    
        normal_moves_list = []
        row, col = piece_pos
        piece_type = board[row][col]

        if piece_type.islower(): 
            directions = []
            if player_to_check == 'o': 
                directions = [(-1, -1), (-1, 1)]
            else: 
                directions = [(1, -1), (1, 1)]

            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] == '-':
                    normal_moves_list.append([new_row, new_col])
        else: 
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] 
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == '-':
                    normal_moves_list.append([r, c])
                    r += dr
                    c += dc
        return normal_moves_list

# processa os clicks do jogador
    def evaluate_click(self, pos):
        if self.lock.locked():
            return
        
        if self.status == "Playing":
            if self.vs_computer and self._current_player_char == self.computer_player:
                return

            row, col = clicked_row(pos), clicked_col(pos)
            clicked_pos = (row, col)

            if self.selected_piece:
                is_valid, jumped_piece_pos = self.is_valid_move(
                    self._current_player_char, self.selected_piece, row, col
                )
                if is_valid:
                    self.make_move(
                        self._current_player_char, self.selected_piece, row, col, jumped_piece_pos
                    )
                elif clicked_pos == self.selected_piece:
                    self.selected_piece = None
                    self.jumping = False 
                    self.update_mandatory_moves() 
                elif self.board[row][col].lower() == self._current_player_char:
                    if clicked_pos in self.mandatory_moves:
                        self.selected_piece = [row, col]
                        self.jumping = False 
                        self.update_mandatory_moves() 
            else:
                if self.board[row][col].lower() == self._current_player_char:
                    if clicked_pos in self.mandatory_moves:
                        self.selected_piece = [row, col]
                        self.jumping = False 

# verifica se o movimento é valido
    def is_valid_move(self, player_char, piece_pos, dest_row, dest_col):

        start_row, start_col = piece_pos
        start_pos_tuple = (start_row, start_col)

        if start_pos_tuple not in self.mandatory_moves:
            return False, None

        for allowed_dest, jumped_piece_pos in self.mandatory_moves[start_pos_tuple]:
            if allowed_dest[0] == dest_row and allowed_dest[1] == dest_col:
                return True, jumped_piece_pos 
        return False, None

    def get_possible_moves(self, piece_pos):
        
        piece_pos_tuple = (piece_pos[0], piece_pos[1]) 
        if piece_pos_tuple in self.mandatory_moves:
            destinations = [move[0] for move in self.mandatory_moves[piece_pos_tuple]]
            is_jump_possible = any(move[1] is not None for move in self.mandatory_moves[piece_pos_tuple])
            return destinations, is_jump_possible
        return [], False

# move a peça, remove a captura e transforma em dama
    def make_move(self, player_char, piece_pos, dest_row, dest_col, jumped_piece_pos=None):
       
        start_row, start_col = piece_pos
        piece = self.board[start_row][start_col]

        self.board[dest_row][dest_col] = piece
        self.board[start_row][start_col] = '-'

        if jumped_piece_pos:
            self.board[jumped_piece_pos[0]][jumped_piece_pos[1]] = '-'

        if (player_char == 'o' and dest_row == 0) or \
           (player_char == 'x' and dest_row == 7):
            self.board[dest_row][dest_col] = piece.upper()

        if jumped_piece_pos: 
            re_evaluated_captures = self._get_capture_moves((dest_row, dest_col), self.board, player_char)
            if re_evaluated_captures:
                self.selected_piece = [dest_row, dest_col] 
                self.jumping = True
                self.mandatory_moves = {(dest_row, dest_col): [(m[0], m[1]) for m in re_evaluated_captures]}
                return 
            else:
                self.jumping = False 

        self.selected_piece = None
        self.jumping = False
        self.next_turn()

        winner = self.check_winner()
        if winner is not None:
            self.status = 'Game Over' # Atualiza o status do jogo

# altera o turno
    def next_turn(self):
        self.turn += 1
        self._current_player_char = self.players[self.turn % 2] 
        self.update_mandatory_moves()
        if self._current_player_char == self.computer_player and self.vs_computer:
            self.computer_turn_active = True
            self.ai_thread = threading.Thread(target=self.run_ai_move)
            self.ai_thread.start() 
        else:
            self.computer_turn_active = False
        
# retorna x, o, tie ou None, checa os vencedores
    def check_winner(self):
        
        pink_count = sum(row.count('x') + row.count('X') for row in self.board)
        blue_count = sum(row.count('o') + row.count('O') for row in self.board)

        if pink_count == 0:
            return 'o' 
        if blue_count == 0:
            return 'x' 

        
        if not self.has_possible_move():
            if self.players[self.turn % 2] == 'o':
                return 'x' 
            else:
                return 'o' 

        return None 

# se o jogador atual pode jogar retorna true
    def has_possible_move(self):
        
        return bool(self.mandatory_moves)

# calcula as possíveis jogadas da IA
    def computer_move(self):
        
        if self.status != "Playing":
            return

        current_player_char = self.players[self.turn % 2]
        if current_player_char != self.computer_player:
            return

        performed_move = False 

        while True:
            self.update_mandatory_moves() 

            if self.jumping and self.selected_piece:
                piece_pos_tuple = (self.selected_piece[0], self.selected_piece[1])
                possible_moves_for_selected_piece = []
                if piece_pos_tuple in self.mandatory_moves:
                    for dest_pos, jumped_piece_pos in self.mandatory_moves[piece_pos_tuple]:
                        if jumped_piece_pos:
                            possible_moves_for_selected_piece.append({
                                'piece_pos': piece_pos_tuple,
                                'dest_pos': dest_pos,
                                'jumped_piece_pos': jumped_piece_pos
                            })
                valid_computer_moves = possible_moves_for_selected_piece
            else:
                valid_computer_moves = []
                all_captures = []
                for piece_pos, moves_info in self.mandatory_moves.items():
                    if self.board[piece_pos[0]][piece_pos[1]].lower() == self.computer_player:
                        for dest_pos, jumped_piece_pos in moves_info:
                            if jumped_piece_pos:
                                all_captures.append({
                                    'piece_pos': piece_pos,
                                    'dest_pos': dest_pos,
                                    'jumped_piece_pos': jumped_piece_pos
                                })

                if all_captures:
                    valid_computer_moves = all_captures
                else:
                    for piece_pos, moves_info in self.mandatory_moves.items():
                        if self.board[piece_pos[0]][piece_pos[1]].lower() == self.computer_player:
                            for dest_pos, jumped_piece_pos in moves_info:
                                if not jumped_piece_pos: 
                                    valid_computer_moves.append({
                                        'piece_pos': piece_pos,
                                        'dest_pos': dest_pos,
                                        'jumped_piece_pos': None
                                    })

            if not valid_computer_moves:
                break 

            best_move = None
            best_score = -float('inf')

            for move_data in valid_computer_moves:
                piece_pos = move_data['piece_pos']
                dest_pos = move_data['dest_pos']
                jumped_piece_pos = move_data['jumped_piece_pos']

                temp_board = copy.deepcopy(self.board)
                temp_piece_char = temp_board[piece_pos[0]][piece_pos[1]]

                temp_board[dest_pos[0]][dest_pos[1]] = temp_piece_char
                temp_board[piece_pos[0]][piece_pos[1]] = '-'
                if jumped_piece_pos:
                    temp_board[jumped_piece_pos[0]][jumped_piece_pos[1]] = '-' 

                promoted_to_king = False
                if (self.computer_player == 'o' and dest_pos[0] == 0) or \
                   (self.computer_player == 'x' and dest_pos[0] == 7):
                    temp_board[dest_pos[0]][dest_pos[1]] = temp_piece_char.upper()
                    promoted_to_king = True

                score = 0
                if jumped_piece_pos:
                    score += 100 
                    post_jump_captures_simulated = self._get_capture_moves(dest_pos, temp_board, self.computer_player)
                    if post_jump_captures_simulated:
                        score += 500 

                if promoted_to_king:
                    score += 200 
                if self.computer_player == 'x': 
                    score += dest_pos[0] * 5 
                else: 
                    score += (7 - dest_pos[0]) * 5 

                center_cols = {2, 3, 4, 5}
                if dest_pos[1] in center_cols:
                    score += 5

                if not self.is_position_safe(dest_pos, temp_board, self.computer_player):
                    score -= 150 

                if score > best_score:
                    best_score = score
                    best_move = move_data

            if best_move:
                self.make_move(self.computer_player, best_move['piece_pos'],
                               best_move['dest_pos'][0], best_move['dest_pos'][1],
                               best_move['jumped_piece_pos'])
                if self.jumping: 
                    display.fill(BG_COLOR)
                    self.draw()
                    pygame.display.update()
                    pygame.time.wait(AI_DELAY_MS // 2) 
                    continue 
                else:
                    performed_move = True 
                    break 
            else:
                break

        
        if performed_move:
            self.computer_turn_active = False
            self.ai_move_timer = None
        else: 
            if self._current_player_char == self.computer_player:
                self.next_turn()  
        self.computer_turn_active = False
        self.ai_move_timer = None

# não deixa a IA se mover para espaços que será capturada
    def is_position_safe(self, pos, board, current_player_char):
        row, col = pos
        opponent_char = 'x' if current_player_char == 'o' else 'o'

        for r_op in range(8):
            for c_op in range(8):
                piece_op = board[r_op][c_op]
                if piece_op.lower() == opponent_char:
                    opponent_captures = self._get_capture_moves((r_op, c_op), board, opponent_char)
                    for dest_op, jumped_op, _ in opponent_captures:
                        if jumped_op == (row, col): 
                            return False 
        return True
    
    # Thread segura que espera 0.5s e chama a IA
    def run_ai_move(self):
        self.lock.acquire()
        try:
            pygame.time.wait(500)
            self.computer_move()
        finally:
            self.lock.release()

# desenha: tabuleiro, peças, destaques, turno, peças capturadas, modo de jogo, alerta de captura obrigatória
    def draw(self):
        for row in range(8):
            for col in range(8):
                color = BOARD_WHITE if (row + col) % 2 == 0 else BOARD_BLACK
                pygame.draw.rect(display, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        
        display.blit(painel_lateral_img, (BOARD_WIDTH_PX, 0))

        pygame.draw.line(display, WHITE, (BOARD_WIDTH_PX, 0), (BOARD_WIDTH_PX, HEIGHT), 2)

        current_player_char = self.players[self.turn % 2]
        for (row, col), moves_info in self.mandatory_moves.items():
            if self.board[row][col].lower() == current_player_char:
                if any(mi[1] is not None for mi in moves_info): 
                    pygame.draw.rect(display, YELLOW, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)


        if self.selected_piece:
            row, col = self.selected_piece
            pygame.draw.rect(display, LIGHT_GREEN, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

            possible_destinations, _ = self.get_possible_moves(self.selected_piece)
            for move in possible_destinations:
                x = move[1] * SQUARE_SIZE
                y = move[0] * SQUARE_SIZE
                pygame.draw.rect(display, LIGHT_GREEN, (x, y, SQUARE_SIZE, SQUARE_SIZE), 3) # Destaca possíveis destinos

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '-':
                    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2

                    if piece.lower() == 'x': 
                        if piece.isupper(): 
                            if CROWN_PINK_IMAGE:
                                image_x = center_x - CROWN_PINK_IMAGE.get_width() // 2
                                image_y = center_y - CROWN_PINK_IMAGE.get_height() // 2
                                display.blit(CROWN_PINK_IMAGE, (image_x, image_y))
                            else: 
                                pygame.draw.circle(display, PINK, (center_x, center_y), 20)
                                pygame.draw.circle(display, YELLOW, (center_x, center_y), 10) 
                        else: 
                            pygame.draw.circle(display, PINK, (center_x, center_y), 20)
                    else:
                        if piece.isupper(): 
                            if CROWN_BLUE_IMAGE:
                                image_x = center_x - CROWN_BLUE_IMAGE.get_width() // 2
                                image_y = center_y - CROWN_BLUE_IMAGE.get_height() // 2
                                display.blit(CROWN_BLUE_IMAGE, (image_x, image_y))
                            else: 
                                pygame.draw.circle(display, BLUE, (center_x, center_y), 20)
                                pygame.draw.circle(display, YELLOW, (center_x, center_y), 10) 
                        else: 
                            pygame.draw.circle(display, BLUE, (center_x, center_y), 20)

        pink_pieces_remaining = sum(row.count('x') + row.count('X') for row in self.board)
        blue_pieces_remaining = sum(row.count('o') + row.count('O') for row in self.board)

        panel_center_x = BOARD_WIDTH_PX + SIDE_PANEL_WIDTH // 2

        if self.status != 'Game Over':
            pink_captured_count = 12 - blue_pieces_remaining
            pink_text = small_font.render(f"Rosa: {pink_captured_count}", True, PINK)
            pink_text_rect = pink_text.get_rect(center=(panel_center_x, 30))
            display.blit(pink_text, pink_text_rect)

            blue_captured_count = 12 - pink_pieces_remaining
            blue_text = small_font.render(f"Azul: {blue_captured_count}", True, BLUE)
            blue_text_rect = blue_text.get_rect(center=(panel_center_x, HEIGHT - 50))
            display.blit(blue_text, blue_text_rect)

            if self.turn % 2 == 0:
                turn_text = large_font.render("Turno do Azul", True, BLUE)
            else:
                turn_text = large_font.render("Turno do Rosa", True, PINK)
            turn_text_rect = turn_text.get_rect(center=(panel_center_x, HEIGHT // 2 - 20))
            display.blit(turn_text, turn_text_rect)

            has_captures_for_current_player = any(
                any(move_info[1] is not None for move_info in moves_list)
                for piece_pos, moves_list in self.mandatory_moves.items()
                if self.board[piece_pos[0]][piece_pos[1]].lower() == self._current_player_char
            )

            if has_captures_for_current_player:
                capture_text = medium_font.render("Captura obrigatória!", True, RED)
                capture_text_rect = capture_text.get_rect(center=(panel_center_x, HEIGHT // 2 + 20))
                display.blit(capture_text, capture_text_rect)

            if self.vs_computer:
                mode_text = small_font.render("Modo: vs Computador", True, WHITE)
            else:
                mode_text = small_font.render("Modo: 2 Jogadores", True, WHITE)
            mode_text_rect = mode_text.get_rect(center=(panel_center_x, HEIGHT // 2 + 70))
            display.blit(mode_text, mode_text_rect)

       


def text_objects(text, font, color):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()

# apenas desenha os botões
def create_button(msg, rect, color, hover_color, text_color):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect[0] <= mouse_pos[0] <= rect[0] + rect[2] and \
                 rect[1] <= mouse_pos[1] <= rect[1] + rect[3]

    if is_hovered:
        pygame.draw.rect(display, hover_color, rect)
    else:
        pygame.draw.rect(display, color, rect)

    text_surf, text_rect = text_objects(msg, small_font, text_color)
    text_rect.center = (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
    display.blit(text_surf, text_rect)

#exibe pos créditos
def show_credits():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False 

        display.fill(BLACK)
        
        lines = [
            "Grupo:",
            "Rafaela Tolentino",
            "Rebeca Gomes Ferreira",
            "Thiago Alves",
            "Vitorya de Almeida Vieira",
            "Viviane Lisboa do Santos",
            "",
            "Curso: Engenharia de Software / Sistemas Operacionais",
            "",
            "Aperte qualquer tecla ou clique para retornar ao menu"
        ]
        
        for i, line in enumerate(lines):
            color = WHITE
            if "Grupo:" in line:
                font_to_use = large_font
            elif "Aperte" in line:
                color = LIGHT_GREEN
                font_to_use = small_font
            else:
                font_to_use = medium_font

            text_surf, text_rect = text_objects(line, font_to_use, color)
            text_rect.center = (WIDTH // 2, 100 + i * 40)
            display.blit(text_surf, text_rect)

        pygame.display.update()
        clock.tick(15)
    return 'menu' # Retorna um sinal para o menu principal continuar


#exibe as regras
def show_rules():
    """Exibe a tela de regras com tamanhos e cores personalizados."""
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False

        display.fill(BLACK)  # Fundo preto
        
        # Configurações de fontes
        title_font = pygame.font.Font('fonts/FonteDamas.ttf', 32)  # Fonte do título
        section_font = pygame.font.Font('fonts/FonteDamas.ttf', 26) # Fonte para seções
        rule_font = pygame.font.Font('fonts/FonteDamas.ttf', 17)   # Fonte para regras
        tip_font = pygame.font.Font('fonts/FonteDamas.ttf', 18)    # Fonte para dicas
        return_font = pygame.font.Font('fonts/FonteDamas.ttf', 20) # Fonte para retorno
        
        # Cores personalizadas
        title_color = (255, 215, 0)    # Dourado
        section_color = (100, 200, 255) # Azul claro
        rule_color = (200, 200, 255)    # Azul muito claro
        tip_color = (144, 238, 144)     # Verde claro
        return_color = (255, 105, 180)  # Rosa
        
        # Desenha o título
        title_surf = title_font.render("Regras do Jogo de Damas", True, title_color)
        title_rect = title_surf.get_rect(center=(WIDTH//2, 30))
        display.blit(title_surf, title_rect)
        
        # Lista de regras com tipos (para aplicar formatação diferente)
        rules = [
            ("OBJETIVO", "section", 70),
            ("Capturar todas as peças do oponente ou bloquear seus movimentos.", "rule", 100),
            ("", "space", 120),
            
            ("MOVIMENTAÇÃO", "section", 150),
            ("Peças comuns movem-se na diagonal, uma casa por vez.", "rule", 180),
            ("Damas (reis) movem-se em qualquer direção diagonal.", "rule", 210),
            ("Capturas são obrigatórias quando possíveis.", "rule", 240),
            ("", "space", 260),
            
            ("DICAS", "section", 290),
            ("Clique em uma peça para selecioná-la.", "tip", 320),
            ("Movimentos válidos são destacados em verde.", "tip", 350),
            ("Peças com capturas obrigatórias são destacadas em amarelo.", "tip", 380),
            ("", "space", 400),
            
            ("Aperte qualquer tecla ou clique para retornar ao menu", "return", 450)
        ]
        
        # Renderiza todas as regras
        for text, rule_type, y_pos in rules:
            if rule_type == "section":
                text_surf = section_font.render(text, True, section_color)
            elif rule_type == "rule":
                text_surf = rule_font.render(text, True, rule_color)
            elif rule_type == "tip":
                text_surf = tip_font.render(text, True, tip_color)
            elif rule_type == "return":
                text_surf = return_font.render(text, True, return_color)
            else:  # space
                continue
                
            text_rect = text_surf.get_rect(center=(WIDTH//2, y_pos))
            display.blit(text_surf, text_rect)

        pygame.display.update()
        clock.tick(30)
    return 'menu'

def show_winner(winner):
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit() 
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False 

        display.fill(BLACK)
        
        if winner == "tie":
            text_surf, text_rect = text_objects("EMPATE!", vencedor_font, WHITE)
        elif winner == "x":
            text_surf, text_rect = text_objects("ROSA GANHOU!", vencedor_font, PINK)
        else: # winner == "o"
            text_surf, text_rect = text_objects("AZUL GANHOU!", vencedor_font, BLUE)

        text_rect.center = (WIDTH//2, HEIGHT//3)
        display.blit(text_surf, text_rect)

        return_text_surf, return_text_rect = text_objects(
            'Aperte qualquer tecla ou clique para retornar ao menu.', medium_font, WHITE
        )
        return_text_rect.center = (WIDTH//2, HEIGHT//3 + 100)
        display.blit(return_text_surf, return_text_rect)

        pygame.display.update()
        clock.tick(15)

#  controla a execução principal do jogo
def game_loop(vs_computer=False):

    game = Game(vs_computer)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit' 
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.status == 'Playing' and not game.computer_turn_active: 
                    game.evaluate_click(event.pos)
            if event.type == pygame.KEYDOWN:
                pass 

       
        if game.status == 'Playing' and game.vs_computer and game.computer_turn_active:
            if game.ai_move_timer and pygame.time.get_ticks() >= game.ai_move_timer:
                game.computer_move() 
        display.fill(BG_COLOR)
        game.draw()
        pygame.display.update()
        clock.tick(60) 

        if game.status == 'Game Over':
            show_winner(game.check_winner())
            running = False 
    return 'menu' 

    def run_ai_move(self):
        self.lock.acquire()
        try:
            pygame.time.wait(AI_DELAY_MS)
            self.computer_move()
        finally:
            self.lock.release()
