import React, { useState, useEffect, useRef } from 'react';
import { FileText, Clock, CheckCircle, AlertCircle, ZoomIn, ZoomOut, Download, ExternalLink } from 'lucide-react';

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
    const iframeRef = useRef(null);

    const activeDocument = documents.find(doc => doc.document_id === activeDocumentId);

    useEffect(() => {
        if (activeDocumentId && sessionId) {
            setLoading(true);
            fetchPdfAsBlob();
        }
    }, [activeDocumentId, sessionId]);

    const fetchPdfAsBlob = async () => {
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

            console.log('PDF fetched as blob successfully');
        } catch (error) {
            console.error('Failed to fetch PDF as blob:', error);
            // Fallback to direct URL
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

    const getPdfUrl = () => {
        if (!activeDocumentId || !sessionId) return null;

        // Use blob URL if available, otherwise fall back to direct URL
        return pdfBlobUrl || `http://localhost:8000/session/${sessionId}/documents/${activeDocumentId}/pdf`;
    };

    const handleTabClick = (documentId) => {
        // Cleanup current blob URL
        if (pdfBlobUrl) {
            URL.revokeObjectURL(pdfBlobUrl);
            setPdfBlobUrl(null);
        }

        setActiveDocumentId(documentId);
        setSelectedText(''); // Clear selection when switching tabs
    };

    // Simple text selection handler for demonstration
    // In a real implementation, this would need to be handled by the PDF viewer
    const handleTextSelection = () => {
        // For demo purposes, simulate text selection
        const demoTexts = [
            "machine learning algorithms and neural networks",
            "data analysis and statistical methods",
            "artificial intelligence applications",
            "deep learning and computer vision",
            "natural language processing techniques"
        ];
        const randomText = demoTexts[Math.floor(Math.random() * demoTexts.length)];
        setSelectedText(randomText);
        if (onTextSelection) {
            onTextSelection(randomText);
        }
    };

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
                        <span>📊 {activeDocument.total_pages || 0} pages</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={handleTextSelection}
                            className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                            title="Simulate text selection for demo"
                        >
                            📝 Demo Select
                        </button>
                        {getPdfUrl() && (
                            <>
                                <a
                                    href={getPdfUrl()}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-3 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600 transition-colors flex items-center"
                                    title="Open in new tab"
                                >
                                    <ExternalLink className="h-3 w-3 mr-1" />
                                    Open
                                </a>
                                <a
                                    href={getPdfUrl()}
                                    download
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
            <div className="flex-1 relative overflow-hidden">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                            <p className="text-gray-600">Loading PDF...</p>
                        </div>
                    </div>
                ) : getPdfUrl() && activeDocument ? (
                    <div className="h-full relative">
                        {/* Use object tag for better PDF handling in browsers */}
                        <object
                            data={getPdfUrl()}
                            type="application/pdf"
                            className="w-full h-full"
                            style={{ border: 'none', backgroundColor: '#525659' }}
                        >
                            {/* Fallback content when object tag fails */}
                            <div className="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-gray-600">
                                <div className="text-6xl mb-4">📄</div>
                                <h3 className="text-xl font-semibold mb-4">PDF Display Not Available</h3>
                                <p className="text-center mb-6 max-w-md">
                                    Your browser cannot display this PDF inline. Use the options below to view the document.
                                </p>
                                <div className="flex gap-4">
                                    <a
                                        href={getPdfUrl()}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center"
                                    >
                                        <ExternalLink className="h-4 w-4 mr-2" />
                                        Open in New Tab
                                    </a>
                                    <a
                                        href={getPdfUrl()}
                                        download
                                        className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center"
                                    >
                                        <Download className="h-4 w-4 mr-2" />
                                        Download PDF
                                    </a>
                                </div>
                                <p className="text-sm text-gray-500 mt-4">
                                    File: {activeDocument.title}
                                </p>
                            </div>
                        </object>

                        {/* Text Selection Indicator */}
                        {selectedText && (
                            <div className="absolute top-4 left-4 bg-green-500 bg-opacity-95 text-white px-3 py-2 rounded-lg shadow-lg text-sm max-w-xs">
                                <div className="font-medium">✅ Text Selected</div>
                                <div className="text-xs opacity-90 mt-1 truncate">
                                    "{selectedText.substring(0, 50)}..."
                                </div>
                            </div>
                        )}

                        {/* Overlay for external text selection demo */}
                        <div
                            className="absolute inset-0 pointer-events-none"
                            style={{ zIndex: 1 }}
                        >
                            {/* This overlay can be used for custom interactions if needed */}
                        </div>
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
                        </div>
                    </div>
                )}
            </div>

            {/* Footer with document status */}
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
