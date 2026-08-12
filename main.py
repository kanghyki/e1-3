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


def compare_scores(score_a: float, score_b: float) -> int:
    if abs(score_a - score_b) < EPSILON:
        return 0
    return 1 if score_a > score_b else -1


def decide(score_cross: float, score_x: float) -> str:
    result = compare_scores(score_cross, score_x)
    if result == 0:
        return UNDECIDED
    return CROSS if result > 0 else X


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


def print_section(title: str) -> None:
    print()
    print("#" + "-" * 39)
    print("# " + title)
    print("#" + "-" * 39)


def print_grid(grid: Grid) -> None:
    for r in range(grid.size):
        print("  " + " ".join(repr(value) for value in grid.row(r)))


def parse_row(line: str, size: int) -> List[float]:
    tokens = line.split()
    if len(tokens) != size:
        raise ValueError(
            "입력 형식 오류: 각 줄에 %d개의 숫자를 공백으로 구분해 입력하세요." % size
        )
    values: List[float] = []
    for token in tokens:
        try:
            values.append(float(token))
        except ValueError:
            raise ValueError("입력 형식 오류: 숫자로 읽을 수 없는 값입니다 (%s)" % token)
    return values


def read_grid(title: str, size: int) -> Grid:
    while True:
        print("%s (%d줄 입력, 공백 구분)" % (title, size))
        rows: List[List[float]] = []
        try:
            for _ in range(size):
                rows.append(parse_row(input(), size))
        except ValueError as error:
            print(error)
            print("처음부터 다시 입력하세요.")
            continue
        return Grid.from_rows(rows)


def run_user_input_mode() -> None:
    size = 3

    print_section("[1] 필터 입력")
    filter_a = read_grid("필터 A", size)
    filter_b = read_grid("필터 B", size)
    print("필터 A 저장 완료")
    print_grid(filter_a)
    print("필터 B 저장 완료")
    print_grid(filter_b)

    print_section("[2] 패턴 입력")
    pattern = read_grid("패턴", size)
    print("패턴 저장 완료")
    print_grid(pattern)

    print_section("[3] MAC 결과")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    avg_ms = measure_mac_ms(pattern, filter_a)
    print("A 점수: %r" % score_a)
    print("B 점수: %r" % score_b)
    print("연산 시간(평균/%d회): %.4f ms" % (PERF_REPEAT, avg_ms))
    result = compare_scores(score_a, score_b)
    if result == 0:
        print("판정: 판정 불가 (|A-B| < %g)" % EPSILON)
    else:
        print("판정: %s" % ("A" if result > 0 else "B"))

    print_section("[4] 성능 분석 (평균/%d회)" % PERF_REPEAT)
    print_performance_table([(size, avg_ms)])
