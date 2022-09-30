import pytest

from src.python.producer.producer import to_boolean


def test_to_boolean():
    assert to_boolean('Y') is True
    assert to_boolean('N') is False

    with pytest.raises(NotImplementedError):
        to_boolean('unknown input value')