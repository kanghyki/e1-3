import json
import time
from typing import NamedTuple


# ---------------------------------------
# Constants
# ---------------------------------------

EPSILON = 1e-9
PERF_REPEAT = 10
DATA_PATH = "data.json"

CROSS = "Cross"
X = "X"
UNDECIDED = "UNDECIDED"

LABEL_TABLE = {"+": CROSS, "cross": CROSS, "x": X}

MIN_FILTERS_PER_SIZE = 2
BASELINE_3X3: list[list[float]] = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]


# ---------------------------------------
# Errors
# ---------------------------------------


class SchemaError(Exception):
    pass


class SizeMismatchError(SchemaError):
    pass


# ---------------------------------------
# Core operations
# ---------------------------------------


class Grid:
    def __init__(self, size: int) -> None:
        if size <= 0:
            raise SchemaError("크기는 1 이상이어야 합니다.")
        self.size: int = size
        self._cells: list[list[float]] = [[0.0] * size for _ in range(size)]

    @classmethod
    def from_rows(cls, rows: object) -> "Grid":
        if not isinstance(rows, list):
            raise SchemaError("2차원 배열이 아닙니다.")
        size = len(rows)
        checked_rows: list[list[object]] = []
        for row in rows:
            if not isinstance(row, list):
                raise SchemaError("2차원 배열이 아닙니다.")
            if len(row) != size:
                raise SizeMismatchError(
                    f"정사각 배열이 아닙니다: 행 {size}개, 열 {len(row)}개"
                )
            checked_rows.append(row)
        grid = cls(size)
        for r in range(size):
            for c in range(size):
                value = checked_rows[r][c]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise SchemaError(f"숫자가 아닌 값이 있습니다: {value!r}")
                grid.set(r, c, float(value))
        return grid

    def get(self, r: int, c: int) -> float:
        return self._cells[r][c]

    def set(self, r: int, c: int, value: float) -> None:
        self._cells[r][c] = value

    def row(self, r: int) -> list[float]:
        return self._cells[r]


def ensure_same_size(pattern: Grid, filter_grid: Grid) -> None:
    if pattern.size != filter_grid.size:
        raise SizeMismatchError(
            f"크기 불일치: 패턴 {pattern.size}x{pattern.size}, "
            f"필터 {filter_grid.size}x{filter_grid.size}"
        )


def mac(pattern: Grid, filter_grid: Grid) -> float:
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


def decide(scores: dict[str, float]) -> str:
    best = max(scores.values())
    leaders = [label for label, score in scores.items() if abs(score - best) < EPSILON]
    return leaders[0] if len(leaders) == 1 else UNDECIDED


def measure_mac_ms(pattern: Grid, filter_grid: Grid, repeat: int = PERF_REPEAT) -> float:
    ensure_same_size(pattern, filter_grid)
    start = time.perf_counter()
    for _ in range(repeat):
        mac(pattern, filter_grid)
    elapsed = time.perf_counter() - start
    return elapsed * 1000 / repeat


# ---------------------------------------
# Shared output
# ---------------------------------------


def print_section(title: str) -> None:
    print()
    print("#" + "-" * 39)
    print("# " + title)
    print("#" + "-" * 39)


def print_performance_table(measurements: list[tuple[int, float]]) -> None:
    print("크기        평균 시간(ms)      연산 횟수")
    print("-" * 40)
    for size, avg_ms in measurements:
        label = f"{size}x{size}"
        print(f"{label:<12}{avg_ms:<18.4f}{size * size}")


# ---------------------------------------
# Mode 1: user input
# ---------------------------------------


def print_grid(grid: Grid) -> None:
    for r in range(grid.size):
        print("  " + " ".join(repr(value) for value in grid.row(r)))


def parse_row(line: str, size: int) -> list[float]:
    tokens = line.split()
    if len(tokens) != size:
        raise ValueError(
            f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요."
        )
    values: list[float] = []
    for token in tokens:
        try:
            values.append(float(token))
        except ValueError:
            raise ValueError(f"입력 형식 오류: 숫자로 읽을 수 없는 값입니다 ({token})")
    return values


def read_grid(title: str, size: int) -> Grid:
    while True:
        print(f"{title} ({size}줄 입력, 공백 구분)")
        rows: list[list[float]] = []
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
    print(f"A 점수: {score_a!r}")
    print(f"B 점수: {score_b!r}")
    print(f"연산 시간(평균/{PERF_REPEAT}회): {avg_ms:.4f} ms")
    result = compare_scores(score_a, score_b)
    if result == 0:
        print(f"판정: 판정 불가 (|A-B| < {EPSILON:g})")
    else:
        print(f"판정: {'A' if result > 0 else 'B'}")

    print_section(f"[4] 성능 분석 (평균/{PERF_REPEAT}회)")
    print_performance_table([(size, avg_ms)])


# ---------------------------------------
# Mode 2: data.json analysis
# ---------------------------------------


class CaseResult(NamedTuple):
    name: str
    passed: bool
    verdict: str
    expected: str
    scores: dict[str, float]
    reason: str


class ParsedCase(NamedTuple):
    name: str
    size: int
    pattern: Grid
    expected: str


FilterTable = dict[int, dict[str, Grid]]


def normalize_label(raw: object) -> str:
    key = str(raw).strip().lower()
    if key not in LABEL_TABLE:
        raise SchemaError(f"알 수 없는 라벨입니다: {raw!r}")
    return LABEL_TABLE[key]


def extract_size(key: str) -> int:
    parts = key.split("_")
    if len(parts) < 2 or parts[0] != "size":
        raise SchemaError(f"키 형식 오류: {key}")
    try:
        return int(parts[1])
    except ValueError:
        raise SchemaError(f"키에서 크기를 읽을 수 없습니다: {key}")


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
            entry = raw_filters[key]
            if not isinstance(entry, dict):
                raise SchemaError(f"{key} 필터 형식 오류: 객체가 아닙니다.")
            labelled: dict[str, Grid] = {}
            for label_key, rows in entry.items():
                grid = Grid.from_rows(rows)
                if grid.size != size:
                    raise SizeMismatchError(
                        f"{key} 필터 크기 불일치: 키 {size}, 실제 {grid.size}"
                    )
                labelled[normalize_label(label_key)] = grid
            if len(labelled) < MIN_FILTERS_PER_SIZE:
                raise SchemaError(
                    f"{key} 필터 부족: {len(labelled)}개 "
                    f"({MIN_FILTERS_PER_SIZE}개 이상 필요)"
                )
        except (SchemaError, AttributeError, TypeError) as error:
            print(f"[FAIL] {key} 필터 로드 실패 ({error})")
            continue
        filters[size] = labelled
        print(f"[OK]   {key:<8} 필터 로드 완료 ({', '.join(sorted(labelled))})")
    return filters


def parse_case(name: str, raw_case: object) -> ParsedCase:
    if not isinstance(raw_case, dict) or "input" not in raw_case or "expected" not in raw_case:
        raise SchemaError("input/expected 키가 필요합니다.")
    size = extract_size(name)
    expected = normalize_label(raw_case["expected"])
    pattern = Grid.from_rows(raw_case["input"])
    if pattern.size != size:
        raise SizeMismatchError(
            f"패턴 크기 불일치: 키 {size}, 실제 {pattern.size}"
        )
    return ParsedCase(name, size, pattern, expected)


def error_result(name: str, reason: str) -> CaseResult:
    return CaseResult(name, False, "ERROR", "-", {}, reason)


def evaluate_case(case: ParsedCase, filters: FilterTable) -> CaseResult:
    if case.size not in filters:
        return error_result(case.name, f"size_{case.size} 필터를 찾을 수 없습니다.")
    labelled = filters[case.size]
    scores = {label: mac(case.pattern, labelled[label]) for label in sorted(labelled)}

    verdict = decide(scores)
    if verdict == case.expected:
        return CaseResult(case.name, True, verdict, case.expected, scores, "")
    if verdict == UNDECIDED:
        reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
    else:
        reason = f"판정 {verdict} != expected {case.expected}"
    return CaseResult(case.name, False, verdict, case.expected, scores, reason)


def print_case_result(result: CaseResult) -> None:
    print(f"--- {result.name} ---")
    if result.verdict == "ERROR":
        print(f"FAIL ({result.reason})")
        return
    for label, score in result.scores.items():
        print(f"{label} 점수: {score!r}")
    verdict_line = (
        f"판정: {result.verdict} | expected: {result.expected} | "
        f"{'PASS' if result.passed else 'FAIL'}"
    )
    if not result.passed:
        verdict_line += f" ({result.reason})"
    print(verdict_line)


def collect_performance(filters: FilterTable, cases: list[ParsedCase]) -> list[tuple[int, float]]:
    patterns: dict[int, Grid] = {}
    for case in cases:
        patterns.setdefault(case.size, case.pattern)
    baseline = Grid.from_rows(BASELINE_3X3)
    measurements = [(3, measure_mac_ms(baseline, baseline))]
    for size in sorted(filters):
        filter_grid = filters[size][min(filters[size])]
        pattern = patterns.get(size, filter_grid)
        measurements.append((size, measure_mac_ms(pattern, filter_grid)))
    return sorted(measurements)


def print_summary(results: list[CaseResult]) -> None:
    failures = [result for result in results if not result.passed]
    print(f"총 테스트: {len(results)}개")
    print(f"통과: {len(results) - len(failures)}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("실패 케이스:")
        for result in failures:
            print(f"- {result.name}: {result.reason}")


def run_json_mode(path: str = DATA_PATH) -> None:
    try:
        with open(path, encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"data.json을 읽을 수 없습니다: {error}")
        return

    print_section("[1] 필터 로드")
    try:
        filters = load_filters(data.get("filters") if isinstance(data, dict) else None)
    except SchemaError as error:
        print(f"필터 로드 실패: {error}")
        return

    patterns = data.get("patterns") if isinstance(data, dict) else None
    if not isinstance(patterns, dict):
        print("patterns 항목이 없거나 형식이 올바르지 않습니다.")
        return

    print_section("[2] 패턴 분석 (라벨 정규화 적용)")
    results: list[CaseResult] = []
    cases: list[ParsedCase] = []
    for name in patterns:
        try:
            case = parse_case(name, patterns[name])
        except SchemaError as error:
            result = error_result(name, str(error))
        else:
            cases.append(case)
            result = evaluate_case(case, filters)
        results.append(result)
        print_case_result(result)

    print_section(f"[3] 성능 분석 (평균/{PERF_REPEAT}회)")
    print_performance_table(collect_performance(filters, cases))

    print_section("[4] 결과 요약")
    print_summary(results)


# ---------------------------------------
# Entry point
# ---------------------------------------


def choose_mode() -> str:
    while True:
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        choice = input("선택: ").strip()
        if choice in ("1", "2"):
            return choice
        print("1 또는 2 중에서 선택하세요.")


def main() -> None:
    print("=== Mini NPU Simulator ===")
    try:
        if choose_mode() == "1":
            run_user_input_mode()
        else:
            run_json_mode()
    except (EOFError, KeyboardInterrupt):
        print()
        print("입력이 종료되어 프로그램을 종료합니다.")


if __name__ == "__main__":
    main()
