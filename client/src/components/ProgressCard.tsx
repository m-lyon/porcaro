import { useNavigate } from 'react-router';
import { Calendar, BarChart3 } from 'lucide-react';
import { Button } from '@porcaro/components/ui/button';
import { Progress } from '@porcaro/components/ui/progress';
import type { LabelingSession } from '@porcaro/api/generated';
import { Card, CardContent } from '@porcaro/components/ui/card';

interface Props {
    session: LabelingSession;
}
export function ProgressCard(props: Props) {
    const { session } = props;
    const navigate = useNavigate();
    const progress = ((session.labeled_clips ?? 0) / (session.total_clips ?? 1)) * 100;

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
                            {session.bpm && <span>{session.bpm.toFixed(1)} BPM</span>}
                            {session.processed && (
                                <span className='flex items-center gap-1'>
                                    <BarChart3 className='h-3 w-3' />
                                    {session.labeled_clips ?? 0}/{session.total_clips ?? 0} labeled
                                </span>
                            )}
                        </div>
                        {session.processed && (session.total_clips ?? 0) > 0 && (
                            <div className='space-y-1'>
                                <div className='flex justify-between text-sm'>
                                    <span>Progress</span>
                                    <span>{progress.toFixed(1)} %</span>
                                </div>
                                <Progress value={progress} className='h-2' />
                            </div>
                        )}
                    </div>
                    <div className='ml-4'>
                        <Button
                            onClick={() => navigate(`/session/${session.session_id}`)}
                            variant={session.processed ? 'default' : 'secondary'}
                        >
                            {session.processed ? 'Continue Labeling' : 'Configure'}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
