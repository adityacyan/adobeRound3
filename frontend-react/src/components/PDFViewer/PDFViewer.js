import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { FileText, Clock, CheckCircle, AlertCircle, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, ExternalLink, Download } from 'lucide-react';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

// Adobe Client ID - you can set this in your .env file as ADOBE_PDF_EMBED_KEY
const ADOBE_CLIENT_ID = process.env.ADOBE_PDF_EMBED_KEY || "YOUR_CLIENT_ID_HERE";

const PDFViewer = ({
    sessionId,
    documents,
    activeDocumentId,
    setActiveDocumentId,
    onTextSelection
}) => {
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
        const initializeAdobe = () => {
            if (window.AdobeDC && !adobeReady && ADOBE_CLIENT_ID !== "YOUR_CLIENT_ID_HERE") {
                console.log('Adobe PDF Embed API loaded');
                setAdobeReady(true);
            } else if (ADOBE_CLIENT_ID === "YOUR_CLIENT_ID_HERE") {
                console.log('Adobe Client ID not configured, using PDF.js fallback');
                setUseAdobeEmbed(false);
                setAdobeReady(false);
            }
        };

        // Check if Adobe is already loaded
        if (window.AdobeDC && ADOBE_CLIENT_ID !== "YOUR_CLIENT_ID_HERE") {
            initializeAdobe();
        } else if (ADOBE_CLIENT_ID === "YOUR_CLIENT_ID_HERE") {
            setUseAdobeEmbed(false);
        } else {
            // Wait for Adobe to load
            const checkInterval = setInterval(() => {
                if (window.AdobeDC) {
                    initializeAdobe();
                    clearInterval(checkInterval);
                }
            }, 100);

            // Fallback to PDF.js after 5 seconds
            setTimeout(() => {
                if (!adobeReady) {
                    console.log('Adobe PDF Embed API failed to load, falling back to PDF.js');
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

            const url = `http://localhost:8000/session/${sessionId}/documents/${activeDocumentId}/pdf`;
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

            const fileName = activeDocument?.title || `document_${activeDocumentId.substring(0, 8)}.pdf`;

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
            const url = `http://localhost:8000/session/${sessionId}/documents/${activeDocumentId}/pdf`;
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

    // Advanced PDF.js text selection (similar to the method you mentioned)
    const getHighlightCoords = useCallback(() => {
        try {
            const selection = window.getSelection();
            if (!selection.rangeCount) return null;

            const range = selection.getRangeAt(0);
            const selectedText = selection.toString().trim();

            if (!selectedText || selectedText.length < 2) return null;

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

    // Set up text selection listeners for PDF.js
    useEffect(() => {
        if (!useAdobeEmbed) {
            const handleMouseUp = (event) => {
                setTimeout(handlePdfJsTextSelection, 50);
            };

            const handleSelectionChange = () => {
                setTimeout(handlePdfJsTextSelection, 10);
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
                            <span className="mr-2 truncate max-w-32">
                                {doc.title || `Document ${doc.document_id.substring(0, 8)}`}
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
                <div className="border-b border-gray-200 bg-gray-50 px-4 py-2 flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span className="font-medium">📄 {activeDocument.title}</span>
                        {useAdobeEmbed && adobeReady ? (
                            <span className="text-red-600 font-medium">🔥 Adobe PDF Embed</span>
                        ) : (
                            <span className="text-blue-600 font-medium">📚 PDF.js Viewer</span>
                        )}
                        {numPages && !useAdobeEmbed && <span>📊 {numPages} pages</span>}
                    </div>
                    <div className="flex items-center space-x-2">
                        {/* PDF.js Navigation controls */}
                        {!useAdobeEmbed && numPages && numPages > 1 && (
                            <div className="flex items-center space-x-1 border rounded-lg px-2 py-1 bg-white">
                                <button
                                    onClick={goToPrevPage}
                                    disabled={pageNumber <= 1}
                                    className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Previous page"
                                >
                                    <ChevronLeft className="h-4 w-4" />
                                </button>
                                <span className="text-sm px-2">
                                    {pageNumber} / {numPages}
                                </span>
                                <button
                                    onClick={goToNextPage}
                                    disabled={pageNumber >= numPages}
                                    className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Next page"
                                >
                                    <ChevronRight className="h-4 w-4" />
                                </button>
                            </div>
                        )}

                        {/* PDF.js Zoom controls */}
                        {!useAdobeEmbed && (
                            <div className="flex items-center space-x-1 border rounded-lg px-2 py-1 bg-white">
                                <button
                                    onClick={zoomOut}
                                    disabled={scale <= 0.5}
                                    className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Zoom out"
                                >
                                    <ZoomOut className="h-4 w-4" />
                                </button>
                                <span className="text-sm px-2 min-w-[3rem] text-center">
                                    {Math.round(scale * 100)}%
                                </span>
                                <button
                                    onClick={zoomIn}
                                    disabled={scale >= 3.0}
                                    className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="Zoom in"
                                >
                                    <ZoomIn className="h-4 w-4" />
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
                                className="px-3 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600 transition-colors"
                                title="Toggle between Adobe and PDF.js"
                            >
                                {useAdobeEmbed ? '📚 Use PDF.js' : '🔥 Use Adobe'}
                            </button>
                        )}

                        {/* External links */}
                        {pdfBlobUrl && (
                            <>
                                <a
                                    href={pdfBlobUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-3 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600 transition-colors flex items-center"
                                    title="Open in new tab"
                                >
                                    <ExternalLink className="h-3 w-3 mr-1" />
                                    Open
                                </a>
                                <a
                                    href={pdfBlobUrl}
                                    download={activeDocument.title || 'document.pdf'}
                                    className="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors flex items-center"
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
                        {selectedText && (
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
                        )}
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
