"""Tests for Gemini LLM Client"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.llm.client import GeminiClient, analyze_code, _parse_sections


class TestGeminiClient:
    """Test suite for GeminiClient"""

    @patch('app.llm.client.GEMINI_AVAILABLE', True)
    @patch('app.llm.client.genai')
    def test_client_initialization_with_api_key(self, mock_genai):
        """Test client initializes correctly with API key"""
        client = GeminiClient(api_key="test_api_key")

        assert client.api_key == "test_api_key"
        assert client.enabled is True
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")

    @patch('app.llm.client.GEMINI_AVAILABLE', False)
    def test_client_initialization_when_unavailable(self):
        """Test client handles missing SDK gracefully"""
        client = GeminiClient(api_key="test_key")

        assert client.enabled is False
        assert client.model is None

    @patch('app.llm.client.GEMINI_AVAILABLE', True)
    @patch('app.llm.client.genai')
    def test_client_initialization_without_api_key(self, mock_genai):
        """Test client initialization without API key"""
        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = None

            client = GeminiClient()

            assert client.enabled is False

    @pytest.mark.asyncio
    @patch('app.llm.client.GEMINI_AVAILABLE', True)
    @patch('app.llm.client.genai')
    async def test_generate_content_success(self, mock_genai):
        """Test successful content generation"""
        # Mock the model
        mock_model = AsyncMock()
        mock_response = Mock()
        mock_response.text = "This is a test response"
        mock_model.generate_content_async.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        client.model = mock_model

        result = await client.generate_content("Test prompt")

        assert result == "This is a test response"
        mock_model.generate_content_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_when_disabled(self):
        """Test generate_content returns None when client is disabled"""
        with patch('app.llm.client.GEMINI_AVAILABLE', False):
            client = GeminiClient(api_key="test_key")

            result = await client.generate_content("Test prompt")

            assert result is None

    @pytest.mark.asyncio
    @patch('app.llm.client.GEMINI_AVAILABLE', True)
    @patch('app.llm.client.genai')
    async def test_generate_content_handles_exception(self, mock_genai):
        """Test generate_content handles API errors gracefully"""
        mock_model = AsyncMock()
        mock_model.generate_content_async.side_effect = Exception("API Error")

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        client.model = mock_model

        result = await client.generate_content("Test prompt")

        assert result is None

    @pytest.mark.asyncio
    @patch('app.llm.client.GEMINI_AVAILABLE', True)
    @patch('app.llm.client.genai')
    async def test_generate_content_with_parameters(self, mock_genai):
        """Test generate_content respects temperature and max_tokens"""
        mock_model = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Response"
        mock_model.generate_content_async.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = Mock(return_value={"temperature": 0.7, "max_output_tokens": 500})

        client = GeminiClient(api_key="test_key")
        client.model = mock_model

        result = await client.generate_content("Test", temperature=0.7, max_tokens=500)

        assert result == "Response"


class TestAnalyzeCode:
    """Test suite for analyze_code function"""

    @pytest.mark.asyncio
    async def test_analyze_code_when_llm_disabled(self):
        """Test analyze_code returns empty when LLM is disabled"""
        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = False
            mock_settings.GEMINI_API_KEY = None

            result = await analyze_code(
                code="def foo(): pass",
                issues=[],
                complexity={}
            )

            assert result["llm_suggestions"] == []
            assert result["critical_issues"] == []
            assert "disabled" in result["analysis"].lower()

    @pytest.mark.asyncio
    @patch('app.llm.client.GeminiClient')
    async def test_analyze_code_with_mock_client(self, mock_client_class):
        """Test analyze_code with mocked successful response"""
        # Create mock client instance
        mock_client = Mock()
        mock_client.enabled = True
        mock_client.generate_content = AsyncMock(return_value="""
**Critical Issues**
- Potential null pointer exception
- SQL injection vulnerability

**Code Quality**
- Add docstrings
- Use type hints

**Best Practices**
- Follow PEP 8
- Use context managers

**Refactoring Ideas**
- Extract method for better readability
- Reduce function complexity
        """)

        mock_client_class.return_value = mock_client

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            result = await analyze_code(
                code="def foo(): pass",
                issues=[{"severity": "warning", "message": "Test issue"}],
                complexity={"foo": 5}
            )

            assert isinstance(result, dict)
            assert "llm_suggestions" in result or "raw_analysis" in result

    @pytest.mark.asyncio
    @patch('app.llm.client.GeminiClient')
    async def test_analyze_code_client_not_enabled(self, mock_client_class):
        """Test analyze_code when client is not enabled"""
        mock_client = Mock()
        mock_client.enabled = False

        mock_client_class.return_value = mock_client

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            result = await analyze_code(
                code="def foo(): pass",
                issues=[],
                complexity={}
            )

            assert "error" in result
            assert "not available" in result["error"].lower()

    @pytest.mark.asyncio
    @patch('app.llm.client.GeminiClient')
    async def test_analyze_code_api_failure(self, mock_client_class):
        """Test analyze_code handles API failures"""
        mock_client = Mock()
        mock_client.enabled = True
        mock_client.generate_content = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            result = await analyze_code(
                code="def foo(): pass",
                issues=[],
                complexity={}
            )

            assert "error" in result
            assert "Failed to get response" in result["error"]

    @pytest.mark.asyncio
    @patch('app.llm.client.GeminiClient')
    async def test_analyze_code_with_long_code(self, mock_client_class):
        """Test analyze_code truncates long code"""
        mock_client = Mock()
        mock_client.enabled = True
        mock_client.generate_content = AsyncMock(return_value="**Code Quality**\n- Looks good")

        mock_client_class.return_value = mock_client

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            long_code = "def foo():\n    pass\n" * 1000  # Very long code

            result = await analyze_code(
                code=long_code,
                issues=[],
                complexity={}
            )

            # Code should be truncated in prompt
            call_args = mock_client.generate_content.call_args
            assert call_args is not None
            # Check that prompt doesn't contain entire long code
            assert len(call_args[0][0]) < len(long_code)

    @pytest.mark.asyncio
    @patch('app.llm.client.GeminiClient')
    async def test_analyze_code_with_many_issues(self, mock_client_class):
        """Test analyze_code limits issues in prompt"""
        mock_client = Mock()
        mock_client.enabled = True
        mock_client.generate_content = AsyncMock(return_value="**Code Quality**\n- Fix issues")

        mock_client_class.return_value = mock_client

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            # Create many issues
            issues = [
                {"severity": f"warning", "message": f"Issue {i}"}
                for i in range(20)
            ]

            result = await analyze_code(
                code="def foo(): pass",
                issues=issues,
                complexity={}
            )

            # Should limit to top 10 issues
            assert result is not None

    @pytest.mark.asyncio
    @patch('app.llm.client.GeminiClient')
    async def test_analyze_code_exception_handling(self, mock_client_class):
        """Test analyze_code handles exceptions gracefully"""
        mock_client = Mock()
        mock_client.enabled = True
        mock_client.generate_content = AsyncMock(side_effect=Exception("Network error"))

        mock_client_class.return_value = mock_client

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            result = await analyze_code(
                code="def foo(): pass",
                issues=[],
                complexity={}
            )

            assert "error" in result
            assert "Network error" in result["error"]


class TestParseSections:
    """Test suite for _parse_sections function"""

    def test_parse_sections_basic(self):
        """Test basic section parsing"""
        text = """
**Critical Issues**
- Issue 1
- Issue 2

**Code Quality**
- Suggestion 1
- Suggestion 2
        """

        result = _parse_sections(text)

        assert "critical issues" in result
        assert len(result["critical issues"]) == 2
        assert "code quality" in result
        assert len(result["code quality"]) == 2

    def test_parse_sections_empty_text(self):
        """Test parsing empty text"""
        result = _parse_sections("")

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parse_sections_no_sections(self):
        """Test parsing text without section headers"""
        text = "Just some random text without sections"

        result = _parse_sections(text)

        assert len(result) == 0

    def test_parse_sections_with_colons(self):
        """Test parsing sections with colons in headers"""
        text = """
**Critical Issues:**
- Issue 1

**Best Practices:**
- Practice 1
        """

        result = _parse_sections(text)

        assert "critical issues" in result
        assert "best practices" in result

    def test_parse_sections_mixed_format(self):
        """Test parsing with different header formats"""
        text = """
**Section One**
Content 1

**Section Two:**
Content 2

Some random text

**Section Three**
Content 3
        """

        result = _parse_sections(text)

        assert len(result) >= 2
        assert "section one" in result or "section two" in result or "section three" in result

    def test_parse_sections_preserves_content(self):
        """Test that content is preserved correctly"""
        text = """
**Test Section**
- First line
- Second line
- Third line
        """

        result = _parse_sections(text)

        assert "test section" in result
        assert len(result["test section"]) == 3
        assert any("First line" in item for item in result["test section"])


class TestIntegration:
    """Integration tests for LLM client"""

    @pytest.mark.asyncio
    @patch('app.llm.client.GEMINI_AVAILABLE', True)
    @patch('app.llm.client.genai')
    async def test_full_workflow(self, mock_genai):
        """Test complete workflow from client creation to analysis"""
        # Setup mocks
        mock_model = AsyncMock()
        mock_response = Mock()
        mock_response.text = """
**Critical Issues**
- Fix buffer overflow

**Code Quality**
- Add error handling

**Best Practices**
- Use type hints

**Refactoring Ideas**
- Extract helper functions
        """
        mock_model.generate_content_async.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        with patch('app.llm.client.settings') as mock_settings:
            mock_settings.ENABLE_LLM = True
            mock_settings.GEMINI_API_KEY = "test_key"

            # Create client
            client = GeminiClient(api_key="test_key")
            client.model = mock_model

            # Analyze code
            result = await analyze_code(
                code="def vulnerable_func(input): return eval(input)",
                issues=[{"severity": "error", "message": "Use of eval"}],
                complexity={"vulnerable_func": 10},
                client=client
            )

            # Verify results
            assert "raw_analysis" in result or "llm_suggestions" in result
