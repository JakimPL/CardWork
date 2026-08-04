from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.ordering.composite import Composite
from cardwork.ordering.preorder import Key, Preorder
from cardwork.ordering.tiers import Tiers

from ..cases import Case, descriptions


class ByLength(Preorder[str]):
    """A preorder with genuine ties: two words of one length sit alongside each other."""

    def key(self, value: str) -> Key:
        return (len(value),)


SIZES: Final[Preorder[str]] = Tiers(("small", "medium", "large"))
LENGTHS: Final[Preorder[str]] = ByLength()


@dataclass(frozen=True)
class ComparisonCase(Case):
    left: str
    right: str
    comparison: int
    equivalent: bool


COMPARISONS: Final[tuple[ComparisonCase, ...]] = (
    ComparisonCase(
        description="a lower place sits below a higher one",
        left="small",
        right="large",
        comparison=-1,
        equivalent=False,
    ),
    ComparisonCase(
        description="a higher place sits above a lower one",
        left="large",
        right="small",
        comparison=1,
        equivalent=False,
    ),
    ComparisonCase(
        description="a value sits alongside itself",
        left="medium",
        right="medium",
        comparison=0,
        equivalent=True,
    ),
)


@pytest.mark.parametrize("case", COMPARISONS, ids=descriptions(COMPARISONS))
def test_comparison_reads_the_places_of_both_values(case: ComparisonCase) -> None:
    assert SIZES.compare(case.left, case.right) == case.comparison
    assert SIZES.equivalent(case.left, case.right) is case.equivalent


@dataclass(frozen=True)
class ExtremaCase(Case):
    values: tuple[str, ...]
    maxima: tuple[str, ...]
    argmaxima: tuple[int, ...]
    minima: tuple[str, ...]
    argminima: tuple[int, ...]


EXTREMA: Final[tuple[ExtremaCase, ...]] = (
    ExtremaCase(
        description="an empty run reaches neither end",
        values=(),
        maxima=(),
        argmaxima=(),
        minima=(),
        argminima=(),
    ),
    ExtremaCase(
        description="a lone value stands at both ends",
        values=("cat",),
        maxima=("cat",),
        argmaxima=(0,),
        minima=("cat",),
        argminima=(0,),
    ),
    ExtremaCase(
        description="distinct places yield one value at each end",
        values=("cat", "kitten", "ox"),
        maxima=("kitten",),
        argmaxima=(1,),
        minima=("ox",),
        argminima=(2,),
    ),
    ExtremaCase(
        description="a shared top yields every value holding it",
        values=("cat", "dog", "ox"),
        maxima=("cat", "dog"),
        argmaxima=(0, 1),
        minima=("ox",),
        argminima=(2,),
    ),
    ExtremaCase(
        description="a shared foot yields every value holding it",
        values=("kitten", "cat", "dog"),
        maxima=("kitten",),
        argmaxima=(0,),
        minima=("cat", "dog"),
        argminima=(1, 2),
    ),
)


@pytest.mark.parametrize("case", EXTREMA, ids=descriptions(EXTREMA))
def test_extrema_report_every_value_reaching_an_end(case: ExtremaCase) -> None:
    assert LENGTHS.maxima(case.values) == case.maxima
    assert LENGTHS.argmaxima(case.values) == case.argmaxima
    assert LENGTHS.minima(case.values) == case.minima
    assert LENGTHS.argminima(case.values) == case.argminima


def test_ordering_a_run_keeps_values_of_one_place_as_they_came() -> None:
    assert LENGTHS.ascending(("dog", "ox", "cat")) == ("ox", "dog", "cat")
    assert LENGTHS.descending(("dog", "ox", "cat")) == ("dog", "cat", "ox")


def test_tiers_place_a_value_where_the_list_names_it() -> None:
    assert SIZES.key("small") == (0,)
    assert SIZES.key("large") == (2,)


def test_tiers_refuse_a_value_they_do_not_list() -> None:
    with pytest.raises(KeyError, match="takes no place"):
        SIZES.key("enormous")


def test_tiers_refuse_a_list_naming_one_value_twice() -> None:
    with pytest.raises(ValueError, match="Every value takes one place"):
        Tiers(("small", "large", "small"))


def test_a_composite_order_refines_the_first_order_by_the_next() -> None:
    refined: Preorder[str] = Composite(LENGTHS, SIZES)

    assert LENGTHS.equivalent("small", "large")
    assert refined.compare("small", "large") == -1
    assert refined.ascending(("medium", "large", "small")) == ("small", "large", "medium")


def test_a_composite_order_refines_at_least_one_order() -> None:
    with pytest.raises(ValueError, match="at least one order"):
        Composite()
