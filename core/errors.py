class DownloadError(Exception):
    pass


class FormatNotAvailableError(DownloadError):
    pass


class VideoNotFoundError(DownloadError):
    pass


class AuthenticationError(DownloadError):
    pass


class NetworkError(DownloadError):
    pass


class FilesystemError(DownloadError):
    pass


class CancelledError(DownloadError):
    pass


class FFmpegNotFoundError(DownloadError):
    pass


class ConversionError(DownloadError):
    pass


class RateLimitError(DownloadError):
    pass


class PlaylistError(DownloadError):
    pass


class MetadataExtractionError(DownloadError):
    pass


def classify_error(error: Exception) -> DownloadError:
    error_str = str(error).lower()
    
    if "cancelled" in error_str or "user cancelled" in error_str:
        return CancelledError(str(error))
    
    if "format" in error_str or "no video formats" in error_str:
        return FormatNotAvailableError(str(error))
    
    if "not found" in error_str or "404" in error_str or "unavailable" in error_str:
        return VideoNotFoundError(str(error))
    
    if "login" in error_str or "authentication" in error_str or "sign in" in error_str:
        return AuthenticationError(str(error))
    
    if "network" in error_str or "connection" in error_str or "timeout" in error_str:
        return NetworkError(str(error))
    
    if "permission" in error_str or "disk" in error_str or "space" in error_str:
        return FilesystemError(str(error))
    
    if "ffmpeg" in error_str:
        return FFmpegNotFoundError(str(error))
    
    if "conversion" in error_str or "postprocessing" in error_str:
        return ConversionError(str(error))
    
    if "rate limit" in error_str or "429" in error_str:
        return RateLimitError(str(error))
    
    if "playlist" in error_str:
        return PlaylistError(str(error))
    
    if "metadata" in error_str or "extract" in error_str:
        return MetadataExtractionError(str(error))
    
    return DownloadError(str(error))
