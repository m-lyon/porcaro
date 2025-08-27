import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { ArrowLeft, Settings, Play, BarChart3, Download, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

export default function SessionPage() {
    const { sessionId } = useParams();
    const navigate = useNavigate();

    const [session, setSession] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const [timeSignature, setTimeSignature] = useState({ numerator: 4, denominator: 4 });
    const [startBeat, setStartBeat] = useState(1);
    const [offset, setOffset] = useState(0);
    const [duration, setDuration] = useState('');
    const [resolution, setResolution] = useState(16);

    useEffect(() => {
        loadSession();
    }, [sessionId]);

    const loadSession = async () => {
        try {
            const sessionData = await api.getSession(sessionId);
            setSession(sessionData);

            // Pre-fill form with session data if available
            if (sessionData.time_signature) {
                setTimeSignature(sessionData.time_signature);
            }
            if (sessionData.start_beat) setStartBeat(sessionData.start_beat);
            if (sessionData.offset) setOffset(sessionData.offset);
            if (sessionData.duration) setDuration(sessionData.duration.toString());
            if (sessionData.resolution) setResolution(sessionData.resolution);
        } catch (error) {
            toast.error('Failed to load session: ' + error.message);
            navigate('/');
        } finally {
            setIsLoading(false);
        }
    };

    const handleProcessAudio = async () => {
        if (!session) return;

        setIsProcessing(true);
        try {
            const processRequest = {
                time_signature: timeSignature,
                start_beat: startBeat,
                offset: offset,
                duration: duration ? parseFloat(duration) : null,
                resolution: resolution,
            };

            await api.processAudio(sessionId, processRequest);
            toast.success('Audio processing started successfully!');

            // Reload session to get updated status
            await loadSession();
        } catch (error) {
            toast.error('Failed to process audio: ' + error.message);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleStartLabeling = () => {
        navigate(`/session/${sessionId}/label`);
    };

    const handleExportData = async () => {
        try {
            const data = await api.exportData(sessionId);
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${session?.filename}_labeled_data.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success('Data exported successfully!');
        } catch (error) {
            toast.error('Failed to export data: ' + error.message);
        }
    };

    const handleDeleteSession = async () => {
        if (
            !confirm('Are you sure you want to delete this session? This action cannot be undone.')
        ) {
            return;
        }

        try {
            await api.deleteSession(sessionId);
            toast.success('Session deleted successfully');
            navigate('/');
        } catch (error) {
            toast.error('Failed to delete session: ' + error.message);
        }
    };

    if (isLoading) {
        return (
            <div className='flex items-center justify-center py-12'>
                <div className='text-center space-y-2'>
                    <div className='w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto'></div>
                    <p className='text-muted-foreground'>Loading session...</p>
                </div>
            </div>
        );
    }

    if (!session) {
        return (
            <div className='text-center py-12'>
                <p className='text-muted-foreground'>Session not found</p>
                <Button onClick={() => navigate('/')} className='mt-4'>
                    Back to Home
                </Button>
            </div>
        );
    }

    const progressPercentage =
        session.total_clips > 0 ? (session.labeled_clips / session.total_clips) * 100 : 0;

    return (
        <div className='space-y-6'>
            {/* Header */}
            <div className='flex items-center gap-4'>
                <Button variant='ghost' onClick={() => navigate('/')}>
                    <ArrowLeft className='h-4 w-4' />
                    Back to Home
                </Button>
                <div>
                    <h1 className='text-2xl font-bold'>{session.filename}</h1>
                    <p className='text-muted-foreground'>
                        Session created {new Date(session.created_at).toLocaleDateString()}
                    </p>
                </div>
            </div>

            <div className='grid gap-6 lg:grid-cols-2'>
                {/* Configuration */}
                <Card>
                    <CardHeader>
                        <CardTitle className='flex items-center gap-2'>
                            <Settings className='h-5 w-5' />
                            Processing Configuration
                        </CardTitle>
                        <CardDescription>
                            Configure how the audio should be processed for transcription
                        </CardDescription>
                    </CardHeader>
                    <CardContent className='space-y-4'>
                        <div className='grid grid-cols-2 gap-4'>
                            <div className='space-y-2'>
                                <Label>Time Signature (Numerator)</Label>
                                <Select
                                    value={timeSignature.numerator.toString()}
                                    onValueChange={(value) =>
                                        setTimeSignature((prev) => ({
                                            ...prev,
                                            numerator: parseInt(value),
                                        }))
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value='2'>2</SelectItem>
                                        <SelectItem value='3'>3</SelectItem>
                                        <SelectItem value='4'>4</SelectItem>
                                        <SelectItem value='5'>5</SelectItem>
                                        <SelectItem value='6'>6</SelectItem>
                                        <SelectItem value='7'>7</SelectItem>
                                        <SelectItem value='8'>8</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className='space-y-2'>
                                <Label>Time Signature (Denominator)</Label>
                                <Select
                                    value={timeSignature.denominator.toString()}
                                    onValueChange={(value) =>
                                        setTimeSignature((prev) => ({
                                            ...prev,
                                            denominator: parseInt(value),
                                        }))
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value='2'>2</SelectItem>
                                        <SelectItem value='4'>4</SelectItem>
                                        <SelectItem value='8'>8</SelectItem>
                                        <SelectItem value='16'>16</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className='space-y-2'>
                            <Label>Start Beat</Label>
                            <Input
                                type='number'
                                value={startBeat}
                                onChange={(e) => setStartBeat(parseFloat(e.target.value) || 1)}
                                min='0'
                                step='0.1'
                            />
                        </div>

                        <div className='space-y-2'>
                            <Label>Offset (seconds)</Label>
                            <Input
                                type='number'
                                value={offset}
                                onChange={(e) => setOffset(parseFloat(e.target.value) || 0)}
                                min='0'
                                step='0.1'
                            />
                        </div>

                        <div className='space-y-2'>
                            <Label>Duration (seconds, optional)</Label>
                            <Input
                                type='number'
                                value={duration}
                                onChange={(e) => setDuration(e.target.value)}
                                min='0'
                                step='0.1'
                                placeholder='Process entire file'
                            />
                        </div>

                        <div className='space-y-2'>
                            <Label>Resolution</Label>
                            <Select
                                value={resolution.toString()}
                                onValueChange={(value) => setResolution(parseInt(value))}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value='8'>8</SelectItem>
                                    <SelectItem value='16'>16</SelectItem>
                                    <SelectItem value='32'>32</SelectItem>
                                    <SelectItem value='64'>64</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <Button
                            onClick={handleProcessAudio}
                            disabled={isProcessing || session.processed}
                            className='w-full'
                        >
                            {isProcessing ? (
                                <>Processing Audio...</>
                            ) : session.processed ? (
                                <>Audio Already Processed</>
                            ) : (
                                <>
                                    <Play className='h-4 w-4 mr-2' />
                                    Process Audio
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                {/* Session Info & Actions */}
                <div className='space-y-6'>
                    <Card>
                        <CardHeader>
                            <CardTitle className='flex items-center gap-2'>
                                <BarChart3 className='h-5 w-5' />
                                Session Status
                            </CardTitle>
                        </CardHeader>
                        <CardContent className='space-y-4'>
                            <div className='grid grid-cols-2 gap-4 text-sm'>
                                <div>
                                    <span className='text-muted-foreground'>Status:</span>
                                    <div className='font-medium'>
                                        {session.processed ? (
                                            <span className='text-green-600'>Processed</span>
                                        ) : (
                                            <span className='text-yellow-600'>
                                                Pending Processing
                                            </span>
                                        )}
                                    </div>
                                </div>
                                {session.bpm && (
                                    <div>
                                        <span className='text-muted-foreground'>BPM:</span>
                                        <div className='font-medium'>{session.bpm.toFixed(1)}</div>
                                    </div>
                                )}
                                <div>
                                    <span className='text-muted-foreground'>Total Clips:</span>
                                    <div className='font-medium'>{session.total_clips}</div>
                                </div>
                                <div>
                                    <span className='text-muted-foreground'>Labeled:</span>
                                    <div className='font-medium'>{session.labeled_clips}</div>
                                </div>
                            </div>

                            {session.processed && session.total_clips > 0 && (
                                <div className='space-y-2'>
                                    <div className='flex justify-between text-sm'>
                                        <span>Labeling Progress</span>
                                        <span>{progressPercentage.toFixed(1)}%</span>
                                    </div>
                                    <Progress value={progressPercentage} className='h-2' />
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Actions */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Actions</CardTitle>
                        </CardHeader>
                        <CardContent className='space-y-3'>
                            <Button
                                onClick={handleStartLabeling}
                                disabled={!session.processed}
                                className='w-full'
                                size='lg'
                            >
                                {session.processed ? 'Start Labeling' : 'Process Audio First'}
                            </Button>

                            {session.labeled_clips > 0 && (
                                <Button
                                    onClick={handleExportData}
                                    variant='outline'
                                    className='w-full'
                                >
                                    <Download className='h-4 w-4 mr-2' />
                                    Export Labeled Data
                                </Button>
                            )}

                            <Button
                                onClick={handleDeleteSession}
                                variant='destructive'
                                className='w-full'
                            >
                                <Trash2 className='h-4 w-4 mr-2' />
                                Delete Session
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
