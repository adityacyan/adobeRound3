import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { uploadPDFs } from '../../services/api';

const UploadArea = ({ sessionId, onUploadComplete, compact = false }) => {
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState(null);

    const onDrop = useCallback(async (acceptedFiles) => {
        if (!sessionId) {
            setError('No session available. Please refresh the page.');
            return;
        }

        console.log('Upload started:', { sessionId, fileCount: acceptedFiles.length });

        // Filter for PDF files only
        const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');

        if (pdfFiles.length === 0) {
            setError('Please upload only PDF files.');
            return;
        }

        if (pdfFiles.length !== acceptedFiles.length) {
            setError('Some files were skipped. Only PDF files are supported.');
        }

        setUploading(true);
        setError(null);
        setUploadProgress(0);

        try {
            console.log('Calling uploadPDFs API...');
            const result = await uploadPDFs(sessionId, pdfFiles, (progress) => {
                console.log('Upload progress:', progress + '%');
                setUploadProgress(progress);
            });

            console.log('Upload result:', result);

            // Wait a moment for processing to start
            setTimeout(() => {
                if (onUploadComplete) {
                    onUploadComplete();
                }
            }, 1000);

        } catch (error) {
            console.error('Upload failed:', error);

            // More detailed error messages
            if (error.response) {
                setError(`Upload failed: ${error.response.status} - ${error.response.data?.detail || error.response.statusText}`);
            } else if (error.request) {
                setError('Upload failed: No response from server. Is the backend running?');
            } else {
                setError(`Upload failed: ${error.message}`);
            }
        } finally {
            setUploading(false);
            setUploadProgress(0);
        }
    }, [sessionId, onUploadComplete]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf']
        },
        multiple: true,
        disabled: uploading
    });

    return (
        <div className={compact ? "w-full" : "h-full flex items-center justify-center p-8"}>
            <div className={compact ? "w-full" : "max-w-2xl w-full"}>
                <div
                    {...getRootProps()}
                    className={`
            border-2 border-dashed rounded-lg text-center cursor-pointer transition-all duration-200
            ${compact ? 'p-4' : 'p-12'}
            ${isDragActive
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                        }
            ${uploading ? 'cursor-not-allowed opacity-60' : ''}
          `}
                >
                    <input {...getInputProps()} />

                    <div className={compact ? "space-y-2" : "space-y-4"}>
                        <div className="flex justify-center">
                            {uploading ? (
                                <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${compact ? 'h-8 w-8' : 'h-16 w-16'}`}></div>
                            ) : (
                                <Upload className={`text-gray-400 ${compact ? 'h-8 w-8' : 'h-16 w-16'}`} />
                            )}
                        </div>

                        <div>
                            <h3 className={`font-semibold text-gray-700 ${compact ? 'text-sm mb-1' : 'text-xl mb-2'}`}>
                                {uploading ? 'Uploading...' : (compact ? 'Drop PDFs here' : 'Upload PDF Documents')}
                            </h3>

                            {uploading ? (
                                <div className="space-y-2">
                                    <p className={`text-gray-600 ${compact ? 'text-xs' : ''}`}>
                                        {uploadProgress}%
                                    </p>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                            style={{ width: `${uploadProgress}%` }}
                                        ></div>
                                    </div>
                                </div>
                            ) : (
                                <div className={`text-gray-600 ${compact ? 'text-xs' : ''}`}>
                                    {isDragActive ? (
                                        <p>Drop files here...</p>
                                    ) : (
                                        <div>
                                            <p>{compact ? 'Drop or click to select' : 'Drag & drop PDF files here, or click to select'}</p>
                                            {!compact && (
                                                <p className="text-sm text-gray-500 mt-2">
                                                    Supports multiple PDFs • Max 100MB per file
                                                </p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {!uploading && !compact && (
                            <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
                                <div className="flex items-center">
                                    <FileText className="h-4 w-4 mr-1" />
                                    PDF Only
                                </div>
                                <div className="flex items-center">
                                    <Upload className="h-4 w-4 mr-1" />
                                    Multiple Files
                                </div>
                            </div>
                        )}

                        {!uploading && compact && (
                            <div className="flex items-center justify-center text-xs text-gray-500">
                                <FileText className="h-3 w-3 mr-1" />
                                PDF files only
                            </div>
                        )}
                    </div>
                </div>

                {error && (
                    <div className={`${compact ? 'mt-2 p-2' : 'mt-4 p-4'} bg-red-50 border border-red-200 rounded-lg`}>
                        <div className="flex items-center">
                            <AlertCircle className={`text-red-500 mr-2 ${compact ? 'h-4 w-4' : 'h-5 w-5'}`} />
                            <span className={`text-red-700 ${compact ? 'text-xs' : ''}`}>{error}</span>
                        </div>
                    </div>
                )}

                {!uploading && !compact && (
                    <div className="mt-8 text-center">
                        <h4 className="text-lg font-medium text-gray-700 mb-4">
                            🚀 What happens after upload?
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <div className="text-blue-600 text-2xl mb-2">📄</div>
                                <h5 className="font-medium text-gray-700">PDF Processing</h5>
                                <p className="text-gray-600">Text extraction & section identification</p>
                            </div>
                            <div className="bg-green-50 p-4 rounded-lg">
                                <div className="text-green-600 text-2xl mb-2">🎯</div>
                                <h5 className="font-medium text-gray-700">AI Insights</h5>
                                <p className="text-gray-600">Automatic takeaways & analysis</p>
                            </div>
                            <div className="bg-purple-50 p-4 rounded-lg">
                                <div className="text-purple-600 text-2xl mb-2">🔍</div>
                                <h5 className="font-medium text-gray-700">Smart Search</h5>
                                <p className="text-gray-600">Text selection → related content</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UploadArea;
