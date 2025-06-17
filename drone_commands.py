from dataclasses import dataclass
from djitellopy import Tello

def requires_connection(func):
    """
    Decorator que garante que o drone esteja conectado antes de executar o comando.
    """
    def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            raise Exception("Drone não está conectado! Por favor, execute connect() primeiro.")
        return func(self, *args, **kwargs)
    return wrapper

@dataclass
class TelloConfig:
    host: str = "192.168.10.1"
    command_port: int = 8889

class TelloController:
    def __init__(self, config: TelloConfig = None):
        if config is None:
            config = TelloConfig()
        self.config = config
        self.tello = Tello()
        self._connected = False

    def connect(self):
        """
        Tenta conectar com o drone e atualiza o estado de conexão.
        """
        response = self.tello.connect()
        self._connected = bool(response)
        return response

    def is_connected(self):
        """
        Retorna True se o drone estiver conectado; False caso contrário.
        """
        return self._connected

    @requires_connection
    def takeoff(self):
        return self.tello.takeoff()

    @requires_connection
    def land(self):
        return self.tello.land()

    @requires_connection
    def move_up(self, distance: int):
        return self.tello.move_up(distance)

    @requires_connection
    def move_down(self, distance: int):
        return self.tello.move_down(distance)

    @requires_connection
    def move_forward(self, distance: int):
        return self.tello.move_forward(distance)

    @requires_connection
    def move_left(self, distance: int):
        return self.tello.move_left(distance)

    @requires_connection
    def move_right(self, distance: int):
        return self.tello.move_right(distance)

    @requires_connection
    def move_back(self, distance: int):
        return self.tello.move_back(distance)

    @requires_connection
    def end(self):
        response = self.tello.end()
        self._connected = False
        return response
