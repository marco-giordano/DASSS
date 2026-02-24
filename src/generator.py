import numpy as np
import scipy.signal as signal
from typing import Optional, Literal, Union
from .schemas import Waveform, RealismConfig, SirenType, MechanicalProfile, VariableWailConfig

# Try importing torch for Metal support
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
class SirenSynthesizer:
    def __init__(self, sample_rate: int = 44100, oversample: int = 8, use_metal: bool = False, realism_config: Optional[RealismConfig] = None):
        self.target_sample_rate = sample_rate
        self.oversample = oversample
        self.sample_rate = sample_rate * oversample  # Internal processing rate
        self.use_metal = use_metal
        self.device = None
        
        # Default realism config if not provided
        self.realism = realism_config if realism_config is not None else RealismConfig()
        
        if self.use_metal:
            if not HAS_TORCH:
                print("WARNING: 'use_metal' requested but PyTorch is not installed. Falling back to CPU/NumPy.")
                self.use_metal = False
            elif not torch.backends.mps.is_available():
                print("WARNING: 'use_metal' requested but MPS (Metal) is not available. Falling back to CPU/NumPy.")
                self.use_metal = False
            else:
                self.device = torch.device("mps")
                print("SirenSynthesizer using Metal (MPS) acceleration.")

    def _generate_phasor(self, frequency_array: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """Integrates instantaneous frequency to get phase.
        
        IMPORTANT: Cumulative summation must be done in float64, even on the MPS
        (Metal) path where tensors are float32. float32 cumsum loses precision as
        the running total grows: at 10s (fs=44100, ~1100Hz carrier) the error
        reaches −37 cycles (−234 rad), at 22s it is −181 cycles (−1139 rad).
        This produces catastrophic broadband noise that grows as O(t²) — exactly
        the "background noise ramping up after ~11s" symptom.
        
        Fix: always compute cumsum in float64 on CPU (numpy), then wrap to [0, 2π]
        before converting back to float32 for MPS. The wrapped values are small
        (≤ 6.28) so float32 represents them accurately (error < 1e-6 rad).
        """
        dt = 1.0 / self.sample_rate
        if self.use_metal and isinstance(frequency_array, torch.Tensor):
            # Pull to CPU, upcast to float64 for numeric precision, cumsum, wrap, 
            # then send result back to MPS as float32.
            freq_np = frequency_array.cpu().numpy().astype(np.float64)
            phase_np = (2.0 * np.pi * np.cumsum(freq_np) * dt) % (2.0 * np.pi)
            return torch.from_numpy(phase_np.astype(np.float32)).to(self.device)
        else:
            # numpy arrays default to float64 — no precision loss here.
            phase = 2.0 * np.pi * np.cumsum(frequency_array) * dt
            phase = phase % (2.0 * np.pi)
            return phase


    def _apply_analog_saturation(self, phase: Union[np.ndarray, "torch.Tensor"], waveform: Waveform, duty_cycle: float = 0.5) -> Union[np.ndarray, "torch.Tensor"]:
        """
        Generates waveforms with 'analog' imperfections (soft clipping/saturation).
        Supports both NumPy and PyTorch (Metal).
        """
        # Return standard waveform if Analog Saturation is disabled
        if not self.realism.analog_saturation:
            p_norm = (phase / (2 * np.pi)) % 1
            if self.use_metal and isinstance(phase, torch.Tensor):
                if waveform == Waveform.SINE: return torch.sin(phase)
                if waveform == Waveform.SQUARE: return torch.where(p_norm < duty_cycle, torch.tensor(1.0, device=self.device), torch.tensor(-1.0, device=self.device))
                if waveform == Waveform.SAWTOOTH: return signal.sawtooth(phase, width=1.0) # wait, torch doesn't have signal.sawtooth
                # We need clean implementations if saturation is off
                # Let's rely on the previous implementation structure or simplified versions
                # For clean waveforms without saturation:
                if waveform == Waveform.SINE: return torch.sin(phase)
                # ... implementing basic clean waveforms ...
            # Actually, to keep it simple, let's just bypass the TANH part and use standard signal generation if disabled.
            # But wait, my manual implementation IS saturation-based. 
            # If disabled, I should use the "perfect" waveform code.
            pass # See below logic
        
        # If disabled, use clean logic
        if not self.realism.analog_saturation:
             if self.use_metal and isinstance(phase, torch.Tensor):
                if waveform == Waveform.SINE: return torch.sin(phase)
                elif waveform == Waveform.SQUARE: 
                    # Simple Square
                    return torch.sign(torch.sin(phase)) # 50% duty approximation for now or use complex logic
                elif waveform == Waveform.SAWTOOTH:
                    p_norm = (phase / (2 * np.pi)) % 1
                    return 2 * p_norm - 1
                elif waveform == Waveform.TRAPEZOID:
                     # Triangle
                    p_norm = (phase / (2 * np.pi)) % 1
                    return 2 * torch.abs(2 * p_norm - 1) - 1
                else: return torch.sin(phase)
             else:
                # NumPy clean
                if waveform == Waveform.SINE: return np.sin(phase)
                elif waveform == Waveform.SQUARE: return signal.square(phase, duty=duty_cycle)
                elif waveform == Waveform.SAWTOOTH: return signal.sawtooth(phase, width=1.0)
                elif waveform == Waveform.TRAPEZOID: return signal.sawtooth(phase, width=0.5)
                else: return np.sin(phase)

        gain = self.realism.saturation_gain
        
        if self.use_metal and isinstance(phase, torch.Tensor):
            # PyTorch Implementation
            sin_p = torch.sin(phase)
            
            if waveform == Waveform.SQUARE:
                raw_wave = sin_p + (duty_cycle - 0.5)
                return torch.tanh(gain * raw_wave)
            
            elif waveform == Waveform.SAWTOOTH:
                p_norm = (phase / (2 * np.pi)) % 1
                return (2 * p_norm) - 1
            
            elif waveform == Waveform.TRAPEZOID:
                 # Wrapped sawtooth to triangle first
                p_norm = (phase / (2 * np.pi)) % 1
                saw = (2 * p_norm) - 1
                tri = 2 * torch.abs(saw) - 1 # Triangle
                # Soft clip
                return torch.tanh(tri * 3.0)
            
            else:
                return sin_p
        
        else:
            # NumPy Implementation
            if waveform == Waveform.SQUARE:
                raw_wave = np.sin(phase) + (duty_cycle - 0.5) 
                return np.tanh(gain * raw_wave)

            elif waveform == Waveform.SAWTOOTH:
                return signal.sawtooth(phase, width=1.0)
                
            elif waveform == Waveform.TRAPEZOID:
                tri = signal.sawtooth(phase, width=0.5)
                return np.tanh(tri * 3.0) 
                
            else: 
                return np.sin(phase)

    def _apply_horn_response(self, audio: Union[np.ndarray, "torch.Tensor"]) -> Union[np.ndarray, "torch.Tensor"]:
        """
        Simulates speaker frequency response.
        """
        if not self.realism.horn_filter:
            return audio
        if self.use_metal and isinstance(audio, torch.Tensor):
            audio_np = audio.cpu().numpy()
        else:
            audio_np = audio

        nyquist = 0.5 * self.sample_rate
        low_cut = 300.0 / nyquist
        high_cut = 5000.0 / nyquist
        
        # Use SOS (Second Order Sections) for numerical stability at high sample rates
        sos = signal.butter(4, [low_cut, high_cut], btype='band', output='sos')
        
        filtered = signal.sosfilt(sos, audio_np)
        
        if self.use_metal and isinstance(audio, torch.Tensor):
            # MPS does not support float64 (double).
            # scipy.signal typically returns float64.
            # Cast to float32 BEFORE sending to MPS device.
            return torch.from_numpy(filtered.astype(np.float32)).to(self.device)
        return filtered

    def _add_oscillator_jitter(self, num_samples: int) -> Union[np.ndarray, "torch.Tensor"]:
        """Adds low-frequency random noise to simulate voltage drift.
        
        Design rationale:
        - A DC-blocking highpass filter is applied BEFORE the smoothing lowpass so
          the jitter has strictly zero mean. This is essential: if DC leaks through,
          cumsum(jitter) in _generate_phasor becomes an unbounded random walk whose
          variance grows as O(n), producing a noise floor that rises over time.
        - Pipeline: white_noise -> highpass (DC-block) -> lowpass (smooth) -> scale
        - The resulting jitter is stationary (bounded variance) for any signal length.
        """
        if not self.realism.oscillator_jitter:
            if self.use_metal: return torch.zeros(num_samples, device=self.device)
            else: return np.zeros(num_samples)
            
        jitter_amt = self.realism.jitter_amount
        
        # --- Step 1: DC-blocking highpass (~0.5 Hz cutoff) ---
        # Removes any DC component so cumsum(jitter) is mean-reverting.
        # Bilinear-transformed 1-pole RC highpass: y[n] = x[n] - x[n-1] + alpha*y[n-1]
        # alpha = R/(R+1) where R = fs / (2*pi*f_cut): very close to 1 for low f_cut.
        alpha_hp = 0.9999  # ~0.5 Hz highpass at 88200 Hz
        b_hp = [1.0, -1.0]
        a_hp = [1.0, -alpha_hp]
        
        # --- Step 2: Smoothing lowpass (shapes frequency content) ---
        # Simple one-pole EMA: y[n] = (1-alpha)*x[n] + alpha*y[n-1]
        # Cutoff ~ fs * (1-alpha) / (2*pi): with alpha=0.995 -> ~70 Hz at 88200
        alpha_lp = 0.995
        b_lp = [1.0 - alpha_lp]
        a_lp = [1.0, -alpha_lp]
        
        # --- Step 3: Scaling ---
        # Target: roughly +/- (jitter_amt * 10) Hz std dev.
        # With the two-filter chain, empirical gain is ~1.0 std for WN(0,1) input.
        scale = jitter_amt * 10.0

        if self.use_metal:
            noise = torch.randn(num_samples, device=self.device)
            noise_np = noise.cpu().numpy()
            # Apply highpass then lowpass
            noise_hp = signal.lfilter(b_hp, a_hp, noise_np)
            jitter_np = signal.lfilter(b_lp, a_lp, noise_hp)
            jitter = torch.from_numpy(jitter_np.astype(np.float32)).to(self.device)
            jitter = scale * jitter
            return jitter
        else:
            noise = np.random.normal(0, 1.0, num_samples)
            # Apply highpass then lowpass
            noise_hp = signal.lfilter(b_hp, a_hp, noise)
            jitter_np = signal.lfilter(b_lp, a_lp, noise_hp)
            jitter = scale * jitter_np
            return jitter

    def _decimate(self, audio: Union[np.ndarray, "torch.Tensor"]) -> np.ndarray:
        if self.use_metal and isinstance(audio, torch.Tensor):
            audio_np = audio.cpu().numpy()
        else:
            audio_np = audio
            
        if self.oversample > 1:
            return signal.decimate(audio_np, self.oversample, ftype='fir')
        return audio_np

    def generate_siren_cycle(self, 
                             f_min: float, 
                             f_max: float, 
                             period: float, 
                             waveform: Waveform, 
                             duration_s: float,
                             duty_cycle: float = 0.5,
                             siren_type: Literal['electronic', 'mechanical'] = 'electronic') -> np.ndarray:
        
        num_samples = int(duration_s * self.sample_rate)
    def _generate_variable_wail_sweep(self, min_duration: float, f_min: float, nominal_f_max: float, nominal_period: float,
                                      rise_ratio: float, rise_exp: float, fall_exp: float, 
                                      limit_f_max: float = 10000.0,
                                      variation_magnitude: float = 0.2) -> Union[np.ndarray, "torch.Tensor"]:
        """
        Generates a non-periodic sweep signal.
        """
        target_samples = int(min_duration * self.sample_rate)
        
        # We need to construct the full array sample by sample or chunk by chunk
        # Since loop in python is slow, we aim for chunk-based.
        
        # Variation magnitude
        mag = variation_magnitude
        
        current_samples = 0
        chunks_freq = []
        
        # Pre-calc constants
        delta_nominal = nominal_f_max - f_min
        if delta_nominal <= 0: delta_nominal = 1.0
        
        while current_samples < target_samples:
            # Randomize f_max for this cycle
            # Variation: +/- mag relative to nominal range?
            # Or f_max varies +/- mag%? 
            # Let's say: f_peak = nominal_f_max * (1 + rand(-mag, mag))
            # But kept > f_min
            var = (np.random.random() * 2 - 1) * mag
            f_peak = nominal_f_max * (1.0 + var)
            
            # --- CONSTRAINTS & CLAMPING (Fixes "Steady f1" artifact) ---
            
            # Constraint 1: Absolute Max Limit Compliance
            if f_peak > limit_f_max:
                f_peak = limit_f_max
                
            # Constraint 2: Maintain sweep. 
            # If f_peak drops too close to f_min, we get a flat cycle (steady f1).
            # Enforce reasonable delta. E.g. at least 10% of nominal delta or 50Hz.
            min_valid_peak = f_min + (0.1 * delta_nominal) 
            if f_peak < min_valid_peak:
                f_peak = min_valid_peak
            
            # Scale period
            # Model: Constant acceleration/deceleration. Time to reach delta is proportional to delta.
            # T_new / T_nom = Delta_new / Delta_nom
            delta = f_peak - f_min
            scale_factor = delta / delta_nominal
            
            # Constrain scale factor to avoid extreme periods?
            # With clamping above, delta shouldn't be zero.
            scale_factor = np.clip(scale_factor, 0.2, 5.0)
            
            cycle_period = nominal_period * scale_factor
            samples_in_cycle = int(cycle_period * self.sample_rate)
            
            # Don't exceed remaining too much? 
            # Actually sirens cut off anywhere.
            
            # Generate one cycle envelope (0->1->0) using pre-calc logic or just in-line
            if self.use_metal:
                t_cycle = torch.linspace(0, 1, samples_in_cycle, device=self.device)
            else:
                t_cycle = np.linspace(0, 1, samples_in_cycle)
                
            # Envelope 0..1
            if self.use_metal:
                env = torch.zeros_like(t_cycle)
                rise_mask = t_cycle < rise_ratio
                fall_mask = ~rise_mask
                
                if rise_ratio > 0:
                    t_rise = t_cycle[rise_mask] / rise_ratio
                    env[rise_mask] = torch.pow(t_rise, rise_exp)
                if rise_ratio < 1.0:
                    t_fall = (1.0 - t_cycle[fall_mask]) / (1.0 - rise_ratio)
                    env[fall_mask] = torch.pow(t_fall, fall_exp)
            else:
                env = np.zeros_like(t_cycle)
                rise_mask = t_cycle < rise_ratio
                fall_mask = ~rise_mask
                
                if rise_ratio > 0:
                    t_rise = t_cycle[rise_mask] / rise_ratio
                    env[rise_mask] = np.power(t_rise, rise_exp)
                if rise_ratio < 1.0:
                    t_fall = (1.0 - t_cycle[fall_mask]) / (1.0 - rise_ratio)
                    env[fall_mask] = np.power(t_fall, fall_exp)
            
            # Convert Envelope (0-1) to Freq (f_min - f_peak)
            freq_chunk = f_min + (f_peak - f_min) * env
            
            chunks_freq.append(freq_chunk)
            current_samples += samples_in_cycle
            
        # Concatenate
        if self.use_metal:
            full_freq = torch.cat(chunks_freq)
        else:
            full_freq = np.concatenate(chunks_freq)
            
        # Return full cycles (do not trim to target_samples)
        return full_freq

    def _generate_mechanical_envelope(self, t: Union[np.ndarray, "torch.Tensor"], period: float, 
                                      rise_ratio: float, rise_exp: float, fall_exp: float) -> Union[np.ndarray, "torch.Tensor"]:
        """
        Generates a customizable Asymmetric Triangle / Envelope.
        Rise phase: 0 -> 1 over (period * rise_ratio)
        Fall phase: 1 -> 0 over (period * (1 - rise_ratio))
        Curvature controlled by exponents.
        """
        # Normalized phase within one cycle [0, 1)
        cycle_t = (t % period) / period
        
        if self.use_metal and isinstance(t, torch.Tensor):
            # PyTorch Implementation
            envelope = torch.zeros_like(cycle_t)
            
            # Masks
            rise_mask = cycle_t < rise_ratio
            fall_mask = ~rise_mask
            
            # Rise: (t / ratio) ^ exp
            # Avoid div by zero if ratio is 0 (unlikely but safe)
            if rise_ratio > 0:
                t_rise = cycle_t[rise_mask] / rise_ratio
                envelope[rise_mask] = torch.pow(t_rise, rise_exp)
                
            # Fall: (1 - (t - ratio)/(1-ratio)) ^ exp = ((1-t)/(1-ratio)) ^ exp
            if rise_ratio < 1.0:
                t_fall = (1.0 - cycle_t[fall_mask]) / (1.0 - rise_ratio)
                envelope[fall_mask] = torch.pow(t_fall, fall_exp)
                
            return envelope
        else:
            # NumPy Implementation
            envelope = np.zeros_like(cycle_t)
            
            rise_mask = cycle_t < rise_ratio
            fall_mask = ~rise_mask
            
            if rise_ratio > 0:
                t_rise = cycle_t[rise_mask] / rise_ratio
                envelope[rise_mask] = np.power(t_rise, rise_exp)
                
            if rise_ratio < 1.0:
                t_fall = (1.0 - cycle_t[fall_mask]) / (1.0 - rise_ratio)
                envelope[fall_mask] = np.power(t_fall, fall_exp)
                
            return envelope
    
    def generate_siren_cycle(self, 
                             f_min: float, 
                             f_max: float, 
                             period: float, 
                             waveform: Waveform, 
                             duration_s: float,
                             duty_cycle: float = 0.5,
                             siren_type: SirenType = SirenType.ELECTRONIC,
                             mechanical_profile: Optional[MechanicalProfile] = None,
                             variable_wail_config: Optional[VariableWailConfig] = None,
                             max_freq_limit: float = 20000.0,
                             enforce_cycle: bool = True) -> np.ndarray:
        
        # Resolve Mechanical Parameters
        # Defaults
        mech_rise = 0.2
        mech_rise_exp = 0.5
        mech_fall_exp = 2.0
        
        if mechanical_profile:
            mech_rise = mechanical_profile.rise_ratio
            mech_rise_exp = mechanical_profile.rise_exponent
            mech_fall_exp = mechanical_profile.fall_exponent
        
        # Check if Variable Wail is Active
        is_variable = False
        if variable_wail_config and variable_wail_config.enabled:
             # Only strictly applies to mechanical/pneumatic or if explicitly allowed?
             # User said "apply them to wail sounds". Typically mechanical.
             # We allow it if configured.
             if siren_type in [SirenType.MECHANICAL, SirenType.PNEUMATIC]:
                 is_variable = True
        
        # Override based on global realism toggle for variable wail?
        # User moved variable wail to JSON, so JSON takes precedence. 
        # But global `mechanical_asymmetry` still exists.
        
        use_asymmetry = self.realism.mechanical_asymmetry and (siren_type in [SirenType.MECHANICAL, SirenType.PNEUMATIC])

        # --- DURATION ADJUSTMENT (Complete Cycle) ---
        if use_asymmetry and is_variable:
            # Temporarily attach magnitude to self for the helper (refactor later to pass explicit magnitude)
            # The helper `_generate_variable_wail_sweep` reads `self.realism.wail_variation_magnitude` which is GONE.
            # I need to update the helper or monkeypatch.
            # Better: Update helper signature. But helper is `_generate_variable_wail_sweep`.
            # I will refactor helper signature in a separate step or assume I fix it. 
            # WAIT. I need to pass magnitude to helper.
            # Let's fix helper first? No, I can pass it as arg if I update helper.
            # I'll update helper inside this tool call? No, it's separate method.
            # I will assume `_generate_variable_wail_sweep` is updated or I update it NOW.
            
            # Let's update `_generate_variable_wail_sweep` signature in next step.
            # For now, call it with a new kwargs `variation_magnitude` if I can? No Python doesn't allow invisible args.
            # I'll update the call here, but I must ensure I update the definition in next step.
            
            inst_freq = self._generate_variable_wail_sweep(
                min_duration=duration_s,
                f_min=f_min,
                nominal_f_max=f_max,
                nominal_period=period,
                rise_ratio=mech_rise,
                rise_exp=mech_rise_exp,
                fall_exp=mech_fall_exp,
                limit_f_max=max_freq_limit,
                variation_magnitude=variable_wail_config.variation_magnitude
            )
            
            if not enforce_cycle:
                target_samples = int(duration_s * self.sample_rate)
                inst_freq = inst_freq[:target_samples]
            
            num_samples = len(inst_freq)
            actual_duration = num_samples / self.sample_rate
            
            if self.use_metal:
                t = torch.arange(0, num_samples, device=self.device) * (1.0 / self.sample_rate)
            else:
                t = np.linspace(0, actual_duration, num_samples, endpoint=False)
                
        else:
            # Standard Periodic
            if enforce_cycle:
                num_cycles = np.ceil(duration_s / period)
                actual_duration = num_cycles * period
                num_samples = int(actual_duration * self.sample_rate)
            else:
                actual_duration = duration_s
                num_samples = int(actual_duration * self.sample_rate)

            # Time Vector
            if self.use_metal:
                t = torch.arange(0, num_samples, device=self.device) * (actual_duration / num_samples)
            else:
                t = np.linspace(0, actual_duration, num_samples, endpoint=False)

            lfo_freq = 1.0 / period

            # --- MODULATOR ---
            if use_asymmetry:
                # Mechanical / Pneumatic Envelope
                sweep_signal = self._generate_mechanical_envelope(
                    t, period, 
                    rise_ratio=mech_rise,
                    rise_exp=mech_rise_exp,
                    fall_exp=mech_fall_exp
                )
                inst_freq = f_min + (f_max - f_min) * sweep_signal
            else:
                # Electronic Linear Sweep (Triangle)
                if self.use_metal:
                    phase_lfo = 2 * np.pi * lfo_freq * t
                    p_norm = (phase_lfo / (2 * np.pi)) % 1
                    saw = 2 * p_norm - 1
                    tri = 2 * torch.abs(saw) - 1 
                    sweep_signal = 0.5 * (1 + tri)
                else:
                    sweep_signal = 0.5 * (1 + signal.sawtooth(2 * np.pi * lfo_freq * t, width=0.5))
                
                inst_freq = f_min + (f_max - f_min) * sweep_signal
        
        # Add Jitter
        jitter = self._add_oscillator_jitter(num_samples)
        if self.use_metal:
             inst_freq = inst_freq + jitter
        else:
             inst_freq = inst_freq + jitter
        
        phase = self._generate_phasor(inst_freq)
        
        audio_high_res = self._apply_analog_saturation(phase, waveform, duty_cycle)
        audio_high_res = self._apply_horn_response(audio_high_res)

        # --- DECIMATION ---
        audio = self._decimate(audio_high_res)
            
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.89
            
        return audio

    def generate_two_tone(self, 
                          f1: float, 
                          f2: float, 
                          period: float, 
                          waveform: Waveform, 
                          duration_s: float,
                          duty_cycle: float = 0.5,
                          enforce_cycle: bool = True,
                          tone_pattern: Optional[str] = None) -> np.ndarray:
        
        # Determine actual period/cycle length
        if enforce_cycle:
             num_cycles = np.ceil(duration_s / period)
             actual_duration = num_cycles * period
             num_samples = int(actual_duration * self.sample_rate)
        else:
             actual_duration = duration_s
             num_samples = int(actual_duration * self.sample_rate)
             
        # Generate Pattern Signal
        if tone_pattern:
            # Custom 6-char pattern (e.g. 'hhhlll')
            pattern_len = len(tone_pattern) 
            sequence = []
            for char in tone_pattern:
                if char.lower() == 'h': sequence.append(1.0)
                elif char.lower() == 'l': sequence.append(0.0)
                else: sequence.append(0.0) # Default low
            
            # Create the pattern array for one cycle
            samples_per_cycle = int(period * self.sample_rate)
            samples_per_step = max(1, samples_per_cycle // pattern_len)
            
            cycle_signal = np.zeros(samples_per_cycle)
            for step_i, val in enumerate(sequence):
                start = step_i * samples_per_step
                end = (step_i + 1) * samples_per_step
                if step_i == pattern_len - 1: end = samples_per_cycle # Fill remainder
                cycle_signal[start:end] = val
            
            # Tile for duration
            repeats = int(np.ceil(num_samples / len(cycle_signal)))
            switching_signal = np.tile(cycle_signal, repeats)[:num_samples]
            
            if self.use_metal:
                 switching_signal = torch.tensor(switching_signal, device=self.device, dtype=torch.float32)

        else:
             # Standard Square LFO
            lfo_freq = 1.0 / period
            
            if self.use_metal:
                t = torch.arange(0, num_samples, device=self.device) * (actual_duration / num_samples)
                # Switch
                is_high = torch.sin(2 * np.pi * lfo_freq * t) >= 0
                switching_signal = torch.where(is_high, torch.tensor(1.0, device=self.device), torch.tensor(0.0, device=self.device))
            else:
                t = np.linspace(0, actual_duration, num_samples, endpoint=False)
                # Using square wave 0 to 1
                switching_signal = 0.5 * (1 + signal.square(2 * np.pi * lfo_freq * t, duty=duty_cycle))
        
        # Apply frequencies
        inst_freq = f1 + (f2 - f1) * switching_signal
        
        # Add Jitter
        jitter = self._add_oscillator_jitter(num_samples)
        if self.use_metal:
             inst_freq = inst_freq + jitter
        else:
             inst_freq = inst_freq + jitter
            
        phase = self._generate_phasor(inst_freq)
        audio_high_res = self._apply_analog_saturation(phase, waveform, duty_cycle)
        audio_high_res = self._apply_horn_response(audio_high_res)
        
        audio = self._decimate(audio_high_res)
        
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.89
        
        return audio