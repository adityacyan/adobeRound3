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

    // Collapsible states
    const [selectionSectionExpanded, setSelectionSectionExpanded] = useState(false);
    const [documentSectionExpanded, setDocumentSectionExpanded] = useState(false);

    // Reset summaries and manage expanded states when active document changes
    useEffect(() => {
        if (activeDocumentId) {
            // Check if we have cached summaries for this document
            const selectionCacheKey = `${activeDocumentId}_selection`;
            const documentCacheKey = `${activeDocumentId}_document`;

            const cachedSelectionSummary = summaryCache.get(selectionCacheKey);
            const cachedDocumentSummary = summaryCache.get(documentCacheKey);

            if (cachedSelectionSummary) {
                setSelectionSummary(cachedSelectionSummary);
                setSelectionSummaryError('');
            } else {
                setSelectionSummary('');
                setSelectionSummaryError('');
            }

            if (cachedDocumentSummary) {
                setDocumentSummary(cachedDocumentSummary);
                setDocumentSummaryError('');
                setDocumentSectionExpanded(true); // Auto-expand if summary exists
            } else {
                setDocumentSummary('');
                setDocumentSummaryError('');
                setDocumentSectionExpanded(false); // Collapsed by default
            }

            // Reset audio URL when document changes
            setAudioUrl(null);
        }
    }, [activeDocumentId, summaryCache]);

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

            setSelectionSummary(result.summary);

            // Cache the summary for this document/selection combination
            const cacheKey = `${activeDocumentId}_selection`;
            setSummaryCache(prev => new Map(prev.set(cacheKey, result.summary)));

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

            setDocumentSummary(result.summary);

            // Cache the summary for this document
            const cacheKey = `${activeDocumentId}_document`;
            setSummaryCache(prev => new Map(prev.set(cacheKey, result.summary)));

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
        setGeneratingDocument(true);

        try {
            // Simulate podcast generation
            await new Promise(resolve => setTimeout(resolve, 3000));

            // This would normally call the backend to generate audio
            setAudioUrl('demo-podcast.mp3'); // Demo URL
        } catch (error) {
            console.error('Failed to generate podcast:', error);
        } finally {
            setGeneratingDocument(false);
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
                                                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectionSummary}</p>
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
                                                        : 'bg-green-600 text-white hover:bg-green-700'
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
                                                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{documentSummary}</p>
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
                            <h4 className="font-medium text-gray-700">Generate Podcast</h4>
                            <button
                                onClick={handleGeneratePodcast}
                                disabled={generatingDocument}
                                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${generatingDocument
                                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                        : 'bg-green-600 text-white hover:bg-green-700'
                                    }
                `}
                            >
                                {generatingDocument ? 'Generating...' : 'Generate'}
                            </button>
                        </div>

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

                                    {/* Audio Player (Demo) */}
                                    <div className="bg-white rounded-lg p-3 border">
                                        <div className="flex items-center space-x-3">
                                            <button className="p-2 bg-green-600 text-white rounded-full hover:bg-green-700">
                                                <Play className="h-4 w-4" />
                                            </button>
                                            <div className="flex-1">
                                                <div className="w-full bg-gray-200 rounded-full h-2">
                                                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '0%' }}></div>
                                                </div>
                                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                                    <span>0:00</span>
                                                    <span>5:23</span>
                                                </div>
                                            </div>
                                            <button className="p-2 text-gray-600 hover:text-gray-800">
                                                <Download className="h-4 w-4" />
                                            </button>
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
