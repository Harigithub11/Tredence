"""Gemini LLM Client

Provides interface to Google's Gemini API for code analysis.
"""

from typing import Dict, Any, List, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. LLM features disabled.")


CODE_REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following Python code and provide specific, actionable improvement suggestions.

**Code:**
```python
{code}
```

**Detected Issues:**
{issues}

**Complexity Metrics:**
{complexity}

Please provide:
1. **Critical Issues**: Security, bugs, or logical errors
2. **Code Quality**: Readability, maintainability improvements
3. **Best Practices**: Pythonic patterns, design principles
4. **Refactoring Ideas**: Structural improvements

Keep suggestions concise and actionable. Focus on the most impactful changes.
"""


class GeminiClient:
    """Client for interacting with Google's Gemini API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.enabled = GEMINI_AVAILABLE and self.api_key is not None

        if self.enabled:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Generate content using Gemini.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum output tokens

        Returns:
            Generated text or None if disabled/error
        """
        if not self.enabled:
            logger.warning("Gemini client not enabled")
            return None

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None


async def analyze_code(
    code: str,
    issues: List[Dict],
    complexity: Dict[str, int],
    client: Optional[GeminiClient] = None
) -> Dict[str, Any]:
    """
    Use Gemini to analyze code and generate suggestions.

    Args:
        code: Python code to analyze
        issues: Detected issues from static analysis
        complexity: Complexity metrics by function
        client: GeminiClient instance (creates new if None)

    Returns:
        Dictionary containing:
        - llm_suggestions: List of refactoring suggestions
        - critical_issues: List of critical issues found
        - quality_tips: Code quality improvements
        - best_practices: Best practice recommendations
        - raw_analysis: Full LLM response
        - error: Error message if analysis failed
    """
    if not settings.ENABLE_LLM or not settings.GEMINI_API_KEY:
        return {
            "llm_suggestions": [],
            "critical_issues": [],
            "quality_tips": [],
            "best_practices": [],
            "analysis": "LLM analysis disabled"
        }

    # Create client if not provided
    if client is None:
        client = GeminiClient()

    if not client.enabled:
        return {
            "llm_suggestions": [],
            "critical_issues": [],
            "quality_tips": [],
            "best_practices": [],
            "error": "Gemini client not available"
        }

    try:
        # Format issues
        issues_str = "\n".join([
            f"- [{i['severity'].upper()}] {i['message']}"
            for i in issues[:10]  # Limit to top 10
        ])

        # Format complexity
        complexity_str = "\n".join([
            f"- {func}: complexity {comp}"
            for func, comp in sorted(
                complexity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # Top 5 most complex
        ])

        # Build prompt
        prompt = CODE_REVIEW_PROMPT.format(
            code=code[:2000],  # Limit code length
            issues=issues_str or "No issues detected",
            complexity=complexity_str or "No complexity data"
        )

        # Call Gemini
        response_text = await client.generate_content(prompt)

        if not response_text:
            return {
                "llm_suggestions": [],
                "error": "Failed to get response from Gemini"
            }

        # Parse response sections
        sections = _parse_sections(response_text)

        return {
            "llm_suggestions": sections.get("refactoring ideas", []),
            "critical_issues": sections.get("critical issues", []),
            "quality_tips": sections.get("code quality", []),
            "best_practices": sections.get("best practices", []),
            "raw_analysis": response_text
        }

    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        return {
            "llm_suggestions": [],
            "error": str(e)
        }


def _parse_sections(text: str) -> Dict[str, List[str]]:
    """
    Parse markdown sections from LLM response.

    Args:
        text: LLM response text

    Returns:
        Dictionary mapping section names to content lists
    """
    sections = {}
    current_section = None

    for line in text.split('\n'):
        line = line.strip()

        # Check for section headers (markdown format)
        if line.startswith('**') and line.endswith('**'):
            # Extract section name
            section_name = line.strip('*').strip(':').lower()
            current_section = section_name
            sections[current_section] = []
        elif current_section and line:
            # Add content to current section
            sections[current_section].append(line)

    return sections
