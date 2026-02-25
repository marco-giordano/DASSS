from enum import Enum
from typing import Dict, Optional, Union, List
from pydantic import BaseModel, Field

class Waveform(str, Enum):
    SINE = "sine"
    SQUARE = "square"
    SAWTOOTH = "sawtooth"
    TRIANGLE = "triangle"
    TRAPEZOID = "trapezoid"

class SirenType(str, Enum):
    ELECTRONIC = "electronic"
    MECHANICAL = "mechanical"
    PNEUMATIC = "pneumatic"

class SirenModeEnum(str, Enum):
    WAIL = "wail"
    YELP = "yelp"
    HI_LO = "hi-lo"
    TWO_TONE = "two-tone"
    PHASER = "phaser"
    PIERCER = "piercer"
    RUMBLER = "rumbler"

class ParameterRange(BaseModel):
    min: float
    max: float

    def get_center(self) -> float:
        return (self.min + self.max) / 2

class MechanicalProfile(BaseModel):
    rise_ratio: float = 0.2
    rise_exponent: float = 0.5
    fall_exponent: float = 2.0

class VariableWailConfig(BaseModel):
    enabled: bool = True
    variation_magnitude: float = 0.2

class NominalFrequencies(BaseModel):
    min: float
    max: float

class SirenModeParams(BaseModel):
    type: SirenType = Field(..., description="Type of siren generation")
    mode: SirenModeEnum = Field(..., description="Mode category")
    
    # Core Parameters
    frequency_range: Optional[ParameterRange] = Field(None, description="Frequency sweep range in Hz (optional if nominal used)")
    period_range: Optional[ParameterRange] = Field(None, description="Modulation period range in seconds")
    nominal_frequencies: Optional[NominalFrequencies] = Field(None, description="Exact fixed frequencies")
    
    # Waveform
    waveform: Union[Waveform, List[Waveform]] = Field(default=Waveform.SQUARE, description="Waveform type or list of types")
    duty_cycle: Optional[float] = Field(0.5, description="Duty cycle for square/trapezoid waves (0.0-1.0)")
    
    # Specific options
    mechanical_profile: Optional[MechanicalProfile] = Field(None, description="Envelope settings for mechanical/pneumatic types")
    variable_wail: Optional[VariableWailConfig] = Field(None, description="Variable wail randomization settings")
    tone_pattern: Optional[str] = Field(None, description="6-character string for duty cycle pattern (e.g. 'hhhlll')")
    
    description: Optional[str] = "User defined siren mode"

class SirenDefinition(BaseModel):
    standard: str = Field(..., description="Name of the standard (e.g., SAE J1849) or 'User-Defined'")
    region: Optional[str] = Field(None, description="Country or Region of adoption")
    
    # Map from siren type name to its parameters
    modes: Dict[str, SirenModeParams]

    seed: Optional[int] = None

class RealismConfig(BaseModel):
    analog_saturation: bool = Field(True, description="Enable soft-clipping saturation")
    saturation_gain: float = Field(10.0, description="Input gain for saturation (tanh)")
    oscillator_jitter: bool = Field(True, description="Enable simulated voltage drift")
    jitter_amount: float = Field(0.01, description="Amount of jitter noise")
    horn_filter: bool = Field(True, description="Enable speaker frequency response simulation")
    mechanical_asymmetry: bool = Field(True, description="Global enable for asymmetric envelope (overrides per-mode if False)")

class BatchConfig(BaseModel):
    definition_file: str = Field(..., description="Path to the siren definition JSON file")
    output_dir: str = Field("./output", description="Directory to save generated samples")
    sample_rate: int = Field(44100, description="Sampling rate in Hz")
    bit_depth: int = Field(24, description="Bit depth (16, 24, 32)")
    num_iterations: int = Field(1, description="Number of samples to generate per siren mode")
    duration_s: float = Field(10.0, description="Duration in seconds for each sample")
    oversampling: int = Field(8, description="Oversampling factor for anti-aliasing (1 = off)")
    use_metal: bool = Field(False, description="Use Metal (MPS) acceleration if available")
    
    # min_frequency_separation: Logic is now complex. Kept as fallback.
    min_frequency_separation: float = Field(1.2, description="Fallback minimum ratio between f_max and f_min")
    
    enforce_complete_cycle: bool = Field(True, description="Ensure audio ends after a complete cycle (extends duration if needed)")
    generate_spectrograms: bool = Field(False, description="Generate spectrogram images for each output file")
    
    # Realism Settings
    realism: RealismConfig = Field(default_factory=RealismConfig, description="Algorithmic realism settings")
    
    # Global overrides or settings
    seed: Optional[int] = None

class GenerationMetadata(BaseModel):
    filename: str
    standard: str
    siren_mode: str
    mode: str
    type: str
    frequency_min: float
    frequency_max: float
    period: float
    waveform: str
    sample_rate: int
    duration_s: float
