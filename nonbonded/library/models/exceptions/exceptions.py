class MutuallyExclusiveError(ValueError):
    def __init__(self, *fields: str):

        fields_string = ", ".join(fields)

        super(MutuallyExclusiveError, self).__init__(
            f"The {fields_string} fields are mutually exclusive"
        )
