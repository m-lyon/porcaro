/**
 * API service for the data labeling backend
 */
// TODO: replace this constant with environment variables
const API_BASE_URL = 'http://localhost:8000/api';

export function getClipAudioUrl(
    sessionId: string,
    clipId: string,
    playbackWindow: number = 1.0
): string {
    return `${API_BASE_URL}/clips/${sessionId}/clips/${clipId}/audio?playback_window=${playbackWindow}`;
}
