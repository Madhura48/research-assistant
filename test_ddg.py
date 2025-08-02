from duckduckgo_search import DDGS
import json

def test_ddg_search():
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("artificial intelligence research 2024", max_results=3))
            print("✓ DuckDuckGo Search is working!")
            print(f"Found {len(results)} results")
            if results:
                print(f"Sample result: {results[0]['title']}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_ddg_search()