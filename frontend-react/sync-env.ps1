# PowerShell script to sync environment variables from root .env to React .env
$rootEnv = Get-Content "../.env"
$reactEnv = Get-Content ".env"

# Extract React-specific variables from root .env
$reactVars = $rootEnv | Where-Object { $_ -match "^REACT_APP_" -or $_ -match "^PORT=" -or $_ -match "^BROWSER=" }

# Keep existing React-specific settings and add the React environment variables from root
$output = @()
$output += "# Environment variables for React frontend"
$output += "REACT_APP_API_URL=http://localhost:8000"
$output += "PORT=8080"
$output += "BROWSER=none"
$output += ""
$output += "# Variables from root .env"
$output += $reactVars

# Write to React .env file
$output | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "Environment variables synced from root .env to React .env"
