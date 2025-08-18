"""
Demo script showing console search output with lower confidence threshold.
This will show more results to demonstrate the full console output format.
"""

import asyncio
from backend.search_engine import SemanticSearchEngine, SearchContext, SearchStrategy
from backend.embedding_service import embedding_service


async def demo_console_search():
    """Demo search with console output showing results."""
    print("🎯 CONSOLE SEARCH DEMO")
    print("=" * 60)
    
    # Initialize services
    await embedding_service.initialize()
    
    # Create search engine with lower confidence threshold to show results
    strategy = SearchStrategy(
        confidence_threshold=0.5,  # Lower threshold to show more results
        max_results=3
    )
    search_engine = SemanticSearchEngine(strategy)
    
    # Create sample documents
    doc_sections = [
        {
            "section_id": "ml_intro",
            "content": "Machine learning algorithms analyze large datasets to identify patterns and make predictions. Common algorithms include linear regression, decision trees, and neural networks.",
            "page_number": 1,
            "section_type": "paragraph"
        },
        {
            "section_id": "ai_overview",
            "content": "Artificial intelligence systems can perform tasks that typically require human intelligence, such as visual perception, speech recognition, and decision-making.",
            "page_number": 1,
            "section_type": "paragraph"
        },
        {
            "section_id": "data_science",
            "content": "Data science combines statistical analysis, machine learning, and domain expertise to extract insights from structured and unstructured data sources.",
            "page_number": 1,
            "section_type": "paragraph"
        }
    ]
    
    # Generate embeddings
    await embedding_service.generate_document_embeddings("demo_doc", doc_sections)
    
    print(f"📚 Created demo document with {len(doc_sections)} sections")
    print(f"🔧 Using confidence threshold: {strategy.confidence_threshold}")
    
    # Test queries that should return results
    test_queries = [
        "machine learning patterns",
        "artificial intelligence tasks", 
        "data analysis techniques"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        context = SearchContext(
            query=query,
            document_ids=["demo_doc"]
        )
        
        # This will show the detailed console output
        results = await search_engine.search(context)
        
        await asyncio.sleep(1)  # Pause between searches
    
    print("\n✨ Demo complete! The console output above shows:")
    print("   🔍 Search query and timing")
    print("   📄 Detailed result information")
    print("   📊 Search statistics and performance")
    print("   🎯 Multi-tier search strategy in action")


if __name__ == "__main__":
    asyncio.run(demo_console_search())