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
