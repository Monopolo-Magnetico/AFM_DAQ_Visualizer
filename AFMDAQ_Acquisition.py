import nidaqmx
import csv
import tkinter as tk
from tkinter import ttk
from threading import Thread
import os
import re
from nidaqmx.constants import TerminalConfiguration

class DAQInterface:
    def __init__(self, master):
        self.master = master
        self.master.title("AFMDAQ Acquisition")
        self.sample_rate_var = tk.DoubleVar(value=1000)
        self.num_samples_var = tk.IntVar(value=1000)
        self.filename_var = tk.StringVar(value="datos_daq.csv")
        self.is_running = False

        # Configuración de la DAQ
        self.channels = ["Dev1/ai0", "Dev1/ai1", "Dev1/ai2", "Dev1/ai3", "Dev1/ai4", "Dev1/ai5"]
        self.file_path = self.filename_var.get()

        # Interfaz gráfica
        ttk.Label(master, text="Frecuencia de muestreo (Hz):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(master, textvariable=self.sample_rate_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(master, text="Número de muestras:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(master, textvariable=self.num_samples_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(master, text="Nombre del archivo CSV:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(master, textvariable=self.filename_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(master, text="Iniciar Muestreo", command=self.start_acquisition).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(master, text="Detener Muestreo", command=self.stop_acquisition).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(master, text="Salir", command=self.exit_application).grid(row=5, column=0, columnspan=2, pady=10)

    def configure_daq(self):
        self.task = nidaqmx.Task()
        for channel in self.channels:
            self.task.ai_channels.add_ai_voltage_chan(channel, min_val=-10.0, max_val=10.0,terminal_config=TerminalConfiguration.RSE)
        self.task.timing.cfg_samp_clk_timing(self.sample_rate_var.get())

    def acquire_and_save_data(self):
        with open(self.file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            headers = [f"Channel_{i+1}" for i in range(len(self.channels))]
            csv_writer.writerow(headers)

        while self.is_running:
            data = self.task.read(number_of_samples_per_channel=1)
            with open(self.file_path, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                datos=[float(e[0]) for e in data]
                csv_writer.writerow(datos)
                #print(datos)
                #print(data)
               

    def start_acquisition(self):
        self.file_path = self.filename_var.get()
        self.configure_daq()
        self.is_running = True
        self.acquisition_thread = Thread(target=self.acquire_and_save_data)
        self.acquisition_thread.start()

    def stop_acquisition(self):
        self.is_running = False
        self.acquisition_thread.join()
        self.task.stop()
        self.task.close()
        print("Muestreo detenido.")

    def exit_application(self):
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DAQInterface(root)
    root.mainloop()
