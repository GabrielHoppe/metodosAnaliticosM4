# Simulador de redes de filas

Este projeto implementa simulação de eventos discretos para filas `G/G/c/K`
e, na etapa atual, para redes com topologia configurável:

- gerador pseudoaleatório linear congruente (LCG);
- qualquer quantidade de filas e servidores;
- capacidades finitas ou ilimitadas;
- chegadas externas em filas configuradas;
- roteamento probabilístico entre filas;
- ciclos e saídas da rede;
- tempos acumulados, probabilidades por estado e perdas.

## Modelo generalizado

A rede é carregada de um arquivo YAML:

```bash
python3 simulador_tandem.py modelo.yml
```

O arquivo `modelo.yml` contém a rede de validação desta etapa. Ele define a
semente, a primeira chegada em `t = 2.0`, o limite de `100000` aleatórios,
as filas e as rotas. Uma fila com `capacity: null` possui capacidade ilimitada.
As filas são referenciadas por índices começando em zero.

Uma rota usa o formato:

```yaml
- from: 0
  to: 1
  probability: 0.2
```

Use `to: null` para representar a saída do sistema. O simulador aceita também
rotas cíclicas e múltiplas chegadas externas.

O resultado informa o tempo global, os aleatórios usados, as perdas de cada
fila, os tempos acumulados e as probabilidades de cada estado. A execução
termina ao consumir o 100.000º número pseudoaleatório.

## Modelo de validação

O `modelo.yml` representa:

- Fila 1: `G/G/1`, chegadas `2..4`, atendimento `1..2`, capacidade ilimitada;
- Fila 2: `G/G/2/5`, atendimento `4..6`;
- Fila 3: `G/G/2/10`, atendimento `5..15`;
- roteamento conforme as probabilidades do modelo fornecido.

Resultado de referência:

```text
Tempo total da simulação: 50788.222050
Aleatórios usados: 100000
Perdas: Fila 1 = 0, Fila 2 = 1, Fila 3 = 11690
```

## Simulador da etapa anterior

O simulador de uma fila continua disponível em `simulador_fila.py`:

```bash
python3 simulador_fila.py --servers 1 --capacity 5 \
  --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5

python3 simulador_fila.py --servers 2 --capacity 5 \
  --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5
```

Para detalhes do formato YAML e dos parâmetros opcionais, consulte
`howto.md`.
