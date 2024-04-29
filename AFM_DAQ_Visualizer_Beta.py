from tkinter import *
from tkinter import filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.signal import detrend

root = Tk()

root.title("AFMDAQ Visualizer Beta v0.1")

root.iconbitmap("Probe_2.ico")

Label(root, text="Welcome to the AFM CSV file processor. Select a file and the graphics to display").pack(side = "top")

#Almacenar el tipo seleccionado
tipo = StringVar()
tipo.set(None)  # Variable en un valor inicial que no coincida con los valores de los radio buttons

def seleccionar_tipo():
    print("Selected type:", tipo.get())
    tipo_seleccionado = tipo.get()
    if tipo_seleccionado == "PFM":
        # Mostrar checkboxes para PFM
        for checkbox, _ in pfm_checkboxes.values():
            checkbox.pack(anchor="w")
        # Ocultar checkboxes para Curvas de Fuerza
        for checkbox, _ in cf_checkboxes.values():
            checkbox.pack_forget()
        # Ocultar checkboxes para Topografía
        for checkbox, _ in topo_checkboxes.values():
            checkbox.pack_forget()
    elif tipo_seleccionado == "CF":
        # Mostrar checkboxes para Curvas de Fuerza
        for checkbox, _ in cf_checkboxes.values():
            checkbox.pack(anchor="w")
        # Ocultar checkboxes para PFM
        for checkbox, _ in pfm_checkboxes.values():
            checkbox.pack_forget()
        # Ocultar checkboxes para Topografía
        for checkbox, _ in topo_checkboxes.values():
            checkbox.pack_forget()
    elif tipo_seleccionado == "Topography":
        # Mostrar checkboxes para Topografía
        for checkbox, _ in topo_checkboxes.values():
            checkbox.pack(anchor="w")
        # Ocultar checkboxes para PFM
        for checkbox, _ in pfm_checkboxes.values():
            checkbox.pack_forget()
        # Ocultar checkboxes para Curvas de Fuerza
        for checkbox, _ in cf_checkboxes.values():
            checkbox.pack_forget()


# Opciones de la naturaleza del tipo de microscopía del cual proviene el csv
lbl_tipo = Label(root, text="Select the type of microscopy the file comes from:")
lbl_tipo.pack(anchor=W)

rb_pfm = Radiobutton(root, text="PFM", variable=tipo, value="PFM", command=seleccionar_tipo)
rb_pfm.pack(anchor=W)

rb_curvas_fuerza = Radiobutton(root, text="Force-time curves", variable=tipo, value="CF", command=seleccionar_tipo)
rb_curvas_fuerza.pack(anchor=W)

rb_topo = Radiobutton(root, text="Topography", variable=tipo, value="Topography", command=seleccionar_tipo)
rb_topo.pack(anchor=W)

def obtener_resolucion():
    # Obtener el valor del Entry y convertirlo a un entero
    valor = int(entry_resolucion.get())
    # Almacenar el valor en la variable resolucion
    resolucion.set(valor)

def obtener_perfil_fila():
    num_fila = int(entry_perfil_fila.get())
    perfil_fila.set(num_fila)

#Resolucion de pixeles nxn
Label(root, text="Pixel resolution:").pack(side=LEFT)
resolucion = IntVar()
entry_resolucion = Entry(root, textvariable=resolucion)
entry_resolucion.pack(side=LEFT)

#Botón para establecer la resolución
btn_establecer_resolucion = Button(root, text="Set resolution", command=obtener_resolucion)
btn_establecer_resolucion.pack(side= LEFT, anchor="w")

#Opcional, establecer donde se quiere el perfil de línea a lo largo del eje X
Label(root, text = "Indicate the pixel on the vertical axis where the line profile will be generated.").pack(side=LEFT, anchor="s")
perfil_fila = IntVar()
entry_perfil_fila = Entry(root, textvariable=perfil_fila)
entry_perfil_fila.pack(side=LEFT, anchor = "s")

#Botón para establecer el pixel de perfil de linea a lo largo de X
btn_perfil_fila = Button(root, text="Set row pixel", command=obtener_resolucion)
btn_perfil_fila.pack(side= LEFT, anchor="s")

"""
#Opcional, establecer donde se quiere el perfil de línea a lo largo del eje Y
Label(root, text = "Indique en cual pixel sobre el eje horizontal se hará el perfil de línea").pack(side=LEFT)
perfil_col = IntVar()
entry_perfil_col = Entry(root, textvariable=perfil_col)
entry_perfil_col.pack(side=LEFT, anchor = "w")
"""

#Variable global para almacenar la ruta del archivo CSV
ruta_archivo_csv = ""

def procesar_csv_PFM(ruta_archivo, opciones_seleccionadas, resolucion):

    global ruta_archivo_csv
    
    if not ruta_archivo_csv:
        print("No CSV file selected.")
        return

     # Importar los datos usando pandas
    data = pd.read_csv(ruta_archivo, skiprows=5, header=None)

    # Asignar nombres a las columnas
    data.columns = ["Dev1ai0", "Dev1ai1", "Dev1ai2", "Dev1ai3", "Deva1ai4", "Deva1ai5"] #[Frame, Line, Pixel, Topo, Amp, Fase]

    # Obtener valores de los datos como matriz numpy
    data_array = data.values

    dimensiones = data_array.shape
    len_filas = dimensiones[0]  # Número de filas
    len_columnas = dimensiones[1]  # Número de columnas

    print(f"La matriz de todos los datos tiene {len_filas} filas y {len_columnas} columnas.")

    m = resolucion.get()
    n = resolucion.get()

    amp = np.zeros((n,m))
    fase = np.zeros((n,m))
    topo = np.zeros((n, m))
    linepos = np.zeros(n)

    dframe = np.diff(data_array[:, 0])  # Derivada de frame

    # Detectar inicio y fin de frame
    frame0 = 0
    framef = 0
    ind = 0
    for i in range(len(dframe)):
        if dframe[i] < -2 and ind == 0:
            frame0 = i
            ind = 1
        if dframe[i] > 2 and ind == 1:
            framef = i

    # Rutina para encontrar las posiciones de las líneas

    dline = np.diff(data_array[:, 1])  # Derivada de la señal de línea

    lp = 0  # Inicializar lp en 0 en lugar de 1
    for i in range(frame0 + 1, framef):
        if dline[i] > 2:
            if lp < n:  # Agregar esta condición para evitar salir del rango
                linepos[lp] = i #En otras palabras, i es el indice respecto a toda la toma de datos de la medida, lp es el indice de la matriz donde se almacena i
                lp += 1

    # Rutina para la reconstrucción de pixeles
    d1 = 160 #para 64 pix 1195 #/4 para 256 son casi 299
    d2 = 72 #para 64 pix 285 #/4 para 256 son casi 72
    #La proporcion d1/d2 debe ser aprox 4.15277
    for i in range(n):
        pos_i = int(linepos[i] + d1)  # Calcular la posición inicial para la fila i
        for j in range(m):
            topo[i, j] = data_array[pos_i, 3]
            amp[i, j] = data_array[pos_i, 4]
            fase[i, j] = data_array[pos_i, 5]
            pos_i += d2  # Actualizar la posición para la siguiente columna

    Altura = topo[:, :m]
    Altura *= 1000
    # Utilizar scipy.signal.detrend para detrender los datos
    Altura_detrended = detrend(Altura, axis=1, type='linear')
    Min_Z = abs(np.min(Altura_detrended))
    print(f"La altura mínima es de {Min_Z}")
    Altura_detrended += Min_Z

    num_fila = perfil_fila.get()

    perfil_topo = Altura_detrended[num_fila, :] #num_fila antes era 128
    perfil_amplitud = amp[num_fila, :]
    perfil_fase = fase[num_fila, :]

    if "2D Topography" in opciones_seleccionadas:
        # Grafica 2D de Topografía
        plt.figure()
        plt.imshow(Altura_detrended)
        plt.title('Topografía 2D')
        plt.colorbar(label='(V)')
        #plt.show()

    if "2D Amplitude" in opciones_seleccionadas:
        # Grafica 2D de Amplitud
        plt.figure()
        plt.imshow(amp)
        plt.title('Amplitud 2D')
        plt.colorbar(label='(V)')
        #plt.show()

    if "2D Phase" in opciones_seleccionadas:
        # Grafica 2D de Fase
        plt.figure()
        plt.imshow(fase)
        plt.title('Fase 2D')
        plt.colorbar(label='(V)')
        #plt.show()

    if "3D Topography" in opciones_seleccionadas:
        # Grafica 3D de Topografía
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(*np.meshgrid(np.arange(m), np.arange(n)), Altura_detrended, cmap='viridis')
        ax.set_title('3D Topography')
        ax.set_xlabel('Pixel X')
        ax.set_ylabel('Pixel Y')
        ax.set_zlabel('Z (V)')
        #plt.show()

    if "3D Amplitude" in opciones_seleccionadas:
        # Grafica 3D de Amplitud
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(*np.meshgrid(np.arange(m), np.arange(n)), amp, cmap='viridis')
        ax.set_title('3D Amplitude')
        ax.set_xlabel('X Pixel')
        ax.set_ylabel('Y Pixel')
        ax.set_zlabel('Amplitude (V)')
        #plt.show()

    if "3D Phase" in opciones_seleccionadas:
        # Grafica 3D de Fase
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(*np.meshgrid(np.arange(m), np.arange(n)), fase, cmap='viridis')
        ax.set_title('3D Phase')
        ax.set_xlabel('X Pixel')
        ax.set_ylabel('Y Pixel')
        ax.set_zlabel('Phase (V)')
        #plt.show()

    if "Topography line profile" in opciones_seleccionadas:
        # Perfil de Línea de Topografía
        #perfil = topo[128, :]
        plt.figure()
        plt.plot(perfil_topo)
        plt.title('Topography line profile')
        plt.xlabel('Pixel')
        plt.ylabel('Z (V)')
        #plt.show()

    if "Amplitude line profile" in opciones_seleccionadas:
        # Perfil de Línea de Amplitud
        #perfil = amp[128, :]
        plt.figure()
        plt.plot(perfil_amplitud)
        plt.title('Amplitude line profile')
        plt.xlabel('Pixel')
        plt.ylabel('Amplitude (V)')
        #plt.show()

    if "Phase line profile" in opciones_seleccionadas:
        # Perfil de Línea de Fase
        #perfil = fase[128, :]
        plt.figure()
        plt.plot(perfil_fase)
        plt.title('Phase line profile')
        plt.xlabel('Pixel')
        plt.ylabel('Phase (V)')
        #plt.show()

    plt.show()

def procesar_csv_CF(ruta_archivo, opciones_seleccionadas, resolucion):#, opciones_seleccionadas):
    #Importar los datos usando pandas
    data = pd.read_csv(ruta_archivo, skiprows=5, header=None)
    #Asignar nombres a las columnas
    data.columns = ["Dev1ai0", "Dev1ai1", "Dev1ai2", "Dev1ai3"] #[Line, Frame, Pixel, Vertical(A-B)]

    #Obtener valores de los datos como matriz numpy
    # Obtener valores de los datos como matriz numpy
    data_array = data.values

    dimensiones = data_array.shape
    len_filas = dimensiones[0]  # Número de filas
    len_columnas = dimensiones[1]  # Número de columnas

    print(f"La matriz de todos los datos tiene {len_filas} filas y {len_columnas} columnas.")

    n = 256
    m = 256

    #amp y fase solo si es necesario
    #amp = np.zeros((n,m))
    #fase = np.zeros((n,m))
    vertical = np.zeros((n, m)) #forward
    vertical2 = np.zeros((n,m)) #backward
    #linepos = np.zeros(n)


    dframe = np.diff(data_array[:, 1])  # Derivada de frame

    p = 1.6

    # Detectar inicio y fin de frame
    frame0 = 0
    framef = 0
    ind = 0
    for i in range(len(dframe)):
        if dframe[i] < -2.5 and ind == 0:
            frame0 = i
            ind = 1
        if dframe[i] > 2.5 and ind == 1:
            framef = i
            ind = 2
        if ind == 2:
            break

    print(f"Inicio de frame en {frame0}, final de frame en {framef}")


    #Correccion de pixeles problematicos

    pixel = data_array[:, 2] #cambio frame0:framef a :, todas las filas 

    print(len(pixel))

    for i in pixel:
        if ((i < 3.25) or (i > 0.025)): #inferior de 0.058 a 0.025, superior de 3.24 a 3.25
            difsup = 3.25 - i
            difinf = i - 0.025
            if difsup <= difinf:
                i= 0.025
            else:
                i= 0.025

    #Por favor Dios mío haz funcar este código 
    pixel[23579454:23579788] = pixel[23579789]

    print(len(pixel))

    #pixel_idx = np.where(pixel)[0] #variable para txt de indices de pixel arreglados

    #pixel ahora ya esta corregido, usar en lugar de pixfil

    np.savetxt('pixel.txt', pixel, delimiter=' ')
    #np.savetxt('pixel_idx.txt', pixel_idx, delimiter=' ') #txt de indices de pixel arreglados
    #Derivada de pixeles filtrados

    derpix_full = np.diff(pixel[frame0:framef])

    derpix = derpix_full[(derpix_full >= p) | (derpix_full <= -p)]

    derpix_pos = derpix_full[derpix_full >= p]
    derpix_neg = derpix_full[derpix_full <= -p]

    print(derpix)

    #Conservar los índices de las derivadas
    derpix_idx = np.where((derpix_full >= p) | (derpix_full <= -p))[0] + frame0 #porque ahora es desde el inicio de la medida, no desde frame0 

    derpix_idx_pos = np.where(derpix_full >= p)[0] + frame0
    derpix_idx_neg = np.where(derpix_full <= -p)[0] + frame0


    print("Índices de valores mayores o iguales a 3.2 filtrados:", derpix_idx)
    print(len(derpix_idx))

    #Guardar indices y sus valores en txt

    np.savetxt('derpix_idx_pos.txt', derpix_idx_pos, delimiter=' ')
    np.savetxt('derpix_idx_neg.txt', derpix_idx_neg, delimiter=' ')
    np.savetxt('derpix_pos.txt', derpix_pos, delimiter=' ')
    np.savetxt('derpix_neg.txt', -derpix_neg, delimiter=' ')
    np.savetxt('derpix_idx.txt', derpix_idx, delimiter=' ')

    # Variable para rastrear la posición actual en la matriz
    fila_actual = 0
    columna_actual = 0


    #Rutina para crear matriz que almacena datos de curvas de fuerza
    for i in range(0, len(derpix_idx), 2):
        # Obtener el par de índices
        start_idx = derpix_idx[i]
        end_idx = derpix_idx[i + 1] if i + 1 < len(derpix_idx) else len(data_array) #cambio else None a len(data_array)

        # Obtener el rango de datos
        #rango_datos = data_array[start_idx:end_idx, :]
        min_cf = np.min(data_array[start_idx:end_idx, 3]) #cambio data_array a cf, elimino el , 3 porque es un vector

        # Almacenar en la matriz correspondiente (vertical o vertical2)
        if fila_actual % 2 == 0: #fila_actual % 2 == 0:
            vertical[fila_actual // 2, columna_actual] = min_cf #El operador // devuelve la parte entera de a/b
        else:
            vertical2[fila_actual // 2, columna_actual] = min_cf


        """
        #Impresión de datos para ayudar a verificar 
        if (fila_actual == 247): #queremos la fila 123 de bwd (imapres), hacemos i//2 = 123, usando (2*n)+1 tenemos (2*123)+1 = 247 
            print(f"Iteración {i//2 + 1}:")
            print(f"  start_idx: {start_idx}, end_idx: {end_idx}")
            print(f"  Minimo_cf: {min_cf}")
            print(f"  fila_actual: {fila_actual}, columna_actual: {columna_actual}")
        """

        # Actualizar la posición en la matriz


        columna_actual += 1

        if columna_actual == m:
            columna_actual = 0
            fila_actual += 1

        # Detener el bucle si ya se llenaron todas las filas
        if fila_actual >= 2*n or columna_actual >= 2*m: #n por n-1, igual para m
            break


    print(vertical)
    print(vertical2)

    #error bwd fila 124 columna 74
    #Iteración 63307:
    #  start_idx: 23579789, end_idx: 23579823
    #  Minimo_cf: -0.695
    #  fila_actual: 247, columna_actual: 74

    #fig, axs = plt.subplots(1, 2, figsize=(12, 6))

    num_fila = perfil_fila.get()

    perfil_cf_fwd = -vertical[num_fila, :]
    perfil_cf_bwd = -vertical2[num_fila, :]

    if "Forward" in opciones_seleccionadas:
        # Configurar el primer subgráfico (vertical)
        fig, ax = plt.subplots()
        im = ax.imshow(-vertical, cmap='inferno', interpolation='nearest')
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')
        ax.set_title('Force-Time Curve - Forward')
        barra = fig.colorbar(im, ax=ax)

    if "Backward" in opciones_seleccionadas:
        fig, ax = plt.subplots()
        im = ax.imshow(-vertical2, cmap='inferno', interpolation='nearest')
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')
        ax.set_title('Force-Time Curve - Backward')
        barra = fig.colorbar(im, ax=ax)

    if "Forward line profile" in opciones_seleccionadas:
        plt.figure()
        plt.plot(perfil_cf_fwd)
        plt.title('Force-Time Curve - Forward line profile')
        plt.xlabel('Pixel')
        plt.ylabel('Z (V)')

    if "Backward line profile" in opciones_seleccionadas:
        plt.figure()
        plt.plot(perfil_cf_bwd)
        plt.title('Force-Time Curve - Backward line profile')
        plt.xlabel('Pixel')
        plt.ylabel('Z (V)')
    
    plt.show()

def procesar_csv_Topo(ruta_archivo, opciones_seleccionadas, resolucion):

    global ruta_archivo_csv
    
    if not ruta_archivo_csv:
        print("No CSV file selected.")
        return

     # Importar los datos usando pandas
    data = pd.read_csv(ruta_archivo, skiprows=5, header=None)

    # Asignar nombres a las columnas
    data.columns = ["Dev1ai0", "Dev1ai1", "Dev1ai2", "Dev1ai3"] #[Frame, Line, Pixel, Topo]

    # Obtener valores de los datos como matriz numpy
    data_array = data.values

    dimensiones = data_array.shape
    len_filas = dimensiones[0]  # Número de filas
    len_columnas = dimensiones[1]  # Número de columnas

    print(f"La matriz de todos los datos tiene {len_filas} filas y {len_columnas} columnas.")

    m = resolucion.get()
    n = resolucion.get()

    topo = np.zeros((n, m))
    linepos = np.zeros(n)

    dframe = np.diff(data_array[:, 0])  # Derivada de frame

    # Detectar inicio y fin de frame
    frame0 = 0
    framef = 0
    ind = 0
    for i in range(len(dframe)):
        if dframe[i] < -2 and ind == 0:
            frame0 = i
            ind = 1
        if dframe[i] > 2 and ind == 1:
            framef = i

    # Rutina para encontrar las posiciones de las líneas

    dline = np.diff(data_array[:, 1])  # Derivada de la señal de línea

    lp = 0  # Inicializar lp en 0 en lugar de 1
    for i in range(frame0 + 1, framef):
        if dline[i] > 2:
            if lp < n:  # Agregar esta condición para evitar salir del rango
                linepos[lp] = i #En otras palabras, i es el indice respecto a toda la toma de datos de la medida, lp es el indice de la matriz donde se almacena i
                lp += 1

    # Rutina para la reconstrucción de pixeles
    d1 = 160 #para 64 pix 1195 #/4 para 256 son casi 299
    d2 = 72 #para 64 pix 285 #/4 para 256 son casi 72
    #La proporcion d1/d2 debe ser aprox 4.15277
    for i in range(n):
        pos_i = int(linepos[i] + d1)  # Calcular la posición inicial para la fila i
        for j in range(m):
            topo[i, j] = data_array[pos_i, 3]
            pos_i += d2  # Actualizar la posición para la siguiente columna

    Altura = topo[:, :m]
    Altura *= 1000
    # Utilizar scipy.signal.detrend para detrender los datos
    Altura_detrended = detrend(Altura, axis=1, type='linear')
    Min_Z = abs(np.min(Altura_detrended))
    print(f"La altura mínima es de {Min_Z}")
    Altura_detrended += Min_Z

    num_fila = perfil_fila.get()

    perfil_topo = Altura_detrended[num_fila, :] #num_fila antes era 128

    if "2D Topography" in opciones_seleccionadas:
    # Grafica 2D de Topografía
        plt.figure()
        plt.imshow(Altura_detrended)
        plt.title('Topografía 2D')
        plt.colorbar(label='(V)')
        #plt.show()
    
    if "3D Topography" in opciones_seleccionadas:
        # Grafica 3D de Topografía
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(*np.meshgrid(np.arange(m), np.arange(n)), Altura_detrended, cmap='viridis')
        ax.set_title('3D Topography')
        ax.set_xlabel('Pixel X')
        ax.set_ylabel('Pixel Y')
        ax.set_zlabel('Z (V)')
        #plt.show()

    if "Topography line profile" in opciones_seleccionadas:
        # Perfil de Línea de Topografía
        #perfil = topo[128, :]
        plt.figure()
        plt.plot(perfil_topo)
        plt.title('Topography line profile')
        plt.xlabel('Pixel')
        plt.ylabel('Z (V)')
        #plt.show()

    plt.show()

def abreFichero():
    global ruta_archivo_csv

    ruta_archivo_csv = filedialog.askopenfilename(title = "Open", initialdir="D:", filetypes=(("CSV files","*.csv"),
            ("Text files", "*.txt"), ("All files", "*.*")))

    print("Selected file:", ruta_archivo_csv)
    lbl_nombre_archivo.config(text=f"Selected file: {ruta_archivo_csv}")
    

#Función para graficar el archivo procesado
def graficar():
    # Verificar el tipo seleccionado y procesar el archivo según corresponda
    tipo_seleccionado = tipo.get()
    if tipo_seleccionado == "PFM":
        opciones_seleccionadas = []
        for opcion, (checkbox, var) in pfm_checkboxes.items():
            if var.get() == 1:
                opciones_seleccionadas.append(opcion)
        procesar_csv_PFM(ruta_archivo_csv, opciones_seleccionadas, resolucion)

    elif tipo_seleccionado == "CF":
        opciones_seleccionadas = []
        for opcion, (checkbox, var) in cf_checkboxes.items():
            if var.get() == 1:
                opciones_seleccionadas.append(opcion)
        procesar_csv_CF(ruta_archivo_csv, opciones_seleccionadas, resolucion)


#Label para mostrar el nombre del archivo seleccionado
lbl_nombre_archivo = Label(root, text="No file selected")
lbl_nombre_archivo.pack(side = "top")



# Botón para graficar el archivo procesado
btn_graficar = Button(root, text="Plot", command=graficar)
btn_graficar.pack(side = "bottom")

# Checkboxes para las opciones
opciones_PFM = ["2D Topography", "2D Amplitude", "2D Phase",
            "3D Topography", "3D Amplitude", "3D Phase",
            "Topography line profile", "Amplitude line profile", "Phase line profile"]

opciones_CF = ["Forward", "Backward", "Forward line profile", "Backward line profile"] #los perfiles tal vez deban ser omitidos

opciones_topo = ["3D Topography", "2D Topography", "Topography line profile"]

pfm_checkboxes = {}
for opcion in opciones_PFM:
    var = IntVar()
    checkbox = Checkbutton(root, text=opcion, variable=var)
    pfm_checkboxes[opcion] = (checkbox, var)

cf_checkboxes = {}
for opcion in opciones_CF:
    var = IntVar()
    checkbox = Checkbutton(root, text=opcion, variable=var)
    cf_checkboxes[opcion] = (checkbox, var)

topo_checkboxes = {}
for opcion in opciones_topo:
    var = IntVar()
    checkbox = Checkbutton(root, text=opcion, variable=var)
    topo_checkboxes[opcion] = (checkbox, var)

# Botón para abrir archivo CSV
btn_abrir = Button(root, text="Open CSV file", command=abreFichero)
btn_abrir.pack(side = "top")

root.mainloop()