import argparse
import os
import soundfile as sf
import time
import shutil
from pathlib import Path
from src.utils import load_json_definition, load_yaml_config, sample_parameters, save_metadata, save_spectrogram
from src.generator import SirenSynthesizer
from src.schemas import GenerationMetadata, Waveform, SirenModeEnum

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
    
    samples_dir = output_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    total_items = len(siren_def.modes) * batch_config.num_iterations
    current_item = 0
    start_time = time.time()
    
    print(f"Starting generation loop for standard: {siren_def.standard}...")
    
    for mode_name, mode_params in siren_def.modes.items():
        print(f"  Generating {batch_config.num_iterations} samples for mode: {mode_name}")
        
        for i in range(batch_config.num_iterations):
            current_item += 1
            if current_item > 1:
                elapsed_time = time.time() - start_time
                avg_time = elapsed_time / (current_item - 1)
                remaining_items = total_items - (current_item - 1)
                eta_seconds = avg_time * remaining_items
                import datetime
                eta_str = str(datetime.timedelta(seconds=int(eta_seconds)))
                print(f"    [Progress: {current_item}/{total_items} | ETA: {eta_str}]")
            else:
                print(f"    [Progress: {current_item}/{total_items} | ETA: Calculating...]")
            # Fallback separation
            current_separation = batch_config.min_frequency_separation
            
            # Sample parameters
            # utils.py handles nominal vs range logic
            params = sample_parameters(mode_params, min_separation=current_separation)
            
            # Duration from config
            duration_s = batch_config.duration_s
            
            # Determine Mode Category for Dispatch
            # params['mode'] is SirenModeEnum member
            mode_enum = params['mode']
            
            # Determine max_freq_limit for clamping (if sweep)
            max_freq_limit = 20000.0
            if mode_params.frequency_range:
                max_freq_limit = mode_params.frequency_range.max
            elif mode_params.nominal_frequencies:
                max_freq_limit = mode_params.nominal_frequencies.max

            audio = None
            if mode_enum in [SirenModeEnum.HI_LO, SirenModeEnum.TWO_TONE]:
                 audio = synth.generate_two_tone(
                    f1=params['frequency_min'], 
                    f2=params['frequency_max'], 
                    period=params['period'], 
                    waveform=params['waveform'], 
                    duration_s=duration_s,
                    duty_cycle=params['duty_cycle'],
                    enforce_cycle=batch_config.enforce_complete_cycle,
                    tone_pattern=params['tone_pattern']
                )
            else:
                # Sweep Based (Wail, Yelp, Phaser, Piercer, Rumbler)
                audio = synth.generate_siren_cycle(
                    f_min=params['frequency_min'], 
                    f_max=params['frequency_max'], 
                    period=params['period'], 
                    waveform=params['waveform'], 
                    duration_s=duration_s,
                    duty_cycle=params['duty_cycle'],
                    siren_type=params['type'],
                    mechanical_profile=params['mechanical_profile'],
                    variable_wail_config=params['variable_wail'],
                    max_freq_limit=max_freq_limit,
                    enforce_cycle=batch_config.enforce_complete_cycle
                )
            
            # Filename: {mode}_{type}_{waveform}_{iteration:02d}.wav
            mode_str = params['mode'].value if hasattr(params['mode'], 'value') else str(params['mode'])
            type_str = params['type'].value if hasattr(params['type'], 'value') else str(params['type'])
            waveform_str = params['waveform'].value if hasattr(params['waveform'], 'value') else str(params['waveform'])
            filename = f"{mode_str}_{type_str}_{waveform_str}_{str(i).zfill(2)}.wav"
            filepath = samples_dir / filename
            
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
            # Calculate actual duration from generated audio
            actual_duration = len(audio) / batch_config.sample_rate
            
            meta = GenerationMetadata(
                filename=filename,
                standard=siren_def.standard,
                siren_mode=mode_name,
                mode=params['mode'].value if hasattr(params['mode'], 'value') else params['mode'],
                type=params['type'].value if hasattr(params['type'], 'value') else params['type'],
                frequency_min=params['frequency_min'],
                frequency_max=params['frequency_max'],
                period=params['period'],
                waveform=params['waveform'].value if hasattr(params['waveform'], 'value') else params['waveform'],
                sample_rate=batch_config.sample_rate,
                duration_s=actual_duration
            )
            metadata_list.append(meta)
            
    # Save Metadata
    meta_path = output_dir / "metadata.csv"
    save_metadata(metadata_list, str(meta_path))
    
    end_time = time.time()
    import datetime
    total_time_str = str(datetime.timedelta(seconds=int(end_time - start_time)))
    print(f"Batch generation complete in {total_time_str}. Output in {output_dir}")

if __name__ == "__main__":
    main()
