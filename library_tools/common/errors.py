"""Error handling with LLM-friendly error messages."""

from typing import Optional


class LibraryToolsError(Exception):
    """Base exception for all library tools errors.

    All exceptions include a user_message attribute with an LLM-friendly
    explanation that can be returned directly to the agent.
    """

    def __init__(self, message: str, user_message: Optional[str] = None):
        """Initialize error with technical and user-friendly messages.

        Args:
            message: Technical error message for logging
            user_message: LLM-friendly message to return to agent
        """
        super().__init__(message)
        self.user_message = user_message or message

    def to_llm_message(self) -> str:
        """Get LLM-friendly error message."""
        return self.user_message


class APIError(LibraryToolsError):
    """Error communicating with an external API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        user_message: Optional[str] = None
    ):
        """Initialize API error.

        Args:
            message: Technical error message
            status_code: HTTP status code if applicable
            user_message: LLM-friendly message
        """
        self.status_code = status_code

        if not user_message:
            if status_code == 404:
                user_message = "The requested resource was not found. Please check your search terms and try again."
            elif status_code == 401 or status_code == 403:
                user_message = "Authentication failed. Please check your API key configuration."
            elif status_code == 429:
                user_message = "Rate limit exceeded. Please try again in a few moments."
            elif status_code and status_code >= 500:
                user_message = "The service is temporarily unavailable. Please try again later."
            else:
                user_message = "An error occurred while contacting the service. Please try again."

        super().__init__(message, user_message)


class ConfigurationError(LibraryToolsError):
    """Error with tool configuration or settings."""

    def __init__(self, message: str, user_message: Optional[str] = None):
        if not user_message:
            user_message = f"Configuration error: {message}. Please check your environment variables or .env file."
        super().__init__(message, user_message)


class ValidationError(LibraryToolsError):
    """Error validating input parameters."""

    def __init__(self, message: str, user_message: Optional[str] = None):
        if not user_message:
            user_message = f"Invalid input: {message}. Please check your parameters and try again."
        super().__init__(message, user_message)


def format_error_for_llm(error: Exception) -> str:
    """Format any exception as an LLM-friendly message.

    Args:
        error: Any exception

    Returns:
        User-friendly error message suitable for LLM consumption
    """
    if isinstance(error, LibraryToolsError):
        return error.to_llm_message()

    # Generic fallback for unexpected errors
    error_type = type(error).__name__
    return f"An unexpected error occurred ({error_type}). Please try rephrasing your request or contact support if the problem persists."
