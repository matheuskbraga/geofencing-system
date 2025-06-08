from dataclasses import dataclass
import customtkinter as ctk
import tkinter.font as tkFont


@dataclass(unsafe_hash=True)
class App(ctk.CTk):
    title_str: str = "Software de Delimitação"
    geometry_str: str = "1280x720"

    def __post_init__(self):
        # Chama explicitamente o construtor da classe base
        ctk.CTk.__init__(self)

        # Define o modo de aparência e o tema padrão
        ctk.set_appearance_mode("system")  # "light", "dark" ou "system"
        ctk.set_default_color_theme("blue")
        
        # Configura título e dimensão da janela
        self.title(self.title_str)
        self.geometry(self.geometry_str)

        # Configuração do layout: 2 linhas x 2 colunas com peso para redimensionamento
        self.grid_columnconfigure((0, 1), weight=1, uniform="column")
        self.grid_rowconfigure((0, 1), weight=1, uniform="row")

        # Cria e organiza os 4 widgets no grid
        widget1 = Widget_Configuracao(self, width=322, height=296)
        widget2 = Widget_Status(self, width=322, height=296)
        widget3 = Widget_Monitoramento(self, width=767, height=480)
        widget4 = Widget_ControleDrone(self, width=767, height=178)

        widget1.place(x=51,  y=36)
        widget2.place(x=51,  y=389)
        widget3.place(x=434,  y=36)
        widget4.place(x=434,  y=521)



class Widget_Configuracao(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_configuracao()

    def setup_configuracao(self):
        label = ctk.CTkLabel(self, text="Configurações", font=("Arial", 20))
        label.place(x=100, y=5)

        label2 = ctk.CTkLabel(self, text="Modo de operação:", font=("Arial", 12))
        label2.place(x=20, y=45)

        chckbox = ctk.CTkComboBox(self, values=["Voo livre", "Modo delimitação"])
        chckbox.place(x=90, y=75)

        label3 = ctk.CTkLabel(self, text="Modo de operação:", font=("Arial", 12))
        label3.place(x=20, y=125)

        slider = ctk.CTkSlider(self, from_=0, to=100)
        slider.place(x=60, y=150)

        label4 = ctk.CTkLabel(self, text="metros", font=("Arial", 12))
        label4.place(x=140, y=167)

        label5 = ctk.CTkLabel(self, text="Raio de delimitação:", font=("Arial", 12))
        label5.place(x=20, y=200)

        input_text = ctk.CTkEntry(self, placeholder_text="Digite a área (metros)", width=250)
        input_text.place(x=20, y=230)



class Widget_Status(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_status()

    def setup_status(self):
        label = ctk.CTkLabel(self, text="Status do Drone", font=("Arial", 20))
        label.place(x=100, y=5)

        label2 = ctk.CTkLabel(self, text="Desconetado/Conectado", font=("Arial", 12), text_color="red")
        label2.place(x=20, y=45)

        label3 = ctk.CTkLabel(self, text="Modo: Delimitação/VooLivre", font=("Arial", 12), text_color="green")
        label3.place(x=20, y=85)

        label4 = ctk.CTkLabel(self, text="Lat: 0.00000, Long: 0,00000, Alt: 0,0m", font=("Arial", 12))
        label4.place(x=20, y=125)

        label5 = ctk.CTkLabel(self, text="Distância: N/A", font=("Arial", 12))
        label5.place(x=20, y=165)

        label5 = ctk.CTkLabel(self, text="Bateria: 50%", font=("Arial", 12))
        label5.place(x=20, y=205)
        
        button1 = ctk.CTkButton(self, text="CONECTAR", font=("Arial", 12))
        button1.place(x=100, y=250)



class Widget_Monitoramento(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)



class Widget_ControleDrone(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_controle()

    
    def setup_controle(self):
        label = ctk.CTkLabel(self, text="Controles do Drone", font=("Arial", 20))
        label.place(x=20, y=5)

        # DECOLAR
        button1 = ctk.CTkButton(self, text="DECOLAR", font=("Arial", 12))
        button1.place(x=20, y=50)

        # POUSAR
        button2 = ctk.CTkButton(self, text="POUSAR", font=("Arial", 12))
        button2.place(x=20, y=100)

        # FRENTE
        button3 = ctk.CTkButton(self, text="FRENTE", font=("Arial", 12))
        button3.place(x=400, y=30)
        
        # TRÁS
        button4 = ctk.CTkButton(self, text="TRÁS", font=("Arial", 12))
        button4.place(x=400, y=90)

        # DIREITA
        button5 = ctk.CTkButton(self, text="DIREITA", font=("Arial", 12))
        button5.place(x=500, y=60)

        # ESQUERDA
        button6 = ctk.CTkButton(self, text="ESQUERDA", font=("Arial", 12))
        button6.place(x=300, y=60)

        # SUBIR
        button7 = ctk.CTkButton(self, text="SUBIR", font=("Arial", 12))
        button7.place(x=320, y=140)

        # DESCER
        button8 = ctk.CTkButton(self, text="DESCER", font=("Arial", 12))
        button8.place(x=480, y=140)