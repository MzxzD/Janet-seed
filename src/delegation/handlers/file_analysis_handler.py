"""
File and Image Analysis Handler - Local file processing with privacy-first protocol
Processes uploaded images and documents using local models (LLaVA for images, text extraction for documents)
Respects privacy: files are ephemeral by default, stored only with explicit consent
"""
from __future__ import annotations
import logging
import base64
import tempfile
import os
from typing import Dict, Optional, List, Any
from pathlib import Path
from datetime import datetime

from .base import (
    DelegationHandler,
    DelegationRequest,
    DelegationResult,
    HandlerCapability
)

logger = logging.getLogger(__name__)

# Image analysis dependencies
try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    np = None

# Document parsing dependencies
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PyPDF2 = None

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    Document = None

# LLaVA model (for image analysis)
try:
    # Try to import transformers for LLaVA
    from transformers import AutoProcessor, AutoModelForCausalLM, BlipProcessor, BlipForConditionalGeneration
    HAS_LLAVA = True
except ImportError:
    HAS_LLAVA = False
    AutoProcessor = None
    AutoModelForCausalLM = None
    BlipProcessor = None
    BlipForConditionalGeneration = None


class FileAnalysisHandler(DelegationHandler):
    """
    Handler for file and image analysis using local models.
    
    Capabilities:
    - analyze_image: Describe images using LLaVA or BLIP
    - extract_text: Extract text from images (OCR)
    - parse_document: Extract and summarize documents (PDF, DOCX, etc.)
    - analyze_code: Review and analyze code files
    """
    
    def __init__(self, model_cache_dir: Optional[str] = None):
        """
        Initialize File Analysis Handler.
        
        Args:
            model_cache_dir: Directory for caching local models
        """
        super().__init__(
            handler_id="file_analysis_handler",
            name="File and Image Analysis"
        )
        
        self.model_cache_dir = Path(model_cache_dir) if model_cache_dir else Path.home() / ".janet" / "models"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Image analysis models (lazy loading)
        self.image_model = None
        self.image_processor = None
        
        # Temporary file storage (ephemeral, deleted after processing)
        self.temp_files: List[Path] = []
        
        # Privacy protocol: files are ephemeral by default
        self.stored_files: Dict[str, Dict[str, Any]] = {}  # Only if user explicitly says to remember
    
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return list of capabilities this handler provides."""
        try:
            return [HandlerCapability.IMAGE_PROCESSING]
        except AttributeError:
            return [HandlerCapability.CUSTOM]
    
    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if this handler can handle the request."""
        task_desc = request.task_description.lower()
        file_keywords = ["image", "picture", "photo", "file", "document", "pdf", "analyze", "describe", "ocr", "extract"]
        return any(keyword in task_desc for keyword in file_keywords)
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """
        Handle the delegation request.
        
        Args:
            request: Delegation request
            
        Returns:
            Delegation result
        """
        try:
            input_data = request.input_data or {}
            task_desc = request.task_description.lower()
            
            # Route to appropriate handler method
            if "image" in task_desc or "picture" in task_desc or "photo" in task_desc:
                return self._handle_image_analysis(request, input_data)
            elif "document" in task_desc or "pdf" in task_desc or "docx" in task_desc:
                return self._handle_document_parse(request, input_data)
            elif "code" in task_desc or ".py" in task_desc or ".js" in task_desc:
                return self._handle_code_analysis(request, input_data)
            elif "ocr" in task_desc or "extract text" in task_desc:
                return self._handle_text_extraction(request, input_data)
            else:
                return DelegationResult(
                    success=False,
                    output_data={},
                    message="Unknown file analysis operation",
                    error=f"Unknown task: {task_desc}"
                )
        
        except Exception as e:
            logger.error(f"Error handling file analysis request: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"File analysis failed: {str(e)}",
                error=str(e)
            )
    
    def _handle_image_analysis(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle image analysis request."""
        # Get file data
        file_data_base64 = input_data.get("file_data")
        file_name = input_data.get("file_name", "image")
        task_type = input_data.get("task", "describe")  # "describe", "ocr", "extract_objects"
        
        if not file_data_base64:
            return DelegationResult(
                success=False,
                output_data={},
                message="No file data provided",
                error="file_data required"
            )
        
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(file_data_base64)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(image_bytes)
                tmp_path = Path(tmp_file.name)
                self.temp_files.append(tmp_path)
            
            # Load image
            if not HAS_PIL:
                return DelegationResult(
                    success=False,
                    output_data={},
                    message="PIL/Pillow not available for image processing",
                    error="PIL not installed"
                )
            
            image = Image.open(tmp_path)
            
            # Analyze based on task type
            if task_type == "describe":
                description = self._describe_image(image)
            elif task_type == "ocr":
                description = self._extract_text_from_image(image)
            else:
                description = self._describe_image(image)
            
            # Clean up temporary file (ephemeral - privacy protocol)
            self._cleanup_temp_file(tmp_path)
            
            # Check if user wants to remember this file
            should_remember = request.input_data.get("remember", False)
            if should_remember:
                # Store summary in handler's memory (will be moved to Green Vault later)
                file_id = str(hash(file_data_base64) % 1000000)
                self.stored_files[file_id] = {
                    "file_name": file_name,
                    "description": description,
                    "task_type": task_type,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
                logger.info(f"Stored file analysis summary for {file_name} (file_id: {file_id})")
            
            return DelegationResult(
                success=True,
                output_data={
                    "file_name": file_name,
                    "description": description,
                    "task_type": task_type,
                    "remembered": should_remember
                },
                message=f"Analyzed {file_name}: {description[:100]}...",
                metadata={"operation": "image_analysis", "ephemeral": not should_remember}
            )
        
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Image analysis failed: {str(e)}",
                error=str(e)
            )
    
    def _describe_image(self, image: Image.Image) -> str:
        """Describe image using LLaVA or BLIP model."""
        # Try LLaVA first, fallback to BLIP, then simple description
        if HAS_LLAVA:
            try:
                # Lazy load model
                if self.image_model is None:
                    self._load_image_model()
                
                if self.image_model and self.image_processor:
                    # Process image with model
                    prompt = "Describe this image in detail."
                    inputs = self.image_processor(images=image, text=prompt, return_tensors="pt")
                    outputs = self.image_model.generate(**inputs, max_length=100)
                    description = self.image_processor.decode(outputs[0], skip_special_tokens=True)
                    return description
            except Exception as e:
                logger.warning(f"LLaVA/BLIP analysis failed: {e}, using fallback")
        
        # Fallback: Basic description
        width, height = image.size
        mode = image.mode
        return f"An image ({width}x{height} pixels, {mode} color mode). Detailed analysis requires LLaVA model installation."
    
    def _load_image_model(self):
        """Lazy load image analysis model."""
        try:
            # Try BLIP (smaller, faster than LLaVA)
            self.image_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.image_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            logger.info("Loaded BLIP image captioning model")
        except Exception as e:
            logger.warning(f"Failed to load BLIP model: {e}")
            # Could try LLaVA here, but it's much larger
            self.image_processor = None
            self.image_model = None
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
            return text if text.strip() else "No text detected in image."
        except ImportError:
            return "OCR not available. Install pytesseract for text extraction."
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return f"OCR extraction failed: {str(e)}"
    
    def _handle_document_parse(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle document parsing (PDF, DOCX, etc.)."""
        file_data_base64 = input_data.get("file_data")
        file_name = input_data.get("file_name", "document")
        file_type = input_data.get("file_type", "").lower()
        
        if not file_data_base64:
            return DelegationResult(
                success=False,
                output_data={},
                message="No file data provided",
                error="file_data required"
            )
        
        try:
            # Decode and save to temporary file
            file_bytes = base64.b64decode(file_data_base64)
            suffix = Path(file_name).suffix if "." in file_name else (".pdf" if "pdf" in file_type else ".docx")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_path = Path(tmp_file.name)
                self.temp_files.append(tmp_path)
            
            # Parse based on file type
            if "pdf" in file_type or file_name.endswith(".pdf"):
                content = self._parse_pdf(tmp_path)
            elif "docx" in file_type or file_name.endswith(".docx"):
                content = self._parse_docx(tmp_path)
            elif "txt" in file_type or file_name.endswith(".txt"):
                content = self._parse_text(tmp_path)
            else:
                content = "Unknown file type. Supported: PDF, DOCX, TXT"
            
            # Clean up
            self._cleanup_temp_file(tmp_path)
            
            # Generate summary using local LLM (would be done via Janet adapter)
            summary = content[:500] + "..." if len(content) > 500 else content
            
            should_remember = request.input_data.get("remember", False)
            if should_remember:
                file_id = str(hash(file_data_base64) % 1000000)
                self.stored_files[file_id] = {
                    "file_name": file_name,
                    "content_preview": summary,
                    "content_length": len(content),
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            
            return DelegationResult(
                success=True,
                output_data={
                    "file_name": file_name,
                    "content": content,
                    "summary": summary,
                    "content_length": len(content),
                    "remembered": should_remember
                },
                message=f"Parsed {file_name}: {len(content)} characters extracted",
                metadata={"operation": "document_parse", "ephemeral": not should_remember}
            )
        
        except Exception as e:
            logger.error(f"Error parsing document: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Document parsing failed: {str(e)}",
                error=str(e)
            )
    
    def _parse_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF."""
        if not HAS_PYPDF2:
            return "PyPDF2 not available for PDF parsing."
        
        try:
            text_parts = []
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
            return "\n".join(text_parts)
        except Exception as e:
            return f"PDF parsing error: {str(e)}"
    
    def _parse_docx(self, docx_path: Path) -> str:
        """Extract text from DOCX."""
        if not HAS_DOCX:
            return "python-docx not available for DOCX parsing."
        
        try:
            doc = Document(docx_path)
            text_parts = [paragraph.text for paragraph in doc.paragraphs]
            return "\n".join(text_parts)
        except Exception as e:
            return f"DOCX parsing error: {str(e)}"
    
    def _parse_text(self, txt_path: Path) -> str:
        """Read plain text file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Text file reading error: {str(e)}"
    
    def _handle_code_analysis(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle code file analysis."""
        file_data_base64 = input_data.get("file_data")
        file_name = input_data.get("file_name", "code")
        
        if not file_data_base64:
            return DelegationResult(
                success=False,
                output_data={},
                message="No file data provided",
                error="file_data required"
            )
        
        try:
            # Decode and parse as text
            code_bytes = base64.b64decode(file_data_base64)
            code_content = code_bytes.decode('utf-8', errors='ignore')
            
            # Basic code analysis (could be extended with AST parsing, etc.)
            lines = code_content.split('\n')
            line_count = len(lines)
            language = self._detect_language(file_name, code_content)
            
            # Simple analysis
            has_functions = any('def ' in line or 'function ' in line or 'fn ' in line for line in lines)
            has_classes = any('class ' in line for line in lines)
            has_comments = any(line.strip().startswith('#') or line.strip().startswith('//') for line in lines)
            
            analysis = {
                "file_name": file_name,
                "language": language,
                "line_count": line_count,
                "has_functions": has_functions,
                "has_classes": has_classes,
                "has_comments": has_comments,
                "preview": code_content[:500]
            }
            
            should_remember = request.input_data.get("remember", False)
            
            return DelegationResult(
                success=True,
                output_data=analysis,
                message=f"Analyzed {file_name}: {language} file with {line_count} lines",
                metadata={"operation": "code_analysis", "ephemeral": not should_remember}
            )
        
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Code analysis failed: {str(e)}",
                error=str(e)
            )
    
    def _detect_language(self, file_name: str, content: str) -> str:
        """Detect programming language from filename and content."""
        ext = Path(file_name).suffix.lower()
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.rs': 'Rust',
            '.go': 'Go',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        return lang_map.get(ext, 'Unknown')
    
    def _handle_text_extraction(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle text extraction (wrapper for OCR)."""
        return self._handle_image_analysis(request, {**input_data, "task": "ocr"})
    
    def _cleanup_temp_file(self, file_path: Path):
        """Clean up temporary file (privacy protocol - files are ephemeral)."""
        try:
            if file_path.exists():
                file_path.unlink()
                if file_path in self.temp_files:
                    self.temp_files.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def cleanup_all_temp_files(self):
        """Clean up all temporary files (called on shutdown)."""
        for tmp_file in self.temp_files[:]:
            self._cleanup_temp_file(tmp_file)
    
    def is_available(self) -> bool:
        """Check if handler is available and ready."""
        # Handler is available if basic dependencies are installed
        # Models can be loaded lazily
        return HAS_PIL or HAS_PYPDF2 or HAS_DOCX
    
    def get_stored_files(self) -> Dict[str, Dict[str, Any]]:
        """Get stored file summaries (for memory transfer to Green Vault)."""
        return self.stored_files.copy()
