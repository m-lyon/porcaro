import { Skeleton } from '@porcaro/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@porcaro/components/ui/card';

export function ClipLoadingSkeleton() {
    return (
        <div className='grid gap-6 lg:grid-cols-2'>
            {/* Audio Player Skeleton */}
            <Card>
                <CardHeader>
                    <Skeleton className='h-6 w-32' />
                    <Skeleton className='h-4 w-48' />
                </CardHeader>
                <CardContent className='space-y-4'>
                    <Skeleton className='h-10 w-full' />
                    <div className='flex items-center justify-center gap-2'>
                        <Skeleton className='h-10 w-10 rounded' />
                        <Skeleton className='h-12 w-12 rounded' />
                        <Skeleton className='h-10 w-10 rounded' />
                    </div>
                </CardContent>
            </Card>

            {/* Labeling Interface Skeleton */}
            <Card>
                <CardHeader>
                    <Skeleton className='h-6 w-32' />
                    <Skeleton className='h-4 w-64' />
                </CardHeader>
                <CardContent className='space-y-4'>
                    <div className='grid grid-cols-2 gap-3'>
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <Skeleton key={i} className='h-10 w-full' />
                        ))}
                    </div>
                    <div className='flex gap-2 pt-4'>
                        <Skeleton className='h-10 flex-1' />
                        <Skeleton className='h-10 flex-1' />
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

export function SessionLoadingSkeleton() {
    return (
        <div className='space-y-6'>
            <div className='flex items-center gap-4'>
                <Skeleton className='h-10 w-32' />
                <div>
                    <Skeleton className='h-8 w-64' />
                    <Skeleton className='h-4 w-48 mt-2' />
                </div>
            </div>

            <div className='grid gap-6 lg:grid-cols-2'>
                <Card>
                    <CardHeader>
                        <Skeleton className='h-6 w-48' />
                        <Skeleton className='h-4 w-64' />
                    </CardHeader>
                    <CardContent className='space-y-4'>
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className='space-y-2'>
                                <Skeleton className='h-4 w-32' />
                                <Skeleton className='h-10 w-full' />
                            </div>
                        ))}
                        <Skeleton className='h-10 w-full' />
                    </CardContent>
                </Card>

                <div className='space-y-6'>
                    <Card>
                        <CardHeader>
                            <Skeleton className='h-6 w-32' />
                        </CardHeader>
                        <CardContent className='space-y-4'>
                            <div className='grid grid-cols-2 gap-4'>
                                {[1, 2, 3, 4].map((i) => (
                                    <div key={i}>
                                        <Skeleton className='h-4 w-20 mb-1' />
                                        <Skeleton className='h-6 w-16' />
                                    </div>
                                ))}
                            </div>
                            <Skeleton className='h-2 w-full' />
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <Skeleton className='h-6 w-20' />
                        </CardHeader>
                        <CardContent className='space-y-3'>
                            <Skeleton className='h-12 w-full' />
                            <Skeleton className='h-10 w-full' />
                            <Skeleton className='h-10 w-full' />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
