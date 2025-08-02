from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime
from ..config import Config

class ResearchControllerAgent:
    """
    Advanced Controller Agent that orchestrates the entire research workflow.
    Implements sophisticated decision-making, error handling, and task delegation.
    """
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.config.LLM_MODEL,
            temperature=self.config.TEMPERATURE,
            max_tokens=self.config.MAX_TOKENS,
            openai_api_key=self.config.OPENAI_API_KEY
        )
        
        # Initialize state tracking
        self.session_state = {
            "session_id": str(int(time.time())),
            "start_time": datetime.now(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "context_memory": [],
            "agent_performance": {}
        }
        
        # Create the controller agent
        self.controller = Agent(
            role="Research Coordinator and Task Orchestrator",
            goal="""Orchestrate a comprehensive research process by analyzing user queries, 
                    breaking them into subtasks, delegating to specialized agents, and 
                    synthesizing results into high-quality research outputs.""",
            backstory="""You are an expert research coordinator with deep knowledge of 
                        information science, academic research methodologies, and AI system 
                        orchestration. You excel at breaking complex research questions into 
                        manageable subtasks, selecting the right specialists for each job, 
                        and ensuring quality control throughout the process.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            max_iter=5,
            memory=True
        )
    
    def analyze_research_request(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze the user's research request and create a comprehensive execution plan.
        """
        analysis_task = Task(
            description=f"""
            Analyze this research request and create a detailed execution plan:
            
            USER QUERY: {user_query}
            
            Your analysis should include:
            1. Research scope and complexity assessment
            2. Key topics and subtopics to investigate
            3. Required research methodologies
            4. Expected challenges and mitigation strategies
            5. Quality criteria and success metrics
            6. Estimated timeline and resource requirements
            
            Provide your analysis in JSON format with clear structure.
            """,
            agent=self.controller,
            expected_output="Detailed JSON analysis of the research request with execution plan"
        )
        
        try:
            crew = Crew(
                agents=[self.controller],
                tasks=[analysis_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse and validate the result
            try:
                analysis = json.loads(str(result))
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = {
                    "query": user_query,
                    "complexity": "medium",
                    "topics": [user_query],
                    "methodology": ["web_search", "analysis", "synthesis"],
                    "challenges": ["information_quality", "source_reliability"],
                    "success_metrics": ["relevance", "accuracy", "completeness"]
                }
            
            self._update_session_state("analysis_completed", analysis)
            return analysis
            
        except Exception as e:
            error_analysis = {
                "error": str(e),
                "query": user_query,
                "fallback_plan": self._create_fallback_plan(user_query)
            }
            self._update_session_state("analysis_failed", error_analysis)
            return error_analysis
    
    def create_task_delegation_plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create a detailed task delegation plan based on the research analysis.
        """
        planning_task = Task(
            description=f"""
            Based on this research analysis, create a detailed task delegation plan:
            
            ANALYSIS: {json.dumps(analysis, indent=2)}
            
            Create a delegation plan that includes:
            1. Specific tasks for each specialized agent
            2. Task dependencies and execution order
            3. Quality checkpoints and validation steps
            4. Error handling and fallback procedures
            5. Resource allocation and time estimates
            
            Format as JSON with clear task definitions.
            """,
            agent=self.controller,
            expected_output="Detailed JSON task delegation plan with agent assignments"
        )
        
        try:
            crew = Crew(
                agents=[self.controller],
                tasks=[planning_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            try:
                delegation_plan = json.loads(str(result))
            except json.JSONDecodeError:
                # Create fallback delegation plan
                delegation_plan = self._create_fallback_delegation_plan(analysis)
            
            self._update_session_state("delegation_planned", delegation_plan)
            return delegation_plan.get("tasks", [])
            
        except Exception as e:
            fallback_tasks = self._create_fallback_delegation_plan(analysis)
            self._update_session_state("delegation_failed", {"error": str(e)})
            return fallback_tasks.get("tasks", [])
    
    def _create_fallback_plan(self, query: str) -> Dict[str, Any]:
        """Create a simple fallback plan when analysis fails"""
        return {
            "query": query,
            "complexity": "medium",
            "approach": "standard_research",
            "steps": ["search", "analyze", "synthesize"],
            "agents_needed": ["research_agent", "analysis_agent", "synthesis_agent"]
        }
    
    def _create_fallback_delegation_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback delegation plan"""
        return {
            "tasks": [
                {
                    "id": "task_1",
                    "type": "information_gathering",
                    "agent": "research_agent",
                    "priority": "high",
                    "description": f"Search for information about: {analysis.get('query', 'research topic')}"
                },
                {
                    "id": "task_2", 
                    "type": "analysis",
                    "agent": "analysis_agent",
                    "priority": "medium",
                    "description": "Analyze gathered information for key insights"
                },
                {
                    "id": "task_3",
                    "type": "synthesis",
                    "agent": "synthesis_agent", 
                    "priority": "high",
                    "description": "Synthesize findings into comprehensive report"
                }
            ]
        }
    
    def _update_session_state(self, event: str, data: Any):
        """Update session state with new information"""
        self.session_state["context_memory"].append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        })
        
        # Keep memory within limits
        if len(self.session_state["context_memory"]) > self.config.MEMORY_SIZE:
            self.session_state["context_memory"] = self.session_state["context_memory"][-self.config.MEMORY_SIZE:]
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get current session performance metrics"""
        return {
            "session_id": self.session_state["session_id"],
            "duration": str(datetime.now() - self.session_state["start_time"]),
            "tasks_completed": self.session_state["completed_tasks"],
            "tasks_failed": self.session_state["failed_tasks"],
            "success_rate": self.session_state["completed_tasks"] / max(self.session_state["total_tasks"], 1),
            "memory_usage": len(self.session_state["context_memory"])
        }