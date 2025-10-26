import docx
import fitz # Part of PyMuPDF
from typing import Optional

def process_file_to_text(file_path: str) -> Optional[str]:
    """
    Reads a document (PDF, DOCX, TXT) and returns its content as a single string.
    """
    file_extension = file_path.split('.')[-1].lower()
    content = ""
    
    try:
        if file_extension == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        elif file_extension == 'docx':
            doc = docx.Document(file_path)
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        elif file_extension == 'pdf':
            with fitz.open(file_path) as doc: # Use PyMuPDF
                for page in doc:
                    content += page.get_text() + "\n"
        
        else:
            return None # Should not happen if file_types is checked

        return content.strip()

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return f"[ERROR: Could not read file content due to {e}]"