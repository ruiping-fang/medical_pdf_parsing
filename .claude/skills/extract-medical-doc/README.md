# Extract Medical Documentation Skill

Comprehensive medical document extraction with dual-layer output: complete text + structured medical information.

## Quick Start

### 1. Install Dependencies

#### macOS
```bash
# Install system dependencies
brew install tesseract poppler

# Install Python packages
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils

# Install Python packages
pip install -r requirements.txt
```

#### Windows
```bash
# Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
# Install Poppler from: https://github.com/oschwartz10612/poppler-windows/releases

# Install Python packages
pip install -r requirements.txt
```

### 2. Configure API Key (Optional)

For AI-powered deep analysis:

```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

### 3. Run Extraction

```bash
python extract_medical_doc.py /path/to/medical_document.pdf
```

## Features

### Free Tier (Rule-Based)
✅ Complete text extraction with layout preservation  
✅ Table extraction  
✅ Image detection and metadata  
✅ ICD code detection  
✅ Medication and dosage pattern matching  
✅ Clinical recommendation level detection  
✅ Page type detection (electronic vs scanned)  
✅ Confidence scoring  

### AI-Powered Tier (Requires API Key)
⚡ Semantic understanding of medical content  
⚡ Treatment protocol extraction  
⚡ Diagnostic criteria identification  
⚡ Adverse effects and contraindications  
⚡ Complex table interpretation  
⚡ Reference linking and validation  

**Cost**: ~$0.30-0.60 per 60-page document  
**User confirms before any API calls**

## Output Structure

```json
{
  "document_id": "clinical_guideline",
  "source_file": "guideline.pdf",
  "processing_metadata": {
    "total_pages": 60,
    "electronic_pages": 42,
    "scanned_pages": 18,
    "processing_time_seconds": 45.2
  },
  "complete_text": {
    "pages": [
      {
        "page_number": 1,
        "page_type": "electronic",
        "confidence": 0.95,
        "needs_review": false,
        "content": "...",
        "tables": [...],
        "images": [...]
      }
    ]
  },
  "structured_medical_data": {
    "diseases": [...],
    "medications": [...],
    "recommendation_levels": [...],
    "references": [...]
  }
}
```

## Accuracy Guarantees

### Critical Information (100% accuracy required)
- **Medications and dosages**: Scanned pages automatically flagged for manual review
- **Original text snippets**: Always included for verification

### Complete Extraction
- **No omissions**: All text, tables, and images extracted
- **Format flexibility**: Minor formatting differences acceptable
- **Table data**: Complete preservation, format may vary

## Usage Examples

### Basic Extraction (Free)
```bash
python extract_medical_doc.py clinical_guideline.pdf
```

### With AI Analysis
```bash
# You'll be prompted to confirm before API calls
python extract_medical_doc.py clinical_guideline.pdf
# > Enable AI analysis? [y/N]: y
```

### Programmatic Usage
```python
from extract_medical_doc import extract_medical_document

result = extract_medical_document("guideline.pdf", use_ai=False)

# Access complete text
for page in result["complete_text"]["pages"]:
    print(f"Page {page['page_number']}: {page['content'][:100]}...")

# Access structured data
medications = result["structured_medical_data"]["medications"]
for med in medications:
    if med["needs_review"]:
        print(f"⚠️  Review: {med['dosage']} on page {med['page']}")
```

## Integration with Knowledge Systems

The output JSON is designed for easy integration with:
- Document management systems
- Medical knowledge bases
- Vector databases (for RAG systems)
- Clinical decision support systems

Example: Loading into a vector database
```python
import json

with open("extracted_medical_data/guideline_extracted.json") as f:
    data = json.load(f)

# Extract chunks for embedding
for page in data["complete_text"]["pages"]:
    chunk = {
        "content": page["content"],
        "metadata": {
            "source": data["source_file"],
            "page": page["page_number"],
            "confidence": page["confidence"]
        }
    }
    # Store in your vector DB
```

## Troubleshooting

### OCR Not Working
```bash
# Verify Tesseract installation
tesseract --version

# If not found, reinstall:
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr  # Linux
```

### PDF2Image Error
```bash
# Verify Poppler installation
pdftoppm -v

# If not found, reinstall:
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Linux
```

### Low Confidence Scores
- Check if PDF is high-quality
- Scanned pages naturally have lower confidence
- Review flagged pages manually

## Performance

| Document Size | Processing Time | Cost (with AI) |
|--------------|----------------|----------------|
| 10 pages | ~15 seconds | $0.05-0.10 |
| 60 pages | ~45 seconds | $0.30-0.60 |
| 200 pages | ~3 minutes | $1.00-2.00 |

*Times are approximate and depend on page types and system specs*

## License

Proprietary - Internal use only
