from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RequestLog:
    request_id: str
    timestamp: str
    provider: str
    model: str
    complexity: str        # "simple" or "complex"
    input_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    is_fallback: bool
    error: str | None = None


@dataclass
class SessionStats:
    logs: list = field(default_factory=list)

    def add(self, log: RequestLog) -> None:
        self.logs.append(log)

    def print_summary(self) -> None:
        successful = [l for l in self.logs if not l.error]
        failed     = [l for l in self.logs if l.error]
        fallbacks  = [l for l in successful if l.is_fallback]
        simple     = [l for l in successful if l.complexity == "simple"]
        complex_   = [l for l in successful if l.complexity == "complex"]

        print("\n" + "=" * 40)
        print("SESSION SUMMARY")
        print("=" * 40)

        if not successful:
            print("No successful requests this session.")
            return

        total_tokens = sum(l.input_tokens + l.output_tokens for l in successful)
        total_cost   = sum(l.estimated_cost_usd for l in successful)
        avg_latency  = sum(l.latency_ms for l in successful) / len(successful)

        provider_counts: dict[str, int] = {}
        for l in successful:
            provider_counts[l.provider] = provider_counts.get(l.provider, 0) + 1

        print(f"Requests     : {len(successful)} successful, {len(failed)} failed")
        print(f"Routing      : {len(simple)} simple, {len(complex_)} complex")
        print(f"Total tokens : {total_tokens:,}")
        print(f"Total cost   : ${total_cost:.5f}")
        print(f"Avg latency  : {avg_latency:.0f} ms")
        print(f"Providers    : {', '.join(f'{p}={c}' for p, c in provider_counts.items())}")
        print(f"Fallbacks    : {len(fallbacks)}")
        print("=" * 40)
