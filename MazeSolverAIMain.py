from Game import Game
from MainMenu import MainMenu
from GamePlay import GamePlay

game = Game("MazeSolving", 800, 600)
main_menu = MainMenu(game.screen)
game_play = GamePlay(game.screen)
main_menu.gameplay_scene = game_play
game_play.main_menu = main_menu


game.run(main_menu)

