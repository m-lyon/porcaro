import { toast } from 'sonner';
import { type ChangeEvent } from 'react';
import { useNavigate } from 'react-router';
import { useState, useEffect } from 'react';
import { Input } from '@porcaro/components/ui/input';
import { Label } from '@porcaro/components/ui/label';
import { Button } from '@porcaro/components/ui/button';
import { CardTitle } from '@porcaro/components/ui/card';
import { Upload, Music, FileAudio } from 'lucide-react';
import { ProgressCard } from '@porcaro/components/ProgressCard';
import { Card, CardContent, CardDescription, CardHeader } from '@porcaro/components/ui/card';
import { createSession, type LabelingSessionResponse, getSessions } from '@porcaro/api/generated';

export default function HomePage() {
    const [sessions, setSessions] = useState<LabelingSessionResponse[]>();
    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        try {
            const sessionsData = await getSessions();
            if (!sessionsData.data) {
                toast.error('Failed to load sessions: No data returned');
                return;
            }
            setSessions(sessionsData.data);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error('Failed to load sessions: ' + errorMessage);
        }
    };

    const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            return;
        }

        setIsUploading(true);
        try {
            const session = await createSession({ body: { file: selectedFile } });
            if (!session.data) {
                toast.error('Failed to create session: No data returned');
                return;
            }
            toast.success(`Session created successfully: ${session.data.filename}`);
            navigate(`/session/${session.data.id}`);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error('Failed to create session: ' + errorMessage);
        } finally {
            setIsUploading(false);
        }
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
                    {(sessions?.length ?? 0) === 0 ? (
                        <div className='text-center py-8'>
                            <FileAudio className='h-12 w-12 mx-auto text-muted-foreground mb-4' />
                            <h3 className='text-lg font-semibold mb-2'>No sessions yet</h3>
                            <p className='text-muted-foreground'>
                                Upload an audio file above to create your first labeling session
                            </p>
                        </div>
                    ) : (
                        <div className='space-y-4'>
                            {sessions?.map((session) => (
                                <ProgressCard key={session.id} session={session} />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
