from pydantic import constr

NonEmptyStr = constr(min_length=1)


IdentifierStr = constr(min_length=1, max_length=32, regex="^[a-z0-9-]*$")
