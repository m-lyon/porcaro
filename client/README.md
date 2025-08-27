# Porcaro Data Labeling Frontend

A modern React-based frontend for the Porcaro drum transcription data labeling system. This interface provides an intuitive way to label audio clips for training machine learning models.

## Features

### 🎵 Audio Management

- **File Upload**: Drag-and-drop support for various audio formats (WAV, MP3, FLAC, OGG, M4A)
- **Session Management**: Create, manage, and track multiple labeling sessions
- **Audio Processing**: Configure time signature, BPM detection, and processing parameters

### 🏷️ Intelligent Labeling Interface

- **Real-time Audio Playback**: Built-in audio player with waveform visualization
- **ML Predictions**: Display machine learning predictions alongside manual labels
- **Keyboard Shortcuts**: Speed up labeling with intuitive keyboard controls
- **Batch Operations**: Filter and process clips efficiently

### 📊 Progress Tracking

- **Session Progress**: Visual progress bars and statistics
- **Label Analytics**: Track labeling completion across sessions
- **Export Functions**: Download labeled data for model training

### 🎹 Keyboard Shortcuts

The interface includes comprehensive keyboard shortcuts for efficient labeling:

- **Space**: Play/Pause audio
- **← →**: Navigate between clips
- **Enter**: Save current labels
- **Escape**: Clear all labels
- **1-6**: Toggle drum labels (Kick, Snare, Hi-Hat, Ride, Tom, Crash)

## Technology Stack

- **Frontend Framework**: React 19 with TypeScript
- **Build Tool**: Vite for fast development and building
- **Styling**: Tailwind CSS v4 with shadcn/ui components
- **Routing**: React Router v7
- **State Management**: React hooks with local state
- **Audio**: Web Audio API with HTML5 audio elements
- **HTTP Client**: Fetch API with custom error handling

## Development

### Prerequisites

- Node.js 18+ and npm
- The Porcaro API backend running on `http://localhost:8000`

### Getting Started

1. **Install Dependencies**

   ```bash
   npm install
   ```

2. **Start Development Server**

   ```bash
   npm run dev
   ```

3. **Build for Production**

   ```bash
   npm run build
   ```

## Supported Drum Labels

The system recognizes six primary drum types:

- **KD** - Kick Drum (Red)
- **SD** - Snare Drum (Blue)  
- **HH** - Hi-Hat (Green)
- **RC** - Ride Cymbal (Yellow)
- **TT** - Tom-Tom (Purple)
- **CC** - Crash Cymbal (Orange)+
