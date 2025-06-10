from dataclasses import dataclass
from djitellopy import Tello


@dataclass
class TelloConfig:
    host: str = "192.168.10.1"
    command_port: int = 8889
    # Aqui você pode incluir outros parâmetros de configuração se necessário


class TelloController:
    def __init__(self, config: TelloConfig = None):
        if config is None:
            config = TelloConfig()
        self.config = config
        self.tello = Tello()

    def connect(self):
        # conectar
        return self.tello.connect()

    def takeoff(self):
        # decolar
        return self.tello.takeoff()

    def land(self):
        # pousar
        return self.tello.land()
    
    def move_up(self, distance: int):
        # subir
        return self.tello.move_up(distance)
    
    def move_down(self, distance: int):
        # descer
        return self.tello.move_down(distance)
    
    def move_forward(self, distance: int):
        # move para frente
        return self.tello.move_forward(distance)

    def move_left(self, distance: int):
        # movimento para a esquerda
        return self.tello.move_left(distance)

    def move_right(self, distance: int):
        # movimento para a direita
        return self.tello.move_right(distance)
    
    def move_back(self, distance: int):
        # move para trás
        return self.tello.move_back(distance)

    def end(self):
        # fecha conexão com o drone
        return self.tello.end()
