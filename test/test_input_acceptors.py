import pytest

from _pyprodtest.input_acceptors import ConsoleInputAcceptor, InputAcceptor


def test_input_acceptor_is_an_interface():
    with pytest.raises(TypeError):
        InputAcceptor()


def test_console_input_acceptor_implements_interface():
    assert isinstance(ConsoleInputAcceptor(), InputAcceptor)


def test_console_input_acceptor_rejects_unsupported_input_type():
    acceptor = ConsoleInputAcceptor()

    with pytest.raises(TypeError, match="bool or str"):
        acceptor.accept("Quantity", int)
