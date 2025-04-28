import socket
import math



# Configuração do socket e endereço do Tello
tello_address = ('192.168.10.1', 8889)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Função para enviar comandos para o Tello
def send_command(command):
    sock.sendto(command.encode(), tello_address)

##############################################################
HOST = '0.0.0.0'  # Aceitar conexões de qualquer IP local
PORT = 3333

# Configurar o raio da cerca (em metros)
GEOFENCE_RADIUS_METERS = 30  # Exemplo: 30 metros

# Variáveis globais
origin_lat = None
origin_lon = None

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

def main():
    global origin_lat, origin_lon

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"Servidor escutando em {HOST}:{PORT}...")
    conn, addr = server_socket.accept()
    print(f"Conexão recebida de {addr}")

    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode('utf-8').strip()
            print("Dados recebidos:", message)

            try:
                parts = message.split(',')
                lat = float(parts[0].split(':')[1])
                lon = float(parts[1].split(':')[1])
                alt = float(parts[2].split(':')[1])

                print(f"Latitude: {lat}, Longitude: {lon}, Altitude: {alt} metros")

                if origin_lat is None or origin_lon is None:
                    # Salvar a primeira posição recebida como origem
                    origin_lat = lat
                    origin_lon = lon
                    print(f"Posição inicial definida: ({origin_lat}, {origin_lon})\n")
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


            except Exception as e:
                print(f"Erro no parsing dos dados: {e}")


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
    send_command('forward 100')  # Avança 100 cm (1 metro)
    time.sleep(5)  # Aguarda o movimento ser concluído
    print("Drone avançou 1 metro!")

# Função para pousar
def land():
    print("Pousando...")
    send_command('land')
    time.sleep(5)
    print("Drone pousado!")

# Função para executar uma sequência simples
def executar_drone():
    connect()
    takeoff()
    #time.sleep(5)  # Voa por 5 segundos
    #land()

if __name__ == "__main__":
    main()
    executar_drone()
