# Simulador de Fila G/G/c/K

Este projeto implementa um simulador de eventos discretos para filas do tipo G/G/c/K, com:

- gerador pseudoaleatório linear congruente (LCG);
- primeiro cliente chegando sempre em t = 3,0;
- chegadas em intervalo uniforme entre 2 e 5;
- atendimento em intervalo uniforme entre 3 e 5;
- capacidade máxima da fila/ sistema de 5 clientes;
- parada ao consumir 100.000 aleatórios;
- relatório de tempos acumulados, probabilidades por estado e perdas.

## Como executar

```bash
python3 simulador_fila.py --servers 1 --capacity 5 --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5
python3 simulador_fila.py --servers 2 --capacity 5 --arrival-min 2 --arrival-max 5 --service-min 3 --service-max 5
```
