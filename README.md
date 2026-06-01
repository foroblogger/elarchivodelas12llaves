# El Archivo de las Doce Llaves

Bot de Telegram para jugar un escape room narrativo en grupo. El bot actúa como narrador y director de juego, guarda el progreso en SQLite y plantea un crimen en una mansión familiar española de pueblo rústico.

El caso base: Javi, heredero de la familia Valcárcel, aparece muerto en la biblioteca durante una noche de tormenta. Los jugadores son detectives externos y deben recorrer 12 habitaciones, encontrar llaves físicas, seguir pistas, esquivar pistas falsas y votar por mayoría hasta acusar al culpable.

## Requisitos

- Python 3.11 o superior.
- Un bot creado en Telegram con BotFather.
- Un grupo de Telegram donde añadir el bot.

## Crear el bot en BotFather

1. Abre Telegram y busca `@BotFather`.
2. Envía `/newbot`.
3. Elige un nombre visible para el bot.
4. Elige un usuario terminado en `bot`, por ejemplo `ArchivoDoceLlavesBot`.
5. BotFather te entregará un token. Guárdalo con cuidado.

Opcionalmente, en BotFather puedes usar `/setcommands` y registrar:

```text
start_escape - Crear una partida nueva
unirse - Unirse a la partida
comenzar - Iniciar la fase 1
estado - Ver el estado de la partida
inventario - Ver objetos conseguidos
pista - Pedir una pista
votar - Votar una opción de investigación
resolver - Resolver la fase actual
reset_escape - Reiniciar la partida
ranking - Ver ranking o resultado final
crear_salas - Crear las salas del grupo
```

## Configurar el entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edita `.env`:

```env
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
DATABASE_PATH=escape_room.sqlite3
```

## Instalar dependencias

Se recomienda usar un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar el bot

```bash
python main.py
```

En Windows PowerShell:

```powershell
python .\main.py
```

Si el token está bien configurado, verás logs en consola indicando que el bot está esperando mensajes.

## Añadirlo a un grupo

1. Abre tu grupo de Telegram.
2. Añade el bot como miembro.
3. Dale permiso para leer y enviar mensajes.
4. Para usar `/reset_escape` y `/crear_salas`, el bot debe poder consultar administradores del grupo. En grupos normales basta con que el bot esté dentro; si hay restricciones fuertes, hazlo administrador.

Permisos recomendados:

- Enviar mensajes.
- Leer mensajes/comandos.
- Ver miembros del grupo.
- Gestionar temas.

## Crear salas del escape room

Para que el bot cree las salas automáticamente:

1. Convierte el grupo en foro activando los temas desde los ajustes del grupo.
2. Haz administrador al bot.
3. Dale permiso para gestionar temas.
4. Escribe en el grupo:

```text
/crear_salas
```

El bot intentará crear:

```text
Vestíbulo del Archivo
Salón principal
Despacho de Javi
Pasillo de retratos
Galería acristalada
Cuarto de caza
Cocina de servicio
Bodega
Capilla familiar
Dormitorio de Don Anselmo
Archivo familiar
Biblioteca
```

## Iniciar una partida

Dentro del grupo puedes hablarle al bot en lenguaje natural:

```text
hola
abrir caso
```

El bot hará una introducción automática y preguntará cuántos detectives habéis venido. Después podéis responder así:

```text
somos 5
me uno
estoy aquí
soy detective
estamos todos
```

Cuando se alcanza el número indicado, el bot empieza a narrar la primera sala automáticamente. También podéis decir `estamos todos`, `estamos listos` o `empezamos` para comenzar antes si ya estáis preparados.

Durante la partida también entiende frases naturales:

```text
investiguemos el paraguas mojado
revisar la vitrina
voto A
acuso a Elena
quiero una pista
cómo vamos
qué llaves tenemos
```

El bot mantiene comandos como respaldo (`/start_escape`, `/unirse`, `/comenzar`, `/votar A`, `/pista`, `/estado`, `/inventario`), pero la forma recomendada de jugar es conversacional. Cada sala propone tres opciones de investigación. Los jugadores unidos votan hablando con el bot y la opción que alcanza mayoría simple desbloquea una llave física y la siguiente habitación.

La solución del crimen cambia de una partida a otra. El bot elige al azar culpable, móvil, pista decisiva y falsas pistas compatibles con la historia.

## Reiniciar una partida

Solo un administrador del grupo puede usar:

```text
/reset_escape
```

El comando borra la partida del grupo actual. Después se puede empezar otra con `abrir caso` o `/start_escape`.

## Ranking

Cuando una partida termina, usa:

```text
/ranking
```

En el chat donde se completó una partida muestra su resultado final. Si no hay partida completada en ese chat, muestra las mejores partidas completadas guardadas en SQLite.

## Persistencia

SQLite guarda una fila por chat con:

- `chat_id`
- `game_active`
- `current_stage`
- `players`
- `inventory`
- `hints_used`
- `wrong_answers`
- `started_at`
- `finished_at`
- `completed`
- `score`
- `case_id`
- `votes`
- `discovered_clues`
- `false_clues`
- `expected_players`

Si el bot se reinicia, la partida continúa desde el último estado guardado.

## Puntuación

La partida empieza con 100 puntos.

Penalizaciones:

- Cada pista usada: -5 puntos.
- Cada respuesta incorrecta: -2 puntos.
- Superar 60 minutos: -20 puntos al finalizar.

Bonificaciones:

- Completar en menos de 40 minutos: +15 puntos.
- Completar sin pistas: +20 puntos.
- Completar con al menos 3 jugadores: +10 puntos.

Rangos:

- 120 o más: Leyendas del Archivo.
- 100 a 119: Guardianes de las Llaves.
- 80 a 99: Compañía Heroica.
- 60 a 79: Aprendices del Umbral.
- Menos de 60: Atrapados parcialmente en el Bucle.

## Modificar o añadir salas

Las salas están en `game_data.py`, dentro de la lista `STAGES`. Las soluciones posibles están en `CASE_PROFILES`.

Cada fase usa la dataclass `GameStage`:

```python
GameStage(
    id=1,
    room_name="Vestíbulo del Archivo",
    title="La llegada bajo la tormenta",
    hero_journey_stage="Mundo ordinario",
    story="Texto narrativo",
    key_item="Llave conseguida",
    options=[...],
    hints=["Pista 1", "Pista 2", "Pista 3"],
)
```

Para añadir una nueva fase:

1. Añade un nuevo `GameStage` al final de `STAGES`.
2. Usa un `id` consecutivo.
3. Incluye al menos una respuesta válida.
4. No reveles la respuesta en las pistas salvo que sea la última pista y quieras hacerlo deliberadamente.
5. Ejecuta los tests.

## Tests

```bash
pytest
```

Cubren normalización de respuestas, cálculo de puntuación, selección de caso, configuración del número de jugadores, votaciones, avance por mayoría, pistas falsas y finalización del caso.

## Estructura

```text
main.py
config.py
database.py
game_data.py
game_engine.py
handlers.py
requirements.txt
.env.example
README.md
tests/test_game_engine.py
```
