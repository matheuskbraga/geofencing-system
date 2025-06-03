from customtkinter import *

app = CTk()
app.geometry("1280x720")

# BOTÃO da interface
btn = CTkButton(master=app, text="Click Me")
btn.pack(padx=0, pady=100)

# COMBOBOX da interface
combobox = CTkComboBox(master=app, values=["Sem delimitação", "Delimitação estática"])
combobox.place(relx=0.5, rely=0.5, anchor="center")


# SLIDER da interface
slider = CTkSlider(master=app, from_=0, to=100, number_of_steps=100)
slider.place(x=100, y=200)

# TEXT BOX da interface
valor_delimitacao = CTkEntry(master=app, placeholder_text="Digite a delimitação a aqui...")
valor_delimitacao.place(x=100, y=300)



app.mainloop()