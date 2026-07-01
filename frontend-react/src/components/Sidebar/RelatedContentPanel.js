import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, FileText, Clock, AlertCircle } from 'lucide-react';
import { searchRelatedContent } from '../../services/api';

// Retry config: attempts at 3s, 6s, 12s, 24s, 48s (capped at 5 retries)
const RETRY_DELAYS_MS = [3000, 6000, 12000, 24000, 48000];

const RelatedContentPanel = ({
    sessionId,
    selectedText,
    relatedContent,
    setRelatedContent,
    documents,
    onNavigateToContent
}) => {
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState(null);
    const [lastSearchText, setLastSearchText] = useState('');
    const [waitingForProcessing, setWaitingForProcessing] = useState(false);

    // Keep refs so retry callbacks always have fresh values without re-triggering effects
    const retryTimerRef = useRef(null);
    const retryAttemptRef = useRef(0);
    const activeSearchTextRef = useRef('');

    const cancelRetry = useCallback(() => {
        if (retryTimerRef.current) {
            clearTimeout(retryTimerRef.current);
            retryTimerRef.current = null;
        }
        retryAttemptRef.current = 0;
        setWaitingForProcessing(false);
    }, []);

    // Cancel any pending retry when selected text changes or component unmounts
    useEffect(() => {
        return () => cancelRetry();
    }, [cancelRetry]);

    useEffect(() => {
        if (selectedText && selectedText !== lastSearchText && selectedText.length > 5) {
            cancelRetry();
            handleSearch(selectedText);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedText]);

    const scheduleRetry = useCallback((text) => {
        const attempt = retryAttemptRef.current;
        if (attempt >= RETRY_DELAYS_MS.length) {
            // Exhausted retries — give up and surface a user-friendly message
            setWaitingForProcessing(false);
            setSearching(false);
            setError('Documents are still processing. Please try again in a moment.');
            return;
        }

        const delay = RETRY_DELAYS_MS[attempt];
        console.log(`Search queued: documents still processing. Retrying in ${delay / 1000}s (attempt ${attempt + 1}/${RETRY_DELAYS_MS.length})`);
        retryAttemptRef.current = attempt + 1;
        setWaitingForProcessing(true);
        setSearching(false);

        retryTimerRef.current = setTimeout(() => {
            // Only retry if the user hasn't changed the selected text in the meantime
            if (activeSearchTextRef.current === text) {
                handleSearch(text, true);
            }
        }, delay);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleSearch = async (text, isRetry = false) => {
        if (!sessionId || !text || text.length < 5) return;

        if (!isRetry) {
            retryAttemptRef.current = 0;
        }

        activeSearchTextRef.current = text;

        console.log('Starting related content search:', {
            sessionId: sessionId.substring(0, 8) + '...',
            selectedText: text.substring(0, 100),
            documentsAvailable: documents.length,
            isRetry
        });

        setSearching(true);
        setError(null);
        setLastSearchText(text);
        setWaitingForProcessing(false);

        try {
            const result = await searchRelatedContent(sessionId, text);

            console.log('Search result received:', {
                totalResults: result.total_results,
                relatedSections: result.related_sections?.length || 0,
                searchTimeMs: result.search_time_ms,
                documentsStillProcessing: result.documents_still_processing
            });

            if (result.related_sections && result.related_sections.length > 0) {
                setRelatedContent(result.related_sections);
                setError(null);
                cancelRetry();
            } else if (result.documents_still_processing) {
                // Documents aren't ready yet — queue a retry instead of failing
                setRelatedContent([]);
                scheduleRetry(text);
            } else {
                const message = result.message || result.processing_note || 'No related content found';
                setError(message);
                setRelatedContent([]);
                cancelRetry();
            }
        } catch (err) {
            console.error('Search failed:', err);
            const errorMessage = err.response?.data?.detail || err.message || 'Search failed. Please try again.';
            setError(errorMessage);
            setRelatedContent([]);
            cancelRetry();
        } finally {
            setSearching(false);
        }
    };

    const handleManualSearch = () => {
        if (selectedText) {
            cancelRetry();
            handleSearch(selectedText);
        }
    };

    const getDocumentTitle = (documentId) => {
        const doc = documents.find(d => d.document_id === documentId);
        return doc?.title || `Document ${documentId.substring(0, 8)}`;
    };

    const getConfidenceColor = (score) => {
        if (score >= 0.8) return 'text-green-600 bg-green-100';
        if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
        return 'text-red-600 bg-red-100';
    };

    const handleContentClick = (section) => {
        console.log('🔗 Navigating to related content:', {
            documentId: section.document_id,
            pageNumber: section.page_number,
            snippet: section.snippet?.substring(0, 50) + '...'
        });

        if (onNavigateToContent) {
            // Extract the most relevant text to highlight from the snippet
            const highlightText = section.snippet || section.text || selectedText;

            // Navigate to the document and page with highlighting
            onNavigateToContent(
                section.document_id,
                section.page_number,
                highlightText.substring(0, 100) // Limit highlight text length
            );
        } else {
            console.warn('Navigation function not available');
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                    <Search className="h-5 w-5 mr-2 text-purple-600" />
                    Related Content
                </h3>
                {selectedText && (
                    <button
                        onClick={handleManualSearch}
                        disabled={searching}
                        className={`
              p-2 rounded-lg transition-colors text-sm
              ${searching
                                ? 'text-gray-400 cursor-not-allowed'
                                : 'text-gray-600 hover:bg-gray-100'
                            }
            `}
                        title="Search again"
                    >
                        <Search className={`h-4 w-4 ${searching ? 'animate-pulse' : ''}`} />
                    </button>
                )}
            </div>

            {/* Status indicator */}
            <div className="text-xs text-gray-600 p-2 bg-gray-50 rounded border">
                <div className="flex justify-between">
                    <span>Session: {sessionId ? '✅ Connected' : '❌ No session'}</span>
                    <span>Docs: {documents.length}</span>
                </div>
                {lastSearchText && (
                    <div className="mt-1 text-gray-500">
                        Last: "{lastSearchText.substring(0, 30)}..."
                    </div>
                )}
            </div>

            {!selectedText ? (
                <div className="text-center py-8">
                    <Search className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm leading-relaxed">
                        Select text in the PDF above to find related content across all documents
                    </p>
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                        <p className="text-blue-700 text-xs">
                            <strong>Tip:</strong> Highlight any text in the PDF and related sections will appear here automatically!
                        </p>
                    </div>
                </div>
            ) : searching ? (
                <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-3"></div>
                    <p className="text-gray-600 font-medium">Searching related content...</p>
                    <p className="text-sm text-gray-500 mt-1">
                        Looking for: "{selectedText.substring(0, 50)}..."
                    </p>
                </div>
            ) : waitingForProcessing ? (
                <div className="text-center py-8">
                    <Clock className="h-12 w-12 text-yellow-400 mx-auto mb-3" />
                    <p className="text-gray-600 font-medium">Documents are still processing</p>
                    <p className="text-sm text-gray-500 mt-1">
                        Your search has been queued and will run automatically once processing completes.
                    </p>
                    <button
                        onClick={handleManualSearch}
                        className="mt-3 text-sm text-purple-600 hover:text-purple-700 underline"
                    >
                        Search now anyway
                    </button>
                </div>
            ) : error ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center">
                        <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                        <span className="text-red-700 text-sm">{error}</span>
                    </div>
                    <button
                        onClick={handleManualSearch}
                        className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
                    >
                        Try again
                    </button>
                </div>
            ) : relatedContent.length > 0 ? (
                <div className="space-y-4">
                    {/* Search Query Display */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                        <h4 className="text-sm font-medium text-purple-800 mb-1">Search Query:</h4>
                        <p className="text-sm text-purple-700">
                            "{selectedText.length > 100 ? selectedText.substring(0, 100) + '...' : selectedText}"
                        </p>
                    </div>

                    {/* Results */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <h4 className="text-sm font-medium text-gray-700">
                                Found {relatedContent.length} related section{relatedContent.length > 1 ? 's' : ''}
                            </h4>
                        </div>

                        {relatedContent.map((section, index) => (
                            <div
                                key={index}
                                className="border-2 border-gray-300 rounded-lg p-3 hover:bg-blue-50 hover:border-blue-400 transition-all duration-200 cursor-pointer group hover:shadow-lg bg-white"
                                onClick={() => handleContentClick(section)}
                            >
                                {/* Header with document info */}
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center text-xs text-gray-600 group-hover:text-blue-700 flex-1 min-w-0">
                                        <FileText className="h-3 w-3 mr-1 flex-shrink-0" />
                                        <span className="font-medium text-xs truncate">
                                            {getDocumentTitle(section.document_id)}
                                        </span>
                                        <span className="mx-1 flex-shrink-0">•</span>
                                        <span className="text-xs flex-shrink-0">Page {section.page_number}</span>
                                    </div>
                                    <div className={`px-1.5 py-0.5 rounded text-xs font-medium ml-2 flex-shrink-0 ${getConfidenceColor(section.similarity_score)}`}>
                                        {Math.round(section.similarity_score * 100)}%
                                    </div>
                                </div>

                                {/* Content snippet */}
                                <div className="text-xs text-gray-700 leading-relaxed group-hover:text-gray-900 mb-2">
                                    {section.snippet || section.text}
                                </div>

                                {/* Metadata */}
                                <div className="text-xs text-gray-500 flex items-center space-x-3 group-hover:text-gray-600">
                                    <span>Type: {section.section_type}</span>
                                    {section.confidence_score && (
                                        <span>Confidence: {Math.round(section.confidence_score * 100)}%</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Search stats */}
                    <div className="text-xs text-gray-500 text-center pt-2 border-t">
                        Search completed • {relatedContent.length} results
                    </div>
                </div>
            ) : selectedText ? (
                <div className="text-center py-8">
                    <Search className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">
                        No related content found for the selected text
                    </p>
                    <p className="text-xs text-gray-400 mt-2">
                        Try selecting different text or ensure documents are fully processed
                    </p>
                </div>
            ) : null}
        </div>
    );
};

export default RelatedContentPanel;
