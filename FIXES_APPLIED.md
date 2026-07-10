# Fixes Applied - Docker Split Services Issues

## Issues Identified and Fixed

### 1. WebSocket Connection Failing (404 Error)
**Problem:** WebSocket endpoint `/api/ws/{session_id}` was returning 404 errors
**Root Cause:** Nginx was not configured to proxy WebSocket connections
**Fix Applied:**
- Added WebSocket proxy configuration in `frontend-react/nginx.conf`
- Configured proper WebSocket upgrade headers
- Set long timeouts for WebSocket connections (7 days)

```nginx
location /api/ws/ {
    proxy_pass http://backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    # ... other headers
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
```

### 2. Event Loop Errors in Document Processing
**Problem:** Backend logs showed "no running event loop" errors during document processing
**Root Cause:** Progress callbacks were trying to create async tasks from synchronous context
**Fix Applied:**
- Wrapped all `asyncio.create_task()` calls in try-except blocks
- Gracefully handle RuntimeError when no event loop is running
- Falls back to logging only when WebSocket updates can't be sent

**Files Modified:**
- `backend/main.py` - Multiple locations where WebSocket updates are sent

### 3. AI Insights Not Working
**Problem:** AI Insights panel was not loading insights for documents
**Root Cause:** API endpoint path mismatch - backend expects requests without `/api` prefix after nginx proxy
**Status:** Partially addressed - needs verification

**Current Configuration:**
- Backend endpoint: `/api/documents/{id}/content`
- Frontend calls: `/api/documents/{id}/content` (proxied through nginx)
- Nginx proxies `/api/` to `http://backend:8000/`

### 4. Podcast Generation - Audio Not Playing/Downloading
**Problem:** Generated podcasts couldn't be played or downloaded
**Root Causes:**
1. Audio endpoint not proxied through nginx
2. Wrong audio MIME type in frontend
3. Absolute URLs instead of relative URLs

**Fixes Applied:**

#### A. Added Audio Proxy in Nginx
```nginx
location /audio/ {
    proxy_pass http://backend:8000/audio/;
    proxy_http_version 1.1;
    # ... proxy headers
    proxy_cache_valid 200 1h;
    add_header Cache-Control "public, max-age=3600";
}
```

#### B. Fixed Audio URL Generation
**File:** `backend/audio_service.py`
- Changed from absolute URL with base_url parameter
- Now returns relative URL: `/audio/{filename}`

```python
def get_audio_url(self, audio_path: str, base_url: str = None) -> str:
    """Generate a URL for accessing the audio file."""
    filename = os.path.basename(audio_path)
    return f"/audio/{filename}"
```

#### C. Fixed Audio MIME Type
**File:** `frontend-react/src/components/Sidebar/ActionControlsPanel.js`
- Changed `type="audio/mpeg"` to `type="audio/wav"`
- Backend generates WAV files from Gemini TTS

```javascript
<audio controls className="w-full" preload="metadata">
    <source src={audioUrl} type="audio/wav" />
    <source src={audioUrl} type="audio/mpeg" />
    Your browser does not support the audio element.
</audio>
```

## Files Modified

1. `frontend-react/nginx.conf` - Added WebSocket and audio proxies
2. `backend/main.py` - Fixed event loop errors in multiple locations
3. `backend/audio_service.py` - Fixed audio URL generation
4. `frontend-react/src/components/Sidebar/ActionControlsPanel.js` - Fixed audio MIME type

## Testing Checklist

### WebSocket
- [ ] WebSocket connects successfully on page load
- [ ] Real-time document processing updates appear
- [ ] No 404 errors in browser console for `/api/ws/`

### Document Processing
- [ ] Documents upload and process without event loop errors
- [ ] Progress indicators update in real-time
- [ ] No "no running event loop" errors in backend logs

### AI Insights
- [ ] Insights panel loads for processed documents
- [ ] No 404 errors for document content endpoint
- [ ] Insights are generated and displayed correctly

### Podcast Generation
- [ ] Podcast can be generated from document content
- [ ] Audio player appears after generation
- [ ] Audio plays correctly in browser
- [ ] Download button works and saves WAV file
- [ ] No CORS or 404 errors for audio files

## Deployment Steps

1. Stop running containers:
   ```bash
   docker-compose down
   ```

2. Rebuild frontend (changes in nginx.conf and ActionControlsPanel.js):
   ```bash
   docker-compose build --no-cache frontend
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Monitor logs:
   ```bash
   docker logs adoberound3-1-backend-1 --tail 50 -f
   docker logs adoberound3-1-frontend-1 --tail 50 -f
   ```

5. Test in browser:
   - Open http://localhost:8080
   - Upload PDFs and verify processing
   - Check AI Insights panel
   - Generate podcast and test playback

## Known Limitations

1. **Audio Storage:** Audio files are stored in container's `/tmp` directory and will be lost on container restart. This is acceptable for temporary podcasts but could be improved with a volume mount if persistence is needed.

2. **Cache:** Podcast cache is stored in browser state and will be lost on page refresh. Backend doesn't track generated podcasts across sessions.

## Additional Notes

- All changes maintain backward compatibility
- No breaking changes to API endpoints
- Environment variables remain unchanged
- Docker compose configuration unchanged (except adding audio volume would be optional enhancement)
