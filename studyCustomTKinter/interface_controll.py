from customtkinter import *

app = CTk()
app.geometry("1280x720")


frameConfig = CTkFrame(master=app, width=322, height=310,fg_color="#8D6F3A", border_color="#FFCC70", border_width=2)
frameConfig.place(x=51, y=36)

frameDroneStatus = CTkFrame(master=app, width=322, height=310,fg_color="#3A688D", border_color="#70AEFF", border_width=2)
frameDroneStatus.place(x=51, y=390)

frameGPS = CTkFrame(master=app, width=760, height=480, fg_color="#3A8D69", border_color="#70FFFA", border_width=2)
frameGPS.place(x=434, y=36)

frameDroneController = CTkFrame(master=app, width=760, height=170, fg_color="#573A8D", border_color="#BA70FF", border_width=2)
frameDroneController.place(x=434, y=531)


app.mainloop()