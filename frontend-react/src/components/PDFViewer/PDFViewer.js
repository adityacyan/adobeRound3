import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { FileText, Clock, CheckCircle, AlertCircle, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, ExternalLink, Download } from 'lucide-react';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

// Adobe Client ID - you can set this in your .env file as REACT_APP_ADOBE_CLIENT_ID
const ADOBE_CLIENT_ID = process.env.REACT_APP_ADOBE_CLIENT_ID || "YOUR_CLIENT_ID_HERE";

const PDFViewer = ({
    sessionId,
    documents,
    activeDocumentId,
    setActiveDocumentId,
    onTextSelection,
    onNavigationRequest
}) => {
    // Utility function to truncate text with ellipsis
    const truncateText = (text, maxLength = 30) => {
        if (!text) return '';
        // Remove .pdf extension for cleaner display
        let displayText = text.endsWith('.pdf') ? text.slice(0, -4) : text;
        return displayText.length > maxLength ? displayText.substring(0, maxLength) + '...' : displayText;
    };

    // Get display title for document
    const getDocumentTitle = (doc) => {
        return doc.title || doc.original_filename || `Document ${doc.document_id.substring(0, 8)}`;
    };

    const [loading, setLoading] = useState(false);
    const [selectedText, setSelectedText] = useState('');
    const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
    const [pdfError, setPdfError] = useState(null);
    const [adobeViewer, setAdobeViewer] = useState(null);
    const [adobeReady, setAdobeReady] = useState(false);
    const [useAdobeEmbed, setUseAdobeEmbed] = useState(true);
    const [numPages, setNumPages] = useState(null);
    const [pageNumber, setPageNumber] = useState(1);
    const [scale, setScale] = useState(1.2);
    const adobeContainerRef = useRef(null);
    const pdfJsContainerRef = useRef(null);
    const currentDocumentRef = useRef(null);

    const activeDocument = documents.find(doc => doc.document_id === activeDocumentId);

    // Initialize Adobe PDF Embed API
    useEffect(() => {
        console.log('Adobe initialization - Client ID:', ADOBE_CLIENT_ID);
        console.log('Adobe initialization - window.AdobeDC available:', !!window.AdobeDC);

        const initializeAdobe = () => {
            if (window.AdobeDC && !adobeReady && ADOBE_CLIENT_ID !== "YOUR_CLIENT_ID_HERE") {
                console.log('Adobe PDF Embed API loaded successfully');
                setAdobeReady(true);
            } else if (ADOBE_CLIENT_ID === "YOUR_CLIENT_ID_HERE") {
                console.log('Adobe Client ID not configured, using PDF.js fallback');
                setUseAdobeEmbed(false);
                setAdobeReady(false);
            }
        };

        // Check if Adobe is already loaded
        if (window.AdobeDC && ADOBE_CLIENT_ID !== "YOUR_CLIENT_ID_HERE") {
            console.log('Adobe already loaded, initializing...');
            initializeAdobe();
        } else if (ADOBE_CLIENT_ID === "YOUR_CLIENT_ID_HERE") {
            console.log('No Adobe Client ID provided, falling back to PDF.js');
            setUseAdobeEmbed(false);
        } else {
            console.log('Waiting for Adobe PDF Embed API to load...');
            // Wait for Adobe to load
            const checkInterval = setInterval(() => {
                console.log('Checking for Adobe API...', !!window.AdobeDC);
                if (window.AdobeDC) {
                    console.log('Adobe API detected, initializing...');
                    initializeAdobe();
                    clearInterval(checkInterval);
                }
            }, 100);

            // Fallback to PDF.js after 5 seconds
            setTimeout(() => {
                if (!adobeReady) {
                    console.log('Adobe PDF Embed API failed to load after 5 seconds, falling back to PDF.js');
                    setUseAdobeEmbed(false);
                    clearInterval(checkInterval);
                }
            }, 5000);
        }
    }, [adobeReady]);

    useEffect(() => {
        if (activeDocumentId && sessionId) {
            setLoading(true);
            setPdfError(null);
            setPageNumber(1);
            if (useAdobeEmbed && adobeReady) {
                fetchPdfAndRenderAdobe();
            } else {
                fetchPdfAndRenderPdfJs();
            }
        }
    }, [activeDocumentId, sessionId, adobeReady, useAdobeEmbed]);

    const fetchPdfAndRenderAdobe = async () => {
        if (!activeDocumentId || !sessionId || !adobeReady) return;

        try {
            // Clear previous viewer
            if (adobeViewer) {
                console.log('Clearing previous Adobe viewer');
            }

            const url = `/api/session/${sessionId}/documents/${activeDocumentId}/pdf`;
            console.log('Fetching PDF from:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const arrayBuffer = await response.arrayBuffer();

            // Clear the container
            if (adobeContainerRef.current) {
                adobeContainerRef.current.innerHTML = '';
            }

            // Configure Adobe PDF Embed
            const adobeDCView = new window.AdobeDC.View({
                clientId: ADOBE_CLIENT_ID,
                divId: "adobe-dc-view",
                locale: "en-US"
            });

            console.log('Rendering PDF with Adobe Embed API');

            const fileName = getDocumentTitle(activeDocument);

            // Render the PDF
            adobeDCView.previewFile({
                content: { promise: Promise.resolve(arrayBuffer) },
                metaData: { fileName: fileName }
            }, {
                embedMode: "SIZED_CONTAINER",
                showAnnotationTools: false,
                showLeftHandPanel: true,
                showDownloadPDF: false,
                showPrintPDF: false,
                showZoomControl: true,
                defaultViewMode: "FIT_WIDTH",
                enableFormFilling: false
            });

            // Set up text selection listeners
            adobeDCView.registerCallback(
                window.AdobeDC.View.Enum.CallbackType.TEXT_SELECTION,
                (textSelectionEvent) => {
                    console.log('Adobe text selection event:', textSelectionEvent);

                    if (textSelectionEvent.data && textSelectionEvent.data.text) {
                        const text = textSelectionEvent.data.text.trim();
                        if (text.length > 2) {
                            console.log('Selected text:', text);
                            setSelectedText(text);

                            if (onTextSelection) {
                                onTextSelection(text);
                            }
                        }
                    }
                },
                { enablePDFAnalytics: false }
            );

            // Save references
            setAdobeViewer(adobeDCView);
            currentDocumentRef.current = activeDocumentId;

            setPdfError(null);
            console.log('Adobe PDF rendered successfully');

        } catch (error) {
            console.error('Failed to fetch/render PDF with Adobe:', error);
            console.log('Falling back to PDF.js');
            setUseAdobeEmbed(false);
            fetchPdfAndRenderPdfJs();
        } finally {
            setLoading(false);
        }
    };

    const fetchPdfAndRenderPdfJs = async () => {
        if (!activeDocumentId || !sessionId) return;

        try {
            const url = `/api/session/${sessionId}/documents/${activeDocumentId}/pdf`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            setPdfBlobUrl(blobUrl);
            setPdfError(null);

            console.log('PDF fetched for PDF.js successfully');
        } catch (error) {
            console.error('Failed to fetch PDF:', error);
            setPdfError(error.message);
            setPdfBlobUrl(null);
        } finally {
            setLoading(false);
        }
    };

    // Cleanup blob URL when component unmounts or document changes
    useEffect(() => {
        return () => {
            if (pdfBlobUrl) {
                URL.revokeObjectURL(pdfBlobUrl);
            }
        };
    }, [pdfBlobUrl]);

    const handleTabClick = (documentId) => {
        // Cleanup current resources
        if (pdfBlobUrl) {
            URL.revokeObjectURL(pdfBlobUrl);
            setPdfBlobUrl(null);
        }

        setActiveDocumentId(documentId);
        setSelectedText('');
        setPdfError(null);
        setPageNumber(1);
        setNumPages(null);

        // Clear the Adobe container
        if (adobeContainerRef.current) {
            adobeContainerRef.current.innerHTML = '';
        }
        setAdobeViewer(null);
    };

    // PDF.js Document load handlers
    const onDocumentLoadSuccess = ({ numPages }) => {
        setNumPages(numPages);
        setLoading(false);
        setPdfError(null);
        console.log(`PDF.js loaded with ${numPages} pages`);
    };

    const onDocumentLoadError = (error) => {
        console.error('PDF.js load error:', error);
        setPdfError(error.message || 'Failed to load PDF');
        setLoading(false);
    };

    // PDF.js navigation controls
    const goToPrevPage = () => {
        setPageNumber(prev => Math.max(prev - 1, 1));
    };

    const goToNextPage = () => {
        setPageNumber(prev => Math.min(prev + 1, numPages || 1));
    };

    const zoomIn = () => {
        setScale(prev => Math.min(prev + 0.2, 3.0));
    };

    const zoomOut = () => {
        setScale(prev => Math.max(prev - 0.2, 0.5));
    };

    // Function to clear existing highlights
    const clearExistingHighlights = useCallback(() => {
        try {
            // Clear span-based highlights
            const highlights = document.querySelectorAll('.pdf-text-highlight');
            highlights.forEach(highlight => {
                const parent = highlight.parentNode;
                if (parent) {
                    parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
                    parent.normalize(); // Merge adjacent text nodes
                }
            });

            // Clear element-based highlights
            const elementHighlights = document.querySelectorAll('.pdf-text-highlight-element');
            elementHighlights.forEach(element => {
                element.style.backgroundColor = '';
                element.style.borderRadius = '';
                element.style.padding = '';
                element.classList.remove('pdf-text-highlight-element');
            });

            // Clear browser selection
            if (window.getSelection) {
                window.getSelection().removeAllRanges();
            }

            console.log('🧹 Existing highlights cleared');
        } catch (error) {
            console.error('Error clearing highlights:', error);
        }
    }, []);

    // Function to highlight text on the current page with light pink overlay
    const highlightTextOnPage = useCallback((searchText) => {
        try {
            console.log('🎯 Attempting to highlight text:', searchText.substring(0, 50));

            // Clear any existing highlights first
            clearExistingHighlights();

            // Find the PDF.js text layer specifically
            const textLayer = document.querySelector('.react-pdf__Page__textContent') ||
                document.querySelector('[data-page-number="' + pageNumber + '"] .react-pdf__Page__textContent') ||
                pdfJsContainerRef.current?.querySelector('.react-pdf__Page__textContent');

            if (!textLayer) {
                console.log('❌ PDF text layer not found, trying general container');
                // Fallback to general PDF container
                const pdfContainer = pdfJsContainerRef.current || document.querySelector('.react-pdf__Document');
                if (!pdfContainer) {
                    console.log('❌ PDF container not found');
                    return;
                }
            }

            const searchContainer = textLayer || pdfJsContainerRef.current || document.querySelector('.react-pdf__Document');

            // Create a case-insensitive search
            const searchLower = searchText.toLowerCase().trim();
            let found = false;

            // Function to recursively search text nodes
            const highlightInNode = (node) => {
                if (node.nodeType === Node.TEXT_NODE) {
                    const text = node.textContent.toLowerCase();
                    let startIndex = 0;

                    // Find all occurrences of the search text
                    while (true) {
                        const index = text.indexOf(searchLower, startIndex);
                        if (index === -1) break;

                        // Found the text, create highlighting
                        const range = document.createRange();
                        range.setStart(node, index);
                        range.setEnd(node, index + searchLower.length);

                        // Create highlight span
                        const highlight = document.createElement('span');
                        highlight.className = 'pdf-text-highlight';

                        try {
                            range.surroundContents(highlight);
                            found = true;

                            // Scroll the first highlighted element into view
                            if (!found || startIndex === 0) {
                                setTimeout(() => {
                                    highlight.scrollIntoView({
                                        behavior: 'smooth',
                                        block: 'center',
                                        inline: 'nearest'
                                    });
                                }, 200);
                            }

                            console.log('✨ Text highlighted successfully with pink overlay');
                            break; // Only highlight first occurrence per text node
                        } catch (e) {
                            console.log('Could not surround range:', e.message);
                            // Skip this occurrence and try the next
                            startIndex = index + 1;
                            continue;
                        }
                    }
                } else if (node.nodeType === Node.ELEMENT_NODE && !node.classList.contains('pdf-text-highlight')) {
                    // Recursively search child nodes, but avoid already highlighted elements
                    const children = Array.from(node.childNodes);
                    children.forEach(child => highlightInNode(child));
                }
            };

            // Start the search
            highlightInNode(searchContainer);

            if (!found) {
                console.log('❌ Text not found in PDF text layer, trying broader search');
                // Try a more flexible search approach
                const allTextElements = searchContainer.querySelectorAll('span, div, p');

                for (let element of allTextElements) {
                    const text = element.textContent.toLowerCase();
                    if (text.includes(searchLower)) {
                        // Create a visual highlight by adding background to the element
                        element.style.backgroundColor = 'rgba(255, 182, 193, 0.6)';
                        element.style.borderRadius = '3px';
                        element.style.padding = '2px';
                        element.classList.add('pdf-text-highlight-element');

                        element.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center',
                            inline: 'nearest'
                        });

                        found = true;
                        console.log('✨ Text highlighted using element-level highlighting');
                        break;
                    }
                }
            }

            if (!found) {
                console.log('❌ Text not found using DOM methods, trying browser find as fallback');
                // Final fallback to browser find
                if (window.find) {
                    window.getSelection().removeAllRanges();
                    const browserFound = window.find(searchText, false, false, true, false, true, false);
                    if (browserFound) {
                        console.log('✨ Text found using browser find');
                    }
                }
            }

        } catch (error) {
            console.error('Error highlighting text:', error);
        }
    }, [pageNumber, clearExistingHighlights]);

    // Navigation function for external components to navigate to specific content
    const navigateToContent = useCallback((documentId, pageNum, searchText = null) => {
        console.log('🧭 Navigation request:', { documentId, pageNum, searchText });

        // Clear any existing highlights first
        clearExistingHighlights();

        // Switch to the target document if different from current
        if (documentId !== activeDocumentId) {
            setActiveDocumentId(documentId);
        }

        // Navigate to the target page
        if (pageNum && pageNum !== pageNumber) {
            setPageNumber(pageNum);
        }

        // If we have search text, we'll attempt to highlight it after the page loads
        if (searchText) {
            // Store the search text to highlight after page render
            const highlightTimeout = setTimeout(() => {
                console.log('🎯 Starting text highlighting after page load');
                highlightTextOnPage(searchText);
            }, 1500); // Give more time for page to render

            return () => clearTimeout(highlightTimeout);
        }
    }, [activeDocumentId, pageNumber, setActiveDocumentId, clearExistingHighlights, highlightTextOnPage]);

    // Clear highlights when changing pages or documents
    useEffect(() => {
        clearExistingHighlights();
    }, [pageNumber, activeDocumentId, clearExistingHighlights]);

    // Expose navigation function to parent component
    useEffect(() => {
        if (onNavigationRequest) {
            onNavigationRequest(navigateToContent);
        }
    }, [navigateToContent, onNavigationRequest]);
    // https://stackoverflow.com/questions/48950038/how-do-i-retrieve-text-from-user-selection-in-pdf-js
    // Advanced PDF.js text selection (similar to the method you mentioned)
    const getHighlightCoords = useCallback(() => {
        try {
            const selection = window.getSelection();
            if (!selection.rangeCount) return null;

            const range = selection.getRangeAt(0);
            const selectedText = selection.toString().trim();

            if (!selectedText || selectedText.length < 2) return null;

            // Check if the selection is within the PDF viewer container
            const container = range.commonAncestorContainer;
            const pdfContainer = container.nodeType === Node.TEXT_NODE
                ? container.parentElement?.closest('.react-pdf__Document')
                : container.closest?.('.react-pdf__Document');

            if (!pdfContainer) {
                console.log('Text selection outside PDF viewer, ignoring');
                return null;
            }

            const rects = range.getClientRects();
            if (rects.length === 0) return null;

            console.log('PDF.js text selection detected:', {
                text: selectedText,
                pageNumber: pageNumber,
                rects: Array.from(rects).map(rect => ({
                    left: rect.left,
                    top: rect.top,
                    right: rect.right,
                    bottom: rect.bottom
                }))
            });

            return {
                text: selectedText,
                pageNumber: pageNumber,
                rects: Array.from(rects)
            };
        } catch (error) {
            console.error('Error getting highlight coords:', error);
            return null;
        }
    }, [pageNumber]);

    // Enhanced text selection for PDF.js with coordinate tracking
    const handlePdfJsTextSelection = useCallback(() => {
        const coords = getHighlightCoords();
        if (coords && coords.text) {
            console.log('PDF.js text selected:', coords.text);
            setSelectedText(coords.text);

            if (onTextSelection) {
                onTextSelection(coords.text, {
                    pageNumber: coords.pageNumber,
                    coordinates: coords.rects
                });
            }
        }
    }, [getHighlightCoords, onTextSelection]);

    // Set up text selection listeners for PDF.js - only within PDF container
    useEffect(() => {
        if (!useAdobeEmbed) {
            const handleMouseUp = (event) => {
                // Check if the mouse up event happened inside the PDF viewer container
                const pdfContainer = event.target.closest('.react-pdf__Document');
                if (pdfContainer) {
                    setTimeout(handlePdfJsTextSelection, 50);
                }
            };

            const handleSelectionChange = () => {
                // Check if the current selection is within the PDF viewer
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    const container = range.commonAncestorContainer;
                    const pdfContainer = container.nodeType === Node.TEXT_NODE
                        ? container.parentElement?.closest('.react-pdf__Document')
                        : container.closest?.('.react-pdf__Document');

                    if (pdfContainer) {
                        setTimeout(handlePdfJsTextSelection, 10);
                    }
                }
            };

            document.addEventListener('mouseup', handleMouseUp);
            document.addEventListener('selectionchange', handleSelectionChange);

            return () => {
                document.removeEventListener('mouseup', handleMouseUp);
                document.removeEventListener('selectionchange', handleSelectionChange);
            };
        }
    }, [handlePdfJsTextSelection, useAdobeEmbed]);

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'processing':
                return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />;
            case 'failed':
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            default:
                return <Clock className="h-4 w-4 text-gray-400" />;
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'completed':
                return 'Ready';
            case 'processing':
                return 'Processing...';
            case 'failed':
                return 'Failed';
            default:
                return 'Pending';
        }
    };

    return (
        <div className="h-full flex flex-col bg-white">
            {/* Document Tabs */}
            <div className="border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <div className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300">
                    {documents.map((doc) => (
                        <button
                            key={doc.document_id}
                            onClick={() => handleTabClick(doc.document_id)}
                            className={`
                                flex items-center px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap
                                transition-colors duration-200 min-w-max
                                ${activeDocumentId === doc.document_id
                                    ? 'border-blue-500 text-blue-600 bg-white shadow-sm'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-100'
                                }
                            `}
                        >
                            <FileText className="h-4 w-4 mr-2 flex-shrink-0" />
                            <span className="mr-2 truncate max-w-32" title={getDocumentTitle(doc)}>
                                {truncateText(getDocumentTitle(doc), 15)}
                            </span>
                            <div className="flex items-center ml-auto">
                                {getStatusIcon(doc.processing_status)}
                                <span className="ml-1 text-xs">
                                    {getStatusText(doc.processing_status)}
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* PDF Controls */}
            {activeDocument && (
                <div className="border-b border-gray-200 bg-gray-50 px-4 py-1.5 flex items-center justify-between flex-shrink-0 h-12">
                    {/* Left side - Document title only */}
                    <div className="flex items-center text-xs text-gray-600 min-w-0 flex-1">
                        <span className="font-medium truncate" title={getDocumentTitle(activeDocument)}>
                            📄 {truncateText(getDocumentTitle(activeDocument), 25)}
                        </span>
                    </div>

                    {/* Right side - All controls and indicators */}
                    <div className="flex items-center space-x-1.5">
                        {/* Viewer type and page count indicators */}
                        {useAdobeEmbed && adobeReady ? (
                            <span className="text-red-600 text-xs font-medium">🔥 Adobe</span>
                        ) : (
                            <span className="text-blue-600 text-xs font-medium">📚 PDF.js</span>
                        )}
                        {numPages && !useAdobeEmbed && <span className="text-xs text-gray-500">📊 {numPages} pages</span>}
                        {/* PDF.js Navigation controls */}
                        {!useAdobeEmbed && numPages && numPages > 1 && (
                            <div className="flex items-center space-x-1 border rounded px-1.5 py-0.5 bg-white h-8">
                                <button
                                    onClick={goToPrevPage}
                                    disabled={pageNumber <= 1}
                                    className="p-0.5 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Previous page"
                                >
                                    <ChevronLeft className="h-3 w-3" />
                                </button>
                                <span className="text-xs px-1 min-w-[2.5rem] text-center">
                                    {pageNumber}/{numPages}
                                </span>
                                <button
                                    onClick={goToNextPage}
                                    disabled={pageNumber >= numPages}
                                    className="p-0.5 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Next page"
                                >
                                    <ChevronRight className="h-3 w-3" />
                                </button>
                            </div>
                        )}

                        {/* PDF.js Zoom controls */}
                        {!useAdobeEmbed && (
                            <div className="flex items-center space-x-1 border rounded px-1.5 py-0.5 bg-white h-8">
                                <button
                                    onClick={zoomOut}
                                    disabled={scale <= 0.5}
                                    className="p-0.5 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Zoom out"
                                >
                                    <ZoomOut className="h-3 w-3" />
                                </button>
                                <span className="text-xs px-1 min-w-[2.5rem] text-center">
                                    {Math.round(scale * 100)}%
                                </span>
                                <button
                                    onClick={zoomIn}
                                    disabled={scale >= 3.0}
                                    className="p-0.5 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Zoom in"
                                >
                                    <ZoomIn className="h-3 w-3" />
                                </button>
                            </div>
                        )}

                        {/* Viewer toggle button */}
                        {window.AdobeDC && ADOBE_CLIENT_ID !== "YOUR_CLIENT_ID_HERE" && (
                            <button
                                onClick={() => {
                                    setUseAdobeEmbed(!useAdobeEmbed);
                                    setLoading(true);
                                }}
                                className="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600 transition-colors h-8 flex items-center"
                                title="Toggle between Adobe and PDF.js"
                            >
                                {useAdobeEmbed ? '📚' : '🔥'}
                            </button>
                        )}

                        {/* External links */}
                        {pdfBlobUrl && (
                            <>
                                <a
                                    href={pdfBlobUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-2 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600 transition-colors flex items-center h-8"
                                    title="Open in new tab"
                                >
                                    <ExternalLink className="h-3 w-3 mr-1" />
                                    Open
                                </a>
                                <a
                                    href={pdfBlobUrl}
                                    download={getDocumentTitle(activeDocument) || 'document.pdf'}
                                    className="px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors flex items-center h-8"
                                    title="Download PDF"
                                >
                                    <Download className="h-3 w-3 mr-1" />
                                    Download
                                </a>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* PDF Display Area */}
            <div className="flex-1 relative overflow-hidden bg-gray-100">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                            <p className="text-gray-600">
                                Loading PDF with {useAdobeEmbed ? 'Adobe Embed' : 'PDF.js'}...
                            </p>
                        </div>
                    </div>
                ) : pdfError ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                        <div className="text-center max-w-md">
                            <AlertCircle className="h-16 w-16 text-red-400 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-700 mb-2">Error Loading PDF</h3>
                            <p className="text-red-600 mb-4">{pdfError}</p>
                            <button
                                onClick={() => {
                                    if (useAdobeEmbed) {
                                        fetchPdfAndRenderAdobe();
                                    } else {
                                        fetchPdfAndRenderPdfJs();
                                    }
                                }}
                                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                ) : activeDocument ? (
                    <div className="h-full relative">
                        {/* Adobe PDF Embed Viewer */}
                        {useAdobeEmbed && adobeReady ? (
                            <div className="h-full">
                                <div
                                    id="adobe-dc-view"
                                    ref={adobeContainerRef}
                                    className="w-full h-full"
                                    style={{ minHeight: '600px' }}
                                />
                            </div>
                        ) : null}

                        {/* PDF.js Viewer */}
                        {!useAdobeEmbed && pdfBlobUrl ? (
                            <div className="h-full flex flex-col items-center pt-4 overflow-auto">
                                <Document
                                    file={pdfBlobUrl}
                                    onLoadSuccess={onDocumentLoadSuccess}
                                    onLoadError={onDocumentLoadError}
                                    loading={
                                        <div className="flex items-center justify-center py-8">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                            <span className="ml-2 text-gray-600">Loading PDF.js...</span>
                                        </div>
                                    }
                                    error={
                                        <div className="flex items-center justify-center py-8">
                                            <AlertCircle className="h-8 w-8 text-red-500 mr-2" />
                                            <span className="text-red-600">Failed to load with PDF.js</span>
                                        </div>
                                    }
                                    noData={
                                        <div className="flex items-center justify-center py-8">
                                            <FileText className="h-8 w-8 text-gray-400 mr-2" />
                                            <span className="text-gray-600">No PDF data</span>
                                        </div>
                                    }
                                    className="pdf-document"
                                >
                                    <Page
                                        pageNumber={pageNumber}
                                        scale={scale}
                                        renderTextLayer={true}
                                        renderAnnotationLayer={true}
                                        className="pdf-page shadow-lg mb-4 mx-auto"
                                        canvasBackground="white"
                                        loading={
                                            <div className="flex items-center justify-center py-8">
                                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                                <span className="ml-2 text-gray-600">Loading page {pageNumber}...</span>
                                            </div>
                                        }
                                        error={
                                            <div className="flex items-center justify-center py-8">
                                                <AlertCircle className="h-6 w-6 text-red-500 mr-2" />
                                                <span className="text-red-600">Failed to load page {pageNumber}</span>
                                            </div>
                                        }
                                    />
                                </Document>
                            </div>
                        ) : null}

                        {/* Text Selection Indicator */}
                        {/* {selectedText && (
                            <div className={`fixed top-20 left-4 px-4 py-3 rounded-lg shadow-lg text-sm max-w-xs z-50 border-2 ${useAdobeEmbed
                                ? 'bg-red-500 bg-opacity-95 text-white border-red-600'
                                : 'bg-blue-500 bg-opacity-95 text-white border-blue-600'
                                }`}>
                                <div className="font-medium flex items-center">
                                    <CheckCircle className="h-4 w-4 mr-2" />
                                    {useAdobeEmbed ? 'Adobe' : 'PDF.js'} Text Selected
                                </div>
                                <div className="text-xs opacity-90 mt-1 break-words">
                                    "{selectedText.length > 100 ? selectedText.substring(0, 100) + '...' : selectedText}"
                                </div>
                                <button
                                    onClick={() => setSelectedText('')}
                                    className={`absolute top-1 right-1 text-white rounded p-1 ${useAdobeEmbed ? 'hover:bg-red-600' : 'hover:bg-blue-600'
                                        }`}
                                >
                                    ×
                                </button>
                            </div>
                        )} */}
                    </div>
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                        <div className="text-center max-w-md">
                            <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-700 mb-2">
                                {documents.length === 0 ? 'No documents uploaded' : 'Select a document'}
                            </h3>
                            <p className="text-gray-500">
                                {documents.length === 0
                                    ? 'Upload PDF files to start viewing and analyzing documents'
                                    : 'Choose a document from the tabs above to view its contents'
                                }
                            </p>
                            {documents.length === 0 && (
                                <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                                    <p className="text-sm text-blue-700">
                                        💡 <strong>Tip:</strong> Use the upload area in the left sidebar to add PDF documents
                                    </p>
                                </div>
                            )}
                            {!adobeReady && ADOBE_CLIENT_ID === "YOUR_CLIENT_ID_HERE" && (
                                <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                                    <p className="text-sm text-yellow-700">
                                        ⚠️ Add your Adobe Client ID to use Adobe PDF Embed. Currently using PDF.js fallback.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>            {/* Footer with document status */}
            {activeDocument && (
                <div className="border-t border-gray-200 bg-gray-50 px-4 py-2 flex-shrink-0">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                        <div className="flex items-center space-x-4">
                            <span>🕒 Uploaded: {new Date(activeDocument.upload_timestamp).toLocaleString()}</span>
                            {activeDocument.file_size && (
                                <span>📦 Size: {(activeDocument.file_size / 1024 / 1024).toFixed(2)} MB</span>
                            )}
                        </div>
                        <div className="flex items-center space-x-2">
                            {getStatusIcon(activeDocument.processing_status)}
                            <span className="font-medium">{getStatusText(activeDocument.processing_status)}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PDFViewer;
