# Como executar o simulador generalizado

## Requisitos

- Python 3.9 ou superior.
- Nenhuma biblioteca externa obrigatória.

## Execução

Na raiz do projeto, execute o modelo generalizado:

```bash
python3 simulador_tandem.py modelo.yml
```

O arquivo YAML define toda a rede: parâmetros da simulação, filas e
roteamento. O programa informa o tempo global, os aleatórios utilizados,
perdas, tempos acumulados por estado e probabilidades de cada fila.

Parâmetros opcionais:

```text
--seed N             substitui a semente do arquivo
--first-arrival T    substitui a chegada inicial da fila 0
--max-randoms N      substitui o limite de aleatórios
```

Exemplo:

```bash
python3 simulador_tandem.py modelo.yml --seed 1 --max-randoms 100000
```

## Formato do arquivo YAML

O modelo possui as seções `simulation`, `queues` e `routes`:

```yaml
simulation:
  seed: 1
  first_arrival: 2.0
  max_randoms: 100000

queues:
  - name: 1
    arrival: [2, 4]
    service: [1, 2]
    servers: 1
    capacity: null

routes:
  - from: 0
    to: 1
    probability: 0.2
```

As filas são identificadas pelo índice na lista, começando em zero:

- `arrival`: intervalo de chegadas externas; use `null` quando a fila não
  recebe chegadas externas;
- `service`: intervalo uniforme de atendimento;
- `servers`: quantidade de servidores;
- `capacity`: capacidade máxima; `null` significa capacidade ilimitada.

Cada item de `routes` informa uma origem, um destino e uma probabilidade. Use
`to: null` para retirar o cliente do sistema. Podem ser definidas rotas para
qualquer fila, inclusive ciclos. As probabilidades de uma origem podem somar
menos que 1; a parcela restante representa saída da rede.

Para agendar mais de uma chegada inicial, adicione:

```yaml
initial_arrivals:
  - queue: 0
    time: 2.0
  - queue: 2
    time: 5.0
```

Sem `initial_arrivals`, o simulador agenda uma chegada na fila `0` no instante
definido por `simulation.first_arrival`.

## Modelo de validação

O arquivo `modelo.yml` usa:

| Fila | Chegadas externas | Atendimento | Servidores | Capacidade |
|---|---:|---:|---:|---:|
| 1 | 2..4 | 1..2 | 1 | ilimitada |
| 2 | nenhuma | 4..6 | 2 | 5 |
| 3 | nenhuma | 5..15 | 2 | 10 |

A primeira chegada ocorre em `t = 2.0`, as filas começam vazias e a simulação
termina ao consumir o 100.000º aleatório.

Resultado de referência:

```text
Tempo total da simulação: 50788.222050
Aleatórios usados: 100000

Fila 1:
  Clientes perdidos: 0

Fila 2:
  Clientes perdidos: 1

Fila 3:
  Clientes perdidos: 11690
```

O programa também imprime os tempos acumulados e as probabilidades de todos
os estados. Cada probabilidade é calculada como:

```text
tempo acumulado do estado / tempo global
```

## Gerador pseudoaleatório

O simulador usa o Método Congruente Linear:

```text
X(i+1) = (1664525 * X(i) + 1013904223) mod 2^32
U(i) = X(i) / 2^32
```

Um número é consumido para cada intervalo de chegada, atendimento ou decisão
de roteamento probabilístico. A simulação encerra ao utilizar o limite
configurado.

## Simulador da etapa anterior

O simulador de fila única continua disponível em `simulador_fila.py`:

```bash
python3 simulador_fila.py --servers 1 --capacity 5 \
  --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5

python3 simulador_fila.py --servers 2 --capacity 5 \
  --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5
```
