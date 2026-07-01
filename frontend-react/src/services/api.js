import axios from 'axios';

// API base URL - relative path routed through nginx proxy
const API_BASE_URL = '/api';

// Create axios instance with default config
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
});

// Add request interceptor to handle different content types
api.interceptors.request.use((config) => {
    // Only set JSON content type for non-FormData requests
    if (!(config.data instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json';
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// API functions
export const checkBackendHealth = async () => {
    try {
        // Health endpoint is at root level, not under /api prefix
        const response = await axios.get('/health');
        return response.status === 200;
    } catch (error) {
        console.error('Backend health check failed:', error);
        return false;
    }
};

export const createSession = async () => {
    try {
        console.log('Creating session...');
        const response = await api.post('/session/create');
        console.log('Session created:', response.data);
        return response.data;
    } catch (error) {
        console.error('Failed to create session:', error);
        throw error;
    }
};

export const uploadPDFs = async (sessionId, files, onProgress) => {
    try {
        const formData = new FormData();

        // Add session_id as form data (not URL parameter)
        formData.append('session_id', sessionId);

        // Add files to form data
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await api.post('/upload/bulk', formData, {
            // Don't set Content-Type header - let browser set it automatically for FormData
            onUploadProgress: (progressEvent) => {
                if (onProgress) {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    onProgress(percentCompleted);
                }
            },
        });

        return response.data;
    } catch (error) {
        console.error('Failed to upload PDFs:', error);
        throw error;
    }
};

export const getSessionDocuments = async (sessionId) => {
    try {
        const response = await api.get(`/session/${sessionId}/documents`);
        return response.data;
    } catch (error) {
        console.error('Failed to get session documents:', error);
        throw error;
    }
};

export const getDocumentContent = async (sessionId, documentId) => {
    try {
        const response = await api.get(`/documents/${documentId}/content?session_id=${sessionId}`);
        return response.data;
    } catch (error) {
        console.error('Failed to get document content:', error);
        throw error;
    }
};

export const generateInsights = async (content) => {
    try {
        const response = await api.post('/insights/generate', { content }, { timeout: 60000 });
        return response.data;
    } catch (error) {
        console.error('Failed to generate insights:', error);
        throw error;
    }
};

export const searchRelatedContent = async (sessionId, selectedText, documentIds = null) => {
    try {
        const response = await api.post('/search/related-content', null, {
            params: {
                session_id: sessionId,
                selected_text: selectedText,
                ...(documentIds && { document_ids: documentIds }),
            },
        });
        return response.data;
    } catch (error) {
        console.error('Failed to search related content:', error);
        throw error;
    }
};

export const getProcessingStatus = async (sessionId) => {
    try {
        const response = await api.get(`/session/${sessionId}/processing/status`);
        return response.data;
    } catch (error) {
        console.error('Failed to get processing status:', error);
        throw error;
    }
};

// WebSocket connection for real-time updates
export class WebSocketService {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
        this.listeners = new Map();
    }

    connect() {
        try {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${wsProtocol}//${window.location.host}/api/ws/${this.sessionId}`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.emit('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);

                    // Emit specific event based on message type
                    if (data.type) {
                        this.emit(data.type, data);
                    }

                    // Also emit generic message event
                    this.emit('message', data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.emit('disconnected');
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => callback(data));
        }
    }
}

export const generateSummary = async (sessionId, content, mode = 'document', documentId = null) => {
    try {
        console.log(`Generating ${mode} summary...`);
        const response = await api.post(`/session/${sessionId}/summary`, {
            content,
            mode,
            document_id: documentId
        });
        console.log('Summary generated:', response.data);
        return response.data;
    } catch (error) {
        console.error('Failed to generate summary:', error);
        throw error;
    }
};

export default api;
