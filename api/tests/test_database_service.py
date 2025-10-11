'''Fixed tests for database session service functionality.'''

from datetime import UTC
from datetime import datetime

from porcaro.api.database.models import AudioClip
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import TimeSignatureModel


def test_create_session(test_db_service):
    '''Test creating a new session.'''
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    assert session.id is not None
    assert session.filename == filename
    assert isinstance(session.created_at, datetime)


def test_get_session(test_db_service):
    '''Test retrieving a session by ID.'''
    filename = 'test_audio.wav'
    created_session = test_db_service.create_session(filename)

    retrieved_session = test_db_service.get_session(created_session.id)

    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.filename == filename


def test_get_nonexistent_session(test_db_service):
    '''Test retrieving a session that doesn't exist.'''
    session = test_db_service.get_session('nonexistent-id')
    assert session is None


def test_update_session(test_db_service):
    '''Test updating session data.'''
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Update with time signature
    time_sig = TimeSignatureModel(numerator=4, denominator=4)
    updates = {
        'time_signature': time_sig,
        'bpm': 120.0,
    }

    updated_session = test_db_service.update_session(session.id, updates)

    assert updated_session is not None
    assert updated_session.bpm == 120.0
    assert updated_session.time_signature_id is not None

    # Verify time signature was created by getting the session fresh from DB
    fresh_session = test_db_service.get_session(session.id)
    assert fresh_session.time_signature_id is not None


def test_delete_session(test_db_service):
    '''Test deleting a session.'''
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Delete the session
    success = test_db_service.delete_session(session.id)
    assert success is True

    # Verify it's gone
    retrieved_session = test_db_service.get_session(session.id)
    assert retrieved_session is None


def test_delete_nonexistent_session(test_db_service):
    '''Test deleting a session that doesn't exist.'''
    success = test_db_service.delete_session('nonexistent-id')
    assert success is False


def test_save_and_get_clips(test_db_service, make_clips):
    '''Test saving and retrieving clips.'''
    # Create a session first
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Create test clips
    clips = make_clips(session.id)

    # Save clips
    test_db_service.save_clips(session.id, clips)

    # Retrieve clips
    retrieved_clips, total_count = test_db_service.get_clips(session.id)

    assert len(retrieved_clips) == 2
    assert total_count == 2
    assert retrieved_clips[0].predicted_labels == [DrumLabel.KICK_DRUM]
    assert retrieved_clips[1].predicted_labels == [DrumLabel.SNARE_DRUM]


def test_update_clip_label(test_db_service, make_clips):
    '''Test updating clip label.'''
    # Create session and clip
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    clips = make_clips(session.id)

    # Get the clip ID before saving
    clip_id = clips[0].id
    test_db_service.save_clips(session.id, clips)

    # Update label
    labels = [DrumLabel.SNARE_DRUM]
    updated_clip = test_db_service.update_clip_label(session.id, clip_id, labels)

    assert updated_clip is not None
    assert updated_clip.user_label == labels
    assert updated_clip.labeled_at is not None


def test_remove_clip_label(test_db_service, make_clips):
    '''Test removing clip label.'''
    # Create session and clip
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    clips = make_clips(session.id)
    clip = clips[0]

    # Get the clip ID before saving
    clip_id = clip.id
    test_db_service.save_clips(session.id, clips)

    updated_clip = test_db_service.remove_clip_label(session.id, clip_id)

    assert updated_clip is not None
    assert updated_clip.user_label is None
    assert updated_clip.labeled_at is None


def test_get_labeled_clips(test_db_service, make_clips):
    '''Test getting labeled clips.'''
    # Create session
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Create clips with different labeling states
    clips = make_clips(session.id)

    test_db_service.save_clips(session.id, clips)
    # Get only labeled clips
    labeled_clips = test_db_service.get_labeled_clips(session.id)

    assert len(labeled_clips) == 1
    assert labeled_clips[0].user_label == [DrumLabel.KICK_DRUM]


def test_count_total_clips(test_db_service, make_clips):
    '''Test counting total clips in a session.'''
    # Create session
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Create multiple clips
    clips = make_clips(session.id)

    test_db_service.save_clips(session.id, clips)

    # Count total clips
    count = test_db_service.count_total_clips(session.id)

    assert count == 2


def test_count_labeled_clips(test_db_service, make_clips):
    '''Test counting labeled clips.'''
    # Create session
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Create clips with different labeling states
    clips = make_clips(session.id)

    test_db_service.save_clips(session.id, clips)

    # Count labeled clips
    count = test_db_service.count_labeled_clips(session.id)

    assert count == 1


def test_get_all_labeled_clips(test_db_service):
    '''Test getting all labeled clips across sessions.'''
    # Create multiple sessions
    session1 = test_db_service.create_session('test1.wav')
    session2 = test_db_service.create_session('test2.wav')

    # Create labeled clips in both sessions
    clip1 = AudioClip(
        start_sample=0,
        start_time=0.0,
        end_sample=1000,
        end_time=1.0,
        sample_rate=44100,
        peak_sample=500,
        peak_time=0.5,
        predicted_labels=[DrumLabel.KICK_DRUM],
        user_label=[DrumLabel.KICK_DRUM],
        labeled_at=datetime.now(UTC),
        session_id=session1.id,
    )

    clip2 = AudioClip(
        start_sample=0,
        start_time=0.0,
        end_sample=1000,
        end_time=1.0,
        sample_rate=44100,
        peak_sample=500,
        peak_time=0.5,
        predicted_labels=[DrumLabel.SNARE_DRUM],
        user_label=[DrumLabel.SNARE_DRUM],
        labeled_at=datetime.now(UTC),
        session_id=session2.id,
    )

    test_db_service.save_clips(session1.id, [clip1])
    test_db_service.save_clips(session2.id, [clip2])

    # Get all labeled clips
    all_labeled_clips = test_db_service.get_all_labeled_clips()

    assert len(all_labeled_clips) == 2
    user_labels = [clip.user_label[0] for clip in all_labeled_clips]
    assert DrumLabel.KICK_DRUM in user_labels
    assert DrumLabel.SNARE_DRUM in user_labels


def test_save_clips_from_dataframe(test_db_service, mocker, tmp_path):
    '''Test saving clips from pandas DataFrame.'''
    import numpy as np
    import pandas as pd

    session = test_db_service.create_session('test_audio.wav')

    # Create test DataFrame with clips data
    rng = np.random.default_rng(42)
    clips_data = {
        'start_sample': [100, 300, 500],
        'start_time': [0.1, 0.3, 0.5],
        'end_sample': [200, 400, 600],
        'end_time': [0.2, 0.4, 0.6],
        'sampling_rate': [44100, 44100, 44100],
        'peak_sample': [150, 350, 550],
        'peak_time': [0.15, 0.35, 0.55],
        'hits': [['KD'], ['SD'], ['HH']],
        'audio_clip': [
            rng.random(100),
            rng.random(100),
            rng.random(100),
        ],
    }
    clips_df = pd.DataFrame(clips_data)
    mocker.patch('numpy.save')
    mocker.patch(
        'porcaro.api.services.database_service.get_clip_filepath',
        side_effect=[tmp_path / f'clip_{i}.npy' for i in range(3)],
    )

    count = test_db_service.save_clips_from_dataframe(session.id, clips_df)

    assert count == 3

    # Verify clips were saved to database
    clips, total = test_db_service.get_clips(session.id)
    assert total == 3
    assert len(clips) == 3

    # Check that predicted labels were mapped correctly
    expected_labels = [DrumLabel.KICK_DRUM, DrumLabel.SNARE_DRUM, DrumLabel.HI_HAT]
    actual_labels = [clip.predicted_labels[0] for clip in clips]
    assert set(actual_labels) == set(expected_labels)


def test_get_clip(test_db_service, make_clips):
    '''Test getting a specific clip by ID.'''
    session = test_db_service.create_session('test_audio.wav')

    # Create and save a clip
    clips = make_clips(session.id)

    test_db_service.save_clips(session.id, clips)
    # Get the clip ID after saving
    saved_clips, _ = test_db_service.get_clips(session.id)
    clip_id = saved_clips[1].id

    # Test getting existing clip
    retrieved_clip = test_db_service.get_clip(session.id, clip_id)

    assert retrieved_clip is not None
    assert retrieved_clip.id == clip_id
    assert retrieved_clip.start_sample == 1000
    assert retrieved_clip.predicted_labels == [DrumLabel.SNARE_DRUM]

    # Test getting non-existent clip
    non_existent_clip = test_db_service.get_clip(session.id, 'non-existent-id')
    assert non_existent_clip is None

    # Test getting clip from wrong session
    other_session = test_db_service.create_session('other_audio.wav')
    wrong_session_clip = test_db_service.get_clip(other_session.id, clip_id)
    assert wrong_session_clip is None


def test_delete_clip(test_db_service, tmp_path):
    '''Test deleting a specific clip.'''
    session = test_db_service.create_session('test_audio.wav')

    audio_clip_path = tmp_path / 'clip.npy'
    audio_clip_path.touch()
    assert audio_clip_path.exists()

    # Create and save a clip
    clip = AudioClip(
        start_sample=100,
        start_time=0.1,
        end_sample=200,
        end_time=0.2,
        sample_rate=44100,
        peak_sample=150,
        peak_time=0.15,
        predicted_labels=[DrumLabel.KICK_DRUM],
        session_id=session.id,
        audio_file_path=str(audio_clip_path),
    )

    test_db_service.save_clips(session.id, [clip])

    # Get the saved clip ID
    saved_clips, _ = test_db_service.get_clips(session.id)
    clip_id = saved_clips[0].id

    # Verify clip exists
    _, total = test_db_service.get_clips(session.id)
    assert total == 1

    # Delete the clip
    result = test_db_service.delete_clip(session.id, clip_id)

    assert result is True

    # Verify clip was deleted from database
    _, total = test_db_service.get_clips(session.id)
    assert total == 0

    # Verify clip file was deleted
    assert not audio_clip_path.exists()

    # Test deleting non-existent clip
    result = test_db_service.delete_clip(session.id, 'non-existent-id')
    assert result is False


def test_get_clips_pagination(test_db_service):
    '''Test get_clips with pagination.'''
    session = test_db_service.create_session('test_audio.wav')

    # Create multiple clips
    clips = []
    for i in range(25):  # More than default page size
        clip = AudioClip(
            start_sample=100 * i,
            start_time=0.1 * i,
            end_sample=100 * i + 100,
            end_time=0.1 * i + 0.1,
            sample_rate=44100,
            peak_sample=100 * i + 50,
            peak_time=0.1 * i + 0.05,
            predicted_labels=[DrumLabel.KICK_DRUM],
            session_id=session.id,
        )
        clips.append(clip)

    test_db_service.save_clips(session.id, clips)

    # Test default pagination (page 1, 20 items)
    page1_clips, total = test_db_service.get_clips(session.id)
    assert total == 25
    assert len(page1_clips) == 20

    # Test second page
    page2_clips, total = test_db_service.get_clips(session.id, page=2, page_size=20)
    assert total == 25
    assert len(page2_clips) == 5

    # Test custom page size
    custom_clips, total = test_db_service.get_clips(session.id, page=1, page_size=10)
    assert total == 25
    assert len(custom_clips) == 10


def test_edge_cases(test_db_service):
    '''Test edge cases and error conditions.'''
    session = test_db_service.create_session('test_audio.wav')

    # Test update_session with non-existent session
    result = test_db_service.update_session('non-existent-id', {'bpm': 120})
    assert result is None

    # Test get_clips with non-existent session (should return empty)
    clips, total = test_db_service.get_clips('non-existent-session')
    assert clips == []
    assert total == 0

    # Test save_clips with empty dictionary
    count = test_db_service.save_clips(session.id, {})
    assert count == 0

    # Test get_labeled_clips with session that has no clips
    labeled_clips = test_db_service.get_labeled_clips(session.id)
    assert labeled_clips == []
