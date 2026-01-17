import argparse
import sys
import numpy as np
import scipy.signal as signal
from src.generator import SirenSynthesizer
from src.schemas import Waveform

def debug_synthesis():
    print("Debugging Synthesis...")
    synth = SirenSynthesizer(sample_rate=44100, oversample=32, use_metal=False) # Test on CPU first
    
    # Generate 1 sec of Wail
    print("Generating 1s of Wail...")
    
    # We will manually step through generation to find where it dies
    # Mocking internal steps of generate_siren_cycle
    duration_s = 1.0
    num_samples = int(duration_s * synth.sample_rate)
    t = np.linspace(0, duration_s, num_samples, endpoint=False)
    lfo_freq = 1.0 / 4.0
    sweep_signal = 0.5 * (1 + signal.sawtooth(2 * np.pi * lfo_freq * t, width=0.8)) ** 2
    inst_freq = 500 + (1600 - 500) * sweep_signal
    phase = synth._generate_phasor(inst_freq)
    
    print(f"Phase range: {np.min(phase)} - {np.max(phase)}")
    
    audio_sat = synth._apply_analog_saturation(phase, Waveform.SQUARE, 0.5)
    print(f"Sat range: {np.min(audio_sat)} - {np.max(audio_sat)}")
    
    audio_horn = synth._apply_horn_response(audio_sat)
    print(f"Horn range: {np.min(audio_horn)} - {np.max(audio_horn)}")
    
    audio_dec = synth._decimate(audio_horn)
    print(f"Decimated range: {np.min(audio_dec)} - {np.max(audio_dec)}")


if __name__ == "__main__":
    debug_synthesis()
