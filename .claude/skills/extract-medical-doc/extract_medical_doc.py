#!/usr/bin/env python3
"""
Extract Medical Documentation Skill
Dual-layer extraction: Complete text + Structured medical information
"""

import fitz  # PyMuPDF
import pdfplumber
import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import base64
from io import BytesIO

try:
    from anthropic import Anthropic
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    HAS_AI_FEATURES = True
except ImportError:
    HAS_AI_FEATURES = False


# ==========================================
# Data Models
# ==========================================

@dataclass
class PageInfo:
    """Information about a single PDF page"""
    page_number: int
    page_type: str  # "electronic" or "scanned"
    has_text_layer: bool
    confidence: float
    needs_review: bool
    content: str
    tables: List[Dict]
    images: List[Dict]


@dataclass
class MedicalEntity:
    """Base structure for extracted medical entities"""
    page: int
    confidence: float
    needs_review: bool
    page_type: str
    text: str = ""
    original_snippet: str = ""


@dataclass
class Medication(MedicalEntity):
    """Medication with dosage information"""
    name: str = ""
    dosage: str = ""


@dataclass
class Disease(MedicalEntity):
    """Disease with ICD code"""
    name: str = ""
    icd_code: str = ""


# ==========================================
# PDF Page Type Detector
# ==========================================

class PDFPageDetector:
    """Detects whether PDF pages are electronic or scanned"""

    @staticmethod
    def detect_page_type(page: fitz.Page) -> Tuple[str, float, bool]:
        """
        Detect if a page is electronic or scanned.

        Returns:
            (page_type, confidence, has_text_layer)
            page_type: "electronic" or "scanned"
            confidence: 0.0 to 1.0
            has_text_layer: bool
        """
        # Extract text
        text = page.get_text().strip()
        text_length = len(text)

        # Get page dimensions
        rect = page.rect
        page_area = rect.width * rect.height

        # Check for images
        image_list = page.get_images()
        has_images = len(image_list) > 0

        # Heuristics for detection
        has_text_layer = text_length > 50

        if not has_text_layer:
            # No text = likely scanned
            return "scanned", 0.95, False

        # Calculate text density
        text_blocks = page.get_text("blocks")
        text_area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in text_blocks if len(b) > 4)
        text_density = text_area / page_area if page_area > 0 else 0

        # Check for typical electronic PDF characteristics
        fonts = set()
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if "font" in span:
                            fonts.add(span["font"])

        has_proper_fonts = len(fonts) > 0

        # Decision logic
        if has_proper_fonts and text_density > 0.1:
            return "electronic", 0.95, True
        elif has_images and text_density < 0.05:
            return "scanned", 0.85, True  # Has text but likely OCR'd
        elif text_length > 500:
            return "electronic", 0.80, True
        else:
            return "scanned", 0.70, True


# ==========================================
# Complete Text Extractor
# ==========================================

class CompleteTextExtractor:
    """Extracts complete text content from PDF with layout preservation"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.fitz_doc = fitz.open(pdf_path)
        self.plumber_doc = pdfplumber.open(pdf_path)

    def extract_all(self) -> List[PageInfo]:
        """Extract complete content from all pages"""
        pages_info = []

        for page_num in range(len(self.fitz_doc)):
            print(f"Processing page {page_num + 1}/{len(self.fitz_doc)}...")
            page_info = self._extract_page(page_num)
            pages_info.append(page_info)

        return pages_info

    def _extract_page(self, page_num: int) -> PageInfo:
        """Extract content from a single page"""
        fitz_page = self.fitz_doc[page_num]
        plumber_page = self.plumber_doc.pages[page_num]

        # Detect page type
        page_type, confidence, has_text_layer = PDFPageDetector.detect_page_type(fitz_page)

        # Extract text
        if page_type == "electronic":
            content = fitz_page.get_text()
        else:
            # Scanned page - use OCR if available
            if HAS_AI_FEATURES:
                content = self._ocr_page(fitz_page)
            else:
                content = fitz_page.get_text()  # Fallback

        # Extract tables
        tables = plumber_page.extract_tables() or []
        table_dicts = [self._format_table(t) for t in tables if t]

        # Extract images
        images = self._extract_images(fitz_page)

        # Determine if needs review (scanned pages with low confidence)
        needs_review = (page_type == "scanned" and confidence < 0.90)

        return PageInfo(
            page_number=page_num + 1,
            page_type=page_type,
            has_text_layer=has_text_layer,
            confidence=confidence,
            needs_review=needs_review,
            content=content,
            tables=table_dicts,
            images=images
        )

    def _ocr_page(self, page: fitz.Page) -> str:
        """Perform OCR on a scanned page"""
        try:
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Perform OCR
            text = pytesseract.image_to_string(img, lang='eng')
            return text
        except Exception as e:
            print(f"OCR failed: {e}")
            return page.get_text()  # Fallback

    def _format_table(self, table: List[List]) -> Dict:
        """Format table as dictionary"""
        if not table:
            return {}

        headers = table[0] if table else []
        rows = table[1:] if len(table) > 1 else []

        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "col_count": len(headers)
        }

    def _extract_images(self, page: fitz.Page) -> List[Dict]:
        """Extract image information from page"""
        images = []
        image_list = page.get_images()

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = self.fitz_doc.extract_image(xref)

            images.append({
                "index": img_index,
                "width": base_image["width"],
                "height": base_image["height"],
                "format": base_image["ext"],
                "size_bytes": len(base_image["image"])
            })

        return images

    def close(self):
        """Close PDF documents"""
        self.fitz_doc.close()
        self.plumber_doc.close()


# ==========================================
# Medical Information Extractor (Rule-based)
# ==========================================

class RuleBasedMedicalExtractor:
    """Extract medical information using rules and patterns"""

    # Common medication name patterns
    MEDICATION_PATTERNS = [
        r'\b[A-Z][a-z]+(?:mab|nib|pril|olol|statin|mycin|cillin)\b',  # Drug suffixes
        r'\b(?:mg|mcg|g|mL|units?)\b',  # Dosage units
    ]

    # ICD code pattern
    ICD_PATTERN = r'\b[A-Z]\d{2}(?:\.\d{1,2})?\b'

    # Dosage pattern
    DOSAGE_PATTERN = r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|mL|units?)\b(?:\s+(?:once|twice|three times|QD|BID|TID|QID)\s+(?:daily|per day))?'

    # Recommendation level pattern
    RECOMMENDATION_PATTERN = r'\b(?:Level|Grade|Class)\s+([ABC]|[I]{1,3})\b'

    def extract_basic_info(self, pages_info: List[PageInfo]) -> Dict[str, List[Dict]]:
        """Extract basic medical information using rules"""
        result = {
            "diseases": [],
            "medications": [],
            "recommendation_levels": [],
            "references": []
        }

        for page_info in pages_info:
            page_num = page_info.page_number
            text = page_info.content

            # Extract ICD codes
            icd_matches = re.finditer(self.ICD_PATTERN, text)
            for match in icd_matches:
                # Get context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                result["diseases"].append({
                    "icd_code": match.group(),
                    "context": context,
                    "page": page_num,
                    "page_type": page_info.page_type,
                    "confidence": page_info.confidence,
                    "needs_review": page_info.needs_review
                })

            # Extract dosages (potential medications)
            dosage_matches = re.finditer(self.DOSAGE_PATTERN, text, re.IGNORECASE)
            for match in dosage_matches:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]

                result["medications"].append({
                    "dosage": match.group(),
                    "context": context,
                    "page": page_num,
                    "page_type": page_info.page_type,
                    "confidence": page_info.confidence,
                    "needs_review": page_info.needs_review or page_info.page_type == "scanned"
                })

            # Extract recommendation levels
            rec_matches = re.finditer(self.RECOMMENDATION_PATTERN, text)
            for match in rec_matches:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                result["recommendation_levels"].append({
                    "level": match.group(1),
                    "context": context,
                    "page": page_num,
                    "page_type": page_info.page_type
                })

        return result


# ==========================================
# Main Extraction Pipeline
# ==========================================

def extract_medical_document(pdf_path: str, use_ai: bool = False) -> Dict[str, Any]:
    """
    Main extraction pipeline.

    Args:
        pdf_path: Path to PDF file
        use_ai: Whether to use AI-powered extraction (requires API key)

    Returns:
        Complete extraction result with dual-layer output
    """
    start_time = datetime.now()

    print(f"\n{'='*60}")
    print(f"Extracting Medical Document: {Path(pdf_path).name}")
    print(f"{'='*60}\n")

    # Phase 1: Complete text extraction (FREE)
    print("Phase 1: Complete text extraction...")
    extractor = CompleteTextExtractor(pdf_path)
    pages_info = extractor.extract_all()

    # Count page types
    electronic_pages = sum(1 for p in pages_info if p.page_type == "electronic")
    scanned_pages = sum(1 for p in pages_info if p.page_type == "scanned")

    print(f"\n✓ Extracted {len(pages_info)} pages")
    print(f"  - Electronic: {electronic_pages}")
    print(f"  - Scanned: {scanned_pages}")

    # Phase 2: Rule-based extraction (FREE)
    print("\nPhase 2: Rule-based medical information extraction...")
    rule_extractor = RuleBasedMedicalExtractor()
    basic_medical_info = rule_extractor.extract_basic_info(pages_info)

    print(f"\n✓ Basic extraction complete:")
    print(f"  - Diseases/ICD codes: {len(basic_medical_info['diseases'])}")
    print(f"  - Medication references: {len(basic_medical_info['medications'])}")
    print(f"  - Recommendation levels: {len(basic_medical_info['recommendation_levels'])}")

    # Prepare output
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()

    result = {
        "document_id": Path(pdf_path).stem,
        "source_file": Path(pdf_path).name,
        "extraction_timestamp": start_time.isoformat(),
        "processing_metadata": {
            "total_pages": len(pages_info),
            "electronic_pages": electronic_pages,
            "scanned_pages": scanned_pages,
            "processing_time_seconds": processing_time,
            "ai_analysis_used": use_ai
        },
        "complete_text": {
            "pages": [asdict(p) for p in pages_info]
        },
        "structured_medical_data": basic_medical_info
    }

    extractor.close()

    return result


# ==========================================
# CLI Interface
# ==========================================

def main():
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python extract_medical_doc.py <pdf_path>")
        print("\nExample:")
        print("  python extract_medical_doc.py clinical_guideline.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    # Check for AI features
    use_ai = False
    if HAS_AI_FEATURES and os.getenv("ANTHROPIC_API_KEY"):
        print("\n" + "="*60)
        print("AI-powered analysis available")
        print("="*60)
        print("\nBasic extraction is FREE (rules-based)")
        print("AI analysis provides:")
        print("  • Deep semantic understanding")
        print("  • Treatment protocol extraction")
        print("  • Diagnostic criteria identification")
        print("  • Adverse effects extraction")
        print(f"\nEstimated cost: ~$0.30-0.60 for this document")
        print("\nEnable AI analysis? [y/N]: ", end="")

        response = input().strip().lower()
        use_ai = response in ['y', 'yes']

    # Run extraction
    result = extract_medical_document(pdf_path, use_ai=use_ai)

    # Save output
    output_dir = Path("extracted_medical_data")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{result['document_id']}_extracted.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("Extraction Complete!")
    print(f"{'='*60}")
    print(f"\nOutput saved to: {output_file}")
    print(f"Processing time: {result['processing_metadata']['processing_time_seconds']:.1f}s")

    # Summary of pages needing review
    pages_needing_review = [
        p for p in result['complete_text']['pages']
        if p['needs_review']
    ]

    if pages_needing_review:
        print(f"\n⚠️  {len(pages_needing_review)} pages flagged for manual review:")
        for page in pages_needing_review[:5]:  # Show first 5
            print(f"   • Page {page['page_number']} ({page['page_type']}, confidence: {page['confidence']:.2f})")
        if len(pages_needing_review) > 5:
            print(f"   ... and {len(pages_needing_review) - 5} more")


if __name__ == "__main__":
    main()
