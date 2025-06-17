from dataclasses import dataclass
import customtkinter as ctk
import tkinter.font as tkFont
from drone_commands import TelloController

@dataclass(unsafe_hash=True)
class App(ctk.CTk):
    title_str: str = "Software de Delimitação"
    geometry_str: str = "1280x720"

    def __post_init__(self):
        # Chama explicitamente o construtor da classe base
        ctk.CTk.__init__(self)

        # Cria uma instância compartilhada do controlador
        controller = TelloController()

        # Define o modo de aparência e o tema padrão
        ctk.set_appearance_mode("light")  # "light", "dark" ou "system"
        ctk.set_default_color_theme("blue")
        
        # Configura título e dimensão da janela
        self.title(self.title_str)
        self.geometry(self.geometry_str)

        # Configuração do layout: 2 linhas x 2 colunas com peso para redimensionamento
        self.grid_columnconfigure((0, 1), weight=1, uniform="column")
        self.grid_rowconfigure((0, 1), weight=1, uniform="row")

        # Cria e organiza os 4 widgets no grid usando as funções criadoras
        widget1 = widget_configuracao(self, width=322, height=296)
        widget2 = widget_status(self, controller, width=322, height=296)
        widget3 = widget_monitoramento(self, width=767, height=480)
        widget4 = widget_controle_drone(self, controller, width=767, height=178)

        widget1.place(x=51,  y=36)
        widget2.place(x=51,  y=389)
        widget3.place(x=434,  y=36)
        widget4.place(x=434,  y=521)


def widget_configuracao(master, **kwargs):
    """
    Cria um frame de Configurações com os controles de operação e delimitação.
    """
    frame = ctk.CTkFrame(master, **kwargs)
    
    label = ctk.CTkLabel(frame, text="Configurações", font=("Arial", 20))
    label.place(x=100, y=5)

    label2 = ctk.CTkLabel(frame, text="Modo de operação:", font=("Arial", 12))
    label2.place(x=20, y=45)

    chckbox = ctk.CTkComboBox(frame, values=["Voo livre", "Modo delimitação"])
    chckbox.place(x=90, y=75)

    label3 = ctk.CTkLabel(frame, text="Modo de operação:", font=("Arial", 12))
    label3.place(x=20, y=125)

    slider = ctk.CTkSlider(frame, from_=0, to=100)
    slider.place(x=60, y=150)

    label4 = ctk.CTkLabel(frame, text="metros", font=("Arial", 12))
    label4.place(x=140, y=167)

    label5 = ctk.CTkLabel(frame, text="Raio de delimitação:", font=("Arial", 12))
    label5.place(x=20, y=200)

    input_text = ctk.CTkEntry(frame, placeholder_text="Digite a área (metros)", width=250)
    input_text.place(x=20, y=230)

    return frame


def widget_status(master, controller, **kwargs):
    """
    Cria um frame de Status que exibe informações do drone
    e possui um botão para conectar.
    """
    frame = ctk.CTkFrame(master, **kwargs)
    
    label = ctk.CTkLabel(frame, text="Status do Drone", font=("Arial", 20))
    label.place(x=100, y=5)

    label2 = ctk.CTkLabel(frame, text="Desconetado/Conectado", font=("Arial", 12), text_color="red")
    label2.place(x=20, y=45)

    label3 = ctk.CTkLabel(frame, text="Modo: Delimitação/VooLivre", font=("Arial", 12), text_color="green")
    label3.place(x=20, y=85)

    label4 = ctk.CTkLabel(frame, text="Lat: 0.00000, Long: 0,00000, Alt: 0,0m", font=("Arial", 12))
    label4.place(x=20, y=125)

    label5 = ctk.CTkLabel(frame, text="Distância: N/A", font=("Arial", 12))
    label5.place(x=20, y=165)

    label6 = ctk.CTkLabel(frame, text="Bateria: 50%", font=("Arial", 12))
    label6.place(x=20, y=205)
    
    button1 = ctk.CTkButton(frame, text="CONECTAR", font=("Arial", 12), command=controller.connect)
    button1.place(x=100, y=250)

    return frame


def widget_monitoramento(master, **kwargs):
    """
    Cria um frame destinado ao monitoramento (por enquanto vazio).
    """
    frame = ctk.CTkFrame(master, **kwargs)
    return frame


def widget_controle_drone(master, controller, **kwargs):
    """
    Cria um frame com os controles para operação do drone. Os botões serão habilitados
    se o drone estiver conectado e desabilitados caso contrário.
    """
    frame = ctk.CTkFrame(master, **kwargs)
    
    label = ctk.CTkLabel(frame, text="Controles do Drone", font=("Arial", 20))
    label.place(x=20, y=5)
    
    # Define o estado dos botões com base na verificação de conexão
    state = "normal" if controller.is_connected() else "disabled"

    # DECOLAR
    button1 = ctk.CTkButton(frame, text="DECOLAR", font=("Arial", 12), state=state, command=controller.takeoff)
    button1.place(x=20, y=50)

    # POUSAR
    button2 = ctk.CTkButton(frame, text="POUSAR", font=("Arial", 12), state=state, command=controller.land)
    button2.place(x=20, y=100)

    # FRENTE
    button3 = ctk.CTkButton(frame, text="FRENTE", font=("Arial", 12), state=state, command=lambda: controller.move_forward(60))
    button3.place(x=400, y=30)
        
    # TRÁS
    button4 = ctk.CTkButton(frame, text="TRÁS", font=("Arial", 12), state=state, command=lambda: controller.move_forward(60))
    button4.place(x=400, y=90)

    # DIREITA
    button5 = ctk.CTkButton(frame, text="DIREITA", font=("Arial", 12), state=state, command=lambda: controller.move_right(60))
    button5.place(x=500, y=60)

    # ESQUERDA
    button6 = ctk.CTkButton(frame, text="ESQUERDA", font=("Arial", 12), state=state, command=lambda: controller.move_left(60))
    button6.place(x=300, y=60)

    # SUBIR
    button7 = ctk.CTkButton(frame, text="SUBIR", font=("Arial", 12), state=state, command=lambda: controller.move_up(60))
    button7.place(x=320, y=140)

    # DESCER
    # Note que o comando utilizado foi controller.move_up;
    # se o desejado for descer, substitua por controller.move_down
    button8 = ctk.CTkButton(frame, text="DESCER", font=("Arial", 12), state=state, command=lambda: controller.move_up(60))
    button8.place(x=480, y=140)

    return frame

