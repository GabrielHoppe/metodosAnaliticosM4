#!/usr/bin/env python3
"""Simulador de fila G/G/c/K com gerador congruente linear."""

from __future__ import annotations

import argparse
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple


class LCG:
    def __init__(self, seed: int = 1, modulus: int = 2**32, a: int = 1664525, c: int = 1013904223):
        self.state = seed % modulus
        self.modulus = modulus
        self.a = a
        self.c = c

    def next(self) -> float:
        self.state = (self.a * self.state + self.c) % self.modulus
        return self.state / self.modulus


class QueueSimulator:
    def __init__(
        self,
        arrival_min: float,
        arrival_max: float,
        service_min: float,
        service_max: float,
        servers: int,
        capacity: int,
        max_randoms: int = 100_000,
        seed: int = 1,
    ) -> None:
        self.arrival_min = arrival_min
        self.arrival_max = arrival_max
        self.service_min = service_min
        self.service_max = service_max
        self.servers_count = servers
        self.capacity = capacity
        self.max_randoms = max_randoms
        self.rng = LCG(seed=seed)
        self.randoms_used = 0

        self.time = 0.0
        self.system_count = 0
        self.queue: Deque[int] = deque()
        self.servers: List[Optional[float]] = [None] * self.servers_count
        self.next_arrival: Optional[float] = 3.0
        self.lost_customers = 0
        self.state_time: Dict[int, float] = {i: 0.0 for i in range(self.capacity + 1)}

    def draw_uniform(self, low: float, high: float) -> float:
        if self.randoms_used >= self.max_randoms:
            raise StopIteration("Limite de 100.000 aleatórios atingido.")
        value = low + (high - low) * self.rng.next()
        self.randoms_used += 1
        return value

    def has_idle_server(self) -> bool:
        return any(server is None for server in self.servers)

    def first_idle_server(self) -> int:
        for index, server in enumerate(self.servers):
            if server is None:
                return index
        raise RuntimeError("Nenhum servidor livre encontrado.")

    def next_service_end(self) -> Optional[Tuple[float, int]]:
        best_time = None
        best_index = None
        for index, end_time in enumerate(self.servers):
            if end_time is not None and (best_time is None or end_time < best_time):
                best_time = end_time
                best_index = index
        if best_time is None or best_index is None:
            return None
        return best_time, best_index

    def schedule_next_arrival(self) -> None:
        if self.randoms_used >= self.max_randoms:
            self.next_arrival = None
            return
        self.next_arrival = self.time + self.draw_uniform(self.arrival_min, self.arrival_max)

    def start_service_for_server(self, server_index: int) -> None:
        service_time = self.draw_uniform(self.service_min, self.service_max)
        self.servers[server_index] = self.time + service_time

    def handle_arrival(self) -> None:
        if self.system_count >= self.capacity:
            self.lost_customers += 1
            self.schedule_next_arrival()
            return

        self.system_count += 1

        if self.has_idle_server():
            server_index = self.first_idle_server()
            self.start_service_for_server(server_index)
        else:
            self.queue.append(1)

        self.schedule_next_arrival()

    def handle_service_completion(self, server_index: int) -> None:
        self.servers[server_index] = None
        self.system_count -= 1

        if self.queue:
            self.queue.popleft()
            if self.system_count < self.capacity:
                self.start_service_for_server(server_index)

    def advance_time(self, next_time: float) -> None:
        if next_time < self.time:
            raise ValueError("Tempo de evento menor que tempo atual.")
        self.state_time[self.system_count] += next_time - self.time
        self.time = next_time

    def run(self) -> Dict[str, object]:
        while self.randoms_used < self.max_randoms:
            next_arrival_time = self.next_arrival
            next_service = self.next_service_end()

            if next_arrival_time is None and next_service is None:
                break

            candidate_times = []
            if next_arrival_time is not None:
                candidate_times.append((next_arrival_time, "arrival", None))
            if next_service is not None:
                candidate_time, server_index = next_service
                candidate_times.append((candidate_time, "service", server_index))

            next_time, event_type, server_index = min(candidate_times, key=lambda item: item[0])
            self.advance_time(next_time)

            if event_type == "arrival":
                self.handle_arrival()
            elif event_type == "service" and server_index is not None:
                self.handle_service_completion(server_index)
            else:
                raise RuntimeError("Evento inválido.")

        total_time = self.time
        probabilities: Dict[int, float] = {}
        for state in range(self.capacity + 1):
            probabilities[state] = self.state_time.get(state, 0.0) / total_time if total_time > 0 else 0.0

        return {
            "tempo_total": total_time,
            "tempos_acumulados": {k: round(v, 6) for k, v in self.state_time.items()},
            "probabilidades": {k: round(v, 6) for k, v in probabilities.items()},
            "perdas": self.lost_customers,
            "aleatorios_usados": self.randoms_used,
        }


def simulate_case(arrival_min: float, arrival_max: float, service_min: float, service_max: float, servers: int, capacity: int, seed: int = 1) -> Dict[str, object]:
    simulator = QueueSimulator(
        arrival_min=arrival_min,
        arrival_max=arrival_max,
        service_min=service_min,
        service_max=service_max,
        servers=servers,
        capacity=capacity,
        max_randoms=100_000,
        seed=seed,
    )
    return simulator.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador de fila G/G/c/K")
    parser.add_argument("--arrival-min", type=float, default=2.0)
    parser.add_argument("--arrival-max", type=float, default=5.0)
    parser.add_argument("--service-min", type=float, default=3.0)
    parser.add_argument("--service-max", type=float, default=5.0)
    parser.add_argument("--servers", type=int, default=1)
    parser.add_argument("--capacity", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    result = simulate_case(
        arrival_min=args.arrival_min,
        arrival_max=args.arrival_max,
        service_min=args.service_min,
        service_max=args.service_max,
        servers=args.servers,
        capacity=args.capacity,
        seed=args.seed,
    )

    print(f"Tempo total da simulação: {result['tempo_total']:.6f}")
    print(f"Clientes perdidos: {result['perdas']}")
    print("Tempos acumulados por estado:")
    for state, duration in result["tempos_acumulados"].items():
        print(f"  Estado {state}: {duration:.6f}")
    print("Probabilidades por estado:")
    for state, probability in result["probabilidades"].items():
        print(f"  Estado {state}: {probability:.6f}")


if __name__ == "__main__":
    main()
