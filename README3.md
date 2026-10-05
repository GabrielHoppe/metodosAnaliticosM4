# Simulador generalizado de redes de filas

Esta etapa generaliza o simulador anterior para carregar uma rede de filas a
partir de um arquivo `.yml`. A rede pode ter qualquer quantidade de filas,
rotas entre quaisquer filas, ciclos, múltiplas chegadas externas e saídas do
sistema.

## Execução

Não há bibliotecas externas obrigatórias:

```bash
python3 simulador_tandem.py modelo.yml
```

Sem informar um arquivo, o comando continua executando a rede tandem da etapa
anterior (`validation_simulation`), preservando a compatibilidade com o
`README2.md`:

```bash
python3 simulador_tandem.py
```

Opções de linha de comando:

```text
--seed N             substitui a semente definida no modelo
--first-arrival T    substitui a chegada inicial da fila 0
--max-randoms N      substitui o limite de números aleatórios
```

O simulador usa o gerador congruente linear:

```text
X(i+1) = (1664525 * X(i) + 1013904223) mod 2^32
U(i) = X(i) / 2^32
```

O contador inclui cada número usado para intervalo de chegada, atendimento ou
roteamento probabilístico. A execução para quando o 100.000º número é
consumido.

## Formato do modelo

O arquivo possui as seções `simulation`, `queues` e `routes`:

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

As filas são identificadas pelo índice na lista, começando em zero. `arrival`
é o intervalo de chegadas externas; use `null` para uma fila que não recebe
clientes externamente. `service` é o intervalo de atendimento e `servers` é o
número de servidores. `capacity: null` representa capacidade ilimitada. Uma
rota com `to: null` remove o cliente da rede. As probabilidades das rotas de
uma origem podem somar menos que 1; o restante também representa saída.

Para agendar mais de uma chegada inicial, use:

```yaml
initial_arrivals:
  - queue: 0
    time: 2.0
  - queue: 3
    time: 5.0
```

Se `initial_arrivals` não existir, é criada uma chegada na fila 0 no instante
`simulation.first_arrival`.

## Modelo de validação entregue

`modelo.yml` reproduz a rede da imagem:

- Fila 1: `G/G/1`, chegadas `2..4`, atendimento `1..2`, capacidade ilimitada;
- Fila 2: `G/G/2/5`, atendimento `4..6`;
- Fila 3: `G/G/2/10`, atendimento `5..15`;
- roteamento conforme as probabilidades mostradas na imagem;
- filas inicialmente vazias, primeira chegada em `t = 2.0`;
- semente 1 e limite de 100.000 aleatórios.

O relatório impresso contém o tempo global, os aleatórios utilizados, perdas,
tempos acumulados por estado e probabilidades de cada fila. A probabilidade de
um estado é `tempo acumulado do estado / tempo global`.

Com a execução de `python3 simulador_tandem.py modelo.yml`, o resultado de
referência deste modelo é:

```text
Tempo total da simulação: 50788.222050
Aleatórios usados: 100000

Fila 1:
  Perdas: 0
  Tempos acumulados: [20370.108910, 26636.157526, 3613.763120,
                      167.231576, 0.960918]
  Probabilidades:    [0.401079, 0.524455, 0.071154, 0.003293, 0.000019]

Fila 2:
  Perdas: 1
  Tempos acumulados: [12598.957468, 20883.806871, 12890.836708,
                      3809.243479, 562.633467, 42.744057]
  Probabilidades:    [0.248068, 0.411194, 0.253815, 0.075002,
                      0.011078, 0.000842]

Fila 3:
  Perdas: 11690
  Tempos acumulados: [3.236456, 2.552629, 2.704986, 6.669747, 7.088859,
                      5.529560, 1.988224, 43.412643, 2862.263035,
                      15904.670839, 31948.105071]
  Probabilidades:    [0.000064, 0.000050, 0.000053, 0.000131, 0.000140,
                      0.000109, 0.000039, 0.000855, 0.056357, 0.313157,
                      0.629046]
```

## Observação sobre compatibilidade

O arquivo também é aceito quando PyYAML está instalado, mas o programa inclui
um leitor interno para o formato simples usado neste projeto. Assim, a
execução padrão não exige `pip install` nem qualquer biblioteca externa.

O simulador da etapa anterior continua disponível em `simulador_fila.py`, e o
simulador de tandem específico continua representado pela função
`validation_simulation` em `simulador_tandem.py`.
