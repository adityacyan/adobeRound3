# Adobe PDF Embed API Setup with PDF.js Fallback

## Overview
The PDF viewer now supports BOTH Adobe PDF Embed API and PDF.js with automatic fallback and manual switching.

## Features
✅ **Adobe PDF Embed** - Native PDF rendering with superior text selection
✅ **PDF.js Fallback** - Works when Adobe isn't available or configured
✅ **Advanced Text Selection** - Enhanced coordinate tracking for PDF.js
✅ **Manual Toggle** - Switch between Adobe and PDF.js viewers
✅ **Environment Configuration** - Store Adobe Client ID in .env file

## Setup Options

### Option 1: Use Adobe PDF Embed (Recommended)

1. **Get Adobe Client ID** (Free):
   - Go to https://developer.adobe.com/document-services/apis/pdf-embed/
   - Click "Get credentials" 
   - Create a free account or sign in
   - Create a new project
   - Copy the Client ID

2. **Add to .env file**:
   ```
   REACT_APP_ADOBE_CLIENT_ID=your_actual_client_id_here
   ```

3. **Restart React app** to load environment variables

### Option 2: Use PDF.js Only

If you prefer not to use Adobe or want to test immediately:
- Leave `REACT_APP_ADOBE_CLIENT_ID=YOUR_CLIENT_ID_HERE` in .env
- The viewer will automatically use PDF.js fallback

## Text Selection Features

### Adobe PDF Embed API
```javascript
// Perfect text selection via Adobe's API
adobeDCView.registerCallback(
    window.AdobeDC.View.Enum.CallbackType.TEXT_SELECTION,
    (textSelectionEvent) => {
        const text = textSelectionEvent.data.text;
        const quads = textSelectionEvent.data.quads; // Bounding boxes
        // Perfect text selection with coordinates!
    }
);
```

### Enhanced PDF.js Text Selection
```javascript
// Advanced coordinate tracking similar to your example
const getHighlightCoords = () => {
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    const rects = range.getClientRects();
    
    return {
        text: selection.toString(),
        pageNumber: currentPageNumber,
        rects: Array.from(rects).map(rect => ({
            left: rect.left,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom
        }))
    };
};
```

## UI Features

- **🔥 Red indicator** when using Adobe PDF Embed
- **📚 Blue indicator** when using PDF.js  
- **Toggle button** to switch between viewers (when Adobe is available)
- **Enhanced controls** for PDF.js (zoom, navigation)
- **Coordinate tracking** for both viewers

## Automatic Fallback Logic

1. **Adobe Client ID configured?** → Try Adobe PDF Embed
2. **Adobe API loaded?** → Use Adobe
3. **Adobe fails?** → Automatically fallback to PDF.js
4. **Manual toggle** → User can switch between viewers

## Benefits

### Adobe PDF Embed:
- Native PDF rendering (no blurriness)
- Professional UI with built-in controls
- Robust text selection API
- Better performance for large PDFs

### PDF.js Enhanced:
- Open source and reliable
- Advanced coordinate tracking
- Full control over UI
- Works offline

## Testing

1. **With Adobe**: Set Client ID → Get professional Adobe viewer
2. **Without Adobe**: Leave default → Get enhanced PDF.js viewer
3. **Toggle**: Switch between both to compare

The viewer now provides the best of both worlds with smart fallback!
