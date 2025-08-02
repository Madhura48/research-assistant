from crewai import tool
from duckduckgo_search import DDGS
from typing import List, Dict, Any
import json
import time
from datetime import datetime

@tool
def advanced_web_search(query: str, max_results: int = 5, region: str = "us-en") -> str:
    """
    Advanced web search tool with quality filtering and result ranking.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
        region: Search region (default: us-en)
    
    Returns:
        JSON string containing search results with metadata
    """
    try:
        results = []
        search_metadata = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "region": region,
            "total_results": 0
        }
        
        with DDGS() as ddgs:
            # Perform text search
            search_results = list(ddgs.text(
                query, 
                max_results=max_results * 2,  # Get more results for filtering
                region=region
            ))
            
            # Filter and rank results
            for result in search_results[:max_results]:
                processed_result = {
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                    "relevance_score": _calculate_relevance(query, result),
                    "content_quality": _assess_content_quality(result),
                    "source_type": _identify_source_type(result.get("href", ""))
                }
                results.append(processed_result)
            
            # Sort by relevance and quality
            results.sort(key=lambda x: (x["relevance_score"] + x["content_quality"]) / 2, reverse=True)
            
            search_metadata["total_results"] = len(results)
            search_metadata["avg_relevance"] = sum(r["relevance_score"] for r in results) / len(results) if results else 0
        
        return json.dumps({
            "metadata": search_metadata,
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat()
        })

def _calculate_relevance(query: str, result: dict) -> float:
    """Calculate relevance score based on query-result matching"""
    query_terms = set(query.lower().split())
    title = result.get("title", "").lower()
    body = result.get("body", "").lower()
    
    title_matches = len([term for term in query_terms if term in title])
    body_matches = len([term for term in query_terms if term in body])
    
    # Weight title matches more heavily
    relevance = (title_matches * 0.7 + body_matches * 0.3) / len(query_terms)
    return min(relevance, 1.0)

def _assess_content_quality(result: dict) -> float:
    """Assess content quality based on various factors"""
    title = result.get("title", "")
    body = result.get("body", "")
    url = result.get("href", "")
    
    quality_score = 0.5  # Base score
    
    # Length indicators
    if len(body) > 100:
        quality_score += 0.2
    if len(title) > 20:
        quality_score += 0.1
    
    # Source quality indicators
    if any(domain in url for domain in [".edu", ".gov", ".org"]):
        quality_score += 0.3
    elif any(domain in url for domain in ["wikipedia", "arxiv", "scholar"]):
        quality_score += 0.2
    
    return min(quality_score, 1.0)

def _identify_source_type(url: str) -> str:
    """Identify the type of source based on URL"""
    if ".edu" in url:
        return "academic"
    elif ".gov" in url:
        return "government"
    elif ".org" in url:
        return "organization"
    elif "wikipedia" in url:
        return "encyclopedia"
    elif "arxiv" in url:
        return "preprint"
    elif any(news in url for news in ["bbc", "cnn", "reuters", "ap", "news"]):
        return "news"
    else:
        return "general"