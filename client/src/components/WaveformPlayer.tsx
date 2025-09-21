import { useMemo } from 'react';
import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import WavesurferPlayer from '@wavesurfer/react';
import { Label } from '@porcaro/components/ui/label';
import { Button } from '@porcaro/components/ui/button';
import { Slider } from '@porcaro/components/ui/slider';
import { Play, Pause, SkipBack, SkipForward } from 'lucide-react';
import type WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js';

interface WaveformPlayerProps {
    audioUrl: string;
    isPlaying: boolean;
    setIsPlaying: (playing: boolean) => void;
    onNext?: () => void;
    onPrevious?: () => void;
    canGoNext?: boolean;
    canGoPrevious?: boolean;
    playbackWindow?: number;
    onPlaybackWindowChange?: (value: number[]) => void;
}

export interface WaveformPlayerRef {
    togglePlayback: () => void;
    play: () => void;
    pause: () => void;
    isPlaying: () => boolean;
}

export const WaveformPlayer = forwardRef<WaveformPlayerRef, WaveformPlayerProps>(
    (
        {
            audioUrl,
            isPlaying,
            setIsPlaying,
            onNext,
            onPrevious,
            canGoNext = true,
            canGoPrevious = true,
            playbackWindow = 1.0,
            onPlaybackWindowChange,
        },
        ref
    ) => {
        const waveSurferRef = useRef<WaveSurfer | null>(null);
        const [isLoading, setIsLoading] = useState(true);
        const [currentTime, setCurrentTime] = useState(0);
        const [duration, setDuration] = useState(0);
        const [playbackSpeed, setPlaybackSpeed] = useState<number[]>([1.0]);
        const regionsPlugin = useMemo(() => RegionsPlugin.create(), []);
        const plugins = useMemo(() => [regionsPlugin], [regionsPlugin]);

        const onDecode = useCallback(
            (_ws: WaveSurfer) => {
                // Add a region to highlight the playback window
                regionsPlugin.addRegion({
                    start: playbackWindow / 2,
                    color: 'rgba(242, 52, 52, 0.75)',
                });
            },
            [regionsPlugin, playbackWindow]
        );

        const onReady = useCallback((ws: WaveSurfer) => {
            waveSurferRef.current = ws;
            setIsLoading(false);
            setDuration(ws.getDuration());
        }, []);

        const onPlay = useCallback(() => {
            setIsPlaying(true);
        }, [setIsPlaying]);

        const onPause = useCallback(() => {
            setIsPlaying(false);
        }, [setIsPlaying]);

        const onFinish = useCallback(() => {
            setIsPlaying(false);
        }, [setIsPlaying]);

        const onTimeupdate = useCallback((ws: WaveSurfer) => {
            setCurrentTime(ws.getCurrentTime());
        }, []);

        const onError = useCallback((_ws: WaveSurfer, error: Error) => {
            console.error('WaveSurfer error:', error);
            setIsLoading(false);
        }, []);

        // Reset loading state when URL changes
        useEffect(() => {
            if (audioUrl) {
                setIsLoading(true);
                setCurrentTime(0);
            }
        }, [audioUrl]);

        const togglePlayback = useCallback(() => {
            if (!waveSurferRef.current) {
                return;
            }
            waveSurferRef.current.playPause();
        }, []);

        // Expose methods via ref
        useImperativeHandle(
            ref,
            () => ({
                togglePlayback,
                play: () => waveSurferRef.current?.play(),
                pause: () => waveSurferRef.current?.pause(),
                isPlaying: () => isPlaying,
            }),
            [togglePlayback, isPlaying]
        );

        const formatTime = (seconds: number) => {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        };

        return (
            <div className='space-y-4'>
                {/* Waveform Container */}
                <div className='relative'>
                    <div className='w-full border rounded-lg bg-slate-50 dark:bg-slate-900 overflow-hidden'>
                        <WavesurferPlayer
                            height={80}
                            waveColor='#94a3b8'
                            progressColor='#3b82f6'
                            cursorColor='#236adcff'
                            barWidth={2}
                            barRadius={1}
                            barGap={1}
                            normalize={true}
                            backend='WebAudio'
                            mediaControls={false}
                            url={audioUrl}
                            audioRate={playbackSpeed[0]}
                            onReady={onReady}
                            onPlay={onPlay}
                            onPause={onPause}
                            onFinish={onFinish}
                            onTimeupdate={onTimeupdate}
                            onError={onError}
                            plugins={plugins}
                            onDecode={onDecode}
                        />
                    </div>
                    {isLoading && (
                        <div className='absolute inset-0 flex items-center justify-center bg-slate-50 dark:bg-slate-900 rounded-lg'>
                            <div className='animate-pulse text-sm text-slate-500'>
                                Loading waveform...
                            </div>
                        </div>
                    )}
                </div>

                {/* Time Display */}
                <div className='flex justify-between text-sm text-slate-600 dark:text-slate-400'>
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                </div>

                {/* Playback Window Slider */}
                {onPlaybackWindowChange && (
                    <div className='space-y-2'>
                        <Label htmlFor='playback-window' className='text-sm font-medium'>
                            Playback Window: {playbackWindow.toFixed(1)}s
                        </Label>
                        <Slider
                            id='playback-window'
                            min={0.2}
                            max={3.0}
                            step={0.1}
                            value={[playbackWindow]}
                            onValueChange={onPlaybackWindowChange}
                            className='w-full'
                        />
                        <div className='flex justify-between text-xs text-slate-500'>
                            <span>0.2s</span>
                            <span>3.0s</span>
                        </div>
                    </div>
                )}

                {/* Playback Speed Slider */}
                <div className='space-y-2'>
                    <Label htmlFor='playback-speed' className='text-sm font-medium'>
                        Playback Speed: {playbackSpeed[0].toFixed(1)}x
                    </Label>
                    <Slider
                        id='playback-speed'
                        min={0.25}
                        max={2.0}
                        step={0.1}
                        value={playbackSpeed}
                        onValueChange={setPlaybackSpeed}
                        className='w-full'
                    />
                    <div className='flex justify-between text-xs text-slate-500'>
                        <span>0.2s</span>
                        <span>3.0s</span>
                    </div>
                </div>

                {/* Controls */}
                <div className='flex items-center justify-center gap-2'>
                    <Button
                        variant='outline'
                        onClick={onPrevious}
                        disabled={!canGoPrevious}
                        size='sm'
                    >
                        <SkipBack className='h-4 w-4' />
                    </Button>

                    <Button onClick={togglePlayback} size='lg' disabled={isLoading}>
                        {isPlaying ? <Pause className='h-4 w-4' /> : <Play className='h-4 w-4' />}
                    </Button>

                    <Button variant='outline' onClick={onNext} disabled={!canGoNext} size='sm'>
                        <SkipForward className='h-4 w-4' />
                    </Button>
                </div>

                {/* Click to seek hint */}
                <div className='text-center text-xs text-slate-500'>
                    Click on the waveform to seek to a specific time
                </div>
            </div>
        );
    }
);
