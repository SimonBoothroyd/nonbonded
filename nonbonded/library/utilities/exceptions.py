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


class UnrecognisedPropertyType(NonbondedException):
    def __init__(self, property_type):

        self.property_type = property_type

        super(UnrecognisedPropertyType, self).__init__(
            f"{property_type} is not a valid property type. The property type must "
            f"be the name of a class defined in `openff.evaluator.properties`."
        )


class UnsupportedEndpointError(NonbondedException):
    pass
