import time
from typing import List, Sequence, Tuple

EPSILON = 1e-9
PERF_REPEAT = 10

CROSS_FILTER_3X3: List[List[float]] = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
X_FILTER_3X3: List[List[float]] = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]

CROSS = "Cross"
X = "X"
UNDECIDED = "UNDECIDED"


class SizeMismatchError(Exception):
    pass


class Grid:
    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValueError("크기는 1 이상이어야 합니다.")
        self.size: int = size
        self._cells: List[List[float]] = [[0.0] * size for _ in range(size)]

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[float]]) -> "Grid":
        size = len(rows)
        for row in rows:
            if len(row) != size:
                raise SizeMismatchError(
                    "정사각 배열이 아닙니다: 행 %d개, 열 %d개" % (size, len(row))
                )
        grid = cls(size)
        for r in range(size):
            for c in range(size):
                grid.set(r, c, float(rows[r][c]))
        return grid

    def get(self, r: int, c: int) -> float:
        return self._cells[r][c]

    def set(self, r: int, c: int, value: float) -> None:
        self._cells[r][c] = value

    def row(self, r: int) -> List[float]:
        return self._cells[r]


def mac(pattern: Grid, filter_grid: Grid) -> float:
    if pattern.size != filter_grid.size:
        raise SizeMismatchError(
            "크기 불일치: 패턴 %dx%d, 필터 %dx%d"
            % (pattern.size, pattern.size, filter_grid.size, filter_grid.size)
        )
    total = 0.0
    for r in range(pattern.size):
        pattern_row = pattern.row(r)
        filter_row = filter_grid.row(r)
        for c in range(pattern.size):
            total += pattern_row[c] * filter_row[c]
    return total


def decide(score_cross: float, score_x: float) -> str:
    if abs(score_cross - score_x) < EPSILON:
        return UNDECIDED
    return CROSS if score_cross > score_x else X


def measure_mac_ms(pattern: Grid, filter_grid: Grid, repeat: int = PERF_REPEAT) -> float:
    start = time.perf_counter()
    for _ in range(repeat):
        mac(pattern, filter_grid)
    elapsed = time.perf_counter() - start
    return elapsed * 1000 / repeat


def print_performance_table(measurements: Sequence[Tuple[int, float]]) -> None:
    print("크기        평균 시간(ms)      연산 횟수")
    print("-" * 40)
    for size, avg_ms in measurements:
        label = "%dx%d" % (size, size)
        print("%-12s%-18.4f%d" % (label, avg_ms, size * size))
