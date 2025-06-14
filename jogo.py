import threading
import pygame
from pygame.locals import *
import random
import time
import copy
import sys

# Initialize Pygame
pygame.init()



# CONSTANTS
WIDTH = 800
HEIGHT = 600
SQUARE_SIZE = 75 # Cada quadrado agora tem 75x75 pixels (8x8 tabuleiro = 600x600 pixels)
BOARD_WIDTH_PX = SQUARE_SIZE * 8 # Largura do tabuleiro em pixels (600 pixels)
SIDE_PANEL_WIDTH = WIDTH - BOARD_WIDTH_PX # Largura do painel lateral (200 pixels)

# Colors
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

# Initialize display
display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Jogo de Damas')
clock = pygame.time.Clock()

# Initialize fonts once for performance
small_font = pygame.font.Font('fonts/FonteDamas.ttf', 14)
medium_font = pygame.font.Font('fonts/FonteDamas.ttf', 13)
large_font = pygame.font.Font('fonts/FonteDamas.ttf', 18)
title_font = pygame.font.Font('fonts/MinhaFonte.ttf', 70)
vencedor_font = pygame.font.Font('fonts/MinhaFonte.ttf', 50)


# Define AI delay
AI_DELAY_MS = 1000 # 1 segundo de atraso para a jogada da IA

# Load crown images with aspect ratio preservation
def load_crown_image(path, target_height):
    """
    Carrega uma imagem e a escala para uma altura alvo,
    mantendo a proporção de aspecto.
    """
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


# Helper functions to convert pixel coordinates to board coordinates
def clicked_row(pos):
    """Converte a coordenada Y do clique em uma linha do tabuleiro."""
    return pos[1] // SQUARE_SIZE

def clicked_col(pos):
    """Converte a coordenada X do clique em uma coluna do tabuleiro."""
    return pos[0] // SQUARE_SIZE

class Game:
    def __init__(self, vs_computer=False):
        self.status = 'Playing'
        self.turn = 0  # Começa com o jogador humano (azul)
        self.players = ('o', 'x')  # Azul primeiro, depois rosa
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
        # mandatory_moves armazenará: {pos_da_peca: [(pos_destino, pos_peca_capturada), ...]}
        self.mandatory_moves = {}
        self.update_mandatory_moves()
        self.vs_computer = vs_computer
        self.computer_player = 'x'  # O computador joga com as peças rosas ('x')
        self._current_player_char = self.players[self.turn % 2] # Inicializa como atributo de instância
        self.computer_turn_active = False
        self.lock = threading.Lock()
        self.ai_thread = None # Nova flag para controlar o turno do computador
        self.ai_move_timer = None # Timer para a jogada da IA
        

    def update_mandatory_moves(self):
        """
        Atualiza o dicionário com todas as jogadas obrigatórias para o jogador atual.
        Prioriza capturas. Se existirem capturas, apenas as jogadas de captura são obrigatórias.
        Caso contrário, todos os movimentos normais são permitidos.
        """
        self.mandatory_moves = {}
        current_player_char = self.players[self.turn % 2]
        has_captures_overall = False

        # Primeiro, encontra todas as capturas possíveis para o jogador atual em todo o tabuleiro
        all_possible_captures = [] # Armazena (pos_destino, pos_peca_capturada, pos_peca_inicial)
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece.lower() == current_player_char:
                    piece_captures = self._get_capture_moves((row, col), self.board, current_player_char)
                    if piece_captures:
                        all_possible_captures.extend(piece_captures)
                        has_captures_overall = True

        if has_captures_overall:
            # Se existirem capturas, apenas elas são permitidas. Popula mandatory_moves com movimentos de captura.
            for dest_pos, jumped_pos, start_pos in all_possible_captures:
                if start_pos not in self.mandatory_moves:
                    self.mandatory_moves[start_pos] = []
                self.mandatory_moves[start_pos].append((dest_pos, jumped_pos))
        else:
            # Se não houver capturas, permite movimentos normais
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece.lower() == current_player_char:
                        normal_moves = self._get_normal_moves((row, col), self.board, current_player_char)
                        if normal_moves:
                            # Para movimentos normais, não há peça capturada, então usa None
                            if (row, col) not in self.mandatory_moves:
                                self.mandatory_moves[(row, col)] = []
                            for move in normal_moves:
                                self.mandatory_moves[(row, col)].append((move, None))

    def _get_capture_moves(self, piece_pos, board, player_to_check):
        """
        Função auxiliar para obter todos os movimentos de captura possíveis para uma dada peça
        em um dado tabuleiro.
        Retorna uma lista de tuplas: (pos_destino, pos_peca_capturada, pos_peca_inicial).
        """
        capture_list = []
        row, col = piece_pos
        piece_type = board[row][col]
        opponent_char = 'x' if player_to_check == 'o' else 'o'

        if piece_type.islower(): # Peça regular
            directions = []
            if player_to_check == 'o': # Peças azuis movem para cima
                directions = [(-1, -1), (-1, 1)]
            else: # Peças rosas movem para baixo
                directions = [(1, -1), (1, 1)]

            for dr, dc in directions:
                # Verifica a peça do oponente a um passo de distância
                new_row, new_col = row + dr, col + dc
                # Verifica o quadrado vazio a dois passos de distância (local de aterrissagem)
                jump_row, jump_col = row + 2 * dr, col + 2 * dc

                if (0 <= new_row < 8 and 0 <= new_col < 8 and
                    board[new_row][new_col].lower() == opponent_char and
                    0 <= jump_row < 8 and 0 <= jump_col < 8 and
                    board[jump_row][jump_col] == '-'):
                    capture_list.append(([jump_row, jump_col], (new_row, new_col), piece_pos))
        else: # Peça Dama (maiúscula)
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] # Damas podem mover em todas as direções
            for dr, dc in directions:
                r, c = row + dr, col + dc
                potential_captured_piece_pos = None
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c].lower() == player_to_check:
                        break # Bateu na própria peça, não pode pular
                    if board[r][c].lower() == opponent_char:
                        if potential_captured_piece_pos: # Já encontrou uma peça para pular
                            break # Não pode pular duas peças em um único movimento
                        potential_captured_piece_pos = (r, c)
                    elif board[r][c] == '-' and potential_captured_piece_pos:
                        # Quadrado vazio após uma peça capturada, este é o local de aterrissagem válido
                        capture_list.append(([r, c], potential_captured_piece_pos, piece_pos))
                    elif board[r][c] == '-' and not potential_captured_piece_pos:
                        pass # Quadrado vazio, continua procurando por uma peça do oponente
                    else: # Bateu em uma peça inválida (ex: outra peça do oponente atrás da primeira)
                        break
                    r += dr
                    c += dc
        return capture_list

    def _get_normal_moves(self, piece_pos, board, player_to_check):
        """
        Função auxiliar para obter todos os movimentos normais (não de captura) para uma dada peça
        em um dado tabuleiro.
        Retorna uma lista de pos_destino.
        """
        normal_moves_list = []
        row, col = piece_pos
        piece_type = board[row][col]

        if piece_type.islower(): # Peça regular
            directions = []
            if player_to_check == 'o': # Peças azuis movem para cima
                directions = [(-1, -1), (-1, 1)]
            else: # Peças rosas movem para baixo
                directions = [(1, -1), (1, 1)]

            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8 and board[new_row][new_col] == '-':
                    normal_moves_list.append([new_row, new_col])
        else: # Peça Dama
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] # Damas podem mover em todas as direções
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == '-':
                    normal_moves_list.append([r, c])
                    r += dr
                    c += dc
        return normal_moves_list

    def evaluate_click(self, pos):
        if self.lock.locked():
            return
        """Lida com um evento de clique do mouse no tabuleiro."""
        
        if self.status == "Playing":
            # Se for o turno do computador, ignora os cliques do jogador humano
            if self.vs_computer and self._current_player_char == self.computer_player:
                return

            row, col = clicked_row(pos), clicked_col(pos)
            clicked_pos = (row, col)

            if self.selected_piece:
                # Uma peça já está selecionada, tenta movê-la
                is_valid, jumped_piece_pos = self.is_valid_move(
                    self._current_player_char, self.selected_piece, row, col
                )
                if is_valid:
                    self.make_move(
                        self._current_player_char, self.selected_piece, row, col, jumped_piece_pos
                    )
                elif clicked_pos == self.selected_piece:
                    # Clicou na mesma peça novamente, deseleciona-a
                    self.selected_piece = None
                    self.jumping = False # Redefine a flag de salto se deselecionado
                    self.update_mandatory_moves() # Reavalia para todas as peças
                elif self.board[row][col].lower() == self._current_player_char:
                    # Clicou em outra peça do mesmo jogador, tenta selecioná-la
                    if clicked_pos in self.mandatory_moves:
                        self.selected_piece = [row, col]
                        self.jumping = False # Não necessariamente saltando ainda
                        # Se um salto múltiplo estava ativo, ele termina se outra peça for selecionada
                        self.update_mandatory_moves() # Reavalia para a peça recém-selecionada
            else:
                # Nenhuma peça está selecionada, tenta selecionar uma
                if self.board[row][col].lower() == self._current_player_char:
                    if clicked_pos in self.mandatory_moves:
                        self.selected_piece = [row, col]
                        self.jumping = False # Não necessariamente saltando ainda

    def is_valid_move(self, player_char, piece_pos, dest_row, dest_col):
        """
        Verifica se um movimento de piece_pos para (dest_row, dest_col) é válido
        de acordo com os movimentos obrigatórios atuais.
        Retorna (True, pos_peca_capturada) se válido, (False, None) caso contrário.
        """
        start_row, start_col = piece_pos
        start_pos_tuple = (start_row, start_col)

        # Verifica se a peça selecionada é sequer permitida para mover
        if start_pos_tuple not in self.mandatory_moves:
            return False, None

        # Verifica se o destino é um dos movimentos permitidos para esta peça
        for allowed_dest, jumped_piece_pos in self.mandatory_moves[start_pos_tuple]:
            if allowed_dest[0] == dest_row and allowed_dest[1] == dest_col:
                return True, jumped_piece_pos # Esta é a peça capturada específica para este movimento
        return False, None

    def get_possible_moves(self, piece_pos):
        """
        Retorna uma lista de posições de destino válidas para a dada piece_pos,
        com base nos mandatory_moves atuais do jogo.
        Retorna uma tupla: (lista de pos_destino, booleano indicando se há saltos envolvidos)
        Isso é principalmente para desenhar destaques.
        """
        piece_pos_tuple = (piece_pos[0], piece_pos[1]) # Correção: alterado de 'piece[1]' para 'piece_pos[1]'
        if piece_pos_tuple in self.mandatory_moves:
            destinations = [move[0] for move in self.mandatory_moves[piece_pos_tuple]]
            # Verifica se algum dos movimentos é um salto (ou seja, jumped_piece_pos não é None)
            is_jump_possible = any(move[1] is not None for move in self.mandatory_moves[piece_pos_tuple])
            return destinations, is_jump_possible
        return [], False

    def make_move(self, player_char, piece_pos, dest_row, dest_col, jumped_piece_pos=None):
        """
        Executa um movimento no tabuleiro.
        Lida com o movimento da peça, captura de peça e promoção a dama.
        Verifica saltos consecutivos.
        """
        start_row, start_col = piece_pos
        piece = self.board[start_row][start_col]

        self.board[dest_row][dest_col] = piece
        self.board[start_row][start_col] = '-'

        if jumped_piece_pos:
            self.board[jumped_piece_pos[0]][jumped_piece_pos[1]] = '-'

        # Promove a dama se atingir a extremidade oposta
        if (player_char == 'o' and dest_row == 0) or \
           (player_char == 'x' and dest_row == 7):
            self.board[dest_row][dest_col] = piece.upper()

        # Verifica saltos consecutivos com a mesma peça
        if jumped_piece_pos: # Se um salto acabou de ocorrer
            # Reavalia as capturas especificamente para a peça que acabou de se mover para sua nova posição
            re_evaluated_captures = self._get_capture_moves((dest_row, dest_col), self.board, player_char)
            if re_evaluated_captures:
                # Se houver mais capturas para esta peça, mantém o turno do mesmo jogador
                self.selected_piece = [dest_row, dest_col] # Mantém a peça selecionada
                self.jumping = True
                # Atualiza mandatory_moves *apenas* para esta peça para o próximo clique
                self.mandatory_moves = {(dest_row, dest_col): [(m[0], m[1]) for m in re_evaluated_captures]}
                return # Permanece no mesmo turno, aguardando o próximo salto
            else:
                self.jumping = False # Não há mais saltos para esta peça

        # Se nenhum salto ocorreu, ou não há mais saltos disponíveis, termina o turno
        self.selected_piece = None
        self.jumping = False
        self.next_turn()

        winner = self.check_winner()
        if winner is not None:
            self.status = 'Game Over' # Atualiza o status do jogo

    def next_turn(self):
        """Avança o turno para o próximo jogador e atualiza os movimentos obrigatórios."""
        self.turn += 1
        self._current_player_char = self.players[self.turn % 2] # Atualiza o atributo de instância
        self.update_mandatory_moves()
        # Se o próximo turno for do computador, ative a flag e o timer
        if self._current_player_char == self.computer_player and self.vs_computer:
            self.computer_turn_active = True
            self.ai_thread = threading.Thread(target=self.run_ai_move)
            self.ai_thread.start() # Define o tempo para a jogada da IA
        else:
            self.computer_turn_active = False
        

    def check_winner(self):
        """
        Verifica se há um vencedor ou um empate.
        Retorna 'o' se o azul vencer, 'x' se o rosa vencer, 'tie' se for um empate, None caso contrário.
        """
        pink_count = sum(row.count('x') + row.count('X') for row in self.board)
        blue_count = sum(row.count('o') + row.count('O') for row in self.board)

        if pink_count == 0:
            return 'o' # Azul vence (todas as peças rosas capturadas)
        if blue_count == 0:
            return 'x' # Rosa vence (todas as peças azuis capturadas)

        # Se o jogador atual não tiver movimentos válidos, ele perde
        if not self.has_possible_move():
            if self.players[self.turn % 2] == 'o':
                return 'x' # Azul não tem movimentos, Rosa vence
            else:
                return 'o' # Rosa não tem movimentos, Azul vence

        return None # Nenhum vencedor ainda

    def has_possible_move(self):
        """
        Verifica se o jogador atual tem algum movimento possível (normal ou de captura).
        Isso é usado para determinar se um jogador está em xeque-mate.
        """
        # Se self.mandatory_moves não estiver vazio, significa que há movimentos disponíveis para o jogador atual
        return bool(self.mandatory_moves)

    def computer_move(self):
        """
        Executa o movimento do computador com uma estratégia aprimorada,
        incluindo a lógica para saltos múltiplos obrigatórios.
        """
        if self.status != "Playing":
            return

        current_player_char = self.players[self.turn % 2]
        if current_player_char != self.computer_player:
            return

        performed_move = False # Flag para rastrear se algum movimento foi feito

        # Loop para permitir múltiplos saltos pela IA
        while True:
            self.update_mandatory_moves() # Sempre atualiza os movimentos obrigatórios para o estado atual

            # Se estivermos em um salto contínuo, a IA só pode mover a peça selecionada
            if self.jumping and self.selected_piece:
                piece_pos_tuple = (self.selected_piece[0], self.selected_piece[1])
                possible_moves_for_selected_piece = []
                if piece_pos_tuple in self.mandatory_moves:
                    for dest_pos, jumped_piece_pos in self.mandatory_moves[piece_pos_tuple]:
                        if jumped_piece_pos: # Deve ser uma captura
                            possible_moves_for_selected_piece.append({
                                'piece_pos': piece_pos_tuple,
                                'dest_pos': dest_pos,
                                'jumped_piece_pos': jumped_piece_pos
                            })
                valid_computer_moves = possible_moves_for_selected_piece
            else:
                # Não está em salto contínuo, procura todos os movimentos, priorizando capturas
                valid_computer_moves = []
                # Primeiramente, coleta todas as capturas disponíveis
                all_captures = []
                for piece_pos, moves_info in self.mandatory_moves.items():
                    # Certifica-se de que a peça pertence ao computador
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
                    # Se não houver capturas, coleta todos os movimentos normais
                    for piece_pos, moves_info in self.mandatory_moves.items():
                         # Certifica-se de que a peça pertence ao computador
                        if self.board[piece_pos[0]][piece_pos[1]].lower() == self.computer_player:
                            for dest_pos, jumped_piece_pos in moves_info:
                                if not jumped_piece_pos: # Movimento normal (jumped_piece_pos is None)
                                    valid_computer_moves.append({
                                        'piece_pos': piece_pos,
                                        'dest_pos': dest_pos,
                                        'jumped_piece_pos': None
                                    })

            if not valid_computer_moves:
                break # Nenhum movimento disponível, sai do loop do turno da IA

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
                    score += 100 # Grande bônus para qualquer captura
                    # Verifica o potencial de capturas consecutivas após este movimento (no tabuleiro simulado)
                    post_jump_captures_simulated = self._get_capture_moves(dest_pos, temp_board, self.computer_player)
                    if post_jump_captures_simulated:
                        score += 500 # Bônus ainda maior por levar a outro salto

                if promoted_to_king:
                    score += 200 # Alto bônus por se tornar uma dama

                # Valor posicional - prioriza mover para o lado do oponente ou centro
                if self.computer_player == 'x': # Rosas movem para baixo (linhas maiores)
                    score += dest_pos[0] * 5 # Mais pontos para linhas mais avançadas
                else: # Azuis movem para cima (linhas menores)
                    score += (7 - dest_pos[0]) * 5 # Mais pontos para linhas mais avançadas

                # Controle central
                center_cols = {2, 3, 4, 5}
                if dest_pos[1] in center_cols:
                    score += 5

                # Verificação básica de segurança (evitar captura imediata pelo oponente)
                if not self.is_position_safe(dest_pos, temp_board, self.computer_player):
                    score -= 150 # Penalidade significativa por pousar em um local perigoso

                if score > best_score:
                    best_score = score
                    best_move = move_data

            if best_move:
                # Executa o movimento escolhido
                self.make_move(self.computer_player, best_move['piece_pos'],
                               best_move['dest_pos'][0], best_move['dest_pos'][1],
                               best_move['jumped_piece_pos'])

                # Se a função make_move determinou que mais saltos são necessários para a mesma peça,
                # ela terá definido self.jumping = True e mantido self.selected_piece.
                # Se não, self.jumping será False e selected_piece None, e ela terá chamado next_turn().
                if self.jumping: # Se um salto acabou de ser realizado e mais saltos são possíveis para esta peça
                    # É necessário renderizar o tabuleiro e pausar brevemente para mostrar o salto antes do próximo
                    display.fill(BG_COLOR)
                    self.draw()
                    pygame.display.update()
                    pygame.time.wait(AI_DELAY_MS // 2) # Atraso menor para múltiplos saltos
                    continue # Continua o loop 'while True' para realizar o próximo salto
                else:
                    performed_move = True # Um movimento (ou sequência de saltos) foi concluído
                    break # Todos os saltos foram feitos, ou foi um movimento normal, então encerra o turno da IA
            else:
                # Não deveria acontecer se valid_computer_moves não estiver vazia, mas um break de segurança
                break

        # Após o loop 'while', se algum movimento foi realizado, o turno é considerado completo.
        # A função next_turn() já foi chamada por make_move (a menos que fosse uma sequência de múltiplos saltos
        # que agora está finalizada). Então, garantimos que computer_turn_active seja False e o timer seja resetado.
        if performed_move:
            self.computer_turn_active = False
            self.ai_move_timer = None
        else: # Nenhum movimento foi feito, talvez a IA não tenha movimentos ou algo deu errado. Finaliza o turno.
            if self._current_player_char == self.computer_player:
                self.next_turn()  # Força o próximo turno se a IA não conseguir fazer um movimento
        self.computer_turn_active = False
        self.ai_move_timer = None


    def is_position_safe(self, pos, board, current_player_char):
        row, col = pos
        opponent_char = 'x' if current_player_char == 'o' else 'o'

        # Itera por todas as peças do oponente no tabuleiro
        for r_op in range(8):
            for c_op in range(8):
                piece_op = board[r_op][c_op]
                if piece_op.lower() == opponent_char:
                    # Verifica se esta peça do oponente pode capturar a peça em 'pos'
                    opponent_captures = self._get_capture_moves((r_op, c_op), board, opponent_char)
                    for dest_op, jumped_op, _ in opponent_captures:
                        if jumped_op == (row, col): # Se o oponente puder pular *minha* peça em (row,col)
                            return False # Posição não é segura
        return True
    
    def run_ai_move(self):
        self.lock.acquire()
        try:
            pygame.time.wait(500)
            self.computer_move()
        finally:
            self.lock.release()


    def draw(self):
        for row in range(8):
            for col in range(8):
                color = BOARD_WHITE if (row + col) % 2 == 0 else BOARD_BLACK
                pygame.draw.rect(display, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Destaca peças com movimentos obrigatórios em amarelo
        current_player_char = self.players[self.turn % 2]
        for (row, col), moves_info in self.mandatory_moves.items():
            # Verifica se a peça em (row, col) pertence ao jogador atual e tem saltos
            # Uma peça é destacada se tiver qualquer movimento válido
            if self.board[row][col].lower() == current_player_char:
                # Se houver qualquer salto para esta peça, destaqua-a em amarelo
                if any(mi[1] is not None for mi in moves_info): # Se algum dos movimentos for um salto
                    pygame.draw.rect(display, YELLOW, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)


        # Destaca a peça selecionada e seus possíveis movimentos de destino
        if self.selected_piece:
            row, col = self.selected_piece
            # Destaca a peça selecionada em verde claro
            pygame.draw.rect(display, LIGHT_GREEN, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

            possible_destinations, _ = self.get_possible_moves(self.selected_piece)
            for move in possible_destinations:
                x = move[1] * SQUARE_SIZE
                y = move[0] * SQUARE_SIZE
                pygame.draw.rect(display, LIGHT_GREEN, (x, y, SQUARE_SIZE, SQUARE_SIZE), 3) # Destaca possíveis destinos

        # Desenha as peças
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '-':
                    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2

                    if piece.lower() == 'x': # Peças rosas
                        if piece.isupper(): # É uma dama (X)
                            if CROWN_PINK_IMAGE:
                                image_x = center_x - CROWN_PINK_IMAGE.get_width() // 2
                                image_y = center_y - CROWN_PINK_IMAGE.get_height() // 2
                                display.blit(CROWN_PINK_IMAGE, (image_x, image_y))
                            else: # Fallback se a imagem não for encontrada, desenha um círculo com um ponto amarelo
                                pygame.draw.circle(display, PINK, (center_x, center_y), 20)
                                pygame.draw.circle(display, YELLOW, (center_x, center_y), 10) # Fallback para dama
                        else: # Peça regular rosa
                            pygame.draw.circle(display, PINK, (center_x, center_y), 20)
                    else: # Peças azuis
                        if piece.isupper(): # É uma dama (O)
                            if CROWN_BLUE_IMAGE:
                                image_x = center_x - CROWN_BLUE_IMAGE.get_width() // 2
                                image_y = center_y - CROWN_BLUE_IMAGE.get_height() // 2
                                display.blit(CROWN_BLUE_IMAGE, (image_x, image_y))
                            else: # Fallback se a imagem não for encontrada, desenha um círculo com um ponto amarelo
                                pygame.draw.circle(display, BLUE, (center_x, center_y), 20)
                                pygame.draw.circle(display, YELLOW, (center_x, center_y), 10) # Fallback para dama
                        else: # Peça regular azul
                            pygame.draw.circle(display, BLUE, (center_x, center_y), 20)

        # Draw game info
        pink_pieces_remaining = sum(row.count('x') + row.count('X') for row in self.board)
        blue_pieces_remaining = sum(row.count('o') + row.count('O') for row in self.board)

        # Posição X base para centralizar texto no painel lateral
        panel_center_x = BOARD_WIDTH_PX + SIDE_PANEL_WIDTH // 2

        if self.status != 'Game Over':
            # Exibe peças capturadas
            # Rosa (jogador 'x') captura peças azuis ('o')
            pink_captured_count = 12 - blue_pieces_remaining
            pink_text = small_font.render(f"Rosa: {pink_captured_count}", True, PINK)
            pink_text_rect = pink_text.get_rect(center=(panel_center_x, 30))
            display.blit(pink_text, pink_text_rect)

            # Azul (jogador 'o') captura peças rosas ('x')
            blue_captured_count = 12 - pink_pieces_remaining
            blue_text = small_font.render(f"Azul: {blue_captured_count}", True, BLUE)
            blue_text_rect = blue_text.get_rect(center=(panel_center_x, HEIGHT - 50))
            display.blit(blue_text, blue_text_rect)

            # Exibe o turno atual
            if self.turn % 2 == 0:
                turn_text = large_font.render("Turno do Azul", True, BLUE)
            else:
                turn_text = large_font.render("Turno do Rosa", True, PINK)
            turn_text_rect = turn_text.get_rect(center=(panel_center_x, HEIGHT // 2 - 20))
            display.blit(turn_text, turn_text_rect)

            # Mostra mensagem se houver capturas obrigatórias
            has_captures_for_current_player = any(
                any(move_info[1] is not None for move_info in moves_list)
                for piece_pos, moves_list in self.mandatory_moves.items()
                if self.board[piece_pos[0]][piece_pos[1]].lower() == self._current_player_char
            )

            if has_captures_for_current_player:
                capture_text = medium_font.render("Captura obrigatória!", True, RED)
                capture_text_rect = capture_text.get_rect(center=(panel_center_x, HEIGHT // 2 + 20))
                display.blit(capture_text, capture_text_rect)

            # Mostra o modo de jogo
            if self.vs_computer:
                mode_text = small_font.render("Modo: vs Computador", True, WHITE)
            else:
                mode_text = small_font.render("Modo: 2 Jogadores", True, WHITE)
            mode_text_rect = mode_text.get_rect(center=(panel_center_x, HEIGHT // 2 + 70))
            display.blit(mode_text, mode_text_rect)

       


# UI Helper Functions
def text_objects(text, font, color):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()

# create_button agora apenas desenha, não lida com ações
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

def show_credits():
    """Exibe a tela de créditos."""
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Retorna um sinal para o menu principal sair
                return 'quit'
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False # Apenas sai deste loop para voltar ao menu

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

def show_rules():
    """Exibe a tela de regras do jogo."""
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Retorna um sinal para o menu principal sair
                return 'quit'
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False # Apenas sai deste loop para voltar ao menu

        display.fill(BLACK)

        rules = [
            "Regras do Jogo de Damas:",
            "",
            "1. Damas é jogado em um tabuleiro 8x8 com 64 casas.",
            "2. O objetivo é capturar todas as peças do oponente ou bloquear seus movimentos.",
            "3. As peças comuns se movem na diagonal para frente, uma casa por vez.",
            "4. Quando uma peça alcança a última fileira do oponente, ela se torna uma dama (rei).",
            "5. As damas podem se mover e capturar tanto para frente quanto para trás na diagonal,",
            "   em qualquer número de casas vazias.",
            "6. Capturar é obrigatório! Se uma peça pode capturar, ela deve fazê-lo.",
            "   (Não há a regra do 'sopro' - peças com capturas obrigatórias são destacadas em amarelo).",
            "7. Duas ou mais peças juntas na mesma diagonal não podem ser capturadas em um único movimento.",
            "8. Capturas múltiplas podem ser encadeadas: se uma peça puder capturar novamente após um salto,",
            "   ela deve fazê-lo na mesma vez.",
            "9. Uma peça ameaçada é aquela que pode ser capturada no próximo turno do oponente.",
            "",
            "Dicas de Jogo:",
            "  - Clique em uma peça para selecioná-la. Seus movimentos válidos serão destacados em verde.",
            "  - Se nada acontecer ao clicar em uma peça, ela pode não ter movimentos válidos ou não é sua vez.",
            "",
            "Aperte qualquer tecla ou clique para retornar ao menu"
        ]
        
        for i, rule in enumerate(rules):
            color = WHITE
            font_to_use = small_font
            if i == 0:
                font_to_use = medium_font
            elif i > 0 and i < 12: # Regras principais
                color = BLUE
            elif "Dicas de Jogo:" in rule: # Título da seção de dicas
                font_to_use = medium_font
            elif "Aperte" in rule:
                color = LIGHT_GREEN

            text_surf, text_rect = text_objects(rule, font_to_use, color)
            # Ajusta a posição para ser legível e o mais centralizada possível
            text_rect.x = 20 # Alinha à esquerda
            text_rect.y = 20 + i * 25 # Espaçamento vertical
            display.blit(text_surf, text_rect)

        pygame.display.update()
        clock.tick(60)
    return 'menu' # Retorna um sinal para o menu principal continuar

def show_winner(winner):
    """Exibe a tela do vencedor após o término de um jogo."""
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit() # Sai da aplicação se a janela for fechada
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False # Retorna ao menu em qualquer tecla ou clique

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

def game_loop(vs_computer=False):
    """Função do loop principal do jogo."""
    game = Game(vs_computer)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit' # Sinaliza para o main_menu que é para sair do jogo
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.status == 'Playing' and not game.computer_turn_active: # Permite clique humano apenas se não for o turno ativo da IA
                    game.evaluate_click(event.pos)
            if event.type == pygame.KEYDOWN:
                pass # Nenhuma ação imediata no game_loop para keydown/mouseup

        # Lógica do turno do computador
        # A IA só joga se o jogo estiver em andamento, for o modo vs computador,
        # a flag 'computer_turn_active' estiver ativada e o timer tiver expirado.
        if game.status == 'Playing' and game.vs_computer and game.computer_turn_active:
            if game.ai_move_timer and pygame.time.get_ticks() >= game.ai_move_timer:
                game.computer_move() # Esta chamada agora lida com todos os saltos consecutivos da IA
                # A lógica de desativar computer_turn_active e resetar o timer está agora dentro de computer_move
                # para garantir que só ocorra após toda a sequência de movimentos da IA.

        display.fill(BG_COLOR)
        game.draw()
        pygame.display.update()
        clock.tick(60) # Limita a taxa de quadros a 60 FPS

        # Verifica o status do jogo após cada atualização (movimento do jogador ou IA)
        if game.status == 'Game Over':
            show_winner(game.check_winner())
            running = False # Sai do loop do jogo para retornar ao menu principal
    return 'menu' # Sinaliza para voltar ao menu

    def run_ai_move(self):
        self.lock.acquire()
        try:
            pygame.time.wait(AI_DELAY_MS)
            self.computer_move()
        finally:
            self.lock.release()
