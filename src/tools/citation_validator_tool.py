from crewai import tool  # Changed from crewai_tools
from typing import Dict, List, Any, Optional
import re
import requests
from datetime import datetime
import json
from urllib.parse import urlparse
import time

@tool("citation_validator")
def citation_validator(citations: str, citation_style: str = "APA") -> str:
    """
    Advanced citation validator and formatter tool that verifies citation accuracy,
    checks URL accessibility, and formats citations according to academic standards.
    
    Args:
        citations: String containing citations to validate (can be multiple citations)
        citation_style: Citation style to use ("APA", "MLA", "Chicago") - default: APA
    
    Returns:
        JSON string with validation results, formatted citations, and quality scores
    """
    try:
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "citation_style": citation_style,
            "input_citations": citations,
            "validation_summary": {},
            "validated_citations": [],
            "issues_found": [],
            "recommendations": []
        }
        
        # Parse individual citations
        citation_list = _parse_citations(citations)
        
        total_citations = len(citation_list)
        valid_citations = 0
        
        for idx, citation in enumerate(citation_list):
            validation_result = _validate_single_citation(citation, citation_style, idx + 1)
            validation_results["validated_citations"].append(validation_result)
            
            if validation_result["is_valid"]:
                valid_citations += 1
            
            # Collect issues
            validation_results["issues_found"].extend(validation_result.get("issues", []))
        
        # Generate summary
        validation_results["validation_summary"] = {
            "total_citations": total_citations,
            "valid_citations": valid_citations,
            "validation_rate": valid_citations / total_citations if total_citations > 0 else 0,
            "overall_quality_score": _calculate_overall_quality(validation_results["validated_citations"]),
            "needs_improvement": valid_citations < total_citations
        }
        
        # Generate recommendations
        validation_results["recommendations"] = _generate_recommendations(validation_results)
        
        return json.dumps(validation_results, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Citation validation failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "input": citations
        })

def _parse_citations(citations_text: str) -> List[str]:
    """Parse multiple citations from input text"""
    # Split by common citation separators
    separators = ['\n\n', '\n•', '\n-', '\n1.', '\n2.', '\n3.']
    
    citations = [citations_text]
    for sep in separators:
        new_citations = []
        for citation in citations:
            new_citations.extend(citation.split(sep))
        citations = new_citations
    
    # Clean and filter
    citations = [c.strip() for c in citations if c.strip() and len(c.strip()) > 20]
    
    return citations

def _validate_single_citation(citation: str, style: str, citation_number: int) -> Dict[str, Any]:
    """Validate a single citation comprehensively"""
    
    validation_result = {
        "citation_number": citation_number,
        "original_citation": citation,
        "is_valid": False,
        "quality_score": 0.0,
        "issues": [],
        "strengths": [],
        "formatted_citation": "",
        "metadata": {},
        "url_validation": {}
    }
    
    # Extract citation components
    components = _extract_citation_components(citation)
    validation_result["metadata"] = components
    
    # Validate required components based on style
    required_components = _get_required_components(style)
    component_score = _validate_components(components, required_components, validation_result)
    
    # Validate URLs if present
    if components.get("url"):
        url_validation = _validate_url_accessibility(components["url"])
        validation_result["url_validation"] = url_validation
        if url_validation["is_accessible"]:
            validation_result["strengths"].append("URL is accessible")
            component_score += 0.1
        else:
            validation_result["issues"].append(f"URL not accessible: {url_validation['error']}")
    
    # Format citation according to style
    validation_result["formatted_citation"] = _format_citation(components, style)
    
    # Calculate final quality score
    validation_result["quality_score"] = min(component_score, 1.0)
    validation_result["is_valid"] = validation_result["quality_score"] >= 0.7
    
    return validation_result

def _extract_citation_components(citation: str) -> Dict[str, str]:
    """Extract components from citation using regex patterns"""
    components = {}
    
    # URL extraction
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, citation)
    if urls:
        components["url"] = urls[0]
    
    # Year extraction
    year_pattern = r'\b(19|20)\d{2}\b'
    years = re.findall(year_pattern, citation)
    if years:
        components["year"] = years[-1]  # Take the last year found
    
    # DOI extraction
    doi_pattern = r'10\.\d{4,}/[^\s]+'
    dois = re.findall(doi_pattern, citation)
    if dois:
        components["doi"] = dois[0]
    
    # Title extraction (text in quotes or after specific patterns)
    title_patterns = [
        r'"([^"]+)"',  # Text in quotes
        r'["""]([^"""]+)["""]',  # Smart quotes
    ]
    
    for pattern in title_patterns:
        titles = re.findall(pattern, citation)
        if titles:
            components["title"] = titles[0]
            break
    
    # Author extraction (names before year or at beginning)
    if components.get("year"):
        author_pattern = f'([^.]+?)\\s*\\({components["year"]}\\)'
        authors = re.findall(author_pattern, citation)
        if authors:
            components["author"] = authors[0].strip()
    
    # Journal/Source extraction (italicized text or after title)
    journal_patterns = [
        r'\*([^*]+)\*',  # Text in asterisks
        r'_([^_]+)_',    # Text in underscores
    ]
    
    for pattern in journal_patterns:
        journals = re.findall(pattern, citation)
        if journals:
            components["journal"] = journals[0]
            break
    
    return components

def _get_required_components(style: str) -> List[str]:
    """Get required citation components for different styles"""
    common_required = ["author", "title", "year"]
    
    style_requirements = {
        "APA": common_required + ["source"],
        "MLA": common_required + ["source"],
        "Chicago": common_required + ["source"]
    }
    
    return style_requirements.get(style.upper(), common_required)

def _validate_components(components: Dict[str, str], required: List[str], 
                        validation_result: Dict[str, Any]) -> float:
    """Validate citation components and return quality score"""
    score = 0.0
    total_required = len(required)
    
    for component in required:
        if components.get(component):
            score += 1.0 / total_required
            validation_result["strengths"].append(f"Has {component}")
        else:
            validation_result["issues"].append(f"Missing {component}")
    
    # Bonus points for additional quality indicators
    if components.get("doi"):
        score += 0.1
        validation_result["strengths"].append("Includes DOI")
    
    if components.get("url"):
        score += 0.05
        validation_result["strengths"].append("Includes URL")
    
    return score

def _validate_url_accessibility(url: str) -> Dict[str, Any]:
    """Check if URL is accessible and gather metadata"""
    validation = {
        "url": url,
        "is_accessible": False,
        "response_time": None,
        "status_code": None,
        "error": None,
        "metadata": {}
    }
    
    try:
        start_time = time.time()
        response = requests.head(url, timeout=10, allow_redirects=True)
        validation["response_time"] = round(time.time() - start_time, 2)
        validation["status_code"] = response.status_code
        validation["is_accessible"] = response.status_code == 200
        
        if response.status_code != 200:
            validation["error"] = f"HTTP {response.status_code}"
        
        # Extract domain information
        parsed_url = urlparse(url)
        validation["metadata"] = {
            "domain": parsed_url.netloc,
            "is_secure": parsed_url.scheme == "https",
            "path": parsed_url.path
        }
        
    except requests.exceptions.Timeout:
        validation["error"] = "Request timeout"
    except requests.exceptions.ConnectionError:
        validation["error"] = "Connection failed"
    except Exception as e:
        validation["error"] = str(e)
    
    return validation

def _format_citation(components: Dict[str, str], style: str) -> str:
    """Format citation according to specified academic style"""
    
    if style.upper() == "APA":
        return _format_apa_citation(components)
    elif style.upper() == "MLA":
        return _format_mla_citation(components)
    elif style.upper() == "CHICAGO":
        return _format_chicago_citation(components)
    else:
        return _format_apa_citation(components)  # Default to APA

def _format_apa_citation(components: Dict[str, str]) -> str:
    """Format citation in APA style"""
    parts = []
    
    if components.get("author"):
        parts.append(f"{components['author']}")
    
    if components.get("year"):
        parts.append(f"({components['year']})")
    
    if components.get("title"):
        parts.append(f"{components['title']}")
    
    if components.get("journal"):
        parts.append(f"*{components['journal']}*")
    
    if components.get("url"):
        parts.append(f"Retrieved from {components['url']}")
    
    return ". ".join(parts) + "."

def _format_mla_citation(components: Dict[str, str]) -> str:
    """Format citation in MLA style"""
    parts = []
    
    if components.get("author"):
        parts.append(f"{components['author']}")
    
    if components.get("title"):
        parts.append(f'"{components["title"]}"')
    
    if components.get("journal"):
        parts.append(f"*{components['journal']}*")
    
    if components.get("year"):
        parts.append(f"{components['year']}")
    
    if components.get("url"):
        parts.append(f"Web. {datetime.now().strftime('%d %b %Y')}")
    
    return ", ".join(parts) + "."

def _format_chicago_citation(components: Dict[str, str]) -> str:
    """Format citation in Chicago style"""
    parts = []
    
    if components.get("author"):
        parts.append(f"{components['author']}")
    
    if components.get("title"):
        parts.append(f'"{components["title"]}"')
    
    if components.get("journal"):
        parts.append(f"*{components['journal']}*")
    
    if components.get("year"):
        parts.append(f"({components['year']})")
    
    if components.get("url"):
        parts.append(f"accessed {datetime.now().strftime('%B %d, %Y')}, {components['url']}")
    
    return ", ".join(parts) + "."

def _calculate_overall_quality(validated_citations: List[Dict[str, Any]]) -> float:
    """Calculate overall quality score for all citations"""
    if not validated_citations:
        return 0.0
    
    total_score = sum(citation.get("quality_score", 0) for citation in validated_citations)
    return total_score / len(validated_citations)

def _generate_recommendations(validation_results: Dict[str, Any]) -> List[str]:
    """Generate specific recommendations for improving citations"""
    recommendations = []
    
    issues = validation_results.get("issues_found", [])
    quality_score = validation_results.get("validation_summary", {}).get("overall_quality_score", 0)
    
    # Common issue patterns
    missing_authors = any("Missing author" in issue for issue in issues)
    missing_years = any("Missing year" in issue for issue in issues)
    missing_titles = any("Missing title" in issue for issue in issues)
    url_issues = any("URL not accessible" in issue for issue in issues)
    
    if missing_authors:
        recommendations.append("Add author information for incomplete citations")
    
    if missing_years:
        recommendations.append("Include publication years for all sources")
    
    if missing_titles:
        recommendations.append("Provide complete titles for all cited works")
    
    if url_issues:
        recommendations.append("Verify all URLs are accessible and current")
    
    if quality_score < 0.7:
        recommendations.append("Review citations for completeness and accuracy")
    
    if quality_score < 0.5:
        recommendations.append("Consider using more authoritative sources")
    
    # Style-specific recommendations
    style = validation_results.get("citation_style", "APA")
    recommendations.append(f"Ensure all citations follow {style} formatting guidelines")
    
    return recommendations

# Additional utility functions for advanced validation
def validate_doi(doi: str) -> bool:
    """Validate DOI format and check if it resolves"""
    doi_pattern = r'^10\.\d{4,}/[^\s]+$'
    if not re.match(doi_pattern, doi):
        return False
    
    try:
        response = requests.head(f"https://doi.org/{doi}", timeout=5)
        return response.status_code in [200, 302]
    except:
        return False

def extract_metadata_from_url(url: str) -> Dict[str, str]:
    """Extract metadata from web page for citation enhancement"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            metadata = {}
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Extract meta tags
            meta_tags = ['author', 'description', 'keywords', 'published-time']
            for tag in meta_tags:
                meta = soup.find('meta', {'name': tag}) or soup.find('meta', {'property': f'article:{tag}'})
                if meta:
                    metadata[tag] = meta.get('content', '')
            
            return metadata
    except:
        return {}