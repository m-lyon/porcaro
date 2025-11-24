# TODO(m-lyon): #3 Mock the relevant database and in memory service calls used in these
# tests so that they are unit tests rather than integration tests.


def test_create_session_endpoint(client_single_session):
    '''Test the create session API endpoint.'''
    client, _ = client_single_session
    files = {'file': ('test.wav', b'fake audio data', 'audio/wav')}
    response = client.post('/api/sessions/', files=files)
    data = response.json()
    assert response.status_code == 200
    assert 'id' in data
    assert data['filename'] == 'test.wav'


def test_get_session_endpoint(client_single_session, sample_session):
    '''Test the get session API endpoint.'''
    client, _ = client_single_session
    response = client.get(f'/api/sessions/{sample_session.id}')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == sample_session.id
    assert data['filename'] == sample_session.filename


def test_get_session_endpoint_post_process(
    client_single_session, sample_session_expanded
):
    '''Test the get session API endpoint after processing.'''
    client, _ = client_single_session
    response = client.get(f'/api/sessions/{sample_session_expanded.id}')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == sample_session_expanded.id
    assert data['filename'] == sample_session_expanded.filename
    assert data['bpm'] == sample_session_expanded.bpm
    assert data['duration'] == sample_session_expanded.duration
    assert data['time_signature']['numerator'] == 4
    assert data['time_signature']['denominator'] == 4


def test_get_nonexistent_session_endpoint(client_single_session):
    '''Test getting a session that doesn't exist.'''
    client, _ = client_single_session
    response = client.get('/api/sessions/nonexistent-id')

    assert response.status_code == 404


def test_get_session_progress_endpoint(client_single_session, sample_session_expanded):
    '''Test the get session progress API endpoint.'''
    client, _ = client_single_session
    response = client.get(f'/api/sessions/{sample_session_expanded.id}/progress')
    assert response.status_code == 200
    data = response.json()
    assert data['total_clips'] == 2
    assert data['labeled_clips'] == 1
    assert data['progress_percentage'] == 50.0
    assert data['remaining_clips'] == 1


def test_delete_session_endpoint(client_single_session, sample_session):
    '''Test the delete session API endpoint.'''
    client, _ = client_single_session
    # Delete the session
    response = client.delete(f'/api/sessions/{sample_session.id}')

    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['session_id'] == sample_session.id

    # Verify it's gone
    get_response = client.get(f'/api/sessions/{sample_session.id}')
    assert get_response.status_code == 404
