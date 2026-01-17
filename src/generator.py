import numpy as np
import scipy.signal as signal
from typing import Optional
from .schemas import Waveform

import scipy.signal as signal
from typing import Optional
from .schemas import Waveform

class SirenSynthesizer:
    def __init__(self, sample_rate: int = 44100, oversample: int = 8):
        self.target_sample_rate = sample_rate
        self.oversample = oversample
        self.sample_rate = sample_rate * oversample  # Internal processing rate

    def _generate_phasor(self, frequency_array: np.ndarray) -> np.ndarray:
        """
        Integrates instantaneous frequency to get phase.
        phi(t) = 2*pi * integral(f(t) dt)
        """
        # dt = 1/fs
        dt = 1.0 / self.sample_rate
        # cumulative sum acts as integration
        phase = 2 * np.pi * np.cumsum(frequency_array) * dt
        return phase

    def _apply_waveform(self, phase: np.ndarray, waveform: Waveform, duty_cycle: float = 0.5) -> np.ndarray:
        if waveform == Waveform.SINE:
            return np.sin(phase)
        elif waveform == Waveform.SQUARE:
            return signal.square(phase, duty=duty_cycle)
        elif waveform == Waveform.SAWTOOTH:
            return signal.sawtooth(phase, width=1.0) # width=1 is rising ramp
        elif waveform == Waveform.TRIANGLE:
            return signal.sawtooth(phase, width=0.5)
        elif waveform == Waveform.TRAPEZOID:
            # Trapezoid approximation: clipped triangle or specialized function.
            # Here we can implement a simple clipped triangle for "electronic/mechanical" sound
            # or use a soft-clipped square.
            # Taking a triangle wave and clipping it is a common trapezoid approximation.
            tri = signal.sawtooth(phase, width=0.5)
            # Clip between -0.8 and 0.8 and normalize
            trap = np.clip(tri * 1.5, -1.0, 1.0) 
            return trap
        else:
            return np.sin(phase)

    def generate_siren_cycle(self, 
                             f_min: float, 
                             f_max: float, 
                             period: float, 
                             waveform: Waveform, 
                             duration_s: float,
                             duty_cycle: float = 0.5) -> np.ndarray:
        
        num_samples = int(duration_s * self.sample_rate)
        t = np.linspace(0, duration_s, num_samples, endpoint=False)
        
        # LFO for frequency modulation
        # Standard sirens (Wail/Yelp) typically use a standard LFO shape (Sine or Triangle) for the pitch sweep
        # SAE J1849 implies a sweep. Usually approximated by a sine or triangle LFO.
        # We will assume a Sine sweep for smooth transitions, or Triangle for linear linear sweep.
        # Let's use a Sine LFO mapped to [f_min, f_max] for natural mechanical sirens,
        # or Triangle for electronic ones. Let's default to Sine for organic feel, 
        # but maybe we should make this configurable? 
        # For this version, let's use a Sine LFO for the SWEEP itself (Modulation source).
        
        # LFO Frequency
        lfo_freq = 1.0 / period
        
        # LFO 0..1 (Sine based) -> -1..1 -> 0..1
        # lfo = 0.5 * (1 + np.sin(2 * np.pi * lfo_freq * t - np.pi/2)) # Start at min?
        
        # Simpler: Linear sweep (Triangle) is very common for electronic wail/yelp.
        # Mechanical sirens are somewhat exponential or log-sweep.
        # Let's use a triangle LFO for the sweep control as it's standard for synth sirens.
        sweep_signal = 0.5 * (1 + signal.sawtooth(2 * np.pi * lfo_freq * t, width=0.5))
        
        # Instantaneous Frequency Array
        inst_freq = f_min + (f_max - f_min) * sweep_signal
        
        # Generate Phase
        phase = self._generate_phasor(inst_freq)
        
        # Generate Audio
        audio_high_res = self._apply_waveform(phase, waveform, duty_cycle)
        
        # Decimate (Low-pass + Downsample)
        if self.oversample > 1:
            audio = signal.decimate(audio_high_res, self.oversample, ftype='fir')
        else:
            audio = audio_high_res
            
        return audio

    def generate_two_tone(self, 
                          f1: float, 
                          f2: float, 
                          period: float, 
                          waveform: Waveform, 
                          duration_s: float,
                          duty_cycle: float = 0.5) -> np.ndarray:
        """
        For Hi-Lo sirens which switch discretely.
        """
        num_samples = int(duration_s * self.sample_rate)
        t = np.linspace(0, duration_s, num_samples, endpoint=False)
        
        # Square LFO for switching
        lfo_freq = 1.0 / period
        # 0 or 1
        switching_signal = 0.5 * (1 + signal.square(2 * np.pi * lfo_freq * t))
        
        inst_freq = f1 + (f2 - f1) * switching_signal
        
        phase = self._generate_phasor(inst_freq)
        audio_high_res = self._apply_waveform(phase, waveform, duty_cycle)
        
        # Decimate (Low-pass + Downsample)
        if self.oversample > 1:
            audio = signal.decimate(audio_high_res, self.oversample, ftype='fir')
        else:
            audio = audio_high_res
        
        return audio
