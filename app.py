

import tkinter as tk
from tkinter import Label, filedialog, messagebox
from tkinter import scrolledtext
from pydub import AudioSegment, silence
import simpleaudio as sa
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker


class AudioApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio Manipulation App")

        self.audio_segment = None
        self.filename = None
        self.play_obj = None
        self.wave_obj = None
        self.is_playing = False

        # Graph Setup
        self.fig = Figure(figsize=(10, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # UI Controls
        control_frame = tk.Frame(master)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Button(control_frame, text="Open Audio File", command=self.open_file).pack()
        self.play_pause_button = tk.Button(control_frame, text="Play", command=self.toggle_playback)
        self.play_pause_button.pack()
        tk.Button(control_frame, text="Detect Silence", command=self.detect_silence).pack()
        tk.Button(control_frame, text="Remove silents and Save New Audio", command=self.remove_silence).pack()
        # Silence Info Display
        self.silence_info_label = Label(control_frame, text='', justify=tk.LEFT, anchor='n', padx=10)
        self.silence_info_label.pack()

    def open_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.m4a")])
        if filename:
            self.filename = filename
            self.audio_segment = AudioSegment.from_file(self.filename)
            self.display_waveform()
            self.prepare_audio()

    def prepare_audio(self):
        # Export the audio to a wav file
        temp_filename = 'temp.wav'
        self.audio_segment.export(temp_filename, format='wav')
        self.wave_obj = sa.WaveObject.from_wave_file(temp_filename)




    def remove_silence(self):
        if not self.audio_segment:
            messagebox.showinfo("Info", "Please load an audio file first.")
            return

        # Parameters for silence detection
        silence_thresh = -50  # dB
        min_silence_len = 1000  # milliseconds

        # Detect non-silent chunks
        nonsilent_chunks = silence.detect_nonsilent(self.audio_segment,
                                                    min_silence_len=min_silence_len,
                                                    silence_thresh=silence_thresh)

        # Create new audio without silence
        new_audio = AudioSegment.empty()
        for start, end in nonsilent_chunks:
            new_audio += self.audio_segment[start:end]

        # Ask user where to save the new audio file
        new_filename = filedialog.asksaveasfilename(defaultextension=".wav",
                                                    filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("All files", "*.*")])
        if new_filename:
            new_audio.export(new_filename, format=new_filename.split('.')[-1])



    def toggle_playback(self):
        if not self.audio_segment:
            messagebox.showinfo("Info", "Please load an audio file first.")
            return

        if self.is_playing:
            self.is_playing = False
            self.play_pause_button.config(text="Play")
            self.play_obj.stop()
        else:
            self.is_playing = True
            self.play_pause_button.config(text="Pause")
            self.play_obj = self.wave_obj.play()

    def detect_silence(self):
        if self.audio_segment:
            silence_thresh = -50  # dB
            min_silence_len = 1000  # milliseconds
            silence_zones = silence.detect_silence(self.audio_segment, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
            silence_zones = [(start, end) for start, end in silence_zones]

            total_silence_duration = sum(end - start for start, end in silence_zones)
            total_duration = len(self.audio_segment)
            
            formatted_silence_info = (
                f"Total Duration: {total_duration/1000:.2f} s\n"
                f"Total Silence: {total_silence_duration/1000:.2f} s\n"
                "Silence Zones:\n" +
                "\n".join([f'{start/1000:.2f}s - {end/1000:.2f}s' for start, end in silence_zones])
            )
            self.silence_info_label.config(text=formatted_silence_info)
            self.display_waveform(silence_zones)
        else:
            messagebox.showinfo("Info", "Please load an audio file first.")

    def display_waveform(self, silence_zones=None):
        samples = np.array(self.audio_segment.get_array_of_samples())
        duration = len(self.audio_segment) / 1000  # Duration in seconds
        time_axis = np.linspace(0, duration, num=len(samples))

        self.ax.clear()
        self.ax.set_facecolor('black')
        self.ax.plot(time_axis, samples, label='Audio Waveform', color='cyan')
        self.ax.grid(True, color='green')
        self.ax.tick_params(axis='x', colors='blue')
        self.ax.tick_params(axis='y', colors='blue')
        self.ax.xaxis.label.set_color('blue')
        self.ax.yaxis.label.set_color('blue')
        self.ax.title.set_color('red')

        # Highlight silence zones
        if silence_zones:
            for start, end in silence_zones:
                self.ax.axvspan(start / 1000, end / 1000, color='red', alpha=0.4, label='Silence')

        self.ax.set_title("Audio Waveform with Silence Zones")
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.2f}s'))

        # Annotate total duration on the graph
        self.ax.annotate(f'Total Duration: {duration:.2f}s', 
                         xy=(0.5, 0.95), 
                         xycoords='axes fraction',
                         ha='center', 
                         va='center',
                         fontsize=10, 
                         color='white')

        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
