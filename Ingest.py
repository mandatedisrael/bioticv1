import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from uuid import uuid4
from models import Models
from typing import List, Optional

load_dotenv()



class DocumentIngestionManager:
    def __init__(self):
        # Initialize Models
        self.model = Models()
        self.embeddings = self.model.embeddings_ollama
        
        # Vector Store Setup
        self.vector_store = Chroma(
            collection_name="documents",
            embedding_function=self.embeddings,
            persist_directory="./db/chroma_db"
        )
        
        # Configuration
        self.PDF_FOLDER = "./pdfs"
        self.TEXT_FOLDER = "./texts"
        self.CHUNK_SIZE = 1000
        self.CHUNK_OVERLAP = 50
        self.CHECK_INTERVAL = 10

    def _create_text_splitter(self):
        """Create a text splitter with configurable chunk size and overlap"""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
            separators=['\n\n','\n', ' ', '']
        )

    def _process_document(self, file_path: str) -> List[str]:
        """
        Process a single document file
        Supports PDF and text files
        """
        try:
            # Determine loader based on file extension
            if file_path.lower().endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.lower().endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                print(f"Unsupported file type: {file_path}")
                return []

            # Load and split documents
            loaded_documents = loader.load()
            text_splitter = self._create_text_splitter()
            documents = text_splitter.split_documents(loaded_documents)

            # Generate unique IDs
            uuids = [str(uuid4()) for _ in range(len(documents))]

            # Add metadata about source file
            for doc in documents:
                doc.metadata['source'] = os.path.basename(file_path)

            # Add documents to vector store
            self.vector_store.add_documents(documents=documents, ids=uuids)

            print(f"Processed {len(documents)} chunks from {file_path}")
            return uuids

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []

    def _get_documents_to_process(self) -> List[str]:
        """
        Collect documents to process from PDF and TEXT folders
        """
        documents = []
        
        # Check PDF folder
        if os.path.exists(self.PDF_FOLDER):
            documents.extend([
                os.path.join(self.PDF_FOLDER, f) 
                for f in os.listdir(self.PDF_FOLDER) 
                if not f.startswith('_') and (f.lower().endswith('.pdf') or f.lower().endswith('.txt'))
            ])
        
        # Check TEXT folder
        if os.path.exists(self.TEXT_FOLDER):
            documents.extend([
                os.path.join(self.TEXT_FOLDER, f) 
                for f in os.listdir(self.TEXT_FOLDER) 
                if not f.startswith('_') and f.lower().endswith('.txt')
            ])
        
        return documents

    def _mark_file_as_processed(self, file_path: str):
        """
        Rename file to indicate it has been processed
        """
        try:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            new_filename = f"_{filename}"
            new_file_path = os.path.join(directory, new_filename)
            
            os.rename(file_path, new_file_path)
            print(f"Marked {file_path} as processed")
        except Exception as e:
            print(f"Error marking {file_path} as processed: {e}")

    def run_ingestion_loop(self):
        """
        Continuous loop to process new documents
        """
        while True:
            # Find documents to process
            documents_to_process = self._get_documents_to_process()
            
            # Process each document
            for doc_path in documents_to_process:
                try:
                    # Process the document
                    processed_uuids = self._process_document(doc_path)
                    
                    # If processed successfully, mark as done
                    if processed_uuids:
                        self._mark_file_as_processed(doc_path)
                
                except Exception as e:
                    print(f"Error processing {doc_path}: {e}")
            
            # Wait before checking for new files again
            time.sleep(self.CHECK_INTERVAL)

def main():
    """
    Main function to start document ingestion
    """
    # Create folders if they don't exist
    os.makedirs("./pdfs", exist_ok=True)
    os.makedirs("./texts", exist_ok=True)
    os.makedirs("./db/chroma_db", exist_ok=True)

    # Initialize and run ingestion manager
    ingestion_manager = DocumentIngestionManager()
    ingestion_manager.run_ingestion_loop()
    print("Ingestion is done. Monitoring for new documents...")


if __name__ == "__main__":
    main()