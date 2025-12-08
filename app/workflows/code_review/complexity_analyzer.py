"""Complexity Analyzer

Analyzes time and space complexity of Python code using AST analysis
and pattern recognition.
"""

import ast
from typing import Dict, List, Tuple, Optional


class ComplexityAnalyzer:
    """Analyzes time and space complexity of Python functions"""

    def __init__(self):
        self.loop_patterns = {}
        self.recursion_depth = 0

    def analyze_function(self, func_node: ast.FunctionDef, code: str) -> Dict:
        """
        Analyze time and space complexity of a function.

        Returns:
            Dictionary with time_complexity, space_complexity, and explanation
        """
        # Reset state
        self.recursion_depth = 0

        # Analyze time complexity
        time_complexity = self._analyze_time_complexity(func_node)

        # Analyze space complexity
        space_complexity = self._analyze_space_complexity(func_node)

        # Generate explanation
        explanation = self._generate_explanation(func_node, time_complexity, space_complexity)

        return {
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "explanation": explanation
        }

    def _analyze_time_complexity(self, node: ast.AST) -> str:
        """
        Determine time complexity by analyzing loops and recursion.

        Patterns:
        - Single loop: O(n)
        - Nested loops: O(n^2), O(n^3), etc.
        - Binary search pattern: O(log n)
        - Two pointer pattern: O(n) even with nested loops
        - Recursive calls: Analyze recursion tree
        - Single pass: O(n)
        """
        max_nesting = self._get_max_loop_nesting(node)
        has_recursion = self._has_recursion(node)
        has_binary_search = self._has_binary_search_pattern(node)
        has_two_pointers = self._has_two_pointer_pattern(node)

        # Check for constant time
        if max_nesting == 0 and not has_recursion:
            return "O(1)"

        # Binary search pattern
        if has_binary_search:
            return "O(log n)"

        # Two pointer pattern - even with nested loops, it's O(n)
        # because pointers converge and don't reset
        if has_two_pointers and max_nesting >= 1:
            return "O(n)"

        # Recursion analysis
        if has_recursion:
            recursion_type = self._analyze_recursion_pattern(node)
            if recursion_type == "binary":
                return "O(log n)"
            elif recursion_type == "linear":
                return "O(n)"
            elif recursion_type == "exponential":
                return "O(2^n)"

        # Loop-based complexity
        if max_nesting == 1:
            return "O(n)"
        elif max_nesting == 2:
            return "O(n^2)"
        elif max_nesting == 3:
            return "O(n^3)"
        elif max_nesting > 3:
            return f"O(n^{max_nesting})"

        return "O(n)"

    def _analyze_space_complexity(self, node: ast.AST) -> str:
        """
        Determine space complexity by analyzing data structures and recursion.

        Patterns:
        - In-place operations: O(1)
        - Creating new list/dict of size n: O(n)
        - Recursion depth n: O(n)
        - 2D array: O(n^2)
        """
        creates_collection = self._creates_collection(node)
        recursion_depth = self._estimate_recursion_depth(node)
        uses_2d_structure = self._uses_2d_structure(node)

        # Recursion stack
        if recursion_depth > 0:
            return "O(n)"

        # 2D structures
        if uses_2d_structure:
            return "O(n^2)"

        # Collection creation
        if creates_collection:
            return "O(n)"

        # In-place operations
        return "O(1)"

    def _get_max_loop_nesting(self, node: ast.AST, current_depth: int = 0) -> int:
        """Get maximum loop nesting depth"""
        max_depth = current_depth

        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                # Check nesting inside this loop
                for inner_child in ast.iter_child_nodes(child):
                    child_depth = self._get_max_loop_nesting(inner_child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)

        return max_depth

    def _has_recursion(self, node: ast.FunctionDef) -> bool:
        """Check if function has recursive calls"""
        func_name = node.name

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == func_name:
                    return True
                if isinstance(child.func, ast.Attribute) and child.func.attr == func_name:
                    return True

        return False

    def _has_binary_search_pattern(self, node: ast.AST) -> bool:
        """Detect binary search pattern (left/right pointers, mid calculation)"""
        has_left_right = False
        has_mid_calc = False

        for child in ast.walk(node):
            # Check for left/right variables
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if target.id in ('left', 'right', 'lo', 'hi'):
                            has_left_right = True

            # Check for mid calculation pattern
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.FloorDiv):
                has_mid_calc = True

        return has_left_right and has_mid_calc

    def _analyze_recursion_pattern(self, node: ast.FunctionDef) -> str:
        """
        Determine recursion type.

        Returns: 'binary', 'linear', or 'exponential'
        """
        recursive_call_count = 0

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == node.name:
                    recursive_call_count += 1
                elif isinstance(child.func, ast.Attribute) and child.func.attr == node.name:
                    recursive_call_count += 1

        # Multiple recursive calls suggest exponential
        if recursive_call_count >= 2:
            return "exponential"

        # Check for binary search recursion (dividing problem in half)
        if self._has_binary_search_pattern(node):
            return "binary"

        return "linear"

    def _creates_collection(self, node: ast.AST) -> bool:
        """Check if function creates a new collection"""
        for child in ast.walk(node):
            # List/dict/set creation
            if isinstance(child, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp)):
                return True

            # List/dict constructor calls
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in ('list', 'dict', 'set', 'defaultdict'):
                        return True

        return False

    def _estimate_recursion_depth(self, node: ast.FunctionDef) -> int:
        """Estimate recursion depth (0 if no recursion)"""
        if self._has_recursion(node):
            return 1  # Assume O(n) recursion depth
        return 0

    def _uses_2d_structure(self, node: ast.AST) -> bool:
        """Check if function uses 2D arrays/matrices"""
        for child in ast.walk(node):
            # Nested list comprehension
            if isinstance(child, ast.ListComp):
                for generator in child.generators:
                    if isinstance(generator.iter, ast.ListComp):
                        return True

            # [[...] for ... in ...] pattern
            if isinstance(child, ast.List):
                for elt in child.elts:
                    if isinstance(elt, ast.List):
                        return True

        return False

    def _generate_explanation(
        self,
        node: ast.FunctionDef,
        time_complexity: str,
        space_complexity: str
    ) -> str:
        """Generate human-readable explanation of the approach"""
        explanations = []

        # Analyze approach
        has_loops = self._get_max_loop_nesting(node) > 0
        has_recursion = self._has_recursion(node)
        has_two_pointers = self._has_two_pointer_pattern(node)
        has_hash_map = self._uses_hash_map(node)
        creates_new_structure = self._creates_collection(node)

        # Build explanation
        if has_two_pointers:
            explanations.append(
                "The code uses two pointers to efficiently traverse the input"
            )

        if has_hash_map:
            explanations.append(
                "Uses a hash map/dictionary for O(1) lookups"
            )

        if has_recursion:
            explanations.append(
                "Employs recursion to break down the problem"
            )
        elif has_loops:
            loop_depth = self._get_max_loop_nesting(node)
            if loop_depth == 1:
                explanations.append(
                    "Iterates through the input once in a single loop"
                )
            elif loop_depth == 2:
                explanations.append(
                    "Uses nested loops to process the input"
                )

        if creates_new_structure and not has_recursion:
            explanations.append(
                "Creates additional data structures proportional to input size"
            )
        elif not creates_new_structure and space_complexity == "O(1)":
            explanations.append(
                "Operates in-place without additional data structures"
            )

        if not explanations:
            explanations.append(
                "Processes the input using basic operations"
            )

        return ". ".join(explanations) + "."

    def _has_two_pointer_pattern(self, node: ast.AST) -> bool:
        """Detect two-pointer pattern"""
        pointer_vars = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if target.id in ('left', 'right', 'i', 'j', 'start', 'end', 'lo', 'hi'):
                            pointer_vars.add(target.id)

        return len(pointer_vars) >= 2

    def _uses_hash_map(self, node: ast.AST) -> bool:
        """Check if code uses dictionary/hash map"""
        for child in ast.walk(node):
            if isinstance(child, ast.Dict):
                return True
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in ('dict', 'defaultdict', 'Counter'):
                        return True
        return False


def analyze_code_complexity(code: str) -> Dict[str, Dict]:
    """
    Analyze complexity for all functions in code.

    Args:
        code: Python source code

    Returns:
        Dictionary mapping function names to complexity analysis
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}

    analyzer = ComplexityAnalyzer()
    results = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            analysis = analyzer.analyze_function(node, code)
            results[node.name] = analysis

    return results
