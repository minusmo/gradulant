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
)


@click.command()
@click.argument("audio_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="출력 파일 경로 (기본: <원본명>.txt)",
)
@click.option(
    "--prompt",
    default=DEFAULT_INITIAL_PROMPT,
    show_default=True,
    help="Whisper initial_prompt에 전달할 한국어 문자열",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL_NAME,
    show_default=True,
    help="모델 이름 (large-v3, large-v3-turbo, medium, small 등)",
)
@click.option(
    "--device",
    default=DEFAULT_DEVICE,
    show_default=True,
    help="추론 디바이스 (mps, cpu, cuda)",
)
@click.option(
    "--compute-type",
    default=DEFAULT_COMPUTE_TYPE,
    show_default=True,
    help="compute_type (float16, int8, float32 등)",
)
@click.option(
    "--beam-size",
    default=DEFAULT_BEAM_SIZE,
    show_default=True,
    type=int,
    help="beam search 폭",
)
@click.option(
    "--best-of",
    default=DEFAULT_BEST_OF,
    show_default=True,
    type=int,
    help="temperature > 0 일 때 샘플링 횟수",
)
@click.option(
    "--temperature",
    default=DEFAULT_TEMPERATURE,
    show_default=True,
    type=float,
    help="샘플링 temperature (0.0 = greedy)",
)
@click.option(
    "--no-vad",
    is_flag=True,
    default=False,
    help="VAD 필터 비활성화",
)
def main(
    audio_path: str,
    output: str | None,
    prompt: str,
    model: str,
    device: str,
    compute_type: str,
    beam_size: int,
    best_of: int,
    temperature: float,
    no_vad: bool,
) -> None:
    """한국어 오디오 파일을 텍스트로 변환한다 (faster-whisper 기반).

    AUDIO_PATH: 변환할 오디오 파일 (m4a, wav, mp3 등)
    """
    audio = Path(audio_path)

    out_path = Path(output) if output else audio.with_suffix(".txt")

    vad_filter = not no_vad

    click.echo(f"[STT] {audio.name} 변환 시작 (model={model}, device={device}) ...")

    text, info = transcribe_file(
        str(audio),
        model_name=model,
        device=device,
        compute_type=compute_type,
        beam_size=beam_size,
        best_of=best_of,
        temperature=temperature,
        vad_filter=vad_filter,
        initial_prompt=prompt,
    )

    out_path.write_text(text, encoding="utf-8")

    click.echo(
        f"[OK] {audio.name} → {out_path} "
        f"(lang={info.language}, p={info.language_probability:.2f})"
    )


if __name__ == "__main__":
    main()
