import { useNavigate } from 'react-router';
import { Calendar, BarChart3 } from 'lucide-react';
import { Button } from '@porcaro/components/ui/button';
import { useCallback, useEffect, useState } from 'react';
import { Progress } from '@porcaro/components/ui/progress';
import { Card, CardContent } from '@porcaro/components/ui/card';
import { type SessionProgressResponse } from '@porcaro/api/generated';
import { getSessionProgress, type LabelingSessionResponse } from '@porcaro/api/generated';

interface Props {
    session: LabelingSessionResponse;
}
export function ProgressCard(props: Props) {
    const { session } = props;
    const navigate = useNavigate();
    const [progress, setProgress] = useState<SessionProgressResponse | null>(null);

    const isProcessed = session.processing_metadata?.processed ?? false;

    const loadProgress = useCallback(async () => {
        const progressData = await getSessionProgress({ path: { session_id: session.id } });
        if (progressData.data) {
            setProgress(progressData.data);
        }
    }, [session.id]);

    useEffect(() => {
        if (isProcessed) {
            loadProgress();
        }
    }, [loadProgress, isProcessed]);

    const formatDate = (dateString: string | undefined) => {
        if (!dateString) {
            return 'Unknown date';
        }
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <Card className='border-2 hover:border-primary/50 transition-colors'>
            <CardContent className='p-4'>
                <div className='flex items-center justify-between'>
                    <div className='space-y-2 flex-1'>
                        <div className='flex items-center gap-2'>
                            <h3 className='font-semibold'>{session.filename}</h3>
                            {session.processing_metadata?.processed ? (
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
                            {session.bpm && <span>{session.bpm.toFixed(1)} BPM</span>}
                            {isProcessed && progress && (
                                <span className='flex items-center gap-1'>
                                    <BarChart3 className='h-3 w-3' />
                                    {progress.labeled_clips}/{progress.total_clips} labeled
                                </span>
                            )}
                        </div>
                        {isProcessed && progress && (
                            <div className='space-y-1'>
                                <div className='flex justify-between text-sm'>
                                    <span>Progress</span>
                                    <span>{progress.progress_percentage.toFixed(1)} %</span>
                                </div>
                                <Progress value={progress.progress_percentage} className='h-2' />
                            </div>
                        )}
                    </div>
                    <div className='ml-4'>
                        <Button
                            onClick={() => navigate(`/session/${session.id}`)}
                            variant={isProcessed ? 'default' : 'secondary'}
                        >
                            {isProcessed ? 'Continue Labeling' : 'Configure'}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
