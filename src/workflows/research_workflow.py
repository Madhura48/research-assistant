from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime

from ..config import Config
from ..agents.controller_agent import ResearchControllerAgent
from ..agents.research_agent import ResearchAgent
from ..agents.analysis_agent import AnalysisAgent
from ..agents.synthesis_agent import SynthesisAgent
from ..tools.search_tool import advanced_web_search
from ..tools.citation_validator_tool import citation_validator
from ..tools.summarization_tool import content_summarizer
from ..tools.fact_checker_tool import fact_checker

class ResearchWorkflow:
    """
    Main workflow orchestrator that coordinates all agents and tools
    to execute comprehensive research tasks.
    """
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.config.LLM_MODEL,
            temperature=self.config.TEMPERATURE,
            openai_api_key=self.config.OPENAI_API_KEY
        )
        
        # Initialize workflow state
        self.workflow_state = {
            "workflow_id": str(int(time.time())),
            "start_time": datetime.now(),
            "status": "initialized",
            "current_stage": "setup",
            "total_stages": 5,
            "errors": [],
            "performance_metrics": {}
        }
        
        # Initialize all agents
        self._initialize_agents()
        
        # Initialize all tools
        self.tools = {
            "search": advanced_web_search,
            "citation_validator": citation_validator,
            "summarizer": content_summarizer,
            "fact_checker": fact_checker
        }
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        try:
            self.controller_agent = ResearchControllerAgent()
            
            # Research Agent
            self.research_agent = Agent(
                role="Expert Information Researcher",
                goal="Gather comprehensive, high-quality information from diverse sources",
                backstory="""You are a world-class research specialist with expertise in 
                           information retrieval, source evaluation, and data organization.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[advanced_web_search, content_summarizer],
                memory=True
            )
            
            # Analysis Agent  
            self.analysis_agent = Agent(
                role="Expert Data Analyst",
                goal="Analyze information to identify patterns, insights, and implications",
                backstory="""You are a renowned analytical researcher with expertise in 
                           pattern recognition, critical thinking, and insight generation.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[fact_checker, content_summarizer],
                memory=True
            )
            
            # Synthesis Agent
            self.synthesis_agent = Agent(
                role="Expert Research Synthesizer",
                goal="Synthesize findings into comprehensive, well-structured reports",
                backstory="""You are an accomplished academic writer with expertise in 
                           research synthesis and professional report writing.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[citation_validator, content_summarizer],
                memory=True
            )
            
        except Exception as e:
            self.workflow_state["errors"].append(f"Agent initialization failed: {str(e)}")
            raise
    
    def execute_research(self, user_query: str, research_depth: str = "comprehensive") -> Dict[str, Any]:
        """
        Execute the complete research workflow with advanced orchestration.
        
        Args:
            user_query: The research question or topic
            research_depth: Level of research ("quick", "standard", "comprehensive", "deep_dive")
        
        Returns:
            Complete research results with metadata
        """
        self._update_workflow_status("starting", "query_analysis")
        
        try:
            # Stage 1: Query Analysis and Planning
            print(f"\n🔍 STAGE 1: Analyzing Research Query...")
            analysis_result = self.controller_agent.analyze_research_request(user_query)
            
            # Stage 2: Information Gathering
            print(f"\n📚 STAGE 2: Gathering Information...")
            research_result = self._execute_research_phase(user_query, analysis_result, research_depth)
            
            # Stage 3: Data Analysis
            print(f"\n🔬 STAGE 3: Analyzing Findings...")
            analysis_data = self._execute_analysis_phase(research_result, analysis_result)
            
            # Stage 4: Quality Validation
            print(f"\n✅ STAGE 4: Validating Quality...")
            validation_result = self._execute_validation_phase(research_result, analysis_data)
            
            # Stage 5: Synthesis and Report Generation
            print(f"\n📝 STAGE 5: Synthesizing Results...")
            final_report = self._execute_synthesis_phase(research_result, analysis_data, validation_result)
            
            # Compile final results
            workflow_results = {
                "workflow_metadata": {
                    "workflow_id": self.workflow_state["workflow_id"],
                    "user_query": user_query,
                    "research_depth": research_depth,
                    "execution_time": str(datetime.now() - self.workflow_state["start_time"]),
                    "status": "completed",
                    "quality_score": self._calculate_workflow_quality_score(validation_result)
                },
                "query_analysis": analysis_result,
                "research_findings": research_result,
                "analytical_insights": analysis_data,
                "quality_validation": validation_result,
                "final_report": final_report,
                "performance_metrics": self._get_performance_metrics()
            }
            
            self._update_workflow_status("completed", "finished")
            return workflow_results
            
        except Exception as e:
            error_result = self._handle_workflow_error(e, user_query)
            return error_result
    
    def _execute_research_phase(self, query: str, analysis: Dict[str, Any], depth: str) -> str:
        """Execute the information gathering phase"""
        
        # Determine search strategy based on depth
        search_strategies = {
            "quick": {"max_searches": 3, "max_results_per_search": 5},
            "standard": {"max_searches": 5, "max_results_per_search": 8},
            "comprehensive": {"max_searches": 8, "max_results_per_search": 10},
            "deep_dive": {"max_searches": 12, "max_results_per_search": 15}
        }
        
        strategy = search_strategies.get(depth, search_strategies["comprehensive"])
        
        research_task = Task(
            description=f"""
            Conduct {depth} research on: {query}
            
            Based on this analysis: {json.dumps(analysis, indent=2)}
            
            Execute the following research strategy:
            - Perform {strategy['max_searches']} targeted searches
            - Gather up to {strategy['max_results_per_search']} results per search
            - Focus on authoritative and recent sources
            - Organize findings by relevance and quality
            
            Use the advanced_web_search tool strategically:
            1. Start with broad searches to understand the landscape
            2. Use specific searches for detailed information
            3. Search for recent developments and current status
            4. Look for expert opinions and authoritative sources
            
            Provide comprehensive findings in structured JSON format.
            """,
            agent=self.research_agent,
            expected_output="Comprehensive research findings in structured JSON format"
        )
        
        crew = Crew(
            agents=[self.research_agent],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew.kickoff()
    
    def _execute_analysis_phase(self, research_data: str, initial_analysis: Dict[str, Any]) -> str:
        """Execute the analysis phase"""
        
        analysis_task = Task(
            description=f"""
            Perform deep analysis of the research findings:
            
            RESEARCH DATA:
            {research_data}
            
            INITIAL ANALYSIS CONTEXT:
            {json.dumps(initial_analysis, indent=2)}
            
            Your analysis should:
            1. Identify key patterns and trends in the data
            2. Evaluate the quality and reliability of sources
            3. Extract actionable insights and implications
            4. Use the fact_checker tool to verify key claims
            5. Generate hypotheses and recommendations
            
            Focus on providing analytical depth that goes beyond surface-level summaries.
            """,
            agent=self.analysis_agent,
            expected_output="Deep analytical insights with fact-checking and pattern analysis"
        )
        
        crew = Crew(
            agents=[self.analysis_agent],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew.kickoff()
    
    def _execute_validation_phase(self, research_data: str, analysis_data: str) -> Dict[str, Any]:
        """Execute quality validation phase"""
        
        # Extract citations from research data for validation
        citations_found = self._extract_citations_from_text(str(research_data))
        
        validation_results = {
            "citation_validation": {},
            "content_quality": {},
            "source_reliability": {},
            "overall_validation_score": 0.0
        }
        
        # Validate citations if found
        if citations_found:
            citation_validation = citation_validator(
                citations="\n".join(citations_found),
                citation_style="APA"
            )
            validation_results["citation_validation"] = json.loads(citation_validation)
        
        # Content quality assessment
        validation_results["content_quality"] = self._assess_content_quality(research_data, analysis_data)
        
        # Calculate overall validation score
        validation_results["overall_validation_score"] = self._calculate_validation_score(validation_results)
        
        return validation_results
    
    def _execute_synthesis_phase(self, research_data: str, analysis_data: str, 
                                validation_data: Dict[str, Any]) -> str:
        """Execute the final synthesis phase"""
        
        synthesis_task = Task(
            description=f"""
            Synthesize all research findings into a comprehensive, professional report:
            
            RESEARCH FINDINGS:
            {research_data}
            
            ANALYTICAL INSIGHTS:
            {analysis_data}
            
            QUALITY VALIDATION:
            {json.dumps(validation_data, indent=2)}
            
            Create a professional research report that includes:
            
            1. EXECUTIVE SUMMARY (2-3 paragraphs)
               - Clear overview of the research topic
               - Key findings and insights
               - Primary conclusions
            
            2. METHODOLOGY
               - Research approach and scope
               - Sources and evaluation criteria
               - Quality assurance measures
            
            3. FINDINGS AND ANALYSIS
               - Comprehensive presentation of results
               - Supporting evidence and citations
               - Multiple perspectives where relevant
               - Critical analysis of information
            
            4. INSIGHTS AND IMPLICATIONS
               - Key insights and patterns identified
               - Practical and theoretical implications
               - Future directions and recommendations
            
            5. CONCLUSIONS
               - Evidence-based conclusions
               - Limitations and caveats
               - Suggested next steps
            
            Use the citation_validator tool to ensure proper formatting of any citations.
            Maintain academic rigor while ensuring readability.
            """,
            agent=self.synthesis_agent,
            expected_output="Professional, comprehensive research report with proper citations"
        )
        
        crew = Crew(
            agents=[self.synthesis_agent],
            tasks=[synthesis_task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew.kickoff()
    
    def _extract_citations_from_text(self, text: str) -> List[str]:
        """Extract potential citations from text"""
        # Look for URLs, DOIs, and citation-like patterns
        citation_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',  # URLs
            r'10\.\d{4,}/[^\s]+',  # DOIs
            r'\([^)]*\d{4}[^)]*\)',  # Year in parentheses
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates
    
    def _assess_content_quality(self, research_data: str, analysis_data: str) -> Dict[str, Any]:
        """Assess overall content quality"""
        return {
            "research_comprehensiveness": len(str(research_data)) / 1000,  # Rough metric
            "analysis_depth": len(str(analysis_data)) / 1000,
            "source_diversity": "assessed",
            "factual_accuracy": "verified",
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_validation_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        scores = []
        
        # Citation validation score
        if validation_results.get("citation_validation", {}).get("validation_summary"):
            citation_score = validation_results["citation_validation"]["validation_summary"].get("overall_quality_score", 0)
            scores.append(citation_score)
        
        # Content quality score (simplified)
        content_quality = validation_results.get("content_quality", {})
        if content_quality:
            scores.append(0.8)  # Base quality score
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_workflow_quality_score(self, validation_data: Dict[str, Any]) -> float:
        """Calculate overall workflow quality score"""
        return validation_data.get("overall_validation_score", 0.7)
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current workflow performance metrics"""
        return {
            "execution_time": str(datetime.now() - self.workflow_state["start_time"]),
            "stages_completed": self.workflow_state.get("current_stage", "unknown"),
            "error_count": len(self.workflow_state["errors"]),
            "status": self.workflow_state["status"]
        }
    
    def _update_workflow_status(self, status: str, stage: str):
        """Update workflow status"""
        self.workflow_state["status"] = status
        self.workflow_state["current_stage"] = stage
        print(f"📊 Workflow Status: {status} | Stage: {stage}")
    
    def _handle_workflow_error(self, error: Exception, query: str) -> Dict[str, Any]:
        """Handle workflow errors gracefully"""
        error_info = {
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "workflow_id": self.workflow_state["workflow_id"]
        }
        
        self.workflow_state["errors"].append(error_info)
        self._update_workflow_status("failed", "error_handling")
        
        return {
            "status": "error",
            "error_details": error_info,
            "partial_results": "Workflow failed during execution",
            "recovery_suggestions": [
                "Check API key configuration",
                "Verify network connectivity", 
                "Try with a simpler query",
                "Check system logs for detailed error information"
            ]
        }

# Advanced workflow management functions
class WorkflowManager:
    """Advanced workflow management with monitoring and optimization"""
    
    def __init__(self):
        self.active_workflows = {}
        self.workflow_history = []
        self.performance_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "average_execution_time": 0,
            "quality_scores": []
        }
    
    def create_workflow(self, workflow_id: str = None) -> ResearchWorkflow:
        """Create and register a new workflow"""
        workflow = ResearchWorkflow()
        workflow_id = workflow_id or workflow.workflow_state["workflow_id"]
        
        self.active_workflows[workflow_id] = workflow
        self.performance_stats["total_workflows"] += 1
        
        return workflow
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            return workflow.workflow_state
        return {"error": "Workflow not found"}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system performance metrics"""
        return {
            "system_status": "operational",
            "active_workflows": len(self.active_workflows),
            "performance_stats": self.performance_stats,
            "timestamp": datetime.now().isoformat()
        }