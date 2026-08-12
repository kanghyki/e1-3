import json
import time
from typing import Dict, List, NamedTuple, Sequence, Tuple

EPSILON = 1e-9
PERF_REPEAT = 10
DATA_PATH = "data.json"
LABEL_TABLE = {"+": "Cross", "cross": "Cross", "x": "X"}

CROSS_FILTER_3X3: List[List[float]] = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
X_FILTER_3X3: List[List[float]] = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]

CROSS = "Cross"
X = "X"
UNDECIDED = "UNDECIDED"


class SchemaError(Exception):
    pass


class SizeMismatchError(SchemaError):
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


class CaseResult(NamedTuple):
    name: str
    passed: bool
    verdict: str
    expected: str
    score_cross: float
    score_x: float
    reason: str


FilterTable = Dict[int, Dict[str, Grid]]


def normalize_label(raw: object) -> str:
    key = str(raw).strip().lower()
    if key not in LABEL_TABLE:
        raise SchemaError("알 수 없는 라벨입니다: %r" % raw)
    return LABEL_TABLE[key]


def extract_size(key: str) -> int:
    parts = key.split("_")
    if len(parts) < 2 or parts[0] != "size":
        raise SchemaError("키 형식 오류: %s" % key)
    try:
        return int(parts[1])
    except ValueError:
        raise SchemaError("키에서 크기를 읽을 수 없습니다: %s" % key)


def safe_size(key: str) -> int:
    try:
        return extract_size(key)
    except SchemaError:
        return -1


def load_filters(raw_filters: object) -> FilterTable:
    if not isinstance(raw_filters, dict):
        raise SchemaError("filters 항목이 없거나 형식이 올바르지 않습니다.")
    filters: FilterTable = {}
    for key in sorted(raw_filters, key=safe_size):
        try:
            size = extract_size(key)
            pair: Dict[str, Grid] = {}
            for label_key, rows in raw_filters[key].items():
                grid = Grid.from_rows(rows)
                if grid.size != size:
                    raise SizeMismatchError(
                        "%s 필터 크기 불일치: 키 %d, 실제 %d" % (key, size, grid.size)
                    )
                pair[normalize_label(label_key)] = grid
            missing = [label for label in (CROSS, X) if label not in pair]
            if missing:
                raise SchemaError("%s 필터 누락: %s" % (key, ", ".join(missing)))
        except (SchemaError, AttributeError, TypeError) as error:
            print("✗ %s 필터 로드 실패 (%s)" % (key, error))
            continue
        filters[size] = pair
        print("✓ %-8s 필터 로드 완료 (%s, %s)" % (key, CROSS, X))
    return filters


def evaluate_case(name: str, raw_case: object, filters: FilterTable) -> CaseResult:
    try:
        if not isinstance(raw_case, dict) or "input" not in raw_case or "expected" not in raw_case:
            raise SchemaError("input/expected 키가 필요합니다.")
        size = extract_size(name)
        expected = normalize_label(raw_case["expected"])
        pattern = Grid.from_rows(raw_case["input"])
        if pattern.size != size:
            raise SizeMismatchError(
                "패턴 크기 불일치: 키 %d, 실제 %d" % (size, pattern.size)
            )
        if size not in filters:
            raise SchemaError("size_%d 필터를 찾을 수 없습니다." % size)
        filter_pair = filters[size]
        score_cross = mac(pattern, filter_pair[CROSS])
        score_x = mac(pattern, filter_pair[X])
    except SchemaError as error:
        return CaseResult(name, False, "ERROR", "-", 0.0, 0.0, str(error))

    verdict = decide(score_cross, score_x)
    if verdict == expected:
        return CaseResult(name, True, verdict, expected, score_cross, score_x, "")
    if verdict == UNDECIDED:
        reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
    else:
        reason = "판정 %s != expected %s" % (verdict, expected)
    return CaseResult(name, False, verdict, expected, score_cross, score_x, reason)


def print_case_result(result: CaseResult) -> None:
    print("--- %s ---" % result.name)
    if result.verdict == "ERROR":
        print("FAIL (%s)" % result.reason)
        return
    print("%s 점수: %r" % (CROSS, result.score_cross))
    print("%s 점수: %r" % (X, result.score_x))
    verdict_line = "판정: %s | expected: %s | %s" % (
        result.verdict,
        result.expected,
        "PASS" if result.passed else "FAIL",
    )
    if not result.passed:
        verdict_line += " (%s)" % result.reason
    print(verdict_line)


def print_summary(results: Sequence[CaseResult]) -> None:
    failures = [result for result in results if not result.passed]
    print("총 테스트: %d개" % len(results))
    print("통과: %d개" % (len(results) - len(failures)))
    print("실패: %d개" % len(failures))
    if failures:
        print("실패 케이스:")
        for result in failures:
            print("- %s: %s" % (result.name, result.reason))


def collect_performance(filters: FilterTable, patterns: Dict[str, object]) -> List[Tuple[int, float]]:
    measurements = [
        (3, measure_mac_ms(Grid.from_rows(X_FILTER_3X3), Grid.from_rows(CROSS_FILTER_3X3)))
    ]
    for size in sorted(filters):
        filter_grid = filters[size][CROSS]
        pattern = filter_grid
        for name, raw_case in patterns.items():
            try:
                if extract_size(name) != size:
                    continue
                candidate = Grid.from_rows(raw_case["input"])
            except (SchemaError, KeyError, TypeError):
                continue
            if candidate.size == size:
                pattern = candidate
                break
        measurements.append((size, measure_mac_ms(pattern, filter_grid)))
    return measurements


def run_json_mode(path: str = DATA_PATH) -> None:
    try:
        with open(path, encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError) as error:
        print("data.json을 읽을 수 없습니다: %s" % error)
        return

    print_section("[1] 필터 로드")
    try:
        filters = load_filters(data.get("filters") if isinstance(data, dict) else None)
    except SchemaError as error:
        print("필터 로드 실패: %s" % error)
        return

    patterns = data.get("patterns") if isinstance(data, dict) else None
    if not isinstance(patterns, dict):
        print("patterns 항목이 없거나 형식이 올바르지 않습니다.")
        return

    print_section("[2] 패턴 분석 (라벨 정규화 적용)")
    results: List[CaseResult] = []
    for name in patterns:
        result = evaluate_case(name, patterns[name], filters)
        results.append(result)
        print_case_result(result)

    print_section("[3] 성능 분석 (평균/%d회)" % PERF_REPEAT)
    print_performance_table(collect_performance(filters, patterns))

    print_section("[4] 결과 요약")
    print_summary(results)
