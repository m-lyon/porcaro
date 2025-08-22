'''Module for constructing a music21 sheet from a DataFrame.'''

from functools import partial

import music21

from porcaro.utils.time_signature import TimeSignature

LABEL_PITCH_MAP = {
    'REST': music21.note.Rest,
    'KD': partial(music21.note.Note, 'F4'),
    'SD': partial(music21.note.Note, 'C5'),
    'SD_xstick': partial(music21.note.Note, 'C5'),
    'HH_close': partial(music21.note.Note, 'G5'),
    'HH_open': partial(music21.note.Note, 'G5'),
    'RC': partial(music21.note.Note, 'G5'),
    'CC': partial(music21.note.Note, 'A5'),
    'HT': partial(music21.note.Note, 'E5'),
    'MT': partial(music21.note.Note, 'D5'),
    'FT': partial(music21.note.Note, 'A4'),
    'HH': partial(music21.note.Note, 'G5'),
    'TT': partial(music21.note.Note, 'E5'),
}

NOTEHEAD_MAP = {'HH_close': 'x', 'HH_open': 'circle-x', 'RC': 'x', 'HH': 'x'}


def get_note_from_label(
    label: str | list[str], duration: music21.duration.Duration
) -> music21.note.Note | music21.percussion.PercussionChord:
    '''Returns a music21 note for the given label.

    Args:
        label (str | list[str]): The label(s) of the note.
        duration (music21.duration.Duration): The duration of the note.

    Returns:
        music21.note.Note: The corresponding music21 note.

    Returns:
        music21.note.Note: The corresponding music21 note.

    '''
    note: music21.note.Note | music21.percussion.PercussionChord
    if isinstance(label, list):
        notes = [get_note_from_label(lbl, duration) for lbl in label]
        note = music21.percussion.PercussionChord(notes)
        note.duration = duration
    else:
        note = LABEL_PITCH_MAP[label]()
        if label in NOTEHEAD_MAP:
            note.notehead = NOTEHEAD_MAP[label]
    note.duration = duration
    note.stemDirection = 'up'
    return note


def construct_sheet(
    matched_durations: list[music21.duration.Duration],
    matched_notes: list[str | list[str]],
    time_sig: TimeSignature,
) -> music21.stream.Stream:
    '''Constructs a sheet from the DataFrame.

    Args:
        matched_durations (list[music21.duration.Duration]): List of matched durations.
        matched_notes (list[str | list[str]]): List of matched note types.
        time_sig (TimeSignature): The time signature of the song.

    Returns:
        music21.stream.Stream: The constructed music21 stream.

    '''
    stream = music21.stream.Stream()
    stream.metadata = music21.metadata.Metadata()
    stream.metadata.composer = 'Porcaro Transcription'
    stream.append(music21.meter.TimeSignature(str(time_sig)))
    for duration, note in zip(matched_durations, matched_notes, strict=True):
        m21_note = get_note_from_label(note, duration)
        stream.append(m21_note)
    stream = stream.makeMeasures()
    return stream
