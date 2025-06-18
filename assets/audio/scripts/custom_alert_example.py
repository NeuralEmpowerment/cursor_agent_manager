from sound_generator import SoundGenerator
import numpy as np
import simpleaudio as sa

# Create a custom alert
def create_custom_alert():
    generator = SoundGenerator()
    
    # Example: Create a custom "tada" sound
    frequencies = [392, 494, 587, 784]  # G4, B4, D5, G5
    durations = [0.1, 0.1, 0.1, 0.4]
    amplitudes = [0.7, 0.8, 0.9, 1.0]
    
    # Combine the tones
    result = np.array([])
    for freq, dur, amp in zip(frequencies, durations, amplitudes):
        tone = generator.generate_tone(freq, dur, amp)
        tone = generator.apply_envelope(tone, attack=0.05, decay=0.05)
        result = np.concatenate([result, tone])
        
        # Add a tiny gap between notes
        gap = np.zeros(int(0.02 * generator.sample_rate))
        result = np.concatenate([result, gap])
    
    # Save and play the custom alert
    filepath = generator.save_wave(result, "alert_custom_tada.wav")
    print("Generated custom tada alert!")
    
    # Test the sound
    wave_obj = sa.WaveObject.from_wave_file(filepath)
    play_obj = wave_obj.play()
    play_obj.wait_done()

if __name__ == "__main__":
    create_custom_alert() 