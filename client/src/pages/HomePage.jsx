import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Upload, Music, FileAudio, Calendar, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

export default function HomePage() {
    const [sessions, setSessions] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        try {
            const sessionsData = await api.listSessions();
            setSessions(sessionsData);
        } catch (error) {
            toast.error('Failed to load sessions: ' + error.message);
        }
    };

    const handleFileSelect = (event) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setIsUploading(true);
        try {
            const session = await api.createSession(selectedFile);
            toast.success(`Session created successfully: ${session.filename}`);
            navigate(`/session/${session.session_id}`);
        } catch (error) {
            toast.error('Failed to create session: ' + error.message);
        } finally {
            setIsUploading(false);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className='space-y-8'>
            {/* Upload Section */}
            <Card>
                <CardHeader>
                    <CardTitle className='flex items-center gap-2'>
                        <Upload className='h-5 w-5' />
                        Upload Audio File
                    </CardTitle>
                    <CardDescription>
                        Upload an audio file to create a new labeling session. Supported formats:
                        WAV, MP3, FLAC, OGG, M4A
                    </CardDescription>
                </CardHeader>
                <CardContent className='space-y-4'>
                    <div className='space-y-2'>
                        <Label htmlFor='audio-file'>Select Audio File</Label>
                        <Input
                            id='audio-file'
                            type='file'
                            accept='.wav,.mp3,.flac,.ogg,.m4a'
                            onChange={handleFileSelect}
                            disabled={isUploading}
                        />
                    </div>
                    {selectedFile && (
                        <div className='p-3 bg-muted rounded-lg'>
                            <div className='flex items-center gap-2'>
                                <FileAudio className='h-4 w-4' />
                                <span className='font-medium'>{selectedFile.name}</span>
                                <span className='text-sm text-muted-foreground'>
                                    ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                                </span>
                            </div>
                        </div>
                    )}
                    <Button
                        onClick={handleUpload}
                        disabled={!selectedFile || isUploading}
                        className='w-full'
                    >
                        {isUploading ? 'Creating Session...' : 'Create Labeling Session'}
                    </Button>
                </CardContent>
            </Card>

            {/* Sessions List */}
            <Card>
                <CardHeader>
                    <CardTitle className='flex items-center gap-2'>
                        <Music className='h-5 w-5' />
                        Recent Sessions
                    </CardTitle>
                    <CardDescription>
                        Your recent labeling sessions and their progress
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {sessions.length === 0 ? (
                        <div className='text-center py-8'>
                            <FileAudio className='h-12 w-12 mx-auto text-muted-foreground mb-4' />
                            <h3 className='text-lg font-semibold mb-2'>No sessions yet</h3>
                            <p className='text-muted-foreground'>
                                Upload an audio file above to create your first labeling session
                            </p>
                        </div>
                    ) : (
                        <div className='space-y-4'>
                            {sessions.map((session) => (
                                <Card
                                    key={session.session_id}
                                    className='border-2 hover:border-primary/50 transition-colors'
                                >
                                    <CardContent className='p-4'>
                                        <div className='flex items-center justify-between'>
                                            <div className='space-y-2 flex-1'>
                                                <div className='flex items-center gap-2'>
                                                    <h3 className='font-semibold'>
                                                        {session.filename}
                                                    </h3>
                                                    {session.processed ? (
                                                        <span className='px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs'>
                                                            Processed
                                                        </span>
                                                    ) : (
                                                        <span className='px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs'>
                                                            Pending
                                                        </span>
                                                    )}
                                                </div>
                                                <div className='flex items-center gap-4 text-sm text-muted-foreground'>
                                                    <span className='flex items-center gap-1'>
                                                        <Calendar className='h-3 w-3' />
                                                        {formatDate(session.created_at)}
                                                    </span>
                                                    {session.bpm && (
                                                        <span>{session.bpm.toFixed(1)} BPM</span>
                                                    )}
                                                    {session.processed && (
                                                        <span className='flex items-center gap-1'>
                                                            <BarChart3 className='h-3 w-3' />
                                                            {session.labeled_clips}/
                                                            {session.total_clips} labeled
                                                        </span>
                                                    )}
                                                </div>
                                                {session.processed && session.total_clips > 0 && (
                                                    <div className='space-y-1'>
                                                        <div className='flex justify-between text-sm'>
                                                            <span>Progress</span>
                                                            <span>
                                                                {(
                                                                    (session.labeled_clips /
                                                                        session.total_clips) *
                                                                    100
                                                                ).toFixed(1)}
                                                                %
                                                            </span>
                                                        </div>
                                                        <Progress
                                                            value={
                                                                (session.labeled_clips /
                                                                    session.total_clips) *
                                                                100
                                                            }
                                                            className='h-2'
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                            <div className='ml-4'>
                                                <Button
                                                    onClick={() =>
                                                        navigate(`/session/${session.session_id}`)
                                                    }
                                                    variant={
                                                        session.processed ? 'default' : 'secondary'
                                                    }
                                                >
                                                    {session.processed
                                                        ? 'Continue Labeling'
                                                        : 'Configure'}
                                                </Button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
