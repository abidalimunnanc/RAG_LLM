from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from models import Document
from routes.documents import add_document
from pdf_scraper import pdf_scraper
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/")
async def upload_document(file: UploadFile = File(...)):
    allowed_types = {".txt", ".md", ".json", ".pdf"}
    file_suffix = Path(file.filename).suffix.lower()

    if file_suffix not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file_suffix} not supported")

    try:
        content = await file.read()
        
        # Handle PDF files
        if file_suffix == ".pdf":
            logger.info(f"📄 Processing PDF file: {file.filename}")
            pdf_result = pdf_scraper.extract_text_from_pdf(content, file.filename)
            
            if not pdf_result["success"]:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to extract text from PDF: {pdf_result.get('error', 'Unknown error')}"
                )
            
            text_content = pdf_result["text"]
            metadata = pdf_result["metadata"]
            
            # Use PDF title if available, otherwise use filename
            title = metadata.get("pdf_title", Path(file.filename).stem)
            
            logger.info(f"✅ PDF processed successfully. Pages: {metadata.get('page_count', 0)}, Method: {pdf_result['method_used']}")
            
        else:
            # Handle text files
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError:
                # Try other encodings
                try:
                    text_content = content.decode("latin-1")
                except:
                    raise HTTPException(status_code=400, detail="Unable to decode file content")
            
            metadata = {
                "filename": file.filename,
                "file_type": file_suffix,
                "upload_method": "file_upload"
            }
            title = Path(file.filename).stem

        # Validate content
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="File appears to be empty or contains no readable text")

        document = Document(
            title=title,
            content=text_content,
            metadata=metadata
        )
        
        result = await add_document(document)
        logger.info(f"✅ Document uploaded successfully: {file.filename}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
