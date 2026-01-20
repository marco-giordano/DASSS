import argparse
import os
import soundfile as sf
import time
import shutil
from pathlib import Path
from src.utils import load_json_definition, load_yaml_config, sample_parameters, save_metadata, save_spectrogram
from src.generator import SirenSynthesizer
from src.schemas import GenerationMetadata, Waveform

def main():
    parser = argparse.ArgumentParser(description="DASSS: Dry Anechoic Synthetic Siren Sounds Generator")
    parser.add_argument("config", help="Path to the batch configuration YAML file")
    args = parser.parse_args()

    # Load Batch Config
    print(f"Loading batch config from {args.config}...")
    batch_config = load_yaml_config(args.config)
    
    # Load Siren Definition
    print(f"Loading siren definition from {batch_config.definition_file}...")
    siren_def = load_json_definition(batch_config.definition_file)
    
    # Setup Output
    output_dir = Path(batch_config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Synthesizer
    synth = SirenSynthesizer(
        sample_rate=batch_config.sample_rate, 
        oversample=batch_config.oversampling,
        use_metal=batch_config.use_metal,
        realism_config=batch_config.realism
    )
    
    
    # 1. Backup Config File
    # 1. Backup Config File
    try:
        shutil.copy(args.config, output_dir / Path(args.config).name)
        print(f"Backed up config to {output_dir / Path(args.config).name}")
    except Exception as e:
        print(f"Warning: Failed to backup config file: {e}")
        
    # 2. Backup Definition File (JSON)
    try:
        shutil.copy(batch_config.definition_file, output_dir / Path(batch_config.definition_file).name)
        print(f"Backed up definition to {output_dir / Path(batch_config.definition_file).name}")
    except Exception as e:
        print(f"Warning: Failed to backup definition file: {e}")

    # 2. Prepare Spectrogram Folder
    spectrogram_dir = output_dir / "spectrograms"
    if batch_config.generate_spectrograms:
        spectrogram_dir.mkdir(parents=True, exist_ok=True)

    metadata_list = []
    
    print(f"Starting generation loop for standard: {siren_def.standard}...")
    
    for mode_name, mode_params in siren_def.modes.items():
        print(f"  Generating {batch_config.num_iterations} samples for mode: {mode_name}")
        
        for i in range(batch_config.num_iterations):
            # Constraint Logic:
            # If force_minor_third is active for Hi-Lo, we shouldn't enforce the large min_separation
            # because the ratio is fixed (approx 1.19) and might be smaller than min_separation (e.g. 1.5).
            # Also, standard Separation (1.5) might exceed Hi-Lo defined range (450-600).
            current_separation = batch_config.min_frequency_separation
            if batch_config.force_minor_third and ("hi-lo" in mode_name.lower() or "two-tone" in mode_name.lower()):
                current_separation = 1.0 # Relax constraint, let minor third logic handle it later
            
            # Sample parameters
            params = sample_parameters(mode_params, min_separation=current_separation)
            
            # Duration from config
            duration_s = batch_config.duration_s
            
            # Generate Audio
            # Check if it's a Hi-Lo (Two-Tone) or Sweep
            # We determine by checking if we have discrete frequencies or a range that implies sweeping.
            # However, the current schema `ParameterRange` implies a range for Randomization, not necessarily discrete tones.
            # A Hi-Lo is typically defined by specific alternating frequencies.
            # Our current schema groups everything into "frequency_range" and "period".
            # To strictly support Hi-Lo with the current schema, we might need to interpret "Hi-Lo" name or add a "type" field.
            # For now, let's assume 'wail'/'yelp'/'phaser' are sweeps, and 'hi-lo' is two-tone.
            # A robust way is to add specific logic or schema fields. 
            # Given the prompt asked for "parameters that define the synthesis", let's assume standard behavior based on mode name 
            # OR we could add a `siren_type` field to the schema. 
            # Let's keep it simple: If 'hi-lo' in name lower case, use two-tone logic? 
            # Or better, we can add a 'siren_class' to `SirenModeParams` in `schemas.py`? 
            # Updating schemas now would require refactoring. 
            # Let's infer for now or update schemas if I can. 
            # Actually, I'll update `schemas.py` to include `type` field in `SirenModeParams` for robustness.
            
            # WAIT: I will update `schemas.py` in a separate step if I decide to. 
            # For this MVP, let's just stick to the generator logic:
            # If the mode name suggests Hi-Lo, we treat it as two tone? 
            # But wait, `f_min` and `f_max` are sampled from ranges.
            # For Hi-Lo, we need f1 and f2. 
            # Let's assume f_min is Low and f_max is High for the specific instance.
            
            # Minor Third Forcing
            if batch_config.force_minor_third and ("hi-lo" in mode_name.lower() or "two-tone" in mode_name.lower()):
                # Calculate Minor Third (3 semitones)
                # Ratio = 2^(3/12) ~= 1.189207
                # We enforce f2 = f1 * Ratio
                # Use f_min as base
                f_base = params['frequency_min']
                f_minor = f_base * (2 ** (3/12))
                params['frequency_max'] = f_minor
                print(f"    [Forced Minor Third] {f_base:.1f}Hz -> {f_minor:.1f}Hz")

            audio = None
            if "hi-lo" in mode_name.lower() or "two-tone" in mode_name.lower():
                 audio = synth.generate_two_tone(
                    f1=params['frequency_min'], 
                    f2=params['frequency_max'], 
                    period=params['period'], 
                    waveform=params['waveform'], 
                    duration_s=duration_s,
                    duty_cycle=params['duty_cycle']
                )
            else:
                # Determine siren type for realism
                # Wail = Mechanical (usually)
                # Others = Electronic
                siren_type = 'mechanical' if 'wail' in mode_name.lower() else 'electronic'
                
                audio = synth.generate_siren_cycle(
                    f_min=params['frequency_min'], 
                    f_max=params['frequency_max'], 
                    period=params['period'], 
                    waveform=params['waveform'], 
                    duration_s=duration_s,
                    duty_cycle=params['duty_cycle'],
                    siren_type=siren_type
                )
            
            # Filename - Simplified without timestamp
            # Use zfill for better sorting: wail_00, wail_01
            filename = f"{siren_def.standard}_{mode_name}_{str(i).zfill(2)}.wav".replace(" ", "_")
            filepath = output_dir / filename
            
            # Save Audio
            sf.write(filepath, audio, batch_config.sample_rate, subtype='PCM_24')
            print(f"    Saved: {filepath}")

            # Save Spectrogram if enabled
            if batch_config.generate_spectrograms:
                spec_filename = f"{filename}.png"
                spec_path = spectrogram_dir / spec_filename
                save_spectrogram(
                    audio_data=audio, 
                    sample_rate=batch_config.sample_rate, 
                    output_path=str(spec_path),
                    title=f"{mode_name} - {filename}"
                )
            
            # Add to Metadata
            meta = GenerationMetadata(
                filename=filename,
                standard=siren_def.standard,
                siren_mode=mode_name,
                frequency_min=params['frequency_min'],
                frequency_max=params['frequency_max'],
                period=params['period'],
                waveform=params['waveform'].value,
                sample_rate=batch_config.sample_rate,
                duration_s=duration_s
            )
            metadata_list.append(meta)
            
    # Save Metadata
    meta_path = output_dir / "metadata.csv"
    save_metadata(metadata_list, str(meta_path))
    print(f"Batch generation complete. Output in {output_dir}")

if __name__ == "__main__":
    main()
