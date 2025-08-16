import requests
import tempfile
import os

# Create a simple test PDF
test_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
190
%%EOF"""

# Test the endpoints
base_url = "http://localhost:8000"

print("1. Testing health check...")
response = requests.get(f"{base_url}/health")
print(f"Health check: {response.status_code} - {response.json()}")

print("\n2. Creating session...")
response = requests.post(f"{base_url}/session/create")
print(f"Session creation: {response.status_code}")
if response.status_code == 200:
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"Session ID: {session_id}")
else:
    print("Failed to create session")
    exit(1)

print("\n3. Testing upload endpoint...")
# Create temporary file
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
    f.write(test_pdf_content)
    temp_file = f.name

try:
    # Test upload
    with open(temp_file, 'rb') as f:
        files = {'files': ('test.pdf', f, 'application/pdf')}
        data = {'session_id': session_id}
        response = requests.post(f"{base_url}/upload/bulk", files=files, data=data)
    
    print(f"Upload response: {response.status_code}")
    if response.status_code == 200:
        print(f"Upload successful: {response.json()}")
    else:
        print(f"Upload failed: {response.text}")

finally:
    # Clean up
    try:
        os.unlink(temp_file)
    except:
        pass

print("\n4. Testing document list...")
response = requests.get(f"{base_url}/session/{session_id}/documents")
print(f"Document list: {response.status_code}")
if response.status_code == 200:
    print(f"Documents: {response.json()}")