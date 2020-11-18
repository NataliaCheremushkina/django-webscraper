"""Own exceptions for scraper."""


class ScraperError(Exception):
    """Parent class for scrapers errors."""
    pass


class AccessDeniedError(ScraperError):
    """Used when scarper need login to access to content."""
    pass


class PageNotFoundError(ScraperError):
    """Used if page not found error in response."""
    pass


class PrivateAccountError(ScraperError):
    """Used if url relate to Private Account."""
    pass


class UnknownPageTypeError(ScraperError):
    """Used when unknown page type in response."""
    pass
