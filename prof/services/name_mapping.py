from prof.enums import UniversityChoices, MajorChoices, YearChoices
from _helpers import singleton


@singleton
class NameMappingService:

    def __init__(self):
        self.university = dict(UniversityChoices.choices)
        self.major = dict(MajorChoices.choices)
        self.year = dict(YearChoices.choices)

    def map_university(self, uni: str) -> str:
        return self.university[uni]

    def map_major(self, mj: str) -> str:
        return self.major[mj]

    def map_year(self, y: str) -> str:
        return self.year[y]
