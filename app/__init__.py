from .config import paths, settings
from .conn import Connection
from .screens import BoardScreen, HomeScreen, SettingsScreen
from .sound import SoundPlayer
from pyglet import app
from pyglet import clock
from pyglet import window
from threading import Thread
import os

class Application(window.Window):
    """
    Classe principal do aplicativo.
    """
    
    __FRAMES_PER_SECOND = 60
    
    def __init__(self, title, chess_game):
        super().__init__(
            caption = title,
            width = settings.size[0],
            height = settings.size[1],
            resizable = False
        )

        self.paths = paths

        self.__address = settings.address
        self.__connection = None

        self.__chess_game = chess_game
        self.__sound_player = SoundPlayer(settings.volume, settings.muted)

        self.__initialize_screens()
        self.__current_screen = self.__home_screen
        
        clock.schedule_interval(self.on_draw, 1 / self.get_fps())

    def __initialize_screens(self):
        """
        Inicializa todas as telas do jogo.
        """
        self.__home_screen = HomeScreen(self)
        self.__home_screen.set_play_function(self.__start_game)
        self.__home_screen.set_settings_function(self.__show_settings_screen)
        self.__home_screen.set_history_function(self.__show_history_screen)
        self.__home_screen.set_achivements_function(self.__show_achivements_screen)
        
        self.__board_screen = BoardScreen(self)
        self.__board_screen.set_board_coordinates(True)
        
        self.__settings_screen = SettingsScreen(self)

    def __finish_online_match_by_error(self):
        """
        Encerra a partida online informando que houve um erro.
        """
        self.go_back()
        self.__current_screen.set_popup_message("Conexão perdida.")

        return False

    def __get_movement(self):
        """
        Retorna a jogada realizada pelo outro jogador, se houver.
        """
        if self.__connection.is_connected():
            return self.__connection.recv()

        return self.__finish_online_match_by_error()

    def __send_movement(self, origin, dest):
        """
        Envia a jogada realizada para o outro jogador.
        """
        if self.__connection.is_connected():
            self.__connection.send(origin, dest)
            return True

        return self.__finish_online_match_by_error()
            
    def __show_achivements_screen(self):
        """
        Alterna para a tela de conquistas.
        """
        self.__current_screen.set_popup_message("Conquistas indisponíveis no momento", "(ಥ﹏ಥ)")

    def __show_history_screen(self):
        """
        Alterna para a tela de histórico de partidas.
        """
        self.__current_screen.set_popup_message("Histórico indisponível no momento", "(ಥ﹏ಥ)")

    def __show_settings_screen(self):
        """
        Alterna para a tela de configurações.
        """
        self.__current_screen = self.__settings_screen

    def __start_connection(self, host_mode):
        """
        Inicia uma conexão com outro jogador.
        """
        self.__connection = Connection(settings.address, host_mode)
        
        attempts = 10
        
        for i in range(attempts):
            self.__connection.connect(timeout = 0.3)
            if self.__connection.is_connected(): return True
        return False
        
    def __start_game(self, selection):
        """
        Inicia o jogo, dada uma seleção (local ou online).
        """

        # Inicia o jogo localmente.
        if selection == 1: return self.__local_game()

        # Inicia o jogo online.
        self.__current_screen.set_popup_message("Procurando por um jogador na rede...", "Por favor, aguarde.")
        clock.schedule_once(lambda interval: self.__start_online_game(selection), 1 / self.get_fps() * 2)

    def __start_local_game(self):
        """
        Inicia o jogo no modo local.
        """
        self.__board_screen.set_new_game(self.__chess_game, self.__board_screen.LOCAL_MODE)
        self.__current_screen = self.__board_screen

    def __start_online_game(self, selection):
        """
        Inicia o jogo no modo online.
        """
        # Tentar estabelecer uma conexão.
        if not self.__start_connection(selection == 2):
            return self.__current_screen.set_popup_message("Infelizmente, não foi possível conectar.", "Por favor, verique a sua conexão.")
        
        self.__board_screen.set_new_game(
            self.__chess_game, self.__board_screen.ONLINE_MODE,
            self.__send_movement, self.__get_movement, selection == 2
        )
        self.__current_screen = self.__board_screen
  
    def get_fps(self):
        """
        Retorna a taxa de frames por segundo do aplicativo.
        """
        return self.__FRAMES_PER_SECOND

    def get_ip_address(self):
        """
        Retorna o endereço IP do usuário.
        """
        return self.__address[0]

    def get_sound_player(self):
        """
        Retorna o reprodutor de som.
        """
        return self.__sound_player

    def go_back(self):
        """
        Volta uma tela para trás.
        """
        if self.__connection:
            self.__connection.close()
            self.__connection = None
            
        self.__current_screen = self.__home_screen

    def on_draw(self, interval = None):
        """
        Evento para desenhar a tela.
        """
        self.clear()
        self.__current_screen.on_draw(not interval is None)

    def on_key_press(self, *args):
        """
        Evento de tecla pressionada.
        """
        self.__current_screen.on_key_press(*args)

    def on_mouse_motion(self, *args):
        """
        Evento de movimentação do cursor.
        """
        self.__current_screen.on_mouse_motion(*args)

    def on_mouse_release(self, *args):
        """
        Evento de botão do mouse pressionado e liberado.
        """
        self.__current_screen.on_mouse_release(*args)

    def resize(self, width, height):
        """
        Altera o tamanho da tela do aplicativo.
        """
        self.width = width
        self.height = height
        self.__initialize_screens()

    def run(self):
        """
        Inicia a execução do aplicativo.
        """
        app.run()    

    def save_settings(self):
        """
        Salva todas as configurações atuais do aplicativo serão salvas.
        """
        settings.address = self.__address
        settings.size = [self.width, self.height]
        settings.volume = self.__sound_player.get_volume()
        settings.muted = self.__sound_player.is_muted()

    def set_ip_address(self, address):
        """
        Define um endereço IP para o usuário.
        """
        self.__address[0] = address
