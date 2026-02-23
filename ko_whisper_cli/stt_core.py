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

_model_cache: dict = {}


def get_model(
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
) -> WhisperModel:
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
    vad_parameters: dict | None = None,
    initial_prompt: str | None = None,
):
    """오디오 파일을 한국어 텍스트로 변환한다.

    Returns:
        tuple[str, TranscriptionInfo]: (변환된 텍스트, faster-whisper TranscriptionInfo)
    """
    if vad_parameters is None:
        vad_parameters = DEFAULT_VAD_PARAMETERS

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
