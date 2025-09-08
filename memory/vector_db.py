import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Optional
from datetime import datetime

class ResearchMemory:
    def __init__(self, persist_dir: str = "./chroma_db"):
        """
        Initialize ChromaDB for storing research papers
        """
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Create collection for research papers
        self.collection = self.client.get_or_create_collection(
            name="research_papers",
            metadata={"hnsw:space": "cosine"}
        )
    
    def store_paper(self, content: str, metadata: Dict, chunks: List[str] = None) -> str:
        """
        Store a research paper in the database
        - content: Full text of the paper
        - metadata: Paper metadata (title, authors, etc.)
        - chunks: Optional list of text chunks for better search
        """
        paper_id = str(uuid.uuid4())
        
        # Use chunks if provided, otherwise use full content
        documents = chunks if chunks else [content]
        
        # Add paper_id to metadata for easier retrieval
        paper_metadata = metadata.copy()
        paper_metadata["paper_id"] = paper_id
        
        self.collection.add(
            documents=documents,
            metadatas=[paper_metadata] * len(documents),
            ids=[f"{paper_id}_{i}" for i in range(len(documents))]
        )
        
        return paper_id
    
    def search_similar_papers(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for papers similar to the query
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        papers = []
        for i in range(len(results["ids"][0])):
            papers.append({
                "id": results["ids"][0][i].split('_')[0],  # Get original paper ID
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i]  # Convert to similarity score
            })
        
        return papers
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """
        Retrieve a specific paper by its ID
        """
        try:
            # Get all chunks for this paper
            results = self.collection.get(
                where={"paper_id": paper_id},
                include=["documents", "metadatas"]
            )
            
            if results["ids"]:
                # Reconstruct full paper content
                full_content = " ".join(results["documents"])
                return {
                    "id": paper_id,
                    "content": full_content,
                    "metadata": results["metadatas"][0]  # Metadata is same for all chunks
                }
        except:
            return None
        return None