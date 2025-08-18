"""
Test script to demonstrate console search output.
This will show the enhanced search results printed to console.
"""

import asyncio
from backend.search_engine import SemanticSearchEngine, SearchContext
from backend.embedding_service import embedding_service


async def test_console_search():
    """Test search with console output."""
    print("🚀 Starting Console Search Test")
    print("This will demonstrate the search engine printing results to console.")
    
    # Initialize services
    print("\n1. Initializing embedding service...")
    await embedding_service.initialize()
    
    print("2. Initializing search engine...")
    search_engine = SemanticSearchEngine()
    
    # Create sample documents with more realistic content
    print("3. Creating sample documents...")
    
    doc1_sections = [
        {
            "section_id": "doc1_intro",
            "content": "Machine learning is a powerful subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data, identify patterns, and make predictions or decisions.",
            "page_number": 1,
            "section_type": "paragraph"
        },
        {
            "section_id": "doc1_applications", 
            "content": "Deep learning neural networks have revolutionized many fields including computer vision, natural language processing, and speech recognition. These networks can process complex, high-dimensional data and extract meaningful features automatically.",
            "page_number": 2,
            "section_type": "paragraph"
        }
    ]
    
    doc2_sections = [
        {
            "section_id": "doc2_overview",
            "content": "Artificial intelligence encompasses various techniques including machine learning, deep learning, and expert systems. Modern AI systems can perform tasks that traditionally required human intelligence such as image recognition and language translation.",
            "page_number": 1,
            "section_type": "paragraph"
        },
        {
            "section_id": "doc2_future",
            "content": "The future of AI involves developing more sophisticated algorithms that can reason, learn from limited data, and explain their decision-making processes. Explainable AI and few-shot learning are key research areas.",
            "page_number": 2,
            "section_type": "paragraph"
        }
    ]
    
    doc3_sections = [
        {
            "section_id": "doc3_ethics",
            "content": "AI ethics and responsible AI development are crucial considerations as these technologies become more prevalent. Issues include bias in algorithms, privacy concerns, and the need for transparency in AI decision-making.",
            "page_number": 1,
            "section_type": "paragraph"
        }
    ]
    
    # Generate embeddings
    print("4. Generating embeddings...")
    await embedding_service.generate_document_embeddings("technical_doc", doc1_sections)
    await embedding_service.generate_document_embeddings("overview_doc", doc2_sections)
    await embedding_service.generate_document_embeddings("ethics_doc", doc3_sections)
    
    print(f"   ✅ Generated embeddings for {embedding_service.get_total_embedding_count()} sections")
    
    # Test different search queries
    test_queries = [
        "machine learning algorithms and data analysis",
        "neural networks for computer vision",
        "artificial intelligence ethics and bias",
        "deep learning applications",
        "AI decision making processes"
    ]
    
    print("\n5. Testing search queries with console output...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i}/{len(test_queries)} ---")
        
        context = SearchContext(
            query=query,
            document_ids=["technical_doc", "overview_doc", "ethics_doc"]
        )
        
        # This will trigger the console output we added
        results = await search_engine.search(context)
        
        # Small delay between searches
        await asyncio.sleep(0.5)
    
    print("\n🎉 Console Search Test Complete!")
    print("You should see detailed search results printed above with:")
    print("   - Query information")
    print("   - Search timing")
    print("   - Result details (document, confidence, snippets)")
    print("   - Search statistics")


if __name__ == "__main__":
    asyncio.run(test_console_search())