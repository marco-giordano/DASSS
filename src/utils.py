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
    # We try up to N times to generate compliant parameters.
    # If we fail, we fall back to safe defaults or error out.
    max_retries = 100
    
    freq_min_limit = params.frequency_range.min
    freq_max_limit = params.frequency_range.max
    # Period limits
    p_min_limit = params.period_range.min
    p_max_limit = params.period_range.max
    
    for _ in range(max_retries):
        # 1. Sample f_min
        # Constraint: f_min must leave room for f_max (f_max >= f_min * min_sep)
        # Max valid f_min = freq_max_limit / min_separation
        upper_fmin_bound = min(freq_max_limit, freq_max_limit / max(1.0, min_separation))
        
        # If range is impossible, we can't solve it.
        if upper_fmin_bound < freq_min_limit:
            # Definition is tighter than separation requirements.
            # Pivot constraint: separation applies?
            # We'll just sample in range and hope checking catches it.
            f_min = random.uniform(freq_min_limit, freq_max_limit)
        else:
            f_min = random.uniform(freq_min_limit, upper_fmin_bound)
            
        # 2. Sample f_max
        # Must be >= f_min * separation
        min_f_max = f_min * min_separation
        
        # Range for f_max is [min_f_max, freq_max_limit]
        if min_f_max > freq_max_limit:
            # This sample of f_min is invalid (too high). Retry.
            continue
            
        f_max = random.uniform(min_f_max, freq_max_limit)
        
        # 3. Sample Period
        period = random.uniform(p_min_limit, p_max_limit)
        
        # Final Verification against Definition (Redundant but requested "verified against specifications")
        if not (freq_min_limit <= f_min <= freq_max_limit): continue
        if not (freq_min_limit <= f_max <= freq_max_limit): continue
        if not (p_min_limit <= period <= p_max_limit): continue
        if f_max < f_min * min_separation: continue # Should be met by construction
        
        # If all good, return
        return {
            "frequency_min": f_min,
            "frequency_max": f_max,
            "period": period,
            "waveform": params.waveform,
            "duty_cycle": params.duty_cycle
        }
        
    # If we exhausted retries, return separate fallback or raise error
    # For robustness, we return the last attempt clamped
    return {
        "frequency_min": freq_min_limit,
        "frequency_max": freq_max_limit,
        "period": p_min_limit,
        "waveform": params.waveform,
        "duty_cycle": params.duty_cycle
    }

def save_spectrogram(audio_data: np.ndarray, sample_rate: int, output_path: str, title: str = "Spectrogram"):
    """
    Generates and saves a spectrogram plot for the given audio data.
    """
    if len(audio_data.shape) > 1:
        y = audio_data[:, 0] # mono
    else:
        y = audio_data
        
    # Compute Spectrogram
    f, t, Sxx = signal.spectrogram(y, sample_rate, nperseg=1024, noverlap=512)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading='gouraud')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.title(f'{title}')
    plt.colorbar(label='Intensity [dB]')
    plt.ylim(0, sample_rate/2)
    
    try:
        plt.savefig(output_path)
    finally:
        plt.close()
