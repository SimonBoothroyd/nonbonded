class NonbondedException(Exception):
    """The base exception for most of the custom exceptions
    within this framework with the exception of HTTP based
    exceptions.
    """

    ...


class UnrecognisedKwargsError(NonbondedException):
    def __init__(self, kwarg_names):

        self.kwarg_names = kwarg_names

        joined_kwarg_names = ", ".join(kwarg_names)

        super(UnrecognisedKwargsError, self).__init__(
            f"The {joined_kwarg_names} kwargs are unrecognised by this function."
        )


class UnrecognisedForceFieldError(NonbondedException):
    def __init__(self, file_extesion):

        self.file_extesion = file_extesion

        super(UnrecognisedForceFieldError, self).__init__(
            f"The type of force field source could not be determined from the "
            f"{file_extesion} extension."
        )


class UnrecognisedPropertyType(NonbondedException):
    def __init__(self, property_type):

        self.property_type = property_type

        super(UnrecognisedPropertyType, self).__init__(
            f"{property_type} is not a valid property type. The property type must "
            f"be the name of a class defined in `openff.evaluator.properties`."
        )


class ForceFieldNotFound(NonbondedException):
    ...


class UnsupportedEndpointError(NonbondedException):
    pass


class InvalidFileObjectError(NonbondedException):
    def __init__(self, file_name, found_type, expected_type):

        self.file_name = file_name

        if not isinstance(found_type, str):
            found_type = found_type.__name__
        if not isinstance(expected_type, str):
            expected_type = expected_type.__name__

        self.found_type = found_type
        self.expected_type = expected_type

        super(InvalidFileObjectError, self).__init__(
            f"The {file_name} file contained an object of type {found_type} while an "
            f"object of type {expected_type} was expected.."
        )


class MissingOptionalDependency(NonbondedException):
    """An exception raised when an optional dependency is required
    but cannot be found.

    Attributes
    ----------
    library_name
        The name of the missing library.
    license_issue
        Whether the library was importable but was unusable due
        to a missing license.
    """

    def __init__(self, library_name: str, license_issue: bool = False):
        """

        Parameters
        ----------
        library_name
            The name of the missing library.
        license_issue
            Whether the library was importable but was unusable due
            to a missing license.
        """

        message = f"The required {library_name} module could not be imported."

        if license_issue:
            message = f"{message} This is due to a missing license."

        super(MissingOptionalDependency, self).__init__(message)

        self.library_name = library_name
        self.license_issue = license_issue
