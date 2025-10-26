import os
from pydub import AudioSegment
from typing import List, Optional

def combine_audio_files(input_files: List[str], output_filename: str) -> Optional[str]:
    """
    Combines a list of audio file paths into a single output file using pydub.
    Assumes input files are compatible (same sample rate/channels).
    Returns the path to the combined file on success, or None on failure.
    """
    if not input_files:
        print("Error: No audio files provided for combination.")
        return None

    # Use the first file to initialize the combined segment
    try:
        combined = AudioSegment.from_file(input_files[0])
    except Exception as e:
        print(f"Error initializing combination with {input_files[0]}: {e}")
        return None

    # Iterate through the rest of the files and append them
    for input_file in input_files[1:]:
        try:
            segment = AudioSegment.from_file(input_file)
            combined += segment
        except Exception as e:
            print(f"Warning: Skipping file {input_file} due to error: {e}")
            continue

    # Export the final combined audio (Exporting as WAV is safest/highest quality for podcast)
    try:
        combined.export(output_filename, format="wav")
        return os.path.abspath(output_filename) # Return the full path
    except Exception as e:
        print(f"Error exporting combined audio to {output_filename}: {e}")
        return None
