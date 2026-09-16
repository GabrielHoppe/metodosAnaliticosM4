#!/usr/bin/env python3
"""Simulador de eventos discretos para redes de filas em tandem."""

from __future__ import annotations

import argparse
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


class LCG:
    def __init__(
        self,
        seed: int = 1,
        modulus: int = 2**32,
        multiplier: int = 1664525,
        increment: int = 1013904223,
    ) -> None:
        self.state = seed % modulus
        self.modulus = modulus
        self.multiplier = multiplier
        self.increment = increment

    def next(self) -> float:
        self.state = (
            self.multiplier * self.state + self.increment
        ) % self.modulus
        return self.state / self.modulus


@dataclass
class Queue:
    """Estado e parâmetros de uma fila, incluindo seus servidores."""

    arrival_min: Optional[float]
    arrival_max: Optional[float]
    service_min: float
    service_max: float
    servers_count: int
    capacity: int
    customers: int = 0
    losses: int = 0
    state_time: List[float] = field(init=False)
    waiting: int = 0
    server_end_times: List[Optional[float]] = field(init=False)

    def __post_init__(self) -> None:
        if self.capacity < 0 or self.servers_count < 1:
            raise ValueError("capacidade deve ser >= 0 e servidores deve ser >= 1")
        if self.service_min > self.service_max:
            raise ValueError("service_min deve ser menor ou igual a service_max")
        if self.arrival_min is not None and (
            self.arrival_max is None or self.arrival_min > self.arrival_max
        ):
            raise ValueError("intervalo de chegada inválido")
        self.state_time = [0.0] * (self.capacity + 1)
        self.server_end_times = [None] * self.servers_count

    def status(self) -> int:
        return self.customers

    def has_idle_server(self) -> bool:
        return any(end is None for end in self.server_end_times)

    def idle_server(self) -> int:
        for index, end_time in enumerate(self.server_end_times):
            if end_time is None:
                return index
        raise RuntimeError("não há servidor livre")


@dataclass(frozen=True)
class Event:
    time: float
    sequence: int
    kind: str
    queue_index: int
    server_index: Optional[int] = None

    def priority(self) -> Tuple[float, int]:
        return self.time, self.sequence


class Scheduler:
    def __init__(self) -> None:
        self._events: List[Tuple[Tuple[float, int], Event]] = []
        self._sequence = 0

    def schedule(
        self,
        time: float,
        kind: str,
        queue_index: int,
        server_index: Optional[int] = None,
    ) -> None:
        event = Event(
            time=time,
            sequence=self._sequence,
            kind=kind,
            queue_index=queue_index,
            server_index=server_index,
        )
        self._sequence += 1
        heapq.heappush(self._events, (event.priority(), event))

    def next(self) -> Event:
        if not self._events:
            raise RuntimeError("escalonador vazio")
        return heapq.heappop(self._events)[1]

    def __bool__(self) -> bool:
        return bool(self._events)


class NetworkSimulator:
    def __init__(
        self,
        queues: Sequence[Queue],
        routes: Dict[int, Sequence[Tuple[int, float]]],
        *,
        first_arrival: float = 2.5,
        max_randoms: int = 100_000,
        seed: int = 1,
    ) -> None:
        if not queues:
            raise ValueError("a rede deve possuir ao menos uma fila")
        self.queues = list(queues)
        self.routes = {source: list(destinations) for source, destinations in routes.items()}
        self.first_arrival = first_arrival
        self.max_randoms = max_randoms
        self.rng = LCG(seed=seed)
        self.randoms_used = 0
        self.time = 0.0
        self.scheduler = Scheduler()
        self.scheduler.schedule(first_arrival, "arrival", 0)

    def uniform(self, low: float, high: float) -> float:
        if self.randoms_used >= self.max_randoms:
            raise StopIteration("limite de aleatórios atingido")
        self.randoms_used += 1
        return low + (high - low) * self.rng.next()

    def service_end(self, queue_index: int) -> float:
        queue = self.queues[queue_index]
        return self.time + self.uniform(queue.service_min, queue.service_max)

    def schedule_external_arrival(self) -> None:
        queue = self.queues[0]
        if queue.arrival_min is None or self.randoms_used >= self.max_randoms:
            return
        arrival = self.time + self.uniform(queue.arrival_min, queue.arrival_max)  # type: ignore[arg-type]
        self.scheduler.schedule(arrival, "arrival", 0)

    def start_service(self, queue_index: int, server_index: int) -> None:
        queue = self.queues[queue_index]
        end_time = self.service_end(queue_index)
        queue.server_end_times[server_index] = end_time
        kind = "passage" if queue_index in self.routes else "departure"
        self.scheduler.schedule(end_time, kind, queue_index, server_index)

    def admit(self, queue_index: int) -> None:
        queue = self.queues[queue_index]
        if queue.customers >= queue.capacity:
            queue.losses += 1
            return
        queue.customers += 1
        if queue.has_idle_server():
            self.start_service(queue_index, queue.idle_server())
        else:
            queue.waiting += 1

    def release_server(self, queue_index: int, server_index: int) -> None:
        queue = self.queues[queue_index]
        queue.server_end_times[server_index] = None
        queue.customers -= 1
        if queue.waiting:
            queue.waiting -= 1
            self.start_service(queue_index, server_index)

    def route_customer(self, source_index: int) -> None:
        destinations = self.routes.get(source_index, ())
        if not destinations:
            return
        selected = destinations[0][0]
        if len(destinations) > 1:
            draw = self.rng.next()
            self.randoms_used += 1
            cumulative = 0.0
            for destination, probability in destinations:
                cumulative += probability
                if draw < cumulative:
                    selected = destination
                    break
        self.admit(selected)

    def advance(self, event_time: float) -> None:
        if event_time < self.time:
            raise ValueError("evento anterior ao tempo atual")
        elapsed = event_time - self.time
        for queue in self.queues:
            queue.state_time[queue.customers] += elapsed
        self.time = event_time

    def handle(self, event: Event) -> None:
        if event.kind == "arrival":
            self.admit(event.queue_index)
            self.schedule_external_arrival()
        elif event.kind == "passage":
            assert event.server_index is not None
            self.release_server(event.queue_index, event.server_index)
            self.route_customer(event.queue_index)
        elif event.kind == "departure":
            assert event.server_index is not None
            self.release_server(event.queue_index, event.server_index)
        else:
            raise RuntimeError(f"evento desconhecido: {event.kind}")

    def run(self) -> Dict[str, object]:
        while self.randoms_used < self.max_randoms and self.scheduler:
            event = self.scheduler.next()
            self.advance(event.time)
            self.handle(event)
        results = []
        for queue in self.queues:
            probabilities = [
                duration / self.time if self.time else 0.0
                for duration in queue.state_time
            ]
            results.append(
                {
                    "tempo_acumulado": [round(value, 6) for value in queue.state_time],
                    "probabilidades": [round(value, 6) for value in probabilities],
                    "perdas": queue.losses,
                }
            )
        return {
            "tempo_total": self.time,
            "aleatorios_usados": self.randoms_used,
            "filas": results,
        }


def validation_simulation(
    seed: int = 1,
    first_arrival: float = 2.5,
    max_randoms: int = 100_000,
) -> NetworkSimulator:
    queues = [
        Queue(1.0, 5.0, 4.0, 5.0, 2, 3),
        Queue(None, None, 1.0, 3.0, 1, 5),
    ]
    return NetworkSimulator(
        queues,
        {0: [(1, 1.0)]},
        first_arrival=first_arrival,
        max_randoms=max_randoms,
        seed=seed,
    )


def print_result(result: Dict[str, object]) -> None:
    print(f"Tempo total da simulação: {result['tempo_total']:.6f}")
    print(f"Aleatórios usados: {result['aleatorios_usados']}")
    for index, queue_result in enumerate(result["filas"], start=1):
        print(f"\nFila {index}:")
        print(f"  Clientes perdidos: {queue_result['perdas']}")
        print("  Tempos acumulados por estado:")
        for state, value in enumerate(queue_result["tempo_acumulado"]):
            print(f"    Estado {state}: {value:.6f}")
        print("  Probabilidades por estado:")
        for state, value in enumerate(queue_result["probabilidades"]):
            print(f"    Estado {state}: {value:.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador de filas em tandem")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--first-arrival", type=float, default=2.5)
    parser.add_argument("--max-randoms", type=int, default=100_000)
    args = parser.parse_args()
    print_result(
        validation_simulation(
            seed=args.seed,
            first_arrival=args.first_arrival,
            max_randoms=args.max_randoms,
        ).run()
    )


if __name__ == "__main__":
    main()
