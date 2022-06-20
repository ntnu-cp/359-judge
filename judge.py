import os
import shutil
import subprocess
import tempfile
import json
import enum
from typing import IO, List, Generator
from dataclasses import dataclass
from pathlib import Path
import click

submission_root = Path('submissions')
testcase_root = Path('testcase')
verbose = 0


class TestcaseResult(str, enum.Enum):
    AC = 'AC'
    WA = 'WA'
    WA_INFO_LEN_NE = 'WA-INFO-LEN-NE'
    WA_NATION_MISSING = 'WA-NATION-MISSING'
    WA_NATION_INFO = 'WA-NATION-INFO'
    WA_LOG_MISSING = 'WA-LOG-MISSING'
    RE = 'RE'
    TLE = 'TLE'
    JE = 'JE'


@dataclass
class Nation:
    name: str
    id: int
    last_update: int
    current_d: int

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Nation':
        NAME_LEN = 128
        assert len(data) == (NAME_LEN + 4 + 4 + 4)
        name = data[:NAME_LEN].rstrip(b'\x00').decode()
        id = int.from_bytes(data[NAME_LEN:NAME_LEN + 4], 'little')
        last_update = int.from_bytes(data[NAME_LEN + 4:NAME_LEN + 8], 'little')
        current_d = int.from_bytes(data[NAME_LEN + 8:NAME_LEN + 12], 'little')
        return cls(
            name=name,
            id=id,
            last_update=last_update,
            current_d=current_d,
        )

    @classmethod
    def parse_mask_info(cls, fp: IO[bytes]) -> List['Nation']:
        NAME_LEN = 128
        STRUCT_LEN = (NAME_LEN + 4 + 4 + 4)
        data = fp.read()
        assert len(data) % STRUCT_LEN == 0
        return [
            cls.from_bytes(data[i:i + STRUCT_LEN])
            for i in range(0, len(data), STRUCT_LEN)
        ]


def get_score(code: Path) -> int:
    try:
        exe_path = compile(code)
    except subprocess.CalledProcessError:
        if verbose > 1:
            print(f'Compile error {code}')
        return 0
    if verbose:
        score = 0
        results = collect_results(exe_path)
        print(f'Run submission {code}')
        for i, s in enumerate(results):
            print(f'Case #{i}: {s}')
            if s == TestcaseResult.AC:
                score += 10
    else:
        results = collect_results(exe_path)
        score = sum(10 for r in results if r == TestcaseResult.AC)
    return score


def collect_results(exe_path: Path) -> Generator[TestcaseResult, None, None]:
    for i in range(10):
        testcase_pat = f'{i:02d}00'
        yield run_testcase(exe_path, testcase_pat)


def compile(code: Path) -> Path:
    tmp_file = tempfile.NamedTemporaryFile('wb', delete=False)
    subprocess.check_call(
        ['gcc', str(code), '-o', tmp_file.name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return Path(tmp_file.name)


def run_testcase(exe_path: Path, testcase_pat: str) -> TestcaseResult:
    student_exe_name = 'main'
    with tempfile.TemporaryDirectory() as sandbox:
        sandbox = Path(sandbox)
        testcase_dir = testcase_root / (testcase_pat + '.in')
        # Copy input
        for f in testcase_dir.iterdir():
            shutil.copy(f, sandbox)
        shutil.copy(exe_path, sandbox / student_exe_name)
        os.unlink(sandbox / 'stdin')
        try:
            subprocess.check_call(
                f'./{student_exe_name}',
                cwd=sandbox,
                timeout=30,
                stdin=(testcase_dir / 'stdin').open(),
                stdout=(sandbox / 'stdout').open('w'),
                stderr=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return TestcaseResult.TLE
        except subprocess.CalledProcessError:
            # Some programs might return non-0 exit code even if they exit normally
            #return TestcaseResult.RE
            pass
        ans_dir = testcase_dir.with_suffix('.out')
        try:
            ans_output = (ans_dir / 'stdout').read_text()
            student_output = (sandbox / 'stdout').read_text()
        except (UnicodeDecodeError, FileNotFoundError):
            return TestcaseResult.WA
        if not cmp_text(ans_output, student_output):
            return TestcaseResult.WA
        try:
            return cmp_out_dir(ans_dir, sandbox)
        except AssertionError:
            return TestcaseResult.JE


def cmp_out_dir(ans_dir: Path, student_dir: Path) -> TestcaseResult:
    assert ans_dir.is_dir()
    assert student_dir.is_dir()
    ans_mask_info = (ans_dir / 'mask.info').open('rb')
    ans_mask_info = Nation.parse_mask_info(ans_mask_info)
    student_mask_info = (student_dir / 'mask.info').open('rb')
    student_mask_info = Nation.parse_mask_info(student_mask_info)
    if len(ans_mask_info) != len(student_mask_info):
        return TestcaseResult.WA_INFO_LEN_NE
    ans_mask_info = {nation.name: nation for nation in ans_mask_info}
    student_mask_info = {nation.name: nation for nation in student_mask_info}
    for name, a_nation in ans_mask_info.items():
        if (s_nation := student_mask_info.get(name)) is None:
            return TestcaseResult.WA_NATION_MISSING
        if a_nation != s_nation:
            return TestcaseResult.WA_NATION_INFO
        a_log = (ans_dir / f'{a_nation.id}.log')
        s_log = (ans_dir / f'{s_nation.id}.log')
        assert a_log.exists()
        if not s_log.exists():
            return TestcaseResult.WA_LOG_MISSING
        if not cmp_n_bit(
                a_log.read_bytes(),
                s_log.read_bytes(),
                a_nation.last_update,
        ):
            return TestcaseResult.WA
    return TestcaseResult.AC


def cmp_n_bit(a: bytes, b: bytes, n: int) -> bool:
    n_bytes = n // 8 + int(n % 8 > 0)
    if len(a) < n_bytes or len(b) < n_bytes:
        print(len(a), len(b), n_bytes, n)
        return False
    if any(a[i] != b[i] for i in range(n // 8)):
        return False
    if (extra_len := n % 8) == 0:
        return True
    a_last = a[n // 8] >> (8 - extra_len)
    b_last = b[n // 8] >> (8 - extra_len)
    return a_last == b_last


def cmp_text(a: str, b: str) -> bool:
    return preprocess_output(a) == preprocess_output(b)


def preprocess_output(s: str) -> str:
    s = s.splitlines()
    s = '\n'.join(l.rstrip() for l in s).rstrip()
    return s


@click.group()
@click.option('_verbose', '-v', '--verbose', count=True)
def main(_verbose: int):
    global verbose
    verbose = _verbose


@main.command()
@click.argument(
    'submission',
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
)
def judge_one(submission: Path):
    '''
    Judge single submission
    '''
    score = get_score(submission)
    if verbose:
        print(f'Total score: {score}')
    else:
        print(score)


@main.command()
def judge_all():
    '''
    Judge all submissions
    '''
    scores = {}
    for user in submission_root.iterdir():
        if verbose:
            print(f'Start {user}')
        scores[user.name] = max(get_score(d) for d in user.iterdir())
    print(json.dumps(scores))


if __name__ == '__main__':
    main()
