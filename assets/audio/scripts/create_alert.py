import numpy as np
import simpleaudio as sa
import wave
import struct

# Generate a simple beep sound
sample_rate = 44100
duration = 0.5  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))
frequency = 440  # Hz (A4 note)
samples = np.sin(2 * np.pi * frequency * t)

# Convert to 16-bit integers
audio = np.int16(samples * 32767)

# Save as WAV file
with wave.open('idle_alert.wav', 'w') as wav_file:
    # Set parameters
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 2 bytes per sample
    wav_file.setframerate(sample_rate)
    
    # Write the frames
    wav_file.writeframes(struct.pack('h' * len(audio), *audio))

print("Created idle_alert.wav successfully!")

# Test the sound
wave_obj = sa.WaveObject.from_wave_file('idle_alert.wav')
play_obj = wave_obj.play()
play_obj.wait_done()  # Wait until sound has finished playing 