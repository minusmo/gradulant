# 프로젝트 계획: ko-whisper-cli (맥 로컬 한국어 STT CLI)

## 1. 목표

- M1 맥 로컬에서 **녹음 파일(예: m4a, wav, mp3) → 한국어 텍스트**로 변환하는 CLI 툴을 만든다.
- 엔진은 **faster-whisper + Whisper large-v3(or large-v3-turbo)**를 사용한다.[1][2]
- 사용자는 터미널에서 아래와 같이 간단히 사용할 수 있어야 한다.
  - `ko-stt input.m4a`
  - `ko-stt input.m4a -o output.txt`
  - `ko-stt input.m4a --prompt "다음은 개발자 회의 녹취록입니다:\n"`

***

## 2. 기술 스택 및 전제

- OS: macOS (M1/M1 Pro)
- 언어: Python 3.10 이상
- 주요 라이브러리
  - `faster-whisper` (ASR 엔진)[1]
  - `click` (CLI 인터페이스)[3]
- 모델
  - 기본: `large-v3`
  - 선택 옵션: `large-v3-turbo` (속도/메모리 최적화)[2]
- 디바이스
  - 기본: `mps` (Apple Silicon GPU)
  - 옵션: `cpu`, `cuda` (서버 확장 시)

***

## 3. 디렉터리 구조

```text
ko-whisper-cli/
  ├─ .venv/                 # 로컬 가상환경 (gitignore)
  ├─ ko_whisper_cli/
  │   ├─ __init__.py
  │   ├─ cli.py             # click 기반 CLI 엔트리포인트
  │   ├─ stt_core.py        # 모델 로딩 및 transcribe 로직
  │   ├─ config.py          # 기본 설정 값 (모델명, 디바이스 등)
  │   └─ utils.py           # 파일 처리/로그 유틸 (필요시)
  ├─ pyproject.toml         # 패키지/엔트리포인트 정의
  ├─ plan.md                # (현재 파일) 개발 계획
  └─ README.md              # 사용법/설치 가이드
```

***

## 4. 기능 명세

### 4.1 기본 CLI 명령

명령어 이름: `ko-stt`

사용 예:

- `ko-stt input.m4a`
- `ko-stt input.wav -o output.txt`
- `ko-stt input.m4a --prompt "다음은 회의 녹취록입니다:\n"`
- `ko-stt input.m4a --model large-v3-turbo --device mps`

옵션:

- `audio_path` (필수 positional)
  - 변환할 오디오 파일 경로 (m4a, wav, mp3 등).
- `--output, -o` (optional)
  - 출력 텍스트 파일 경로 (기본: `<원본파일명>.txt`).
- `--prompt` (optional, default: `"다음은 회의 녹취록입니다:\n"`)
  - Whisper `initial_prompt`에 전달할 한국어 문자열.[4]
- `--model` (optional, default: `"large-v3"`)
  - `large-v3`, `large-v3-turbo`, `medium`, `small` 등 지정.[5][2]
- `--device` (optional, default: `mps`)
  - `mps`, `cpu`, `cuda` 중 하나.
- `--beam-size` (optional, default: `5`)
- `--best-of` (optional, default: `5`)
- `--temperature` (optional, default: `0.0`)
- `--no-vad` (flag, default: VAD 사용)
  - VAD 비활성화 시 사용하는 플래그.

### 4.2 한국어 최적화 설정

`stt_core.py` 내 기본값:

- `language="ko"` 고정.[4]
- `beam_size=5`, `best_of=5`, `temperature=0.0` (정확도 우선).[4]
- `vad_filter=True`, `vad_parameters={"min_silence_duration_ms": 500}`.[6]
- `condition_on_previous_text=True`.
- `initial_prompt`는 CLI에서 전달받아 그대로 전달.

### 4.3 출력 처리

- Whisper 세그먼트(`segments`)를 순회하여 텍스트를 합친다.
- 기본 구현:
  - `text = " ".join(seg.text.strip() for seg in segments)`
  - 마지막에 `strip()` 후 파일로 저장.
- 향후 확장 가능:
  - SRT/VTT 자막 형식 출력.
  - 줄바꿈 기준(시간/문장부호) 조정.

***

## 5. 구현 단계

### 5.1 환경 세팅

1. 프로젝트 디렉터리 생성 및 가상환경:

   ```bash
   mkdir ko-whisper-cli && cd ko-whisper-cli
   python -m venv .venv
   source .venv/bin/activate
   ```

2. 의존성 설치:

   ```bash
   pip install faster-whisper click
   ```

### 5.2 pyproject.toml 작성

- 패키지 이름, 의존성, 콘솔 스크립트 정의.

```toml
[project]
name = "ko-whisper-cli"
version = "0.1.0"
description = "Korean Whisper STT CLI for macOS"
requires-python = ">=3.10"
dependencies = [
  "faster-whisper",
  "click",
]

[project.scripts]
ko-stt = "ko_whisper_cli.cli:main"
```

### 5.3 config.py

- 기본 설정을 한 곳에 모아둔다.

```python
# ko_whisper_cli/config.py

DEFAULT_MODEL_NAME = "large-v3"          # or "large-v3-turbo"
DEFAULT_DEVICE = "mps"                   # M1 맥 기준
DEFAULT_COMPUTE_TYPE = "float16"         # mps에서 권장
DEFAULT_INITIAL_PROMPT = "다음은 회의 녹취록입니다:\n"

DEFAULT_LANGUAGE = "ko"
DEFAULT_BEAM_SIZE = 5
DEFAULT_BEST_OF = 5
DEFAULT_TEMPERATURE = 0.0

DEFAULT_VAD_FILTER = True
DEFAULT_VAD_PARAMETERS = {"min_silence_duration_ms": 500}
```

### 5.4 stt_core.py

- 모델 로딩 및 transcribe 기능 구현.
- 모델은 모듈 레벨에서 한 번만 로딩하여 재사용.

```python
# ko_whisper_cli/stt_core.py

from faster_whisper import WhisperModel
from .config import (
    DEFAULT_MODEL_NAME,
    DEFAULT_DEVICE,
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_LANGUAGE,
    DEFAULT_BEAM_SIZE,
    DEFAULT_BEST_OF,
    DEFAULT_TEMPERATURE,
    DEFAULT_VAD_FILTER,
    DEFAULT_VAD_PARAMETERS,
)

_model_cache = {}

def get_model(model_name: str = DEFAULT_MODEL_NAME,
              device: str = DEFAULT_DEVICE,
              compute_type: str = DEFAULT_COMPUTE_TYPE) -> WhisperModel:
    key = (model_name, device, compute_type)
    if key not in _model_cache:
        _model_cache[key] = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
    return _model_cache[key]

def transcribe_file(
    audio_path: str,
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: str = DEFAULT_LANGUAGE,
    beam_size: int = DEFAULT_BEAM_SIZE,
    best_of: int = DEFAULT_BEST_OF,
    temperature: float = DEFAULT_TEMPERATURE,
    vad_filter: bool = DEFAULT_VAD_FILTER,
    vad_parameters: dict = DEFAULT_VAD_PARAMETERS,
    initial_prompt: str | None = None,
):
    model = get_model(model_name, device, compute_type)

    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=beam_size,
        best_of=best_of,
        temperature=temperature,
        vad_filter=vad_filter,
        vad_parameters=vad_parameters,
        condition_on_previous_text=True,
        initial_prompt=initial_prompt,
    )

    text = " ".join(seg.text.strip() for seg in segments)
    return text.strip(), info
```

### 5.5 cli.py

- `click` 기반 CLI 엔트리포인트.

```python
# ko_whisper_cli/cli.py

import click
from pathlib import Path
from .stt_core import transcribe_file
from .config import (
    DEFAULT_MODEL_NAME,
    DEFAULT_DEVICE,
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_BEAM_SIZE,
    DEFAULT_BEST_OF,
    DEFAULT_TEMPERATURE,
    DEFAULT_VAD_FILTER,
)

@click.command()
@click.argument("audio_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="출력 파일 경로 (기본: <원본명>.txt)")
@click.option("--prompt", default=DEFAULT_INITIAL_PROMPT, help="초기 프롬프트")
@click.option("--model", default=DEFAULT_MODEL_NAME, help="모델 이름 (large-v3, large-v3-turbo 등)")
@click.option("--device", default=DEFAULT_DEVICE, help="디바이스 (mps, cpu, cuda)")
@click.option("--compute-type", default=DEFAULT_COMPUTE_TYPE, help="compute_type (float16, int8 등)")
@click.option("--beam-size", default=DEFAULT_BEAM_SIZE, show_default=True, type=int)
@click.option("--best-of", default=DEFAULT_BEST_OF, show_default=True, type=int)
@click.option("--temperature", default=DEFAULT_TEMPERATURE, show_default=True, type=float)
@click.option("--no-vad", is_flag=True, help="VAD 필터 비활성화")
def main(
    audio_path,
    output,
    prompt,
    model,
    device,
    compute_type,
    beam_size,
    best_of,
    temperature,
    no_vad,
):
    audio_path = Path(audio_path)

    if output is None:
        output = audio_path.with_suffix(".txt")
    output = Path(output)

    vad_filter = not no_vad

    text, info = transcribe_file(
        str(audio_path),
        model_name=model,
        device=device,
        compute_type=compute_type,
        beam_size=beam_size,
        best_of=best_of,
        temperature=temperature,
        vad_filter=vad_filter,
        initial_prompt=prompt,
    )

    output.write_text(text, encoding="utf-8")

    click.echo(
        f"[OK] {audio_path.name} → {output} "
        f"(model={model}, device={device}, lang={info.language}, p={info.language_probability:.2f})"
    )

if __name__ == "__main__":
    main()
```

***

## 6. 설치 및 사용 플로우

1. 개발 설치:

   ```bash
   pip install -e .
   ```

2. 사용:

   ```bash
   ko-stt meeting.m4a
   ko-stt meeting.m4a -o meeting.txt
   ko-stt meeting.m4a --model large-v3-turbo --device mps
   ko-stt meeting.m4a --prompt "다음은 개발자 스탠드업 미팅 녹취록입니다:\n"
   ```

***

## 7. 확장 아이디어 (후순위)

- 옵션: `--srt`, `--vtt`로 자막 파일 생성 (segments 기반 타임스탬프 활용).[1]
- 간단한 한국어 후처리 모듈 추가
  - 맞춤법/띄어쓰기 교정
  - 도메인 용어 사전 치환
- 여러 파일 batch 처리: `ko-stt *.m4a` 형태 대응 (glob 처리).
- macOS 서비스/Automator/Alfred 워크플로우로 연동:
  - Finder에서 파일 선택 → 서비스 실행 → 텍스트 파일 생성.

출처
[1] Faster Whisper transcription with CTranslate2 - GitHub https://github.com/SYSTRAN/faster-whisper
[2] openai/whisper-large-v3-turbo https://huggingface.co/openai/whisper-large-v3-turbo
[3] 12 Creating a click command line tool https://www.youtube.com/watch?v=Mh0dpKd-RaY
[4] Settings / Parameters documentation #2108 - openai whisper https://github.com/openai/whisper/discussions/2108
[5] openai/whisper-large-v3 - Hugging Face https://huggingface.co/openai/whisper-large-v3
[6] Support for specifying language and diarization · Issue #245 - GitHub https://github.com/guillaumekln/faster-whisper/issues/245
