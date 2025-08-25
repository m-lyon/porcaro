# Instructions

I'm building a web app that will transcribe songs into drum scores. As part of this web app I need to train a machine learning model, and therefore I need to collect data to train this model. I want you to build a web interface that will streamline the process of labelling data. The web interface should be built in the client directory, and should be built using modern typescript, React, Vite, and shadcn for styling. The backend should be built in Python within the api directory.

## Backend

This web interface will serve the user a series of sound clips, and the user will have the option to select which label the sound corresponds to. In the backend you should use the code within api/transcription.py as a starting point, it has the following functionality:

load_song_data: Loads the song data into memory
get_librosa_onsets: Calculates where the onset of sounds within the song are
run_prediction_on_track: Formats the data and produces a dataframe with predictions of the sound clips. It is this dataframe that should be used to serve the data to the user for labelling.

An example of how to run these functions is given with api/transcription.py in the transcribe_drum_audio function. The dataframe has the following columns:

- audio_clip: a numpy array containing the song clip data
- sample_start: the start time of the clip in samples
- sample_end: the end time of the clip in samples
- sample_rate: the sample rate of the audio
- peak_sample: the time (in samples) where the peak (i.e. the start) of the sound clip is. This will be in between sample_start and sample_end as there is padding applied either side.
- peak_time: the time (in seconds) where the peak of the sound clip is.
- hits: this is a list of the detected note types predicted by the model.

I want you to use this document to create a plan to write the backend that will serve examples of song clips for the user to label.

## Frontend

The backend is functional so now I want you to build the frontend. Specifically I want you to build a frontend interface for the data labelling API. This interface should allow the user to upload music files and label music samples. You can look at the README within the api directory for more information, and look at the code within the api/porcaro/api directory for the implementation.