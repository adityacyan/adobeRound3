import React, { useState, useEffect } from 'react';
import { FileText, Download, Play, Volume2, Copy, Share, ChevronDown, ChevronUp } from 'lucide-react';
import { generateSummary } from '../../services/api';

const ActionControlsPanel = ({
    sessionId,
    activeDocumentId,
    selectedText,
    activeDocument
}) => {
    const [generatingSelection, setGeneratingSelection] = useState(false);
    const [generatingDocument, setGeneratingDocument] = useState(false);
    const [selectionSummary, setSelectionSummary] = useState('');
    const [documentSummary, setDocumentSummary] = useState('');
    const [selectionSummaryError, setSelectionSummaryError] = useState('');
    const [documentSummaryError, setDocumentSummaryError] = useState('');
    const [audioUrl, setAudioUrl] = useState(null);
    const [summaryCache, setSummaryCache] = useState(new Map());
    const [podcastCache, setPodcastCache] = useState(new Map());

    // Podcast generation progress state
    const [generatingPodcast, setGeneratingPodcast] = useState(false);
    const [podcastProgress, setPodcastProgress] = useState(0);
    const [podcastProgressMessage, setPodcastProgressMessage] = useState('');

    // Collapsible states
    const [selectionSectionExpanded, setSelectionSectionExpanded] = useState(false);
    const [documentSectionExpanded, setDocumentSectionExpanded] = useState(false);

    // WebSocket reference for cleanup
    const [wsRef, setWsRef] = useState(null);

    // Reset summaries and manage expanded states when active document changes
    useEffect(() => {
        if (activeDocumentId) {
            // Check if we have cached summaries for this document
            const selectionCacheKey = `${activeDocumentId}_selection`;
            const documentCacheKey = `${activeDocumentId}_document`;
            const podcastCacheKey = `${sessionId}_${activeDocumentId}`;

            const cachedSelectionSummary = summaryCache.get(selectionCacheKey);
            const cachedDocumentSummary = summaryCache.get(documentCacheKey);
            const cachedPodcast = podcastCache.get(podcastCacheKey);

            if (cachedSelectionSummary) {
                const summaryText = typeof cachedSelectionSummary === 'string'
                    ? cachedSelectionSummary
                    : JSON.stringify(cachedSelectionSummary, null, 2);
                setSelectionSummary(summaryText);
                setSelectionSummaryError('');
            } else {
                setSelectionSummary('');
                setSelectionSummaryError('');
            }

            if (cachedDocumentSummary) {
                const summaryText = typeof cachedDocumentSummary === 'string'
                    ? cachedDocumentSummary
                    : JSON.stringify(cachedDocumentSummary, null, 2);
                setDocumentSummary(summaryText);
                setDocumentSummaryError('');
                setDocumentSectionExpanded(true); // Auto-expand if summary exists
            } else {
                setDocumentSummary('');
                setDocumentSummaryError('');
                setDocumentSectionExpanded(false); // Collapsed by default
            }

            // Reset audio URL when document changes, or set cached podcast
            if (cachedPodcast) {
                setAudioUrl(cachedPodcast);
            } else {
                setAudioUrl(null);
            }
        }
    }, [activeDocumentId, summaryCache, podcastCache, sessionId]);

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (wsRef) {
                wsRef.close();
            }
        };
    }, [wsRef]);

    // Manage selection section expansion based on selected text and existing summary
    useEffect(() => {
        if (selectedText && selectedText.trim().length > 0) {
            // If text is selected and no cached summary exists, expand the section
            const selectionCacheKey = `${activeDocumentId}_selection`;
            const cachedSelectionSummary = summaryCache.get(selectionCacheKey);

            if (!cachedSelectionSummary) {
                setSelectionSectionExpanded(true);
            }
        } else {
            // If no text selected, check if we have a cached summary to decide expansion
            const selectionCacheKey = `${activeDocumentId}_selection`;
            const cachedSelectionSummary = summaryCache.get(selectionCacheKey);

            if (!cachedSelectionSummary) {
                setSelectionSectionExpanded(false);
            }
        }
    }, [selectedText, activeDocumentId, summaryCache]);

    const handleSummarizeSelection = async () => {
        if (!selectedText || selectedText.trim().length === 0) {
            setSelectionSummaryError('No text selected for summarization');
            return;
        }

        setGeneratingSelection(true);
        setSelectionSummary(''); // Clear previous summary
        setSelectionSummaryError(''); // Clear previous errors

        // Set a timeout for the summary generation
        const timeoutId = setTimeout(() => {
            setGeneratingSelection(false);
            setSelectionSummaryError('Summary generation is taking longer than expected. Please try again.');
        }, 45000); // 45 second timeout

        try {
            console.log('Generating selection summary...');

            const result = await generateSummary(sessionId, selectedText, 'selection', activeDocumentId);

            // Clear the timeout since we got a response
            clearTimeout(timeoutId);

            // Debug logging to understand response structure
            console.log('Selection summary result:', result);
            console.log('Selection summary type:', typeof result.summary);
            console.log('Selection summary content:', result.summary);

            // Ensure the summary is a string, not an object
            const summaryText = typeof result.summary === 'string'
                ? result.summary
                : typeof result.summary === 'object'
                    ? JSON.stringify(result.summary, null, 2)
                    : String(result.summary);

            setSelectionSummary(summaryText);

            // Cache the summary for this document/selection combination
            const cacheKey = `${activeDocumentId}_selection`;
            setSummaryCache(prev => new Map(prev.set(cacheKey, summaryText)));

            console.log('Selection summary generated successfully:', result);

        } catch (error) {
            // Clear the timeout since we got an error response
            clearTimeout(timeoutId);

            console.error('Failed to generate selection summary:', error);
            setSelectionSummaryError(error.message || 'Failed to generate summary. Please try again.');
        } finally {
            setGeneratingSelection(false);
        }
    };

    const handleSummarizeDocument = async () => {
        if (!activeDocument || !activeDocumentId) {
            setDocumentSummaryError('No document available for summarization');
            return;
        }

        setGeneratingDocument(true);
        setDocumentSummary(''); // Clear previous summary
        setDocumentSummaryError(''); // Clear previous errors

        // Set a timeout for the summary generation
        const timeoutId = setTimeout(() => {
            setGeneratingDocument(false);
            setDocumentSummaryError('Summary generation is taking longer than expected. Please try again.');
        }, 45000); // 45 second timeout

        try {
            console.log('Generating document summary...');

            // For document mode, just pass a placeholder - backend will fetch full content
            const content = `Document: ${activeDocument.title || activeDocument.original_filename}`;

            const result = await generateSummary(sessionId, content, 'document', activeDocumentId);

            // Clear the timeout since we got a response
            clearTimeout(timeoutId);

            // Debug logging to understand response structure
            console.log('Document summary result:', result);
            console.log('Document summary type:', typeof result.summary);
            console.log('Document summary content:', result.summary);

            // Ensure the summary is a string, not an object
            const summaryText = typeof result.summary === 'string'
                ? result.summary
                : typeof result.summary === 'object'
                    ? JSON.stringify(result.summary, null, 2)
                    : String(result.summary);

            setDocumentSummary(summaryText);

            // Cache the summary for this document
            const cacheKey = `${activeDocumentId}_document`;
            setSummaryCache(prev => new Map(prev.set(cacheKey, summaryText)));

            console.log('Document summary generated successfully:', result);

        } catch (error) {
            // Clear the timeout since we got an error response
            clearTimeout(timeoutId);

            console.error('Failed to generate document summary:', error);
            setDocumentSummaryError(error.message || 'Failed to generate summary. Please try again.');
        } finally {
            setGeneratingDocument(false);
        }
    };

    const handleGeneratePodcast = async () => {
        // Check if we already have a cached podcast for this session/document
        const podcastCacheKey = activeDocumentId ? `${sessionId}_${activeDocumentId}` : sessionId;
        const cachedPodcast = podcastCache.get(podcastCacheKey);

        if (cachedPodcast) {
            setAudioUrl(cachedPodcast);
            console.log('Using cached podcast:', cachedPodcast);
            return;
        }

        setGeneratingPodcast(true);
        // Remove this line that was causing interference: setGeneratingDocument(true);
        setPodcastProgress(0);
        setPodcastProgressMessage('Starting podcast generation...');

        // Set up WebSocket for progress updates
        let ws = null;
        if (sessionId) {
            try {
                ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
                setWsRef(ws);

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'processing_update') {
                            const { status, message } = data;

                            // Update progress based on status
                            switch (status) {
                                case 'started':
                                    setPodcastProgress(15);
                                    setPodcastProgressMessage(message || 'Initializing podcast generation...');
                                    break;
                                case 'processing':
                                    // Determine sub-stage based on message content
                                    if (message && message.includes('insights')) {
                                        setPodcastProgress(35);
                                        setPodcastProgressMessage('Analyzing content and generating insights...');
                                    } else if (message && message.includes('audio')) {
                                        setPodcastProgress(70);
                                        setPodcastProgressMessage('Converting text to speech...');
                                    } else {
                                        setPodcastProgress(50);
                                        setPodcastProgressMessage(message || 'Processing content...');
                                    }
                                    break;
                                case 'completed':
                                    setPodcastProgress(100);
                                    setPodcastProgressMessage(message || 'Podcast generation complete!');
                                    break;
                                default:
                                    // Gradual progress increase for unknown states
                                    setPodcastProgress(prev => Math.min(prev + 5, 85));
                                    setPodcastProgressMessage(message || 'Processing...');
                            }
                        }
                    } catch (e) {
                        console.warn('Failed to parse WebSocket message:', e);
                    }
                };

                ws.onerror = (error) => {
                    console.warn('WebSocket error:', error);
                };
            } catch (error) {
                console.warn('Failed to establish WebSocket connection:', error);
            }
        }

        try {
            if (!sessionId) {
                console.error('No session ID available');
                return;
            }

            // Prepare podcast request
            const podcastRequest = {
                use_insights: true,
                use_dual_speaker: true,
                include_selection: !!selectedText
            };

            // If there's selected text, prioritize it as content
            if (selectedText) {
                podcastRequest.content = selectedText;
                console.log('Using selected text for podcast');
            }
            // Only include document_id if we have an active document AND no selected text
            else if (activeDocumentId) {
                podcastRequest.document_id = activeDocumentId;
                console.log('Using active document for podcast:', activeDocumentId);
            }
            // Otherwise, let the backend use all available content or demo content

            console.log('Generating podcast with request:', podcastRequest);

            // Call the backend API
            const response = await fetch(`http://localhost:8000/session/${sessionId}/podcast/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(podcastRequest),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Podcast generated:', result);

            // Set the audio URL for playback
            setAudioUrl(result.audio_url);

            // Cache the podcast
            const podcastCacheKey = activeDocumentId ? `${sessionId}_${activeDocumentId}` : sessionId;
            setPodcastCache(prev => new Map(prev.set(podcastCacheKey, result.audio_url)));

            // Final progress update
            setPodcastProgress(100);
            setPodcastProgressMessage('Podcast ready for playback!');

        } catch (error) {
            console.error('Failed to generate podcast:', error);
            setPodcastProgress(0);
            setPodcastProgressMessage('Failed to generate podcast');
            alert(`Failed to generate podcast: ${error.message}`);
        } finally {
            setGeneratingPodcast(false);
            // Remove this line that was causing interference: setGeneratingDocument(false);

            // Close WebSocket connection
            if (ws) {
                ws.close();
                setWsRef(null);
            }

            // Clear progress after a delay
            setTimeout(() => {
                if (!generatingPodcast) {
                    setPodcastProgress(0);
                    setPodcastProgressMessage('');
                }
            }, 3000);
        }
    };

    const handleCopySelection = () => {
        if (selectionSummary) {
            navigator.clipboard.writeText(selectionSummary);
        }
    };

    const handleCopyDocument = () => {
        if (documentSummary) {
            navigator.clipboard.writeText(documentSummary);
        }
    };

    const handleDownloadSelection = () => {
        if (selectionSummary) {
            const blob = new Blob([selectionSummary], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `selection-summary-${activeDocument?.title || 'document'}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    const handleDownloadDocument = () => {
        if (documentSummary) {
            const blob = new Blob([documentSummary], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `document-summary-${activeDocument?.title || 'document'}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center">
                <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                    <FileText className="h-5 w-5 mr-2 text-orange-600" />
                    Actions
                </h3>
            </div>

            {!activeDocumentId ? (
                <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Select a document to see available actions</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {/* Selection Summary Section */}
                    <div className="bg-white border border-gray-200 rounded-lg">
                        <div
                            className="p-4 cursor-pointer hover:bg-gray-50 transition-colors duration-200"
                            onClick={() => setSelectionSectionExpanded(!selectionSectionExpanded)}
                        >
                            <div className="flex items-center justify-between">
                                <h4 className="font-medium text-gray-700">
                                    📝 Summarize Selection
                                </h4>
                                {selectionSectionExpanded ? (
                                    <ChevronUp className="h-4 w-4 text-gray-500" />
                                ) : (
                                    <ChevronDown className="h-4 w-4 text-gray-500" />
                                )}
                            </div>
                        </div>

                        {selectionSectionExpanded && (
                            <div className="px-4 pb-4 border-t border-gray-100">
                                <div className="pt-4">
                                    {!selectedText || selectedText.trim().length === 0 ? (
                                        <div className="text-center py-6 text-gray-500">
                                            <FileText className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                                            <p className="text-sm">Select text in the document to summarize</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-gray-600">Selected text ready for summarization</span>
                                                <button
                                                    onClick={handleSummarizeSelection}
                                                    disabled={generatingSelection}
                                                    className={`
                                                        px-3 py-1 rounded-md text-sm font-medium transition-colors
                                                        ${generatingSelection
                                                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                            : 'bg-blue-600 text-white hover:bg-blue-700'
                                                        }
                                                    `}
                                                >
                                                    {generatingSelection ? 'Generating...' : 'Generate Summary'}
                                                </button>
                                            </div>

                                            <div className="p-3 bg-blue-50 rounded-lg">
                                                <p className="text-sm text-blue-800 font-medium mb-1">Selected Text:</p>
                                                <p className="text-sm text-blue-700">
                                                    "{selectedText.length > 150 ? selectedText.substring(0, 150) + '...' : selectedText}"
                                                </p>
                                            </div>

                                            {/* Loading Animation */}
                                            {generatingSelection && (
                                                <div className="p-4 bg-blue-50 rounded-lg">
                                                    <div className="flex items-center space-x-3">
                                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                                                        <div className="flex-1">
                                                            <p className="text-sm font-medium text-blue-800">Generating Selection Summary...</p>
                                                            <p className="text-xs text-blue-600">Analyzing selected text</p>
                                                        </div>
                                                    </div>
                                                    <div className="mt-3">
                                                        <div className="w-full bg-blue-200 rounded-full h-1">
                                                            <div className="bg-blue-600 h-1 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Error Display */}
                                            {selectionSummaryError && !generatingSelection && (
                                                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                                    <div className="flex items-start space-x-2">
                                                        <div className="flex-shrink-0">
                                                            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                                            </svg>
                                                        </div>
                                                        <div className="flex-1">
                                                            <p className="text-sm font-medium text-red-800">Selection Summary Failed</p>
                                                            <p className="text-sm text-red-600 mt-1">{selectionSummaryError}</p>
                                                            <button
                                                                onClick={handleSummarizeSelection}
                                                                className="mt-2 text-sm text-red-700 hover:text-red-900 underline"
                                                            >
                                                                Try Again
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Success Summary Display */}
                                            {selectionSummary && !generatingSelection && !selectionSummaryError && (
                                                <div className="space-y-3">
                                                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                                                        <div className="flex items-center space-x-2 mb-2">
                                                            <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                            </svg>
                                                            <p className="text-sm font-medium text-green-800">Selection Summary Generated</p>
                                                        </div>
                                                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                                            {typeof selectionSummary === 'string'
                                                                ? selectionSummary
                                                                : JSON.stringify(selectionSummary, null, 2)
                                                            }
                                                        </p>
                                                    </div>

                                                    <div className="flex space-x-2">
                                                        <button
                                                            onClick={handleCopySelection}
                                                            className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                                                        >
                                                            <Copy className="h-4 w-4 mr-1" />
                                                            Copy
                                                        </button>
                                                        <button
                                                            onClick={handleDownloadSelection}
                                                            className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                                                        >
                                                            <Download className="h-4 w-4 mr-1" />
                                                            Download
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Document Summary Section */}
                    <div className="bg-white border border-gray-200 rounded-lg">
                        <div
                            className="p-4 cursor-pointer hover:bg-gray-50 transition-colors duration-200"
                            onClick={() => setDocumentSectionExpanded(!documentSectionExpanded)}
                        >
                            <div className="flex items-center justify-between">
                                <h4 className="font-medium text-gray-700 text-sm truncate pr-2">
                                    📄 Summarize - {activeDocument && (
                                        activeDocument.title || activeDocument.original_filename
                                    )}
                                </h4>
                                {documentSectionExpanded ? (
                                    <ChevronUp className="h-4 w-4 text-gray-500 flex-shrink-0" />
                                ) : (
                                    <ChevronDown className="h-4 w-4 text-gray-500 flex-shrink-0" />
                                )}
                            </div>
                        </div>

                        {documentSectionExpanded && (
                            <div className="px-4 pb-4 border-t border-gray-100">
                                <div className="pt-4">
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-gray-600">Generate summary of entire document</span>
                                            <button
                                                onClick={handleSummarizeDocument}
                                                disabled={generatingDocument}
                                                className={`
                                                    px-3 py-1 rounded-md text-sm font-medium transition-colors
                                                    ${generatingDocument
                                                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                        : 'bg-purple-600 text-white hover:bg-purple-700'
                                                    }
                                                `}
                                            >
                                                {generatingDocument ? 'Generating...' : 'Generate Summary'}
                                            </button>
                                        </div>

                                        {/* Loading Animation */}
                                        {generatingDocument && (
                                            <div className="p-4 bg-green-50 rounded-lg">
                                                <div className="flex items-center space-x-3">
                                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600"></div>
                                                    <div className="flex-1">
                                                        <p className="text-sm font-medium text-green-800">Generating Document Summary...</p>
                                                        <p className="text-xs text-green-600">Processing document content</p>
                                                    </div>
                                                </div>
                                                <div className="mt-3">
                                                    <div className="w-full bg-green-200 rounded-full h-1">
                                                        <div className="bg-green-600 h-1 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Error Display */}
                                        {documentSummaryError && !generatingDocument && (
                                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                                <div className="flex items-start space-x-2">
                                                    <div className="flex-shrink-0">
                                                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex-1">
                                                        <p className="text-sm font-medium text-red-800">Document Summary Failed</p>
                                                        <p className="text-sm text-red-600 mt-1">{documentSummaryError}</p>
                                                        <button
                                                            onClick={handleSummarizeDocument}
                                                            className="mt-2 text-sm text-red-700 hover:text-red-900 underline"
                                                        >
                                                            Try Again
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Success Summary Display */}
                                        {documentSummary && !generatingDocument && !documentSummaryError && (
                                            <div className="space-y-3">
                                                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                                                    <div className="flex items-center space-x-2 mb-2">
                                                        <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                        </svg>
                                                        <p className="text-sm font-medium text-green-800">Document Summary Generated</p>
                                                    </div>
                                                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                                        {typeof documentSummary === 'string'
                                                            ? documentSummary
                                                            : JSON.stringify(documentSummary, null, 2)
                                                        }
                                                    </p>
                                                </div>

                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={handleCopyDocument}
                                                        className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                                                    >
                                                        <Copy className="h-4 w-4 mr-1" />
                                                        Copy
                                                    </button>
                                                    <button
                                                        onClick={handleDownloadDocument}
                                                        className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                                                    >
                                                        <Download className="h-4 w-4 mr-1" />
                                                        Download
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Podcast Generation */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <h4 className="font-medium text-gray-700">Generate Podcast</h4>
                                {/* Cache indicator commented out
                                {(() => {
                                    const podcastCacheKey = activeDocumentId ? `${sessionId}_${activeDocumentId}` : sessionId;
                                    const isCached = podcastCache.has(podcastCacheKey);
                                    return isCached ? (
                                        <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                                            Cached
                                        </span>
                                    ) : null;
                                })()}
                                */}
                            </div>
                            <button
                                onClick={handleGeneratePodcast}
                                disabled={generatingPodcast}
                                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${generatingPodcast
                                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                        : 'bg-green-600 text-white hover:bg-green-700'
                                    }
                `}
                            >
                                {generatingPodcast ? 'Generating...' : 'Generate'}
                            </button>
                        </div>

                        {/* Progress Bar */}
                        {generatingPodcast && (
                            <div className="mb-4 bg-gray-50 rounded-lg p-3 border">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-medium text-gray-700">
                                        {podcastProgressMessage || 'Generating podcast...'}
                                    </span>
                                    <span className="text-sm text-gray-500 font-mono">
                                        {Math.round(podcastProgress)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-700 ease-out relative"
                                        style={{ width: `${podcastProgress}%` }}
                                    >
                                        {generatingPodcast && podcastProgress > 0 && podcastProgress < 100 && (
                                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
                                        )}
                                    </div>
                                </div>
                                {podcastProgress < 100 && (
                                    <p className="text-xs text-gray-500 mt-2">
                                        This may take 30-60 seconds for quality audio generation...
                                    </p>
                                )}
                            </div>
                        )}

                        <p className="text-sm text-gray-600 mb-3">
                            Create an AI-generated podcast from this document with natural conversation flow.
                        </p>

                        {audioUrl && (
                            <div className="space-y-3">
                                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                    <div className="flex items-center mb-2">
                                        <Volume2 className="h-4 w-4 text-green-600 mr-2" />
                                        <span className="text-sm font-medium text-green-800">Podcast Ready!</span>
                                    </div>

                                    {/* HTML5 Audio Player */}
                                    <div className="bg-white rounded-lg p-3 border">
                                        <audio
                                            controls
                                            className="w-full"
                                            preload="metadata"
                                        >
                                            <source src={audioUrl} type="audio/mpeg" />
                                            Your browser does not support the audio element.
                                        </audio>

                                        <div className="flex justify-between items-center mt-2">
                                            <span className="text-xs text-gray-500">AI-Generated Podcast</span>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => {
                                                        const podcastCacheKey = activeDocumentId ? `${sessionId}_${activeDocumentId}` : sessionId;
                                                        setPodcastCache(prev => {
                                                            const newCache = new Map(prev);
                                                            newCache.delete(podcastCacheKey);
                                                            return newCache;
                                                        });
                                                        setAudioUrl(null);
                                                    }}
                                                    className="text-xs text-red-600 hover:text-red-700"
                                                    title="Clear cached podcast"
                                                >
                                                    Clear Cache
                                                </button>
                                                <a
                                                    href={audioUrl}
                                                    download
                                                    className="flex items-center text-xs text-green-600 hover:text-green-700"
                                                >
                                                    <Download className="h-3 w-3 mr-1" />
                                                    Download
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Document Info */}
                    {/* <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <h4 className="font-medium text-gray-700 mb-3">Document Info</h4>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Title:</span>
                                <span className="text-gray-800 font-medium">{activeDocument?.title}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Pages:</span>
                                <span className="text-gray-800">{activeDocument?.total_pages || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Status:</span>
                                <span className={`
                  font-medium
                  ${activeDocument?.processing_status === 'completed'
                                        ? 'text-green-600'
                                        : activeDocument?.processing_status === 'processing'
                                            ? 'text-yellow-600'
                                            : 'text-red-600'
                                    }
                `}>
                                    {activeDocument?.processing_status || 'Unknown'}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Uploaded:</span>
                                <span className="text-gray-800">
                                    {activeDocument?.upload_timestamp
                                        ? new Date(activeDocument.upload_timestamp).toLocaleDateString()
                                        : 'Unknown'
                                    }
                                </span>
                            </div>
                        </div>
                    </div> */}

                    {/* Quick Actions */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <h4 className="font-medium text-gray-700 mb-3">Quick Actions</h4>
                        <div className="grid grid-cols-2 gap-2">
                            <button className="flex items-center justify-center px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">
                                <Share className="h-4 w-4 mr-1" />
                                Share
                            </button>
                            <button className="flex items-center justify-center px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">
                                <Download className="h-4 w-4 mr-1" />
                                Export
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ActionControlsPanel;
