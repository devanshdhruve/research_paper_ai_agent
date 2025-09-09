from memory.vector_db import ResearchMemory

def main():
    memory = ResearchMemory()
    
    # Get all papers
    all_data = memory.collection.get()
    
    # Count unique papers
    paper_ids = set()
    for id_str in all_data["ids"]:
        paper_id = id_str.split('_')[0]  # Extract base paper ID from chunk ID
        paper_ids.add(paper_id)
    
    print(f"📊 Papers in memory: {len(paper_ids)}")
    print(f"📊 Total chunks: {len(all_data['ids'])}")
    
    # Show first few papers if available
    if paper_ids:
        print(f"\n📚 Paper IDs:")
        for i, paper_id in enumerate(list(paper_ids)[:6], 1):
            print(f"   {i}. {paper_id}")
        
        if len(paper_ids) > 5:
            print(f"   ... and {len(paper_ids) - 6} more")

if __name__ == "__main__":
    main()