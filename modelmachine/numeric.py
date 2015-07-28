# -*- coding: utf-8 -*-

"""Arithmetic logic unit make operations with internal registers."""

from numbers import Number

class Integer(Number):

    """Integer type with fixed length."""

    def __init__(self, value, size, signed):
        """See help(type(x))."""
        self.size = size
        self.signed = signed

        self.value = value % 2 ** size

    def __hash__(self):
        """Hash is important for indexing."""
        return hash((self.size, self.signed, self.value))

    def check_compability(self, other):
        """Test compability of two numbers."""
        if  (not isinstance(other, type(self)) or
             self.size != other.size or
             self.signed != other.signed):
            raise NotImplementedError('Not compability types.')

    def get_value(self):
        """Return integer value."""
        if self.signed:
            sign_bit = 2 ** (self.size - 1)
            if self.value & sign_bit != 0:
                return self.value - 2 ** self.size

        return self.value

    def get_data(self):
        """Return value in two's complement."""
        return self.value

    def __add__(self, other):
        """Equal to self + other."""
        self.check_compability(other)
        value = self.get_value() + other.get_value()
        return type(self)(value=value, size=self.size, signed=self.signed)

    def __sub__(self, other):
        """Equal to self - other."""
        self.check_compability(other)
        value = self.get_value() - other.get_value()
        return type(self)(value=value, size=self.size, signed=self.signed)

    def __mul__(self, other):
        """Equal to self * other."""
        self.check_compability(other)
        value = self.get_value() * other.get_value()
        return type(self)(value=value, size=self.size, signed=self.signed)

    def __divmod__(self, other):
        """Equal to divmod(self, other)."""
        self.check_compability(other)

        div = abs(self.get_value()) // abs(other.get_value())
        if self.get_value() * other.get_value() < 0:
            div *= -1

        mod = self.get_value() - div * other.get_value()

        return (Integer(div, self.size, self.signed),
                Integer(mod, self.size, self.signed))

    def __floordiv__(self, other):
        """self // other."""
        return divmod(self, other)[0]


    def __truediv__(self, other):
        """self / other."""
        return divmod(self, other)[0]

    def __mod__(self, other):
        """self % other."""
        return divmod(self, other)[1]

    def __eq__(self, other):
        """Test if two integer is equal."""
        self.check_compability(other)
        return self.get_value() == other.get_value()
