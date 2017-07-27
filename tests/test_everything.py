import pytest

import satras.calc_skills as sc


def test_prepare_lines():
    # should no longer contain comments
    test_input = [
        "normal line\n",
        "# comment\n",
        "  # comment with indentation\n",
        "line without ending char",
        "    line with indentation\n",
        "",
        "   \n",
        "   ",
        "\n",
        "line with trailing whitespace   \n",
    ]
    expected = [
        "normal line",
        "line without ending char",
        "line with indentation",
        "line with trailing whitespace",
    ]
    assert sc.prepare_lines(test_input) == expected


def test_eval_tree():
    assert False


@pytest.mark.parametrize("test_input,expected", [
    # positive tests
    ("foo",
     [("PLAYER", "foo")]),
    (">",
     [(">",)]),
    ("=",
     [("=",)]),
    (",",
     [(",",)]),
    ("foo > bar",
     [("PLAYER", "foo"), (">",), ("PLAYER", "bar")]),
    ("foo = bar",
     [("PLAYER", "foo"), ("=",), ("PLAYER", "bar")]),
    ("unusual_name123 > bar",
     [("PLAYER", "unusual_name123"), (">",), ("PLAYER", "bar")]),
    ("foo, bar > batz, foobar",
     [("PLAYER", "foo"), (",",), ("PLAYER", "bar"), (">",),
      ("PLAYER", "batz"), (",",), ("PLAYER", "foobar")]),
])
def test_tokenize(test_input, expected):
    assert sc.tokenize(test_input) == expected


    # negative tests
#    ("<",
#     None), # maybe throw error because it's unsupported; is it a player name?
#    (">>",
#     None), # maybe throw error because player missing; or do it in wisent?
#    ("foo > = bar",
#     None), # maybe throw error because player missing; or do it in wisent?
#    ("foo, > bar",
#     None), # maybe throw error because player missing; or do it in wisent?
def test_game_line2game_tree():
    assert False


def test_structure_games():
    assert False
    # associate metadata with games

def test_flatten_structure():
    assert False
    # creates a proper pandas DataFrame for easy grouping
