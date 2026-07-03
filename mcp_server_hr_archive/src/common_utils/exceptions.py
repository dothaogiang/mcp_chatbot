class ArchiveClientError(Exception):
    pass


class NotFoundError(ArchiveClientError):
    pass


class BackendError(ArchiveClientError):
    pass


class UnauthorizedError(ArchiveClientError):
    pass


class ForbiddenError(ArchiveClientError):
    pass


class BadRequestError(ArchiveClientError):
    pass
