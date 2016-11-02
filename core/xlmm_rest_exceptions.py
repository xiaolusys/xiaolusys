from rest_framework.exceptions import APIException, ValidationError as OriValidationError, \
    ParseError as OriParseError, AuthenticationFailed as OriAuthenticationFailed, NotAuthenticated as OriNotAuthenticated, \
    PermissionDenied, NotFound as OriNotFound, NotAcceptable as OriNotAcceptable, \
    UnsupportedMediaType as OriUnsupportedMediaType, Throttled as OriThrottled


class ValidationError(OriValidationError):
    status_code = 200


class ParseError(OriParseError):
    status_code = 200


class AuthenticationFailed(OriAuthenticationFailed):
    status_code = 200


class NotAuthenticated(OriNotAuthenticated):
    status_code = 200


class NotFound(OriNotFound):
    status_code = 200


class NotAcceptable(OriNotAcceptable):
    status_code = 200


class UnsupportedMediaType(OriUnsupportedMediaType):
    status_code = 200


class Throttled(OriThrottled):
    status_code = 200