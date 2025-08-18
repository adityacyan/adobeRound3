import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import InsightsPanel from '../Sidebar/InsightsPanel';
import RelatedContentPanel from '../Sidebar/RelatedContentPanel';
import ActionControlsPanel from '../Sidebar/ActionControlsPanel';
import PDFViewer from '../PDFViewer/PDFViewer';
import UploadArea from '../PDFViewer/UploadArea';
import { createSession, getSessionDocuments } from '../../services/api';
import { WebSocketService } from '../../services/api';

const ThreeColumnLayout = () => {
    const [sessionId, setSessionId] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [activeDocumentId, setActiveDocumentId] = useState(null);
    const [selectedText, setSelectedText] = useState('');
    const [insights, setInsights] = useState(null);
    const [relatedContent, setRelatedContent] = useState([]);
    const [loading, setLoading] = useState(false);
    const [wsService, setWsService] = useState(null);

    // Initialize session on mount
    useEffect(() => {
        const initSession = async () => {
            try {
                const sessionData = await createSession();
                setSessionId(sessionData.session_id);

                // Initialize WebSocket connection
                const ws = new WebSocketService(sessionData.session_id);
                ws.connect();

                ws.on('processing_update', (data) => {
                    console.log('Processing update:', data);
                    // Refresh documents when processing completes
                    if (data.status === 'completed') {
                        loadDocuments(sessionData.session_id);
                    }
                });

                setWsService(ws);
            } catch (error) {
                console.error('Failed to initialize session:', error);
            }
        };

        initSession();

        return () => {
            if (wsService) {
                wsService.disconnect();
            }
        };
    }, []);

    const loadDocuments = async (sid = sessionId) => {
        if (!sid) return;

        try {
            const documentsData = await getSessionDocuments(sid);
            setDocuments(documentsData.documents || []);

            // Auto-select first document if none selected
            if (!activeDocumentId && documentsData.documents?.length > 0) {
                setActiveDocumentId(documentsData.documents[0].document_id);
            }
        } catch (error) {
            console.error('Failed to load documents:', error);
        }
    };

    // Load documents when session is ready
    useEffect(() => {
        if (sessionId) {
            loadDocuments();
        }
    }, [sessionId]);

    const handleUploadComplete = () => {
        loadDocuments();
    };

    const handleTextSelection = (text) => {
        setSelectedText(text);
        console.log('Text selected:', text);
    };

    const activeDocument = documents.find(doc => doc.document_id === activeDocumentId);

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <div className="flex items-center">
                            <h1 className="text-2xl font-bold text-gray-900">📄 PDF Analysis Workbench</h1>
                            <span className="ml-3 text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                React + FastAPI
                            </span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <div className="text-sm text-gray-500">
                                Session: {sessionId?.substring(0, 8)}...
                            </div>
                            <div className="flex items-center">
                                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                                <span className="text-sm text-gray-600">Backend Connected</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content - 3 Column Layout */}
            <div className="flex h-[calc(100vh-80px)]">
                {/* Left Sidebar - Insights & Related Content */}
                <div className="w-80 min-w-80 bg-white border-r border-gray-200 flex flex-col">
                    <div className="flex-1 overflow-y-auto">
                        <div className="p-4">
                            <InsightsPanel
                                sessionId={sessionId}
                                activeDocumentId={activeDocumentId}
                                insights={insights}
                                setInsights={setInsights}
                                loading={loading}
                            />
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto border-t border-gray-200">
                        <div className="p-4">
                            <RelatedContentPanel
                                sessionId={sessionId}
                                selectedText={selectedText}
                                relatedContent={relatedContent}
                                setRelatedContent={setRelatedContent}
                                documents={documents}
                            />
                        </div>
                    </div>
                </div>

                {/* Center - PDF Viewer */}
                <div className="flex-1 bg-white min-w-0">
                    <div className="h-full flex flex-col">
                        {documents.length === 0 ? (
                            <div className="h-full flex items-center justify-center">
                                <UploadArea
                                    sessionId={sessionId}
                                    onUploadComplete={handleUploadComplete}
                                />
                            </div>
                        ) : (
                            <PDFViewer
                                sessionId={sessionId}
                                documents={documents}
                                activeDocumentId={activeDocumentId}
                                setActiveDocumentId={setActiveDocumentId}
                                onTextSelection={handleTextSelection}
                            />
                        )}
                    </div>
                </div>

                {/* Right Sidebar - Actions & Upload */}
                <div className="w-80 min-w-80 bg-white border-l border-gray-200 flex flex-col">
                    <div className="flex-1 overflow-y-auto">
                        <div className="p-4">
                            <ActionControlsPanel
                                sessionId={sessionId}
                                activeDocumentId={activeDocumentId}
                                selectedText={selectedText}
                                activeDocument={activeDocument}
                            />
                        </div>
                    </div>
                    {/* Always show upload area in right sidebar */}
                    <div className="border-t border-gray-200 p-4">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">📁 Upload More Documents</h3>
                        <UploadArea
                            sessionId={sessionId}
                            onUploadComplete={handleUploadComplete}
                            compact={true}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ThreeColumnLayout;
