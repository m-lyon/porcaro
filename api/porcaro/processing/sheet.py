'''Module for constructing a music21 sheet from a DataFrame.'''

import music21

from porcaro.utils.time_signature import TimeSignature

LABEL_PITCH_MAP = {
    'KD': 'F4',
    'SD': 'C5',
    'SD_xstick': 'C5',
    'HH_close': 'G5',
    'HH_open': 'G5',
    'RC': 'G5',
    'CC': 'A5',
    'HT': 'E5',
    'MT': 'D5',
    'FT': 'A4',
    'HH': 'G5',
    'TT': 'E5',
}


def construct_sheet(
    matched_durations: list[music21.duration.Duration],
    matched_notes: list[str],
    time_sig: TimeSignature,
) -> music21.stream.Stream:
    '''Constructs a sheet from the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing the transcription data.
        song_title (str): Title of the song.
        time_sig (TimeSignature): Time signature of the song.

    Returns:
        music21.stream.Stream: The constructed music21 stream.

    '''
    stream = music21.stream.Stream()
    stream.metadata = music21.metadata.Metadata()
    stream.metadata.composer = 'Porcaro Transcription'
    stream.append(music21.meter.TimeSignature(str(time_sig)))
    for duration, note in zip(matched_durations, matched_notes, strict=True):
        # instead of this dict, use a mapping function to convert note names to pitches
        # 'rest' -> music21.note.Rest()
        # will need to follow the logic within sheet_construction method of DrumTranscriber
        pitch = LABEL_PITCH_MAP[note]
        m21_note = music21.note.Note(pitch)
        m21_note.duration = duration
        stream.append(m21_note)
