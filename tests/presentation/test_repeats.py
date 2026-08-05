from cardwork.presentation.repeats import distinct, repeated


def test_distinct_names_each_value_once_in_the_order_it_first_appears() -> None:
    assert distinct(("a", "b", "a", "c", "b")) == ("a", "b", "c")


def test_repeated_names_the_values_appearing_more_than_once() -> None:
    assert repeated(("a", "b", "a", "c", "b", "a")) == ("a", "b")
