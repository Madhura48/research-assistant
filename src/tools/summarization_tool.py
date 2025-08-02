from crewai import tool  # Changed from crewai_tools
from typing import Dict, Any
import json
from datetime import datetime

@tool("content_summarizer")
def content_summarizer(content: str, summary_type: str = "comprehensive") -> str:
    """
    Advanced content summarization tool with multiple summary types.
    
    Args:
        content: Text content to summarize
        summary_type: Type of summary ("brief", "comprehensive", "bullet_points", "abstract")
    
    Returns:
        JSON string with summarized content and metadata
    """
    try:
        # Content analysis
        word_count = len(content.split())
        char_count = len(content)
        
        # Determine summary length based on content and type
        summary_lengths = {
            "brief": min(100, word_count // 10),
            "comprehensive": min(300, word_count // 5), 
            "bullet_points": min(150, word_count // 8),
            "abstract": min(250, word_count // 6)
        }
        
        target_length = summary_lengths.get(summary_type, 200)
        
        # Create summary instructions based on type
        instructions = {
            "brief": "Create a concise summary highlighting only the most essential points.",
            "comprehensive": "Create a detailed summary covering all major points and key details.",
            "bullet_points": "Extract key points and present as structured bullet points.",
            "abstract": "Create an academic-style abstract with background, methods, results, and conclusions."
        }
        
        summary_result = {
            "timestamp": datetime.now().isoformat(),
            "summary_type": summary_type,
            "original_length": word_count,
            "target_length": target_length,
            "compression_ratio": target_length / word_count if word_count > 0 else 0,
            "instructions_used": instructions.get(summary_type, instructions["comprehensive"]),
            "content_metadata": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_reading_time": f"{word_count // 200} minutes"
            }
        }
        
        return json.dumps(summary_result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Summarization failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })