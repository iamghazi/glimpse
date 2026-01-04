"""
Custom Exception Classes
"""


class VideoAnalyserException(Exception):
    """Base exception for all video analyser errors"""

    pass


class VideoProcessingError(VideoAnalyserException):
    """Error during video processing (chunking, frame extraction)"""

    pass


class AIAnalysisError(VideoAnalyserException):
    """Error during AI analysis (transcription, visual description)"""

    pass


class EmbeddingGenerationError(VideoAnalyserException):
    """Error during embedding generation"""

    pass


class VectorDBError(VideoAnalyserException):
    """Error during vector database operations"""

    pass


class SearchError(VideoAnalyserException):
    """Error during search operations"""

    pass


class RerankingError(VideoAnalyserException):
    """Error during reranking operations"""

    pass


class ChatError(VideoAnalyserException):
    """Error during chat operations"""

    pass


class ConfigurationError(VideoAnalyserException):
    """Error in application configuration"""

    pass


class ValidationError(VideoAnalyserException):
    """Error in data validation"""

    pass
