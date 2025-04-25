import socket

# Defina o IP e a porta do servidor (deve ser o mesmo configurado no ESP8266)
local_ip = "0.0.0.0"  # A escuta de todas as interfaces
local_port = 8888

# Criar o socket UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((local_ip, local_port))

print(f"Esperando dados na {local_ip}:{local_port}...")

# Loop infinito para receber dados do ESP8266
while True:
    data, addr = server_socket.recvfrom(1024)  # Buffer de 1024 bytes
    print(f"Dados recebidos de {addr}: {data.decode()}")
