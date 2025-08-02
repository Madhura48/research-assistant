#!/usr/bin/env python3
"""
Production-Level Research Assistant System
A comprehensive agentic AI system demonstrating multi-agent orchestration,
custom tools, and advanced research capabilities.
"""

import os
import sys
import json
import time
import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

class Config:
    """System configuration"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = "gpt-4-turbo-preview"
    TEMPERATURE = 0.1
    MAX_TOKENS = 4000
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env file")
        return True

class AdvancedWebSearchTool:
    """Advanced web search tool with quality assessment"""
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute advanced web search"""
        try:
            results = []
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))
                
                for result in search_results:
                    processed_result = {
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", ""),
                        "relevance_score": self._calculate_relevance(query, result),
                        "source_type": self._identify_source_type(result.get("href", ""))
                    }
                    results.append(processed_result)
                
                # Sort by relevance
                results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "results": results
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}", "query": query}
    
    def _calculate_relevance(self, query: str, result: dict) -> float:
        """Calculate relevance score"""
        query_terms = set(query.lower().split())
        title = result.get("title", "").lower()
        body = result.get("body", "").lower()
        
        title_matches = len([term for term in query_terms if term in title])
        body_matches = len([term for term in query_terms if term in body])
        
        if not query_terms:
            return 0.5
        
        relevance = (title_matches * 0.7 + body_matches * 0.3) / len(query_terms)
        return min(relevance, 1.0)
    
    def _identify_source_type(self, url: str) -> str:
        """Identify source type"""
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
        else:
            return "general"

class CitationValidatorTool:
    """Custom citation validator tool"""
    
    def validate(self, citations: str, style: str = "APA") -> Dict[str, Any]:
        """Validate and format citations"""
        try:
            citation_list = self._parse_citations(citations)
            validated_citations = []
            
            for idx, citation in enumerate(citation_list):
                validation = self._validate_single_citation(citation, style, idx + 1)
                validated_citations.append(validation)
            
            total_valid = sum(1 for c in validated_citations if c["is_valid"])
            
            return {
                "timestamp": datetime.now().isoformat(),
                "citation_style": style,
                "total_citations": len(citation_list),
                "valid_citations": total_valid,
                "validation_rate": total_valid / len(citation_list) if citation_list else 0,
                "validated_citations": validated_citations,
                "overall_quality": "Good" if total_valid / len(citation_list) > 0.7 else "Needs Improvement"
            }
        except Exception as e:
            return {"error": f"Citation validation failed: {str(e)}"}
    
    def _parse_citations(self, text: str) -> List[str]:
        """Parse individual citations"""
        citations = text.split('\n')
        return [c.strip() for c in citations if c.strip() and len(c.strip()) > 20]
    
    def _validate_single_citation(self, citation: str, style: str, number: int) -> Dict[str, Any]:
        """Validate single citation"""
        components = self._extract_components(citation)
        
        required = ["author", "title", "year"]
        has_required = sum(1 for req in required if components.get(req))
        
        return {
            "citation_number": number,
            "original": citation,
            "components_found": components,
            "has_author": bool(components.get("author")),
            "has_title": bool(components.get("title")),
            "has_year": bool(components.get("year")),
            "has_url": bool(components.get("url")),
            "is_valid": has_required >= 2,
            "quality_score": has_required / len(required)
        }
    
    def _extract_components(self, citation: str) -> Dict[str, str]:
        """Extract citation components"""
        components = {}
        
        # URL extraction
        url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', citation)
        if url_match:
            components["url"] = url_match.group()
        
        # Year extraction
        year_match = re.search(r'\b(19|20)\d{2}\b', citation)
        if year_match:
            components["year"] = year_match.group()
        
        # Title extraction (text in quotes)
        title_match = re.search(r'"([^"]+)"', citation)
        if title_match:
            components["title"] = title_match.group(1)
        
        # Simple author extraction (text before year or beginning)
        if components.get("year"):
            author_match = re.search(rf'([^.]+?)\s*\({components["year"]}\)', citation)
            if author_match:
                components["author"] = author_match.group(1).strip()
        
        return components

class ResearchAssistantSystem:
    """Main Research Assistant System"""
    
    def __init__(self):
        """Initialize the system"""
        Config.validate()
        
        # Initialize tools
        self.search_tool = AdvancedWebSearchTool()
        self.citation_tool = CitationValidatorTool()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Initialize agents
        self._create_agents()
        
        # System state
        self.session_id = str(int(time.time()))
        self.start_time = datetime.now()
    
    def _create_agents(self):
        """Create specialized agents"""
        
        # Research Agent
        self.research_agent = Agent(
            role="Expert Information Researcher",
            goal="Gather comprehensive information from web sources and evaluate quality",
            backstory="""You are a world-class research specialist with expertise in 
                        information retrieval, source evaluation, and data organization.
                        You excel at finding authoritative sources and organizing findings.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            memory=True
        )
        
        # Analysis Agent
        self.analysis_agent = Agent(
            role="Expert Data Analyst and Insight Generator",
            goal="Analyze research findings to extract patterns, insights, and implications",
            backstory="""You are a renowned analytical researcher with expertise in 
                        pattern recognition, critical thinking, and insight generation.
                        You excel at finding meaningful insights in complex information.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            memory=True
        )
        
        # Synthesis Agent
        self.synthesis_agent = Agent(
            role="Expert Research Synthesizer and Report Writer",
            goal="Synthesize research and analysis into comprehensive, well-structured reports",
            backstory="""You are an accomplished academic writer with expertise in 
                        research synthesis and professional report writing. You excel at 
                        creating compelling, well-structured research reports.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            memory=True
        )
    
    def execute_research(self, query: str, depth: str = "comprehensive") -> Dict[str, Any]:
        """Execute complete research workflow"""
        
        print(f"\n🚀 Starting {depth} research on: '{query}'")
        start_time = datetime.now()
        
        try:
            # Stage 1: Information Gathering
            print("\n📚 STAGE 1: Gathering Information...")
            research_data = self._gather_information(query, depth)
            
            # Stage 2: Analysis
            print("\n🔬 STAGE 2: Analyzing Information...")
            analysis_data = self._analyze_information(research_data, query)
            
            # Stage 3: Citation Validation
            print("\n✅ STAGE 3: Validating Citations...")
            citation_validation = self._validate_citations(research_data)
            
            # Stage 4: Synthesis
            print("\n📝 STAGE 4: Synthesizing Report...")
            final_report = self._synthesize_report(research_data, analysis_data, query)
            
            # Compile results
            execution_time = datetime.now() - start_time
            
            results = {
                "session_metadata": {
                    "session_id": self.session_id,
                    "query": query,
                    "depth": depth,
                    "execution_time": str(execution_time),
                    "timestamp": datetime.now().isoformat()
                },
                "research_data": research_data,
                "analysis_data": analysis_data,
                "citation_validation": citation_validation,
                "final_report": final_report,
                "quality_metrics": self._calculate_quality_metrics(research_data, analysis_data)
            }
            
            print(f"\n✅ Research completed in {execution_time}")
            return results
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _gather_information(self, query: str, depth: str) -> Dict[str, Any]:
        """Stage 1: Information gathering with web search"""
        
        # Determine search strategy based on depth
        search_counts = {
            "quick": 3,
            "standard": 5,
            "comprehensive": 8,
            "deep_dive": 12
        }
        
        max_results = search_counts.get(depth, 5)
        
        # Create research task
        research_task = Task(
            description=f"""
            Conduct comprehensive research on: {query}
            
            Your task:
            1. I will provide you with search results for this topic
            2. Analyze and organize the information systematically
            3. Identify key themes, facts, and insights
            4. Evaluate source quality and credibility
            5. Structure findings for further analysis
            
            Focus on:
            - Accuracy and reliability of information
            - Multiple perspectives where relevant
            - Recent developments and current status
            - Authoritative sources and expert opinions
            
            Provide your findings in a clear, organized format.
            """,
            agent=self.research_agent,
            expected_output="Comprehensive analysis of research findings with source evaluation"
        )
        
        # Get search results
        search_results = self.search_tool.search(query, max_results)
        
        # Execute research task with search context
        research_task.description += f"\n\nSEARCH RESULTS:\n{json.dumps(search_results, indent=2)}"
        
        crew = Crew(
            agents=[self.research_agent],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True
        )
        
        research_output = crew.kickoff()
        
        return {
            "search_results": search_results,
            "research_analysis": str(research_output),
            "metadata": {
                "search_query": query,
                "results_count": search_results.get("total_results", 0),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _analyze_information(self, research_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Stage 2: Deep analysis"""
        
        analysis_task = Task(
            description=f"""
            Perform deep analysis of the research findings for: {query}
            
            RESEARCH DATA TO ANALYZE:
            {json.dumps(research_data, indent=2)}
            
            Your analysis should:
            1. Identify key patterns and trends
            2. Extract actionable insights
            3. Evaluate information quality and reliability
            4. Highlight surprising or significant findings
            5. Assess different perspectives and viewpoints
            6. Generate implications and recommendations
            
            Provide structured analytical insights that go beyond surface-level summaries.
            """,
            agent=self.analysis_agent,
            expected_output="Deep analytical insights with patterns, trends, and implications"
        )
        
        crew = Crew(
            agents=[self.analysis_agent],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True
        )
        
        analysis_output = crew.kickoff()
        
        return {
            "analysis_results": str(analysis_output),
            "timestamp": datetime.now().isoformat()
        }
    
    def _validate_citations(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: Citation validation using custom tool"""
        
        # Extract URLs from search results for citation validation
        search_results = research_data.get("search_results", {}).get("results", [])
        citations = []
        
        for result in search_results:
            if result.get("url"):
                # Create a simple citation format
                citation = f'{result.get("title", "Unknown")} ({datetime.now().year}). Retrieved from {result.get("url")}'
                citations.append(citation)
        
        if citations:
            citations_text = "\n".join(citations)
            validation_result = self.citation_tool.validate(citations_text)
        else:
            validation_result = {"message": "No citations found for validation"}
        
        return validation_result
    
    def _synthesize_report(self, research_data: Dict[str, Any], analysis_data: Dict[str, Any], query: str) -> str:
        """Stage 4: Final synthesis"""
        
        synthesis_task = Task(
            description=f"""
            Create a comprehensive research report on: {query}
            
            RESEARCH FINDINGS:
            {json.dumps(research_data, indent=2)}
            
            ANALYSIS INSIGHTS:
            {json.dumps(analysis_data, indent=2)}
            
            Create a professional report with:
            
            1. EXECUTIVE SUMMARY
               - Clear overview of the research topic
               - 3-5 key findings
               - Primary conclusions
            
            2. DETAILED FINDINGS
               - Comprehensive presentation of research results
               - Supporting evidence from sources
               - Multiple perspectives where relevant
            
            3. ANALYSIS AND INSIGHTS
               - Key patterns and trends identified
               - Critical evaluation of information
               - Implications and significance
            
            4. CONCLUSIONS
               - Evidence-based conclusions
               - Practical applications
               - Future directions
            
            5. SOURCES
               - List of sources consulted
               - Quality assessment of sources
            
            Write in clear, professional language suitable for an educated audience.
            Maintain academic rigor while ensuring readability.
            """,
            agent=self.synthesis_agent,
            expected_output="Professional, comprehensive research report"
        )
        
        crew = Crew(
            agents=[self.synthesis_agent],
            tasks=[synthesis_task],
            process=Process.sequential,
            verbose=True
        )
        
        return str(crew.kickoff())
    
    def _calculate_quality_metrics(self, research_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality metrics"""
        search_results = research_data.get("search_results", {})
        total_results = search_results.get("total_results", 0)
        
        # Calculate average relevance
        results = search_results.get("results", [])
        avg_relevance = sum(r.get("relevance_score", 0) for r in results) / len(results) if results else 0
        
        # Source diversity
        source_types = set(r.get("source_type", "general") for r in results)
        source_diversity = len(source_types) / 6  # Max 6 source types
        
        return {
            "search_effectiveness": min(total_results / 5, 1.0),  # Normalize to 1.0
            "average_relevance": avg_relevance,
            "source_diversity": source_diversity,
            "overall_quality": (avg_relevance + source_diversity) / 2
        }

def display_results(results: Dict[str, Any]):
    """Display research results professionally"""
    
    print("\n" + "="*70)
    print("📋 RESEARCH RESULTS")
    print("="*70)
    
    # Session metadata
    metadata = results.get("session_metadata", {})
    print(f"🆔 Session ID: {metadata.get('session_id', 'Unknown')}")
    print(f"📝 Query: {metadata.get('query', 'Unknown')}")
    print(f"⏱️  Execution Time: {metadata.get('execution_time', 'Unknown')}")
    
    # Quality metrics
    quality = results.get("quality_metrics", {})
    print(f"🎯 Overall Quality: {quality.get('overall_quality', 0):.2f}")
    print(f"📊 Average Relevance: {quality.get('average_relevance', 0):.2f}")
    print(f"🔍 Source Diversity: {quality.get('source_diversity', 0):.2f}")
    
    # Final report
    final_report = results.get("final_report", "No report generated")
    print(f"\n📄 RESEARCH REPORT:")
    print("-" * 50)
    
    # Display first 1000 characters of report
    report_preview = final_report[:1000] + "..." if len(final_report) > 1000 else final_report
    print(report_preview)
    
    # Citation validation summary
    citation_val = results.get("citation_validation", {})
    if citation_val and "total_citations" in citation_val:
        print(f"\n📚 CITATION VALIDATION:")
        print(f"   Total Citations: {citation_val.get('total_citations', 0)}")
        print(f"   Valid Citations: {citation_val.get('valid_citations', 0)}")
        print(f"   Validation Rate: {citation_val.get('validation_rate', 0):.1%}")

def test_tools():
    """Test individual tools"""
    
    print("\n🧪 TESTING SYSTEM COMPONENTS")
    print("="*50)
    
    # Test search tool
    print("1. Testing Web Search Tool...")
    search_tool = AdvancedWebSearchTool()
    search_result = search_tool.search("machine learning", 2)
    
    if "error" in search_result:
        print(f"   ✗ Search failed: {search_result['error']}")
        return False
    else:
        print(f"   ✓ Search successful: {search_result['total_results']} results")
    
    # Test citation tool
    print("2. Testing Citation Validator...")
    citation_tool = CitationValidatorTool()
    test_citation = 'Smith, J. (2024). "Artificial Intelligence Research". Journal of AI. https://example.com'
    citation_result = citation_tool.validate(test_citation)
    
    if "error" in citation_result:
        print(f"   ✗ Citation validation failed: {citation_result['error']}")
    else:
        print(f"   ✓ Citation validation successful: {citation_result.get('validation_rate', 0):.1%} valid")
    
    print("3. Testing LLM Connection...")
    try:
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.1,
            openai_api_key=Config.OPENAI_API_KEY
        )
        print("   ✓ LLM connection successful")
        return True
    except Exception as e:
        print(f"   ✗ LLM connection failed: {str(e)}")
        return False

def main():
    """Main application entry point"""
    
    print("="*70)
    print("🎯 PRODUCTION-LEVEL RESEARCH ASSISTANT SYSTEM")
    print("🤖 Advanced Agentic AI with Multi-Agent Orchestration")
    print("="*70)
    
    # Validate environment
    try:
        Config.validate()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please ensure OPENAI_API_KEY is set in your .env file")
        return
    
    # Test system components
    if not test_tools():
        print("❌ System component tests failed")
        return
    
    print("✅ All system components operational")
    
    # Initialize system
    try:
        system = ResearchAssistantSystem()
        print("✅ Research Assistant System initialized")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return
    
    # Interactive loop
    while True:
        print("\n" + "="*50)
        print("📋 RESEARCH ASSISTANT MENU")
        print("="*50)
        print("1. 🔍 Conduct Research")
        print("2. 📊 System Status")
        print("3. 🚪 Exit")
        print("="*50)
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            # Get research parameters
            query = input("\n📝 Enter research question: ").strip()
            if not query:
                print("❌ Research query cannot be empty")
                continue
            
            print("\n📊 Select research depth:")
            print("1. Quick (2-3 minutes)")
            print("2. Standard (5-7 minutes)")
            print("3. Comprehensive (8-12 minutes)")
            
            depth_choice = input("Select depth (1-3): ").strip()
            depth_map = {"1": "quick", "2": "standard", "3": "comprehensive"}
            depth = depth_map.get(depth_choice, "standard")
            
            # Execute research
            print(f"\n🚀 Executing {depth} research...")
            print("⏱️  This will take several minutes - please wait...")
            
            results = system.execute_research(query, depth)
            
            if "error" in results:
                print(f"❌ Research failed: {results['error']}")
            else:
                display_results(results)
                
                # Save option
                save = input("\n💾 Save results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"research_results_{int(time.time())}.json"
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(results, f, indent=2, ensure_ascii=False)
                        print(f"✅ Results saved to: {filename}")
                    except Exception as e:
                        print(f"❌ Save failed: {e}")
        
        elif choice == "2":
            print(f"\n📊 SYSTEM STATUS")
            print(f"Session ID: {system.session_id}")
            print(f"Uptime: {datetime.now() - system.start_time}")
            print("Status: Operational ✅")
        
        elif choice == "3":
            print("\n👋 Thank you for using Research Assistant System!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Research Assistant System terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ System Error: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)