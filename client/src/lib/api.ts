/**
 * API service for the data labeling backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

export interface DrumLabel {
    KD: 'KD';
    SD: 'SD';
    HH: 'HH';
    RC: 'RC';
    TT: 'TT';
    CC: 'CC';
}

export type DrumLabelValue = keyof DrumLabel;

export interface TimeSignature {
    numerator: number;
    denominator: number;
}

export interface AudioClip {
    clip_id: string;
    start_sample: number;
    start_time: number;
    end_sample: number;
    end_time: number;
    sample_rate: number;
    peak_sample: number;
    peak_time: number;
    predicted_labels: DrumLabelValue[];
    user_label?: DrumLabelValue[] | null;
    confidence_scores?: Record<string, number> | null;
    labeled_at?: string | null;
}

export interface LabelingSession {
    session_id: string;
    filename: string;
    time_signature?: TimeSignature | null;
    start_beat: number;
    offset: number;
    duration?: number | null;
    resolution?: number | null;
    bpm?: number | null;
    total_clips: number;
    labeled_clips: number;
    created_at: string;
    processed: boolean;
}

export interface ProcessAudioRequest {
    time_signature: TimeSignature;
    start_beat?: number;
    offset?: number;
    duration?: number | null;
    resolution?: number;
}

export interface LabelClipRequest {
    labels: DrumLabelValue[];
}

export interface ClipListResponse {
    clips: AudioClip[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
}

export interface SessionProgressResponse {
    session_id: string;
    total_clips: number;
    labeled_clips: number;
    progress_percentage: number;
    remaining_clips: number;
}

export interface ExportDataResponse {
    session_id: string;
    export_format: string;
    data: unknown;
    created_at: string;
}

export interface Statistics {
    total_labeled_clips: number;
    clips_by_label: Record<string, number>;
    sessions_count: number;
}

class APIError extends Error {
    public status: number;

    constructor(status: number, message: string) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new APIError(response.status, errorData.detail || 'Request failed');
    }
    return response.json();
}

export const api = {
    // Session Management
    async createSession(file: File): Promise<LabelingSession> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/sessions/`, {
            method: 'POST',
            body: formData,
        });

        return handleResponse<LabelingSession>(response);
    },

    async getSession(sessionId: string): Promise<LabelingSession> {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
        return handleResponse<LabelingSession>(response);
    },

    async processAudio(sessionId: string, request: ProcessAudioRequest): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        return handleResponse<void>(response);
    },

    async getSessionProgress(sessionId: string): Promise<SessionProgressResponse> {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/progress`);
        return handleResponse<SessionProgressResponse>(response);
    },

    async deleteSession(sessionId: string): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
            method: 'DELETE',
        });

        return handleResponse<void>(response);
    },

    async listSessions(): Promise<LabelingSession[]> {
        const response = await fetch(`${API_BASE_URL}/sessions/`);
        return handleResponse<LabelingSession[]>(response);
    },

    // Clip Management
    async getClips(
        sessionId: string,
        page: number = 1,
        pageSize: number = 20,
        labeled?: boolean
    ): Promise<ClipListResponse> {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
        });

        if (labeled !== undefined) {
            params.append('labeled', labeled.toString());
        }

        const response = await fetch(`${API_BASE_URL}/clips/${sessionId}/clips?${params}`);
        return handleResponse<ClipListResponse>(response);
    },

    async getClip(sessionId: string, clipId: string): Promise<AudioClip> {
        const response = await fetch(`${API_BASE_URL}/clips/${sessionId}/clips/${clipId}`);
        return handleResponse<AudioClip>(response);
    },

    getClipAudioUrl(sessionId: string, clipId: string): string {
        return `${API_BASE_URL}/clips/${sessionId}/clips/${clipId}/audio`;
    },

    // Labeling
    async labelClip(
        sessionId: string,
        clipId: string,
        request: LabelClipRequest
    ): Promise<AudioClip> {
        const response = await fetch(`${API_BASE_URL}/labels/${sessionId}/clips/${clipId}/label`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        return handleResponse<AudioClip>(response);
    },

    async removeClipLabel(sessionId: string, clipId: string): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/labels/${sessionId}/clips/${clipId}/label`, {
            method: 'DELETE',
        });

        return handleResponse<void>(response);
    },

    async exportData(sessionId: string, format: string = 'json'): Promise<ExportDataResponse> {
        const response = await fetch(`${API_BASE_URL}/labels/${sessionId}/export?format=${format}`);
        return handleResponse<ExportDataResponse>(response);
    },

    // Dataset Management
    async getStatistics(): Promise<Statistics> {
        const response = await fetch(`${API_BASE_URL}/labels/statistics`);
        return handleResponse<Statistics>(response);
    },

    async removeSessionLabeledData(sessionId: string): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/labels/${sessionId}/labeled_data`, {
            method: 'DELETE',
        });

        return handleResponse<void>(response);
    },
};

export { APIError };
