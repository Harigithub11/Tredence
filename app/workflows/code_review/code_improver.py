"""AI-Powered Code Improvement Generator - Multi-Stage Pipeline

Uses LLM to generate improved code through a staged approach:
1. Fix individual issues (missing docstrings, type hints, naming, etc.)
2. Optimize algorithm if complexity is high
3. Apply PEP-8 formatting
4. Merge all improvements into final code
5. Generate alternative solutions
"""

from typing import Dict, List, Optional
import logging
from app.llm import GeminiClient

logger = logging.getLogger(__name__)


async def generate_improved_code(
    original_code: str,
    analysis_results: Dict,
    use_llm: bool = True
) -> Dict[str, any]:
    """
    Generate improved code using multi-stage LLM pipeline.

    Stage 1: Fix each identified issue separately
    Stage 2: Optimize algorithm if needed
    Stage 3: Merge and format (PEP-8)
    Stage 4: Generate alternatives

    Args:
        original_code: The original code to improve
        analysis_results: Results from code review analysis
        use_llm: Whether to use LLM for generation

    Returns:
        Dict containing:
        - improved_code: The optimized version
        - algorithm_name: Name of the algorithm/pattern used
        - improvements_applied: List of improvements made
        - alternatives: List of alternative solutions (if available)
    """
    print(f"\n\n{'='*60}")
    print(f"CODE IMPROVER CALLED: use_llm={use_llm}")
    print(f"{'='*60}\n")
    logger.info(f"=== CODE IMPROVER CALLED: use_llm={use_llm} ===")

    if not use_llm:
        print("LLM DISABLED - returning generic improvement")
        logger.info("LLM disabled by user, returning generic improvement")
        return _generate_generic_improvement(original_code, analysis_results)

    llm_client = GeminiClient()
    logger.info(f"LLM Client created: enabled={llm_client.enabled}")

    if not llm_client.enabled:
        logger.warning("LLM client not enabled, returning generic improvement")
        return _generate_generic_improvement(original_code, analysis_results)

    # Extract relevant info
    functions = analysis_results.get('functions', [])
    if not functions:
        return {"improved_code": original_code, "algorithm_name": None, "improvements_applied": [], "alternatives": []}

    func = functions[0]
    func_name = func.get('name', '')
    complexity_analysis = analysis_results.get('complexity_analysis', {}).get(func_name, {})
    issues = analysis_results.get('issues', [])
    suggestions = analysis_results.get('rule_suggestions', [])

    improvements_applied = []
    current_code = original_code
    algorithm_name = None

    logger.info(f"Starting multi-stage pipeline: {len(issues)} issues, avg_complexity={analysis_results.get('avg_complexity', 0)}")

    try:
        # ============================================================
        # STAGE 0: Logic Correctness Validation (NEW)
        # ============================================================
        logger.info("STAGE 0: Checking logic correctness")
        logic_errors = []
        edge_case_failures = []

        logic_check_prompt = f"""Analyze this code for LOGICAL CORRECTNESS only. Ignore style and formatting.

CODE:
```python
{original_code}
```

FUNCTION: {func_name}
COMPLEXITY: {complexity_analysis.get('time_complexity', 'Unknown')}

Answer these questions:
1. Does this algorithm produce CORRECT results?
2. Are there edge cases that will FAIL? (empty lists, negative numbers, single element, etc.)
3. Is the approach fundamentally FLAWED?
4. Are there unnecessary nested loops causing wrong logic?

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "is_correct": true or false,
  "logic_errors": ["error description 1", "error description 2"],
  "edge_case_failures": ["edge case 1", "edge case 2"]
}}
"""

        try:
            logic_response = await llm_client.generate_content(logic_check_prompt, temperature=0.1)
            # Parse JSON from response
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', logic_response, re.DOTALL)
            if json_match:
                logic_data = json.loads(json_match.group(0))
                is_correct = logic_data.get('is_correct', True)
                logic_errors = logic_data.get('logic_errors', [])
                edge_case_failures = logic_data.get('edge_case_failures', [])

                logger.info(f"Logic check: is_correct={is_correct}, errors={len(logic_errors)}, edge_cases={len(edge_case_failures)}")

                # Store for later use
                analysis_results['logic_check'] = {
                    'is_correct': is_correct,
                    'logic_errors': logic_errors,
                    'edge_case_failures': edge_case_failures
                }
        except Exception as e:
            logger.warning(f"Logic check failed: {e}")
            # Continue without logic check

        # ============================================================
        # STAGE 1: Fix Individual Issues
        # ============================================================
        logger.info(f"STAGE 1: Processing {len(issues)} issues")
        for issue in issues:
            issue_type = issue.get('type', '')
            issue_desc = issue.get('description', '')

            # Skip if not a fixable issue type
            if issue_type in ['high_complexity', 'performance_warning']:
                continue

            fix_prompt = f"""Fix ONLY this specific issue in the code. Return ONLY the fixed code, nothing else.

CURRENT CODE:
```python
{current_code}
```

ISSUE TO FIX: {issue_type}
DESCRIPTION: {issue_desc}

Rules:
- Fix ONLY this specific issue
- Keep all other code exactly the same
- Return ONLY the complete fixed code in a python code block
- No explanations, just the code"""

            try:
                fix_response = await llm_client.generate_content(fix_prompt)
                fixed_code = _extract_code_from_response(fix_response)
                if fixed_code and fixed_code != current_code:
                    current_code = fixed_code
                    improvements_applied.append(f"Fixed {issue_type}: {issue_desc}")
            except Exception as e:
                print(f"Failed to fix issue {issue_type}: {e}")
                continue

        # ============================================================
        # STAGE 2: Add Type Hints if Missing
        # ============================================================
        if not any('type hint' in imp.lower() for imp in improvements_applied):
            type_hint_prompt = f"""Add complete type hints to this code. Return ONLY the code with type hints added.

CODE:
```python
{current_code}
```

Rules:
- Add type hints to ALL parameters and return types
- Use proper typing imports (List, Dict, Optional, etc.)
- Keep logic exactly the same
- Return ONLY the code"""

            try:
                type_response = await llm_client.generate_content(type_hint_prompt)
                typed_code = _extract_code_from_response(type_response)
                if typed_code and typed_code != current_code:
                    current_code = typed_code
                    improvements_applied.append("Added complete type hints for parameters and return types")
            except Exception as e:
                print(f"Failed to add type hints: {e}")

        # ============================================================
        # STAGE 3: Optimize Algorithm if High Complexity
        # ============================================================
        avg_complexity = analysis_results.get('avg_complexity', 0)
        if avg_complexity > 5:
            optimize_prompt = f"""Optimize this code's algorithm to reduce time/space complexity.

CURRENT CODE:
```python
{current_code}
```

CURRENT COMPLEXITY:
- Time: {complexity_analysis.get('time_complexity', 'Unknown')}
- Space: {complexity_analysis.get('space_complexity', 'Unknown')}

Your task:
1. Identify the algorithm currently being used
2. Replace it with a more efficient algorithm
3. Return the optimized code with a comment explaining the algorithm

Format:
ALGORITHM_NAME: [name like "Two-Pass Hash Set", "Binary Search", etc.]

CODE:
```python
[optimized code]
```"""

            try:
                opt_response = await llm_client.generate_content(optimize_prompt)

                # Extract algorithm name
                if "ALGORITHM_NAME:" in opt_response:
                    algo_line = opt_response.split("ALGORITHM_NAME:")[1].split("\n")[0].strip()
                    algorithm_name = algo_line

                optimized_code = _extract_code_from_response(opt_response)
                if optimized_code and optimized_code != current_code:
                    current_code = optimized_code
                    improvements_applied.append(f"Optimized algorithm to {algorithm_name or 'more efficient approach'}")
                    improvements_applied.append(f"Reduced complexity from {complexity_analysis.get('time_complexity', 'O(n²)')} to better performance")
            except Exception as e:
                print(f"Failed to optimize algorithm: {e}")

        # ============================================================
        # STAGE 4: Add Professional Docstring
        # ============================================================
        if not any('docstring' in imp.lower() for imp in improvements_applied):
            docstring_prompt = f"""Add a comprehensive professional docstring to this code.

CODE:
```python
{current_code}
```

The docstring should include:
- Purpose and what the function does
- Algorithm used: {algorithm_name or 'current approach'}
- Parameters with types and descriptions
- Return value description
- Time complexity: {complexity_analysis.get('time_complexity', 'O(n)')}
- Space complexity: {complexity_analysis.get('space_complexity', 'O(1)')}
- Example usage

Return ONLY the code with the docstring added."""

            try:
                doc_response = await llm_client.generate_content(docstring_prompt)
                doc_code = _extract_code_from_response(doc_response)
                if doc_code and doc_code != current_code:
                    current_code = doc_code
                    improvements_applied.append("Added comprehensive docstring with complexity analysis and examples")
            except Exception as e:
                print(f"Failed to add docstring: {e}")

        # ============================================================
        # STAGE 5: Apply PEP-8 Formatting
        # ============================================================
        pep8_prompt = f"""Format this code to be PEP-8 compliant. Return ONLY the formatted code.

CODE:
```python
{current_code}
```

Apply:
- Proper spacing (2 lines between functions, 1 between methods)
- Correct indentation (4 spaces)
- Line length limits
- Import ordering
- Naming conventions

Return ONLY the formatted code."""

        try:
            pep8_response = await llm_client.generate_content(pep8_prompt)
            pep8_code = _extract_code_from_response(pep8_response)
            if pep8_code and pep8_code != current_code:
                current_code = pep8_code
                improvements_applied.append("Applied PEP-8 formatting standards")
        except Exception as e:
            print(f"Failed to apply PEP-8: {e}")

        # ============================================================
        # STAGE 6: Generate Alternative Solutions
        # ============================================================
        alternatives = []
        if avg_complexity > 3:
            alt_prompt = f"""Provide 3 completely different algorithmic approaches to solve the same problem as this code:

REFERENCE CODE:
```python
{original_code}
```

For each alternative:
- Use a DIFFERENT algorithm or data structure
- Provide working code
- Explain when it's better

Format EXACTLY as:

SOLUTION_1:
Name: [algorithm name]
Description: [brief explanation]
Code:
```python
[complete code]
```
Pros: [key advantages]

SOLUTION_2:
Name: [different algorithm]
Description: [explanation]
Code:
```python
[complete code]
```
Pros: [advantages]

SOLUTION_3:
Name: [another algorithm]
Description: [explanation]
Code:
```python
[complete code]
```
Pros: [advantages]"""

            try:
                alt_response = await llm_client.generate_content(alt_prompt)
                alternatives = _parse_alternatives_from_response(alt_response)
            except Exception as e:
                print(f"Failed to generate alternatives: {e}")

        return {
            "improved_code": current_code,
            "algorithm_name": algorithm_name,
            "improvements_applied": improvements_applied,
            "alternatives": alternatives
        }

    except Exception as e:
        print(f"LLM generation pipeline failed: {e}")
        return _generate_generic_improvement(original_code, analysis_results)


def _extract_code_from_response(response: str) -> Optional[str]:
    """Extract Python code from LLM response."""
    if not response:
        return None

    # Try to find code in markdown code block
    if "```python" in response:
        try:
            code = response.split("```python")[1].split("```")[0].strip()
            return code
        except:
            pass

    # Try generic code block
    if "```" in response:
        try:
            code = response.split("```")[1].split("```")[0].strip()
            # Remove language identifier if present
            if code.startswith("python\n"):
                code = code[7:]
            return code
        except:
            pass

    # If no code blocks, return the response as-is (might be just code)
    # But only if it looks like Python code
    if "def " in response or "class " in response or "import " in response:
        return response.strip()

    return None


def _parse_alternatives_from_response(response: str) -> List[Dict]:
    """Parse LLM response for alternative solutions (legacy format)."""
    alternatives = []

    for i in range(1, 4):  # Parse up to 3 solutions
        solution_key = f"SOLUTION_{i}:"
        if solution_key not in response:
            continue

        solution_text = response.split(solution_key)[1]
        if f"SOLUTION_{i+1}:" in solution_text:
            solution_text = solution_text.split(f"SOLUTION_{i+1}:")[0]

        alt = {
            "name": "",
            "description": "",
            "code": "",
            "pros": ""
        }

        # Extract name
        if "Name:" in solution_text:
            name_line = solution_text.split("Name:")[1].split("\n")[0].strip()
            alt["name"] = name_line

        # Extract description
        if "Description:" in solution_text:
            desc_line = solution_text.split("Description:")[1].split("\n")[0].strip()
            alt["description"] = desc_line

        # Extract code
        if "```python" in solution_text:
            code = solution_text.split("```python")[1].split("```")[0].strip()
            alt["code"] = code

        # Extract pros
        if "Pros:" in solution_text:
            pros_line = solution_text.split("Pros:")[1].split("\n")[0].strip()
            alt["pros"] = pros_line

        if alt["name"] and alt["code"]:  # Only add if we got both name and code
            alternatives.append(alt)

    return alternatives


def _generate_generic_improvement(original_code: str, analysis_results: Dict) -> Dict:
    """Generate a basic improvement without LLM."""
    functions = analysis_results.get('functions', [])
    if not functions:
        return {
            "improved_code": original_code,
            "algorithm_name": None,
            "improvements_applied": ["Original code preserved"],
            "alternatives": []
        }

    func = functions[0]
    func_name = func.get('name', 'function')
    args = func.get('args', [])
    complexity_analysis = analysis_results.get('complexity_analysis', {}).get(func_name, {})

    # Create basic improved version
    args_with_types = ', '.join([f"{arg}: Any" for arg in args])

    improved = f"""from typing import Any

def {func_name}({args_with_types}) -> Any:
    \"\"\"
    {func_name.replace('_', ' ').title()}.

    Time Complexity: {complexity_analysis.get('time_complexity', 'O(n)')}
    Space Complexity: {complexity_analysis.get('space_complexity', 'O(1)')}

    Args:
        {chr(10).join([f'{arg}: Parameter {arg}' for arg in args])}

    Returns:
        Result of the operation
    \"\"\"
{chr(10).join(['    ' + line for line in original_code.split(chr(10))[1:]])}
"""

    return {
        "improved_code": improved.strip(),
        "algorithm_name": "Standard Implementation",
        "improvements_applied": [
            "Added type hints",
            "Added comprehensive docstring",
            "Included complexity analysis"
        ],
        "alternatives": []
    }
