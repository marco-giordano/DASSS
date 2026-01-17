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

def sample_parameters(params: SirenModeParams, min_separation: float = 1.0) -> Dict[str, Any]:
    """
    Randomly samples parameters from the defined ranges using uniform distribution.
    Enforces f_max >= f_min * min_separation.
    """
    freq_min_rng = params.frequency_range.min
    freq_max_rng = params.frequency_range.max
    # Ensure min < max
    if freq_min_rng > freq_max_rng:
        freq_min_rng, freq_max_rng = freq_max_rng, freq_min_rng
        
    # Sample f_min from the WHOLE allowed range first?
    # Or sample f_min such that a valid f_max exists?
    # Valid f_max must be >= f_min * sep.
    # So max possible f_min is freq_max_rng / sep.
    
    # Constraint: f_min * sep <= freq_max_rng
    limit_f_min = freq_max_rng / max(1.0, min_separation)
    
    valid_range_min = min(freq_min_rng, limit_f_min)
    # If the range is invalid (limit < freq_min_rng), we have a problem definition.
    # We'll just clamp.
    actual_limit_f_min = max(valid_range_min, limit_f_min)
    if actual_limit_f_min < freq_min_rng:
         # This means even the lowest f_min * sep > max_rng. 
         # Cannot satisfy. Just sample normally and warn? Or try best effort.
         # Let's pivot: Sample f_min normally. Then trying to find f_max.
         pass

    # Simplified Approach:
    # 1. Sample f_min from [freq_min_rng, freq_max_rng]
    # 2. Calculate min_f_max = f_min * sep
    # 3. If min_f_max > freq_max_rng:
    #    Retry f_min? Or clamp constraint?
    #    User says "taking f_min as a pivot".
    #    So we stick with sampled f_min.
    #    We must choose f_max in [min_f_max, freq_max_rng].
    #    If min_f_max > freq_max_rng, we can't satisfy both range and separation.
    #    Separation usually wins for realism? Or Range wins for compliance?
    #    Let's assume Definition is broad enough.
    
    # Let's try to enable valid sampling by restricting f_min if possible.
    effective_max_fmin = freq_max_rng / min_separation
    
    # Sample f_min
    # Cap f_min sampling to ensure room for f_max
    sampling_max_fmin = min(freq_max_rng, effective_max_fmin)
    if sampling_max_fmin < freq_min_rng:
        # Range is too tight or sep too large. 
        # Fallback: sample freely
        f_min = random.uniform(freq_min_rng, freq_max_rng)
    else:
        f_min = random.uniform(freq_min_rng, sampling_max_fmin)
        
    # Calculate required minimum for f_max
    req_f_max_low = f_min * min_separation
    
    # Allowed range for f_max is [max(req_f_max_low, freq_min_rng), freq_max_rng]
    # (Since f_max must also be in [min, max] typically, or just > f_min?)
    # "choosing f_max in the range between the minimum separation and the maximum provided by the definition file"
    low_bound = max(req_f_max_low, freq_min_rng)
    high_bound = freq_max_rng
    
    if low_bound > high_bound:
        # Conflict. Separation pushes f_max outside allowed definition.
        # Use high_bound (clamp) or low_bound (violate range)?
        # Assume Separation is a soft "try to", but Definition is hard?
        # User said "choosing f_max in the range between the minimum separation and the maximum".
        # If min_sep > max, then range is empty.
        # We will just clamp f_max to high_bound.
        f_max = high_bound
    else:
        f_max = random.uniform(low_bound, high_bound)
    
    # Ensure min < max final check (if sep < 1.0)
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
