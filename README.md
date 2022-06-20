# judge script for CPII problem 359 - 快篩預購 app

## Links

- [Problem](https://v2.noj.tw/course/110-Computer-Programming-II/problem/359)
- Sample testcase is avaliable [here](https://idocntnu-my.sharepoint.com/:u:/g/personal/40747019s_eduad_ntnu_edu_tw/EZ2oBYJGLDdDhYPZCo2zvwYB10kZqh5QCcvw_YFuoiCm3Q?e=2CPWzz).
  You should extract this to `./testcase`.

## Testcase Structure

本題測資目錄結構如下：

```
xxxx.in                # 編號 xxxx 的輸入
├── 1665.log
├── 1665.update
├── mask.info
└── stdin              # 標準輸入，i.e. 一個整數 + 一堆名字
```

`xxxx.out` 為預期的結果，其中 `stdout` 為標準輸出。

## Cheatsheet

```bash
poetry run python judge.py -vv judge-one <your submission script>
# e.g. poetry run python judge.py -vv judge-one my-main.c
```

The output is like following:

```
Run submission my-main.c
Case #0: AC
Case #1: AC
Case #2: AC
Case #3: AC
Case #4: AC
Case #5: AC
Case #6: AC
Case #7: AC
Case #8: AC
Case #9: AC
Total score: 100
```

## Run Locally

### Requirements

- [Poetry](https://python-poetry.org/)

### Install dependency

```bash
poetry install
```

### Execute

```bash
poetry run python judge.py --help
```

## Run with Docker

### Requirements

- [Docker](https://python-poetry.org/)
- [Docker Compose](https://docs.docker.com/compose/)

### Build

```bash
docker-compose build
```

### Execute

```bash
docker-compose run --rm judger --help
```
