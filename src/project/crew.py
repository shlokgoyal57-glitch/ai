"""
VERITAS Crew - Self-Auditing AI Assistant
"The First Chatbot That Checks Itself Before It Wrecks Itself"

4 Guardian Agents + Meta-Agent Orchestrator
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Import custom tools
from project.tools.pii_scanner import get_pii_scanner
from project.tools.bias_detector import get_bias_detector
from project.tools.safety_checker import get_safety_checker
from project.tools.source_tracer import get_source_tracer
from project.tools.trust_calculator import get_trust_calculator


@CrewBase
class VeritasCrew():
    """
    VERITAS - Verify, Explain, Regulate, Inspect, Trust, Audit, Secure
    
    A self-auditing AI crew where every response passes through 4 independent
    Guardian Agents before reaching the user.
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    # =====================================================
    # 🛡️ GUARDIAN AGENTS
    # =====================================================

    @agent
    def privus(self) -> Agent:
        """PRIVUS - Privacy Guardian (Data Protection Officer)"""
        return Agent(
            config=self.agents_config['privus'],
            tools=[get_pii_scanner()],
            verbose=True
        )

    @agent
    def aequitas(self) -> Agent:
        """AEQUITAS - Bias Detector (Fairness Auditor)"""
        return Agent(
            config=self.agents_config['aequitas'],
            tools=[get_bias_detector()],
            verbose=True
        )

    @agent
    def lumen(self) -> Agent:
        """LUMEN - Transparency Engine (Explainability Expert)"""
        return Agent(
            config=self.agents_config['lumen'],
            tools=[get_source_tracer()],
            verbose=True
        )

    @agent
    def ethos(self) -> Agent:
        """ETHOS - Ethical Oversight (Moral Compass)"""
        return Agent(
            config=self.agents_config['ethos'],
            tools=[get_safety_checker()],
            verbose=True
        )

    @agent
    def concordia(self) -> Agent:
        """CONCORDIA - Trust Orchestrator (Decision Maker)"""
        return Agent(
            config=self.agents_config['concordia'],
            tools=[get_trust_calculator()],
            verbose=True
        )

    # =====================================================
    # 📋 GUARDIAN TASKS (Sequential Pipeline)
    # =====================================================

    @task
    def privacy_scan(self) -> Task:
        """Task 1: Privacy scan by PRIVUS"""
        return Task(
            config=self.tasks_config['privacy_scan'],
        )

    @task
    def bias_analysis(self) -> Task:
        """Task 2: Bias analysis by AEQUITAS"""
        return Task(
            config=self.tasks_config['bias_analysis'],
        )

    @task
    def transparency_check(self) -> Task:
        """Task 3: Transparency check by LUMEN"""
        return Task(
            config=self.tasks_config['transparency_check'],
        )

    @task
    def ethics_evaluation(self) -> Task:
        """Task 4: Ethics evaluation by ETHOS"""
        return Task(
            config=self.tasks_config['ethics_evaluation'],
        )

    @task
    def orchestrate_trust(self) -> Task:
        """Task 5: Trust orchestration by CONCORDIA"""
        return Task(
            config=self.tasks_config['orchestrate_trust'],
            output_file='trust_certificate.md'
        )

    # =====================================================
    # 🚀 CREW ASSEMBLY
    # =====================================================

    @crew
    def crew(self) -> Crew:
        """Creates the VERITAS crew with sequential processing"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Pipeline: PRIVUS -> AEQUITAS -> LUMEN -> ETHOS -> CONCORDIA
            verbose=True,
        )
