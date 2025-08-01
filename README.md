# **Status: 🚧 In Development**

This project is currently under active development. Please exercise caution if using in production environments.

---

# Geofencing System com Drones

Este projeto é um software de geofencing desenvolvido para delimitar áreas tridimensionais com base em dados de localização geográfica de drones. A aplicação recebe dados de latitude, longitude e altitude via GPS e constrói, em tempo real, um "espaço aéreo virtual" para monitoramento e controle de áreas específicas.

---

## Funcionalidades

- Recebimento de coordenadas via GPS (latitude, longitude e altitude)
- Construção de um espaço tridimensional ao redor do drone
- Delimitação estática da área de atuação
- Registro e monitoramento de violações do perímetro
- Desenvolvimento baseado na metodologia FDD (Feature-Driven Development)

---

## Tecnologias Utilizadas

- Lingugens de programação Python e C++
- Libs: TinyGPS, Customtkinter
- Componentes eletrônicos: ESP8266 Node MCU, Módulo GNSS AT6558 e Bateria 3,7V 1000 mH

---

## Vídeo do Funcionamento

link: 

---

## Circuito eletrônico

![imagem](https://github.com/user-attachments/assets/5ecf19b9-f7c1-4b8c-b60c-8357f56ad39a)


---
## Como Executar

Observação: Este projeto foi desenvolvido especificamente para o drone Tello, da DJI, incluindo sua execução e controle via software. Caso outro modelo de drone seja utilizado, será necessário ajustar o código, especialmente nos trechos relacionados aos comandos de voo e/ou à linguagem de comunicação compatível com o novo dispositivo.

1. Clone este repositório:
   ```bash
   git clone https://github.com/matheuskbraga/geofencing-system
   
2. Altere o endereço do dispositivo no código transmitter.ino para o IP de quem irá rodar o software.

3. Ative o hotspot no dispositivo que rodará o software.

4. Conecte o ESP8266 à rede criada pelo hotspot.

5. Dê um git clone no repositório do projeto.

6. Instale as dependências com pip install -r requirements.txt.

7. Execute o arquivo main.py com python main.py.

8. Conecte o dispositivo na mesma rede do drone.

9. O sistema já estará funcionando e começará a monitorar automaticamente.
