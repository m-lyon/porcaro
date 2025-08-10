'''Module for handling song metadata.'''

from .bpm import BPM
from .time_signature import TimeSignature


class SongData:
    '''Class to represent song metadata.'''

    def __init__(
        self,
        bpm: BPM | None = None,
        time_signature: TimeSignature | None = None,
        duration: float | None = None,
        sample_rate: int | float | None = None,
        start_beat: float | None = None,
    ):
        '''Initialize the SongData class.

        Args:
            bpm (float | None): Beats per minute of the song.
            time_signature (TimeSignature | None): Time signature of the song.
            duration (float | None): Duration of the song in seconds.
            sample_rate (int | float | None): Sample rate of the song.
            start_beat (float | None): Start beat of the song, relative to the time
                signature. e.g. if the time signature is 4/4, then 1 is the first
                note, 1.5 is the second eighth note, etc.

        '''
        self._bpm = bpm
        self._time_signature = time_signature
        self._duration = duration
        self._sample_rate = sample_rate
        self._start_beat = start_beat

    @property
    def bpm(self) -> BPM:
        '''Get the beats per minute of the song.'''
        if self._bpm is None:
            raise ValueError('BPM is not set')
        return self._bpm

    @bpm.setter
    def bpm(self, value: BPM):
        '''Set the beats per minute of the song.'''
        if not isinstance(value, BPM):
            raise TypeError('BPM must be an instance of BPM')
        self._bpm = value

    @property
    def time_signature(self) -> TimeSignature:
        '''Get the time signature of the song.'''
        if self._time_signature is None:
            raise ValueError('Time signature is not set')
        return self._time_signature

    @time_signature.setter
    def time_signature(self, value: TimeSignature):
        '''Set the time signature of the song.'''
        if not isinstance(value, TimeSignature):
            raise TypeError('Time signature must be an instance of TimeSignature')
        self._time_signature = value

    @property
    def duration(self) -> float:
        '''Get the duration of the song in seconds.'''
        if self._duration is None:
            raise ValueError('Duration is not set')
        return self._duration

    @duration.setter
    def duration(self, value: float):
        '''Set the duration of the song in seconds.'''
        if not isinstance(value, int | float):
            raise TypeError('Duration must be a number')
        self._duration = value

    @property
    def sample_rate(self) -> int | float:
        '''Get the sample rate of the song.'''
        if self._sample_rate is None:
            raise ValueError('Sample rate is not set')
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value: int | float):
        '''Set the sample rate of the song.'''
        if not isinstance(value, int | float):
            raise TypeError('Sample rate must be a number')
        self._sample_rate = value

    @property
    def start_beat(self) -> float:
        '''Get the start beat of the song.'''
        if self._start_beat is None:
            raise ValueError('Start beat is not set')
        return self._start_beat

    @start_beat.setter
    def start_beat(self, value: float):
        '''Set the start beat of the song.'''
        if not isinstance(value, int | float):
            raise TypeError('Start beat must be a number')
        self._start_beat = value
