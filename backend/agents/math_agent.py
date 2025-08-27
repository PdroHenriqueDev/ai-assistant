import os
import re
import logging
from datetime import datetime
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class MathAgent:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        
    def is_math_query(self, text: str) -> bool:
        math_patterns = [
            r'\d+\s*[+\-*/÷×]\s*\d+',
            r'\d+\s*\^\s*\d+',
            r'\b(?:sqrt|sin|cos|tan|log|ln)\s*\(',
            r'\b(?:calculate|compute|solve|what is|how much)\b.*\d',
            r'\d+\s*%',
            r'\([^)]*\d[^)]*\)',
            r'\d+\s*(?:squared|cubed|to the power)',
            r'\bequation\b|\bformula\b',
        ]
        
        text_lower = text.lower()
        
        for pattern in math_patterns:
            if re.search(pattern, text_lower):
                return True
                
        return False
    
    def _evaluate_simple_math(self, expression: str) -> str:
        try:
            logger.info(f"Evaluating simple math for: '{expression}'")
            
            cleaned = re.sub(r'\b(?:what is|calculate|compute|solve|how much is|how much|how many)\b', '', expression.lower()).strip()
            cleaned = re.sub(r'\s*x\s*', ' * ', cleaned)
            cleaned = re.sub(r'[?!,;:]', '', cleaned)
            cleaned = re.sub(r'(?<!\d)\.(?!\d)', '', cleaned)
            cleaned = re.sub(r'[^0-9+\-*/().\s]', '', cleaned)
            cleaned = cleaned.strip()
            
            logger.info(f"Cleaned expression: '{cleaned}'")
            
            if not cleaned:
                logger.info("Expression is empty after cleaning")
                return None
                
            if re.match(r'^[0-9+\-*/().\s]+$', cleaned):
                cleaned = cleaned.replace('×', '*').replace('÷', '/')
                
                result = eval(cleaned)
                logger.info(f"Successfully evaluated: {cleaned} = {result}")
                return f"{cleaned} = {result}"
            else:
                logger.info(f"Expression doesn't match safety pattern: '{cleaned}'")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in simple math evaluation: {e}")
            return None
    
    def process_query(self, message: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            query = message.get("text", "") or message.get("message", "")
            print(f"DEBUG: Math agent processing query: '{query}'")
            
            simple_result = self._evaluate_simple_math(query)
            print(f"DEBUG: Simple math result: {simple_result}")
            if simple_result:
                execution_time = (datetime.now() - start_time).total_seconds()
                print(f"DEBUG: Returning simple math result: {simple_result}")
                return {
                    "text": simple_result,
                    "type": "math",
                    "timestamp": datetime.now().isoformat(),
                    "source": "simple_calculator",
                    "execution_time": execution_time,
                    "metadata": {
                        "query": query,
                        "method": "simple_evaluation"
                    }
                }
            
            if not self.client or not self.openai_api_key:
                return {
                    "text": "I can handle simple arithmetic like '3 + 5' or '10 * 2'. For complex math, OpenAI API access is needed.",
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "source": "system_error",
                    "execution_time": (datetime.now() - start_time).total_seconds()
                }
            
            system_prompt = """
You are a mathematical assistant. Your task is to:
1. Interpret and solve mathematical expressions and problems
2. Show step-by-step solutions when appropriate
3. Provide clear, accurate answers
4. Handle various formats: equations, word problems, calculations
5. Support basic arithmetic, algebra, geometry, and common mathematical functions

Examples:
- "What is 65 x 3.11?" → Calculate and show: 65 × 3.11 = 202.15
- "78 + 12" → 78 + 12 = 90
- "(42 * 2) / 6" → (42 × 2) ÷ 6 = 84 ÷ 6 = 14

Always show your work and provide the final answer clearly.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "text": answer,
                "type": "math",
                "timestamp": datetime.now().isoformat(),
                "source": "openai_gpt",
                "execution_time": execution_time,
                "metadata": {
                    "query": query,
                    "model_used": "gpt-3.5-turbo",
                    "tokens_used": response.usage.total_tokens if response.usage else None
                }
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in math agent: {str(e)}")
            
            return {
                "text": "Sorry, I encountered an error while processing your mathematical query. Please try rephrasing your question.",
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "source": "math_agent_error",
                "execution_time": execution_time,
                "error_details": str(e)
            }