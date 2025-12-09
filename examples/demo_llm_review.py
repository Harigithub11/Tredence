"""Demo: LLM-Enhanced Code Review

Demonstrates the hybrid code review workflow with LLM (Gemini) integration.
Shows both rule-based and AI-generated suggestions.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from app.workflows.code_review import run_code_review


# Example: Code with multiple issues
PROBLEMATIC_CODE = """
def process_data(data, config, options, params, flags, mode):
    result = []
    for item in data:
        if mode == 'strict':
            if item > 0:
                if item % 2 == 0:
                    if item < 100:
                        if config.get('filter'):
                            result.append(item)
        elif mode == 'lenient':
            result.append(item)
    return result
"""


async def main():
    print("=" * 70)
    print("LLM-ENHANCED CODE REVIEW DEMO")
    print("=" * 70)
    print()
    print("Analyzing problematic code with hybrid approach:")
    print("  1. Rule-based static analysis")
    print("  2. AI-powered suggestions (Google Gemini)")
    print()
    print("=" * 70)
    print()

    # Run with LLM enabled
    result = await run_code_review(
        PROBLEMATIC_CODE,
        use_llm=True,
        quality_threshold=70.0
    )

    print("CODE ANALYSIS RESULTS")
    print("=" * 70)
    print()

    # Complexity Analysis
    if "complexity_analysis" in result.data:
        analysis = result.data["complexity_analysis"]
        for func_name, details in analysis.items():
            print(f"Function: {func_name}")
            print(f"  Time Complexity:  {details['time_complexity']}")
            print(f"  Space Complexity: {details['space_complexity']}")
            print(f"  Explanation: {details['explanation']}")
            print()

    # Issues Found
    print(f"Quality Score: {result.data.get('quality_score', 'N/A')}/100")
    print(f"Issues Found: {result.data.get('issue_count', 0)}")
    print()

    issues = result.data.get('issues', [])
    if issues:
        print("Detected Issues:")
        for issue in issues[:5]:  # Show first 5
            severity = issue['severity'].upper()
            issue_type = issue['type'].replace('_', ' ').title()
            print(f"  [{severity}] {issue_type}: {issue['message']}")
        print()

    # Rule-based Suggestions
    rule_suggestions = result.data.get('rule_suggestions', [])
    if rule_suggestions:
        print("RULE-BASED SUGGESTIONS")
        print("-" * 70)
        for i, suggestion in enumerate(rule_suggestions, 1):
            print(f"{i}. {suggestion}")
        print()

    # LLM-Enhanced Suggestions
    llm_suggestions = result.data.get('llm_suggestions', [])
    if llm_suggestions:
        print("AI-POWERED SUGGESTIONS (Gemini)")
        print("-" * 70)
        for i, suggestion in enumerate(llm_suggestions, 1):
            print(f"{i}. {suggestion}")
        print()

    # Full LLM Analysis
    llm_analysis = result.data.get('llm_analysis', '')
    if llm_analysis:
        print("DETAILED AI ANALYSIS")
        print("-" * 70)
        print(llm_analysis)
        print()

    # Additional LLM insights
    if 'llm_critical_issues' in result.data:
        critical = result.data['llm_critical_issues']
        if critical:
            print("Critical Issues (AI-detected):")
            for issue in critical:
                print(f"  - {issue}")
            print()

    if 'llm_quality_tips' in result.data:
        tips = result.data['llm_quality_tips']
        if tips:
            print("Code Quality Tips (AI):")
            for tip in tips[:3]:  # Show first 3
                print(f"  - {tip}")
            print()

    if 'llm_best_practices' in result.data:
        practices = result.data['llm_best_practices']
        if practices:
            print("Best Practices (AI):")
            for practice in practices[:3]:  # Show first 3
                print(f"  - {practice}")
            print()

    print("=" * 70)
    print("Analysis Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
