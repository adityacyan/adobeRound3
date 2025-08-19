import React, { useState } from 'react';
import { FileText, Download, Play, Volume2, Copy, Share } from 'lucide-react';
import { generateSummary } from '../../services/api';

const ActionControlsPanel = ({
    sessionId,
    activeDocumentId,
    selectedText,
    activeDocument
}) => {
    const [generating, setGenerating] = useState(false);
    const [summary, setSummary] = useState('');
    const [summaryError, setSummaryError] = useState('');
    const [audioUrl, setAudioUrl] = useState(null);

    const handleSummarize = async () => {
        setGenerating(true);
        setSummary(''); // Clear previous summary
        setSummaryError(''); // Clear previous errors

        // Set a timeout for the summary generation
        const timeoutId = setTimeout(() => {
            setGenerating(false);
            setSummaryError('Summary generation is taking longer than expected. Please try again.');
        }, 45000); // 45 second timeout

        try {
            let content = '';
            let mode = 'document';

            if (selectedText && selectedText.trim().length > 0) {
                content = selectedText;
                mode = 'selection';
            } else if (activeDocument && activeDocumentId) {
                // For document mode, just pass a placeholder - backend will fetch full content
                content = `Document: ${activeDocument.title || activeDocument.original_filename}`;
                mode = 'document';
            } else {
                throw new Error('No document available for summarization');
            }

            console.log(`Generating ${mode} summary...`);

            const result = await generateSummary(sessionId, content, mode, activeDocumentId);

            // Clear the timeout since we got a response
            clearTimeout(timeoutId);

            setSummary(result.summary);
            console.log('Summary generated successfully:', result);

        } catch (error) {
            // Clear the timeout since we got an error response
            clearTimeout(timeoutId);

            console.error('Failed to generate summary:', error);
            setSummaryError(error.message || 'Failed to generate summary. Please try again.');
        } finally {
            setGenerating(false);
        }
    };

    const handleGeneratePodcast = async () => {
        setGenerating(true);

        try {
            // Simulate podcast generation
            await new Promise(resolve => setTimeout(resolve, 3000));

            // This would normally call the backend to generate audio
            setAudioUrl('demo-podcast.mp3'); // Demo URL
        } catch (error) {
            console.error('Failed to generate podcast:', error);
        } finally {
            setGenerating(false);
        }
    };

    const handleCopy = () => {
        if (summary) {
            navigator.clipboard.writeText(summary);
        }
    };

    const handleDownload = () => {
        if (summary) {
            const blob = new Blob([summary], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `summary-${activeDocument?.title || 'document'}.txt`;
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
                    {/* Summary Section */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium text-gray-700">
                                {selectedText ? 'Summarize Selection' : 'Summarize Document'}
                            </h4>
                            <button
                                onClick={handleSummarize}
                                disabled={generating}
                                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${generating
                                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                        : 'bg-blue-600 text-white hover:bg-blue-700'
                                    }
                `}
                            >
                                {generating ? 'Generating...' : 'Generate'}
                            </button>
                        </div>

                        {selectedText && (
                            <div className="mb-3 p-3 bg-blue-50 rounded-lg">
                                <p className="text-sm text-blue-800 font-medium mb-1">Selected Text:</p>
                                <p className="text-sm text-blue-700">
                                    "{selectedText.length > 150 ? selectedText.substring(0, 150) + '...' : selectedText}"
                                </p>
                            </div>
                        )}

                        {/* Loading Animation */}
                        {generating && (
                            <div className="p-4 bg-blue-50 rounded-lg">
                                <div className="flex items-center space-x-3">
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-blue-800">Generating Summary...</p>
                                        <p className="text-xs text-blue-600">
                                            {selectedText ? 'Analyzing selected text' : 'Processing document content'}
                                        </p>
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
                        {summaryError && !generating && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                <div className="flex items-start space-x-2">
                                    <div className="flex-shrink-0">
                                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-red-800">Summary Generation Failed</p>
                                        <p className="text-sm text-red-600 mt-1">{summaryError}</p>
                                        <button
                                            onClick={handleSummarize}
                                            className="mt-2 text-sm text-red-700 hover:text-red-900 underline"
                                        >
                                            Try Again
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Success Summary Display */}
                        {summary && !generating && !summaryError && (
                            <div className="space-y-3">
                                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <p className="text-sm font-medium text-green-800">Summary Generated</p>
                                    </div>
                                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{summary}</p>
                                </div>

                                <div className="flex space-x-2">
                                    <button
                                        onClick={handleCopy}
                                        className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                                    >
                                        <Copy className="h-4 w-4 mr-1" />
                                        Copy
                                    </button>
                                    <button
                                        onClick={handleDownload}
                                        className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                                    >
                                        <Download className="h-4 w-4 mr-1" />
                                        Download
                                    </button>
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
                                disabled={generating}
                                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${generating
                                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                        : 'bg-green-600 text-white hover:bg-green-700'
                                    }
                `}
                            >
                                {generating ? 'Generating...' : 'Generate'}
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
