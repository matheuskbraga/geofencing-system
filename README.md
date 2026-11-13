# Geofencing Lab: cerca virtual para drones

Software em Python para pilotar um drone **DJI Tello** pelo teclado e mantê-lo dentro de uma **cerca virtual** (raio + altura máxima). Um módulo **ESP8266 + GPS** pode enviar a posição real por Wi-Fi. A interface, em estilo educacional, mostra sensores, radar e registro de eventos em tempo real.

> **Status: em desenvolvimento.** Ainda não foi validado com o drone e o GPS reais. Veja [Limitações](#limitações) e [Segurança](#segurança) antes de voar.

---

## O que o projeto faz

- **Controle por teclado** do Tello (WASD, setas, decolar, pousar e emergência).
- **Cerca virtual (geofence)** em forma de cilindro: o movimento que sairia da área é **bloqueado antes** de ser enviado ao drone.
- **Monitoramento ao vivo:** bateria, altura, distância da origem, posição, GPS e violações.
- **Radar** com vista de cima: cerca, trilha do voo e o drone.
- **GPS opcional** (ESP8266 + módulo GPS): detecta o drone fora do perímetro mesmo sem comando seu, e pode pousá-lo automaticamente.
- **Modo demonstração** (`--demo`): testa tudo sem drone e sem GPS.

## Como funciona

```
                     ┌──────────────────────────────┐
  Teclado / mouse ──►│ interface.py (telas, teclas) │
                     └──────────────┬───────────────┘
                                    │ comandos (em outra thread)
                     ┌──────────────▼───────────────┐      ┌──────────────┐
                     │ drone_commands.py            │─────►│ Drone Tello  │
                     │ valida + consulta a cerca    │      └──────────────┘
                     └──────────────┬───────────────┘
                                    │ "este destino é permitido?"
                     ┌──────────────▼───────────────┐
                     │ geofence.py (regras puras)   │
                     └──────────────────────────────┘

  GPS ─► ESP8266 ─► Wi-Fi/UDP ─► gps.py ─► interface.py (checa a cerca com a posição real)
```

Duas camadas de proteção se complementam:

1. **Estimativa por comandos (dead reckoning):** antes de cada movimento, o sistema soma o deslocamento à posição estimada e recusa o que sairia da cerca.
2. **GPS:** confere a posição **real** a cada 0,5 s e registra (ou pousa) se o drone sair, por exemplo por deriva do vento.

---

## Instalação

Requisitos: **Python 3.10 ou superior** (testado no 3.13) e Windows, Linux ou macOS com Tkinter.

```bash
git clone https://github.com/matheuskbraga/geofencing-system
cd geofencing-system
pip install -r requirements.txt
```

## Uso

```bash
python main.py --demo   # simulado: não precisa de drone nem de GPS
python main.py          # com o Tello real
```

Com o drone real:

1. Ligue o Tello e conecte o computador ao Wi-Fi dele (`TELLO-XXXXXX`).
2. Abra o programa e clique em **CONECTAR**.
3. Escolha **Modo delimitação**, defina raio e altura máxima e clique em **APLICAR**.
4. Pressione **T** para decolar e pilote com o teclado.

### Teclas

| Tecla | Ação |
|---|---|
| `W` / `S` | Frente / Trás |
| `A` / `D` | Esquerda / Direita |
| `↑` (ou `R`) / `↓` (ou `F`) | Subir / Descer |
| `T` | Decolar |
| `L` ou `Espaço` | Pousar |
| `Esc` `Esc` | **Emergência**: desliga os motores (exige apertar duas vezes) |
| `+` / `-` | Aumenta / diminui a distância por movimento (20 a 500 cm) |

Segurar uma tecla repete o movimento. As teclas são ignoradas enquanto você digita num campo de texto (Esc ou um clique fora devolve o teclado ao voo).

---

## GPS com ESP8266 (opcional)

O firmware [`firmware/transmitter/transmitter.ino`](firmware/transmitter/transmitter.ino) lê o GPS e envia a posição por UDP para o computador (porta `5005`).

![Circuito ESP8266 + GPS](https://github.com/user-attachments/assets/5ecf19b9-f7c1-4b8c-b60c-8357f56ad39a)

| GPS (GY-GPS6MV2) | NodeMCU ESP8266 |
|---|---|
| TX | D5 (GPIO14) |
| RX | D6 (GPIO12) |
| VCC | 3V3 |
| GND | GND |

1. Na Arduino IDE, instale o pacote de placas **esp8266** e a biblioteca **TinyGPSPlus**.
2. Em `transmitter.ino`, preencha `WIFI_SSID` e `WIFI_PASS`. Deixe `PC_IP` vazio para enviar em *broadcast* ou informe o IP do computador.
3. Grave na placa (*NodeMCU 1.0*) e abra o Monitor Serial (115200) para ver os pacotes.
4. Permita o Python no firewall do Windows para a porta UDP **5005**.
5. No programa, use o botão **ORIGEM GPS** (ou decole: a origem é definida automaticamente).

Formato do pacote: `lat,lon,alt,sats,hdop,fix`, por exemplo `-23.550520,-46.633308,760.2,8,1.10,1`.

**Rede:** o PC precisa estar no Wi-Fi do Tello e o ESP numa rede que o PC alcance. O mais simples é o ESP entrar no Wi-Fi do próprio Tello (o *broadcast* cobre isso). Alternativa: um segundo adaptador de rede no PC.

---

## Estrutura do projeto

| Arquivo | Função |
|---|---|
| `main.py` | Ponto de entrada (`--demo` para o modo simulado) |
| `interface.py` | Telas, teclado e execução de comandos em threads |
| `widgets.py` / `theme.py` | Componentes visuais (cartões, sensores, radar) e paleta |
| `keyboard.py` | Mapa de teclas e confirmação da emergência |
| `drone_commands.py` | Controle do Tello, validações e checagem da cerca |
| `geofence.py` | Regras da cerca, registro de violações e Haversine |
| `gps.py` | Recepção UDP do GPS e conversão para metros |
| `simulator.py` | Drone e GPS simulados (`--demo`) |
| `config.py` | Constantes (limites, portas, tempos) |
| `firmware/transmitter/` | Firmware do ESP8266 |
| `tests/` | Testes automatizados |
| `docs/Explicacao_do_Codigo.pdf` | **Guia completo**: arquitetura e código explicado trecho por trecho |

Quer entender o código a fundo? Leia o [guia em PDF](docs/Explicacao_do_Codigo.pdf).

## Testes

```bash
python -m pytest -q
```

Os testes não precisam de drone, rede nem janela: usam um Tello falso.

---

## Limitações

- **Posição estimada:** sem GPS, a posição vem da soma dos comandos e pode divergir da real (vento, imprecisão).
- **Precisão do GPS:** módulos como o NEO-6M erram tipicamente 2,5 m ou mais. Prefira raios de **15 m ou mais** e uso **ao ar livre**.
- **Movimento em passos:** o Tello recebe comandos do tipo "andar 60 cm", não velocidade contínua.
- **Sem giro:** o drone não gira; "frente" é sempre o sentido da decolagem.
- **Radar** mostra a posição estimada pelos comandos, não a do GPS.
- Projeto feito para o **Tello**; outro drone exige adaptar `drone_commands.py`.
- O firmware e a integração com o hardware real ainda precisam de validação em campo.

## Segurança

Voe em área aberta, longe de pessoas, e comece com raios pequenos. O drone pode se comportar de forma inesperada: mantenha sempre à mão o **Esc duas vezes** (emergência) e o **L** (pousar). A cerca virtual é uma ajuda, não substitui a atenção do piloto nem as regras de voo da sua região.

## Roadmap

- [ ] Validar firmware e GPS em campo
- [ ] Retornar à origem automaticamente em violação
- [ ] Fundir GPS e estimativa por comandos (filtro)
- [ ] Suporte a giro (guinada) e controle contínuo (`send_rc_control`)
- [ ] Vídeo do Tello no painel de monitoramento
- [ ] Gravar o registro de violações em arquivo

## Licença

[MIT](LICENCE)
