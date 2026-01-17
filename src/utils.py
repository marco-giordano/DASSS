import json
import yaml
import random
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

def sample_parameters(params: SirenModeParams) -> Dict[str, Any]:
    """
    Randomly samples parameters from the defined ranges using uniform distribution.
    """
    freq_min = params.frequency_range.min
    freq_max = params.frequency_range.max
    # Ensure min < max
    if freq_min > freq_max:
        freq_min, freq_max = freq_max, freq_min
        
    f_min = random.uniform(freq_min, freq_max)
    f_max = random.uniform(freq_min, freq_max)
    
    # Ensure sampled min < sampled max for the sweep
    if f_min > f_max:
        f_min, f_max = f_max, f_min
        
    # Period
    p_min = params.period_range.min
    p_max = params.period_range.max
    period = random.uniform(p_min, p_max)
    
    return {
        "frequency_min": f_min,
        "frequency_max": f_max,
        "period": period,
        "waveform": params.waveform,
        "duty_cycle": params.duty_cycle
    }
