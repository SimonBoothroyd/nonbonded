from nonbonded.library.utilities.exceptions import NonbondedException


class ComponentException(NonbondedException):
    ...


class InvalidInputException(ComponentException):
    ...
