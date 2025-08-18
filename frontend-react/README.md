# PDF Analysis Workbench - React Frontend

A modern React frontend for the PDF Analysis Workbench that provides:

## Features

- **Real-time PDF analysis** with instant insights
- **Text selection → related content** search without page refresh
- **AI-powered insights** generation (takeaways, contradictions, examples, facts)
- **Drag & drop PDF upload** with progress tracking
- **Responsive 3-column layout** (insights, PDF viewer, actions)
- **Professional UI** with loading states and error handling

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- FastAPI backend running on port 8000

### Installation

```bash
# Navigate to React frontend directory
cd frontend-react

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

### Production Build

```bash
npm run build
```

## Architecture

```
src/
├── components/
│   ├── Layout/ThreeColumnLayout.js     # Main layout component
│   ├── PDFViewer/
│   │   ├── PDFViewer.js               # PDF display with tabs
│   │   └── UploadArea.js              # Drag & drop upload
│   └── Sidebar/
│       ├── InsightsPanel.js           # AI insights display
│       ├── RelatedContentPanel.js     # Related content search
│       └── ActionControlsPanel.js     # Summary & podcast actions
├── services/
│   └── api.js                         # FastAPI backend integration
└── hooks/                             # Custom React hooks (future)
```

## Key Improvements over Streamlit

✅ **Real-time updates** - No page refresh needed for text selection
✅ **Better PDF integration** - Smooth iframe handling
✅ **Professional UI** - Modern React components with Tailwind CSS
✅ **Responsive design** - Works on desktop, tablet, mobile
✅ **Better state management** - Efficient caching and updates
✅ **WebSocket support** - Real-time processing updates (ready)

## API Integration

The React app connects to your existing FastAPI backend:

- `POST /session/create` - Create new session
- `POST /upload/bulk` - Upload PDFs
- `GET /api/documents/{id}/content` - Get document content
- `POST /api/insights/generate` - Generate AI insights
- `POST /search/related-content` - Search related content

## Usage

1. **Upload PDFs** - Drag & drop multiple PDFs
2. **View insights** - AI-generated takeaways appear automatically
3. **Select text** - Highlight text in PDF to find related content
4. **Generate summaries** - Use action panel for summaries and podcasts

## Technologies

- React 18 with hooks
- Tailwind CSS for styling
- Axios for API calls
- react-dropzone for file upload
- Lucide React for icons
- WebSocket support for real-time updates
