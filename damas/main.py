from menu import main_menu # main_menu - menu principal com botões e título animado
from jogo import game_loop, show_rules, show_credits 
# game_loop - loop principal do jogo
# show_rules, show_credits - telas informativas

def main():
    while True:
        escolha = main_menu() # mostra o menu principal e espera o usuário clicar em um botão

        if escolha == "2players": # dois jogadores
            resultado = game_loop(vs_computer=False)
            if resultado == 'quit': # encerra o loop
                break

        elif escolha == "vscomp": # vs computador
            resultado = game_loop(vs_computer=True)
            if resultado == 'quit':
                break

        elif escolha == "rules": # regras
            resultado = show_rules()
            if resultado == 'quit':
                break

        elif escolha == "credits": # créditos 
            resultado = show_credits()
            if resultado == 'quit':
                break

        elif escolha == "quit": # sair do jogo
            break

if __name__ == "__main__": # execução do programa quando iniciado
    main()
