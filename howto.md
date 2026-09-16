# Como executar o simulador de filas em tandem

## Requisitos

- Python 3.9 ou superior.
- Nenhuma biblioteca externa.

## Execução da rede de validação

Na raiz do projeto, execute:

```bash
python3 simulador_tandem.py
```

Essa execução simula:

| Fila | Chegadas externas | Atendimento | Servidores | Capacidade |
|---|---:|---:|---:|---:|
| 1 | 1..5 | 4..5 | 2 | 3 |
| 2 | nenhuma | 1..3 | 1 | 5 |

A Fila 1 recebe o primeiro cliente em `t = 2,5`. Cada cliente que termina o atendimento
na Fila 1 é encaminhado para a Fila 2. Depois do atendimento na Fila 2, o cliente sai
do sistema.

Os parâmetros opcionais são:

```text
--seed N             semente do gerador (padrão: 1)
--first-arrival T    instante do primeiro cliente (padrão: 2.5)
--max-randoms N      quantidade máxima de aleatórios (padrão: 100000)
```

Exemplo:

```bash
python3 simulador_tandem.py --seed 1 --first-arrival 2.5 --max-randoms 100000
```

## Gerador pseudoaleatório

O simulador usa o Método Congruente Linear:

```text
X(i+1) = (1664525 * X(i) + 1013904223) mod 2^32
U(i) = X(i) / 2^32
```

A semente padrão é `1`. O contador é incrementado somente quando um aleatório é
solicitado para um intervalo de chegada, atendimento ou roteamento probabilístico.
Ao utilizar o 100.000º aleatório, a simulação é encerrada.

## Sintaxe de roteamento

O modelo utiliza a estrutura:

```python
{fila_origem: [(fila_destino, probabilidade), ...]}
```

Os índices das filas começam em zero. Assim, a rede em tandem usada na validação é:

```python
{0: [(1, 1.0)]}
```

Isso significa que 100% dos clientes que saem da Fila 1 passam para a Fila 2.
Uma fila que não aparece como origem na tabela de roteamento envia seus clientes
para fora da rede após o atendimento.

## Saída

O programa informa:

- tempo global da simulação;
- quantidade de aleatórios utilizados;
- perdas de cada fila;
- tempo acumulado em cada estado de cada fila;
- probabilidade de permanência em cada estado.

As probabilidades são calculadas por `tempo acumulado do estado / tempo global`.

## Resultado da rede de validação

Com os parâmetros padrão (`seed=1`, primeiro cliente em `t=2.5` e 100.000
aleatórios), o resultado é:

```text
Tempo total da simulação: 100649.370495
Aleatórios usados: 100000

Fila 1:
  Perdas: 393
  Tempos acumulados: [1120.657008, 49584.135790, 43659.663972, 6284.913723]
  Probabilidades:    [0.011134, 0.492642, 0.433780, 0.062444]

Fila 2:
  Perdas: 0
  Tempos acumulados: [34365.950489, 60076.741145, 6191.404839,
                      15.274022, 0.000000, 0.000000]
  Probabilidades:    [0.341442, 0.596891, 0.061515, 0.000152,
                      0.000000, 0.000000]
```

## Valores de referência da Parte 1

O programa anterior continua disponível em `simulador_fila.py`. Seus cenários de
fila simples podem ser executados, por exemplo, com:

```bash
python3 simulador_fila.py --servers 1 --capacity 5 \
  --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5

python3 simulador_fila.py --servers 2 --capacity 5 \
  --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5
```

Esses comandos reproduzem os resultados entregues na Parte 1 usando a semente
padrão `1`.
