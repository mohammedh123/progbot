import enum
from dataclasses import dataclass, field
from itertools import chain
from typing import FrozenSet, Iterable


class EncounterId(enum.Enum):
    TOP = 1068
    FRU = 1079
    DMU = 1085


@dataclass(eq=True, frozen=True)
class ProgIndicator:
    cast_ids: FrozenSet[int]
    cast_count: int
    description: str = field(compare=False, hash=False)

    def __init__(
        self, cast_ids: int | Iterable[int], cast_count: int, description: str
    ) -> None:
        if isinstance(cast_ids, int):
            cast_ids = [cast_ids]

        object.__setattr__(self, "cast_ids", frozenset(cast_ids))
        object.__setattr__(self, "cast_count", cast_count)
        object.__setattr__(self, "description", description)


@dataclass(eq=True, frozen=True)
class Encounter:
    id: EncounterId
    name: str
    prog_indicators: list[ProgIndicator]

    def __post_init__(self) -> None:
        # Basically map (cast_id, count) to the PI
        object.__setattr__(
            self,
            "_prog_indicator_map",
            {
                (cast_id, pi.cast_count): pi
                for pi in self.prog_indicators
                for cast_id in pi.cast_ids
            },
        )

    def get_prog_indicator_by_cast_and_count(
        self, cast_id: int, count: int
    ) -> ProgIndicator:
        return self._prog_indicator_map.get((cast_id, count))

    def prog_indicating_cast_ids(self) -> set[int]:
        return set(chain.from_iterable(pi.cast_ids for pi in self.prog_indicators))


encounter_by_id = {
    e.id: e
    for e in (
        Encounter(
            EncounterId.TOP,
            "The Omega Protocol (Ultimate)",
            [
                ProgIndicator(*args)
                for args in (
                    (31491, 1, "Program Loop"),
                    (31499, 1, "Pantokrator"),
                    (31551, 1, "Party Synergy"),
                    (31544, 1, "Limitless Synergy"),
                    (31507, 1, "P3 Transition"),
                    (31573, 1, "Hello, World"),
                    (31596, 1, "Monitors"),
                    (31560, 1, "P3 Enrage"),
                    (31617, 1, "P4"),
                    (31611, 1, "P4 Enrage"),
                    (31624, 1, "Run: ****mi* (Delta Version)"),
                    (32788, 1, "Run: ****mi* (Sigma Version)"),
                    (32789, 1, "Run: ****mi* (Omega Version)"),
                    (31623, 1, "Blind Faith"),
                    (31649, 1, "Cosmo Memory"),
                    (31650, 1, "Cosmo Arrow 1"),
                    (31660, 1, "Unlimited Wave Cannon 1"),
                    (31650, 2, "Cosmo Arrow 2"),
                    (31660, 2, "Unlimited Wave Cannon 2"),
                    (31664, 1, "Cosmo Meteor"),
                    (31670, 1, "Magic Number 1"),
                    (31670, 2, "Magic Number 2"),
                    (31648, 1, "P6 Enrage"),
                )
            ],
        ),
        Encounter(
            EncounterId.FRU,
            "Futures Rewritten (Ultimate)",
            [
                ProgIndicator(*args)
                for args in (
                    ((40144, 40148), 1, "Cyclonic Break"),
                    ((40154, 40155), 1, "Utopian Sky"),
                    (40172, 1, "Fall of Faith"),
                    (40133, 1, "P1 Towers"),
                    (40128, 1, "P1 Enrage"),
                    (40197, 1, "Diamond Dust"),
                    (40179, 1, "Mirrors"),
                    (40212, 1, "Light Rampant"),
                    (40224, 1, "P2 Enrage"),
                    (40225, 1, "Intermission"),
                    (40259, 1, "Intermission Enrage"),
                    (40265, 1, "Hell's Judgment"),
                    (40266, 1, "Ultimate Relativity"),
                    (40296, 1, "Apocalypse"),
                    (40300, 1, "P3 Enrage"),
                    (40301, 1, "Darklit Dragonsong"),
                    (40298, 1, "Crystallize Time"),
                    (40305, 1, "P4 Enrage"),
                    (40263, 1, "Tree (Bad Ending)"),
                    (40306, 1, "Exalines 1"),
                    (40319, 1, "Towers 1"),
                    (40316, 1, "Polarizing Strikes 1"),
                    (40326, 1, "Pandora's Box"),
                    (40306, 2, "Exalines 2"),
                    (40319, 2, "Towers 2"),
                    (40316, 2, "Polarizing Strikes 2"),
                    (40306, 3, "Exalines 3"),
                    (40328, 1, "P5 Enrage"),
                )
            ],
        ),
        Encounter(
            EncounterId.DMU,
            "Dancing Mad (Ultimate)",
            [
                ProgIndicator(*args)
                for args in (
                    (50179, 1, "Revolting Ruin III"),
                    (48370, 1, "Graven Image 1"),
                    (48370, 2, "Graven Image 2"),
                    (48370, 3, "Graven Image 3"),
                    (47803, 1, "P1 Enrage"),
                    (47804, 1, "Forsaken"),
                    (47839, 1, "Trine"),
                    (47841, 1, "P2 Enrage"),
                    (49890, 1, "P3"),
                    (47858, 1, "Bowels of Agony"),
                    (47891, 1, "Vacuum Wave"),
                    (47845, 1, "Big Kefka"),
                    (47867, 1, "Black Hole"),
                    (50718, 1, "P3 Enrage"),
                )
            ],
        ),
    )
}

DEFAULT_ENCOUNTER_ID = EncounterId.DMU
