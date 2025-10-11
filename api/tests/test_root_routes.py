def test_root_endpoint(client):
    '''Test the root API endpoint.'''
    response = client.get('/')

    assert response.status_code == 200
    data = response.json()
    assert data['message'] == 'Porcaro Data Labeling API'
    assert data['version'] == '0.1.0'


def test_health_check_endpoint(client):
    '''Test the health check API endpoint.'''
    response = client.get('/health')

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
