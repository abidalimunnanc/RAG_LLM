import logging
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
import re
import io
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json

class PDFScraper:
    """State-of-the-art PDF text extraction utility with advanced features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_text_from_pdf(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract text from PDF content using multiple advanced methods
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            self.logger.info(f"🚀 Starting advanced PDF extraction for {filename}")
            
            # Extract with multiple methods
            results = {
                "pdfplumber": self._extract_with_pdfplumber(pdf_content),
                "pymupdf": self._extract_with_pymupdf(pdf_content),
                "pypdf2": self._extract_with_pypdf2(pdf_content)
            }
            
            # Analyze and combine results
            combined_text = self._combine_extraction_results(results)
            
            # Advanced text processing
            processed_text = self._advanced_text_processing(combined_text)
            
            # Extract comprehensive metadata
            metadata = self._extract_comprehensive_metadata(pdf_content, filename)
            
            # Analyze content structure
            content_analysis = self._analyze_content_structure(processed_text, metadata)
            
            self.logger.info(f"✅ Advanced PDF extraction completed for {filename}")
            
            return {
                "text": processed_text,
                "method_used": "advanced_combined",
                "metadata": metadata,
                "content_analysis": content_analysis,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Advanced PDF extraction failed for {filename}: {e}")
            return {
                "text": "",
                "method_used": "failed",
                "metadata": {"filename": filename},
                "success": False,
                "error": str(e)
            }
    
    def _extract_with_pdfplumber(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract text using pdfplumber with advanced features"""
        try:
            text_parts = []
            tables_found = []
            images_found = []
            
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extract text with layout preservation
                        page_text = page.extract_text(layout=True)
                        
                        # Extract tables
                        tables = page.extract_tables()
                        if tables:
                            tables_found.append(f"Page {page_num}: {len(tables)} tables")
                            for i, table in enumerate(tables):
                                table_text = self._format_table(table)
                                page_text += f"\n\n[TABLE {i+1}]\n{table_text}\n[/TABLE]"
                        
                        # Check for images
                        if page.images:
                            images_found.append(f"Page {page_num}: {len(page.images)} images")
                            page_text += f"\n\n[IMAGES: {len(page.images)} found on this page]"
                        
                        if page_text:
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ pdfplumber failed on page {page_num}: {e}")
                        continue
            
            return {
                "text": "\n\n".join(text_parts),
                "tables": tables_found,
                "images": images_found
            }
        except Exception as e:
            self.logger.warning(f"⚠️ pdfplumber extraction failed: {e}")
            return {"text": "", "tables": [], "images": []}
    
    def _extract_with_pymupdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract text using PyMuPDF (fitz) with advanced features"""
        try:
            text_parts = []
            equations_found = []
            drawings_found = []
            
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    
                    # Extract text with better formatting
                    text_dict = page.get_text("dict")
                    
                    # Process text blocks with positioning
                    page_text = ""
                    for block in text_dict["blocks"]:
                        if "lines" in block:
                            for line in block["lines"]:
                                line_text = ""
                                for span in line["spans"]:
                                    # Handle different font sizes (headers, body, etc.)
                                    font_size = span["size"]
                                    if font_size > 14:
                                        line_text += f"# {span['text']} "
                                    elif font_size > 12:
                                        line_text += f"## {span['text']} "
                                    else:
                                        line_text += span['text'] + " "
                                page_text += line_text + "\n"
                    
                    # Extract equations and mathematical content
                    math_blocks = page.get_text("math")
                    if math_blocks:
                        equations_found.append(f"Page {page_num + 1}: {len(math_blocks)} equations")
                        page_text += f"\n\n[MATH CONTENT]\n{math_blocks}\n[/MATH]"
                    
                    # Check for drawings/vector graphics
                    drawings = page.get_drawings()
                    if drawings:
                        drawings_found.append(f"Page {page_num + 1}: {len(drawings)} drawings")
                        page_text += f"\n\n[DRAWINGS: {len(drawings)} vector graphics found]"
                    
                    if page_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ PyMuPDF failed on page {page_num + 1}: {e}")
                    continue
            
            doc.close()
            
            return {
                "text": "\n\n".join(text_parts),
                "equations": equations_found,
                "drawings": drawings_found
            }
        except Exception as e:
            self.logger.warning(f"⚠️ PyMuPDF extraction failed: {e}")
            return {"text": "", "equations": [], "drawings": []}
    
    def _extract_with_pypdf2(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract text using PyPDF2 as fallback"""
        try:
            text_parts = []
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                except Exception as e:
                    self.logger.warning(f"⚠️ PyPDF2 failed on page {page_num}: {e}")
                    continue
            
            return {"text": "\n\n".join(text_parts)}
        except Exception as e:
            self.logger.warning(f"⚠️ PyPDF2 extraction failed: {e}")
            return {"text": ""}
    
    def _combine_extraction_results(self, results: Dict[str, Dict[str, Any]]) -> str:
        """Intelligently combine results from multiple extraction methods"""
        texts = []
        
        # Prioritize PyMuPDF for better formatting
        if results["pymupdf"]["text"]:
            texts.append(results["pymupdf"]["text"])
        
        # Add pdfplumber for tables and layout
        if results["pdfplumber"]["text"]:
            texts.append(results["pdfplumber"]["text"])
        
        # Add PyPDF2 as fallback
        if results["pypdf2"]["text"]:
            texts.append(results["pypdf2"]["text"])
        
        # Combine and deduplicate
        combined = "\n\n".join(texts)
        return self._deduplicate_text(combined)
    
    def _deduplicate_text(self, text: str) -> str:
        """Remove duplicate content while preserving structure"""
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        
        for line in lines:
            # Normalize line for comparison
            normalized = re.sub(r'\s+', ' ', line.strip())
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def _advanced_text_processing(self, text: str) -> str:
        """Advanced text processing and cleaning"""
        if not text:
            return ""
        
        # Preserve mathematical expressions
        text = self._preserve_math_expressions(text)
        
        # Clean and normalize
        text = self._clean_text_advanced(text)
        
        # Restore mathematical expressions
        text = self._restore_math_expressions(text)
        
        # Structure the content
        text = self._structure_content(text)
        
        return text
    
    def _preserve_math_expressions(self, text: str) -> str:
        """Preserve mathematical expressions during processing"""
        # Store math expressions temporarily
        math_expressions = []
        
        # Find and replace math patterns
        def replace_math(match):
            math_expressions.append(match.group(0))
            return f"__MATH_{len(math_expressions)-1}__"
        
        # Common math patterns
        patterns = [
            r'\$[^$]+\$',  # LaTeX inline math
            r'\\\([^)]+\\\)',  # LaTeX display math
            r'\\\[[^\]]+\\\]',  # LaTeX display math
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]+',  # Equations
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/]\s*[a-zA-Z_][a-zA-Z0-9_]*',  # Math operations
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, replace_math, text)
        
        # Store for later restoration
        text = f"__MATH_EXPRESSIONS__:{json.dumps(math_expressions)}__\n{text}"
        
        return text
    
    def _restore_math_expressions(self, text: str) -> str:
        """Restore mathematical expressions after processing"""
        # Extract stored expressions
        if "__MATH_EXPRESSIONS__:" in text:
            parts = text.split("__MATH_EXPRESSIONS__:", 1)
            if len(parts) == 2:
                try:
                    math_data = parts[1].split("__\n", 1)
                    if len(math_data) == 2:
                        math_expressions = json.loads(math_data[0])
                        text = math_data[1]
                        
                        # Restore expressions
                        for i, expr in enumerate(math_expressions):
                            text = text.replace(f"__MATH_{i}__", expr)
                except:
                    pass
        
        return text
    
    def _clean_text_advanced(self, text: str) -> str:
        """Advanced text cleaning while preserving structure"""
        # Normalize whitespace but preserve structure
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Preserve page markers
        text = re.sub(r'--- Page (\d+) ---', r'\n--- Page \1 ---\n', text)
        
        # Clean up common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII
        text = re.sub(r'[^\w\s\-.,;:!?()[\]{}"\']+', ' ', text)  # Keep important punctuation
        
        return text.strip()
    
    def _structure_content(self, text: str) -> str:
        """Structure the content with proper formatting"""
        lines = text.split('\n')
        structured_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect headers
            if re.match(r'^[A-Z][A-Z\s]{3,}$', line):
                structured_lines.append(f"\n## {line}\n")
            elif re.match(r'^\d+\.\s+[A-Z]', line):
                structured_lines.append(f"\n### {line}\n")
            else:
                structured_lines.append(line)
        
        return '\n'.join(structured_lines)
    
    def _format_table(self, table: List[List[str]]) -> str:
        """Format extracted table data"""
        if not table:
            return ""
        
        formatted_rows = []
        for row in table:
            if row:
                formatted_row = " | ".join(str(cell).strip() if cell else "" for cell in row)
                formatted_rows.append(formatted_row)
        
        return "\n".join(formatted_rows)
    
    def _extract_comprehensive_metadata(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract comprehensive PDF metadata"""
        metadata = {
            "filename": filename,
            "file_type": ".pdf",
            "upload_method": "advanced_pdf_upload"
        }
        
        try:
            # Try PyMuPDF for comprehensive metadata
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            metadata["page_count"] = len(doc)
            metadata["file_size"] = len(pdf_content)
            
            # Get document metadata
            doc_metadata = doc.metadata
            if doc_metadata:
                for key, value in doc_metadata.items():
                    if value:
                        metadata[f"pdf_{key.lower()}"] = value
            
            # Analyze content structure
            text_blocks = 0
            image_blocks = 0
            total_text_length = 0
            
            for page in doc:
                text_dict = page.get_text("dict")
                for block in text_dict["blocks"]:
                    if "lines" in block:
                        text_blocks += 1
                        for line in block["lines"]:
                            for span in line["spans"]:
                                total_text_length += len(span["text"])
                    elif "image" in block:
                        image_blocks += 1
            
            metadata["text_blocks"] = text_blocks
            metadata["image_blocks"] = image_blocks
            metadata["total_text_length"] = total_text_length
            
            doc.close()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to extract comprehensive metadata: {e}")
            # Fallback to PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                metadata["page_count"] = len(pdf_reader.pages)
                metadata["file_size"] = len(pdf_content)
            except:
                metadata["page_count"] = 0
                metadata["file_size"] = 0
        
        return metadata
    
    def _analyze_content_structure(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure and content of the extracted text"""
        analysis = {
            "total_words": len(text.split()),
            "total_characters": len(text),
            "paragraphs": len([p for p in text.split('\n\n') if p.strip()]),
            "pages": metadata.get("page_count", 0),
            "content_types": {}
        }
        
        # Analyze content types
        if "[TABLE" in text:
            analysis["content_types"]["tables"] = text.count("[TABLE")
        if "[IMAGES:" in text:
            analysis["content_types"]["images"] = text.count("[IMAGES:")
        if "[MATH CONTENT]" in text:
            analysis["content_types"]["mathematical_content"] = text.count("[MATH CONTENT]")
        if "[DRAWINGS:" in text:
            analysis["content_types"]["drawings"] = text.count("[DRAWINGS:")
        
        # Detect document type
        if analysis["content_types"].get("mathematical_content", 0) > 0:
            analysis["document_type"] = "scientific/technical"
        elif analysis["content_types"].get("tables", 0) > 0:
            analysis["document_type"] = "data/report"
        else:
            analysis["document_type"] = "general"
        
        return analysis

# Global instance
pdf_scraper = PDFScraper()
