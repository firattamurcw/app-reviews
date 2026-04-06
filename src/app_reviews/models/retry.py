"""Retry configuration model."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """HTTP retry and timeout settings."""

    max_retries: int = 3
    backoff_factor: float = 0.5
    timeout: float = 30.0
    retry_on: list[int] = field(default_factory=lambda: [429, 503])

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.backoff_factor < 0:
            raise ValueError("backoff_factor must be >= 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
