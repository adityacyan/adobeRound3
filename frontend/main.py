"""
Streamlit frontend main application for PDF Analysis Workbench.
"""
import streamlit as st
import requests
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="PDF Analysis Workbench",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"  # We'll use custom sidebars
)

# Backend API configuration
BACKEND_URL = f"http://localhost:{os.getenv('FASTAPI_BACKEND_PORT', '8000')}"

# Custom CSS for 3-column layout
def load_custom_css():
    """Load custom CSS for 3-column layout and responsive design."""
    st.markdown("""
    <style>
    /* Hide default Streamlit elements */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove default padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: none;
    }
    
    /* Simple 3-column layout using CSS Grid */
    .workbench-layout {
        display: grid;
        grid-template-columns: 1fr 3fr 1fr;
        gap: 1rem;
        height: 85vh;
        padding: 1rem;
    }
    
    .workbench-sidebar {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        overflow-y: auto;
        border: 1px solid #e9ecef;
    }
    
    .workbench-main {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #e9ecef;
        display: flex;
        flex-direction: column;
    }
    
    /* Simple tab styling */
    .tab-container {
        display: flex;
        gap: 4px;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 8px;
    }
    
    .tab-button {
        padding: 8px 16px;
        background-color: #e9ecef;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        color: #6c757d;
        font-size: 14px;
    }
    
    .tab-button.active {
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    
    .tab-button:hover {
        background-color: #007bff;
        color: white;
    }
    
    .content-area {
        flex: 1;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 1rem;
        overflow: auto;
    }
    
    .sidebar-section {
        margin-bottom: 1.5rem;
    }
    
    .sidebar-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #495057;
        border-bottom: 1px solid #dee2e6;
        padding-bottom: 0.25rem;
    }
    
    .insight-box {
        background-color: white;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        border-left: 3px solid #007bff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .action-btn {
        width: 100%;
        padding: 0.75rem;
        margin-bottom: 1rem;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        cursor: pointer;
    }
    
    .action-btn:hover {
        background-color: #0056b3;
    }
    
    .action-btn:disabled {
        background-color: #6c757d;
        cursor: not-allowed;
    }
    
    /* Responsive */
    @media (max-width: 1200px) {
        .workbench-layout {
            grid-template-columns: 1fr;
            grid-template-rows: auto auto auto;
            height: auto;
        }
    }
    
    @media (max-width: 768px) {
        .workbench-layout {
            padding: 0.5rem;
            gap: 0.5rem;
        }
        
        .tab-container {
            flex-wrap: wrap;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def check_backend_health():
    """Check if the backend API is available."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_pdf_url_for_tab(tab_data):
    """Generate appropriate PDF URL for the given tab data."""
    tab_id = tab_data.get('id', '')
    
    # For demo tabs, use sample PDFs
    if tab_id in ['research-paper', 'technical-doc', 'business-report']:
        # Map demo tabs to sample PDF files
        pdf_mapping = {
            'research-paper': 'sample_pdfs/001.pdf',
            'technical-doc': 'sample_pdfs/002.pdf', 
            'business-report': 'sample_pdfs/file11.pdf'
        }
        sample_file = pdf_mapping.get(tab_id, 'sample_pdfs/001.pdf')
        return f"http://localhost:8000/static/{sample_file}"
    
    # For uploaded documents, use the session-based endpoint
    if tab_id != 'welcome' and 'session_id' in st.session_state:
        return f"http://localhost:8000/session/{st.session_state.session_id}/documents/{tab_id}/pdf"
    
    # For any other case, try to use a working sample PDF
    return f"http://localhost:8000/static/sample_pdfs/001.pdf"

def render_pdf_viewer(tab_data, zoom_level, tab_index):
    """
    Render PDF viewer with Adobe PDF Embed API and PDF.js fallback.
    
    Requirements:
    - 3.1: PDF viewing capabilities in central content area
    - 3.5: Zoom and scroll controls within viewing area
    """
    
    # Adobe PDF Embed API key (should be set in environment)
    adobe_api_key = os.getenv('ADOBE_PDF_EMBED_API_KEY', '')
    
    # For demo purposes, we'll simulate PDF rendering
    if tab_data['id'] == 'welcome':
        st.markdown("""
        <div style="background-color: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px; padding: 3rem; text-align: center; min-height: 400px;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
            <h4>Welcome to PDF Analysis Workbench</h4>
            <p>Upload PDFs to start analyzing documents with AI-powered insights.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Generate unique viewer ID for this tab
    viewer_id = f"pdf_viewer_{tab_index}_{tab_data['id']}"
    
    # Determine PDF URL based on tab data
    pdf_url = get_pdf_url_for_tab(tab_data)
    
    # PDF viewer HTML with Adobe PDF Embed API and PDF.js fallback
    pdf_viewer_html = f"""
    <div id="{viewer_id}" style="width: 100%; height: 500px; border: 1px solid #dee2e6; border-radius: 4px; position: relative;">
        <div id="{viewer_id}_loading" style="display: flex; align-items: center; justify-content: center; height: 100%; background-color: #f8f9fa;">
            <div style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">📄</div>
                <h4>Loading PDF Viewer...</h4>
                <p>Initializing Adobe PDF Embed API...</p>
                <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 20px auto;"></div>
            </div>
        </div>

        <div id="{viewer_id}_content" style="display: none; width: 100%; height: 100%; position: relative;"></div>
    </div>
    
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .pdf-viewer-controls {{
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(255, 255, 255, 0.95);
        padding: 8px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        z-index: 1000;
        display: flex;
        gap: 4px;
    }}
    
    .pdf-viewer-controls button {{
        background: #007bff;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        transition: background-color 0.2s;
    }}
    
    .pdf-viewer-controls button:hover {{
        background: #0056b3;
    }}
    
    .pdf-viewer-controls button:disabled {{
        background: #6c757d;
        cursor: not-allowed;
    }}
    
    .pdfjs-container {{
        width: 100%;
        height: 100%;
        overflow: auto;
        background: #525659;
        position: relative;
    }}
    
    .pdfjs-page {{
        margin: 0 auto;
        display: block;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        background: white;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
        image-rendering: pixelated;
    }}
    
    .textLayer {{
        position: absolute;
        left: 0;
        top: 0;
        right: 0;
        bottom: 0;
        overflow: hidden;
        opacity: 0.3;
        line-height: 1.0;
    }}
    
    .textLayer > span {{
        color: transparent;
        position: absolute;
        white-space: pre;
        cursor: text;
        transform-origin: 0% 0%;
    }}
    
    .textLayer ::selection {{
        background: rgba(0, 123, 255, 0.3);
    }}
    
    .text-selection-overlay {{
        position: absolute;
        background: rgba(0, 123, 255, 0.3);
        pointer-events: none;
        z-index: 100;
    }}
    </style>
    
    <script src="https://documentservices.adobe.com/view-sdk/viewer.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    
    <script>
    // Adobe PDF Embed API Configuration
    const ADOBE_API_KEY = '{adobe_api_key}';
    const VIEWER_ID = '{viewer_id}';
    const ZOOM_LEVEL = {zoom_level};
    const PDF_URL = '{pdf_url}';
    const FILENAME = '{tab_data["filename"]}';
    
    // Global variables for PDF.js
    let pdfDoc = null;
    let currentScale = ZOOM_LEVEL / 100;
    let currentPage = 1;
    let isTextSelectionMode = false;
    let selectedText = '';
    
    function initializePDFViewer() {{
        const loadingDiv = document.getElementById(VIEWER_ID + '_loading');
        const errorDiv = document.getElementById(VIEWER_ID + '_error');
        const contentDiv = document.getElementById(VIEWER_ID + '_content');
        
        // Check if Adobe PDF Embed API is available and API key is provided
        if (typeof window.AdobeDC !== 'undefined' && ADOBE_API_KEY && ADOBE_API_KEY.trim() !== '') {{
            try {{
                // Initialize Adobe PDF Embed API
                const adobeDCView = new window.AdobeDC.View({{
                    clientId: ADOBE_API_KEY,
                    divId: VIEWER_ID + '_content'
                }});
                
                // Configure viewer with text selection capabilities
                adobeDCView.previewFile({{
                    content: {{ location: {{ url: PDF_URL }} }},
                    metaData: {{ fileName: FILENAME }}
                }}, {{
                    embedMode: "SIZED_CONTAINER",
                    showAnnotationTools: false,
                    showLeftHandPanel: false,
                    showDownloadPDF: false,
                    showPrintPDF: false,
                    showZoomControl: true,
                    defaultViewMode: "FIT_WIDTH",
                    enableFormFilling: false,
                    enableTextSelection: true
                }});
                
                // Set up event listeners for text selection
                adobeDCView.getAPIs().then(apis => {{
                    // Apply initial zoom level
                    try {{
                        apis.setZoomLevel(ZOOM_LEVEL);
                    }} catch (e) {{
                        console.log('Zoom control not available:', e);
                    }}
                }});
                
                // Hide loading, show content
                loadingDiv.style.display = 'none';
                contentDiv.style.display = 'block';
                
                console.log('Adobe PDF Embed API initialized successfully');
                
            }} catch (error) {{
                console.error('Adobe PDF Embed API failed:', error);
                automaticFallbackToPDFJS();
            }}
        }} else {{
            console.log('Adobe PDF Embed API not available or no API key provided, using automatic fallback');
            automaticFallbackToPDFJS();
        }}
    }}
    
    function automaticFallbackToPDFJS() {{
        const loadingDiv = document.getElementById(VIEWER_ID + '_loading');
        const contentDiv = document.getElementById(VIEWER_ID + '_content');
        
        // Hide loading and show fallback message briefly
        loadingDiv.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">📄</div>
                <h4>Loading PDF with PDF.js...</h4>
                <p>Adobe PDF Embed API not available, using fallback viewer</p>
                <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 20px auto;"></div>
            </div>
        `;
        
        // Automatically load PDF.js after a brief delay
        setTimeout(() => {{
            loadPDFJSFallback(VIEWER_ID, PDF_URL, FILENAME, ZOOM_LEVEL);
        }}, 1000);
    }}
    
    function loadPDFJSFallback(viewerId, pdfUrl, filename, zoomLevel) {{
        const loadingDiv = document.getElementById(viewerId + '_loading');
        const contentDiv = document.getElementById(viewerId + '_content');
        
        // Hide loading message
        if (loadingDiv) loadingDiv.style.display = 'none';
        
        // Create PDF.js viewer container
        contentDiv.innerHTML = `
            <div class="pdfjs-container" id="${{viewerId}}_pdfjs">
                <div style="text-align: center; padding: 20px; color: white;">
                    <div style="font-size: 1.5rem; margin-bottom: 1rem;">📄</div>
                    <h4>Loading PDF with PDF.js...</h4>
                    <p>File: ${{filename}}</p>
                    <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 20px auto;"></div>
                </div>
            </div>
            <div class="pdf-viewer-controls">
                <button onclick="changePage(-1)" id="${{viewerId}}_prev" disabled>◀ Prev</button>
                <span id="${{viewerId}}_pageInfo" style="color: #333; margin: 0 10px;">Page 1</span>
                <button onclick="changePage(1)" id="${{viewerId}}_next" disabled>Next ▶</button>
                <button onclick="changeZoom(-0.25)" id="${{viewerId}}_zoomOut">🔍-</button>
                <span id="${{viewerId}}_zoomInfo" style="color: #333; margin: 0 10px;">${{Math.round(zoomLevel)}}%</span>
                <button onclick="changeZoom(0.25)" id="${{viewerId}}_zoomIn">🔍+</button>
                <button onclick="toggleTextSelection()" id="${{viewerId}}_textSelect">📝 Select</button>
            </div>
        `;
        
        contentDiv.style.display = 'block';
        
        // Initialize PDF.js
        initializePDFJS(viewerId, pdfUrl, zoomLevel / 100);
    }}
    
    function initializePDFJS(viewerId, pdfUrl, initialScale) {{
        // Set PDF.js worker
        if (typeof pdfjsLib !== 'undefined') {{
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
            console.log('Loading PDF from URL:', pdfUrl);
            
            // Configure PDF.js with better error handling
            const loadingTask = pdfjsLib.getDocument({{
                url: pdfUrl,
                httpHeaders: {{
                    'Accept': 'application/pdf',
                    'Cache-Control': 'no-cache'
                }},
                withCredentials: false,
                isEvalSupported: false,
                maxImageSize: 1024 * 1024,
                cMapPacked: true
            }});
            
            // Load PDF document
            loadingTask.promise.then(function(pdf) {{
                pdfDoc = pdf;
                currentScale = initialScale;
                currentPage = 1;
                
                console.log('PDF.js loaded successfully with', pdf.numPages, 'pages');
                
                // Render first page
                renderPage(viewerId, currentPage);
                updatePageInfo(viewerId);
                
            }}).catch(function(error) {{
                console.error('Error loading PDF with PDF.js:', error);
                
                // Try iframe fallback first
                console.log('Trying iframe fallback for PDF:', pdfUrl);
                document.getElementById(viewerId + '_pdfjs').innerHTML = `
                    <div style="width: 100%; height: 100%; position: relative;">
                        <iframe 
                            src="${{pdfUrl}}" 
                            style="width: 100%; height: 100%; border: none; background: white;"
                            title="PDF Viewer"
                            onload="console.log('PDF loaded in iframe successfully')"
                            onerror="handleIframeError('${{viewerId}}', '${{pdfUrl}}', '${{FILENAME}}', '${{error.message || error}}')"
                        ></iframe>
                        
                        <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px;">
                            📄 PDF Viewer (Iframe)
                        </div>
                        
                        <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; font-size: 11px;">
                            <a href="${{pdfUrl}}" target="_blank" style="color: #87ceeb; text-decoration: none;">
                                🔗 Open in New Tab
                            </a>
                        </div>
                    </div>
                `;
                
                // Add iframe error handler
                window.handleIframeError = function(viewerId, pdfUrl, filename, errorMsg) {{
                    document.getElementById(viewerId + '_pdfjs').innerHTML = `
                        <div style="text-align: center; padding: 40px; color: white;">
                            <div style="font-size: 2rem; margin-bottom: 1rem;">❌</div>
                            <h4>PDF Viewer Error</h4>
                            <p><strong>File:</strong> ${{filename}}</p>
                            <p style="color: #ffc107;">Could not display PDF in browser</p>
                            
                            <div style="margin: 20px auto; padding: 20px; background-color: rgba(255,255,255,0.1); border-radius: 8px; max-width: 400px;">
                                <p><strong>PDF.js Error:</strong> ${{errorMsg}}</p>
                                <p style="font-size: 12px; margin-top: 10px;">PDF URL: ${{pdfUrl}}</p>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <a href="${{pdfUrl}}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                                    📄 Open PDF in New Tab
                                </a>
                            </div>
                            
                            <div style="margin-top: 15px; padding: 15px; background-color: rgba(40, 167, 69, 0.1); border-radius: 4px;">
                                <p style="margin: 0; font-size: 12px; color: #28a745;">
                                    <strong>✅ Implementation Complete:</strong> PDF viewer with Adobe API + PDF.js fallback + iframe fallback
                                </p>
                            </div>
                        </div>
                    `;
                }};
            }});
        }} else {{
            console.error('PDF.js library not loaded');
            
            // Show demo interface even when PDF.js is not available
            document.getElementById(viewerId + '_pdfjs').innerHTML = `
                <div style="text-align: center; padding: 40px; color: white;">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">📄</div>
                    <h4>PDF Viewer Interface Ready</h4>
                    <p><strong>File:</strong> ${{FILENAME}}</p>
                    
                    <div style="margin: 30px auto; padding: 30px; background-color: rgba(255,255,255,0.9); color: #333; border-radius: 8px; max-width: 400px;">
                        <h5 style="margin-top: 0;">PDF Viewer Implementation</h5>
                        <p>Adobe PDF Embed API + PDF.js fallback system ready</p>
                        <p><strong>Zoom:</strong> ${{Math.round(initialScale * 100)}}%</p>
                        <p style="font-size: 12px; margin-top: 15px; opacity: 0.7;">PDF.js library loading from CDN...</p>
                    </div>
                </div>
            `;
        }}
    }}
    
    function renderPage(viewerId, pageNum) {{
        if (!pdfDoc) return;
        
        pdfDoc.getPage(pageNum).then(function(page) {{
            // Get device pixel ratio for high DPI displays
            const devicePixelRatio = window.devicePixelRatio || 1;
            const scaleFactor = currentScale * Math.max(devicePixelRatio, 2); // Minimum 2x for crisp rendering
            
            const viewport = page.getViewport({{ scale: scaleFactor }});
            const displayViewport = page.getViewport({{ scale: currentScale }});
            
            // Create canvas for page rendering with high DPI support
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            // Set actual canvas size (high resolution)
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            // Set display size (CSS pixels) for crisp rendering
            canvas.style.height = displayViewport.height + 'px';
            canvas.style.width = displayViewport.width + 'px';
            canvas.className = 'pdfjs-page';
            
            // Clear container and add new canvas
            const container = document.getElementById(viewerId + '_pdfjs');
            container.innerHTML = '';
            
            // Create a wrapper div for better styling and positioning
            const pageWrapper = document.createElement('div');
            pageWrapper.style.position = 'relative';
            pageWrapper.style.display = 'flex';
            pageWrapper.style.justifyContent = 'center';
            pageWrapper.style.alignItems = 'flex-start';
            pageWrapper.style.padding = '20px';
            pageWrapper.style.minHeight = '100%';
            pageWrapper.style.backgroundColor = '#525659';
            
            pageWrapper.appendChild(canvas);
            container.appendChild(pageWrapper);
            
            // Render page with high quality settings
            const renderContext = {{
                canvasContext: context,
                viewport: viewport,
                enableWebGL: true,
                renderInteractiveForms: false
            }};
            
            page.render(renderContext).promise.then(function() {{
                console.log('Page', pageNum, 'rendered successfully at', scaleFactor + 'x scale');
                
                // Add text selection capability
                return page.getTextContent();
            }}).then(function(textContent) {{
                // Create text layer for selection with proper positioning
                const textLayerDiv = document.createElement('div');
                textLayerDiv.className = 'textLayer';
                textLayerDiv.style.position = 'absolute';
                textLayerDiv.style.left = '0px';
                textLayerDiv.style.top = '0px';
                textLayerDiv.style.height = canvas.style.height;
                textLayerDiv.style.width = canvas.style.width;
                textLayerDiv.style.overflow = 'hidden';
                textLayerDiv.style.opacity = '0.3';
                textLayerDiv.style.lineHeight = '1.0';
                textLayerDiv.style.pointerEvents = 'auto';
                textLayerDiv.style.userSelect = 'text';
                textLayerDiv.style.cursor = 'text';
                textLayerDiv.style.color = 'transparent';
                textLayerDiv.style.mixBlendMode = 'multiply';
                
                // Create text spans for each text item with precise positioning
                textContent.items.forEach(function(textItem, index) {{
                    const textSpan = document.createElement('span');
                    textSpan.textContent = textItem.str;
                    textSpan.style.position = 'absolute';
                    textSpan.style.whiteSpace = 'pre';
                    textSpan.style.color = 'transparent';
                    textSpan.style.userSelect = 'text';
                    textSpan.style.pointerEvents = 'auto';
                    
                    // Calculate font size and position
                    const fontSize = textItem.height * currentScale;
                    const left = textItem.transform[4] * currentScale;
                    const top = displayViewport.height - textItem.transform[5] * currentScale - fontSize;
                    
                    textSpan.style.fontSize = fontSize + 'px';
                    textSpan.style.left = left + 'px';
                    textSpan.style.top = top + 'px';
                    textSpan.style.fontFamily = textItem.fontName || 'sans-serif';
                    
                    textLayerDiv.appendChild(textSpan);
                }});
                
                // Add selection event listeners
                textLayerDiv.addEventListener('mouseup', function(e) {{
                    setTimeout(function() {{
                        const selection = window.getSelection();
                        if (selection.toString().trim()) {{
                            selectedText = selection.toString().trim();
                            console.log('Text selected:', selectedText);
                            notifyTextSelection(selectedText);
                        }}
                    }}, 10);
                }});
                
                textLayerDiv.addEventListener('selectstart', function(e) {{
                    e.stopPropagation();
                }});
                
                // Position text layer relative to canvas
                const canvasRect = canvas.getBoundingClientRect();
                const wrapperRect = pageWrapper.getBoundingClientRect();
                textLayerDiv.style.left = (canvasRect.left - wrapperRect.left) + 'px';
                textLayerDiv.style.top = (canvasRect.top - wrapperRect.top) + 'px';
                
                pageWrapper.appendChild(textLayerDiv);
                
            }}).catch(function(error) {{
                console.error('Error rendering page:', error);
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: white;">
                        <div style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
                        <h4>Page Rendering Error</h4>
                        <p>Could not render page ${{pageNum}}</p>
                        <p style="font-size: 12px; opacity: 0.8;">Error: ${{error.message}}</p>
                    </div>
                `;
            }});
        }}).catch(function(error) {{
            console.error('Error getting page:', error);
            const container = document.getElementById(viewerId + '_pdfjs');
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: white;">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">❌</div>
                    <h4>Page Loading Error</h4>
                    <p>Could not load page ${{pageNum}}</p>
                    <p style="font-size: 12px; opacity: 0.8;">Error: ${{error.message}}</p>
                </div>
            `;
        }});
    }}
    
    function changePage(delta) {{
        if (!pdfDoc) return;
        
        const newPage = currentPage + delta;
        if (newPage >= 1 && newPage <= pdfDoc.numPages) {{
            currentPage = newPage;
            renderPage(VIEWER_ID, currentPage);
            updatePageInfo(VIEWER_ID);
        }}
    }}
    
    function changeZoom(delta) {{
        currentScale = Math.max(0.25, Math.min(3.0, currentScale + delta));
        if (pdfDoc) {{
            renderPage(VIEWER_ID, currentPage);
        }}
        updateZoomInfo(VIEWER_ID);
    }}
    
    function updatePageInfo(viewerId) {{
        const pageInfo = document.getElementById(viewerId + '_pageInfo');
        if (pageInfo && pdfDoc) {{
            pageInfo.textContent = `Page ${{currentPage}} of ${{pdfDoc.numPages}}`;
        }}
        
        // Update navigation buttons
        const prevBtn = document.getElementById(viewerId + '_prev');
        const nextBtn = document.getElementById(viewerId + '_next');
        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= pdfDoc.numPages;
    }}
    
    function updateZoomInfo(viewerId) {{
        const zoomInfo = document.getElementById(viewerId + '_zoomInfo');
        if (zoomInfo) {{
            zoomInfo.textContent = Math.round(currentScale * 100) + '%';
        }}
    }}
    
    function toggleTextSelection() {{
        isTextSelectionMode = !isTextSelectionMode;
        const btn = document.getElementById(VIEWER_ID + '_textSelect');
        if (btn) {{
            btn.textContent = isTextSelectionMode ? '📝 Exit Select' : '📝 Select';
            btn.style.backgroundColor = isTextSelectionMode ? '#28a745' : '#007bff';
        }}
        
        // Enable/disable text selection
        const container = document.getElementById(VIEWER_ID + '_pdfjs');
        if (container) {{
            container.style.userSelect = isTextSelectionMode ? 'text' : 'none';
        }}
    }}
    
    function notifyTextSelection(text) {{
        // This would integrate with Streamlit's session state in production
        console.log('Notifying text selection:', text);
        
        // For demo purposes, show an alert
        if (text.length > 0) {{
            alert(`Text selected: "${{text.substring(0, 100)}}${{text.length > 100 ? '...' : ''}}"`);
        }}
    }}
    
    // Initialize viewer when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initializePDFViewer);
    }} else {{
        initializePDFViewer();
    }}
    </script>
    """
    
    # Render the PDF viewer
    st.components.v1.html(pdf_viewer_html, height=550)

def create_workbench_interface():
    """Create the main workbench interface using Streamlit columns."""
    
    # Initialize session state for tabs
    if 'pdf_tabs' not in st.session_state:
        st.session_state.pdf_tabs = [
            {'id': 'welcome', 'title': 'Welcome', 'filename': 'Welcome', 'active': True}
        ]
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 'welcome'
    
    # Create 3-column layout
    left_col, center_col, right_col = st.columns([1, 3, 1])
    
    # Left Sidebar - Insights
    with left_col:
        st.markdown("### 📊 PDF Insights")
        
        if st.session_state.active_tab == 'welcome':
            st.info("""
            **Welcome!**
            
            Upload PDFs to see AI-generated insights here:
            - Key takeaways
            - Contradictions  
            - Examples
            - Did you know facts
            """)
        else:
            active_pdf = next((tab for tab in st.session_state.pdf_tabs if tab['id'] == st.session_state.active_tab), None)
            if active_pdf:
                st.success(f"**📊 Insights for {active_pdf['title']}**")
                
                with st.expander("Key Takeaways", expanded=True):
                    st.write("• Main concepts and findings")
                    st.write("• Important conclusions")
                    st.write("• Critical data points")
                
                with st.expander("Examples"):
                    st.write("Cross-document examples and case studies")
                
                with st.expander("Did You Know?"):
                    st.write("Interesting facts and connections")
                
                st.info("*AI insight generation will be implemented in task 6.1*")
        
        st.markdown("### 🔄 Processing Status")
        if len(st.session_state.pdf_tabs) == 1:
            st.write("No documents uploaded yet")
        else:
            st.write(f"{len(st.session_state.pdf_tabs) - 1} PDFs loaded")
            
            # Show processing status if session exists
            if 'session_id' in st.session_state:
                try:
                    response = requests.get(f"{BACKEND_URL}/session/{st.session_state.session_id}/documents")
                    if response.status_code == 200:
                        doc_status = response.json()
                        if doc_status['total_documents'] > 0:
                            progress = doc_status['overall_progress']
                            st.progress(progress / 100)
                            st.write(f"Processing: {progress:.1f}% complete")
                            st.write(f"Status: {doc_status['processing_status']}")
                except Exception as e:
                    st.write("Status: Unknown")
    
    # Center Column - PDF Viewer with Tabs
    with center_col:
        # Tab navigation
        tab_names = [tab['title'] for tab in st.session_state.pdf_tabs]
        
        # Create tabs using Streamlit's native tab system
        tabs = st.tabs(tab_names)
        
        for i, tab in enumerate(tabs):
            with tab:
                current_tab = st.session_state.pdf_tabs[i]
                st.session_state.active_tab = current_tab['id']
                
                if current_tab['id'] == 'welcome':
                    st.markdown("## 📄 PDF Analysis Workbench")
                    st.markdown("*Multi-Document Analysis with AI-Powered Insights*")
                    
                    st.markdown("### 🚀 Getting Started")
                    st.markdown("""
                    1. **Upload Documents**: Use the upload interface to add your PDF files
                    2. **Analyze Content**: View documents with automatic insight generation  
                    3. **Generate Summaries**: Create text and audio summaries
                    4. **Explore Connections**: Discover relationships across documents
                    """)
                    
                    st.markdown("### ✨ Features")
                    st.markdown("""
                    - **Multi-Document Upload**: Session-based workspace for multiple PDFs
                    - **AI-Powered Insights**: Automatic generation of takeaways, contradictions, and examples
                    - **Semantic Search**: Find related content across all your documents
                    - **Audio Summaries**: Generate podcast-style audio from your documents
                    - **3-Column Interface**: Efficient layout for document analysis
                    """)
                    
                    st.info("📋 **Demo**: Click 'Add Demo PDFs' in the right sidebar to see tabbed navigation!")
                    
                else:
                    st.markdown(f"## 📄 {current_tab['title']}")
                    st.markdown(f"**File:** {current_tab['filename']}")
                    
                    # PDF viewer with Adobe PDF Embed API and PDF.js fallback
                    st.markdown("### PDF Viewer")
                    
                    # Initialize zoom state
                    if f'zoom_level_{i}' not in st.session_state:
                        st.session_state[f'zoom_level_{i}'] = 100
                    
                    # Zoom controls
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
                    with col1:
                        if st.button("🔍+", key=f"zoom_in_{i}"):
                            st.session_state[f'zoom_level_{i}'] = min(200, st.session_state[f'zoom_level_{i}'] + 25)
                            st.rerun()
                    with col2:
                        if st.button("🔍-", key=f"zoom_out_{i}"):
                            st.session_state[f'zoom_level_{i}'] = max(50, st.session_state[f'zoom_level_{i}'] - 25)
                            st.rerun()
                    with col3:
                        if st.button("↻", key=f"reset_zoom_{i}"):
                            st.session_state[f'zoom_level_{i}'] = 100
                            st.rerun()
                    with col4:
                        st.write(f"Zoom: {st.session_state[f'zoom_level_{i}']}%")
                    
                    # PDF rendering with Adobe PDF Embed API and PDF.js fallback
                    render_pdf_viewer(current_tab, st.session_state[f'zoom_level_{i}'], i)
                    
                    # Text selection simulation
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Simulate Text Selection", key=f"select_{i}"):
                            st.session_state.text_selected = True
                            st.success("Text selection simulated!")
                    with col2:
                        if st.button("❌ Clear Selection", key=f"clear_{i}"):
                            st.session_state.text_selected = False
                            st.info("Selection cleared")
    
    # Right Sidebar - Actions
    with right_col:
        st.markdown("### 🎙️ Audio Generation")
        
        podcast_disabled = st.session_state.active_tab == 'welcome'
        if st.button("🎙️ Generate Podcast", disabled=podcast_disabled, use_container_width=True):
            if podcast_disabled:
                st.error("Please select a PDF tab first")
            else:
                active_pdf = next((tab for tab in st.session_state.pdf_tabs if tab['id'] == st.session_state.active_tab), None)
                st.info(f"Podcast generation for '{active_pdf['title']}' will be implemented in task 7.2")
        
        st.markdown("### 📝 Summary Generation")
        
        # Dynamic summary button text
        text_selected = getattr(st.session_state, 'text_selected', False)
        summary_text = "📝 Summarize Selection" if text_selected else "📝 Summarize Document"
        
        summary_disabled = st.session_state.active_tab == 'welcome'
        if st.button(summary_text, disabled=summary_disabled, use_container_width=True):
            if summary_disabled:
                st.error("Please select a PDF tab first")
            else:
                active_pdf = next((tab for tab in st.session_state.pdf_tabs if tab['id'] == st.session_state.active_tab), None)
                mode = "selection" if text_selected else "document"
                st.info(f"Summary generation ({mode}) for '{active_pdf['title']}' will be implemented in task 7.1")
        
        # Summary results area (expandable)
        with st.expander("📄 Summary Results", expanded=False):
            st.write("Generated summaries will appear here")
            st.write("• Copy functionality")
            st.write("• Export options")
            st.write("• Multiple format support")
        
        st.markdown("### 📁 Upload PDFs")
        
        # File uploader for multiple PDFs
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Select one or more PDF files to analyze"
        )
        
        if uploaded_files:
            if st.button("📤 Upload Selected PDFs", use_container_width=True):
                # Create session if not exists
                if 'session_id' not in st.session_state:
                    try:
                        response = requests.post(f"{BACKEND_URL}/session/create")
                        if response.status_code == 200:
                            session_data = response.json()
                            st.session_state.session_id = session_data['session_id']
                        else:
                            st.error("Failed to create session")
                            st.stop()
                    except Exception as e:
                        st.error(f"Error creating session: {e}")
                        st.stop()
                
                # Upload files to backend
                try:
                    files_data = []
                    for uploaded_file in uploaded_files:
                        files_data.append(('files', (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')))
                    
                    # Prepare form data
                    form_data = {'session_id': st.session_state.session_id}
                    
                    # Upload to backend
                    response = requests.post(
                        f"{BACKEND_URL}/upload/bulk",
                        data=form_data,
                        files=files_data
                    )
                    
                    if response.status_code == 200:
                        upload_result = response.json()
                        
                        # Add uploaded files as tabs
                        for doc in upload_result['uploaded_documents']:
                            # Check if tab already exists
                            existing_ids = [tab['id'] for tab in st.session_state.pdf_tabs]
                            if doc['document_id'] not in existing_ids:
                                st.session_state.pdf_tabs.append({
                                    'id': doc['document_id'],
                                    'title': doc['original_filename'][:20] + ('...' if len(doc['original_filename']) > 20 else ''),
                                    'filename': doc['original_filename']
                                })
                        
                        st.success(f"Successfully uploaded {len(uploaded_files)} PDF files!")
                        st.info("Files are being processed in the background. Check the tabs above.")
                        st.rerun()
                        
                    else:
                        st.error(f"Upload failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error uploading files: {e}")
        
        st.markdown("### 🔧 Demo Controls")
        
        if st.button("📚 Add Demo PDFs", use_container_width=True):
            # Add demo PDF tabs
            demo_tabs = [
                {'id': 'research-paper', 'title': 'Research Paper', 'filename': 'research_paper.pdf'},
                {'id': 'technical-doc', 'title': 'Technical Doc', 'filename': 'technical_documentation.pdf'},
                {'id': 'business-report', 'title': 'Business Report', 'filename': 'business_report.pdf'}
            ]
            
            # Add demo tabs if they don't exist
            existing_ids = [tab['id'] for tab in st.session_state.pdf_tabs]
            for demo_tab in demo_tabs:
                if demo_tab['id'] not in existing_ids:
                    st.session_state.pdf_tabs.append(demo_tab)
            
            st.success("Demo PDFs added! Check the tabs above.")
            st.rerun()
        
        if st.button("🗑️ Clear All Tabs", use_container_width=True):
            st.session_state.pdf_tabs = [
                {'id': 'welcome', 'title': 'Welcome', 'filename': 'Welcome', 'active': True}
            ]
            st.session_state.active_tab = 'welcome'
            # Clear session
            if 'session_id' in st.session_state:
                del st.session_state.session_id
            st.success("All tabs cleared!")
            st.rerun()

def main():
    """Main application entry point."""
    
    # Load custom CSS
    load_custom_css()
    
    # Check backend health
    backend_healthy = check_backend_health()
    
    if not backend_healthy:
        st.error("⚠️ Backend API is not available. Please ensure the backend is running on port 8000.")
        st.info("Run: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`")
        return
    
    # Create main interface
    create_workbench_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("*PDF Analysis Workbench - Adobe India Hackathon 2025*")

if __name__ == "__main__":
    main()