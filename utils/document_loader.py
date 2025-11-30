"""
Document Loading Utilities
Handles loading and parsing of PDF and text documents
"""
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Utility class for loading and splitting documents"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document loader
        
        Args:
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_pdf(self, file_path: str):
        """
        Load and split PDF document
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            List of document chunks
        """
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Loaded PDF: {file_path} ({len(chunks)} chunks)")
            return chunks
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            return []
    
    def load_text(self, file_path: str):
        """
        Load and split text document
        
        Args:
            file_path: Path to text file
        
        Returns:
            List of document chunks
        """
        try:
            loader = TextLoader(file_path)
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Loaded text: {file_path} ({len(chunks)} chunks)")
            return chunks
        except Exception as e:
            logger.error(f"Error loading text {file_path}: {e}")
            return []
    
    def load_directory(self, directory_path: str, file_extension: str = ".pdf"):
        """
        Load all documents of specified type from directory
        
        Args:
            directory_path: Path to directory
            file_extension: File extension to filter
        
        Returns:
            List of all document chunks
        """
        all_chunks = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.warning(f"Directory not found: {directory_path}")
            return all_chunks
        
        for file_path in directory.glob(f"*{file_extension}"):
            if file_extension == ".pdf":
                chunks = self.load_pdf(str(file_path))
            else:
                chunks = self.load_text(str(file_path))
            all_chunks.extend(chunks)
        
        logger.info(f"Loaded {len(all_chunks)} total chunks from {directory_path}")
        return all_chunks