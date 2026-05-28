from dataclasses import dataclass


@dataclass(frozen=True)
class GameStage:
    id: int
    title: str
    hero_journey_stage: str
    story: str
    valid_answers: list[str]
    success_message: str
    reward_item: str
    hints: list[str]


STAGES: list[GameStage] = [
    GameStage(
        id=1,
        title="Mundo ordinario",
        hero_journey_stage="Mundo ordinario",
        story="""🕯️ El grupo estaba en una conversación normal de Telegram cuando, de pronto, todos los mensajes anteriores comenzaron a distorsionarse.

Una frase aparece una y otra vez:

'Lo cotidiano es la primera prisión del héroe.'

En la pantalla veis cuatro palabras parpadeando:

CASA - PUERTA - SOMBRA - LLAVE

El Archivista susurra:

'Todo viaje empieza cuando alguien se atreve a abrir algo.'

¿Qué palabra representa el comienzo del viaje?""",
        valid_answers=["PUERTA"],
        success_message="""✅ La PUERTA aparece ante vosotros.

No era una metáfora.

Una puerta negra se abre dentro del propio chat.

Habéis abandonado el mundo ordinario.""",
        reward_item="🗝️ Llave del Umbral",
        hints=[
            "Pensad en algo que se abre.",
            "No es un objeto cualquiera: marca el paso de un sitio a otro.",
            "Todo viaje empieza cruzando una puerta.",
        ],
    ),
    GameStage(
        id=2,
        title="La llamada a la aventura",
        hero_journey_stage="Llamada a la aventura",
        story="""📜 El Archivista os entrega un mensaje cifrado:

OD OODYH HV PHQWH

Debajo aparece una nota:

'El Bucle Negro desplaza la verdad tres pasos hacia delante.
Para encontrarla, caminad tres pasos hacia atrás.'

Descifrad el mensaje.""",
        valid_answers=["MENTE", "LA LLAVE ES MENTE"],
        success_message="""✅ Habéis recuperado la primera verdad:

'La llave es mente.'

El Archivista asiente.

'No se escapa con fuerza. Se escapa entendiendo.'""",
        reward_item="🧠 Llave de la Mente",
        hints=[
            "Es un cifrado clásico.",
            "Cada letra se ha desplazado tres posiciones.",
            "OD significa LA.",
        ],
    ),
    GameStage(
        id=3,
        title="Rechazo de la llamada",
        hero_journey_stage="Rechazo de la llamada",
        story="""🌫️ Una niebla cubre el Archivo.

El Bucle Negro habla por primera vez:

'Podéis volver atrás. Nadie os obligó a entrar. Cerrad Telegram, olvidad esta historia y estaréis a salvo.'

Aparecen tres caminos:

1. VOLVER
2. ESPERAR
3. AVANZAR

Pero el suelo muestra esta inscripción:

'El héroe no es quien no teme, sino quien camina con miedo.'

¿Qué decisión debéis tomar?""",
        valid_answers=["AVANZAR", "VALOR"],
        success_message="""✅ Elegís avanzar.

La niebla retrocede.

El Bucle Negro no desaparece, pero por primera vez parece dudar.""",
        reward_item="🔥 Valor",
        hints=[
            "El héroe puede tener miedo, pero no se queda quieto.",
            "No hay que volver atrás.",
            "La decisión correcta es seguir adelante.",
        ],
    ),
    GameStage(
        id=4,
        title="Encuentro con el mentor",
        hero_journey_stage="Encuentro con el mentor",
        story="""🧙 El Archivista toma forma.

No es una persona. Es una voz hecha de libros, mapas y mensajes perdidos.

'Todo héroe necesita tres cosas: memoria, valor y unión.'

Os entrega una tabla incompleta:

SOL = 1
LUNA = 2
RÍO = 3
MONTAÑA = 4

Pero el orden correcto de los sellos se ha perdido.

Pistas:

- El Sol abre el camino.
- El Río fluye justo después del Sol.
- La Luna cierra la noche.
- La Montaña queda entre el Río y la Luna.

Escribid el orden correcto de los cuatro sellos.""",
        valid_answers=["SOL RIO MONTAÑA LUNA", "SOL RÍO MONTAÑA LUNA"],
        success_message="""✅ Los sellos se iluminan en orden:

☀️ SOL
🌊 RÍO
⛰️ MONTAÑA
🌙 LUNA

El Archivista os entrega el Mapa Interior.""",
        reward_item="🗺️ Mapa del Archivo",
        hints=[
            "El Sol va primero.",
            "El Río va justo después del Sol.",
            "La Montaña queda entre el Río y la Luna.",
        ],
    ),
    GameStage(
        id=5,
        title="Cruce del umbral",
        hero_journey_stage="Cruce del umbral",
        story="""🚪 Llegáis a la Primera Gran Puerta.

No tiene cerradura, solo una frase:

'Para entrar, debes saber qué llevas contigo.'

Inventario actual:

🗝️ Llave del Umbral
🧠 Llave de la Mente
🔥 Valor
🗺️ Mapa del Archivo

La puerta pregunta:

'No soy objeto, pero abro caminos.
No soy fuerza, pero vence al miedo.
No soy una persona, pero une al grupo.'

¿Qué soy?""",
        valid_answers=["CONFIANZA"],
        success_message="""✅ La palabra CONFIANZA atraviesa la puerta.

El grupo cruza el umbral.

A partir de ahora, no sois visitantes.

Sois la Compañía de las Doce Llaves.""",
        reward_item="🤝 Llave de la Confianza",
        hints=[
            "No es algo físico.",
            "Tiene que ver con creer en los demás.",
            "Sin ella, un grupo se rompe.",
        ],
    ),
    GameStage(
        id=6,
        title="Pruebas, aliados y enemigos",
        hero_journey_stage="Pruebas, aliados y enemigos",
        story="""⚔️ Entráis en la Galería de las Pruebas.

Tres estatuas bloquean el paso.

La primera dice:
'Tengo ciudades, pero no casas.'

La segunda dice:
'Tengo montañas, pero no árboles.'

La tercera dice:
'Tengo ríos, pero no agua.'

¿Qué soy?""",
        valid_answers=["MAPA"],
        success_message="""✅ La respuesta es MAPA.

El Mapa del Archivo se despliega solo y revela una ruta oculta.""",
        reward_item="🧭 Brújula de las Decisiones",
        hints=[
            "No penséis en algo vivo.",
            "Sirve para orientarse.",
            "Representa lugares, pero no los contiene de verdad.",
        ],
    ),
    GameStage(
        id=7,
        title="El enemigo se muestra",
        hero_journey_stage="Pruebas, aliados y enemigos",
        story="""🕳️ El Bucle Negro infecta el chat.

Aparecen mensajes repetidos:

MIEDO MIEDO MIEDO
DUDA DUDA DUDA
PRISA PRISA PRISA
EGO EGO EGO

El Archivista grita:

'El enemigo no siempre está fuera. A veces bloquea al grupo desde dentro.'

Para romper el bucle debéis elegir la palabra contraria a cada bloqueo:

MIEDO = ?
DUDA = ?
PRISA = ?
EGO = ?

Escribid las cuatro palabras en orden.""",
        valid_answers=["VALOR CONFIANZA CALMA EQUIPO"],
        success_message="""✅ El bucle se rompe.

MIEDO se transforma en VALOR.
DUDA se transforma en CONFIANZA.
PRISA se transforma en CALMA.
EGO se transforma en EQUIPO.""",
        reward_item="🛡️ Escudo del Equipo",
        hints=[
            "Buscad lo contrario de cada palabra negativa.",
            "La última palabra tiene que ver con no actuar solo.",
            "MIEDO se vence con VALOR.",
        ],
    ),
    GameStage(
        id=8,
        title="Acercamiento a la cueva profunda",
        hero_journey_stage="Acercamiento a la cueva profunda",
        story="""🕯️ Llegáis a la Cámara del Silencio.

En el centro hay una inscripción:

'No se puede derrotar al Bucle Negro con una sola voz.'

El bot envía cuatro fragmentos:

Fragmento A: LA
Fragmento B: UNION
Fragmento C: ABRE
Fragmento D: EL CENTRO

Ordenad los fragmentos para formar la frase correcta.""",
        valid_answers=["LA UNION ABRE EL CENTRO", "LA UNIÓN ABRE EL CENTRO"],
        success_message="""✅ La Cámara del Silencio se abre.

Por primera vez veis el núcleo del Archivo.

El Bucle Negro no está destruyendo el Archivo.

Lo está encerrando en una repetición infinita.""",
        reward_item="🔮 Cristal del Centro",
        hints=[
            "La frase empieza por LA.",
            "El sujeto de la frase es LA UNIÓN.",
            "La frase completa explica qué abre el centro.",
        ],
    ),
    GameStage(
        id=9,
        title="Prueba suprema",
        hero_journey_stage="Prueba suprema",
        story="""🖤 El Bucle Negro aparece.

'No podéis escapar. Todo grupo falla por lo mismo: unos hablan, otros callan, otros se rinden.'

El núcleo muestra una ecuación simbólica:

MENTE + VALOR + CONFIANZA + EQUIPO = ?

El Archivista dice:

'Esta no es una suma matemática. Es lo que nace cuando el grupo actúa como uno.'

¿Qué palabra completa la ecuación?""",
        valid_answers=["HEROE", "HÉROE"],
        success_message="""✅ El núcleo reconoce la respuesta:

HÉROE.

Pero no señala a una persona.

Señala al grupo entero.""",
        reward_item="⚔️ Llave del Héroe",
        hints=[
            "No es una operación matemática.",
            "La respuesta tiene que ver con el viaje que estáis viviendo.",
            "No hay un único protagonista: el grupo entero lo es.",
        ],
    ),
    GameStage(
        id=10,
        title="Recompensa",
        hero_journey_stage="Recompensa",
        story="""✨ El Bucle Negro cae de rodillas.

El Archivista os entrega la Llave Maestra, pero está incompleta.

Tiene grabadas seis marcas:

PUERTA
MENTE
VALOR
CONFIANZA
MAPA
HEROE

La Llave Maestra necesita una última palabra.

Una palabra que explique por qué habéis llegado hasta aquí.

No es ganar.
No es escapar.
No es competir.

Es hacerlo juntos.

¿Qué palabra falta?""",
        valid_answers=["UNION", "UNIÓN"],
        success_message="""✅ La Llave Maestra se completa.

Pero el Archivo empieza a derrumbarse.

Aún falta salir.""",
        reward_item="🗝️ Llave Maestra de la Unión",
        hints=[
            "No se trata de ganar individualmente.",
            "Tiene que ver con hacerlo juntos.",
            "La palabra puede escribirse con o sin tilde.",
        ],
    ),
    GameStage(
        id=11,
        title="Camino de regreso",
        hero_journey_stage="Camino de regreso",
        story="""🚨 El Archivo se colapsa.

Tenéis que activar la salida escribiendo las palabras clave en el orden en que fueron descubiertas.

Recordad vuestro camino.

Formato esperado:

PALABRA1 PALABRA2 PALABRA3 PALABRA4 PALABRA5 PALABRA6""",
        valid_answers=[
            "PUERTA MENTE AVANZAR CONFIANZA MAPA HEROE",
            "PUERTA MENTE VALOR CONFIANZA MAPA HEROE",
            "PUERTA MENTE AVANZAR CONFIANZA MAPA HÉROE",
            "PUERTA MENTE VALOR CONFIANZA MAPA HÉROE",
        ],
        success_message="""✅ La salida se abre.

Corréis hacia la última puerta mientras el Archivo se reconstruye a vuestro alrededor.

El Bucle Negro lanza una última pregunta.""",
        reward_item="🚪 Salida del Archivo",
        hints=[
            "La primera palabra era PUERTA.",
            "La segunda estaba en el mensaje cifrado.",
            "Recordad las palabras clave de las primeras pruebas.",
        ],
    ),
    GameStage(
        id=12,
        title="Resurrección y decisión final",
        hero_journey_stage="Resurrección del héroe",
        story="""🖤 El Bucle Negro os ofrece un trato:

'Puedo dejar salir a una sola persona ahora mismo.
El resto quedará atrapado.
Elegid.'

Aparecen dos opciones:

1. SALVARME
2. UNIR

El Archivista susurra:

'El héroe verdadero no regresa solo con el premio. Regresa con el elixir para todos.'

¿Qué elegís?""",
        valid_answers=["UNIR"],
        success_message="""🌟 Habéis elegido UNIR.

El Bucle Negro se rompe.

No porque lo hayáis destruido, sino porque habéis rechazado jugar con sus reglas.

El Archivo queda libre.

Las Doce Llaves vuelven a brillar.

Habéis completado el viaje del héroe.""",
        reward_item="🌟 Elixir del Archivo",
        hints=[
            "No se trata de salvarse solo.",
            "El viaje del héroe termina regresando con algo para todos.",
            "La opción correcta no es SALVARME.",
        ],
    ),
]
