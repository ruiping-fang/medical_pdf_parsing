# Extract Medical Documentation

A comprehensive skill for extracting and structuring medical information from PDF documents (clinical guidelines, research papers, drug information sheets).

## Description

This skill provides **dual-layer output**:
1. **Complete text extraction**: Full document content with layout preservation
2. **Structured medical information**: Intelligent extraction of 7 key medical data categories

### Key Features

- **Hybrid PDF support**: Handles both electronic and scanned pages
- **Smart page detection**: Automatically identifies scanned pages requiring OCR
- **Quality assurance**: Confidence scoring with manual review flagging for critical information
- **Cost transparency**: Estimates API costs and prompts user confirmation before AI analysis
- **Medical-specific extraction**: 
  - Diseases and ICD codes
  - Medications and dosages (100% accuracy requirement)
  - Treatment protocols
  - Clinical recommendation levels
  - Diagnostic criteria
  - Adverse effects and contraindications
  - References with links

## Usage

```bash
/extract-medical-doc [path/to/file.pdf]
```

If no path provided, interactive file selection will be offered.

## Output Structure

```json
{
  "document_id": "guideline_name",
  "source_file": "clinical_guideline.pdf",
  "processing_metadata": {
    "total_pages": 60,
    "electronic_pages": 42,
    "scanned_pages": 18,
    "processing_time": "2m 15s",
    "api_cost": "$0.32"
  },
  "complete_text": {
    "pages": [
      {
        "page_number": 1,
        "page_type": "electronic",
        "content": "...",
        "tables": [...],
        "images": [...]
      }
    ]
  },
  "structured_medical_data": {
    "diseases": [...],
    "medications": [...],
    "treatment_protocols": [...],
    "recommendation_levels": [...],
    "diagnostic_criteria": [...],
    "adverse_effects": [...],
    "references": [...]
  }
}
```

## Dependencies

### Python Libraries
- `pymupdf` (PyMuPDF) - PDF text extraction
- `pdfplumber` - Table extraction with layout preservation
- `pytesseract` - OCR for scanned pages
- `pdf2image` - Convert PDF pages to images for OCR
- `Pillow` - Image processing
- `anthropic` - Claude API for intelligent extraction

### System Requirements
- Tesseract OCR installed (`brew install tesseract` on macOS)
- Poppler utilities (`brew install poppler` on macOS)

## Configuration

Create `.env` file with:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Accuracy Guarantees

- **Medications and dosages**: 100% accuracy requirement
  - Scanned pages flagged for manual review
  - Original text snippets and images provided for verification
- **Other content**: Complete extraction without omissions
- **Format flexibility**: Minor formatting differences acceptable
- **Table data**: Complete data preservation, format may vary

## License

Proprietary - for internal use only
