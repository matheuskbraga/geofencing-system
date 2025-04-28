import socket
import time

# Configuração do socket e endereço do Tello
tello_address = ('192.168.10.1', 8889)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Função para enviar comandos para o Tello
def send_command(command):
    sock.sendto(command.encode(), tello_address)

# Função para conectar ao Tello
def connect():
    print("Conectando ao Tello...")
    send_command('command')
    time.sleep(2)
    print("Conectado!")

# Função para decolar
def takeoff():
    print("Decolando...")
    send_command('takeoff')
    time.sleep(5)
    print("Drone no ar!")

# Função para pousar
def land():
    print("Pousando...")
    send_command('land')
    time.sleep(5)
    print("Drone pousado!")

# Função para executar uma sequência simples
def main():
    connect()
    takeoff()
    time.sleep(5)  # Voa por 5 segundos
    land()

if __name__ == "__main__":
    main()
