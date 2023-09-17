import pyaudio
import numpy as np
from pydub import AudioSegment
from pydub.playback import play

# Initialize the audio recorder
p = pyaudio.PyAudio()

# Define audio recording parameters
format = pyaudio.paInt16
channels = 1
sample_rate = 44100
chunk = 1024

# Start recording
stream = p.open(format=format,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk)

print("Recording... (Press Ctrl+C to stop)")

frames = []

try:
    while True:
        data = stream.read(chunk)
        frames.append(data)
except KeyboardInterrupt:
    pass

print("Recording stopped.")

# Stop and close the audio stream
stream.stop_stream()
stream.close()
p.terminate()

# Convert the recorded audio data to an audio segment
audio = AudioSegment(
    np.frombuffer(b"".join(frames), dtype=np.int16),
    frame_rate=sample_rate,
    sample_width=2,
    channels=1,
)

# Calculate pitch (a basic proxy for stress)
pitch = audio.dBFS  # You can use other pitch estimation libraries for more accuracy

# Determine stress level based on pitch
print(pitch)
if pitch > -20:
    print("High stress detected.")
else:
    print("Low stress detected.")

# Play back the recorded audio
play(audio)
