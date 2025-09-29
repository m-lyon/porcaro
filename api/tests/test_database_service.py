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
    assert session.total_clips == 0
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
        'total_clips': 10,
    }

    updated_session = test_db_service.update_session(session.id, updates)

    assert updated_session is not None
    assert updated_session.bpm == 120.0
    assert updated_session.total_clips == 10
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


def test_save_and_get_clips(test_db_service):
    '''Test saving and retrieving clips.'''
    # Create a session first
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Create test clips
    clips = {
        'clip_0': AudioClip(
            start_sample=0,
            start_time=0.0,
            end_sample=1000,
            end_time=1.0,
            sample_rate=44100,
            peak_sample=500,
            peak_time=0.5,
            predicted_labels=[DrumLabel.KICK_DRUM],
            session_id=session.id,
        ),
        'clip_1': AudioClip(
            start_sample=1000,
            start_time=1.0,
            end_sample=2000,
            end_time=2.0,
            sample_rate=44100,
            peak_sample=1500,
            peak_time=1.5,
            predicted_labels=[DrumLabel.SNARE_DRUM],
            session_id=session.id,
        ),
    }

    # Save clips
    test_db_service.save_clips(session.id, clips)

    # Retrieve clips
    retrieved_clips, total_count = test_db_service.get_clips(session.id)

    assert len(retrieved_clips) == 2
    assert total_count == 2
    assert retrieved_clips[0].predicted_labels == [DrumLabel.KICK_DRUM]
    assert retrieved_clips[1].predicted_labels == [DrumLabel.SNARE_DRUM]


def test_update_clip_label(test_db_service):
    '''Test updating clip label.'''
    # Create session and clip
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    clip = AudioClip(
        start_sample=0,
        start_time=0.0,
        end_sample=1000,
        end_time=1.0,
        sample_rate=44100,
        peak_sample=500,
        peak_time=0.5,
        predicted_labels=[DrumLabel.KICK_DRUM],
        session_id=session.id,
    )

    # Get the clip ID before saving
    clip_id = clip.id
    test_db_service.save_clips(session.id, {clip_id: clip})

    # Update label
    labels = [DrumLabel.SNARE_DRUM]
    updated_clip = test_db_service.update_clip_label(session.id, clip_id, labels)

    assert updated_clip is not None
    assert updated_clip.user_label == labels
    assert updated_clip.labeled_at is not None


def test_remove_clip_label(test_db_service):
    '''Test removing clip label.'''
    # Create session and clip
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    clip = AudioClip(
        start_sample=0,
        start_time=0.0,
        end_sample=1000,
        end_time=1.0,
        sample_rate=44100,
        peak_sample=500,
        peak_time=0.5,
        predicted_labels=[DrumLabel.KICK_DRUM],
        user_label=[DrumLabel.SNARE_DRUM],
        labeled_at=datetime.now(UTC),
        session_id=session.id,
    )

    # Get the clip ID before saving
    clip_id = clip.id
    test_db_service.save_clips(session.id, {clip_id: clip})

    updated_clip = test_db_service.remove_clip_label(session.id, clip_id)

    assert updated_clip is not None
    assert updated_clip.user_label is None
    assert updated_clip.labeled_at is None


def test_get_labeled_clips(test_db_service):
    '''Test getting labeled clips.'''
    # Create session
    filename = 'test_audio.wav'
    session = test_db_service.create_session(filename)

    # Create clips with different labeling states
    clips = {
        'clip_0': AudioClip(
            start_sample=0,
            start_time=0.0,
            end_sample=1000,
            end_time=1.0,
            sample_rate=44100,
            peak_sample=500,
            peak_time=0.5,
            predicted_labels=[DrumLabel.KICK_DRUM],
            user_label=[DrumLabel.KICK_DRUM],  # Labeled
            labeled_at=datetime.now(UTC),
            session_id=session.id,
        ),
        'clip_1': AudioClip(
            start_sample=1000,
            start_time=1.0,
            end_sample=2000,
            end_time=2.0,
            sample_rate=44100,
            peak_sample=1500,
            peak_time=1.5,
            predicted_labels=[DrumLabel.SNARE_DRUM],
            session_id=session.id,
            # Not labeled
        ),
    }

    test_db_service.save_clips(session.id, clips)

    # Get only labeled clips
    labeled_clips = test_db_service.get_labeled_clips(session.id)

    assert len(labeled_clips) == 1
    assert labeled_clips[0].user_label == [DrumLabel.KICK_DRUM]


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

    test_db_service.save_clips(session1.id, {clip1.id: clip1})
    test_db_service.save_clips(session2.id, {clip2.id: clip2})

    # Get all labeled clips
    all_labeled_clips = test_db_service.get_all_labeled_clips()

    assert len(all_labeled_clips) == 2
    user_labels = [clip.user_label[0] for clip in all_labeled_clips]
    assert DrumLabel.KICK_DRUM in user_labels
    assert DrumLabel.SNARE_DRUM in user_labels
