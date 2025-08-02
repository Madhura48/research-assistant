from crewai import tool  # Changed from crewai_tools
from typing import List, Dict, Any
import json
from datetime import datetime
import re

@tool("fact_checker")
def fact_checker(claims: str, sources: str) -> str:
    """
    Advanced fact-checking tool that verifies claims against sources.
    
    Args:
        claims: Claims or statements to verify
        sources: Source information to check against
    
    Returns:
        JSON string with fact-checking results and confidence scores
    """
    try:
        # Parse claims into individual statements
        claim_list = _parse_claims(claims)
        
        fact_check_results = {
            "timestamp": datetime.now().isoformat(),
            "total_claims": len(claim_list),
            "verification_results": [],
            "overall_reliability": 0.0,
            "methodology": "cross-reference verification with confidence scoring"
        }
        
        total_confidence = 0.0
        
        for idx, claim in enumerate(claim_list):
            verification = _verify_claim_against_sources(claim, sources, idx + 1)
            fact_check_results["verification_results"].append(verification)
            total_confidence += verification.get("confidence_score", 0)
        
        # Calculate overall reliability
        if len(claim_list) > 0:
            fact_check_results["overall_reliability"] = total_confidence / len(claim_list)
        
        return json.dumps(fact_check_results, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Fact checking failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

def _parse_claims(claims_text: str) -> List[str]:
    """Parse individual claims from text"""
    # Split by sentence endings and common separators
    sentences = re.split(r'[.!?]+|\n+', claims_text)
    
    # Clean and filter meaningful claims
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and not sentence.startswith(('http', 'www')):
            claims.append(sentence)
    
    return claims

def _verify_claim_against_sources(claim: str, sources: str, claim_number: int) -> Dict[str, Any]:
    """Verify a single claim against provided sources"""
    
    verification = {
        "claim_number": claim_number,
        "claim": claim,
        "confidence_score": 0.0,
        "verification_status": "unverified",
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "analysis": ""
    }
    
    # Simple keyword matching for verification
    claim_keywords = set(re.findall(r'\b\w+\b', claim.lower()))
    source_text = sources.lower()
    
    # Calculate keyword overlap
    matching_keywords = [kw for kw in claim_keywords if kw in source_text]
    keyword_overlap = len(matching_keywords) / len(claim_keywords) if claim_keywords else 0
    
    # Determine verification status
    if keyword_overlap >= 0.7:
        verification["verification_status"] = "strongly_supported"
        verification["confidence_score"] = 0.9
        verification["analysis"] = "High keyword overlap with sources suggests strong support"
    elif keyword_overlap >= 0.4:
        verification["verification_status"] = "partially_supported"
        verification["confidence_score"] = 0.6
        verification["analysis"] = "Moderate keyword overlap suggests partial support"
    else:
        verification["verification_status"] = "insufficient_evidence"
        verification["confidence_score"] = 0.3
        verification["analysis"] = "Low keyword overlap suggests insufficient supporting evidence"
    
    return verification