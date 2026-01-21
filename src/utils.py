import json
import yaml
import random
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
from typing import Dict, Any, Union, Tuple
from pathlib import Path
from .schemas import SirenDefinition, BatchConfig, SirenModeParams

def load_json_definition(path: str) -> SirenDefinition:
    with open(path, 'r') as f:
        data = json.load(f)
    return SirenDefinition(**data)

def load_yaml_config(path: str) -> BatchConfig:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return BatchConfig(**data)

def save_metadata(metadata: list, output_path: str):
    import csv
    if not metadata:
        return
    
    keys = metadata[0].model_dump().keys()
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for idx in metadata:
            writer.writerow(idx.model_dump())

def sample_parameters(params: SirenModeParams, min_separation: float = 1.0) -> Dict[str, Any]:
    """
    Randomly samples parameters from the defined ranges using uniform distribution.
    Enforces f_max >= f_min * min_separation.
    """
    # Rejection Sampling Loop
    max_retries = 100
    
    # Init limits with safe defaults or derived values
    freq_min_limit = 0.0
    freq_max_limit = 0.0
    
    # 1. Frequency Constraints
    if params.nominal_frequencies:
        # Use Fixed values (simulating a range where min=max)
        freq_min_limit = params.nominal_frequencies.min
        freq_max_limit = params.nominal_frequencies.max
    elif params.frequency_range:
        freq_min_limit = params.frequency_range.min
        freq_max_limit = params.frequency_range.max
    else:
        raise ValueError(f"Siren mode '{params.description}' must have either frequency_range or nominal_frequencies.")

    # 2. Period Constraints
    period_limit_min = 1.0
    period_limit_max = 1.0
    if params.period_range:
        period_limit_min = params.period_range.min
        period_limit_max = params.period_range.max
    else:
        # If no period range, is there a nominal period? No, schema has period_range.
        # Maybe we should allow single 'period' in future, but for now strict.
        # Or default?
        raise ValueError(f"Siren mode '{params.description}' must have period_range.")
    
    for _ in range(max_retries):
        
        # 1. Sample F_min
        if params.nominal_frequencies:
            f_min = params.nominal_frequencies.min
        else:
            f_min = random.uniform(freq_min_limit, freq_max_limit)
            
        # 2. Sample F_max
        if params.nominal_frequencies:
            f_max = params.nominal_frequencies.max
        else:
             f_max = random.uniform(freq_min_limit, freq_max_limit)

        # Ensure f_min < f_max
        if f_min > f_max:
            f_min, f_max = f_max, f_min
            
        # 3. Sample Period
        if period_limit_min == period_limit_max:
            period = period_limit_min
        else:
            period = random.uniform(period_limit_min, period_limit_max)
            
        # 4. Validation
        # Check explicit constraints if ranges were used
        if not params.nominal_frequencies:
            # Check Min Separation
            if f_max < f_min * min_separation:
                continue
                
            # Check Absolute Limits
            if not (freq_min_limit <= f_min <= freq_max_limit): continue
            if not (freq_min_limit <= f_max <= freq_max_limit): continue
        
        # If we get here, valid
        return {
            "frequency_min": f_min,
            "frequency_max": f_max,
            "period": period,
            "waveform": params.waveform,
            "duty_cycle": params.duty_cycle,
            # Pass through new parameters for generator
            "type": params.type,
            "mode": params.mode,
            "mechanical_profile": params.mechanical_profile,
            "variable_wail": params.variable_wail,
            "tone_pattern": params.tone_pattern
        }
    
    # Fallback to defaults if sampling fails
    if params.nominal_frequencies:
         f_min = params.nominal_frequencies.min
         f_max = params.nominal_frequencies.max
    else:
         f_min = freq_min_limit
         # Fallback max ensures separation
         safe_max = f_min * min_separation
         if safe_max > freq_max_limit:
             # If definition doesn't allow separation, we cap at limit (violating separation preference but respecting definition)
             f_max = freq_max_limit
         else:
             f_max = safe_max

    return {
        "frequency_min": f_min,
        "frequency_max": f_max,
        "period": period_limit_min,
        "waveform": params.waveform,
        "duty_cycle": params.duty_cycle,
        "type": params.type,
        "mode": params.mode,
        "mechanical_profile": params.mechanical_profile,
        "variable_wail": params.variable_wail,
        "tone_pattern": params.tone_pattern
    }

def save_spectrogram(audio_data: np.ndarray, sample_rate: int, output_path: str, title: str = "Spectrogram"):
    """
    Generates and saves a spectrogram plot for the given audio data.
    Automatically adjusts the frequency axis (ylim) to focus on the effective bandwidth.
    """
    if len(audio_data.shape) > 1:
        y = audio_data[:, 0] # mono
    else:
        y = audio_data
        
    # Compute Spectrogram
    # Sxx is the periodogram (magnitude squared)
    f, t, Sxx = signal.spectrogram(y, sample_rate, nperseg=1024, noverlap=512)
    
    # Analyze Spectrum to find effective bandwidth
    # Sum energy across time for each frequency bin
    freq_energy = np.sum(Sxx, axis=1)
    
    # Normalize
    total_energy = np.sum(freq_energy)
    if total_energy > 0:
        cum_energy = np.cumsum(freq_energy) / total_energy
        # Find frequency where 99% of energy is contained
        # returns index where constraint is met
        valid_indices = np.where(cum_energy >= 0.995)[0] 
        if len(valid_indices) > 0:
            top_freq_idx = valid_indices[0]
            effective_max_freq = f[top_freq_idx]
        else:
            effective_max_freq = sample_rate / 2
    else:
        effective_max_freq = sample_rate / 2

    # Add 10% margin, but clamp to Nyquist
    plot_max_freq = min(effective_max_freq * 1.2, sample_rate / 2)
    
    # Ensure we don't zoom in TOO much (e.g. valid silence or extremely low rumble)
    # Keep at least 2000Hz visible unless it's strictly sub-bass
    plot_max_freq = max(plot_max_freq, 2000.0)

    # Plot
    plt.figure(figsize=(10, 6))
    # Add epsilon to avoid log(0)
    Sxx_db = 10 * np.log10(Sxx + 1e-10)
    plt.pcolormesh(t, f, Sxx_db, shading='gouraud')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.title(f'{title}')
    plt.colorbar(label='Intensity [dB]')
    plt.ylim(0, plot_max_freq)
    
    try:
        plt.savefig(output_path)
    finally:
        plt.close()
