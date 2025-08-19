# Docker Commands for Windows - Linux Containers

## Check if you're using Linux containers
docker version
# Look for "OS/Arch: linux/amd64" in Server section

## Your project commands (both work on Windows with Docker Linux containers):

### Option 1: Linux-style syntax in PowerShell
```powershell
docker run -d \
  --name pdf-workbench \
  -e GEMINI_API_KEY="your-key" \
  -e AZURE_TTS_KEY="your-key" \
  -e AZURE_TTS_ENDPOINT="your-endpoint" \
  -e ADOBE_EMBED_API_KEY="your-adobe-key" \
  -p 8080:8080 \
  pdf-workbench:latest
```

### Option 2: PowerShell-native syntax
```powershell
docker run -d `
  --name pdf-workbench `
  --env GEMINI_API_KEY="your-key" `
  --env AZURE_TTS_KEY="your-key" `
  --env AZURE_TTS_ENDPOINT="your-endpoint" `
  --env ADOBE_EMBED_API_KEY="your-adobe-key" `
  -p 8080:8080 `
  pdf-workbench:latest
```

### Option 3: All on one line (simplest)
```powershell
docker run -d --name pdf-workbench -e GEMINI_API_KEY="your-key" -e AZURE_TTS_KEY="your-key" -e AZURE_TTS_ENDPOINT="your-endpoint" -e ADOBE_EMBED_API_KEY="your-adobe-key" -p 8080:8080 pdf-workbench:latest
```

## Benefits of Linux Containers on Windows:
✅ Better performance with WSL 2
✅ More compatible with most Docker images
✅ Same containers work on Linux servers
✅ Better resource efficiency
✅ Your project uses Linux base images anyway
