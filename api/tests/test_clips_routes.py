import numpy as np

from porcaro.api.database.models import ProcessingMetadata

# TODO(m-lyon): #3 Mock the relevant database and in memory service calls used in these
# tests so that they are unit tests rather than integration tests.


def test_get_clips_endpoint(client_single_session, sample_session_expanded):
    '''Test the get clips API endpoint when clips exist.'''
    client, _ = client_single_session
    response = client.get(f'/api/clips/{sample_session_expanded.id}/clips')

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data['clips'], list)
    assert len(data['clips']) == 2


def test_get_clips_not_processed_endpoint(client_single_session, sample_session):
    '''Test the get clips API endpoint when session audio not processed.'''
    client, _ = client_single_session
    response = client.get(f'/api/clips/{sample_session.id}/clips')

    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == 'Session audio has not been processed yet'


def test_get_clips_no_clips_endpoint(
    test_db_session, client_single_session, sample_session
):
    '''Test the get clips API endpoint when no clips exist.'''
    client, _ = client_single_session
    # Add processing metadata but no clips
    processing_metadata = ProcessingMetadata(
        id='test-id',
        processed=True,
        duration=10.0,
        song_sample_rate=44100.0,
        onset_algorithm='test_onset',
        prediction_algorithm='test_prediction',
        model_weights_path='test_weights.pt',
    )
    test_db_session.add(processing_metadata)
    test_db_session.commit()

    response = client.get(f'/api/clips/{sample_session.id}/clips')

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data['clips'], list)
    assert len(data['clips']) == 0


def test_get_clip_endpoint(client_single_session, sample_session_expanded):
    '''Test the get single clip API endpoint.'''
    client, _ = client_single_session
    clip_id = sample_session_expanded.clips[0].id
    response = client.get(f'/api/clips/{sample_session_expanded.id}/clips/{clip_id}')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == clip_id
    assert data['end_sample'] == 1000
    assert data['predicted_labels'] == ['KD']


def test_get_nonexistent_clip_endpoint(client_single_session, sample_session_expanded):
    '''Test the get single clip API endpoint.'''
    client, _ = client_single_session
    # Try to get a non-existent clip
    response = client.get(
        f'/api/clips/{sample_session_expanded.id}/clips/nonexistent-clip-id'
    )

    assert response.status_code == 404


def test_get_clip_audio_endpoint(
    client_single_session, sample_session_expanded, mocker
):
    '''Test the get clip audio API endpoint.'''
    client, (_, track_path) = client_single_session
    track_path.touch()
    mock_get_windowed_sample = mocker.patch(
        'porcaro.api.routers.clips.get_windowed_sample', return_value=b'test audio data'
    )
    mock_np_load = mocker.patch(
        'porcaro.api.services.memory_service.np.load', return_value=np.array([1, 2, 3])
    )
    mock_audio_clip_to_wav_bytes = mocker.patch(
        'porcaro.api.routers.clips.audio_clip_to_wav_bytes',
        return_value=b'test audio data',
    )

    clip_id = sample_session_expanded.clips[0].id
    response = client.get(
        f'/api/clips/{sample_session_expanded.id}/clips/{clip_id}/audio'
    )

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'audio/wav'
    assert response.content == b'test audio data'
    mock_np_load.assert_called_once()
    mock_get_windowed_sample.assert_called_once()
    mock_audio_clip_to_wav_bytes.assert_called_once()
