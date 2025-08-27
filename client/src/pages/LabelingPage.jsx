import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, Check, X, Keyboard } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { ClipLoadingSkeleton } from '@/components/LoadingSkeletons';
import { DrumLabelBadge } from '@/components/ClipBadges';
import { useKeyboardShortcuts, formatKeyboardShortcut } from '@/hooks/useKeyboardShortcuts';

const DRUM_LABELS = [
    { value: 'KD', label: 'Kick Drum', color: 'bg-red-500', key: '1' },
    { value: 'SD', label: 'Snare Drum', color: 'bg-blue-500', key: '2' },
    { value: 'HH', label: 'Hi-Hat', color: 'bg-green-500', key: '3' },
    { value: 'RC', label: 'Ride Cymbal', color: 'bg-yellow-500', key: '4' },
    { value: 'TT', label: 'Tom-Tom', color: 'bg-purple-500', key: '5' },
    { value: 'CC', label: 'Crash Cymbal', color: 'bg-orange-500', key: '6' },
];

export default function LabelingPage() {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const audioRef = useRef(null);

    const [session, setSession] = useState(null);
    const [clips, setClips] = useState([]);
    const [currentClipIndex, setCurrentClipIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [selectedLabels, setSelectedLabels] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [filterStatus, setFilterStatus] = useState('all'); // all, labeled, unlabeled
    const [progress, setProgress] = useState(null);
    const [showShortcuts, setShowShortcuts] = useState(false);

    const togglePlayback = () => {
        if (!audioRef.current) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
    };

    const nextClip = () => {
        if (currentClipIndex < clips.length - 1) {
            const newIndex = currentClipIndex + 1;
            setCurrentClipIndex(newIndex);
            loadClipLabels(clips[newIndex]);
            setIsPlaying(false);
        }
    };

    const previousClip = () => {
        if (currentClipIndex > 0) {
            const newIndex = currentClipIndex - 1;
            setCurrentClipIndex(newIndex);
            loadClipLabels(clips[newIndex]);
            setIsPlaying(false);
        }
    };

    const saveLabel = async () => {
        const currentClip = clips[currentClipIndex];
        if (!currentClip) return;

        setIsSaving(true);
        try {
            if (selectedLabels.length === 0) {
                // Remove label if no labels selected
                await api.removeClipLabel(sessionId, currentClip.clip_id);
                toast.success('Label removed');
            } else {
                // Save labels
                await api.labelClip(sessionId, currentClip.clip_id, { labels: selectedLabels });
                toast.success('Label saved');
            }

            // Update the clip in our local state
            setClips((prev) =>
                prev.map((clip, index) =>
                    index === currentClipIndex
                        ? { ...clip, user_label: selectedLabels.length > 0 ? selectedLabels : null }
                        : clip
                )
            );

            // Update progress
            const progressData = await api.getSessionProgress(sessionId);
            setProgress(progressData);

            // Auto-advance to next unlabeled clip
            if (filterStatus === 'unlabeled' || filterStatus === 'all') {
                nextClip();
            }
        } catch (error) {
            toast.error('Failed to save label: ' + error.message);
        } finally {
            setIsSaving(false);
        }
    };

    const clearLabels = () => {
        setSelectedLabels([]);
    };

    // Keyboard shortcuts configuration
    const keyboardShortcuts = [
        { key: ' ', callback: togglePlayback, description: 'Play/Pause audio' },
        { key: 'ArrowLeft', callback: previousClip, description: 'Previous clip' },
        { key: 'ArrowRight', callback: nextClip, description: 'Next clip' },
        { key: 'Enter', callback: saveLabel, description: 'Save current labels' },
        { key: 'Escape', callback: clearLabels, description: 'Clear all labels' },
        ...DRUM_LABELS.map((label) => ({
            key: label.key,
            callback: () => toggleLabel(label.value),
            description: `Toggle ${label.label}`,
        })),
    ];

    const currentClip = clips[currentClipIndex];

    useKeyboardShortcuts(keyboardShortcuts, !isLoading && !!currentClip);

    useEffect(() => {
        loadSessionAndClips();
    }, [sessionId, filterStatus]);

    // Remove the old keyboard event handler since we're using the hook now

    const loadSessionAndClips = async () => {
        try {
            setIsLoading(true);

            // Load session info
            const sessionData = await api.getSession(sessionId);
            setSession(sessionData);

            // Load progress
            const progressData = await api.getSessionProgress(sessionId);
            setProgress(progressData);

            // Load clips based on filter
            const labeled =
                filterStatus === 'labeled'
                    ? true
                    : filterStatus === 'unlabeled'
                    ? false
                    : undefined;

            const clipsData = await api.getClips(sessionId, 1, 100, labeled);
            setClips(clipsData.clips);

            // Reset to first clip if we have clips
            if (clipsData.clips.length > 0) {
                setCurrentClipIndex(0);
                loadClipLabels(clipsData.clips[0]);
            }
        } catch (error) {
            toast.error('Failed to load session data: ' + error.message);
            navigate('/');
        } finally {
            setIsLoading(false);
        }
    };

    const loadClipLabels = (clip) => {
        if (clip?.user_label) {
            setSelectedLabels([...clip.user_label]);
        } else {
            setSelectedLabels([]);
        }
    };

    const toggleLabel = (labelValue) => {
        setSelectedLabels((prev) =>
            prev.includes(labelValue) ? prev.filter((l) => l !== labelValue) : [...prev, labelValue]
        );
    };

    if (isLoading) {
        return (
            <div className='space-y-6'>
                <div className='flex items-center gap-4'>
                    <Button variant='ghost' onClick={() => navigate(`/session/${sessionId}`)}>
                        <ArrowLeft className='h-4 w-4' />
                        Back to Session
                    </Button>
                    <div>
                        <div className='h-8 w-64 bg-muted animate-pulse rounded mb-2'></div>
                        <div className='h-4 w-48 bg-muted animate-pulse rounded'></div>
                    </div>
                </div>
                <ClipLoadingSkeleton />
            </div>
        );
    }

    if (!currentClip) {
        return (
            <div className='space-y-6'>
                <div className='flex items-center gap-4'>
                    <Button variant='ghost' onClick={() => navigate(`/session/${sessionId}`)}>
                        <ArrowLeft className='h-4 w-4' />
                        Back to Session
                    </Button>
                    <h1 className='text-2xl font-bold'>No clips to label</h1>
                </div>
                <Card>
                    <CardContent className='pt-6 text-center'>
                        <p className='text-muted-foreground'>
                            {filterStatus === 'unlabeled'
                                ? 'All clips have been labeled!'
                                : 'No clips found for the current filter.'}
                        </p>
                        <div className='mt-4 space-x-2'>
                            <Button onClick={() => setFilterStatus('all')}>Show All Clips</Button>
                            <Button onClick={() => navigate(`/session/${sessionId}`)}>
                                Back to Session
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const progressPercentage = progress ? (progress.labeled_clips / progress.total_clips) * 100 : 0;

    return (
        <div className='space-y-6'>
            {/* Header */}
            <div className='flex items-center justify-between'>
                <div className='flex items-center gap-4'>
                    <Button variant='ghost' onClick={() => navigate(`/session/${sessionId}`)}>
                        <ArrowLeft className='h-4 w-4' />
                        Back to Session
                    </Button>
                    <div>
                        <h1 className='text-2xl font-bold'>Labeling: {session?.filename}</h1>
                        <p className='text-muted-foreground'>
                            Clip {currentClipIndex + 1} of {clips.length}
                            {progress &&
                                ` • ${progress.labeled_clips}/${progress.total_clips} total clips labeled`}
                        </p>
                    </div>
                </div>

                <div className='flex items-center gap-2'>
                    <Button
                        variant='outline'
                        size='sm'
                        onClick={() => setShowShortcuts(!showShortcuts)}
                    >
                        <Keyboard className='h-4 w-4 mr-2' />
                        Shortcuts
                    </Button>

                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                        <SelectTrigger className='w-40'>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value='all'>All Clips</SelectItem>
                            <SelectItem value='unlabeled'>Unlabeled Only</SelectItem>
                            <SelectItem value='labeled'>Labeled Only</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* Keyboard shortcuts help */}
            {showShortcuts && (
                <Card>
                    <CardHeader>
                        <CardTitle className='flex items-center gap-2'>
                            <Keyboard className='h-5 w-5' />
                            Keyboard Shortcuts
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className='grid grid-cols-2 md:grid-cols-3 gap-3 text-sm'>
                            {keyboardShortcuts.map((shortcut, index) => (
                                <div
                                    key={index}
                                    className='flex items-center justify-between p-2 bg-muted rounded'
                                >
                                    <span>{shortcut.description}</span>
                                    <Badge variant='outline' className='ml-2'>
                                        {formatKeyboardShortcut(shortcut.key)}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Progress */}
            {progress && (
                <Card>
                    <CardContent className='pt-6'>
                        <div className='flex justify-between text-sm mb-2'>
                            <span>Overall Progress</span>
                            <span>{progressPercentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={progressPercentage} className='h-2' />
                    </CardContent>
                </Card>
            )}

            <div className='grid gap-6 lg:grid-cols-2'>
                {/* Audio Player */}
                <Card>
                    <CardHeader>
                        <CardTitle>Audio Clip</CardTitle>
                        <CardDescription>
                            Peak at {currentClip.peak_time.toFixed(3)}s
                            {currentClip.predicted_labels.length > 0 && (
                                <div className='flex gap-1 mt-2'>
                                    <span className='text-muted-foreground'>Predicted:</span>
                                    {currentClip.predicted_labels.map((label) => (
                                        <DrumLabelBadge
                                            key={label}
                                            label={label}
                                            variant='predicted'
                                            size='sm'
                                        />
                                    ))}
                                </div>
                            )}
                        </CardDescription>
                    </CardHeader>
                    <CardContent className='space-y-4'>
                        <audio
                            ref={audioRef}
                            src={api.getClipAudioUrl(sessionId, currentClip.clip_id)}
                            onPlay={() => setIsPlaying(true)}
                            onPause={() => setIsPlaying(false)}
                            onEnded={() => setIsPlaying(false)}
                            preload='auto'
                            className='w-full'
                            controls
                        />

                        <div className='flex items-center justify-center gap-2'>
                            <Button
                                variant='outline'
                                onClick={previousClip}
                                disabled={currentClipIndex === 0}
                            >
                                <SkipBack className='h-4 w-4' />
                            </Button>

                            <Button onClick={togglePlayback} size='lg'>
                                {isPlaying ? (
                                    <Pause className='h-4 w-4' />
                                ) : (
                                    <Play className='h-4 w-4' />
                                )}
                            </Button>

                            <Button
                                variant='outline'
                                onClick={nextClip}
                                disabled={currentClipIndex === clips.length - 1}
                            >
                                <SkipForward className='h-4 w-4' />
                            </Button>
                        </div>

                        <div className='text-center text-sm text-muted-foreground'>
                            <p>
                                Use keyboard shortcuts: Space (play/pause), ← → (navigate), Enter
                                (save)
                            </p>
                        </div>
                    </CardContent>
                </Card>

                {/* Labeling Interface */}
                <Card>
                    <CardHeader>
                        <CardTitle>Drum Labels</CardTitle>
                        <CardDescription>
                            Select the drums you hear in this clip. Use number keys 1-6 for
                            shortcuts.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className='space-y-4'>
                        <div className='grid grid-cols-2 gap-3'>
                            {DRUM_LABELS.map((label) => (
                                <Button
                                    key={label.value}
                                    variant={
                                        selectedLabels.includes(label.value) ? 'default' : 'outline'
                                    }
                                    onClick={() => toggleLabel(label.value)}
                                    className={`justify-start ${
                                        selectedLabels.includes(label.value)
                                            ? `${label.color} text-white`
                                            : ''
                                    }`}
                                >
                                    <span className='w-6 text-xs bg-muted text-muted-foreground rounded px-1 mr-2'>
                                        {label.key}
                                    </span>
                                    {label.label}
                                </Button>
                            ))}
                        </div>

                        {currentClip.user_label && (
                            <div className='p-3 bg-green-50 border border-green-200 rounded-lg'>
                                <p className='text-sm text-green-700 font-medium mb-2'>
                                    Current labels:
                                </p>
                                <div className='flex gap-2 flex-wrap'>
                                    {currentClip.user_label.map((label) => (
                                        <DrumLabelBadge
                                            key={label}
                                            label={label}
                                            variant='user'
                                            size='sm'
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className='flex gap-2 pt-4 border-t'>
                            <Button onClick={clearLabels} variant='outline' className='flex-1'>
                                <X className='h-4 w-4 mr-2' />
                                Clear (Esc)
                            </Button>

                            <Button onClick={saveLabel} disabled={isSaving} className='flex-1'>
                                {isSaving ? (
                                    <>Saving...</>
                                ) : (
                                    <>
                                        <Check className='h-4 w-4 mr-2' />
                                        Save (Enter)
                                    </>
                                )}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
