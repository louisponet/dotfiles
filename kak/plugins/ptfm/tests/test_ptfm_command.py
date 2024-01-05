from ptfm.command import ArgScanner, TokenType


def test_scanner():
    tokens = ArgScanner.tokenize('-foo bar -hop! -baz "titi \\"toto\\" tata"')

