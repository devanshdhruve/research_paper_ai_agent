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
    
    def get_all_paper_metadata(self) -> List[Dict]:
        """
        Retrieve metadata for all papers (fast, for listing only)
        Returns list of metadata dictionaries without content
        """
        try:
            # Get all items but only include metadatas
            results = self.collection.get(include=["metadatas"])
        
            if not results["ids"]:
                return []
        
            # Use dict to get unique papers based on paper_id in metadata
            unique_papers = {}
        
            for metadata in results["metadatas"]:
                paper_id = metadata.get("paper_id")
                if paper_id and paper_id not in unique_papers:
                    # Create a copy to avoid modifying original metadata
                    paper_metadata = metadata.copy()
                    unique_papers[paper_id] = paper_metadata
        
            return list(unique_papers.values())
        
        except Exception as e:
            print(f"Error retrieving paper metadata: {e}")
            return []

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """
        Retrieve a specific paper by its ID with full content
        For processing, summarization, etc.
        """
        try:
            # Get all chunks for this paper
            results = self.collection.get(
                where={"paper_id": paper_id},
                include=["documents", "metadatas"]
            )
        
            if results["ids"]:
                # Reconstruct full paper content from chunks
                full_content = " ".join(results["documents"])
                return {
                    "id": paper_id,
                    "content": full_content,
                    "metadata": results["metadatas"][0]  # Metadata is same for all chunks
                }
        except Exception as e:
            print(f"Error retrieving paper {paper_id}: {e}")
            return None
        return None