from enum import Enum
from typing import Dict, Optional, Union, List
from pydantic import BaseModel, Field

class Waveform(str, Enum):
    SINE = "sine"
    SQUARE = "square"
    SAWTOOTH = "sawtooth"
    TRIANGLE = "triangle"
    TRAPEZOID = "trapezoid"

class ParameterRange(BaseModel):
    min: float
    max: float

    def get_center(self) -> float:
        return (self.min + self.max) / 2

class SirenModeParams(BaseModel):
    frequency_range: ParameterRange = Field(..., description="Frequency sweep range in Hz")
    period_range: ParameterRange = Field(..., description="Modulation period range in seconds")
    waveform: Waveform = Field(default=Waveform.SQUARE, description="Waveform type")
    duty_cycle: Optional[float] = Field(0.5, description="Duty cycle for square/trapezoid waves (0.0-1.0)")
    
    # Specific options
    description: Optional[str] = "User defined siren mode"

class SirenDefinition(BaseModel):
    standard: str = Field(..., description="Name of the standard (e.g., SAE J1849) or 'User-Defined'")
    region: Optional[str] = Field(None, description="Country or Region of adoption")
    
    # Map from siren type name (e.g., "wail", "yelp") to its parameters
    modes: Dict[str, SirenModeParams]

    seed: Optional[int] = None

class RealismConfig(BaseModel):
    analog_saturation: bool = Field(True, description="Enable soft-clipping saturation")
    saturation_gain: float = Field(10.0, description="Input gain for saturation (tanh)")
    oscillator_jitter: bool = Field(True, description="Enable simulated voltage drift")
    jitter_amount: float = Field(0.01, description="Amount of jitter noise")
    horn_filter: bool = Field(True, description="Enable speaker frequency response simulation")
    
    # Mechanical Asymmetry Settings
    mechanical_asymmetry: bool = Field(True, description="Enable asymmetric envelope for mechanical sirens")
    mechanical_rise_ratio: float = Field(0.2, description="Proportion of period spent rising (0.0-1.0)")
    mechanical_rise_exponent: float = Field(0.5, description="Shape of rise (0.5=concave, 1.0=linear, 2.0=convex)")
    mechanical_fall_exponent: float = Field(2.0, description="Shape of fall (0.5=concave, 1.0=linear, 2.0=convex)")
    
    # Variable Wail (Randomize f_max per cycle)
    variable_wail: bool = Field(True, description="Vary f_max and period for each wail cycle")
    wail_variation_magnitude: float = Field(0.2, description="Magnitude of f_max variation (0.0-1.0)")

class BatchConfig(BaseModel):
    definition_file: str = Field(..., description="Path to the siren definition JSON file")
    output_dir: str = Field("./output", description="Directory to save generated samples")
    sample_rate: int = Field(44100, description="Sampling rate in Hz")
    bit_depth: int = Field(24, description="Bit depth (16, 24, 32)")
    num_iterations: int = Field(1, description="Number of samples to generate per siren mode")
    duration_s: float = Field(10.0, description="Duration in seconds for each sample")
    oversampling: int = Field(8, description="Oversampling factor for anti-aliasing (1 = off)")
    use_metal: bool = Field(False, description="Use Metal (MPS) acceleration if available")
    force_minor_third: bool = Field(False, description="Force Hi-Lo sirens to use a Minor Third interval")
    min_frequency_separation: float = Field(1.2, description="Minimum ratio between f_max and f_min (f_max >= k * f_min)")
    generate_spectrograms: bool = Field(False, description="Generate spectrogram images for each output file")
    
    # Realism Settings
    realism: RealismConfig = Field(default_factory=RealismConfig, description="Algorithmic realism settings")
    
    # Global overrides or settings
    seed: Optional[int] = None

class GenerationMetadata(BaseModel):
    filename: str
    standard: str
    siren_mode: str
    frequency_min: float
    frequency_max: float
    period: float
    waveform: str
    sample_rate: int
    duration_s: float
