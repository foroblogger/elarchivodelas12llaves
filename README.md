# El Archivo de las Doce Llaves

Bot de Telegram para jugar un escape room narrativo en grupo. El bot actúa como narrador y director de juego, guarda el progreso en SQLite y plantea un crimen en una mansión familiar española de pueblo rústico.

El caso base: Javi, heredero de la familia Valcárcel, aparece muerto en la biblioteca durante una noche de tormenta. Los jugadores son detectives externos y deben recorrer 12 habitaciones, encontrar llaves físicas, seguir pistas, esquivar pistas falsas y votar por mayoría hasta acusar al culpable.

## Iniciar una partida

Dentro del grupo podéis decir:

```text
abrir caso
somos 5
me uno
estamos todos
investiguemos el paraguas mojado
quiero una pista
cómo vamos
qué llaves tenemos
```

Al abrir el caso, el bot pregunta cuántos detectives estáis. Cuando respondéis algo como `somos 5`, guarda el tamaño del equipo. Cada jugador se presenta diciendo `me uno`; cuando se alcanza el número indicado, el bot empieza a narrar la primera sala automáticamente. También podéis decir `estamos todos` para empezar antes si ya estáis listos.

Comandos de respaldo: `/start_escape`, `/unirse`, `/comenzar`, `/votar A`, `/pista`, `/estado`, `/inventario`, `/reset_escape`, `/ranking`, `/crear_salas`.

## Persistencia

SQLite guarda el estado del chat, jugadores, llaves, votos, pistas, caso aleatorio y `expected_players`, por lo que el bot puede continuar tras un reinicio.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe main.py
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```
