from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from typing import Dict, Any
import json
from ..config import Config

class AnalysisAgent:
    """
    Specialized agent for deep analysis, pattern recognition, and insight generation.
    """
    
    def __init__(self):
        self.config = Config()
        self.llm = ChatOpenAI(
            model=self.config.LLM_MODEL,
            temperature=0.2,
            openai_api_key=self.config.OPENAI_API_KEY
        )
        
        self.agent = Agent(
            role="Expert Data Analyst and Insight Generator",
            goal="""Analyze research findings to identify patterns, trends, insights,
                    and implications while maintaining analytical rigor and objectivity.""",
            backstory="""You are a renowned data scientist and analytical researcher with
                        expertise in pattern recognition, statistical analysis, and critical thinking.
                        You excel at finding meaningful insights in complex information and
                        identifying implications that others might miss.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3,
            memory=True
        )
    
    def analyze_research_findings(self, research_data: str, analysis_objectives: List[str] = None) -> str:
        """Perform deep analysis of research findings"""
        
        objectives_text = f"\nSpecific analysis objectives: {', '.join(analysis_objectives)}" if analysis_objectives else ""
        
        task = Task(
            description=f"""
            Perform comprehensive analysis of these research findings:
            
            RESEARCH DATA:
            {research_data}
            {objectives_text}
            
            Your analysis should include:
            
            1. PATTERN IDENTIFICATION:
               - Identify recurring themes and patterns
               - Analyze trends and developments over time
               - Recognize relationships between different concepts
               
            2. CRITICAL EVALUATION:
               - Assess the strength of evidence for key claims
               - Identify potential biases or limitations in sources
               - Evaluate methodological rigor where applicable
               
            3. INSIGHT GENERATION:
               - Extract key insights and implications
               - Identify surprising or counterintuitive findings
               - Generate hypotheses for further investigation
               
            4. COMPARATIVE ANALYSIS:
               - Compare different perspectives and approaches
               - Identify areas of consensus and disagreement
               - Analyze the evolution of ideas or practices
               
            5. GAP ANALYSIS:
               - Identify information gaps or uncertainties
               - Suggest areas where additional research is needed
               - Note conflicting information that requires resolution
            
            Provide your analysis in structured JSON format with:
            - executive_summary: Key insights and conclusions
            - detailed_findings: Organized by category
            - evidence_assessment: Quality and reliability evaluation
            - implications: Practical and theoretical implications
            - recommendations: Suggested next steps
            - confidence_levels: Confidence in different findings
            """,
            agent=self.agent,
            expected_output="Comprehensive JSON analysis with insights, patterns, and implications"
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        return crew.kickoff()