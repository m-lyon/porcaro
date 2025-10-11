from porcaro.api.database.models import DrumLabel

# TODO(m-lyon): #3 Mock the relevant database and in memory service calls used in these
# tests so that they are unit tests rather than integration tests.


def test_label_clip_endpoint(client_single_session, sample_session_expanded):
    '''Test the label clip API endpoint.'''
    clip_id = sample_session_expanded.clips[0].id

    # Label the clip
    label_data = {'labels': [DrumLabel.SNARE_DRUM.value]}
    response = client_single_session.post(
        f'/api/labels/{sample_session_expanded.id}/clips/{clip_id}/label',
        json=label_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['user_label'] == [DrumLabel.SNARE_DRUM.value]
    assert data['labeled_at'] is not None


def test_label_nonexistent_clip(client_single_session, sample_session_expanded):
    '''Test labeling a clip that doesn't exist.'''
    label_data = {'labels': [DrumLabel.KICK_DRUM.value]}

    response = client_single_session.post(
        f'/api/labels/{sample_session_expanded.id}/clips/nonexistent-clip-id/label',
        json=label_data,
    )

    assert response.status_code == 404


def test_remove_clip_label_endpoint(client_single_session, sample_session_expanded):
    '''Test the remove clip label API endpoint.'''
    clip_id = sample_session_expanded.clips[0].id

    # Remove the label
    response = client_single_session.delete(
        f'/api/labels/{sample_session_expanded.id}/clips/{clip_id}/label'
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['previous_labels'] == [DrumLabel.KICK_DRUM.value]


def test_remove_label_nonexistent_clip(client_single_session, sample_session_expanded):
    '''Test removing label from a clip that doesn't exist.'''
    response = client_single_session.delete(
        f'/api/labels/{sample_session_expanded.id}/clips/nonexistent-clip-id/label'
    )

    assert response.status_code == 404


def test_export_labeled_data_json_endpoint(
    client_single_session, sample_session_expanded
):
    '''Test the export labeled data API endpoint in json format.'''
    response = client_single_session.get(
        f'/api/labels/{sample_session_expanded.id}/export?fmt=json'
    )

    assert response.status_code == 200
    # Response should be a structured JSON response with CSV data
    assert response.headers['content-type'] == 'application/json'
    data = response.json()
    assert data['export_format'] == 'json'
    assert len(data['data']['clips']) == 1
    assert data['data']['clips'][0]['user_label'] == [DrumLabel.KICK_DRUM.value]
    assert data['data']['clips'][0]['predicted_labels'] == [DrumLabel.KICK_DRUM.value]
    assert data['data']['session_info']['total_clips'] == 2
    assert data['data']['session_info']['labeled_clips'] == 1
    assert data['data']['session_info']['time_signature'] == {
        'denominator': 4,
        'numerator': 4,
    }


def test_get_labeled_data_statistics_endpoint(client, multi_sample_expanded_sessions):
    '''Test the get labeled data statistics API endpoint.'''
    _ = multi_sample_expanded_sessions
    # Get statistics
    response = client.get('/api/labels/statistics')

    assert response.status_code == 200
    data = response.json()
    assert 'total_labeled_clips' in data
    assert 'clips_by_label' in data
    assert data['total_labeled_clips'] == 3
    assert DrumLabel.KICK_DRUM.value in data['clips_by_label']
    assert DrumLabel.SNARE_DRUM.value not in data['clips_by_label']
    assert data['clips_by_label'][DrumLabel.KICK_DRUM.value] == 3


def test_get_all_labeled_clips_endpoint(client, multi_sample_expanded_sessions):
    '''Test the get all labeled clips API endpoint.'''
    _ = multi_sample_expanded_sessions
    # Get all labeled clips
    response = client.get('/api/labels/all_labeled_clips')

    assert response.status_code == 200
    data = response.json()
    assert len(data['clips']) == 3
    assert data['clips'][0]['user_label'] == [DrumLabel.KICK_DRUM.value]
