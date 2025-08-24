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
- **Data Export**: Export labelled data in JSON or CSV format
- **Progress Tracking**: Monitor labelling progress across sessions

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

##### labelling

- `POST /api/labels/{session_id}/clips/{clip_id}/label` - Submit clip label
- `DELETE /api/labels/{session_id}/clips/{clip_id}/label` - Remove clip label
- `GET /api/labels/{session_id}/export` - Export labelled data

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

# Label a clip
clip_id = clips[0]["clip_id"] 
label_data = {"labels": ["KD"]}
requests.post(f"http://localhost:8000/api/labels/{session_id}/clips/{clip_id}/label",
              json=label_data)

# Export labelled data
response = requests.get(f"http://localhost:8000/api/labels/{session_id}/export")
labelled_data = response.json()
```

### Configuration

#### Processing Parameters

- **time_signature**: Music time signature (e.g., 4/4)
- **start_beat**: Starting beat offset (default: 1)
- **offset**: Start time offset in seconds (default: 0.0)  
- **duration**: Duration to process in seconds (optional)
- **resolution**: Window size resolution, 4/8/16/32 (default: 16)

#### Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- OGG (.ogg)
- M4A (.m4a)

### Architecture

The backend follows a clean architecture with:

- **FastAPI Router**: HTTP endpoint handling
- **Service Layer**: Business logic and audio processing
- **Models**: Pydantic data models for validation
- **Session Store**: In-memory storage for session management

### Development

The API integrates seamlessly with the existing porcaro codebase:

- Uses `porcaro.transcription` module for audio processing
- Leverages existing ML models for drum classification  
- Maintains compatibility with current data structures

For production deployment, consider:

- Database storage instead of in-memory sessions
- Authentication and authorization
- Rate limiting and request validation
- File storage optimization

## To-Do

- Check `async def create_session(file: UploadFile = File(...)):` `=File` is needed.
