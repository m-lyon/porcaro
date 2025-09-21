import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import { labelClip } from '@porcaro/api/generated';
import { getClipAudioUrl } from '@porcaro/lib/api';
import { Badge } from '@porcaro/components/ui/badge';
import { useParams, useNavigate } from 'react-router';
import { Button } from '@porcaro/components/ui/button';
import { CardTitle } from '@porcaro/components/ui/card';
import { Progress } from '@porcaro/components/ui/progress';
import { SelectValue } from '@porcaro/components/ui/select';
import { ArrowLeft, Check, X, Keyboard } from 'lucide-react';
import { DrumLabelBadge } from '@porcaro/components/ClipBadges';
import { useState, useEffect, useRef, useCallback } from 'react';
import { ClipLoadingSkeleton } from '@porcaro/components/LoadingSkeletons';
import { type LabelingSession, type SessionProgress } from '@porcaro/api/generated';
import { type AudioClip, type DrumLabel as DrumLabelValue } from '@porcaro/api/generated';
import { WaveformPlayer, type WaveformPlayerRef } from '@porcaro/components/WaveformPlayer';
import { Card, CardContent, CardDescription, CardHeader } from '@porcaro/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@porcaro/components/ui/select';
import { getClips, getSession, getSessionProgress, removeClipLabel } from '@porcaro/api/generated';
import { useKeyboardShortcuts, formatKeyboardShortcut } from '@porcaro/hooks/useKeyboardShortcuts';

interface DrumLabel {
    value: DrumLabelValue;
    label: string;
    color: string;
    key: string;
}

type FilterStatus = 'all' | 'labeled' | 'unlabeled';

const DRUM_LABELS: DrumLabel[] = [
    { value: 'KD', label: 'Kick Drum', color: 'bg-red-500', key: '1' },
    { value: 'SD', label: 'Snare Drum', color: 'bg-blue-500', key: '2' },
    { value: 'HH', label: 'Hi-Hat', color: 'bg-green-500', key: '3' },
    { value: 'RC', label: 'Ride Cymbal', color: 'bg-yellow-500', key: '4' },
    { value: 'TT', label: 'Tom-Tom', color: 'bg-purple-500', key: '5' },
    { value: 'CC', label: 'Crash Cymbal', color: 'bg-orange-500', key: '6' },
];

export default function LabelingPage() {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();
    const waveformPlayerRef = useRef<WaveformPlayerRef>(null);

    // Early return if sessionId is undefined
    if (!sessionId) {
        navigate('/');
    }

    const [session, setSession] = useState<LabelingSession | null>(null);
    const [clips, setClips] = useState<AudioClip[]>([]);
    const [currentClipIndex, setCurrentClipIndex] = useState<number>(0);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    const [selectedLabels, setSelectedLabels] = useState<DrumLabelValue[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [isSaving, setIsSaving] = useState<boolean>(false);
    const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
    const [progress, setProgress] = useState<SessionProgress | null>(null);
    const [showShortcuts, setShowShortcuts] = useState<boolean>(false);
    const [playbackWindow, setPlaybackWindow] = useState<number[]>([1.0]);
    const [debouncedPlaybackWindow] = useDebounce(playbackWindow[0], 500);

    const togglePlayback = () => {
        if (waveformPlayerRef.current) {
            waveformPlayerRef.current.togglePlayback();
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
        if (!currentClip || !sessionId) {
            return;
        }

        setIsSaving(true);
        try {
            if (selectedLabels.length === 0) {
                // Remove label if no labels selected
                await removeClipLabel({
                    path: { session_id: sessionId, clip_id: currentClip.clip_id },
                });
                toast.success('Label removed');
            } else {
                // Save labels
                await labelClip({
                    body: { labels: selectedLabels },
                    path: { session_id: sessionId, clip_id: currentClip.clip_id },
                });
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
            const progressResponse = await getSessionProgress({
                path: { session_id: sessionId },
            });
            if (progressResponse && progressResponse.data) {
                setProgress(progressResponse.data);
            }

            // Auto-advance to next unlabeled clip
            if (filterStatus === 'unlabeled' || filterStatus === 'all') {
                nextClip();
            }
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error('Failed to save label: ' + errorMessage);
        } finally {
            setIsSaving(false);
        }
    };

    const clearLabels = () => {
        setSelectedLabels([]);
    };

    const loadClipLabels = (clip: AudioClip) => {
        if (clip?.user_label) {
            setSelectedLabels([...clip.user_label]);
        } else {
            setSelectedLabels([]);
        }
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

    const loadSessionAndClips = useCallback(async () => {
        if (!sessionId) {
            return;
        }

        setIsLoading(true);

        // Load session info
        const sessionData = await getSession({
            path: { session_id: sessionId },
        });
        if (!sessionData || !sessionData.data) {
            toast.error('Session not found');
            setIsLoading(false);
            return;
        }
        setSession(sessionData.data);

        // Load progress
        const progressResponse = await getSessionProgress({
            path: { session_id: sessionId },
        });
        if (!progressResponse || !progressResponse.data) {
            toast.error('Failed to load session progress');
            setIsLoading(false);
            return;
        }
        setProgress(progressResponse.data);

        // Load clips based on filter
        const labeled =
            filterStatus === 'labeled' ? true : filterStatus === 'unlabeled' ? false : undefined;
        const clipsData = await getClips({
            path: { session_id: sessionId },
            query: { page: 1, page_size: 100, labeled },
        });
        if (!clipsData || !clipsData.data) {
            toast.error('Failed to load clips');
            setIsLoading(false);
            return;
        }
        setClips(clipsData.data.clips);

        // Reset to first clip if we have clips
        if (clipsData.data.clips.length > 0) {
            setCurrentClipIndex(0);
            loadClipLabels({
                ...clipsData.data.clips[0],
                user_label:
                    clipsData.data.clips[0].user_label === undefined
                        ? null
                        : clipsData.data.clips[0].user_label,
            });
        }
        setIsLoading(false);
    }, [sessionId, filterStatus]);

    useEffect(() => {
        loadSessionAndClips();
    }, [loadSessionAndClips]);

    const toggleLabel = (labelValue: DrumLabelValue) => {
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

                    <Select
                        value={filterStatus}
                        onValueChange={(value: FilterStatus) => setFilterStatus(value)}
                    >
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
                            <span>{progress.progress_percentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={progress.progress_percentage} className='h-2' />
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
                        <WaveformPlayer
                            ref={waveformPlayerRef}
                            audioUrl={
                                sessionId && currentClip
                                    ? getClipAudioUrl(
                                          sessionId,
                                          currentClip.clip_id,
                                          debouncedPlaybackWindow
                                      )
                                    : ''
                            }
                            isPlaying={isPlaying}
                            setIsPlaying={setIsPlaying}
                            onNext={nextClip}
                            onPrevious={previousClip}
                            canGoNext={currentClipIndex < clips.length - 1}
                            canGoPrevious={currentClipIndex > 0}
                            playbackWindow={playbackWindow[0]}
                            onPlaybackWindowChange={setPlaybackWindow}
                        />

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
