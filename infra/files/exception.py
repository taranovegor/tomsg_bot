class FileError(Exception):
    """Base class for file subsystem errors."""

    pass


class FileTooLargeError(FileError):
    """Raised when a remote file exceeds configured size limits."""

    pass


class FileDownloadError(FileError):
    """Raised on failures while downloading a file (HTTP/network/IO)."""

    pass
