# porcaro

Automatic Drum Transcription

## Installation

1. Install dependencies using `uv`:

```bash
cd /Users/user/Dev/git/porcaro/api
uv sync
```

## Data Labelling API

A FastAPI-based backend for the drum transcription data labelling interface. This API processes audio files through the porcaro transcription pipeline and serves audio clips with ML predictions for manual labelling.

### Features

- **Session Management**: Create and manage labelling sessions for audio files
- **Audio Processing**: Process audio through the existing porcaro transcription pipeline
- **Clip Serving**: Serve individual audio clips with metadata and predictions
- **Labelling Interface**: Submit and manage user labels for audio clips
- **Persistent Storage**: Automatically save labeled clips to disk for training data collection
- **Data Export**: Export labelled data in JSON or CSV format
- **Progress Tracking**: Monitor labelling progress across sessions
- **Dataset Management**: Statistics and bulk operations for labeled datasets

### Supported Drum Labels

The system recognizes the following drum types:

- **KD** - Kick Drum
- **SD** - Snare Drum  
- **HH** - Hi-Hat
- **RC** - Ride Cymbal
- **TT** - Tom-Tom
- **CC** - Crash Cymbal

1. The API server dependencies are now included in `pyproject.toml`

### Usage

#### Starting the Server

```bash
python start_server.py
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

#### Basic Workflow

1. **Create Session**: Upload an audio file to create a new labelling session
2. **Process Audio**: Configure processing parameters and run transcription
3. **Label Clips**: Get clips and submit labels through the API
4. **Export Data**: Download labelled data for training

#### API Endpoints

##### Session Management

- `POST /api/sessions/` - Create new session with audio file upload
- `GET /api/sessions/{session_id}` - Get session information
- `POST /api/sessions/{session_id}/process` - Process audio through pipeline
- `GET /api/sessions/{session_id}/progress` - Get labelling progress
- `DELETE /api/sessions/{session_id}` - Delete session and clean-up

##### Clip Management

- `GET /api/clips/{session_id}/clips` - Get paginated list of clips
- `GET /api/clips/{session_id}/clips/{clip_id}` - Get specific clip metadata
- `GET /api/clips/{session_id}/clips/{clip_id}/audio` - Stream clip audio as WAV

##### Labelling

- `POST /api/labels/{session_id}/clips/{clip_id}/label` - Submit clip label (automatically saves to disk)
- `DELETE /api/labels/{session_id}/clips/{clip_id}/label` - Remove clip label (removes from disk)
- `GET /api/labels/{session_id}/export` - Export labelled data (includes audio file paths)

##### Dataset Management

- `GET /api/statistics` - Get statistics about all labeled data
- `GET /api/all_labeled_clips` - Get all labeled clips from all sessions
- `DELETE /api/{session_id}/labeled_data` - Clean up labeled data for a session

#### Example Usage

```python
import requests

# Create session
files = {"file": open("drum_track.wav", "rb")}
response = requests.post("http://localhost:8000/api/sessions/", files=files)
session = response.json()
session_id = session["session_id"]

# Process audio
process_config = {
    "time_signature": {"numerator": 4, "denominator": 4},
    "start_beat": 1,
    "offset": 0.0,
    "resolution": 16
}
requests.post(f"http://localhost:8000/api/sessions/{session_id}/process", 
              json=process_config)

# Get clips to label
response = requests.get(f"http://localhost:8000/api/clips/{session_id}/clips")
clips = response.json()["clips"]

# Label a clip (automatically saved to disk)
clip_id = clips[0]["clip_id"] 
label_data = {"labels": ["KD"]}
requests.post(f"http://localhost:8000/api/labels/{session_id}/clips/{clip_id}/label",
              json=label_data)

# Export labelled data (includes audio file paths)
response = requests.get(f"http://localhost:8000/api/labels/{session_id}/export")
labelled_data = response.json()

# Export data includes file paths to model input audio files
for clip in labelled_data['clips']:
    print(f"Audio file: {clip['model_input_audio_file_path']}")

# Get dataset statistics
response = requests.get("http://localhost:8000/api/statistics")
stats = response.json()
print(f"Total labeled clips: {stats['total_labeled_clips']}")
print(f"Clips by label: {stats['clips_by_label']}")
```

### Configuration

#### Processing Parameters

- **time_signature**: Music time signature (e.g., 4/4)
- **start_beat**: Starting beat offset (default: 1)
- **offset**: Start time offset in seconds (default: 0.0)  
- **duration**: Duration to process in seconds (optional)
- **resolution**: Window size resolution, 4/8/16/32 (default: 16)

#### Storage Configuration

- **Labeled Data Directory**: By default stored in `labeled_data/` (configurable)****
- **Automatic Persistence**: All labeled clips are automatically saved to disk
- **File Structure**: Each labeled clip gets its own directory with audio and metadata

#### Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- OGG (.ogg)
- M4A (.m4a)

### Labeled Data Persistence

The system automatically saves labeled clips to disk for persistent training data collection:

#### Storage Structure

```
labeled_data/
├── {session_id_1}/
│   ├── {clip_id_1}/
│   │   ├── metadata.json
│   │   └── {clip_id_1}.wav
│   ├── {clip_id_2}/
│   │   ├── metadata.json
│   │   └── {clip_id_2}.wav
│   └── ...
├── {session_id_2}/
│   └── ...
```

#### Benefits

- **Immediate data preservation**: Labels saved to disk immediately
- **Training data collection**: Audio files and metadata ready for ML training
- **Data recovery**: Labels persist across server restarts
- **Dataset management**: Easy export and bulk operations

#### Machine Learning Integration

The persistent storage format is designed for easy ML training integration:

```python
import json
import numpy as np
from pathlib import Path

def load_training_data(labeled_data_dir):
    """Load all labeled clips for training."""
    training_data = []
    
    for session_dir in Path(labeled_data_dir).iterdir():
        for clip_dir in session_dir.iterdir():
            if not clip_dir.is_dir():
                continue
                
            metadata_file = clip_dir / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Load audio
                audio_file = clip_dir / metadata['files']['audio_file']
                audio = np.read(audio_file)
                
                # Extract labels
                labels = metadata['clip_info']['user_label']
                
                training_data.append({
                    'audio': audio,
                    'labels': labels,
                    'metadata': metadata
                })
    
    return training_data
```

### Architecture

The backend follows a clean architecture with:

- **FastAPI Router**: HTTP endpoint handling
- **Service Layer**: Business logic and audio processing
- **LabeledDataService**: Persistent storage operations
- **Models**: Pydantic data models for validation
- **Session Store**: In-memory storage for session management

### Development

The API integrates seamlessly with the existing porcaro codebase:

- Uses `porcaro.transcription` module for audio processing
- Leverages existing ML models for drum classification  
- Maintains compatibility with current data structures
- Automatic labeled data persistence for training dataset collection

For production deployment, consider:

- Database storage instead of in-memory sessions
- Authentication and authorization
- Rate limiting and request validation
- File storage optimization
- Backup strategies for labeled data

## To-Do

- Check `async def create_session(file: UploadFile = File(...)):` `=File` is needed.
