from click import Option, UsageError


class MutuallyExclusiveOption(Option):
    """
    Notes
    -----
    Taken from the StackOverflow post (https://stackoverflow.com/a/37491504)
    by Jacob on the 06/05/2020.
    """

    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help_kwarg = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help_kwarg + (
                " NOTE: This argument is mutually exclusive with "
                "arguments: [" + ex_str + "]."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(self.name, ", ".join(self.mutually_exclusive))
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)
