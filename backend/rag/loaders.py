"""
Document Loaders for Tamil AI Voice Assistant

This module provides document loaders for various file formats
including PDF, DOCX, TXT, and more. Optimized for Tamil text extraction.
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.settings import settings

# Import document parsing libraries
try:
    from pypdf import PdfReader
except ImportError:
    raise ImportError(
        "pypdf not installed. "
        "Run: pip install pypdf>=4.0.0"
    )

try:
    from docx import Document as DocxDocument
except ImportError:
    raise ImportError(
        "python-docx not installed. "
        "Run: pip install python-docx>=1.0.0"
    )


@dataclass
class LoadedDocument:
    """Represents a loaded document with metadata"""
    content: str
    metadata: Dict
    source: str
    doc_type: str

    def __post_init__(self):
        # Ensure metadata has required fields
        if "loaded_at" not in self.metadata:
            self.metadata["loaded_at"] = datetime.now().isoformat()
        if "source" not in self.metadata:
            self.metadata["source"] = self.source
        if "doc_type" not in self.metadata:
            self.metadata["doc_type"] = self.doc_type


class BaseLoader:
    """Base class for document loaders"""

    def __init__(self, file_path: Path):
        """
        Initialize loader

        Args:
            file_path: Path to the file to load
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

    def load(self) -> LoadedDocument:
        """
        Load the document

        Returns:
            LoadedDocument object
        """
        raise NotImplementedError("Subclasses must implement load()")

    def _get_base_metadata(self) -> Dict:
        """Get base metadata for the file"""
        stat = self.file_path.stat()
        return {
            "filename": self.file_path.name,
            "file_path": str(self.file_path),
            "file_size": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }


class PDFLoader(BaseLoader):
    """
    PDF document loader

    Extracts text from PDF files, preserving Tamil Unicode characters.
    """

    def load(self) -> LoadedDocument:
        """
        Load PDF document

        Returns:
            LoadedDocument with extracted text
        """
        try:
            reader = PdfReader(str(self.file_path))

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(page_text)

            # Combine all pages
            content = "\n\n".join(text_parts)

            # Get metadata
            metadata = self._get_base_metadata()
            metadata.update({
                "num_pages": len(reader.pages),
                "pdf_metadata": self._extract_pdf_metadata(reader),
            })

            return LoadedDocument(
                content=content,
                metadata=metadata,
                source=str(self.file_path),
                doc_type="pdf"
            )

        except Exception as e:
            raise RuntimeError(f"Error loading PDF: {e}")

    def _extract_pdf_metadata(self, reader: PdfReader) -> Dict:
        """Extract PDF metadata if available"""
        metadata = {}

        if reader.metadata:
            # Convert PDF metadata to dict
            for key in ['/Title', '/Author', '/Subject', '/Creator', '/Producer']:
                if key in reader.metadata:
                    clean_key = key.strip('/')
                    metadata[clean_key.lower()] = str(reader.metadata[key])

        return metadata


class DOCXLoader(BaseLoader):
    """
    DOCX document loader

    Extracts text from Microsoft Word documents.
    """

    def load(self) -> LoadedDocument:
        """
        Load DOCX document

        Returns:
            LoadedDocument with extracted text
        """
        try:
            doc = DocxDocument(str(self.file_path))

            # Extract paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        paragraphs.append(row_text)

            # Combine all content
            content = "\n\n".join(paragraphs)

            # Get metadata
            metadata = self._get_base_metadata()
            metadata.update({
                "num_paragraphs": len(doc.paragraphs),
                "num_tables": len(doc.tables),
                "docx_metadata": self._extract_docx_metadata(doc),
            })

            return LoadedDocument(
                content=content,
                metadata=metadata,
                source=str(self.file_path),
                doc_type="docx"
            )

        except Exception as e:
            raise RuntimeError(f"Error loading DOCX: {e}")

    def _extract_docx_metadata(self, doc: DocxDocument) -> Dict:
        """Extract DOCX core properties"""
        metadata = {}

        if hasattr(doc, 'core_properties'):
            props = doc.core_properties
            if props.title:
                metadata['title'] = props.title
            if props.author:
                metadata['author'] = props.author
            if props.subject:
                metadata['subject'] = props.subject
            if props.keywords:
                metadata['keywords'] = props.keywords

        return metadata


class TXTLoader(BaseLoader):
    """
    Plain text file loader

    Loads .txt files with UTF-8 encoding (for Tamil text).
    """

    def __init__(self, file_path: Path, encoding: str = "utf-8"):
        """
        Initialize TXT loader

        Args:
            file_path: Path to the file
            encoding: Text encoding (default: utf-8 for Tamil)
        """
        super().__init__(file_path)
        self.encoding = encoding

    def load(self) -> LoadedDocument:
        """
        Load text file

        Returns:
            LoadedDocument with file content
        """
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read()

            # Get metadata
            metadata = self._get_base_metadata()
            metadata.update({
                "encoding": self.encoding,
                "num_lines": content.count('\n') + 1,
                "num_chars": len(content),
            })

            return LoadedDocument(
                content=content,
                metadata=metadata,
                source=str(self.file_path),
                doc_type="txt"
            )

        except UnicodeDecodeError:
            raise RuntimeError(
                f"Error decoding file with {self.encoding} encoding. "
                "Try a different encoding."
            )
        except Exception as e:
            raise RuntimeError(f"Error loading text file: {e}")


class DocumentLoaderFactory:
    """
    Factory for creating appropriate document loaders based on file type
    """

    LOADERS = {
        '.pdf': PDFLoader,
        '.docx': DOCXLoader,
        '.doc': DOCXLoader,  # .doc files can sometimes be read as .docx
        '.txt': TXTLoader,
    }

    @classmethod
    def create_loader(cls, file_path: Path) -> BaseLoader:
        """
        Create appropriate loader for the file

        Args:
            file_path: Path to the file

        Returns:
            Appropriate loader instance

        Raises:
            ValueError: If file type not supported
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix not in cls.LOADERS:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: {', '.join(cls.LOADERS.keys())}"
            )

        loader_class = cls.LOADERS[suffix]
        return loader_class(file_path)

    @classmethod
    def load_document(cls, file_path: Path) -> LoadedDocument:
        """
        Load document using appropriate loader

        Args:
            file_path: Path to the file

        Returns:
            LoadedDocument object
        """
        loader = cls.create_loader(file_path)
        return loader.load()

    @classmethod
    def load_directory(
        cls,
        directory: Path,
        recursive: bool = False,
        file_extensions: Optional[List[str]] = None,
    ) -> List[LoadedDocument]:
        """
        Load all supported documents from a directory

        Args:
            directory: Directory path
            recursive: Search subdirectories
            file_extensions: Filter by extensions (default: all supported)

        Returns:
            List of LoadedDocument objects
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Determine which extensions to load
        extensions = file_extensions or list(cls.LOADERS.keys())

        # Find files
        documents = []
        pattern = "**/*" if recursive else "*"

        for ext in extensions:
            for file_path in directory.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    try:
                        doc = cls.load_document(file_path)
                        documents.append(doc)
                        print(f"✅ Loaded: {file_path.name}")
                    except Exception as e:
                        print(f"⚠️  Failed to load {file_path.name}: {e}")

        return documents


if __name__ == "__main__":
    # Test document loaders
    print("="*60)
    print("🧪 Testing Document Loaders")
    print("="*60)

    # Create a test text file
    test_dir = Path("data/docs")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "test_tamil.txt"
    tamil_content = """வணக்கம்!

இது ஒரு சோதனை ஆவணம். தமிழ் மொழியில் எழுதப்பட்டுள்ளது.

செயற்கை நுண்ணறிவு:
- இயந்திரக் கற்றல்
- ஆழ்ந்த கற்றல்
- இயற்கை மொழி செயலாக்கம்

இது முதல் பத்தி முடிந்தது.

இது இரண்டாவது பத்தி. மேலும் சில விவரங்கள் இங்கே.
"""

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(tamil_content)

    print(f"\n📝 Created test file: {test_file}")

    # Test TXT loader
    print("\n" + "="*60)
    print("🧪 Test 1: Loading TXT file")
    print("="*60)

    try:
        doc = DocumentLoaderFactory.load_document(test_file)
        print(f"\n✅ Document loaded successfully!")
        print(f"   Type: {doc.doc_type}")
        print(f"   Source: {doc.source}")
        print(f"   Content length: {len(doc.content)} chars")
        print(f"   Lines: {doc.metadata.get('num_lines')}")
        print(f"\nFirst 150 characters:")
        print(doc.content[:150])
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test with directory
    print("\n" + "="*60)
    print("🧪 Test 2: Loading directory")
    print("="*60)

    try:
        docs = DocumentLoaderFactory.load_directory(
            test_dir,
            file_extensions=['.txt']
        )
        print(f"\n✅ Loaded {len(docs)} documents from directory")
        for doc in docs:
            print(f"   - {doc.metadata['filename']} ({len(doc.content)} chars)")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    print("\nNote: To test PDF and DOCX loaders, add sample files to data/docs/")
