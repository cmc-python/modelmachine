# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.numeric import Integer
from pytest import raises

class TestNumeric:

    """Case test for Integer class."""

    first, second = None, None

    def setup(self):
        """Init two test values."""
        self.first = Integer(10, 32, True)
        self.second = Integer(12, 32, True)

    def test_init(self):
        """Test, that we can create numbers."""
        assert self.first.size == 32
        assert self.first.signed == True
        assert self.first.get_value() == 10

        self.first = Integer(2 ** 32 - 1, 32, True)
        assert self.first.get_value() == -1

        self.first = Integer(2 ** 32 - 1, 32, False)
        assert self.first.get_value() == 2 ** 32 - 1

        for size in (8, 16, 32, 64):
            for signed in (True, False):
                self.first = Integer(10, size, signed)
                assert self.first.size == size
                assert self.first.signed == signed
                assert self.first.get_value() == 10
                self.first = Integer(10, signed=signed, size=size)
                assert self.first.size == size
                assert self.first.signed == signed
                assert self.first.get_value() == 10

    def test_check_compability(self):
        """Test check compability method."""
        with raises(NotImplementedError):
            self.first.check_compability(14)
        with raises(NotImplementedError):
            self.first.check_compability(Integer(14, 32, False))
        with raises(NotImplementedError):
            self.first.check_compability(Integer(14, 16, True))
        print(self.first.size)
        print(self.first.signed)
        print(self.second.size)
        print(self.second.signed)
        self.first.check_compability(self.second)
        self.first.check_compability(Integer(14, 32, True))

        for first_size in (8, 16, 32, 64):
            for second_size in (8, 16, 32, 64):
                for signed in (False, True):
                    self.first = Integer(10, first_size, signed)
                    self.second = Integer(12, second_size, signed)

                    if first_size == second_size:
                        self.first.check_compability(self.second)
                        self.second.check_compability(self.first)
                    else:
                        with raises(NotImplementedError):
                            self.first.check_compability(self.second)
                        with raises(NotImplementedError):
                            self.second.check_compability(self.first)

                    self.first = Integer(10, first_size, signed)
                    self.second = Integer(12, second_size, not signed)
                    with raises(NotImplementedError):
                        self.first.check_compability(self.second)
                    with raises(NotImplementedError):
                        self.second.check_compability(self.first)

        Integer(15, 8, False).check_compability(Integer(16, 8, False))
        with raises(NotImplementedError):
            Integer(15, 8, False).check_compability(Integer(16, 8, True))
        with raises(NotImplementedError):
            Integer(15, 16, False).check_compability(Integer(16, 8, False))

    def test_get_value(self):
        """Test get_value method."""
        assert isinstance(self.first.get_value(), int)
        assert self.first.get_value() == 10
        assert isinstance(self.second.get_value(), int)
        assert self.second.get_value() == 12
        assert Integer(2 ** 32 - 1, 32, True).get_value() == -1
        assert Integer(2 ** 32 - 1, 32, False).get_value() == 2 ** 32 - 1

    def test_index(self):
        """Test, if we can useinteger for indexing."""
        arr = [1, 2, 3, 4]
        self.first = Integer(1, 32, True)
        assert arr[self.first.get_value()] == 2
        arr[self.first.get_value()] = 10
        assert arr == [1, 10, 3, 4]

    def test_add(self):
        """Test sum of two integer."""
        result = self.first + self.second

        assert isinstance(result, Integer)
        assert result.size == 32
        assert result.signed == True
        assert result.get_value() == 22

        result = Integer(2 ** 31 - 1, 32, True) + Integer(2 ** 31 - 1, 32, True)
        assert result.get_value() == -2

        with raises(NotImplementedError):
            result = self.first + 42

    def test_mul(self):
        """Test multiplication of two integer."""
        result = self.first * self.second

        assert isinstance(result, Integer)
        assert result.size == 32
        assert result.signed == True
        assert result.get_value() == 120

        result = Integer(1555256314, 32, True) * Integer(-1234567890, 32, True)
        assert result.get_value() == 264317164

        with raises(NotImplementedError):
            result = self.first * 42

    def test_sub(self):
        """Test substraction of two integer."""
        result = self.first - self.second

        assert isinstance(result, Integer)
        assert result.size == 32
        assert result.signed == True
        assert result.get_value() == -2

        result = self.second - self.first

        assert isinstance(result, Integer)
        assert result.size == 32
        assert result.signed == True
        assert result.get_value() == 2

        self.first = Integer(10, 32, False)
        self.second = Integer(12, 32, False)

        result = self.first - self.second

        assert isinstance(result, Integer)
        assert result.size == 32
        assert result.signed == False
        assert result.get_value() == 2 ** 32 - 2

        result = self.second - self.first

        assert isinstance(result, Integer)
        assert result.size == 32
        assert result.signed == False
        assert result.get_value() == 2

        result = Integer(-2145634518, 32, True) - Integer(2000000000, 32, True)
        assert result.get_value() == 149332778

        with raises(NotImplementedError):
            result = self.first - 42

    def test_eq(self):
        """Test __eq__ method."""
        assert self.first != self.second
        assert self.first == Integer(10, 32, True)

    def test_divmod(self):
        """Test  method."""
        assert divmod(self.second, self.first) == (Integer(1, 32, True), Integer(2, 32, True))
        assert (divmod(Integer(156, 32, True), Integer(10, 32, True)) ==
                (Integer(15, 32, True), Integer(6, 32, True)))
        assert (divmod(Integer(-156, 32, True), Integer(10, 32, True)) ==
                (Integer(-15, 32, True), Integer(-6, 32, True)))
        assert (divmod(Integer(156, 32, True), Integer(-10, 32, True)) ==
                (Integer(-15, 32, True), Integer(6, 32, True)))
        assert (divmod(Integer(-156, 32, True), Integer(-10, 32, True)) ==
                (Integer(15, 32, True), Integer(-6, 32, True)))

        assert self.second / self.first == Integer(1, 32, True)
        assert self.second // self.first == Integer(1, 32, True)
        assert self.second % self.first == Integer(2, 32, True)

    def test_get_data(self):
        """Test two's complement."""
        assert self.first.get_data() == 10
        self.first = Integer(-5, 32, True)
        assert self.first.get_data() == 2 ** 32 - 5
        assert self.first.get_value() == -5
        self.first = Integer(-5, 32, signed=False)
        assert self.first.get_data() == 2 ** 32 - 5
        assert self.first.get_value() == 2 ** 32 - 5

    def test_hash(self):
        """Test if we can use Integer for indexing."""
        third = Integer(10, 32, True)
        assert hash(self.first) != hash(self.second)
        assert hash(self.first) == hash(third)
        assert hash(self.second) != hash(third)
        dic = dict()
        dic[self.first] = 10
        dic[self.second] = 11
        assert dic[self.first] == 10
        assert dic[self.second] == 11
        assert dic[third] == 10
