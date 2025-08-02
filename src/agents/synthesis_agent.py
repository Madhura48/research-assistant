from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
from ..config import Config

class SynthesisAgent:
    """
    Specialized agent for synthesizing research and analysis into coherent,
    well-structured final outputs.
    """
    
    def __init__(self):
        self.config = Config()
        self.llm = ChatOpenAI(
            model=self.config.LLM_MODEL,
            temperature=0.3,
            openai_api_key=self.config.OPENAI_API_KEY
        )
        
        self.agent = Agent(
            role="Expert Research Synthesizer and Report Writer",
            goal="""Synthesize research findings and analysis into comprehensive,
                    well-structured reports that effectively communicate insights
                    to target audiences.""",
            backstory="""You are an accomplished academic writer and research synthesizer
                        with expertise in creating compelling, well-structured research reports.
                        You excel at weaving together complex information into coherent narratives
                        that are both comprehensive and accessible.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3,
            memory=True
        )
    
    def synthesize_research(self, research_data: str, analysis_data: str, 
                          output_format: str = "comprehensive_report") -> str:
        """Synthesize research and analysis into final output"""
        
        task = Task(
            description=f"""
            Synthesize the following research findings and analysis into a high-quality,
            comprehensive research report:
            
            RESEARCH FINDINGS:
            {research_data}
            
            ANALYSIS RESULTS:
            {analysis_data}
            
            TARGET FORMAT: {output_format}
            
            Your synthesis should include:
            
            1. EXECUTIVE SUMMARY:
               - Clear overview of the research topic
               - Key findings and insights (3-5 main points)
               - Primary conclusions and implications
               
            2. METHODOLOGY OVERVIEW:
               - Research approach and scope
               - Sources consulted and evaluation criteria
               - Limitations and caveats
               
            3. DETAILED FINDINGS:
               - Comprehensive presentation of research results
               - Supporting evidence and source citations
               - Multiple perspectives where relevant
               
            4. ANALYSIS AND INSIGHTS:
               - Deep analysis of patterns and trends
               - Critical evaluation of evidence
               - Novel insights and implications
               
            5. CONCLUSIONS AND RECOMMENDATIONS:
               - Clear, evidence-based conclusions
               - Practical recommendations where appropriate
               - Future research directions
               
            6. APPENDICES:
               - Source bibliography with quality ratings
               - Methodology details
               - Additional supporting information
            
            Use clear, professional language appropriate for an educated audience.
            Include proper citations and maintain academic rigor throughout.
            """,
            agent=self.agent,
            expected_output=f"Professional {output_format} with comprehensive research synthesis"
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        return crew.kickoff()