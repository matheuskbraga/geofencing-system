import socket
import math
import threading
import logging
import time

# Configuração de logs
logging.basicConfig(filename='drone_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuração do socket e endereço do Tello
TELLO_IP = '192.168.10.1'
TELLO_PORT = 8889
TELLO_ADDRESS = (TELLO_IP, TELLO_PORT)

# Configuração do servidor para GPS
HOST = '0.0.0.0'  # Aceitar conexões de qualquer IP local
PORT = 3333

# Configuração do raio da cerca geográfica (em metros)
GEOFENCE_RADIUS_METERS = 30  # Exemplo: 30 metros

# Variáveis globais
origin_lat = None
origin_lon = None

# Modo de simulação (útil para testes)
SIMULACAO = False

# Criação do socket para comunicação com o drone
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(10)  # Timeout configurado para evitar bloqueios

# Função para enviar comandos ao drone
def send_command(command):
    try:
        if SIMULACAO:
            print(f"[Simulação] Comando enviado: {command}")
        else:
            sock.sendto(command.encode('utf-8'), TELLO_ADDRESS)
            response, _ = sock.recvfrom(1024)
            logging.info(f"Comando enviado: {command}, Resposta: {response.decode('utf-8')}")
            print(f"Resposta do drone: {response.decode('utf-8')}")
    except socket.timeout:
        logging.error("Erro: Timeout ao enviar comando.")
        print("Erro: Timeout ao enviar comando.")
    except Exception as e:
        logging.error(f"Erro ao enviar comando: {e}")
        print(f"Erro ao enviar comando: {e}")

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

# Função para avançar 1 metro
def forward():
    print("Avançando 1 metro...")
    send_command('forward 100')  # Avança 1 metro (100 cm)
    time.sleep(5)
    print("Drone avançou 1 metro!")

# Função para pousar
def land():
    print("Pousando...")
    send_command('land')
    time.sleep(5)
    print("Drone pousado!")

# Função para calcular distância entre dois pontos GPS usando Haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = R * c
    return distance

# Função para processar mensagens de GPS e verificar a cerca geográfica
def process_message(message):
    global origin_lat, origin_lon

    try:
        parts = message.split(',')
        if len(parts) == 3:
            lat = float(parts[0].split(':')[1])
            lon = float(parts[1].split(':')[1])
            alt = float(parts[2].split(':')[1])

            print(f"Latitude: {lat}, Longitude: {lon}, Altitude: {alt} metros")

            if origin_lat is None or origin_lon is None:
                # Salvar a primeira posição recebida como origem
                origin_lat = lat
                origin_lon = lon
                print(f"Posição inicial definida: ({origin_lat}, {origin_lon})\n")
                logging.info(f"Posição inicial definida: ({origin_lat}, {origin_lon})")
            else:
                # Calcular distância atual até a posição inicial
                distance = haversine(origin_lat, origin_lon, lat, lon)
                print(f"Distância até o centro: {distance:.2f} metros")

                if distance <= GEOFENCE_RADIUS_METERS:
                    print("✅ Dentro da área permitida.\n")
                    forward()
                else:
                    print("🚫 Fora da área permitida!\n")
                    land()
        else:
            print("Erro: formato da mensagem inválido!")
            logging.error("Formato da mensagem inválido!")
    except Exception as e:
        print(f"Erro no parsing dos dados: {e}")
        logging.error(f"Erro no parsing dos dados: {e}")

# Função para gerenciar conexões com clientes
def handle_client(conn, addr):
    print(f"Conexão recebida de {addr}")
    logging.info(f"Conexão recebida de {addr}")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode('utf-8').strip()
            print("Dados recebidos:", message)
            process_message(message)

# Função principal para iniciar o servidor
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Servidor escutando em {HOST}:{PORT}...")
    logging.info(f"Servidor escutando em {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

# Executa o programa
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Encerrando programa...")
        logging.info("Programa encerrado pelo usuário.")
    finally:
        sock.close()
        print("Recursos liberados.")
