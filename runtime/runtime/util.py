from enum import IntEnum


class AutoIntEnum(IntEnum):
    """
    An enum with automatically incrementing integer values, starting from zero.

    References:
        .. _Python `enum` Reference
            https://docs.python.org/3/library/enum.html#using-automatic-values
    """
    # pylint: disable=no-self-argument
    def _generate_next_value_(name, start, count, last_values):
        return count
