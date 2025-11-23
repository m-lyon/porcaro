import { toast } from 'sonner';
import { Input } from '@porcaro/components/ui/input';
import { Label } from '@porcaro/components/ui/label';
import { useParams, useNavigate } from 'react-router';
import { Button } from '@porcaro/components/ui/button';
import { CardTitle } from '@porcaro/components/ui/card';
import { useState, useEffect, useCallback } from 'react';
import { Progress } from '@porcaro/components/ui/progress';
import { SelectValue } from '@porcaro/components/ui/select';
import { deleteSession, type SessionProgressResponse } from '@porcaro/api/generated';
import { ArrowLeft, Settings, Play, BarChart3, Download, Trash2 } from 'lucide-react';
import { getProcessingStatus, type ProcessingResponse } from '@porcaro/api/generated';
import { getSessionProgress, type LabelingSessionResponse } from '@porcaro/api/generated';
import { Card, CardContent, CardDescription, CardHeader } from '@porcaro/components/ui/card';
import { exportLabeledData, getSession, startSessionProcessing } from '@porcaro/api/generated';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@porcaro/components/ui/select';

export default function SessionPage() {
    const { sessionId } = useParams();
    const navigate = useNavigate();

    const [session, setSession] = useState<LabelingSessionResponse | null>(null);
    const [progress, setProgress] = useState<SessionProgressResponse | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [processingStatus, setProcessingStatus] = useState<ProcessingResponse | null>(null);
    const [taskId, setTaskId] = useState<string | null>(null);

    const [timeSignature, setTimeSignature] = useState({ numerator: 4, denominator: 4 });
    const [startBeat, setStartBeat] = useState(1);
    const [offset, setOffset] = useState(0);
    const [duration, setDuration] = useState('');
    const [resolution, setResolution] = useState(16);

    const loadSession = useCallback(async () => {
        if (!sessionId) {
            toast.error('Invalid session ID');
            navigate('/');
            setIsLoading(false);
            return;
        }
        const sessionData = await getSession({ path: { session_id: sessionId } });
        if (!sessionData || !sessionData.data) {
            toast.error('Session not found');
            navigate('/');
            setIsLoading(false);
            return;
        }
        const progressData = await getSessionProgress({ path: { session_id: sessionId } });
        if (!progressData || !progressData.data) {
            toast.error('Session progress not found');
            navigate('/');
            setIsLoading(false);
            return;
        }
        setSession(sessionData.data);
        if (sessionData.data.time_signature) {
            setTimeSignature(sessionData.data.time_signature);
        }
        if (sessionData.data.start_beat) {
            setStartBeat(sessionData.data.start_beat);
        }
        if (sessionData.data.offset) {
            setOffset(sessionData.data.offset);
        }
        if (sessionData.data.duration) {
            setDuration(sessionData.data.duration.toString());
        }
        if (sessionData.data.resolution) {
            setResolution(sessionData.data.resolution);
        }
        if (progressData && progressData.data) {
            setProgress(progressData.data);
        }
        setIsLoading(false);
    }, [sessionId, navigate]);

    // Polling function for processing status
    const pollProcessingStatus = useCallback(
        async (sessionId: string, taskId: string) => {
            try {
                const statusResponse = await getProcessingStatus({
                    path: { session_id: sessionId, task_id: taskId },
                });

                if (statusResponse.data) {
                    setProcessingStatus(statusResponse.data);

                    // Check if processing is complete
                    if (statusResponse.data.current_state === 'SUCCESS') {
                        setIsProcessing(false);
                        setTaskId(null);
                        toast.success('Audio processing completed successfully!');
                        // Reload session to get updated data
                        await loadSession();
                        return false; // Stop polling
                    } else if (statusResponse.data.current_state === 'FAILURE') {
                        setIsProcessing(false);
                        setTaskId(null);
                        toast.error(
                            'Audio processing failed: ' + statusResponse.data.current_status
                        );
                        return false; // Stop polling
                    }

                    return true; // Continue polling
                }
            } catch (error) {
                console.error('Error polling processing status:', error);
                const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                toast.error('Failed to get processing status: ' + errorMessage);
                setIsProcessing(false);
                setTaskId(null);
                return false; // Stop polling
            }
            return false;
        },
        [loadSession]
    );

    // Effect to handle polling when there's an active task
    useEffect(() => {
        if (!taskId || !sessionId) return;

        const pollInterval = setInterval(async () => {
            const shouldContinue = await pollProcessingStatus(sessionId, taskId);
            if (!shouldContinue) {
                clearInterval(pollInterval);
            }
        }, 1000); // Poll every second

        return () => clearInterval(pollInterval);
    }, [taskId, sessionId, pollProcessingStatus]);

    useEffect(() => {
        loadSession();
    }, [loadSession]);

    const handleProcessAudio = async () => {
        if (!session) {
            return;
        }

        setIsProcessing(true);
        setProcessingStatus(null);
        try {
            const processRequest = {
                time_signature: timeSignature,
                start_beat: startBeat,
                offset: offset,
                duration: duration ? parseFloat(duration) : null,
                resolution: resolution,
            };

            const response = await startSessionProcessing({
                body: processRequest,
                path: { session_id: session.id },
            });

            if (response.data) {
                setTaskId(response.data.task_id);
                setProcessingStatus(response.data);
                toast.success('Audio processing started successfully!');
            }
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error('Failed to start processing: ' + errorMessage);
            setIsProcessing(false);
        }
    };

    const handleStartLabeling = () => {
        navigate(`/session/${sessionId}/label`);
    };

    const handleExportData = async () => {
        try {
            if (!sessionId) {
                throw new Error('Invalid session ID');
            }
            const exportData = await exportLabeledData({ path: { session_id: sessionId } });
            if (!exportData || !exportData.data) {
                throw new Error('No data to export');
            }
            const blob = new Blob([JSON.stringify(exportData.data, null, 2)], {
                type: 'application/json',
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${session?.filename}_labeled_data.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success('Data exported successfully!');
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error('Failed to save label: ' + errorMessage);
        }
    };

    const handleDeleteSession = async () => {
        if (
            !confirm('Are you sure you want to delete this session? This action cannot be undone.')
        ) {
            return;
        }

        try {
            if (!sessionId) {
                throw new Error('Invalid session ID');
            }
            await deleteSession({ path: { session_id: sessionId } });
            toast.success('Session deleted successfully');
            navigate('/');
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error('Failed to delete session: ' + errorMessage);
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

    if (!session || !progress) {
        return (
            <div className='text-center py-12'>
                <p className='text-muted-foreground'>Session not found</p>
                <Button onClick={() => navigate('/')} className='mt-4'>
                    Back to Home
                </Button>
            </div>
        );
    }

    const isProcessed = session.session_metadata?.processed ?? false;

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
                        Session created{' '}
                        {session.created_at
                            ? new Date(session.created_at).toLocaleDateString()
                            : 'Unknown date'}
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
                            disabled={isProcessing || isProcessed}
                            className='w-full'
                        >
                            {isProcessing ? (
                                <>
                                    <div className='w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2'></div>
                                    Processing Audio...
                                </>
                            ) : isProcessed ? (
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
                                        {isProcessing ? (
                                            <span className='text-blue-600'>Processing...</span>
                                        ) : isProcessed ? (
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
                                    <div className='font-medium'>{progress.total_clips}</div>
                                </div>
                                <div>
                                    <span className='text-muted-foreground'>Labeled:</span>
                                    <div className='font-medium'>{progress.labeled_clips}</div>
                                </div>
                            </div>

                            {/* Processing Progress */}
                            {isProcessing && processingStatus && (
                                <div className='space-y-2 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border'>
                                    <div className='flex justify-between text-sm'>
                                        <span className='font-medium text-blue-700 dark:text-blue-300'>
                                            {processingStatus.current_status}
                                        </span>
                                        <span className='text-blue-600 dark:text-blue-400'>
                                            {processingStatus.progress_percentage}%
                                        </span>
                                    </div>
                                    <Progress
                                        value={processingStatus.progress_percentage}
                                        className='h-2'
                                    />
                                    <div className='text-xs text-blue-600 dark:text-blue-400'>
                                        State: {processingStatus.current_state}
                                    </div>
                                </div>
                            )}

                            {/* Labeling Progress */}
                            {isProcessed && progress.total_clips > 0 && (
                                <div className='space-y-2'>
                                    <div className='flex justify-between text-sm'>
                                        <span>Labeling Progress</span>
                                        <span>{progress.progress_percentage.toFixed(1)}%</span>
                                    </div>
                                    <Progress
                                        value={progress.progress_percentage}
                                        className='h-2'
                                    />
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
                                disabled={!isProcessed}
                                className='w-full'
                                size='lg'
                            >
                                {isProcessed ? 'Start Labeling' : 'Process Audio First'}
                            </Button>

                            {progress.labeled_clips > 0 && (
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
