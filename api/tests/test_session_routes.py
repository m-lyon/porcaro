import numpy as np
import pandas as pd

from porcaro.api.database.models import ProcessingMetadataModel

# TODO(m-lyon): #3 Mock the relevant database and in memory service calls used in these
# tests so that they are unit tests rather than integration tests.


def test_create_session_endpoint(client_single_session):
    '''Test the create session API endpoint.'''
    files = {'file': ('test.wav', b'fake audio data', 'audio/wav')}
    response = client_single_session.post('/api/sessions/', files=files)
    data = response.json()
    assert response.status_code == 200
    assert 'id' in data
    assert data['filename'] == 'test.wav'


def test_get_session_endpoint(client_single_session, sample_session):
    '''Test the get session API endpoint.'''
    response = client_single_session.get(f'/api/sessions/{sample_session.id}')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == sample_session.id
    assert data['filename'] == sample_session.filename


def test_get_nonexistent_session_endpoint(client_single_session):
    '''Test getting a session that doesn't exist.'''
    response = client_single_session.get('/api/sessions/nonexistent-id')

    assert response.status_code == 404


def test_process_session_audio_endpoint(client_single_session, sample_session, mocker):
    '''Test the process session audio API endpoint (tests update_session).'''
    mock_track = np.array([1, 2, 3])  # Simple array with nbytes
    mock_df = pd.DataFrame()
    mock_metadata = ProcessingMetadataModel(
        processed=True,
        duration=10.0,
        song_sample_rate=44100.0,
        onset_algorithm='test_onset',
        prediction_algorithm='test_prediction',
        model_weights_path='test_weights.pt',
    )

    # Mock the transcription process
    mock_process_audio = mocker.patch(
        'porcaro.api.routers.sessions.process_audio_file',
        return_value=(
            mock_track,
            mock_df,
            120,
            mock_metadata,
        ),
    )

    response = client_single_session.post(
        f'/api/sessions/{sample_session.id}/process',
        json={
            'time_signature': {'numerator': 4, 'denominator': 4},
            'start_beat': 1.0,
            'offset': 0.0,
            'resolution': 16,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data['bpm'] == 120
    assert data['duration'] == 10.0
    mock_process_audio.assert_called_once()


def test_get_session_progress_endpoint(client_single_session, sample_session_expanded):
    '''Test the get session progress API endpoint.'''
    response = client_single_session.get(
        f'/api/sessions/{sample_session_expanded.id}/progress'
    )
    assert response.status_code == 200
    data = response.json()
    assert data['total_clips'] == 2
    assert data['labeled_clips'] == 1
    assert data['progress_percentage'] == 50.0
    assert data['remaining_clips'] == 1


def test_delete_session_endpoint(client_single_session, sample_session):
    '''Test the delete session API endpoint.'''
    # Delete the session
    response = client_single_session.delete(f'/api/sessions/{sample_session.id}')

    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['session_id'] == sample_session.id

    # Verify it's gone
    get_response = client_single_session.get(f'/api/sessions/{sample_session.id}')
    assert get_response.status_code == 404
