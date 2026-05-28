# El Archivo de las Doce Llaves

Bot de Telegram para jugar un escape room narrativo en grupo. El bot actúa como narrador y director de juego, guarda el progreso en SQLite y sigue la estructura del viaje del héroe.

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
Sala 01 - Mundo ordinario
Sala 02 - Llamada a la aventura
Sala 03 - Rechazo de la llamada
Sala 04 - Encuentro con el mentor
Sala 05 - Cruce del umbral
Sala 06 - Pruebas y aliados
Sala 07 - El Bucle Negro
Sala 08 - Cámara del Silencio
Sala 09 - Prueba suprema
Sala 10 - Recompensa
Sala 11 - Camino de regreso
Sala 12 - Decisión final
Ranking - Salón de los Héroes
```

## Iniciar una partida

Dentro del grupo:

```text
/start_escape
/unirse
/comenzar
```

Durante la partida:

```text
/resolver respuesta
/pista
/estado
/inventario
```

El bot no permite abrir una segunda partida activa en el mismo grupo.

## Reiniciar una partida

Solo un administrador del grupo puede usar:

```text
/reset_escape
```

El comando borra la partida del grupo actual. Después se puede empezar otra con `/start_escape`.

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

## Modificar o añadir fases

Las fases están en `game_data.py`, dentro de la lista `STAGES`.

Cada fase usa la dataclass `GameStage`:

```python
GameStage(
    id=1,
    title="Mundo ordinario",
    hero_journey_stage="Mundo ordinario",
    story="Texto narrativo",
    valid_answers=["PUERTA"],
    success_message="Mensaje al resolver",
    reward_item="Objeto conseguido",
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

Cubren normalización de respuestas, cálculo de puntuación, avance de fase, respuestas correctas e incorrectas.

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
