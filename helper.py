from pydub import AudioSegment

# Load the .wav file
audio = AudioSegment.from_wav("audio_references/davis_reference_full.wav")

# Get duration in milliseconds
duration_ms = len(audio)

cut = audio[3 * duration_ms // 4 :duration_ms * 4/5.1]

# Export to new file
cut.export("audio_references/davis_trimmed_quarter.wav", format="wav")

print("Saved trimmed audio as trimmed.wav")
