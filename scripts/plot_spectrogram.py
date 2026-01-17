import argparse
import matplotlib.pyplot as plt
import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

def plot_spectrogram(audio_path: str, output_path: str = None):
    # Load audio
    y, sr = sf.read(audio_path)
    if len(y.shape) > 1:
        y = y[:, 0] # mono
        
    # Compute Spectrogram
    f, t, Sxx = signal.spectrogram(y, sr, nperseg=1024, noverlap=512)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading='gouraud')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.title(f'Spectrogram: {Path(audio_path).name}')
    plt.colorbar(label='Intensity [dB]')
    plt.ylim(0, sr/2)
    
    if output_path:
        plt.savefig(output_path)
        print(f"Saved spectrogram to {output_path}")
    else:
        plt.show()
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Generate Spectrogram for Audio File")
    parser.add_argument("file", help="Path to input audio file (WAV)")
    parser.add_argument("--output", "-o", help="Path to save output image (PNG). If not provided, shows plot.", default=None)
    args = parser.parse_args()
    
    plot_spectrogram(args.file, args.output)

if __name__ == "__main__":
    main()
