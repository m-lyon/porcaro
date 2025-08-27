import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface ClipStatusBadgeProps {
    clip: {
        user_label?: string[] | null;
        predicted_labels: string[];
    };
}

export function ClipStatusBadge({ clip }: ClipStatusBadgeProps) {
    if (clip.user_label && clip.user_label.length > 0) {
        return (
            <Badge variant='default' className='bg-green-500 hover:bg-green-600'>
                <CheckCircle className='h-3 w-3 mr-1' />
                Labeled
            </Badge>
        );
    }

    if (clip.predicted_labels && clip.predicted_labels.length > 0) {
        return (
            <Badge variant='secondary'>
                <AlertTriangle className='h-3 w-3 mr-1' />
                Predicted
            </Badge>
        );
    }

    return (
        <Badge variant='outline'>
            <Clock className='h-3 w-3 mr-1' />
            Pending
        </Badge>
    );
}

interface DrumLabelBadgeProps {
    label: string;
    variant?: 'default' | 'predicted' | 'user';
    size?: 'sm' | 'default';
}

export function DrumLabelBadge({
    label,
    variant = 'default',
    size = 'default',
}: DrumLabelBadgeProps) {
    const getDrumLabelInfo = (label: string) => {
        const labelMap = {
            KD: { name: 'Kick', color: 'bg-red-500' },
            SD: { name: 'Snare', color: 'bg-blue-500' },
            HH: { name: 'Hi-Hat', color: 'bg-green-500' },
            RC: { name: 'Ride', color: 'bg-yellow-500' },
            TT: { name: 'Tom', color: 'bg-purple-500' },
            CC: { name: 'Crash', color: 'bg-orange-500' },
        };
        return labelMap[label as keyof typeof labelMap] || { name: label, color: 'bg-gray-500' };
    };

    const labelInfo = getDrumLabelInfo(label);

    const baseClasses = size === 'sm' ? 'text-xs px-1.5 py-0.5' : '';

    if (variant === 'user') {
        return (
            <Badge className={`${labelInfo.color} text-white hover:opacity-90 ${baseClasses}`}>
                {labelInfo.name}
            </Badge>
        );
    }

    if (variant === 'predicted') {
        return (
            <Badge
                variant='outline'
                className={`border-${labelInfo.color.replace('bg-', 'border-')} ${baseClasses}`}
            >
                {labelInfo.name}
            </Badge>
        );
    }

    return (
        <Badge variant='secondary' className={baseClasses}>
            {labelInfo.name}
        </Badge>
    );
}
