from pydub import AudioSegment

# Load the .wav file
audio = AudioSegment.from_wav("./audio_references/davis_reference_full.wav")

# Get duration in milliseconds
duration_ms = len(audio)

# cut = audio[2.78 * duration_ms // 4 :duration_ms * 4/5.1]
cut = audio[52000:92000]


# Export to new file
cut.export("./audio_references/davis_trimmed.wav", format="wav")

print("Saved trimmed audio as trimmed.wav")