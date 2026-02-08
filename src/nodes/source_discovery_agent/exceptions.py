"""
Custom exceptions for Source Discovery Agent
"""


class SourceDiscoveryError(Exception):
    """Base exception for all Source Discovery Agent errors"""
    pass


class QueryValidationError(SourceDiscoveryError):
    """Raised when query validation fails"""
    pass


class NoSourcesFoundError(SourceDiscoveryError):
    """Raised when no valid sources are discovered"""
    pass


class QueryParsingError(SourceDiscoveryError):
    """Raised when query parsing fails"""
    pass


class CredibilityThresholdError(SourceDiscoveryError):
    """Raised when all sources are below credibility threshold"""
    pass


class NetworkError(SourceDiscoveryError):
    """Raised when network operations fail"""
    pass


class RobotsTxtError(SourceDiscoveryError):
    """Raised when robots.txt parsing fails"""
    pass


class ValidationError(SourceDiscoveryError):
    """Raised when source validation fails"""
    pass


class ConfigurationError(SourceDiscoveryError):
    """Raised when configuration is invalid"""
    pass
