from dataclasses import dataclass


@dataclass(frozen=True)
class VoteOption:
    code: str
    label: str
    result: str
    clue: str
    is_true_clue: bool = False


@dataclass(frozen=True)
class GameStage:
    id: int
    room_name: str
    title: str
    hero_journey_stage: str
    story: str
    key_item: str
    options: list[VoteOption]
    hints: list[str]


@dataclass(frozen=True)
class CaseProfile:
    id: str
    culprit: str
    motive: str
    method: str
    decisive_clue: str
    false_leads: list[str]
    confession: str
    final_options: list[VoteOption]


CASE_PROFILES = [
    CaseProfile(
        id="elena",
        culprit="Elena, la economista",
        motive="Javi iba a denunciar la doble contabilidad que ella usaba para tapar deudas de la empresa familiar.",
        method="Cogió la escopeta de postas durante el apagón, disparó desde el pasillo de servicio y devolvió el arma limpia a medias.",
        decisive_clue="El libro mayor tenía una página arrancada, pero el calco quedó marcado en la hoja siguiente.",
        false_leads=["Víctor discutió con Javi.", "Irina preguntó por la herencia.", "Clara tenía una llave del despacho."],
        confession="Elena calculó mentalmente el coste de una defensa penal antes de pedir agua. Mala señal, buen Excel.",
        final_options=[
            VoteOption("A", "Acusar a Elena por la contabilidad oculta", "", "", True),
            VoteOption("B", "Acusar a Víctor por la venta de la empresa", "", ""),
            VoteOption("C", "Acusar a Irina por la herencia", "", ""),
        ],
    ),
    CaseProfile(
        id="victor",
        culprit="Víctor, el socio bizco",
        motive="Javi descubrió que Víctor negociaba vender la empresa familiar a espaldas de todos.",
        method="Preparó la galería, esperó a Javi y aprovechó la tormenta para confundir el disparo con un trueno.",
        decisive_clue="La mirilla del pasillo demostraba que Víctor pudo vigilar la biblioteca desde la galería.",
        false_leads=["Elena ocultaba documentos.", "Don Anselmo cambió el testamento.", "Ramiro mintió sobre su ronda."],
        confession="Víctor intentó mirar indignado a todos a la vez. Por una vez, su estrabismo no fue coartada suficiente.",
        final_options=[
            VoteOption("A", "Acusar a Don Anselmo por la herencia", "", ""),
            VoteOption("B", "Acusar a Víctor por la venta secreta", "", "", True),
            VoteOption("C", "Acusar a Clara por la llave perdida", "", ""),
        ],
    ),
    CaseProfile(
        id="irina",
        culprit="Irina, la mujer extranjera de Don Anselmo",
        motive="Javi encontró documentos que podían anular su parte de la herencia.",
        method="Entró por la capilla, dejó barro rojo y disparó con la escopeta de postas antes de esconder la llave bajo el reclinatorio.",
        decisive_clue="El barro rojo de la capilla apareció en el dobladillo del abrigo de Irina.",
        false_leads=["Elena tenía facturas alteradas.", "Víctor compró cartuchos.", "Don Anselmo cambió el testamento."],
        confession="Irina sonrió con una calma tan cara que en el pueblo la confundieron con educación. No lo era.",
        final_options=[
            VoteOption("A", "Acusar a Elena por las facturas", "", ""),
            VoteOption("B", "Acusar a Ramiro por la llave de servicio", "", ""),
            VoteOption("C", "Acusar a Irina por la herencia anulada", "", "", True),
        ],
    ),
    CaseProfile(
        id="ramiro",
        culprit="Ramiro, el guarda nocturno",
        motive="Ramiro era el hijo no reconocido de Don Anselmo y Javi quería expulsarlo de la finca antes de que reclamara nada.",
        method="Usó su llave maestra, cogió la escopeta de postas y disparó desde el acceso de servicio de la biblioteca.",
        decisive_clue="La llave maestra de Ramiro tenía cera de la biblioteca pegada en los dientes.",
        false_leads=["Víctor dejó huellas en la galería.", "Clara recibió una transferencia.", "Don Anselmo ocultó la carta."],
        confession="Ramiro dijo que solo quería justicia. Lo dijo con la escopeta demasiado bien limpiada para resultar poético.",
        final_options=[
            VoteOption("A", "Acusar a Ramiro por la carta de filiación", "", "", True),
            VoteOption("B", "Acusar a Don Anselmo por ocultar su pasado", "", ""),
            VoteOption("C", "Acusar a Víctor por el negocio fallido", "", ""),
        ],
    ),
]


STAGES = [
    GameStage(1, "Vestíbulo del Archivo", "La llegada bajo la tormenta", "Mundo ordinario", "⛈️ Llegáis a la mansión Valcárcel. Javi, heredero de la casa, ha aparecido muerto en la biblioteca por un disparo de escopeta de postas. En el vestíbulo hay tres rastros iniciales.", "🗝️ Llave de hierro del Salón", [VoteOption("A", "El paraguas mojado sin iniciales", "Encontráis barro rojo en el puño.", "Barro rojo de la capilla", True), VoteOption("B", "El recibo de taxi arrugado", "Parece incriminar a Elena, pero la hora no encaja.", "Recibo con hora dudosa"), VoteOption("C", "La bandeja de copas", "Una copa tiene carmín y poco más.", "Copa con carmín")], ["El barro viaja.", "No todo viene del camino principal.", "El color importará."]),
    GameStage(2, "Salón principal", "Los invitados empiezan a sudar", "Llamada a la aventura", "🕯️ En el salón, la familia reparte el duelo con codazos. Elena calcula, Víctor mira raro, Clara calla y Don Anselmo exige dignidad.", "🗝️ Llave pequeña del Despacho", [VoteOption("A", "Interrogar a Elena sobre las cuentas", "Admite que Javi pidió el libro mayor.", "Javi pidió el libro mayor", True), VoteOption("B", "Presionar a Don Anselmo", "Confiesa que cambió el testamento.", "Testamento cambiado"), VoteOption("C", "Observar a Clara", "Está nerviosa, agotada y poco concluyente.", "Nervios de Clara")], ["El dinero habla.", "Javi pidió documentos.", "Buscad papeles."]),
    GameStage(3, "Despacho de Javi", "El heredero tenía enemigos archivados", "Rechazo de la llamada", "📚 El despacho está demasiado ordenado. Hay una caja de cartas, un portátil sin batería y recortes del periódico local.", "🗝️ Llave latonada del Pasillo de Retratos", [VoteOption("A", "Abrir la caja de correspondencia", "Halláis una carta sobre un hijo no reconocido.", "Carta de filiación de Ramiro", True), VoteOption("B", "Forzar el portátil", "Aparece una foto borrosa de Víctor.", "Foto borrosa de Víctor"), VoteOption("C", "Revisar recortes", "Irina aparece en una vieja escuela de azafatas.", "Recorte sobre Irina")], ["La sangre también escribe.", "Una carta pesa más que una foto.", "El secreto tiene firma antigua."]),
    GameStage(4, "Pasillo de retratos", "La familia mira desde la pared", "Encuentro con el mentor", "🖼️ Los retratos juzgan con más entusiasmo que pruebas. Hay un marco torcido, cera en el suelo y una puerta disimulada.", "🗝️ Llave oxidada de la Galería", [VoteOption("A", "Mover el retrato torcido", "Descubrís una mirilla hacia la biblioteca.", "Mirilla hacia la biblioteca", True), VoteOption("B", "Seguir la cera del suelo", "Conduce hacia la capilla.", "Gotas de cera"), VoteOption("C", "Escuchar tras la puerta", "Víctor discute con alguien.", "Víctor nervioso")], ["Alguien pudo ver sin ser visto.", "El pasillo conecta con el crimen.", "Una mirilla rompe coartadas."]),
    GameStage(5, "Galería acristalada", "El trueno perfecto", "Cruce del umbral", "🌩️ Desde la galería se ve la biblioteca y la tormenta suena bastante fuerte para tapar un disparo.", "🗝️ Llave de bronce del Cuarto de Caza", [VoteOption("A", "El pestillo manipulado", "El cierre fue alterado antes del apagón.", "Pestillo preparado antes del crimen", True), VoteOption("B", "La colilla", "Pertenece a Don Anselmo.", "Colilla de Don Anselmo"), VoteOption("C", "La pisada", "Es una bota común de campo.", "Pisada común")], ["Se prepara antes.", "No confundáis vicio con culpa.", "Un pestillo también declara."]),
    GameStage(6, "Cuarto de caza", "La escopeta y otras tradiciones", "Pruebas, aliados y enemigos", "🔫 La escopeta de postas ha sido usada y devuelta. Alguien limpió con prisa.", "🗝️ Llave pesada de la Cocina", [VoteOption("A", "El paño escondido", "Tiene aceite y una fibra azul.", "Fibra azul en el paño", True), VoteOption("B", "Los cartuchos", "Víctor los compró días atrás.", "Cartuchos comprados por Víctor"), VoteOption("C", "La vitrina", "No fue forzada.", "Vitrina abierta con llave")], ["La limpieza deja rastro.", "Comprar no es disparar.", "Buscad conexión con persona."]),
    GameStage(7, "Cocina de servicio", "Donde se cuece la coartada", "El enemigo se muestra", "🍲 La cocina está despierta. Hay un reloj parado, una lista de cena y una puerta de servicio.", "🗝️ Llave ennegrecida de la Bodega", [VoteOption("A", "Comparar el reloj con el apagón", "El reloj se paró cinco minutos antes del supuesto disparo.", "Hora real alterada", True), VoteOption("B", "Leer la lista de cena", "Javi cenó poco, pero no fue veneno.", "Cena incompleta"), VoteOption("C", "Interrogar a la cocinera", "Confirma que todos mienten con horarios distintos.", "Testimonio confuso")], ["La hora oficial puede ser teatro.", "El disparo no fue cuando dicen.", "Un reloj parado habla."]),
    GameStage(8, "Bodega", "Barricas, deudas y verdades", "Acercamiento a la cueva profunda", "🍷 La bodega guarda vinos viejos y secretos peores. Hay un escondite en una barrica.", "🗝️ Llave fría de la Capilla", [VoteOption("A", "Abrir el escondite de la barrica", "Encontráis copias de facturas manipuladas.", "Facturas manipuladas", True), VoteOption("B", "Raspar el barro seco", "Es parecido al del vestíbulo.", "Barro con cal"), VoteOption("C", "Revisar botellas apartadas", "Hay una etiqueta falsa.", "Etiqueta falsa")], ["La empresa deja huellas.", "Las facturas también matan.", "Buscad papeles."]),
    GameStage(9, "Capilla familiar", "Donde todos rezan por coartada", "Prueba suprema", "⛪ Bajo el reclinatorio hay arañazos recientes. El barro rojo mancha una losa.", "🗝️ Llave plateada del Dormitorio", [VoteOption("A", "Levantar el reclinatorio", "Halláis la marca donde se escondió una llave.", "Llave escondida en la capilla", True), VoteOption("B", "Analizar la vela", "Se apagó durante el apagón.", "Vela apagada"), VoteOption("C", "Examinar la losa", "El barro rojo confirma paso reciente.", "Barro rojo reciente")], ["La capilla fue paso.", "Mirad donde se arrodillan.", "Una llave estuvo aquí."]),
    GameStage(10, "Dormitorio de Don Anselmo", "El teatro del patriarca", "Recompensa", "🛏️ El cuarto de Don Anselmo huele a colonia fuerte y decisiones débiles. Hay testamento, medicación y una foto antigua.", "🗝️ Llave dorada del Archivo Familiar", [VoteOption("A", "El borrador del testamento", "Javi iba a heredar menos de lo que creía.", "Testamento recortado", True), VoteOption("B", "La medicación", "Don Anselmo no estaba para correr con una escopeta.", "Medicación del padre"), VoteOption("C", "La foto doblada", "Aparece Ramiro de niño junto a la finca.", "Foto antigua de Ramiro")], ["Herencia no siempre significa padre.", "Un testamento cambia relaciones.", "Dinero y sangre se mezclan."]),
    GameStage(11, "Archivo familiar", "El papel nunca olvida", "Camino de regreso", "🗄️ En el archivo hay libros mayores, escrituras, cartas y una caja con sellos viejos.", "🗝️ Llave negra de la Biblioteca", [VoteOption("A", "Comparar libro mayor y facturas", "Las cifras no cuadran.", "Doble contabilidad", True), VoteOption("B", "Revisar escrituras", "Irina no figura como propietaria directa.", "Escritura sin Irina"), VoteOption("C", "Leer cartas antiguas", "Confirman secretos de sangre.", "Cartas de familia")], ["Ordenad dinero, tiempo y arma.", "La última llave está entre documentos.", "No todo secreto es asesinato."]),
    GameStage(12, "Biblioteca", "La acusación final", "Resurrección del héroe", "📖 Volvéis a la biblioteca. Sobre la mesa están la escopeta, las llaves y una familia que preferiría vender la mansión antes que decir la verdad.", "🗝️ Llave final de la Verdad", [], ["Ordenad móvil, acceso y oportunidad.", "Una pista falsa señala emoción; una real señala mecanismo.", "La acusación correcta explica por qué murió Javi."]),
]
