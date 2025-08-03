'''Transcriber for drum predictions.'''

import logging
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import librosa
from music21 import note
from music21 import meter
from music21 import stream
from music21 import duration
from music21 import metadata
from music21 import percussion

from porcaro.utils import TimeSignature
from porcaro.utils.bpm import BPM

logger = logging.getLogger(__name__)


class Grid:
    '''Class to handle grid calculations for drum transcription.'''

    def __init__(
        self,
        eighth_note_grid: np.ndarray,
        sixteenth_note_grid: None | np.ndarray = None,
        thirty_second_note_grid: None | np.ndarray = None,
        eighth_note_triplet_grid: None | np.ndarray = None,
        eighth_note_sixlet_grid: None | np.ndarray = None,
    ):
        '''Initialize the Grid class.'''
        self.eighth_notes = eighth_note_grid
        self._sixteenth_notes: None | np.ndarray = sixteenth_note_grid
        self._thirty_second_notes: None | np.ndarray = thirty_second_note_grid
        self._eighth_note_triplets: None | np.ndarray = eighth_note_triplet_grid
        self._eighth_note_sixlets: None | np.ndarray = eighth_note_sixlet_grid

    @property
    def sixteenth_notes(self) -> np.ndarray:
        '''The sixteenth note grid.'''
        if self._sixteenth_notes is not None:
            return self._sixteenth_notes
        self._sixteenth_notes = self.eighth_notes[:-1] + (
            np.diff(self.eighth_notes) / 2
        )
        return self._sixteenth_notes

    @property
    def thirty_second_notes(self) -> np.ndarray:
        '''The thirty-second note grid.'''
        if self._thirty_second_notes is not None:
            return self._thirty_second_notes
        combined = np.sort(
            np.concatenate((self.eighth_notes, self.sixteenth_notes), axis=0)
        )
        self._thirty_second_notes = combined[:-1] + (np.diff(combined) / 2)
        return self._thirty_second_notes

    @property
    def eighth_note_triplets(self) -> np.ndarray:
        '''The eighth note triplet grid.'''
        if self._eighth_note_triplets is not None:
            return self._eighth_note_triplets
        triplets_first = self.eighth_notes[:-1] + (np.diff(self.eighth_notes) / 3)
        triplets_second = self.eighth_notes[:-1] + (np.diff(self.eighth_notes) / 3 * 2)
        self._eighth_note_triplets = np.sort(
            np.concatenate((triplets_first, triplets_second), axis=0)
        )
        return self._eighth_note_triplets

    @property
    def eighth_note_sixlets(self) -> np.ndarray:
        '''The eighth note sixlet grid.'''
        if self._eighth_note_sixlets is not None:
            return self._eighth_note_sixlets
        combined = np.sort(
            np.concatenate((self.eighth_note_triplets, self.eighth_notes), axis=0)
        )
        self._eighth_note_sixlets = combined[:-1] + (np.diff(combined) / 2)
        return self._eighth_note_sixlets


class DrumTranscriber:
    '''Transcribes drum predictions into readable sheet music format.'''

    def __init__(
        self,
        predictions: pd.DataFrame,
        duration: float,
        bpm: float,
        sample_rate: int | float,
        time_sig: TimeSignature,
        note_offset: int | None = None,
        song_title: None | str = None,
    ):
        '''Initialize the DrumTranscriber.'''
        self.time_sig = time_sig
        self.duration = duration
        self.beats_in_measure = self.time_sig.beats_in_measure * 2
        self.bpm = BPM(bpm)
        self.sample_rate = sample_rate
        self._note_offset = note_offset
        self.predictions = predictions
        self.note_line = predictions.peak_sample.apply(
            lambda x: librosa.samples_to_time(x, sr=sample_rate)
        ).to_numpy()
        eighth_notes = self.get_eighth_note_time_grid(self.note_offset)
        synced_eighth_notes = self.map_onsets_to_eighth_notes(eighth_notes)
        self.grid = Grid(synced_eighth_notes)
        self.synced_grid = self.master_sync(self.grid)
        pitch_dict = self.get_pitch_dict()
        stream_time_map, stream_pitch, stream_note = self.build_stream(
            self.grid, pitch_dict, self.synced_grid
        )
        music21_data = self.get_music21_data(stream_time_map, stream_pitch, stream_note)
        self.sheet = self.sheet_construction(music21_data, song_title=song_title)

    @property
    def offset(self) -> bool:
        '''Check if the note offset is set.'''
        return bool(self._note_offset)

    @property
    def note_offset(self) -> int:
        '''Get the note offset.'''
        if isinstance(self._note_offset, int):
            return self._note_offset
        total_eighth_notes: list[int] = []
        for n in range(20):
            tmp_eighth_note_grid = self.get_eighth_note_time_grid(n)
            tmp_synced_eighth_note_grid = self.map_onsets_to_eighth_notes(
                tmp_eighth_note_grid
            )
            total_eighth_notes.append(
                len(
                    np.intersect1d(
                        np.around(self.note_line, 8),
                        np.around(tmp_synced_eighth_note_grid, 8),
                    )
                )
            )
        note_offset = int(np.argmax(total_eighth_notes))
        logger.info('Note offset set to %d', note_offset)
        self._note_offset = note_offset
        return note_offset

    def get_eighth_note_time_grid(self, note_offset: int = 0) -> np.ndarray:
        '''Calculates the eighth note time grid.

        Args:
            note_offset (int): The offset in notes to start the grid from. Default is 0.

        Returns:
            np.ndarray: An array of time values for the eighth note grid.

        '''
        first_note = librosa.samples_to_time(
            self.predictions.peak_sample.iloc[note_offset], sr=self.sample_rate
        )
        return np.arange(first_note, self.duration, self.bpm.eighth_note)

    def map_onsets_to_eighth_notes(self, eigth_note_time_grid: np.ndarray):
        '''Map the eighth note time grid to the onsets.'''
        # match timing of the first note
        synced_eighth_note_grid = [eigth_note_time_grid[0]]
        diff_log = 0

        # First, map and sync 8th notes to the onset
        # Here we iterate over the eigth_note_time_grid starting from the second
        # element. Then we find the closest note in our onset array self.note_line.
        # If the difference between the note and the eigth note is larger than
        # the duration of a thirty-second note, we assume that the note is not
        # synced and we add the duration of an eighth note to the last synced note.
        # Otherwise, we adjust the diff_log to sync the note with the eigth note.
        for note in eigth_note_time_grid[1:]:
            pos = np.argmin(np.abs(self.note_line - (note + diff_log)))
            diff = self.note_line[pos] - (note + diff_log)

            if np.abs(diff) > self.bpm.thirty_second_note:
                synced_eighth_note_grid.append(
                    synced_eighth_note_grid[-1] + self.bpm.eighth_note
                )
            else:
                diff_log = diff_log + diff
                synced_eighth_note_grid.append(note + diff_log)
        if self.offset:
            [
                synced_eighth_note_grid.insert(
                    0, synced_eighth_note_grid[0] - self.bpm.eighth_note
                )
                for _ in range(self.beats_in_measure)
            ]
        return np.array(synced_eighth_note_grid)

    def master_sync(self, grid: Grid):
        '''A note quantization function.

        Maps 16th, 32th, 8th triplets or
        8th sixthlet note to each onset when applicable

        Args:
            grid (Grid): The grid object containing the synced eighth notes.

        '''
        # TODO: one day get round to refactoring this garbagio code
        # round the onsets and synced eighth note position (in the unit of seconds) to 8 decimal
        # places for convinience
        note_line = np.round(self.note_line, 8)
        eighth_notes = np.round(grid.eighth_notes, 8)

        # declare a few variables to store the result
        synced_16_div = []
        synced_32_div = []
        synced_8_3_div = []
        synced_8_6_div = []

        # iterate though all synced 8th notes
        for i in range(len(eighth_notes) - 1):
            res = self._get_best_division(grid, i, note_line)
            if res is None:
                continue
            key, sub_notes = res
            if key == '_16':
                synced_16_div.extend(sub_notes)
            elif key == '_32':
                synced_32_div.extend(sub_notes)
            elif key == '_8_3':
                synced_8_3_div.extend(sub_notes)
            else:
                synced_8_6_div.extend(sub_notes)

        # If there is any notes living in between 2 consecutive 8th notes, the first 8th note is
        # not an 8th note anymore. The for loop below will remove those notes from the eighth note
        # variable
        synced_8_div_clean = grid.eighth_notes.copy()
        for div in [synced_16_div, synced_32_div, synced_8_3_div, synced_8_6_div]:
            synced_8_div_clean = synced_8_div_clean[
                ~np.isin(np.around(synced_8_div_clean, 8), np.around(div, 8))
            ]
        return Grid(
            synced_8_div_clean,
            np.array(synced_16_div),
            np.array(synced_32_div),
            np.array(synced_8_3_div),
            np.array(synced_8_6_div),
        )

    @staticmethod
    def _get_best_division(
        grid: Grid, i: int, note_line: np.ndarray
    ) -> tuple[str, np.ndarray] | None:
        # retrive the current 8th note and the next 8th note (n and n+1)
        eighth_pair = grid.eighth_notes[i : i + 2]
        sub_notes = note_line[
            (note_line > eighth_pair[0]) & (note_line < eighth_pair[1])
        ]
        # Check whether there is any detected onset exist between 2 consecutive eighth notes
        if len(sub_notes) == 0:
            return None
        # if onsets are deteced between 2 consecuive eighth notes,
        # the algorithm will match each note (based on its position in the time domain) to
        # the closest note division (16th, 32th, eighth triplets or eighth sixthlet note)
        dist_dict = {'_16': [], '_32': [], '_8_3': [], '_8_6': []}
        sub_notes_dict = {
            '_16': np.round(
                np.linspace(grid.eighth_notes[i], grid.eighth_notes[i + 1], 3), 8
            )[:-1],
            '_32': np.round(
                np.linspace(grid.eighth_notes[i], grid.eighth_notes[i + 1], 5), 8
            )[:-1],
            '_8_3': np.round(
                np.linspace(grid.eighth_notes[i], grid.eighth_notes[i + 1], 4), 8
            )[:-1],
            '_8_6': np.round(
                np.linspace(grid.eighth_notes[i], grid.eighth_notes[i + 1], 7), 8
            )[:-1],
        }

        for sub_note in sub_notes:
            diff_16 = np.min(np.abs(grid.sixteenth_notes - sub_note))
            dist_dict['_16'].append(diff_16)
            _16closest_line = grid.sixteenth_notes[
                np.argmin(np.abs(grid.sixteenth_notes - sub_note))
            ]
            sub_notes_dict['_16'] = np.where(
                sub_notes_dict['_16'] == np.round(_16closest_line, 8),
                sub_note,
                sub_notes_dict['_16'],
            )

            diff_32 = np.min(np.abs(grid.thirty_second_notes - sub_note))
            dist_dict['_32'].append(diff_32)
            _32closest_line = grid.thirty_second_notes[
                np.argmin(np.abs(grid.thirty_second_notes - sub_note))
            ]
            sub_notes_dict['_32'] = np.where(
                sub_notes_dict['_32'] == np.round(_32closest_line, 8),
                sub_note,
                sub_notes_dict['_32'],
            )

            diff_8_triplet = np.min(np.abs(grid.eighth_note_triplets - sub_note))
            dist_dict['_8_3'].append(diff_8_triplet)
            _8_3closest_line = grid.eighth_note_triplets[
                np.argmin(np.abs(grid.eighth_note_triplets - sub_note))
            ]
            sub_notes_dict['_8_3'] = np.where(
                sub_notes_dict['_8_3'] == np.round(_8_3closest_line, 8),
                sub_note,
                sub_notes_dict['_8_3'],
            )

            diff_8_sixlet = np.min(np.abs(grid.eighth_note_sixlets - sub_note))
            dist_dict['_8_6'].append(diff_8_sixlet)
            _8_6closest_line = grid.eighth_note_sixlets[
                np.argmin(np.abs(grid.eighth_note_sixlets - sub_note))
            ]
            sub_notes_dict['_8_6'] = np.where(
                sub_notes_dict['_8_6'] == np.round(_8_6closest_line, 8),
                sub_note,
                sub_notes_dict['_8_6'],
            )
        avg_dist = {k: sum(v) / len(v) for k, v in dist_dict.items() if v}
        best_div = min(avg_dist, key=lambda k: avg_dist[k])
        return best_div, sub_notes_dict[best_div]

    def get_pitch_dict(self) -> dict[float, list[str]]:
        '''Reformats the prediction result.

        Formats the predictions into a dictionary where the keys are the time in seconds
        and the values are lists of pitches that are active at that time.
        '''
        pitch_mapping = self.predictions[
            ['peak_sample', 'SD', 'HH', 'KD', 'RC', 'TT', 'CC']
        ].set_index('peak_sample')
        pitches: dict[int, dict[str, float]] = pitch_mapping.to_dict(orient='index')  # type: ignore
        pitch_dict = {}
        for p in pitches:
            pitch_dict[round(librosa.samples_to_time(p, sr=self.sample_rate), 8)] = [
                d for d in pitches[p] if pitches[p][d] == 1
            ]
        return pitch_dict

    @staticmethod
    def build_measure(measure_iter, synced_grid: Grid):
        '''Builds a measure from the synced divisions.'''
        sixteenth_notes = np.around(synced_grid.sixteenth_notes, 8)
        thirty_second_notes = np.around(synced_grid.thirty_second_notes, 8)
        eighth_note_triplets = np.around(synced_grid.eighth_note_triplets, 8)
        eighth_note_sixlets = np.around(synced_grid.eighth_note_sixlets, 8)
        measure = []
        note_dur = []
        for notey in measure_iter:
            _div = False
            for div in [
                (sixteenth_notes, 2, 0.25),
                (thirty_second_notes, 4, 0.125),
                (eighth_note_triplets, 3, 1 / 6),
                (eighth_note_sixlets, 6, 1 / 12),
            ]:
                if notey in div[0]:
                    pos = np.where(div[0] == notey)
                    pos = pos[0][0]
                    measure.append(list(div[0][pos : pos + div[1]]))
                    note_dur.append([div[2]] * div[1])
                    _div = True
            if not _div:
                measure.append([notey])
                note_dur.append([0.5])

        measure = [item for sublist in measure for item in sublist]
        note_dur = [item for sublist in note_dur for item in sublist]
        return measure, note_dur

    def build_stream(
        self, grid: Grid, pitch_dict: dict[float, list[str]], synced_grid: Grid
    ):
        '''Builds the stream of time, pitch, and note duration.

        This function constructs a stream of time, pitch, and note duration based on the
        synced eighth note divisions. It organizes the data into measures, where each measure
        contains a fixed number of beats defined by the time signature.
        '''
        measure_log = 0
        stream_time_map = []
        stream_pitch = []
        stream_note = []
        eighth_notes = np.around(grid.eighth_notes, 8)
        for _ in range(len(eighth_notes) // self.beats_in_measure):
            measure_iter = list(
                eighth_notes[measure_log : measure_log + self.beats_in_measure]
            )
            measure, note_dur = self.build_measure(measure_iter, synced_grid)
            stream_time_map.append(measure)
            stream_note.append(note_dur)
            measure_log = measure_log + self.beats_in_measure

        remaining_8 = len(eighth_notes) % self.beats_in_measure
        measure, note_dur = self.build_measure(eighth_notes[-remaining_8:], synced_grid)
        measure.extend([-1] * (self.beats_in_measure - remaining_8))
        note_dur.extend([8] * (self.beats_in_measure - remaining_8))

        stream_time_map.append(measure)
        stream_note.append(note_dur)

        for measure in stream_time_map:
            pitch_set = []
            for notey in measure:
                if notey in pitch_dict:
                    if len(pitch_dict[notey]) == 0:
                        pitch_set.append(['rest'])
                    else:
                        pitch_set.append(pitch_dict[notey])
                else:
                    pitch_set.append(['rest'])
            stream_pitch.append(pitch_set)
        return stream_time_map, stream_pitch, stream_note

    def get_music21_data(self, stream_time_map, stream_pitch, stream_note):
        '''Converts the stream data into a format suitable for music21.'''
        music21_data = []
        for i in range(len(stream_time_map)):
            music21_data.append(
                list(zip(stream_note[i], stream_pitch[i], strict=False))
            )
        return music21_data

    def duration_set(self, pred_note, n) -> note.Note:
        '''Sets the duration of the note based on the predicted note.'''
        if pred_note[0] == 1 / 6:
            t = duration.Tuplet(3, 1, 'eighth')
            n.duration.type = 'eighth'
            n.duration.appendTuplet(deepcopy(t))
        elif pred_note[0] == 1 / 12:
            t = duration.Tuplet(6, 1, 'eighth')
            n.duration.type = 'eighth'
            n.duration.appendTuplet(deepcopy(t))
        else:
            n.duration = duration.Duration(pred_note[0])
        return n

    def sheet_construction(self, music21_data, song_title=None) -> stream.Stream:
        '''Constructs the sheet music using music21.'''
        label_pitch_map = {
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

        s = stream.Stream()
        s.insert(
            0,
            meter.TimeSignature(
                f'{int(self.beats_in_measure / 2)}/{self.time_sig.note_value}'
            ),
        )
        s.insert(0, metadata.Metadata())
        if song_title is None:
            s.metadata.title = 'Drum Sheet Music'
        else:
            s.metadata.title = song_title
        s.metadata.composer = 'Generated by The Annoteators'
        for _measure in music21_data:
            for pred_note in _measure:
                if pred_note[1][0] == 'rest':
                    n = note.Rest()
                    n = self.duration_set(pred_note, n)
                    n.stemDirection = 'up'
                    s.append(n)
                else:
                    if len(pred_note[1]) > 1:
                        notes_group = []
                        for i in range(len(pred_note[1])):
                            _n = note.Unpitched(label_pitch_map[pred_note[1][i]])
                            if pred_note[1][i] in ['HH_close', 'HH_open', 'RC', 'HH']:
                                _n.notehead = 'x'
                            notes_group.append(_n)
                        n = percussion.PercussionChord(notes_group)
                        n = self.duration_set(pred_note, n)
                        n.stemDirection = 'up'
                        s.append(n)
                    else:
                        n = note.Unpitched(label_pitch_map[pred_note[1][0]])
                        n = self.duration_set(pred_note, n)
                        if pred_note[1][0] in ['HH_close', 'HH_open', 'RC', 'HH']:
                            n.notehead = 'x'
                        n.stemDirection = 'up'
                        s.append(n)
        s = s.makeMeasures()
        return s

    def write_sheet(self, fpath: str | Path):
        '''Writes the sheet music to a PDF file.

        Args:
            fpath (str): The file path where the PDF will be saved.

        '''
        self.sheet.write(fmt='musicxml.pdf', fp=fpath)
