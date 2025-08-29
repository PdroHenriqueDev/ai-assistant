import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.brokers.broker_system import BrokerSystem

class TestRouterAgentDecision:
    
    def setup_method(self):
        with patch('backend.brokers.broker_system.MathAgent'), \
             patch('backend.brokers.broker_system.KnowledgeAgent'):
            self.broker = BrokerSystem()
    
    def test_math_agent_selection_basic_arithmetic(self):
        test_cases = [
            "2 + 3",
            "10 - 5",
            "4 * 6",
            "15 / 3",
            "8 × 7",
            "20 ÷ 4"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
            assert decision_details["reasoning"] == "Mathematical patterns detected"
    
    def test_math_agent_selection_with_keywords(self):
        test_cases = [
            "calculate 5 + 3",
            "compute 10 * 2",
            "solve 15 - 7",
            "what is 9 + 1",
            "what's 12 / 4",
            "how much is 6 * 8",
            "how many is 20 - 5"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
    
    def test_math_agent_selection_advanced_functions(self):
        test_cases = [
            "square root of 16",
            "sqrt 25",
            "power of 2",
            "exponent calculation",
            "sin 30",
            "cos 45",
            "tan 60",
            "log 10",
            "ln 5"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
    
    def test_math_agent_selection_special_operators(self):
        test_cases = [
            "15%",
            "2^3",
            "(5 + 3)",
            "(10 - 2) * 4",
            "5 x 6",
            "7 × 8",
            "9 * 2"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
    
    def test_knowledge_agent_selection(self):
        test_cases = [
            "What are the card machine fees?",
            "Can I use my phone as a card machine?",
            "How do I set up my account?",
            "What is InfinitePay?",
            "Help me with payment processing",
            "Tell me about your services",
            "How to contact support?"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "knowledge", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) == 0
            assert decision_details["reasoning"] == "No mathematical patterns, routing to knowledge agent"
    
    def test_edge_cases(self):
        test_cases = [
            ("", "knowledge"),  # Empty string
            ("   ", "knowledge"),  # Whitespace only
            ("calculate", "knowledge"),  # Math keyword without numbers
            ("what is your name", "knowledge"),  # 'what is' without numbers
            ("123", "knowledge"),  # Numbers only without operators
            ("+ - * /", "knowledge"),  # Operators only without numbers
        ]
        
        for message, expected_agent in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == expected_agent, f"Failed for message: '{message}'"
    
    def test_case_insensitive_matching(self):
        test_cases = [
            "CALCULATE 5 + 3",
            "Compute 10 * 2",
            "SOLVE 15 - 7",
            "WHAT IS 9 + 1",
            "Square Root of 16",
            "SIN 30",
            "LOG 10"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
    
    def test_decision_details_structure(self):
        agent_type, decision_details = self.broker._determine_agent("2 + 2")
        
        # Check required fields
        assert "patterns_checked" in decision_details
        assert "matches_found" in decision_details
        assert "reasoning" in decision_details
        
        # Check data types
        assert isinstance(decision_details["patterns_checked"], int)
        assert isinstance(decision_details["matches_found"], list)
        assert isinstance(decision_details["reasoning"], str)
        
        # Check values
        assert decision_details["patterns_checked"] == 7  # Number of patterns in the code
        assert len(decision_details["matches_found"]) > 0
    
    def test_complex_mathematical_expressions(self):
        test_cases = [
            "How much is 65 x 3.11?",  # Example from requirements
            "Calculate (5 + 3) * (10 - 2)",
            "What's the square root of (16 + 9)?",
            "Solve 2^3 + 4^2",
            "Compute sin(30) + cos(60)"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
    
    def test_mixed_content_with_math(self):
        test_cases = [
            "I need to calculate 5 + 3 for my business",
            "Can you help me solve 10 * 2 please?",
            "The total should be 15 - 7, right?"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "math", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) > 0
    
    def test_numbers_without_operators(self):
        test_cases = [
            "I have 5 cards",
            "My phone number is 123456789",
            "The year is 2024",
            "I need 10 more days"
        ]
        
        for message in test_cases:
            agent_type, decision_details = self.broker._determine_agent(message)
            assert agent_type == "knowledge", f"Failed for message: {message}"
            assert len(decision_details["matches_found"]) == 0