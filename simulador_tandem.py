#!/usr/bin/env python3
"""Simulador de eventos discretos para redes de filas configuráveis."""

from __future__ import annotations

import argparse
import ast
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
    capacity: Optional[int]
    customers: int = 0
    losses: int = 0
    state_time: List[float] = field(init=False)
    waiting: int = 0
    server_end_times: List[Optional[float]] = field(init=False)

    def __post_init__(self) -> None:
        if (self.capacity is not None and self.capacity < 0) or self.servers_count < 1:
            raise ValueError("capacidade deve ser >= 0 e servidores deve ser >= 1")
        if self.service_min > self.service_max:
            raise ValueError("service_min deve ser menor ou igual a service_max")
        if self.arrival_min is not None and (
            self.arrival_max is None or self.arrival_min > self.arrival_max
        ):
            raise ValueError("intervalo de chegada inválido")
        self.state_time = [0.0]
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

    def add_state(self) -> None:
        while len(self.state_time) <= self.customers:
            self.state_time.append(0.0)


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
        routes: Dict[int, Sequence[Tuple[Optional[int], float]]],
        *,
        first_arrival: float = 2.5,
        initial_arrivals: Optional[Sequence[Tuple[int, float]]] = None,
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
        if initial_arrivals is None:
            initial_arrivals = [(0, first_arrival)]
        for queue_index, arrival_time in initial_arrivals:
            self.scheduler.schedule(arrival_time, "arrival", queue_index)

    def uniform(self, low: float, high: float) -> float:
        if self.randoms_used >= self.max_randoms:
            raise StopIteration("limite de aleatórios atingido")
        self.randoms_used += 1
        return low + (high - low) * self.rng.next()

    def service_end(self, queue_index: int) -> float:
        queue = self.queues[queue_index]
        return self.time + self.uniform(queue.service_min, queue.service_max)

    def schedule_external_arrival(self, queue_index: int) -> None:
        queue = self.queues[queue_index]
        if queue.arrival_min is None or self.randoms_used >= self.max_randoms:
            return
        arrival = self.time + self.uniform(queue.arrival_min, queue.arrival_max)  # type: ignore[arg-type]
        self.scheduler.schedule(arrival, "arrival", queue_index)

    def start_service(self, queue_index: int, server_index: int) -> None:
        queue = self.queues[queue_index]
        end_time = self.service_end(queue_index)
        queue.server_end_times[server_index] = end_time
        kind = "passage" if queue_index in self.routes else "departure"
        self.scheduler.schedule(end_time, kind, queue_index, server_index)

    def admit(self, queue_index: int) -> None:
        queue = self.queues[queue_index]
        if queue.capacity is not None and queue.customers >= queue.capacity:
            queue.losses += 1
            return
        queue.customers += 1
        queue.add_state()
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
        selected: Optional[int] = None
        if len(destinations) == 1 and destinations[0][1] >= 1.0:
            selected = destinations[0][0]
        else:
            draw = self.uniform(0.0, 1.0)
            cumulative = 0.0
            for destination, probability in destinations:
                cumulative += probability
                if draw < cumulative:
                    selected = destination
                    break
        if selected is not None:
            self.admit(selected)

    def advance(self, event_time: float) -> None:
        if event_time < self.time:
            raise ValueError("evento anterior ao tempo atual")
        elapsed = event_time - self.time
        for queue in self.queues:
            queue.add_state()
            queue.state_time[queue.customers] += elapsed
        self.time = event_time

    def handle(self, event: Event) -> None:
        if event.kind == "arrival":
            self.admit(event.queue_index)
            self.schedule_external_arrival(event.queue_index)
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
            try:
                self.handle(event)
            except StopIteration:
                break
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


def _scalar(value: str) -> object:
    value = value.strip()
    if value in {"null", "None", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value.strip("\"'")


def _read_simple_yaml(path: str) -> Dict[str, object]:
    """Read the small YAML subset used by model files without external packages."""
    lines = [
        (len(line) - len(line.lstrip()), line.strip())
        for line in open(path, encoding="utf-8")
        if line.strip() and not line.lstrip().startswith("#")
    ]

    def block(position: int, indent: int) -> Tuple[object, int]:
        is_list = position < len(lines) and lines[position][0] == indent and lines[position][1].startswith("- ")
        result: object = [] if is_list else {}
        while position < len(lines) and lines[position][0] == indent:
            text = lines[position][1]
            if is_list:
                if not text.startswith("- "):
                    break
                item_text = text[2:].strip()
                if ":" in item_text:
                    key, raw = item_text.split(":", 1)
                    item: Dict[str, object] = {key.strip(): _scalar(raw) if raw.strip() else None}
                    position += 1
                    if position < len(lines) and lines[position][0] > indent:
                        child, position = block(position, lines[position][0])
                        if isinstance(child, dict):
                            item.update(child)
                    result.append(item)  # type: ignore[union-attr]
                else:
                    result.append(_scalar(item_text))  # type: ignore[union-attr]
                    position += 1
            else:
                key, raw = text.split(":", 1)
                key = key.strip()
                position += 1
                if raw.strip():
                    value = _scalar(raw)
                elif position < len(lines) and lines[position][0] > indent:
                    value, position = block(position, lines[position][0])
                else:
                    value = None
                result[key] = value  # type: ignore[index]
        return result, position

    parsed, _ = block(0, lines[0][0])
    if not isinstance(parsed, dict):
        raise ValueError("o modelo YAML deve possuir um objeto na raiz")
    return parsed


def load_model(path: str) -> NetworkSimulator:
    """Build a simulator from YAML (PyYAML is optional for this schema)."""
    try:
        import yaml  # type: ignore
    except ImportError:
        model = _read_simple_yaml(path)
    else:
        with open(path, encoding="utf-8") as file:
            model = yaml.safe_load(file)
    if not isinstance(model, dict):
        raise ValueError("modelo inválido")

    simulation = model.get("simulation", {})
    if not isinstance(simulation, dict):
        raise ValueError("simulation deve ser um objeto")
    queue_data = model.get("queues")
    if not isinstance(queue_data, list) or not queue_data:
        raise ValueError("queues deve ser uma lista não vazia")

    queues: List[Queue] = []
    for item in queue_data:
        if not isinstance(item, dict):
            raise ValueError("cada fila deve ser um objeto")
        arrival = item.get("arrival")
        if arrival is not None and (not isinstance(arrival, list) or len(arrival) != 2):
            raise ValueError("arrival deve conter [mínimo, máximo] ou ser null")
        queues.append(
            Queue(
                arrival_min=None if arrival is None else float(arrival[0]),
                arrival_max=None if arrival is None else float(arrival[1]),
                service_min=float(item["service"][0]),
                service_max=float(item["service"][1]),
                servers_count=int(item["servers"]),
                capacity=None if item.get("capacity") is None else int(item["capacity"]),
            )
        )

    routes: Dict[int, List[Tuple[Optional[int], float]]] = {}
    for item in model.get("routes", []):
        if not isinstance(item, dict):
            raise ValueError("cada rota deve ser um objeto")
        source = int(item["from"])
        destination = item.get("to")
        if source < 0 or source >= len(queues):
            raise ValueError(f"origem de rota inválida: {source}")
        if destination is not None and (int(destination) < 0 or int(destination) >= len(queues)):
            raise ValueError(f"destino de rota inválido: {destination}")
        probability = float(item["probability"])
        if probability < 0:
            raise ValueError("probabilidades não podem ser negativas")
        routes.setdefault(source, []).append(
            (None if destination is None else int(destination), probability)
        )
    for source, destinations in routes.items():
        total = sum(probability for _, probability in destinations)
        if total > 1.0 + 1e-9:
            raise ValueError(f"probabilidades da fila {source} excedem 1")

    initial_data = model.get("initial_arrivals")
    initial_arrivals = None
    if initial_data is not None:
        initial_arrivals = [
            (int(item["queue"]), float(item["time"])) for item in initial_data
        ]
    return NetworkSimulator(
        queues,
        routes,
        first_arrival=float(simulation.get("first_arrival", 2.0)),
        initial_arrivals=initial_arrivals,
        max_randoms=int(simulation.get("max_randoms", 100_000)),
        seed=int(simulation.get("seed", 1)),
    )


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
    parser = argparse.ArgumentParser(description="Simulador de redes de filas")
    parser.add_argument("model", nargs="?")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--first-arrival", type=float)
    parser.add_argument("--max-randoms", type=int)
    args = parser.parse_args()
    if args.model is None:
        print_result(
            validation_simulation(
                seed=args.seed,
                first_arrival=2.5 if args.first_arrival is None else args.first_arrival,
                max_randoms=100_000 if args.max_randoms is None else args.max_randoms,
            ).run()
        )
        return

    simulator = load_model(args.model)
    if args.seed != 1:
        simulator.rng = LCG(seed=args.seed)
    if args.first_arrival is not None:
        simulator.scheduler = Scheduler()
        simulator.scheduler.schedule(args.first_arrival, "arrival", 0)
    if args.max_randoms is not None:
        simulator.max_randoms = args.max_randoms
    print_result(simulator.run())


if __name__ == "__main__":
    main()
