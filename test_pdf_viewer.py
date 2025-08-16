"""
Test PDF viewer functionality and backend PDF serving endpoint.
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_pdf_serving_endpoint():
    """Test that the PDF serving endpoint works correctly."""
    
    # Create a session first
    response = client.post("/session/create")
    assert response.status_code == 200
    session_data = response.json()
    session_id = session_data["session_id"]
    
    # Create a dummy PDF file for testing
    dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(dummy_pdf_content)
        temp_pdf_path = temp_file.name
    
    try:
        # Upload the PDF file
        with open(temp_pdf_path, 'rb') as pdf_file:
            files = {"files": ("test.pdf", pdf_file, "application/pdf")}
            data = {"session_id": session_id}
            response = client.post("/upload/bulk", files=files, data=data)
        
        assert response.status_code == 200
        upload_data = response.json()
        assert len(upload_data["uploaded_documents"]) == 1
        
        document_id = upload_data["uploaded_documents"][0]["document_id"]
        
        # Test PDF serving endpoint
        response = client.get(f"/session/{session_id}/documents/{document_id}/pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # Verify the content is the same
        assert response.content == dummy_pdf_content
        
    finally:
        # Clean up temporary  "-v"])le__,fi([__test.main":
    py"__main__ name__ ==

if __"]ildeta"()[onse.jsresponn  iund"on not foessissert "S4
    a == 40s_codese.staturt responassepdf")
    _doc/uments/somen/docvalid_sessiosession/in"/(getclient.e =   respons 
  
   """ session.th invalidrving wi"Test PDF se  ""n():
  d_sessionvaling_ivit_pdf_ser tes

def"]tail"de()[sonnse.j respoinnd"  fouDocument notssert "   ade == 404
 status_cort response.")
    assedfnt/pxistets/none_id}/documensessionn/{t(f"/sessioent.ge cliesponse =nt
    rent docume-exist access nonto  # Try     
  
id"]session_a["ation_dn_id = sessssio
    se()onponse.jsata = res  session_d  
code == 200atus_onse.stsert resp as")
   reatesion/cst("/seslient.poesponse = c   rt
 sion firs sesCreate a
    #     t."""
entent documnon-exisng with servi"Test PDF ""():
    nt_document_nonexisteserving test_pdf_defh)

pdf_pat(temp_os.unlink          f_path):
  p_pd.exists(temos.pathif       file
  