# -*- coding: utf-8 -*-

"""Arithmetic logic unit make operations with internal registers."""

from numpy import int8, int16, int32, int64, uint8, uint16, uint32, uint64
from numbers import Number

class Integer(Number):

    """Integer type with fixed length.

    Allowed sizes: 8, 16, 32, 64."""

    def __init__(self, value, size=32, signed=True):
        """See help(type(x))."""
        self.size = size
        self.signed = signed

        if size == 8 and signed:
            self.internal_type = int8
        elif size == 16 and signed:
            self.internal_type = int16
        elif size == 32 and signed:
            self.internal_type = int32
        elif size == 64 and signed:
            self.internal_type = int64
        elif size == 8 and not signed:
            self.internal_type = uint8
        elif size == 16 and not signed:
            self.internal_type = uint16
        elif size == 32 and not signed:
            self.internal_type = uint32
        elif size == 64 and not signed:
            self.internal_type = uint64
        else:
            if signed:
                raise NotImplementedError('Signed type with {size} bits '
                                          'length not implemented yet'
                                          .format(size=size))
            else:
                raise NotImplementedError('Unsigned type with {size} bits '
                                          'length not implemented yet'
                                          .format(size=size))

        self.value = self.internal_type(value)

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
        return int(self.value)

    def __add__(self, other):
        """self + other."""
        self.check_compability(other)
        value = self.value + other.value
        return type(self)(value=value, size=self.size, signed=self.signed)

    def __sub__(self, other):
        """self - other."""
        self.check_compability(other)
        value = self.value - other.value
        return type(self)(value=value, size=self.size, signed=self.signed)

    def __mul__(self, other):
        """self * other."""
        self.check_compability(other)
        value = self.value * other.value
        return type(self)(value=value, size=self.size, signed=self.signed)

    def __divmod__(self, other):
        """Equals divmod(self, other)."""
        self.check_compability(other)

        div = abs(self.get_value()) // abs(other.get_value())
        if self.get_value() * other.get_value() < 0:
            div *= -1

        mod = self.get_value() - div * other.get_value()

        return (Integer(div, self.size, self.signed),
                Integer(mod, self.size, self.signed))

    def __floordiv__(self, other):
        """Equals self // other."""
        return divmod(self, other)[0]


    def __truediv__(self, other):
        """Equals self / other."""
        return divmod(self, other)[0]

    def __mod__(self, other):
        """Equals self % other."""
        return divmod(self, other)[1]

    def __eq__(self, other):
        """Test if two integer is equal."""
        self.check_compability(other)
        return self.get_value() == other.get_value()
