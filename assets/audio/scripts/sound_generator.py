import numpy as np
import simpleaudio as sa
import wave
import struct
from typing import List, Tuple
import os

class SoundGenerator:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.output_dir = os.path.dirname(os.path.abspath(__file__))

    def generate_tone(self, frequency: float, duration: float, amplitude: float = 1.0) -> np.ndarray:
        """Generate a single tone."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return amplitude * np.sin(2 * np.pi * frequency * t)

    def apply_envelope(self, samples: np.ndarray, attack: float = 0.1, decay: float = 0.1) -> np.ndarray:
        """Apply an ADSR envelope to the samples."""
        num_samples = len(samples)
        attack_samples = int(attack * self.sample_rate)
        decay_samples = int(decay * self.sample_rate)
        
        envelope = np.ones(num_samples)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
        
        return samples * envelope

    def save_wave(self, samples: np.ndarray, filename: str):
        """Save the samples as a WAV file."""
        # Normalize and convert to 16-bit integers
        normalized = np.int16(samples * 32767)
        
        filepath = os.path.join(self.output_dir, filename)
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(struct.pack('h' * len(normalized), *normalized))
        
        return filepath

    def generate_pattern(self, pattern_type: str) -> np.ndarray:
        """Generate different sound patterns."""
        if pattern_type == "ascending":
            # Ascending pattern (doo doo DOO!)
            frequencies = [330, 392, 494]  # E4, G4, B4
            durations = [0.2, 0.2, 0.4]
            amplitudes = [0.7, 0.8, 1.0]
        
        elif pattern_type == "descending":
            # Descending pattern (DOO doo doo...)
            frequencies = [494, 392, 330]  # B4, G4, E4
            durations = [0.4, 0.2, 0.2]
            amplitudes = [1.0, 0.8, 0.7]
        
        elif pattern_type == "notification":
            # Short notification (ding!)
            frequencies = [784]  # G5
            durations = [0.3]
            amplitudes = [1.0]
        
        elif pattern_type == "warning":
            # Warning pattern (doo-doo, doo-doo)
            frequencies = [392, 330, 392, 330]  # G4, E4, G4, E4
            durations = [0.2, 0.2, 0.2, 0.2]
            amplitudes = [1.0, 0.8, 1.0, 0.8]
        
        elif pattern_type == "success":
            # Success pattern (doo doo DOOO)
            frequencies = [392, 494, 587]  # G4, B4, D5
            durations = [0.2, 0.2, 0.5]
            amplitudes = [0.7, 0.8, 1.0]
        
        elif pattern_type == "error":
            # Error pattern (DOO doo...)
            frequencies = [466, 415]  # A#4, Ab4
            durations = [0.3, 0.4]
            amplitudes = [1.0, 0.7]
        
        elif pattern_type == "waiting":
            # Waiting pattern (doo... doo...)
            frequencies = [392, 392, 392]  # G4, G4, G4
            durations = [0.2, 0.2, 0.2]
            amplitudes = [0.7, 0.5, 0.3]
        
        elif pattern_type == "completed":
            # Task completed (doo doo doo DOOO)
            frequencies = [392, 440, 494, 587]  # G4, A4, B4, D5
            durations = [0.15, 0.15, 0.15, 0.4]
            amplitudes = [0.7, 0.8, 0.9, 1.0]
        
        elif pattern_type == "thinking":
            # Thinking pattern (doo... doo... doo...)
            frequencies = [330, 392, 330, 392]  # E4, G4, E4, G4
            durations = [0.2, 0.2, 0.2, 0.2]
            amplitudes = [0.6, 0.8, 0.6, 0.8]
        
        else:  # default
            frequencies = [440]  # A4
            durations = [0.3]
            amplitudes = [1.0]

        # Generate and combine the tones
        result = np.array([])
        for freq, dur, amp in zip(frequencies, durations, amplitudes):
            tone = self.generate_tone(freq, dur, amp)
            tone = self.apply_envelope(tone, attack=0.05, decay=0.05)
            result = np.concatenate([result, tone])
            
            # Add a tiny gap between notes
            gap = np.zeros(int(0.02 * self.sample_rate))
            result = np.concatenate([result, gap])

        return result

def generate_all_alerts():
    """Generate all alert sound variations."""
    generator = SoundGenerator()
    patterns = [
        "ascending", "descending", "notification", "warning",
        "success", "error", "waiting", "completed", "thinking"
    ]
    
    for pattern in patterns:
        samples = generator.generate_pattern(pattern)
        filename = f"alert_{pattern}.wav"
        filepath = generator.save_wave(samples, filename)
        
        # Test the sound
        print(f"Generated {filename}")
        wave_obj = sa.WaveObject.from_wave_file(filepath)
        play_obj = wave_obj.play()
        play_obj.wait_done()  # Wait until sound has finished playing

if __name__ == "__main__":
    generate_all_alerts() 