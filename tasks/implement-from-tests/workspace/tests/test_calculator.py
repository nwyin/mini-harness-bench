import pytest
from calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


def test_add_positive(calc):
    assert calc.add(2, 3) == 5


def test_add_negative(calc):
    assert calc.add(-1, -1) == -2


def test_add_zero(calc):
    assert calc.add(0, 0) == 0


def test_subtract(calc):
    assert calc.subtract(10, 4) == 6


def test_subtract_negative_result(calc):
    assert calc.subtract(3, 7) == -4


def test_multiply(calc):
    assert calc.multiply(3, 4) == 12


def test_multiply_by_zero(calc):
    assert calc.multiply(5, 0) == 0


def test_divide(calc):
    assert calc.divide(10, 2) == 5.0


def test_divide_float_result(calc):
    assert calc.divide(7, 2) == 3.5


def test_divide_by_zero(calc):
    with pytest.raises(ValueError):
        calc.divide(1, 0)


def test_power(calc):
    assert calc.power(2, 3) == 8


def test_power_zero_exponent(calc):
    assert calc.power(5, 0) == 1


def test_modulo(calc):
    assert calc.modulo(10, 3) == 1


def test_modulo_by_zero(calc):
    with pytest.raises(ValueError):
        calc.modulo(10, 0)
