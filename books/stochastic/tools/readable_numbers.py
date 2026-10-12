"""Normalize omitted leading zeros without touching code strings or comments."""
import ast
import io
import re
import tokenize

LEADING_DECIMAL = re.compile(r"(?<![A-Za-z0-9_.])\.(?=[0-9])")
TEX_DECIMAL = re.compile(r"(\\[A-Za-z]+\s*)\.(?=[0-9])")


def readable_text(text):
    return LEADING_DECIMAL.sub("0.", text)


def readable_tex(text):
    """A TeX control word is a boundary, even without a following space."""
    return TEX_DECIMAL.sub(r"\g<1>0.", readable_text(text))


def readable_code(source, language):
    if language == "python":
        lines = source.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        changes = []
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NUMBER and token.string.startswith("."):
                row, col = token.start
                changes.append(offsets[row - 1] + col)
        revised = source
        for offset in reversed(changes):
            revised = revised[:offset] + "0" + revised[offset:]
        if ast.dump(ast.parse(source)) != ast.dump(ast.parse(revised)):
            raise ValueError("Python number normalization changed the syntax tree")
        return revised
    if language != "c":
        raise ValueError(language)
    # A C lexer: string/character literals, comments and identifiers stay intact.
    tokens = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|0[xX](?:[0-9a-fA-F]+(?:\.[0-9a-fA-F]*)?|\.[0-9a-fA-F]+)[pP][+-]?[0-9]+[fFlL]?|0[xX][0-9a-fA-F]+[uUlL]*|[A-Za-z_][A-Za-z_0-9]*|(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)(?:[eE][+-]?[0-9]+)?[fFlLuU]*')
    def replace(match):
        value = match.group()
        return "0" + value if value.startswith(".") else value
    return tokens.sub(replace, source)
