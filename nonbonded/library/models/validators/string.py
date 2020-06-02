from pydantic import constr

NonEmptyStr = constr(min_length=1)
