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

class BatchConfig(BaseModel):
    definition_file: str = Field(..., description="Path to the siren definition JSON file")
    output_dir: str = Field("./output", description="Directory to save generated samples")
    sample_rate: int = Field(44100, description="Sampling rate in Hz")
    bit_depth: int = Field(24, description="Bit depth (16, 24, 32)")
    num_iterations: int = Field(1, description="Number of samples to generate per siren mode")
    duration_s: float = Field(10.0, description="Duration in seconds for each sample")
    oversampling: int = Field(8, description="Oversampling factor for anti-aliasing (1 = off)")
    
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
