from typing import Collection, Hashable


class MutuallyExclusiveError(ValueError):
    def __init__(self, *fields: str):

        fields_string = ", ".join(fields)

        super(MutuallyExclusiveError, self).__init__(
            f"The {fields_string} fields are mutually exclusive"
        )


class DuplicateItemsError(ValueError):
    """An exception raised when a field which only accepts a list of unique items
    has a value which contains duplicates."""

    def __init__(self, field_name: str, duplicate_items: Collection[Hashable]):

        duplicate_items_string = ", ".join(map(str, {*duplicate_items}))

        super(DuplicateItemsError, self).__init__(
            f"{field_name} contains duplicate items: {duplicate_items_string}."
        )

        self.duplicate_items = duplicate_items
        self.field_name = field_name
