from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
from datetime import datetime
from ..config import Config
from ..tools.search_tool import advanced_web_search

class ResearchAgent:
    """
    Specialized agent for information gathering and source evaluation.
    Implements advanced search strategies and quality assessment.
    """
    
    def __init__(self):
        self.config = Config()
        self.llm = ChatOpenAI(
            model=self.config.LLM_MODEL,
            temperature=0.1,
            openai_api_key=self.config.OPENAI_API_KEY
        )
        
        self.agent = Agent(
            role="Expert Information Researcher and Source Evaluator",
            goal="""Gather comprehensive, high-quality information from diverse sources,
                    evaluate source credibility, and organize findings for analysis.""",
            backstory="""You are a world-class research librarian and information scientist
                        with expertise in academic research, fact-checking, and source evaluation.
                        You excel at finding authoritative sources, assessing information quality,
                        and organizing complex information in structured formats.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[advanced_web_search],
            max_iter=3,
            memory=True
        )
    
    def gather_information(self, research_query: str, focus_areas: List[str] = None) -> str:
        """Execute comprehensive information gathering"""
        
        focus_text = f"\nFocus on these specific areas: {', '.join(focus_areas)}" if focus_areas else ""
        
        task = Task(
            description=f"""
            Conduct comprehensive research on: {research_query}
            {focus_text}
            
            Your research process should:
            
            1. SEARCH STRATEGY:
               - Use multiple search queries to cover different aspects
               - Search for both general information and specific details
               - Look for recent developments and historical context
               
            2. SOURCE EVALUATION:
               - Assess source credibility and authority
               - Identify potential biases or limitations
               - Prioritize academic, government, and reputable sources
               
            3. INFORMATION ORGANIZATION:
               - Categorize findings by topic and relevance
               - Note source types and publication dates
               - Identify key facts, statistics, and expert opinions
               
            4. QUALITY ASSURANCE:
               - Cross-reference information across sources
               - Flag conflicting information or uncertain claims
               - Assess completeness of coverage
            
            Provide your findings in a structured JSON format with:
            - search_queries_used: List of search terms
            - sources_found: Detailed source information
            - key_findings: Organized by category
            - quality_assessment: Overall evaluation
            - gaps_identified: Areas needing more research
            """,
            agent=self.agent,
            expected_output="Comprehensive JSON report of research findings with source evaluation"
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        return crew.kickoff()