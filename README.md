# ko-whisper-cli

M1 맥 로컬에서 한국어 오디오 파일을 텍스트로 변환하는 CLI 툴.
엔진: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) + Whisper large-v3

---

## 요구사항

- macOS (M1/M1 Pro 권장)
- Python 3.10 이상
- ffmpeg (오디오 디코딩)

```bash
brew install ffmpeg
```

---

## 설치

```bash
# 저장소 클론 후 가상환경 생성
python -m venv .venv
source .venv/bin/activate

# 개발 모드 설치 (ko-stt 커맨드 등록)
pip install -e .
```

첫 실행 시 모델이 자동으로 다운로드됩니다 (~3GB for large-v3).

---

## 사용법

```bash
# 기본 사용 (출력: input.txt)
ko-stt input.m4a

# 출력 경로 지정
ko-stt input.m4a -o meeting.txt

# 초기 프롬프트 지정 (도메인 힌트)
ko-stt input.m4a --prompt "다음은 개발자 스탠드업 미팅 녹취록입니다:"

# 모델/디바이스 선택
ko-stt input.m4a --model large-v3-turbo --device mps

# VAD 비활성화
ko-stt input.m4a --no-vad
```

### 전체 옵션

```
Usage: ko-stt [OPTIONS] AUDIO_PATH

  한국어 오디오 파일을 텍스트로 변환한다 (faster-whisper 기반).

  AUDIO_PATH: 변환할 오디오 파일 (m4a, wav, mp3 등)

Options:
  -o, --output PATH        출력 파일 경로 (기본: <원본명>.txt)
  --prompt TEXT            Whisper initial_prompt에 전달할 한국어 문자열
                           [default: 다음은 회의 녹취록입니다:\n]
  --model TEXT             모델 이름 (large-v3, large-v3-turbo, medium, small 등)
                           [default: large-v3]
  --device TEXT            추론 디바이스 (mps, cpu, cuda)  [default: mps]
  --compute-type TEXT      compute_type (float16, int8, float32 등)
                           [default: float16]
  --beam-size INTEGER      beam search 폭  [default: 5]
  --best-of INTEGER        temperature > 0 일 때 샘플링 횟수  [default: 5]
  --temperature FLOAT      샘플링 temperature (0.0 = greedy)  [default: 0.0]
  --no-vad                 VAD 필터 비활성화
  --help                   Show this message and exit.
```

---

## 지원 오디오 포맷

ffmpeg이 지원하는 모든 포맷: m4a, wav, mp3, flac, ogg, aac 등.

---

## 모델 비교

| 모델 | 속도 | 정확도 | VRAM |
|------|------|--------|------|
| `large-v3` | 느림 | 최고 | ~10GB |
| `large-v3-turbo` | 빠름 | 높음 | ~6GB |
| `medium` | 매우 빠름 | 중간 | ~5GB |
| `small` | 최고 빠름 | 낮음 | ~2GB |

M1 맥에서는 `mps` 디바이스 + `float16` compute_type 조합을 권장합니다.

---

## 향후 계획

- `--srt` / `--vtt` 옵션으로 자막 파일 생성
- 여러 파일 batch 처리: `ko-stt *.m4a`
- 한국어 맞춤법/띄어쓰기 후처리
- macOS Automator/Alfred 워크플로우 연동
