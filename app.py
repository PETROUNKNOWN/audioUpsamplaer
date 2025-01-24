import os
import numpy as np
import customtkinter as ctk
from pydub import AudioSegment
from tkinter import filedialog, messagebox
from scipy.io.wavfile import read as wav_read, write as wav_write


class AudioUpsamplerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Upsampler")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Variables
        self.input_file = ""
        self.output_file = ""
        # self.process_channel = 0  # 0 for left, 1 for right

        self.create_widgets()

    def create_widgets(self):
        file_frame = ctk.CTkFrame(self.root)
        file_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(file_frame, text="Input File:").grid(row=0, column=0, padx=5, pady=5)
        self.input_file_entry = ctk.CTkEntry(file_frame, width=400)
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(file_frame, text="Browse", command=self.browse_input_file).grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(file_frame, text="Output File:").grid(row=1, column=0, padx=5, pady=5)
        self.output_file_entry = ctk.CTkEntry(file_frame, width=400)
        self.output_file_entry.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(file_frame, text="Browse", command=self.browse_output_file).grid(row=1, column=2, padx=5, pady=5)

        # channel_frame = ctk.CTkFrame(self.root)
        # channel_frame.pack(pady=10, padx=10, fill="x")

        # ctk.CTkLabel(channel_frame, text="Process Channel:").grid(row=0, column=0, padx=5, pady=5)
        # self.channel_var = ctk.IntVar(value=0)
        # ctk.CTkRadioButton(channel_frame, text="Left Channel", variable=self.channel_var, value=0).grid(row=0, column=1, padx=5, pady=5)
        # ctk.CTkRadioButton(channel_frame, text="Right Channel", variable=self.channel_var, value=1).grid(row=0, column=2, padx=5, pady=5)

        console_frame = ctk.CTkFrame(self.root)
        console_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.console = ctk.CTkTextbox(console_frame, wrap="word", state="disabled")
        self.console.pack(pady=5, padx=5, fill="both", expand=True)

        ctk.CTkButton(self.root, text="Process Audio", command=self.process_audio).pack(pady=10)

    def browse_input_file(self):
        self.input_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.flac *.mp3")])
        self.input_file_entry.delete(0, "end")
        self.input_file_entry.insert(0, self.input_file)

    def browse_output_file(self):
        self.output_file = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav"), ("FLAC Files", "*.flac"), ("MP3 Files", "*.mp3")])
        self.output_file_entry.delete(0, "end")
        self.output_file_entry.insert(0, self.output_file)

    def log_to_console(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.configure(state="disabled")
        self.console.see("end")

    

    def process_audio(self):
        if not self.input_file or not self.output_file:
            messagebox.showerror("Error", "Please select input and output files.")
            return

        self.log_to_console("Starting audio processing...")

        try:
            # Determine the file format
            file_format = os.path.splitext(self.input_file)[1].lower()

            # Load the audio file based on its format
            if file_format == '.wav':
                sample_rate, data = wav_read(self.input_file)
                if len(data.shape) == 1:
                    # Convert mono to stereo by duplicating the channel
                    data = np.column_stack((data, data))
                left_channel = data[:, 0]
                right_channel = data[:, 1]
            elif file_format in ['.flac', '.mp3']:
                try:
                    audio = AudioSegment.from_file(self.input_file)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load audio file. \nEnsure FFmpeg is installed and accessible. \nError: {e}")
                    # raise RuntimeError() # IDK if this will be used
                sample_rate = audio.frame_rate
                left_channel = np.array(audio.split_to_mono()[0].get_array_of_samples())
                right_channel = np.array(audio.split_to_mono()[1].get_array_of_samples())
            else:
                messagebox.showerror("Error", "Unsupported file format. \nOnly .wav, .flac, and .mp3 are supported.")
                # raise ValueError("Unsupported file format. Only .wav, .flac, and .mp3 are supported.")

            processed_left_channel = self.process_channel_samples(left_channel)
            processed_right_channel = self.process_channel_samples(right_channel)

            new_data = np.column_stack((processed_left_channel, processed_right_channel))

            

            # Save the processed audio based on the output file format
            if file_format == '.wav':
                wav_write(self.output_file, sample_rate, new_data.astype(np.int16))
            elif file_format in ['.flac', '.mp3']:
                processed_audio = AudioSegment(
                    new_data.tobytes(),
                    frame_rate=sample_rate,
                    sample_width=new_data.dtype.itemsize,
                    channels=2
                )
                processed_audio.export(self.output_file, format=file_format[1:]) # Remove the dot from the format # stackoveflow.com

            self.log_to_console("Audio processing completed successfully!")
            self.log_to_console(f"Processed audio saved to {self.output_file}")
            # messagebox.showinfo("Success", "Audio processing completed successfully!")
        except Exception as e:
            self.log_to_console(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    
    
    def process_channel_samples(self,samples):
        new_samples = [] # An array to hold new samples

        samples = samples.astype(np.int32) # We convert sample values to int32 to solve overflow bug

        for i in range(len(samples) - 1): # Algo to iterate through samples and calculate average between adjacent samples
            current_sample = samples[i]
            next_sample = samples[i + 1]

            average_amplitude = (current_sample + next_sample) // 2  # Use integer division, otherwise bitwise takes the values too low, ie. destroys the music

            new_samples.append(current_sample)
            new_samples.append(average_amplitude) # Here we append the samples to the new array we are making, first the original, then the average(new one).

        new_samples.append(samples[-1]) # Dont forget the last sample since it did not go through the loop

        return np.array(new_samples, dtype=np.int16) # Convert the list back to a numpy array with the original data type int16

   

# Run the application
if __name__ == "__main__":
    root = ctk.CTk()
    app = AudioUpsamplerApp(root)
    root.mainloop()