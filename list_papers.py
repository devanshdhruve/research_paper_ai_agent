from memory.vector_db import ResearchMemory

def main():
    memory = ResearchMemory()
    papers = memory.get_all_papers()
    
    print("📚 Papers in ChromaDB:")
    print("======================")
    
    for paper_id in papers:
        paper_data = memory.get_paper_by_id(paper_id)
        if paper_data:
            title = paper_data['metadata'].get('title', 'Unknown Title')
            processed = "✅" if paper_data['metadata'].get('processed') else "⏳"
            print(f"{processed} {title}")
            print(f"   ID: {paper_id}")
            print(f"   File: {paper_data['metadata'].get('file_name')}")
            print()

if __name__ == "__main__":
    main()