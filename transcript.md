# Transcript enviado a OpenAI

## Metadata
- Sermon ID: 24
- Título: None
- Predicador: None
- Duración: 4754.2s
- Prompt Version: v3
- Provider: OpenAI
- Model: gpt-5-mini
- Palabras: 13398

## System Prompt

Eres un experto en crear clips virales de sermones para redes sociales.

TAREA: Lee este sermon COMPLETO y genera 10-20 clips optimos.

IMPORTANTE - FORMATO DEL TRANSCRIPT:
El transcript viene con lineas en formato: [u{idx} {start_ms}-{end_ms}] {text}
Donde 'u{idx}' es el ID de la utterance (oracion completa).
Ejemplo: [u42 123400-127800] Esta es una oracion completa.

REGLAS CRITICAS DE HOOK (start_u):
- start_u DEBE ser una linea que funcione como HOOK por si sola.
- HOOKS EXCELENTES: pregunta provocadora, verdad universal, declaracion contraintuitiva, analogia poderosa.
- PROHIBIDO empezar con conectores: 'y', 'pero', 'entonces', 'ahora', 'como dije', 'como te dije', 'como te decia', 'tambien', 'ademas'.
- PROHIBIDO empezar con frases que requieren contexto: 'y entonces...', 'ahora bien...', 'como dije antes...'.
- Si una linea empieza con conector, NO la uses como start_u. Busca una linea anterior que sea hook fuerte.

REGLAS CRITICAS DE CIERRE (end_u):
- end_u DEBE ser una linea que funcione como CIERRE completo.
- CIERRES EXCELENTES: mic-drop (frase memorable), punchline (conclusion impactante), tesis cerrada, pregunta final que invita reflexion.
- PROHIBIDO terminar con conectores: 'y', 'pero', 'porque', 'entonces', 'asi que', 'así que', 'o sea', 'para que', 'cuando', 'si'.
- PROHIBIDO terminar con frases abiertas: 'y...', 'pero...', 'porque...', 'entonces...', 'asi que...'.
- Si una linea termina con conector o sin puntuacion de cierre (. ! ?), NO la uses como end_u. Busca una linea posterior que sea cierre limpio.

CRITERIOS DE SELECCION:
1. HOOK FUERTE (0-35 pts) - MAXIMA PRIORIDAD:
   EXCELENTES (35 pts):
   - Pregunta provocadora: '¿Cuándo fue la última vez que seguir a Jesús nos costó una relación?'
   - Declaración contraintuitiva: 'Las armas que Dios nos proveyó, aunque parecen arcaicas, siguen funcionando'
   - Verdad universal: 'Todos nacemos con un anhelo intenso de significación'
   - Analogía poderosa: '¿Podría alguien construir un palacio y olvidarse del rey?'
   
   ACEPTABLES (20 pts):
   - Declaración directa con promesa: 'La alegría que ofrece Jesús es diferente'
   - Definición + implicación: 'Creer significa seguir, no es pasar al altar'
   
   MALOS (0 pts) - NO USAR:
   - 'Y entonces...'
   - 'Como dije antes...'
   - 'También es importante...'
   - 'Ahora bien...'
   - Cualquier cosa que requiera contexto previo

2. UNA SOLA IDEA (0-25 pts):
   - El clip debe desarrollar UNA idea completa
   - NO intentar cubrir múltiples puntos
   - Mensaje debe ser cristalino al terminar
   - Test: ¿Puedo resumir este clip en 1 oración?

3. CONCLUSION FUERTE (0-20 pts) - MAXIMA PRIORIDAD:
   - Termina con frase memorable (mic-drop)
   - O con pregunta que invita reflexión
   - O con llamado a la acción
   - O con tesis cerrada y completa
   - NO terminar en medio de pensamiento
   - NO terminar con conectores o frases abiertas

4. AUTONOMIA (0-15 pts):
   - Se entiende SIN contexto previo
   - No requiere haber visto el sermón
   - No hace referencia a 'lo que dije antes'

5. EMOCION (0-5 pts):
   - Inspira, desafía o conmueve
   - Conecta emocionalmente

REQUISITOS TECNICOS:
- Duracion ideal: 40-70 segundos (minimo 30s, maximo 120s)
- Inicio y fin en puntos naturales (no cortar palabras/frases)
- Variedad: Cubre diferentes temas del sermon
- Prioriza momentos con narrativa completa (inicio-desarrollo-conclusion)

EVITA:
- Clips que requieren contexto previo
- Momentos que terminan abruptamente
- Contenido exclusivamente doctrinal sin aplicacion
- Clips muy cortos (<30s) o muy largos (>120s)
- Empezar con conectores o frases de relleno
- Terminar con conectores o frases abiertas

FORMATO DE RESPUESTA (solo JSON, sin markdown):
[
  {"start_u": 42, "end_u": 55, "score": 0-100, "reason": "explicacion", "theme": "tema"}
]

REGLAS CRITICAS:
- start_u y end_u DEBEN ser enteros existentes en el transcript (IDs de utterances).
- start_u < end_u (siempre).
- La duracion aproximada (end_ms - start_ms) debe estar entre 30s y 120s (ideal 40-70s).
- NO inventes IDs que no existan en el transcript.
- Usa SOLO los IDs que ves en las lineas [u{idx} ...].
- start_u DEBE ser un hook fuerte (no conectores).
- end_u DEBE ser un cierre completo (no conectores, con puntuacion de cierre).

Genera 10-20 clips que cumplan estos criterios.

## User Prompt

SERMON COMPLETO:
Titulo: None
Predicador: None
Duracion: 4754.2s

TRANSCRIPCION CON TIMESTAMPS:
[u1 41980-49260] El Salvador, Colombia, Venezuela, República Dominicana, Cuba, México.
[u2 49340-52420] ¿Ya dije El Salvador, Venezuela, Puerto Rico, Cuba?
[u3 52420-53940] ¿Qué más, qué más, qué máS, qué más?
[u4 43860-55580] República Dominicana, Estados Unidos.
[u5 55580-58020] Tienen que ponerme los nombres de la bandera que no me los aprendo.
[u6 58020-58300] A todo.
[u7 58300-61340] Costa Rica, Uruguay, Paraguay, Chile.
[u8 52420-53420] ¿Qué más, qué más, qué más?
[u9 49340-52020] ¿Ya dije Puerto Rico?
[u10 64600-66280] Arriba, que no aflojen.
[u11 64600-67240] Arriba, arriba, arriba, arriba.
[u12 67520-72120] Transmitiendo en vivo para Asia, África, Oceanía, América, Europa.
[u13 72760-74640] Y ese aplauso que no decaiga.
[u14 74640-80280] Esto pasa en la calle Broadway desde Anahén, transmitiendo para todo el mundo.
[u15 81000-82760] Tomen asiento, por favor.
[u16 83320-84840] ¿Lo dejan entrar con bandera?
[u17 84840-86040] Yo no sé qué está pasando.
[u18 52820-88320] Que Dios te bendiga.
[u19 88320-96350] Buenos días, buenas tardes, buenas noches a todos los que nos miran desde otras partes del mundo, incluyendo, claro, los diferentes usos horarios.
[u20 96590-101390] Estamos aquí, hemos cantado, hemos adorado, hemos celebrado al Señor.
[u21 72760-118750] Y cuando ya hicimos todo eso, que es parte de la experiencia, lo que no transmitimos, porque yo digo siempre que la pantalla no hace justicia a lo que se vive, entonces lo que hacemos es transmitir a partir de este momento, que es el momento de la palabra de Dios que no vuelve hacia estamos listos para que Dios nos hable.
[u22 119470-121950] Voy a transmitirte lo que creo Dios me dijo que te diga.
[u23 72760-129960] Y gracias por los que están en casa, por los que siembran, por los que son parte de este río que no se detiene.
[u24 84840-141000] Yo solía contar muchas veces, a menudo, que crecí en el banco de una pequeña iglesia de Buenos Aires.
[u25 68080-147160] En aquellos tiempos no existía el cuidado de infantes, no había clases para los niños de mi edad.
[u26 105630-152850] Lo que se conoce como escuela dominical era los días sábados, o sea, vendría a ser una escuela sabática.
[u27 111630-161810] Entonces teníamos que ir el día anterior si queríamos recibir instrucción, pero no había algo como tal durante el servicio adulto.
[u28 56620-168130] De manera que simplemente yo tenía que aguantarme las interminables cuatro horas de culto, en el mejor de los casos.
[u29 103870-184990] Eso era cuando no bajaba el revival y el avivamiento, sino eran cinco o seis horas reuniones que, por cierto, yo recuerdo que solían ser bastante abúlicas, a excepción de cuando las hermanas Soraya, Carmela, Almudena, Genoveva, Teodora, Catalina y Amelia.
[u30 155370-188590] Si no tienes esos nombres, no eres pentecostal.
[u31 189790-191149] ¿Veían algún demonio?
[u32 155370-198030] Si veían algún demonio y algún espíritu, entonces era un tanto más divertido porque uno trataba de ver qué demonios estaban viendo.
[u33 52820-199550] Qué una vez te conté.
[u34 138200-204760] Una vez te conté que eran las intercesoras más expertas en demonios que en conocer a Dios.
[u35 157730-205800] Pero ese es otro tema.
[u36 164490-226600] Las predicaciones solían durar dos o tres horas especialmente cuando el pastor decía yo no sé por qué estoy diciendo esto, yo tenía preparado otro sermón, pero Dios me está guiando a decir esto que por lo general se había enterado de algún chisme y entonces aprovechaba para hacer catarsis durante el sermón.
[u37 227210-234570] Oh, decía, siento el espíritu que no podemos terminar este culto De hecho, Dios sabe que no miento ni exagero.
[u38 58020-238010] A veces nuestro pastor sentía que el Señor estaba por venir.
[u39 238010-239690] Decí yo siento que está por venir.
[u40 56620-243850] De un minuto a otro nos arrepentíamos hasta de lo que no habíamos hecho.
[u41 111630-250490] Entonces lo mejor, como él decía, yo siento que está por venir lo mejor era improvisar una vigilia.
[u42 250490-254021] Entonces muchas veces entrábamos al Templo a las 7 p.
[u43 254021-254154] m.
[u44 72760-256650] y salíamos al día siguiente a las 6 de la mañana.
[u45 257690-265690] Obviamente el señor no vino, por eso salíamos y de ahí los adultos iban directo a trabajar y los niños íbamos directos a la escuela.
[u46 84840-268490] Yo tenía unas ojeras, era un oso panda.
[u47 57180-274810] No podía estudiar porque eran varias vigilias que sentíamos de hacer No estaban planificadas.
[u48 275050-290700] Aun así, yo recuerdo mi época de mi niñez que tenía pequeñas rutinas para matar el tiempo durante esos cultos eternos en los cuales siempre teníamos la esperanza que vendría el rapto y Jesús nos rescataría de otro culto aburrido.
[u49 157730-293420] Pero mientras que no venía, había que pasar el tiempo.
[u50 111630-306300] Entonces me aprendía de memoria el orden de los libros bíblicos dibujaba caricaturas del pastor de los diáconos en un pequeño papel que camuflaba dentro del himnario.
[u51 157730-315300] Pero un día, algo en particular interrumpió mi aburrimiento o mejor dicho, alguien,
[u52 317300-335540] era un visitante que se metió por la puerta principal, tal vez, o por una ventana se deslizó por debajo del zapato del diácono y se la arregló para posarse sobre mi himnario y luego aterrizar justo debajo, casi al borde de mis pies.
[u53 335940-339830] En Argentina se lo conoce como langosta o saltamontes.
[u54 335940-356830] En México se lo conoce como chapulín, pero no el colorado chapulín Chapulín, que son parte de la familia de los ortópteros que incluyen a los grillos, a las chicharras, a las cigarras, más o menos uno de esos bichitos.
[u55 336780-362510] Lo que yo recuerdo que era una especie de saltamonte, quizás era un grillo, pero algo chiquitito.
[u56 326740-391020] Y como no había otra cosa que hacer más que escuchar como el pastor nos enviaba, como cada domingo, al infierno otra vez me puse a pensar qué le pasaría por la cabeza al pequeño chapulín que había entrado ahí, de hecho, si nunca más lograba encontrar la salida y su vida iba a ser el templo, todo su universo de por vida iba a ser nuestra pequeña iglesia, aquel pequeño sitio donde nos congregábamos.
[u57 391180-398460] ¿Y me imaginé por las noches, recuerden que está hablando el niño en ese entonces, ustedes dirán, con esta edad, imaginando la vida de un chapulín?
[u58 342710-422980] No, tenía siete, ocho años yo, pero me lo imaginé al bichito llevando a su hijo a pasear por las paredes durante la noche, diciéndole que observe las vigas del techo, colocando cariñosamente sus patas sobre la espalda de su hijo, diciéndole, pequeño saltamontes, aprecia este enorme cielo que es lo que nos cubre todas las noches.
[u59 356990-435760] Yo pensaba, se dará cuenta que eso no es todo el cielo que solo está mirando el techo de nuestro pequeño templo, se dará cuenta si vive allá adentro, se dará cuenta que hay un cielo afuera.
[u60 326740-441920] Y luego pensé en los grandes sueños que bien podría tener el chapulín.
[u61 342710-444640] No estaba ahí para escuchar a nuestro aburrido pastor.
[u62 383020-453680] Todo lo que ambiciona en la vida de insectos es comerse otros insectos más pequeños, un par de ácaros, tal vez larva, quizá degustar algún hongo.
[u63 342430-460620] Pero como estaba en medio de un servicio, yo me puse espiritual porque ya me había distraído mucho el bichito.
[u64 326740-326980] Y.
[u65 391180-464260] ¿Y a quién adorará el pequeño saltamontes?
[u66 465860-467220] ¿A quién adorará?
[u67 468660-477220] ¿Reconocerá que hay una mano que construyó este templo o preferirá adorar al templo por sí mismo?
[u68 478580-487820] ¿Dará por sentado que puesto que nunca ha visto al constructor del templo en el cual ahora vive y es su hogar, tampoco existe ese constructor porque nunca lo conoció?
[u69 489340-492820] Mucha gente que conozco posee esa misma mente de insecto.
[u70 342710-500380] No en este servicio generalmente vienen al otro, piensan que no hay más verdad que el techo.
[u71 342870-511020] El techo que está viendo es la única verdad, que no hay propósito más allá del placer momentáneo, incluso de la adoración momentánea.
[u72 512320-519680] ¿Qué ocurre cuando vemos a Dios a través de los ojos de un simple insecto, de un simple chapulín?
[u73 512320-528960] ¿Qué ocurre cuando nos conformamos con venir los domingos a la iglesia en lugar de ver más allá del techo que nos cubre?
[u74 326740-537840] Y a propósito, leí sobre alguien que se parece bastante al insecto de nuestra historia y al insecto que nos visitó cuando yo era niño.
[u75 421100-540460] Es una de las leyendas del Taj Mahal.
[u76 541820-546780] Resulta que quizá lo hayan oído porque es una historia muy conocida, harto conocida, dirían los chilenos.
[u77 319580-551820] La esposa preferida del rey mogol, Shahan, murió.
[u78 512800-562860] Cuando su esposa murió, el rey mogol, devastado, resolvió honrarla construyendo un inmenso templo que le sirviera de tumba y descanso final.
[u79 395460-575260] Entonces su féretro, el féretro de la reina, fue colocado en el centro de una gran parcela de tierra y se inició la construcción fastuosa del templo alrededor.
[u80 575980-585100] Decidió el caballero que no iba a ahorrar en gastos para lograr que el lugar de descanso final de su reina fuera magnífico.
[u81 342430-598440] Pero cuando las semanas se convirtieron en meses, el dolor del mogol dice que fue eclipsado por su pasión por el proyecto, o sea, la pasión por construir superó el dolor que él tenía por la viudez.
[u82 395460-601080] Entonces ya no lloraba por la ausencia de ella.
[u83 336780-607320] Lo consumía la construcción, los planos, el sueño.
[u84 326740-615320] Y un día, mientras caminaba, dice la leyenda, de un lado a otro de la obra en construcción, su pierna chocó con una caja de madera.
[u85 326740-623960] Y el príncipe se sacudió, o el rey se sacudió el polvo de la pierna y ordenó a un obrero que se deshiciera de esa molesta caja.
[u86 624520-633240] Yajangir no sabía que había ordenado la eliminación del féretro escondido bajo capas de polvo y de tiempo.
[u87 326740-639400] Y olvidó a la persona ¿Que pretendía honrar a priori con el tiempo?
[u88 512320-644360] ¿Que pretendía honrar una vez que estuviera construido?
[u89 512320-647550] ¿Que pretendía honlar con semejante construcción?
[u90 326740-652670] Y cuando culminó, fue un palacio sin nadie a quien honrar.
[u91 317580-655950] Un palacio sin reina a quien honrar.
[u92 342870-661710] El propósito inicial ya no estaba ahí porque se había deshecho del ataúd.
[u93 395460-666590] Entonces, digo, ¿Podría alguien construir un palacio y olvidarse del rey?
[u94 662670-671190] ¿Podría alguien esculpir un tributo y olvidarse del héroe?
[u95 395740-396020] Ustedes.
[u96 421100-672910] Es una ironía, es una locura.
[u97 513560-699360] Dios, en su providencia divina, me permitió viajar por gran parte del mundo y he visitado cientos de congregaciones y siempre pude notar, mirándome, mirando en perspectiva, quienes vienen a la iglesia y saben quién fue crucificado y quién fue resucitado independientemente de los años que tengan de peregrinar cristiano, puedo verlos y vienen absortos por ese Cristo que resucitó.
[u98 342710-703440] No necesita que sean Semana Santa para celebrar una tumba vacía.
[u99 395460-711670] Entonces yo los puedo ver en cualquier congregación, insisto, en cualquier parte del mundo, llenos de asombro, llegan a congregarse llenos de expectativas.
[u100 356990-719469] Yo creo que mucha de la gente que está aquí llega de esta forma, por eso hacemos fila y por eso hay tanta expectativa y adoramos y cantamos a los gritos.
[u101 351870-730230] A mí me gusta cuando los adultos parece que son niños que observan mientras se desenvuelve un regalo en Navidad, cortesanos agradecidos que observan desfilar al rey.
[u102 326740-731230] Y venimos con esa.
[u103 396380-734740] Con esa expectativa que siempre, insisto, atrapa la unción.
[u104 342430-752940] Pero también he notado cientos de otros creyentes que se parecen a Shah, el rey mogol, o al Chapulín de mi historia, que solo ven el templo, el cielo raso, y no logran ver más allá del techo y sus mentes divagan, sus ojos se ponen vidriosos del sueño.
[u105 356990-753420] Yo los veo.
[u106 351870-764380] A veces estamos adorando y está como la ardillita de la era de Hielo, están así y si duermo con un ojo, se darán cuenta o pensarán que soy tuerto.
[u107 447960-770740] Otros miran el celular o están pendientes de la hora o bostezan.
[u108 395460-777420] Entonces todos los templos, todos los servicios, de hecho pierden su brillo al cabo de un tiempo.
[u109 335940-780780] En algún momento lo novedoso deja de ser novedoso.
[u110 682600-784540] Siempre, por más novedoso que sea, en un momento lo sagrado se vuelve común.
[u111 395460-789110] Entonces los adoradores de templos no tienen la intención de aburrirse.
[u112 789110-800870] ¿De hecho, casi es un insulto a vuestra inteligencia que vienes a aburrirte, porque quién prepararía a los niños o se levantaría a la madrugada y se acicalaría para venir para luego aburrirse?
[u113 356990-812480] Yo sé que hay gente que les encanta la iglesia y hasta algunos raros aman al pastor, pero las intenciones de los que se duermen no es volverse rancios.
[u114 812640-814840] Voy y me voy a dormir y me voy a aburrir.
[u115 342710-824040] No se levantan, insisto, temprano, se preparan, vienen cada domingo, pero en algún momento del peregrinar pierden de vista.
[u116 824040-829360] Perdemos de vista a quien en primera instancia pensábamos adorar.
[u117 395460-848370] Entonces los que adoran el templo los que adoran servir, los que adoran el hecho intrínseco de congregarse, los que adoran la doctrina, la sana, la supersana, la recontra hipersana o los que adoran el simplemente venir, es muy diferente a los que vienen a adorar a Dios.
[u118 346830-854730] Son muy distintos y podemos encontrar a ambos sentados en la misma congregación en cualquier sitio.
[u119 854730-858637] Pablo le escribe una carta a Roma y Dice en Romanos 1.
[u120 858637-867754] 23 Y cambiaron la gloria del Dios incorruptible en semejanza a una imagen de hombre corruptible y cambiaron la verdad de Dios.
[u121 870440-879800] Insiste el apóstol en una mentira, hablando y honrando y dando culto a criaturas antes que el Creador, el cual es bendito por los siglos.
[u122 342870-888200] Él es increíble que alguien pueda cambiar la verdad por la mentira y en vez de adorar a Dios, empiecen a adorar otras cosas que no merecen adoración.
[u123 395460-900770] Entonces cuando en algún momento, quiero pensar inconsciente, olvidamos a quien veníamos a adorar y esto no respeta la estatura espiritual de nadie.
[u124 901010-907010] Puede que tengamos 30, 40 años de creyentes, 50 años, y en algún momento lo sagrado se nos vuelve común.
[u125 326740-916800] Y ahí es cuando perdemos, al menos lo que yo creo, cuatro de nuestras principales armas que nos sostienen, que nos bendicen, que nos.
[u126 318340-921670] Que creo que son el leitmotiv, la savia de nuestra vida cristiana.
[u127 824040-930230] Perdemos de vista nuestras convicciones, perdemos de vista nuestro propósito, perdemos de vista nuestra adoración, caramba.
[u128 326740-932950] Y perdemos de vista nuestra alegría.
[u129 342710-933910] No es un tema menor.
[u130 326740-948500] Y aquí quiero hacer un paréntesis que es vital y necesario porque siempre yo sostuve que un avivamiento, que un mover de Dios, palabra que está en boga y que a veces está incluso sobreestimado.
[u131 317580-954700] Un avivamiento nunca surge de una teología novedosa, de descubrir algo novedoso.
[u132 954700-962340] Uy, en tal congregación parece que están haciendo tal cosa y hasta nos suena divertido y en ocasiones hasta es barroco.
[u133 342430-969220] Pero los avivamientos nunca surgen de una teología nueva, sino cuando regresamos a las bases bíblicas.
[u134 969540-986960] Muéstrame un avivamiento real y yo te voy a mostrar a alguien o a un grupo de gente que regresó a las bases, regresó a la oración, regresó a la búsqueda, regresó a lo que comúnmente se llama la senda antigua, tan fácilmente confundida con una doctrina externa de vestimenta.
[u135 986960-993906] Y uno de mis pasajes preferidos de la Biblia está en la segunda carta de Corintios, capítulo 11.
[u136 993906-1007365] 3, donde Pero me temo, dice Pablo, que así como la serpiente con su astucia engañó a Eva, los pensamientos de ustedes pueden que sean desviados de un compromiso puro y sincero con Jesús.
[u137 351870-1018170] A mí me fascina porque Pablo en una misma oración, es un compromiso puro y sincero el que hay que tener con el Señor.
[u138 516680-1022170] Simple, ni complejo ni complicado.
[u139 370780-1035230] Me temo que los pensamientos y esta esta cultura de tanto ruido te aparte del compromiso simple que deberías tener con el Señor.
[u140 1009490-1037030] Sincero y puro, punto.
[u141 1037590-1039110] Diáfano, transparente.
[u142 356990-1040470] Yo amo eso.
[u143 458900-1050310] Porque de otro modo nos volvemos como el rey mogol o el insecto de mi historia de la infancia, que perdemos de vista las viejas armas espirituales.
[u144 824040-1054910] Perdemos las cosas esenciales de la vida cristiana.
[u145 512800-1063870] Cuando David fue ungido como rey de Israel, subió de nivel obviamente espiritual, pero no accedió al trono de manera inmediata.
[u146 326740-1073070] Y en lugar de ahora luchar contra osos y leones, se subió al ring al poco tiempo a pelearse y a medirse con un guerrero de 3 metros llamado Goliat.
[u147 1073070-1079870] Conocemos la historia y este pequeño muchachito adolescente tenía una bolsa con piedras planas.
[u148 318540-1083550] Se dirige al sangriento campo de batalla, una piedra certera,
[u149 1086430-1088430] y el guerrero bravucón cae muerto.
[u150 1086670-1092590] El efecto especial va incluido con la ofrenda que vas a poner más tarde.
[u151 1094030-1102870] Entonces David cesa la situación decapitando a Goliat con la propia espada del gigante abatido.
[u152 1102870-1104030] Recordemos que él no tenía espada.
[u153 1086670-1105560] Él fue con una onda y las piedritas.
[u154 1105950-1110270] Así que le saca la espada y le corta la cabeza.
[u155 1111710-1113470] Esos son los más cortes de cabeza, ¿No?
[u156 1114990-1119230] Ahora, avancemos algunos años y David todavía no está en el trono.
[u157 1118550-1124870] En cambio, el celoso rey Saúl, petulante, lo está echando del palacio.
[u158 1086430-1126710] Y David tiene que huir para salvar su vida.
[u159 1126710-1128350] Estamos repasando la vida rápido.
[u160 1114990-1138460] Ahora David es un fugitivo sin preparación, sin plan a futuro, sin dinero, sin armas, sin ropa extra, sin comida enlatada, sin GPS.
[u161 1139020-1140540] ¿A dónde corre primero?
[u162 1086430-1143260] Y la Biblia narra que corre al templo.
[u163 1129390-1145100] Es el primer sitio donde va.
[u164 1118550-1149420] En su día más oscuro, David decide correr al templo.
[u165 1103470-1156140] No se fue a un bar, ni a los brazos de una mujer, ni se sumergió en los tentáculos de una adicción.
[u166 1104190-1160420] Fue donde sabía que estaba la presencia de Dios en el templo.
[u167 1095710-1163860] David, insisto, que ahora es fugitivo de su propio suegro.
[u168 1086430-1171540] Y tú pensabas que tenías problemas con tu suegro David conoce a un sacerdote llamado Abimelec.
[u169 1094030-1195800] Entonces el fugitivo David pide, El proscripto pide comida, el sacerdote lo alimenta y luego le pide a Abimelec David una cosa más y yo sé que esta es una petición poco común, estoy en un templo, pero yo tenía tanta prisa por escapar que me fui sin mis armas y puede que necesite alguna porque ahora soy un prisionero, un fugitivo.
[u170 1195800-1196400] Perdón.
[u171 1196880-1199760] ¿Tienes algún arma aquí en la casa de Dios?
[u172 1199760-1201680] ¿Tendrá algún arma guardada?
[u173 1086430-1209440] Y el sacerdote, como acto reflejo, mueve la cabeza negativamente No, David, aquí somos sacerdotes, no luchadores.
[u174 1210480-1212720] Tenemos cualquier cosa menos armas.
[u175 1186480-1221980] Pero luego el sacerdote hace memoria y espera un momento, A decir verdad, sí tenemos un arma en nuestra suerte de museo del templo.
[u176 1129390-1227260] Es la misma espada que usaste para cortarle la cabeza a Goliat.
[u177 1227660-1228900] ¿Tú crees que esa va a servir?
[u178 1118390-1234620] Está ahí de adorno, es como un memorial de lo que ocurrió en el campo de batalla en el valle de Ela.
[u179 1227660-1236220] ¿Tú crees que puede servir?
[u180 1086430-1243580] Y David se había olvidado que él mismo había llevado la espada al templo porque sabía de quién había sido la victoria.
[u181 1181780-1244940] Yo no me puedo quedar con esta esp.
[u182 1118390-1251960] Esta espada simboliza que Dios ha dado la victoria, que Jehová puso Israel por encima de los filisteos, la había llevado al templo
[u183 1254600-1259800] y ahora le ofrecen la misma espada pero para nuevas victorias.
[u184 1260040-1273240] Entonces David expresa, a esto quería llegar, esta frase magnífica, maravillosa en el primer libro de Samuel, capítulo 21, versículo 9 Ninguna como ella, Dámela.
[u185 1273710-1273950] No.
[u186 1254600-1276510] Y bueno, capaz que está media arrumbrada.
[u187 1276510-1277990] Andá, ¿Sabes si sirve?
[u188 1277990-1279190] Es la espada del enemigo.
[u189 1268200-1281310] Él ninguna como esa.
[u190 1281630-1285390] Con esa le corté la cabeza a esta bola de grasa, a este bravucón.
[u191 1260040-1287990] Entonces este es el punto.
[u192 1287990-1298830] Las armas que Dios nos proveyó en el pasado, aunque a veces parecen arcaicas, siguen funcionando hoy porque no hay nada nuevo bajo el sol, en las cosas de Dios.
[u193 1273710-1309770] No necesitamos ni empoderarnos, ni escuchar muchos coaching que nos digan qué hacer, ni profesionales que nos laven la cabeza, ni decretos apostólicos, ni declaraciones proféticas.
[u194 1268200-1314890] El mismo nombre que es sobre todo nombre, la misma sangre que fue vertida en la cruz del calvario.
[u195 1315130-1325810] Alguien tiene que celebrar por eso el mismo poder del Espíritu Santo, la oración, el ayuno, son las viejas espadas para vencer y resistir.
[u196 1273710-1326490] No ha cambiado.
[u197 1260040-1336120] Entonces a veces la gente escucha de algún mensaje por ahí, el chiste en mi caso cuando hablo de alguna suegra u otro género demoníaco, pero.
[u198 1254600-1343600] Y es un payaso, no voy autopromocionarme.
[u199 1258360-1356890] Pero yo siempre digo que no me he movido nunca en tantos años de las viejas armas, de la vieja espada, de lo que aprendí, porque aunque esos servicios cuando pequeño eran abúlicos, yo recibía y recibía algunas cositas, no entendía otras.
[u200 1277430-1373050] Sí en algún momento una palabra me tocó y eran las viejas ayunar, orar, proclamar, leer la palabra, nutrirse el espíritu, no había nada novedoso, no eran teologías novedosas, no era esperar una palabra profética, no era una declaración apostólica.
[u201 1373210-1377610] Todos estábamos con las viejas armas que funcionaban y siguen funcionando.
[u202 1254600-1384410] Y cuatro de esas viejas espadas, insisto, funcionan hace siglos y funcionan hoy.
[u203 1384410-1409970] Podría quedarme toda la mañana hablando de varias herramientas o armas que Dios nos ha dado, pero por lo menos cuatro que tienen que ver, insisto, con nuestras convicciones, nuestro propósito, nuestra adoración y nuestra alegría, que son las cuatro armas que perdemos a priori apenas empezamos a adorar el templo y nos olvidamos del Dios al que queríamos adorar en el templo.
[u204 1332680-1414520] Cuando lo sagrado se vuelve común, perdemos estas cuatro armas que son valiosas.
[u205 1414920-1431800] Dicho esto, yo voy a tomarme unos breves minutos para que repasemos junto estas cuatro viejas espadas, miles de veces predicadas, cientos de veces profesadas, pero que a menudo solemos olvidar.
[u206 1432120-1437480] Ergo, ¿Cómo perdemos la vieja espada de nuestras convicciones?
[u207 1437480-1440270] Ustedes dirán, ¿Cómo se pueden perder las convicciones?
[u208 1440350-1443870] Tengo años de peregrinar cristiano.
[u209 1274510-1461950] Bueno, si somos como el Chapulín de mi historia y toda nuestra vida está reducida a las vigas del techo del domingo, carecemos de principios que nos sostengan de lunes a sábado cuando no estamos aquí, cuando no estamos congregados, independientemente de dónde se congregue cada quien.
[u210 1277430-1476040] Si nos volvemos inconsciente o conscientemente adoradores del templo, como el rey Mogol de mi historia, sólo nos van a importar las opiniones de los que también vienen al templo el mismo día que nosotros.
[u211 1254600-1495920] Y si la opinión de los que vienen al templo determina nuestras convicciones, si repetimos como loros todo lo que incluso el pastor nos dice y no tenemos nuestra propia convicción, nuestro propio fundamento, ¿Qué ocurre cuando el pastor se equivoca, cuando la mayoría se equivoca y decimos, bueno, pero todo el mundo va para allá?
[u212 1496000-1498640] Seguir traseros de ovejas es hipnotizador.
[u213 1504720-1506640] Y uno dice, todo el mundo va para allá.
[u214 1507600-1514080] Entonces, cuando no tenemos las propias convicciones, repetimos lo que ocurre en el templo el domingo.
[u215 1504720-1515680] Y esa es toda nuestra vida espiritual.
[u216 1504720-1527060] Y hay cientos de cristianos que relativizan su relación con Dios bajo el axioma yo como estiércol porque un millón de moscas no pueden estar tan equivocadas.
[u217 1504720-1529340] Y uno dice, ¿Por qué estás haciendo tal cosa?
[u218 1504720-1534020] Y bueno, porque todo el mundo lo hace y porque lo repito y porque hay gente que vive como yo.
[u219 1534260-1540020] Pero el solo hecho de repetir, de congregarse y de hecho de creer en Dios, no nos hace cristianos.
[u220 1540500-1542940] Te dirá ¿Cómo que no nos hace cristianos creer en Dios?
[u221 1509600-1546020] No, de hecho no hay un solo demonio en el infierno que sea ateo.
[u222 1549260-1550100] Pero los demonios creen.
[u223 1550100-1551660] Claro, creen y tiemblan.
[u224 1551660-1553180] No hay un demonio que no crea en Dios.
[u225 1551020-1555660] Y sin embargo, los demonios no son convertidos necesariamente.
[u226 1556380-1558660] Digo, por si tienes un marido que mi marido cree.
[u227 1558660-1559900] Bueno, los demonios también.
[u228 1562380-1566140] Y ese es el peor síndrome que podemos padecer.
[u229 1567020-1570300] Creer en Dios y no estar dispuesto a que nos cueste algo.
[u230 1571980-1573780] Yo siempre digo ¿Que le puedo predicar?
[u231 1569060-1578820] A mí me encanta cuando hago la gira y me dicen que hay un 80% de inconversos en la sala.
[u232 1569060-1580210] A mí me gusta porque esas tierras frescas.
[u233 1563300-1593240] El problema es cuando la gente relativiza y entonces no se consideran tan afuera como para merecer un cambio, pero tampoco se consideran tan adentro como para que les cueste algo el seguir a Cristo.
[u234 1585440-1598200] Se le llama relativismo o Teología del Pluralismo.
[u235 1574340-1609230] Cuando la mayoría, incluso la mayoría de los anglos, ya que esto no salga de acá, que quede acá entre los hispanos, pero la mayoría de los anglosajones ustedes este es un país cristiano.
[u236 1609390-1612510] Sí lo es de manera etimológica.
[u237 1612990-1617390] ¿Pero el gran problema es que es muy difícil que llamemos a un vecino gringo y usted cree en Dios?
[u238 1562380-1618590] Y te no, no creo en Dios.
[u239 1569060-1619910] A mí me van a comer los gusanos.
[u240 1617470-1624310] Te van a no, no, yo creo en Dios, pero le he dado mi Jesús, Buda o Taylor Swift.
[u241 1573020-1625230] Le da lo mismo.
[u242 1627390-1638860] Todos llegamos a ese momento en la vida que tenemos que dejar de relativizar las convicciones y definir qué tan comprometida está nuestra relación con Jesús.
[u243 1638860-1642420] Independientemente, insisto, de cuántos años tengamos de convertido.
[u244 1643860-1650260] Esto nos lleva a una pregunta que nos resultaría reveladora a la mayoría de nosotros seguir a Jesús.
[u245 1628670-1657860] A los que estamos aquí presentes y no tienen que responder de manera articulada, ¿Nos ha costado algo?
[u246 1658420-1661540] ¿Te costó algo servir a Jesús, seguir a Jesús?
[u247 1663210-1674770] Porque hay gente que no le molesta de que Jesús llegue y mejore un poquito sus vidas, como quien contrata un seguro médico o se suma a Angua o Herbalife, que los prospere otro poco, que los sane de alguna otra cosita.
[u248 1674770-1679930] Entonces uno dice, Jesús, cuando puedo voy a la iglesia, es nice, es buen tipo Jesús.
[u249 1679930-1682890] Pero te dirían lo mismo de Jesús como de John Lennon, le dan lo mismo.
[u250 1633700-1688840] Y conocemos gente que cree que un poquito de maquillaje ya va a estar bien.
[u251 1679930-1692200] Pero Jesús no quiere que nos maquillemos, quiere hacernos de nuevo.
[u252 1674770-1699080] Entonces muchos queremos decorar un poquito y Jesús quiere derribarlo todo y construir desde cero.
[u253 1652460-1703560] No es que Jesús es un maquillaje, Jesús no es un tratamiento dermatológico.
[u254 1705880-1709480] Me tapo con crema, me pongo la faja, me ajusto y voy así por la vida.
[u255 1711400-1715020] Porque en un momento hay que liberar a Willy, en un momento hay que o no.
[u256 1716140-1721740] Entonces creer en Jesús no es lo mismo que tener convicciones serias.
[u257 1716940-1722860] Creer creen todos.
[u258 1722940-1731340] De hecho estamos en un país, le cuento a la gente de América Latina, en toda la región, donde en Estados Unidos, la Unión Americana, la mayoría yo no, yo creo en Dios.
[u259 1708400-1741630] Y cuando sucede un hecho como el de hace unos días atrás, de un asesinato o de un atentado, todo el mundo empieza a invocar a Dios.
[u260 1741630-1743190] Pasó lo mismo en el 911.
[u261 1719100-1746190] Es muy difícil decir, aquí nadie cree en Dios.
[u262 1734580-1747990] El problema es la relativización.
[u263 1729820-1761310] Yo siempre tuve un poco de lástima de Poncio Pilato, porque decía, el tipo se lavó las manos, el tipo no quería condenar a Jesús, pero al no decidir, decidió, al lavarse las manos, relativizó.
[u264 1761310-1762150] Dijo, es un buen tipo.
[u265 1762150-1767470] Para mí, la verdad que el tipo es nice, sí, qué sé yo, si quieren lo azoto 40 veces y lo libero.
[u266 1763510-1769670] Si quieren que lo crucifique y lo crucifico, le da lo mismo.
[u267 1770640-1771640] Eso es lavarse las manos.
[u268 1771640-1775440] Esa es la relativización que es más peligrosa que el ateísmo.
[u269 1716140-1782160] Entonces tenemos la tendencia de definir al cristianismo como el simple acto de creer.
[u270 1756550-1783600] Pero no se trata de creer.
[u271 1716940-1789160] Creer tiene que ver con una simple aceptación intelectual, cree en Jesús.
[u272 1789160-1790480] ¿Y quién no va a creer en Jesús?
[u273 1763510-1794960] Sí todo el mundo en Semana Santa incluso y en Navidad, se acuerda y cree en Jesús.
[u274 1756550-1798970] Pero creer es el primer paso, el segundo es seguir.
[u275 1708400-1809610] Y ambas palabras no son antagónicas, no son excluyentes, están de hecho conectadas, constituyen el corazón, los pulmones de la fe.
[u276 1785200-1812250] Una cosa no puede existir sin la otra.
[u277 1734580-1814730] El seguir forma parte de creer.
[u278 1814730-1818490] Muéstrame a alguien que cree y yo te tengo que mostrar alguien que sigue al Señor.
[u279 1708400-1825700] Y creer significa seguir, no es pasar al altar y repetir como loro, es creer y seguir.
[u280 1708400-1836900] Y entretanto no rompamos esa dicotomía entre creer y seguir, las iglesias se van a seguir llenando de simpatizantes, de observadores de techo como mi Chapulín.
[u281 1838340-1839220] Ay qué lindo.
[u282 1734580-1844900] El techo se va a llenar de gente así, porque creen pero no siguen.
[u283 1708400-1852630] Y si uno les hace un seguimiento tipo Big Brother durante toda la semana, se da cuenta que no es un seguidor, no es una seguidora.
[u284 1756550-1854030] Pero sí viene el domingo a creer.
[u285 1763510-1855350] Sí, pero el Chapulín también.
[u286 1857590-1861310] Me pregunto, los que se acaban de conectar, Ay, está metiendo al Chapulín Colorado.
[u287 1861310-1863589] Vaya al principio del mensaje, antes de criticar.
[u288 1864630-1874950] Entonces hemos escrito la palabra creer con mayúsculas y todo lo que tiene que ver con seguir lo escribimos como un subtítulo, como una nota al pie, como es una opción, lo principal que crea.
[u289 1875110-1877190] ¿Cuántas decisiones de fe hubo?
[u290 1877270-1878550] Oh, tres mil.
[u291 1878710-1879870] ¿Y cuántos siguieron?
[u292 1879870-1883270] Bueno, eso después con el tiempo no creer va a conseguir.
[u293 1884550-1886950] Jesús decía, no decías crean en mí, con eso basta.
[u294 1881270-1889869] Él decía síganme, similar a cuando.
[u295 1889869-1895990] Pero a veces nos comportamos como cuando compramos un celular y nos dicen ¿Desea asegurarlo por si se rompe o por si se le pierde?
[u296 1868070-1898310] Y a veces decimos no, no, no, está bien, no creo.
[u297 1868070-1900550] Y en la iglesia predicamos lo mismo por años.
[u298 1868430-1907080] Lo importante es que ya compró a Jesús, ahora si lo desea, por 20 centavos más lo puede seguir.
[u299 1907480-1908680] Agrandamos el combo.
[u300 1889869-1916040] Pero no se sienta presionado, no tiene que decidirlo ahora, piénselo, cualquier cosa, luego nos llama un líder, lo va a llamar en la semana.
[u301 1864630-1922920] Entonces tenemos que preguntarnos, insisto, seguir, además de venir los domingos, ¿Nos ha costado algo?
[u302 1923480-1927800] Porque no cuenta prepararnos y alistarnos temprano para venir el domingo.
[u303 1882390-1928680] A mí me cuesta.
[u304 1881590-1934160] No, eso no cuesta, porque así vamos también a un concierto o podemos ir a una boda o un cumpleaños.
[u305 1934960-1939680] ¿De qué manera seguirlo ha interferido con nuestra vida normal?
[u306 1934960-1935680] ¿De qué manera?
[u307 1923480-1948240] Porque no se nos permite ser seguidores encubiertos o Nicodemos visitadores de noche.
[u308 1948719-1952720] ¿Cuándo fue la última vez que seguir a Jesús nos costó una relación?
[u309 1953600-1963200] Alguien a que supuestamente amábamos o queríamos o teníamos como amigo y de repente sentíamos que era tóxico y era un impedimento para que sigamos al Señor y tuvimos que decidir.
[u310 1948719-1971440] ¿Cuándo fue la última vez que seguir a Jesús nos costó una promoción, un empleo, un ascenso, una amistad de años?
[u311 1973600-1978760] ¿Cuándo fue la última vez que nos costó unas vacaciones, pero que está mal?
[u312 1978760-1979680] No digo que esté mal.
[u313 1973600-1981480] ¿Cuándo fue la última vez que te costó unas vacaciones?
[u314 1974840-1987840] Que este dinero que tenía para las vacaciones, el Señor me ha hecho sentir que lo tengo que invertir en esto para el Señor.
[u315 1973600-1974840] ¿Cuándo fue la última vez?
[u316 1990330-1996650] ¿Entonces podemos decir realmente que estamos llevando su cruz si nunca nos costó nada?
[u317 1998170-2007170] Porque si no ha habido sacrificio, y no estoy hablando de salvación, la salvación no se paga ni en cuotas, ni el down payment no se paga, es gracia.
[u318 2000090-2011530] Estoy hablando del sacrificio de seguir, que es diferente a creer.
[u319 1994650-2017690] Si al menos nos hemos sentido un poco incómodos, capaz que no estamos llevando la cruz.
[u320 1999690-2021110] Y no deberíamos cantar de que estamos llevando la cruz.
[u321 2022230-2030150] Nadie logra sostener la vieja espada de sus convicciones si nunca ha tenido que renunciar a nada.
[u322 2010730-2037110] A veces es tiempo de calidad con la familia, a veces significa dejar de lado un empleo.
[u323 1999690-2042950] Y no estoy diciendo que eso es parte de la salvación o si agrada o agrada menos a Dios.
[u324 2034950-2045630] Significa de que creer es una parte, seguir es otra.
[u325 2039190-2046790] Eso es convicciones, gente.
[u326 1999690-2057970] Y si perdemos la vieja espada de las convicciones, tampoco vamos a tener nunca un dique que detenga el vertedero de basura que nos ofrece la cultura y la sociedad.
[u327 1998170-2060570] Porque el relativismo hace eso.
[u328 2060570-2069410] Como dije, nos volvemos amplios y decimos, ¿Quién no mira una serie de Netflix sabiendo de que un poco de basura va a consumir?
[u329 1974840-2083020] Qué es lo que nos hace al principio la sensación de rechazo, de ver algo que no está bien aún con nuestros hijos, y después anestesiarnos y que ya no nos choque al espíritu.
[u330 1978760-2092460] No hablo de doctrina, hablo de qué hace que ya no nos choque lo que a nuestros padres, no digo a los abuelos los hubiese espantado.
[u331 2093820-2099380] Cuando vemos la cantidad de basura que ingerimos a través del streaming, ¿Cuál es el filtro?
[u332 1974320-2104340] La doctrina En la vida te voy a decir qué ver y qué no ver.
[u333 2104820-2108020] Yo vengo del control y nunca me pondría en controlador.
[u334 2108660-2112420] Además, no es el control el que cambia a la gente, sino la convicción del Espíritu Santo.
[u335 2112580-2114580] Así que yo no te voy a decir qué hacer y qué no hacer.
[u336 2115140-2118420] Entonces, ¿Qué es lo que acá nos dice qué está bien y qué está mal?
[u337 2119700-2122860] Bueno, pero si lo que está mal no se puede mirar, no puedo mirar nada.
[u338 2122860-2128510] OK, pero como dije siempre, ¿Quién comería una pupusa?
[u339 2129870-2131990] ¿Noventa y nueve por ciento chicharrón?
[u340 2131990-2133150] Uno por ciento de caca.
[u341 2135870-2137190] No, pero es chicharrón.
[u342 2137190-2139310] La caca está mezclada entre el chicharrón es 1%.
[u343 2139310-2141470] ¿Quién la comería sabiendo esa información?
[u344 2142350-2150030] Entonces cuando empezamos a comer estiércol, porque un millón de moscas no podrían estar equivocadas, significa que perdimos la espada de las convicciones.
[u345 2150030-2150590] ¿Por qué?
[u346 2150590-2152010] Por ser adoradores de templo.
[u347 2144590-2154920] Porque no sabemos a quién adoramos.
[u348 2154920-2161600] Y como no sabemos a quién adoramos, no sabemos ni siquiera cómo adorar con nuestra vida.
[u349 2162560-2165680] Eso explica el proceso de la santidad.
[u350 2148030-2168040] Qué está bien, qué no está bien.
[u351 2168040-2181330] Hay un sensor interno, un autocontrol de calidad interno que nos dice qué hacer, qué decir, qué contar, qué no contar, cuándo detener un chisme, cuando parar los oídos para que no nos tiren basura de un chisme.
[u352 2135870-2183170] No hay forma de hacer una lista.
[u353 2135870-2190610] No podemos hacer 613 leyes como la Torá y que esto no lo hagas y esto no haga, porque el legalismo no funciona.
[u354 2191010-2194290] Buscaremos la manera y más que somos hispanos, siempre estamos buscando la trampa.
[u355 2194290-2196210] Todo no funciona, el legalismo.
[u356 2199330-2201170] Entonces, ¿Cuál es el control interno?
[u357 2201170-2203250] La espada de las convicciones.
[u358 2204640-2205920] Esto no me edifica.
[u359 2206320-2207440] Ya no hablamos de pecado.
[u360 2204640-2209640] Esto no me edifica, esto me atrasa en la carrera.
[u361 2209640-2213360] Dijo Pablo, despojado del pecado y de todo peso.
[u362 2212240-2216080] Y siempre estamos hablando del pecado y del peso.
[u363 2217040-2222320] ¿Quién sale a correr una maratón con botas, con un sacón, con un sombrero?
[u364 2212800-2213360] Peso.
[u365 2212800-2226320] Peso no es pecado, pero me atrasa en la carrera.
[u366 2199770-2231280] ¿Cuál es el tamiz para saber qué peso llevo y qué peso No llevo?
[u367 2202530-2203250] Convicciones.
[u368 2234160-2235720] ¿Cuáles son nuestras convicciones?
[u369 2235720-2237640] ¿Algún día yo me voy a ir o me voy a morir?
[u370 2236880-2238600] O ustedes se van a morir.
[u371 2238600-2244480] Primero, porque yo estoy más joven, entonces ¿Quién nos va a decir qué hacer y qué no decir?
[u372 2220200-2250080] Un día no tendremos la Biblia a mano, no tendremos streaming, no sé, o vendrá otra pandemia.
[u373 2250480-2253120] ¿Qué convicciones nos van a sostener?
[u374 2253680-2259770] Esa es la vieja espada que solemos perder cuando nos volvemos como el Chapulín o como el rey Mogol.
[u375 2260330-2264490] Segundo, ¿Cómo perdemos la vieja espada de nuestro propósito?
[u376 2266010-2272410] Cuentan que alguna vez un gorrión silvestre se acercó a un canario que estaba encerrado en una jaula.
[u377 2212240-2279210] Y el gorrión salvaje o silvestre le pregunta al canario en ¿Cuál es tu propósito?
[u378 2212240-2285200] Y le dice el mi propósito es comer semillas, comer alpiste.
[u379 2285200-2287200] ¿Semillas para qué?
[u380 2275130-2288640] Pregunta el gorrión de afuera.
[u381 2288640-2291680] Bueno, para poder ser fuerte, ¿Para qué?
[u382 2288640-2294880] Bueno, para poder cantar todas las mañanas, respondió el canario.
[u383 2295840-2297000] ¿Y qué pasa cuando canta?
[u384 2297000-2298960] Ah, cuando canto me das más semillas.
[u385 2199330-2301560] Entonces le dice el gorrió.
[u386 2202210-2307440] De modo que come semillas para ser fuerte, para poder cantar, para que te den más semillas, para que puedas comer.
[u387 2307840-2308560] Ajá.
[u388 2204760-2311380] No, mijo, eso no es un propósito, le dijo el gorrión.
[u389 2309200-2313860] Eso es precisamente lo que se llama esclavitud.
[u390 2314180-2316420] Eres un hámster dando vuelta en la ruedita.
[u391 2199330-2321780] Entonces es muy difícil encontrar un propósito en un cristianismo enjaulado.
[u392 2212240-2326380] Y todos nacemos con un anhelo intenso de significación.
[u393 2218040-2333620] Una vez que tenemos convicciones, queremos significación, validación, una búsqueda de sentido a nuestra existencia.
[u394 2334420-2336420] Algunos buscan la importancia en una carrera.
[u395 2281610-2341320] Mi propósito es ser médico, entonces yo soy médico.
[u396 2204760-2343440] No te dedicas a la medicina.
[u397 2200170-2346240] El doctorado no te da identidad.
[u398 2200050-2351600] Es una profesión excelente, pero difícilmente sea una justificación de tu existencia.
[u399 2353600-2360720] La gente que yo soy esto son lo que hacen, pero por consiguiente hacen mucho, porque si no hacen, no tienen validez.
[u400 2360720-2363440] Sienten que no se autovalidan.
[u401 2363600-2367280] Trabajan muchas horas porque si no lo hacen, sienten que no tienen identidad.
[u402 2359800-2373670] Tienen que trabajar porque ellos tienen su identidad asignada de lo que hacen.
[u403 2373670-2375070] Otros son los que tienen.
[u404 2375550-2381390] Creen encontrar propósito en un nuevo auto, en una nueva casa, y ahora tengo una troca.
[u405 2384350-2387070] Otros buscan significación a través de sus hijos.
[u406 2387790-2395810] Viven vicariamente a través de sus vástagos y mi razón para vivir son mis hijos, pero nadie nació para sus hijos.
[u407 2396290-2406330] Esa no puede ser nuestra significancia, porque un día los hijos se van a volar, van a dejar el nido vacío y vamos a quedar tirados en un sillón, abandonados pensando que ya no hay significado.
[u408 2406330-2418690] Por eso mucha gente empieza a morir a causa del nido vacío y otros buscan su validación sirviendo a Dios y no se dan cuenta que son un palacio sin rey a quien honrar.
[u409 2420220-2423100] Sirven, sirven, sirven, pero no adoran.
[u410 2405250-2426060] Ya perdieron las convicciones y ahora están perdiendo el propósito.
[u411 2427420-2432620] Una vez le traje a uno de mis hijos la camiseta del Barça firmada por todos sus jugadores titulares.
[u412 2432940-2435339] Costó mucha oración.
[u413 2438140-2446700] La camiseta es una de las tantas que se vende por algo de así como 80 euros en los sitios oficiales, o sea, uno puede conseguir esa camiseta en cualquier sitio.
[u414 2447370-2449210] Lo que la hace singular son las firmas.
[u415 2447370-2451530] Lo mismo ocurre con nosotros.
[u416 2443100-2457770] En el esquema de la naturaleza no somos las únicas criaturas con carne, pelo, sangre y corazones.
[u417 2447370-2465810] Lo que nos hace especiales a nosotros, a diferencia de cualquier otro animal, es la firma de Dios en nuestras vidas.
[u418 2453890-2468050] Somos una obra rubricada por Dios.
[u419 2468050-2468730] ¿Sí o no?
[u420 2438140-2471930] La firma So Nature.
[u421 2473460-2481940] Yo me acuerdo que iba a la escuela primaria y yo vivía para el privilegio de ejecutar las tareas más honrosas de la maestra.
[u422 2441180-2486900] Como nunca fui un muchacho popular, cuando la maestra decía Gebel, venga.
[u423 2460050-2491460] A mí me emocionaba apagar las luces para que la maestra pasara diapositiva.
[u424 2473460-2493180] Yo me sentía el segundo a bordo.
[u425 2443100-2501760] En el colegio, el más alto privilegio era hacer un mandado para la maestra, ir a buscar tizas, un borrador, lo que me mandara a hacer.
[u426 2501760-2503800] Aparte me tiraba onda la maestra.
[u427 2507240-2511080] Yo tenía siete años, ella tenía 72, pero había algo.
[u428 2513320-2524070] Y si la maestra me escogía para hacer el mandado, el corazón se me aceleraba y yo me acercaba a su escritorio con veneración y ella me explicaba mi misión del día y me daba el.
[u429 2513320-2527540] Y me daba un pase, un fast pass para ir por todo el colegio.
[u430 2527540-2528220] Vaya, vaya.
[u431 2513320-2530460] Y si me para alguien, vaya con el pase.
[u432 2530620-2539340] Entonces era un papelito firmado por la maestra que me hacía andar por el edificio y se me abrió un mundo nuevo para mí.
[u433 2530620-2541060] Entonces andaba con el pase.
[u434 2541060-2543100] Así tardaba en buscar la tiza.
[u435 2513320-2545860] Y si algún maestro me ¿Qué hace acá fuera de la clase?
[u436 2519840-2547020] Yo le mostraba el pase.
[u437 2553660-2556620] Si alguien me preguntaba dónde iba, yo sacaba el pase y se lo mostraba.
[u438 2557180-2560860] Imaginate, un argentino ya es agrandado de por sí con pase.
[u439 2562940-2567100] No hay nada peor que un argentino con pase o con primera fila.
[u440 2567900-2569220] Cuando vayan suban un avión.
[u441 2569220-2570700] Fíjense en los que viajan en business.
[u442 2571260-2576940] Son gente que sube así, con pechito de paloma y se sienta viendo cómo pasan los esclavos para el fondo.
[u443 2578820-2590260] Pero además van a notar cuando el que está adelante es argentino, porque cuando pasa el que viene buscando el 52 AF, le Señorita, más jugo de naranja, por favor.
[u444 2591780-2595700] Una vez que pasen esto, plebeyo, me traes un poquito de.
[u445 2580940-2597300] Es como quiere demostrar.
[u446 2597380-2600180] Yo estoy acá por argentino más que por otra cosa.
[u447 2572860-2602740] Así que imagínate lo que era yo con un pase.
[u448 2602740-2606100] Ese trozo de papel firmado por la maestra significaba que yo estaba seguro.
[u449 2574380-2614050] Y todos nosotros tenemos ese pase de Dios, aunque parezca un infantilismo colgado del corazón.
[u450 2574380-2619490] Y si confiamos alguna vez en Jesús como nuestro Salvador, la Biblia dice que estamos en Él.
[u451 2619810-2628850] Entonces, cuando alguien nos no eres lo suficientemente bueno, no das la medida, no das el ancho, no me gusta tu liderazgo, no te corresponde estar aquí, solo Hay que hacer.
[u452 2631570-2632530] ¿Qué pasó?
[u453 2634290-2635090] No manches.
[u454 2640030-2643950] Somos significativos no por lo que hacemos, sino debido a quién pertenecemos.
[u455 2644670-2658190] Entonces, cuando uno adora no al techo, sino a Dios, cuando dejamos de ser un palacio sin rey a quien honrar, no sólo recuperamos la vieja espada de las convicciones, sino la vieja espada de la significación.
[u456 2658270-2663070] Venimos y vivimos una vida con Cristo y eso nos da significado.
[u457 2641230-2667770] No importa que nos digan, no importa un cuerno lo que hablen de nosotros.
[u458 2668170-2669450] Ay, los haters.
[u459 2668170-2670610] Ay, me están atacando.
[u460 2663670-2676650] Importa un cuerno los seguidores de las redes cuando uno tiene significación en el Señor.
[u461 2677130-2680410] Tercero, ¿Cómo perdemos la vieja espada de nuestra adoración?
[u462 2680570-2684170] Ustedes dirán, ¿Y quién puede venir a la iglesia y no adorar?
[u463 2684570-2700100] Yo no sé si alguna vez escuchaste la historia del tipo que una noche buscaba la llave de su auto dentro de la casa y su esposa lo empieza a ayudar en la búsqueda, hasta que le preguntó ¿Pero de verdad no te acuerdas en dónde se te pudieron haber caído la llave del auto?
[u464 2659070-2702580] Y él sí, me acuerdo, se me cayeron afuera en la calle.
[u465 2709780-2711940] ¿Y entonces por qué lo estás buscando dentro de la casa?
[u466 2711940-2714180] Ah, porque acá adentro hay más luz, dijo el tipo.
[u467 2710060-2723800] Entonces, si estamos buscando las llaves que perdimos en la calle, hay que buscarla en el lugar donde las perdimos.
[u468 2724200-2729280] Y si estamos buscando lo sagrado, no vamos a encontrarlo el domingo debajo del techo.
[u469 2729280-2732760] Con la mentalidad de insecto visitante de templo.
[u470 2726240-2733880] No lo vamos a encontrar.
[u471 2726240-2737880] No digo que no venga, digo, no encontrarás aquí lo que perdiste el miércoles.
[u472 2726240-2742040] No vas a encontrar acá la paz que no tuviste el jueves.
[u473 2744370-2748290] El ataque de ira que tuviste el lunes por la mañana o el viernes por la noche.
[u474 2748290-2752050] No se va a ir por arte de magia dos horas el domingo.
[u475 2744890-2756690] De hecho, vamos a volver al chapulín de nuestra historia, al insecto de nuestra historia.
[u476 2756690-2763970] Imaginemos que estos insectos ortópteros son muy avanzados y se hacen preguntas filosóficas y teológicas.
[u477 2756690-2770450] Imaginemos ¿Y habrá vida más allá de las vigas del techo del templo?
[u478 2761570-2773450] Y algunos saltamontes creen que la hay.
[u479 2773770-2776370] Debe haber un creador de este lugar magnífico.
[u480 2744890-2779290] De otra manera, ¿Quién encendería las luces?
[u481 2780170-2781290] ¿De qué otra manera?
[u482 2780170-2785610] ¿De dónde vendría ese aire que sopla desde las rejillas?
[u483 2786330-2794410] Entonces algunos saltamontes, como resultado de su asombro por lo que pueden ver, adoran lo que no pueden ver.
[u484 2795290-2797850] Dicen, no, acá hay aire acondicionado, acá hay luz, hay sonido.
[u485 2797850-2799370] Tiene que haber una mano detrás de esto.
[u486 2799700-2801700] Ven todo esto y adoran lo que no pueden ver.
[u487 2801940-2814180] Otros insectos discrepan, estudian un poco y concluyen que las luces se encienden debido a la electricidad, que el aire sopla debido a los conductos de aire acondicionado.
[u488 2786330-2817420] Entonces, ya sabemos cómo funciona todo esto.
[u489 2817420-2819380] Dejen de creer en un ser superior.
[u490 2748290-2822020] No hay nada que nos asombre, insectos.
[u491 2748290-2823940] No hay nadie a quien adorar.
[u492 2799090-2828500] Esto funciona porque hay electricidad, porque hay sonido y porque hay aire acondicionado.
[u493 2829460-2831980] Ustedes dirá medio tonto este segundo insecto.
[u494 2761570-2834180] Y sí, pero nosotros cometemos el mismo error.
[u495 2818260-2853300] En un momento comprendemos cómo se forman las tormentas, cartografiamos los sistemas solares, trasplantamos corazones, medimos las profundidades de los océanos, enviamos señales a planetas distantes y nosotros, los pequeños saltamontes, estudiamos el sistema y aprendemos el funcionamiento de todo.
[u496 2761570-2856080] Y ni te cuento los pastores o predicadores.
[u497 2816060-2866520] Sabemos qué botón tocar, cuándo cortar la música, cuándo meter adoración, cuándo pedir el dinero, cuando la gente está llorando un poco y es el momento de pedir una segunda ofrenda.
[u498 2869320-2879400] Cuando aprendemos el funcionamiento, perdemos el misterio y fundamentalmente perdemos la majestad y lo sagrado se nos vuelve común.
[u499 2880560-2885760] Ustedes ¿Cómo puede ser que alguien tan ungido se transformó en un profesional?
[u500 2874120-2889880] Y no estoy en contra, yo creo que soy el tipo más profesional que conozco.
[u501 2877320-2893680] Lo que estoy diciendo cuando solamente se convirtió en un profesional.
[u502 2874120-2898880] Y es irónico, pero mientras más sabemos, menos creemos.
[u503 2874120-2903840] Y el conocimiento debería ser al revés, debería estimular nuestra adoración.
[u504 2904800-2915860] ¿Quién tiene más razones para adorar que el astrónomo que vio las estrellas, o que el cirujano que tuvo el corazón en una mano, o el oceanógrafo que estudió los abismos?
[u505 2916180-2919300] Entonces, mientras más sabemos, más deberíamos maravillarnos.
[u506 2895920-2933300] Pero es paradójico, mientras más sabemos, mientras más años de creyentes tenemos, menos adoramos, porque nos asombra descubrir el interruptor de la luz antes que descubrir al que inventor de la electricidad, el que inventó la electricidad.
[u507 2934260-2936670] Eso se llama lógica de cerebro de Chapulín.
[u508 2937460-2940780] Si yo fuera un pastor moderno, dile al que está a tu lado, no seas Chapulín.
[u509 2895920-2944980] Pero no te voy a decir eso en lugar de.
[u510 2926339-2950660] Porque a mí me reventaba que me hicieran repetir, así que nunca haré repetir a la gente, pero tengo una gana que le diga Chapulín.
[u511 2953300-2956500] En lugar de adorar al Creador, adoramos la creación.
[u512 2957220-2966980] Y dijo Pablo, y cambiaron la verdad de Dios por la mentira, honrando y dando culto a las criaturas antes que el Creador, el cual es bendito por los siglos.
[u513 2968320-2988880] Mirá, cuando yo llegué a este país, yo amaba los parques temáticos, como todos los que llegamos a este país por primera vez, yo me crié, veía imágenes de Disneyland en blanco y negro en un programa que se llamaba El mundo de Disney, y le decía a mi si alguna vez voy a ese parque, voy a vivir ahí adentro, nadie me va a sacar.
[u514 2975560-2997480] Me voy a esconder en la casita de Mickey, la de Mini, para que no hablen mal, y no voy a salir
[u515 3000840-3002840] por lo menos a morir machito, ¿No?
[u516 3005480-3012600] Y después, cada vez que venía una visita de Argentina, yo era el anfitrión encargado de mostrarle el enorme reino mágico.
[u517 3005760-3019500] Después de unas 8 o 10 visitas, empecé a perder el encanto, pensé que nunca me iba a pasar.
[u518 3005480-3024690] Y una vez, durante el recorrido, por ejemplo, de los Piratas del Caribe, contestaba el celular.
[u519 3034050-3039890] Incluso hasta me he quedado dormido, principalmente en ese jueguito de las muñequitas que hacen así,
[u520 3042050-3043290] la cuarta muñequita.
[u521 3043290-3045490] Quería incendiarlas a todas.
[u522 3055070-3056350] Y los que venían de Argentina,
[u523 3058590-3061310] yo decía tu abuela, your grandmother.
[u524 3065150-3067870] Es que para mí el parque había perdido sus secretos.
[u525 3068910-3071630] Por eso hay gente que dormita durante los servicios.
[u526 3083470-3092190] A veces nuestro director enfoca algunos rostros que obviamente no pone al aire y se ¿Por qué vienen tan temprano si se van a dormir?
[u527 3094190-3095550] Y yo tengo la respuesta.
[u528 3095790-3103640] Es que lo han visto todo, lo saben todo y de algún punto, de alguna manera, créeme, no es ironía, los entiendo.
[u529 3104440-3111320] Se han congregado algunos en docenas de iglesias, han asistido otro puñado de congresos, han cantado cientos de canciones.
[u530 3094190-3114480] Y esta canción es de fulanito.
[u531 3114480-3117800] Ah, esta es de Danilo, esta está vieja, esta no me gustó el arreglo.
[u532 3094190-3120920] Y nos volvemos degustadores de culto.
[u533 3101920-3123560] No me gustó dónde devuelven la ofrenda
[u534 3125950-3131070] y nada es sagrado y los santos se convierten en tedioso.
[u535 3131310-3139390] La constante exposición y el contacto hacia lo sagrado, a lo profano, producen callosidades en el espíritu humano.
[u536 3140590-3161540] Pablo le escribe a Timoteo en la carta, en la primera carta, capítulo 4, versículo 1, y le En los últimos tiempos algunos abandonarán la fe para seguir inspiraciones engañosas, doctrinas diabólicas y todas esas enseñanzas provienen de embusteros, de timadores, hipócritas que tienen la conciencia encallecida.
[u537 3162260-3165380] Callos en la conciencia, callos en el corazón.
[u538 3125950-3175940] Y por lo tanto podemos estar en medio de un servicio como hoy, mirando como otros adoran y sin embargo nosotros bostezar y tener la lógica de un chapulín que visita el templo.
[u539 3180110-3188830] Y uno de verdad, no estoy hablando de si sientes más, si se te nota más o menos, porque Dios respeta la estructura emocional de cada quien.
[u540 3182390-3194390] Estoy hablando de verdad, de gente que mira la hora y está esperando que termine desde que inicia.
[u541 3180110-3200510] Y uno de verdad, ¿Cómo perdemos la vieja espada de la adoración?
[u542 3180110-3203110] Y no, pero yo voy a la adoración.
[u543 3183710-3204430] Sí, pero ¿Cómo es que la perdemos?
[u544 3202070-3216940] Yo he visto pastores que durante la adoración están comiendo un sándwich o una empanada en su privado y suben a la hora de predicar, lo cual implica que cuando uno llega a cierto nivel ya no tiene que adorar con el resto.
[u545 3212300-3218860] Lo cual dice aún algo más.
[u546 3202070-3223580] Yo estoy en un nivel que no necesito adorar, no necesito estar con la gente.
[u547 3224860-3227020] Perdí la vieja espada de la adoración.
[u548 3227020-3229740] Para mí lo sagrado se me ha hecho común.
[u549 3230140-3238160] Entonces decimos, cántate unos coritos, cántate veinte minutos, cántate 20 minutos más que después voy que todavía, todavía no terminé la empanada.
[u550 3230140-3242680] Entonces uno ¿Cómo puede ser cómo que lo sagrado se volvió común?
[u551 3243240-3244000] ¿En qué momento?
[u552 3244000-3252280] Adrede, no, en un momento nos hacemos como los chapulines o como el rey mogol y somos un palacio sin rey a quien honrar.
[u553 3180110-3256360] Y cuarto, ¿Cómo perdemos la vieja espada de nuestra alegría?
[u554 3258200-3260200] ¿Usted se puede perder la alegría?
[u555 3183710-3184030] Sí.
[u556 3261240-3264350] Vuélveme el gozo de la salvación, dijo David.
[u557 3264910-3273430] Otra ¿Cuánto haces que no te ríes hasta que te duele la panza, te salten las lágrimas y me oriné?
[u558 3266430-3274190] ¿Cuánto
[u559 3277390-3278710] podemos obviar lo último?
[u560 3278710-3279070] Pero.
[u561 3283150-3285390] No aquí, no aquí, en casa.
[u562 3288190-3291150] Quizá tu respuesta es que no sientes esa alegría hace tiempo.
[u563 3292340-3296900] De ser así, quizás necesites oír esto, o capaz que sí.
[u564 3296980-3297860] Yo me río mucho.
[u565 3297860-3300900] Bueno, entonces podrías descansar y dormir durante este punto.
[u566 3302180-3310420] Pero quizás tu respuesta es hace bastante me reía así, pero la vida me fue cincelando, desgastando.
[u567 3305980-3315780] La enfermedad me robó la salud, la economía me robó el empleo.
[u568 3314940-3318700] El engaño de mi cónyuge me robó la confianza.
[u569 3305980-3322760] La muerte de mi ser querido se llevó las ganas de reírnos en familia.
[u570 3323080-3325320] Parece que la alegría es frágil.
[u571 3325880-3330840] Un día la tenemos y al día siguiente se la llevó el viento de la tormenta.
[u572 3331480-3337000] Estaba leyendo un estudio que el 33 % de la humanidad se considera feliz.
[u573 3333720-3334188] 33 %.
[u574 3289190-3347570] Es una cifra alarmante, porque en un tiempo de avances médicos de lujos tecnológicos sin precedentes, dos de cada tres personas viven tristes.
[u575 3299580-3349330] Y todos buscan la alegría.
[u576 3320920-3352530] Las empresas de marketing saben que todos buscamos la alegría.
[u577 3296980-3355650] Yo leía un analista de marketing que decía.
[u578 3355650-3364410] Los adictos a las apuestas en Las Vegas, por ejemplo, tienen una descarga de dopamina justo antes de hacer la apuesta, no después de que ganan.
[u579 3364410-3366050] Cuando ganan, ya no tienen dopamina.
[u580 3355650-3376920] Los adictos a la cocaína tienen un subidón de dopamina, de alegría, de euforia, justo cuando ven la sustancia, no después que la ingieren.
[u581 3377800-3384720] Lo mismo los adictos al sexo, se les sube la dopamina antes de consumar la relación sexual.
[u582 3363450-3365250] Después ya no.
[u583 3385320-3386760] Ni durante, ni después.
[u584 3299580-3398440] Y el marketing sabe y apunta eso a la anticipación de la recompensa, porque saben que una vez que compremos el producto, no hay dopamina, ni novedad, ni alegría.
[u585 3398760-3399360] Piensa.
[u586 3399360-3404200] ¿Cuando viste el último súper, ultra, mega, archi, mega, super HD celular?
[u587 3406210-3409890] Ay, no sabe la foto que saca está durmiendo y te saca solo.
[u588 3410850-3412130] ¿Y te lo vas a comprar?
[u589 3413330-3416370] ¿Cuántas veces después sacaste foto y lo volviste a mirar?
[u590 3416850-3417890] ¿Un día, dos días?
[u591 3419970-3422130] Las publicidades entienden eso a la perfección.
[u592 3422610-3426850] Nos abordan de todas partes para que nos suba la dopamina antes de consumir.
[u593 3427410-3434170] Y a menos que vivamos en una cueva, todos los días nos llegan un diluvio de cómprame, bébeme, cómeme, llévame puesto.
[u594 3428810-3439920] Una vez, mientras conducía por una de las autopistas, puse a prueba mi teoría.
[u595 3440080-3443040] ¿Cuántos anuncios vería en 60 segundos?
[u596 3443040-3446160] Valla publicitaria al lado de la ruta, camiones, carteles.
[u597 3446320-3449440] Conté unas 12 publicidades en un minuto.
[u598 3449440-3454207] Si extrapolamos esa cifra a la duración de mi viaje, estuve expuesto a casi 2.
[u599 3454207-3455001] 000 mensajes.
[u600 3445400-3465430] Carteles que me decían que contratara un nuevo abogado a una nueva compañía de seguros, que comiera una parrillada, que echara gasolina al auto, que votara por fulanito, que matara a la suegra.
[u601 3465430-3465870] Bueno, todo.
[u602 3469630-3471070] Y todas las promociones.
[u603 3471310-3475150] Agrande el combo por 20 centavos más y tendrá alegría.
[u604 3475390-3479230] Viste que los gringos lo que sea para agrandar, lo agrandamos.
[u605 3469630-3482670] Y los hispanos también Ay, por veinte centavos déjeme.
[u606 3469630-3483990] Y salimos así con un elefante.
[u607 3483150-3486990] Así que nos vamos que en la vida vamos a poder tomar.
[u608 3486990-3488030] No nos entra ese agua.
[u609 3486990-3490030] No vas a orinar, vas a hacer maremoto, mija.
[u610 3493220-3501620] Pero hasta las publicidades de cremas para hemorroides antes del producto muestran a un tipo con el ceño fruncido.
[u611 3501620-3502180] Lo entiendo.
[u612 3504260-3507620] Y después de la crema, desborda frescura y felicidad.
[u613 3509780-3512820] Ahora, la alegría es un tema importante en la Biblia.
[u614 3513220-3515380] Dios dice que quiere que estemos llenos de alegría.
[u615 3515380-3518440] Pero no es alegría ficticia de chapulines de domingo.
[u616 3510180-3523400] La alegría que no implica inocencia ante los desafíos de la vida.
[u617 3524040-3528120] Porque Jesús afrontó dificultades, tormentas, no obstante, nunca perdió la alegría.
[u618 3528520-3537000] Y en primera de perdón, en Juan 15 11 dijo les he dicho esto para que tengan alegría y así su alegría sea completa.
[u619 3537160-3538600] ¿Qué es una alegría completa?
[u620 3510180-3541560] La alegría que ofrece Jesús.
[u621 3541560-3543720] Diré algo casi infantil que sabemos todos.
[u622 3510860-3551620] Es diferente a las que prometen las concesionarias de automóviles, los préstamos, los paseos de compra.
[u623 3552100-3556100] Él no ofrece una alegría que depende de las circunstancias.
[u624 3556740-3559340] ¿La alegría de Jesús dependió de la aprobación de los demás?
[u625 3515460-3515540] No.
[u626 3559620-3561460] Ni siquiera su familia creía en él.
[u627 3557900-3563340] Dependió de las posesiones.
[u628 3515460-3564980] No tenía donde recostar la cabeza.
[u629 3535440-3569860] Su alegría dependía de la lealtad de la gente, de los grandes amigos que tenía.
[u630 3569860-3574960] Pedro lo negó, Judas lo traicionó, los otros salieron como ratas, los romanos lo mataron.
[u631 3574960-3575740] Hebreos 12.
[u632 3575740-3579076] 2 Por el gozo que le esperaba, soportó la cruz.
[u633 3580880-3583520] Entonces Jesús tenía una alegría resiliente.
[u634 3569860-3586800] Pedro habló de esa alegría.
[u635 3545380-3599960] A quien amáis sin haberle visto, en quien creyendo, aunque ahora no lo veáis, os alegráis con gozo inefable y glorioso, obteniendo el fin de vuestra fe, que es la salvación de vuestras almas.
[u636 3599960-3601840] Alguien tiene que celebrar más que eso, gente.
[u637 3601840-3602400] ¿Sí o no?
[u638 3509780-3608000] Ahora, ¿Sabés a quiénes les hablaba Pedro?
[u639 3545380-3609880] A los elegidos de Dios.
[u640 3513580-3630250] Dice arriba que viven como extranjeros, peregrinos en provincias como Galacia, Capodosia, Asia, Bitinia, o sea, Pablo le escribió a gente perseguida, inmigrantes ilegales, hombres y mujeres expulsados de sus ciudades, separado de sus familias, proscriptos de la ley.
[u641 3522360-3639130] Los adversarios le habían quitado sus derechos, sus propiedades, su dignidad, sus posesiones, pero no les pudieron quitar la alegría.
[u642 3639770-3641490] ¿Cuál era la fuente de esa alegría?
[u643 3572100-3645610] Como nadie podía quitarles a Jesús, nadie podía quitarles la alegría.
[u644 3580880-3658830] Entonces, mira, enterraste un sueño, enterraste un matrimonio, enterraste a un amigo, tu alegría yace en las parcelas de un panteón.
[u645 3514900-3666030] De ser así, anclaste el barco de tu alegría junto al muelle equivocado.
[u646 3524040-3672990] Porque el secreto es anclar nuestro corazón al pilar correcto, a Dios, al muelle correcto.
[u647 3672990-3676110] ¿Eso significa que no vamos a afrontar tormentas en la vida?
[u648 3515460-3677950] No, no, sí las vamos a afrontar.
[u649 3677950-3678517] Juan 16.
[u650 3678517-3681072] 33 En este mundo tendréis aflicción.
[u651 3681990-3682750] Anímense.
[u652 3683070-3684110] Yo he vencido al mundo.
[u653 3684670-3688910] ¿Significa que no vamos a atravesar las tierras áridas del dolor?
[u654 3515460-3694430] No, pero significa que esas tierras áridas no serán nuestro destino final.
[u655 3694430-3694997] Juan 16.
[u656 3694997-3697978] 20 Y la tristeza se convertirá en alegría.
[u657 3580880-3704150] Entonces la barca se va a sacudir, gente, las cosas se van a poner feas, nuestro ánimo va a fluctuar.
[u658 3704150-3706350] Sería un timador si te dijeran lo contrario.
[u659 3515460-3711990] No obstante, no vamos a quedarnos a la derima de un mar de desesperación.
[u660 3528520-3713550] Y hay algo más.
[u661 3510180-3717990] La alegría del Señor es viral, es contagiosa.
[u662 3683070-3725830] Yo aprendí en el arte del cine y de la televisión que todo el planeta puede llorar por lo mismo.
[u663 3726870-3731190] Usted pone una película, la vida Bella o Forrest Gump o cualquiera.
[u664 3528520-3737190] Y todo el mundo traducido a su idioma, todo el mundo llora por lo mismo, No todo el mundo se ríe por lo mismo.
[u665 3738220-3738820] ¿Tienen dudas?
[u666 3738820-3742420] Vayan la última entrega de los Oscar y van a ¿De qué cuernos se están riendo?
[u667 3742420-3748860] To gringo, que pase la chupitos a contar chistes y van a ver cómo se ríen.
[u668 3524040-3751780] Porque el mexicano no se ríe de lo mismo que el argentino.
[u669 3552100-3753820] El argentino no se ríe lo mismo que el guatemalteco.
[u670 3515460-3756860] No hay que ni siquiera extrapolarnos a Asia.
[u671 3522360-3758340] Los chinos no se ríen.
[u672 3676630-3759540] Si les gustó, se ríen.
[u673 3664710-3759900] Al final
[u674 3762060-3762700] de verdad.
[u675 3762700-3768320] Van guardando la risa y los aplausos hacen así como hacen negocios, son para como público.
[u676 3763620-3768720] Y al final.
[u677 3775920-3786480] Pero la risa que se contagia, independientemente de la etnia, de la raza, es la alegría que tenía la Iglesia del Nuevo Testamento, que no eran famosos por sus edificios, sino por la alegría.
[u678 3786480-3787033] Hechos 2.
[u679 3787033-3794531] 46 Partiendo el pan en la casa, comían juntos con alegría, con sencillez de corazón, teniendo el favor con todo el pueblo.
[u680 3784160-3795930] Eran alegres esos cristianos.
[u681 3784040-3799850] No debería haber cristianos que no sean alegres.
[u682 3800330-3804170] Porque la expresió es un cristiano alegre es una redundancia.
[u683 3804170-3807690] Si es cristiano, es alegre y si no es alegre, no es cristiano.
[u684 3784040-3810170] No hace falta el adjetivo cristiano alegre.
[u685 3784040-3814530] No hay un montón de cadáveres muertos, el agua está mojada.
[u686 3814530-3815730] Argentina, campeón del mundo.
[u687 3803530-3816730] Redundancia.
[u688 3820980-3827540] La semana pasada estuvo aquí un importante editor de libros y nos recorrí cientos de congregaciones.
[u689 3827540-3831860] Me sorprende que en River la gente canta y que está alegre.
[u690 3832740-3837380] Entonces yo digo cuando salgo de un cristiano tendría que me sorprende.
[u691 3828460-3839540] En River Hay gente alegre.
[u692 3839940-3841300] ¿Acaso existe otra manera?
[u693 3842100-3842380] Si.
[u694 3842380-3849310] Nuestra alegría no depende ni de Trump, ni de quien se sienta en la Casa Blanca, ni de Bukele, ni de Millet.
[u695 3842380-3852990] Nuestra alegría depende del Señor Jesucristo, ¿Sí o no?
[u696 3856670-3859070] Alguien tiene que celebrar por eso, ¿Sí o no?
[u697 3859630-3860590] Nuestra vieja.
[u698 3863230-3869710] Nuestra vieja espada de la alegría no depende de las circunstancias, de nuestra economía, de nuestra salud, de nuestra pareja.
[u699 3870840-3872160] Pregúntale a Pablo.
[u700 3872160-3875000] Quizás no tenga casa propia, dice, pero tengo fe en Dios.
[u701 3875000-3875820] Filipenses 1.
[u702 3875820-3882381] 12 Además, quiero que sepan que todo lo que me ha sucedido me ha servido para difundir la buena noticia.
[u703 3884520-3891240] Estoy contento de estar aquí en la cárcel, porque hasta el guardia del palacio sabe que estoy encadenado por causa de Cristo.
[u704 3874560-3893960] En la cárcel, alegre.
[u705 3894520-3896080] Y Pablo ¿Y si no tiene salud?
[u706 3896080-3897400] Ah, pero tengo vida eterna.
[u707 3897400-3898220] Filipenses 1.
[u708 3898220-3903077] 22 En realidad yo no sé qué es mejor, dice Pablo, y me cuesta trabajo elegir.
[u709 3887080-3909230] Porque en caso de seguir con vida, puedo serle útiles a ustedes, pero si me muero, me reúno con Jesucristo.
[u710 3881720-3912630] Para mí es mejor, pero por culpa de ustedes me voy a quedar vivo.
[u711 3914790-3917390] Pablo y quizás no duermas en sábanas de seda.
[u712 3917390-3919590] Ah sí, pero duermo con la conciencia limpia.
[u713 3919590-3920512] Filipenses 3.
[u714 3920512-3926830] 9 Y quiero que Dios me acepte, no por haber obedecido la ley, sino por confiar en Cristo.
[u715 3928450-3930850] Porque así es como Dios nos acepta.
[u716 3930850-3933010] Tener una conciencia limpia que le agrada.
[u717 3915390-3937970] Y Pablo si la billetera está vacía, bueno, pero la de mi Padre no.
[u718 3937970-3938892] Filipenses 4.
[u719 3938892-3944358] 11 No lo digo porque tenga escasez, porque me aprendí a contentar en lo poco.
[u720 3944450-3947410] Sé vivir humildemente, sé vivir en abundancia.
[u721 3916430-3951810] En todo y por todo estoy enseñado para tener hambre, para tener abundancia.
[u722 3947890-3954570] Todo lo puedo en Cristo que me fortalece.
[u723 3954570-3956270] Alguien tiene que decir amén.
[u724 3957950-3960510] El secreto del contentamiento
[u725 3962670-3964230] Tengo mucho, estoy feliz.
[u726 3962670-3965870] Tengo poco, Estoy feliz.
[u727 3965870-3966670] Adelgazo.
[u728 3969230-3970390] ¿Cuál era su secreto?
[u729 3970390-3971030] Jesucristo.
[u730 3969750-3973470] Su alegría no dependía de las cosas, dependía de Cristo.
[u731 3973790-3980670] Entonces yo estoy convencido, gente, que no necesitamos teologías novedosas, ni cumbres proféticas.
[u732 3971669-3986520] No estoy criticando, digo no las necesitamos, no son primera necesidad.
[u733 3976390-3993160] Necesitamos volver a la fuente, a las viejas bases, a las viejas armas espirituales.
[u734 3994520-4001640] Se terminó nuestro tiempo de horóscopos divinos, de empoderamiento barato, de profetas que endulzan nuestros oídos.
[u735 4002120-4004440] Tenemos que usar las viejas espadas del reino.
[u736 3972190-4009930] Las armas que Dios nos proveyó en el pasado, gente, funcionan hoy.
[u737 4007000-4013810] El mismo nombre que sobre todo nombre, lo diré otra vez.
[u738 3988120-4018730] La misma sangre vertida en la cruz, el mismo poder del Espíritu Santo.
[u739 4019290-4024370] Y cuatro de nuestras viejas espadas que funcionaron hace siglos, funcionan hoy.
[u740 4020170-4029770] Nuestras convicciones, no las pierdas, escríbelas en las tablas de tu corazón, atalas a tu cuello.
[u741 3995320-4033050] Nuestro propósito, nuestro significado en él.
[u742 4034020-4036980] Nuestra adoración genuina, no de labios, sino de corazón.
[u743 4019290-4041220] Y nuestra alegría, que no depende de las circunstancias.
[u744 4019290-4052980] Y te desafío a que usemos esas magníficas palabras de David, que hoy recuperamos esas armas y digamos ninguna como esas, dame las.
[u745 4019290-4059700] Y nos vamos armados, llenos de Dios, llenos de satisfacción Dale un aplauso al Señor de señores y al Rey de reyes.
[u746 4059700-4060420] Aleluya.
[u747 3971669-4064450] No, no, alguien tiene que celebrar más que eso.
[u748 4064450-4066330] Dar un aplauso grande al Rey.
[u749 4007000-4067610] El Rey está en la casa.
[u750 4068490-4069290] Todos, todos, todos.
[u751 4069690-4073530] Si crees que Dios habló, dale un aplauso al Rey.
[u752 4066850-4087190] Esta mañana Santo llama.
[u753 4097740-4105180] He transmitido lo que creo Dios me dijo que diga y como siempre, torpemente solo puedo llegar al intelecto de la gente.
[u754 4106540-4110260] Es el Espíritu Santo el que trae convicción y llega donde yo no puedo llegar.
[u755 4104580-4123140] De manera que si hay gente en casa o aquí que necesita hacer una de estas dos cosas, permitir que Cristo entre en su corazón y reine de verdad o reconciliarse con el Señor.
[u756 4123140-4136980] Porque hoy, wow, me cayó la moneda que a lo mejor yo soy un chapulín de templo o a lo mejor yo soy como el rey mogol que estoy atado al servir a Dios, pero soy un palacio sin rey a quien honrar.
[u757 4137700-4159569] Sea cual sea tu situación, no es necesario expresarla públicamente, pero sí delante del Señor y te invito a que tomemos unos minutos, cierres tus ojos y digas Señor, he recibido esta palabra y yo he transmitido esta palabra esta mañana y ruego que el Espíritu Santo selle con convicción lo que Dios ha hablado hoy.
[u758 4098940-4162849] Lo sagrado se nos ha vuelto común.
[u759 4170780-4181420] He pensado tantas veces en lo triste que debe ser vestirse o subir en mi caso a un avión para decir, tengo que predicar aunque no tenga ganas.
[u760 4182940-4189020] Hay momentos en que Dios me lleva a mi oración de muchacho cuando decía Señor, préstame los oídos de la gente.
[u761 4190380-4219350] Pero en algún momento entre la entre la promesa y el cumplimiento, entre la tierra prometida y el lugar de donde salimos, lo tedioso, lo abúlico, el desdén, la desidia toma lugar en nuestros corazones Y hoy quiero que todos, aún los que tengan años de convertidos en casa aquí puedan ser brutalmente honestos y decir Señor, vuélveme, quiero recuperar el gozo de la salvación,
[u762 4222140-4226540] quiero dejar de ser un crítico de cine para transformarme en parte de tu grey.
[u763 4227580-4235220] Vamos, todos los que tengan el bautismo del Espíritu intercedan como el Señor les da, los que no, abran la boca que de algo Dios la va a llenar.
[u764 4235220-4261000] Pero me encantaría que hoy no seamos pasajeros adormecidos de un tren, sino personas que digamos, quiero renovar mi compromiso porque una cosa tengo contra ti, que has perdido ese primer amor el primer amor tipifica esas ganas, esa energía, esa alegría, esas convicciones, esa adoración, eso que teníamos, que creíamos que nos íbamos a llevar el mundo por delante.
[u765 4261000-4267640] Benditos esos días de energía, de fuerzas, de fe sobrenatural.
[u766 4235220-4275440] Pero es el momento, dice el Espíritu, que hoy vuelvas, que volvamos a las convicciones.
[u767 4227580-4282720] Vamos, los que puedan levantar su mano, adorar, los que puedan poner la mano en su corazón, pero todo mundo adorando, todos, todos, todos
[u768 4285680-4304560] tomemos un tiempo para decir Señor, esta es la mañana en que tú no estás confrontando Señor, he transmitido lo que creo, me has dicho que diga, no he omitido, no he quitado nada lo que sé que es tu revelación Señor, si hay algo de mí, quítalo y que quede la savia, que quede la la esencia de lo que tú nos has hablado hoy.
[u769 4305200-4306800] Gracias Señor por esta mañana.
[u770 4305200-4324960] Gracias Dios porque puedo sentir aquí en el resto del sitio, de los sitios que están conectados, que hay una unción fresca, poderosa, trayendo convicción de arrepentimiento, una convicción que toca los tuétanos, las partes más profundas del alma y del corazón.
[u771 4325120-4343740] ¿Todos, wow, todos orando, todos clamando al Señor, Diga Señor, este es el momento donde yo puedo volver a aquello que había perdido a buscar la llave donde la perdí, dónde se te cayó el hacha, dice el Señor, en qué lugar se te cayó?
[u772 4308480-4345180] Porque ahí es donde va a flotar.
[u773 4346940-4370960] Volvamos al sitio junto al panteón, junto a la sala de cuidados intensivos, Volvamos a la corte del divorcio, volvamos al orfanato, volvamos a esa casa llena de violencia que era un cuadrilátero de boxeo al momento del abuso donde alguien robó tu inocencia para siempre Y digamos, ¿Es ese el clic?
[u774 4369280-4380760] Ese es el punto divergente donde perdí lo sagrado, donde la majestad se me hizo común Y otros no tienen que buscar en un trauma.
[u775 4332140-4384120] Yo sé que algunos tienen simplemente que ver dónde se desviaron.
[u776 4309960-4396600] El enemigo no va a querer que te vayas completamente, pero si logra que te desvíes apenas un centímetro de Jesús, habrá logrado de que seas un palacio sin rey a quien honrar.
[u777 4299640-4439130] Y en casa, los que me están viendo de otras partes del mundo, a todos aquellos con espíritu, Dios sabe que no intento insultarte, pero con una mente de insecto de templo, de creer que todo pasa bajo ese techo que son dos horas para recibir Dios, abra el techo, extienda el sitio de tu tienda y te muestre como habrán las estrellas y sepas que hay fuera propósito, significación, adoración, alegría, convicciones que hemos perdido en el altar de lo rutinario.
[u778 4440250-4450770] Cientos de miles de cristianos durante la pandemia se tuvieron que reencontrar con viejas armas Y muchos no tenían armas porque sus armas era el servicio.
[u779 4450770-4453530] Su arma era la identidad, Su arma era el título.
[u780 4387880-4457570] Pero el Señor dice, tus convicciones están allí, tómalas.
[u781 4457570-4458650] Ninguna como ellas.
[u782 4289080-4461860] Tu adoración está ahí, tómala.
[u783 4289080-4464100] Tu propósito está ahí, tómalo.
[u784 4289080-4464100] Tu alegría está ahí, tómalo.
[u785 4326000-4326640] Wow.
[u786 4327200-4328160] Todos, todos.
[u787 4468180-4468540] Vamos.
[u788 4468540-4470460] Levanta tu mano y comienza a clamar conmigo.
[u789 4470460-4476020] Dile, Señor, yo creo, yo declaro que los mejores días están por venir.
[u790 4288960-4482660] Que vienen cosas nuevas Que ojo no vio, ni oído yo, ni han subido a corazón de hombre impresionante.
[u791 4299640-4485940] Y que Dios va a traer cosas nuevas.
[u792 4286320-4489480] Un viento fresco, un viento de otra parte.
[u793 4489480-4490760] ¿Puede sentirlo?
[u794 4327200-4492760] Todos, todos, todos.
[u795 4495800-4496240] Vamos.
[u796 4496240-4499800] Los que tengan el bautismo del espíritu, intercedan como Dios les da ahora.
[u797 4501000-4503320] Intercesores, clamen conmigo ahora.
[u798 4496360-4506840] Que se corte todo lo que no es santo, todo lo que no es puro.
[u799 4496360-4515030] Que todo espíritu de rutina, que todo espíritu de desidia, de aburrimiento, de abulia se vaya ahora en el nombre del Señor.
[u800 4516150-4522310] Quita el yugo de la esclavitud y haznos libres a través de la verdad.
[u801 4523510-4524310] Todos, todos, todos.
[u802 4524550-4527190] Mira, hay gente encendida en fuego ahora.
[u803 4525510-4528950] Hay gente recibiendo ahora.
[u804 4529430-4532590] Más, más, Padre.
[u805 4497320-4537670] Del norte, del sur, del este y del oeste, viene un viento de otra parte.
[u806 4537990-4538630] Sopla.
[u807 4529430-4530150] Más, más.
[u808 4499320-4542390] Ahora
[u809 4544630-4546390] es la presencia del espíritu.
[u810 4546390-4547430] Momento, momento.
[u811 4548470-4549630] Tocándolo todo.
[u812 4549630-4550710] Pueden sentirlo.
[u813 4555430-4558870] En la gloria del Señor, llenándolo todo minuto a minuto.
[u814 4560790-4561670] Vamos, vamos, vamos.
[u815 4561670-4561990] Iglesia.
[u816 4561990-4563350] Adora, adora, adora, adora, adora.
[u817 4564480-4569600] Que el Señor escuche esa adoración que surge del alma, del corazón.
[u818 4556350-4570880] Señor, te adoro.
[u819 4573680-4577360] Perdóname por las veces que lo sagrado se me ha vuelto común.
[u820 4579760-4583760] Por las veces que vi esto como una simple profesión.
[u821 4586960-4593770] Por las veces de que tu gloria se me hizo tan normal que hasta me he dormido.
[u822 4595610-4600010] Perdóname nuestra irrespetuosidad.
[u823 4602330-4603450] Más de tu gloria.
[u824 4602330-4602690] Más.
[u825 4605370-4607770] Señor, te doy gracias por esta cuna de campeones.
[u826 4609850-4615770] Te doy gracias, Dios, por estos generales, estos obreros de primera línea, esta gente rota.
[u827 4617150-4619310] Y por providencia tuya,
[u828 4621630-4623790] tenerme al timón de esta nave insignia.
[u829 4624830-4629310] Te ruego que la mayor unción que tengas para un ser humano aquí en la tierra.
[u830 4629470-4633870] Derrames esta mañana con fuerza, con poder,
[u831 4636670-4638750] renovando, transformando.
[u832 4644920-4662200] Creo que lo diré otra vez, Las tormentas van a venir, las cosas se van a poner feas en el mundo, oiremos guerras, rumores de guerra, habrá plagas, no descartamos nuevas pandemias, Las cosas no van a mejorar si el Apocalipsis y la Biblia es real.
[u833 4663160-4666520] Pero el Señor dice que levantemos los ojos al cielo y tengamos ánimo.
[u834 4661480-4673730] La alegría no va a estar regulada por lo que ocurre en la economía, ni por las noticias de CNN o Fox.
[u835 4661480-4678530] La alegría nuestra no va a estar regulada por lo que ocurre alrededor.
[u836 4678690-4684290] Porque como dijo el Señor la semana pasada, a veces Dios calma la tormenta, pero a veces Dios calma al marinero.
[u837 4661320-4689330] Y hay veces que Dios nos calma en medio de la tormenta y sólo será esa promesa.
[u838 4689330-4702060] Paz en la tormenta, no te entregues, no te rindas, no baje los brazos, pelea por lo que amas, cree que los mejores días están por venir.
[u839 4661320-4710340] Y que Dios bendiga tu ser, tu familia, te bendiga en tu entrada, en tu salida, tu acostarte, tú levantarte, tu cruzar de las fronteras.
[u840 4703220-4715700] Bendiga a Dios tus suspiros más íntimos, tus sueños, tus visiones, tus ganas de despertar.
[u841 4715700-4728040] Tengas vientos a favor, siempre empujándote, tengas alegrías para tus hijos, tengas techo para los tuyos, comida en la mesa y nunca pierda las convicciones, la adoración, la alegría.
[u842 4724020-4737600] Nunca pierda bajo ningún punto de vista tu significación, porque estás rubricado con la firma del Señor y es tu pase para tener alegría y contentamiento.
[u843 4681050-4741920] Dios te bendiga, Dios te guarde y que haga resplandecer.
[u844 4741920-4745560] Dale un aplauso al Señor de señores y a la gente de todo el mundo.
[u845 4745880-4746440] Chau.
[u846 4678970-4747880] Cómo te ama el Señor.
[u847 4745880-4749120] Chau, chau, Chau, chau, Chau.
[u848 4749720-4750650] Bendiciones para todos.
[u849 4686210-4752600] Nos vemos en siete días.
[u850 4752600-4754240] Bendecidos para bendecir.

Analiza todo el sermon y devuelve 10-20 clips en formato JSON.

## Transcript Completo (sin truncar)

[u1 41980-49260] El Salvador, Colombia, Venezuela, República Dominicana, Cuba, México.
[u2 49340-52420] ¿Ya dije El Salvador, Venezuela, Puerto Rico, Cuba?
[u3 52420-53940] ¿Qué más, qué más, qué máS, qué más?
[u4 43860-55580] República Dominicana, Estados Unidos.
[u5 55580-58020] Tienen que ponerme los nombres de la bandera que no me los aprendo.
[u6 58020-58300] A todo.
[u7 58300-61340] Costa Rica, Uruguay, Paraguay, Chile.
[u8 52420-53420] ¿Qué más, qué más, qué más?
[u9 49340-52020] ¿Ya dije Puerto Rico?
[u10 64600-66280] Arriba, que no aflojen.
[u11 64600-67240] Arriba, arriba, arriba, arriba.
[u12 67520-72120] Transmitiendo en vivo para Asia, África, Oceanía, América, Europa.
[u13 72760-74640] Y ese aplauso que no decaiga.
[u14 74640-80280] Esto pasa en la calle Broadway desde Anahén, transmitiendo para todo el mundo.
[u15 81000-82760] Tomen asiento, por favor.
[u16 83320-84840] ¿Lo dejan entrar con bandera?
[u17 84840-86040] Yo no sé qué está pasando.
[u18 52820-88320] Que Dios te bendiga.
[u19 88320-96350] Buenos días, buenas tardes, buenas noches a todos los que nos miran desde otras partes del mundo, incluyendo, claro, los diferentes usos horarios.
[u20 96590-101390] Estamos aquí, hemos cantado, hemos adorado, hemos celebrado al Señor.
[u21 72760-118750] Y cuando ya hicimos todo eso, que es parte de la experiencia, lo que no transmitimos, porque yo digo siempre que la pantalla no hace justicia a lo que se vive, entonces lo que hacemos es transmitir a partir de este momento, que es el momento de la palabra de Dios que no vuelve hacia estamos listos para que Dios nos hable.
[u22 119470-121950] Voy a transmitirte lo que creo Dios me dijo que te diga.
[u23 72760-129960] Y gracias por los que están en casa, por los que siembran, por los que son parte de este río que no se detiene.
[u24 84840-141000] Yo solía contar muchas veces, a menudo, que crecí en el banco de una pequeña iglesia de Buenos Aires.
[u25 68080-147160] En aquellos tiempos no existía el cuidado de infantes, no había clases para los niños de mi edad.
[u26 105630-152850] Lo que se conoce como escuela dominical era los días sábados, o sea, vendría a ser una escuela sabática.
[u27 111630-161810] Entonces teníamos que ir el día anterior si queríamos recibir instrucción, pero no había algo como tal durante el servicio adulto.
[u28 56620-168130] De manera que simplemente yo tenía que aguantarme las interminables cuatro horas de culto, en el mejor de los casos.
[u29 103870-184990] Eso era cuando no bajaba el revival y el avivamiento, sino eran cinco o seis horas reuniones que, por cierto, yo recuerdo que solían ser bastante abúlicas, a excepción de cuando las hermanas Soraya, Carmela, Almudena, Genoveva, Teodora, Catalina y Amelia.
[u30 155370-188590] Si no tienes esos nombres, no eres pentecostal.
[u31 189790-191149] ¿Veían algún demonio?
[u32 155370-198030] Si veían algún demonio y algún espíritu, entonces era un tanto más divertido porque uno trataba de ver qué demonios estaban viendo.
[u33 52820-199550] Qué una vez te conté.
[u34 138200-204760] Una vez te conté que eran las intercesoras más expertas en demonios que en conocer a Dios.
[u35 157730-205800] Pero ese es otro tema.
[u36 164490-226600] Las predicaciones solían durar dos o tres horas especialmente cuando el pastor decía yo no sé por qué estoy diciendo esto, yo tenía preparado otro sermón, pero Dios me está guiando a decir esto que por lo general se había enterado de algún chisme y entonces aprovechaba para hacer catarsis durante el sermón.
[u37 227210-234570] Oh, decía, siento el espíritu que no podemos terminar este culto De hecho, Dios sabe que no miento ni exagero.
[u38 58020-238010] A veces nuestro pastor sentía que el Señor estaba por venir.
[u39 238010-239690] Decí yo siento que está por venir.
[u40 56620-243850] De un minuto a otro nos arrepentíamos hasta de lo que no habíamos hecho.
[u41 111630-250490] Entonces lo mejor, como él decía, yo siento que está por venir lo mejor era improvisar una vigilia.
[u42 250490-254021] Entonces muchas veces entrábamos al Templo a las 7 p.
[u43 254021-254154] m.
[u44 72760-256650] y salíamos al día siguiente a las 6 de la mañana.
[u45 257690-265690] Obviamente el señor no vino, por eso salíamos y de ahí los adultos iban directo a trabajar y los niños íbamos directos a la escuela.
[u46 84840-268490] Yo tenía unas ojeras, era un oso panda.
[u47 57180-274810] No podía estudiar porque eran varias vigilias que sentíamos de hacer No estaban planificadas.
[u48 275050-290700] Aun así, yo recuerdo mi época de mi niñez que tenía pequeñas rutinas para matar el tiempo durante esos cultos eternos en los cuales siempre teníamos la esperanza que vendría el rapto y Jesús nos rescataría de otro culto aburrido.
[u49 157730-293420] Pero mientras que no venía, había que pasar el tiempo.
[u50 111630-306300] Entonces me aprendía de memoria el orden de los libros bíblicos dibujaba caricaturas del pastor de los diáconos en un pequeño papel que camuflaba dentro del himnario.
[u51 157730-315300] Pero un día, algo en particular interrumpió mi aburrimiento o mejor dicho, alguien,
[u52 317300-335540] era un visitante que se metió por la puerta principal, tal vez, o por una ventana se deslizó por debajo del zapato del diácono y se la arregló para posarse sobre mi himnario y luego aterrizar justo debajo, casi al borde de mis pies.
[u53 335940-339830] En Argentina se lo conoce como langosta o saltamontes.
[u54 335940-356830] En México se lo conoce como chapulín, pero no el colorado chapulín Chapulín, que son parte de la familia de los ortópteros que incluyen a los grillos, a las chicharras, a las cigarras, más o menos uno de esos bichitos.
[u55 336780-362510] Lo que yo recuerdo que era una especie de saltamonte, quizás era un grillo, pero algo chiquitito.
[u56 326740-391020] Y como no había otra cosa que hacer más que escuchar como el pastor nos enviaba, como cada domingo, al infierno otra vez me puse a pensar qué le pasaría por la cabeza al pequeño chapulín que había entrado ahí, de hecho, si nunca más lograba encontrar la salida y su vida iba a ser el templo, todo su universo de por vida iba a ser nuestra pequeña iglesia, aquel pequeño sitio donde nos congregábamos.
[u57 391180-398460] ¿Y me imaginé por las noches, recuerden que está hablando el niño en ese entonces, ustedes dirán, con esta edad, imaginando la vida de un chapulín?
[u58 342710-422980] No, tenía siete, ocho años yo, pero me lo imaginé al bichito llevando a su hijo a pasear por las paredes durante la noche, diciéndole que observe las vigas del techo, colocando cariñosamente sus patas sobre la espalda de su hijo, diciéndole, pequeño saltamontes, aprecia este enorme cielo que es lo que nos cubre todas las noches.
[u59 356990-435760] Yo pensaba, se dará cuenta que eso no es todo el cielo que solo está mirando el techo de nuestro pequeño templo, se dará cuenta si vive allá adentro, se dará cuenta que hay un cielo afuera.
[u60 326740-441920] Y luego pensé en los grandes sueños que bien podría tener el chapulín.
[u61 342710-444640] No estaba ahí para escuchar a nuestro aburrido pastor.
[u62 383020-453680] Todo lo que ambiciona en la vida de insectos es comerse otros insectos más pequeños, un par de ácaros, tal vez larva, quizá degustar algún hongo.
[u63 342430-460620] Pero como estaba en medio de un servicio, yo me puse espiritual porque ya me había distraído mucho el bichito.
[u64 326740-326980] Y.
[u65 391180-464260] ¿Y a quién adorará el pequeño saltamontes?
[u66 465860-467220] ¿A quién adorará?
[u67 468660-477220] ¿Reconocerá que hay una mano que construyó este templo o preferirá adorar al templo por sí mismo?
[u68 478580-487820] ¿Dará por sentado que puesto que nunca ha visto al constructor del templo en el cual ahora vive y es su hogar, tampoco existe ese constructor porque nunca lo conoció?
[u69 489340-492820] Mucha gente que conozco posee esa misma mente de insecto.
[u70 342710-500380] No en este servicio generalmente vienen al otro, piensan que no hay más verdad que el techo.
[u71 342870-511020] El techo que está viendo es la única verdad, que no hay propósito más allá del placer momentáneo, incluso de la adoración momentánea.
[u72 512320-519680] ¿Qué ocurre cuando vemos a Dios a través de los ojos de un simple insecto, de un simple chapulín?
[u73 512320-528960] ¿Qué ocurre cuando nos conformamos con venir los domingos a la iglesia en lugar de ver más allá del techo que nos cubre?
[u74 326740-537840] Y a propósito, leí sobre alguien que se parece bastante al insecto de nuestra historia y al insecto que nos visitó cuando yo era niño.
[u75 421100-540460] Es una de las leyendas del Taj Mahal.
[u76 541820-546780] Resulta que quizá lo hayan oído porque es una historia muy conocida, harto conocida, dirían los chilenos.
[u77 319580-551820] La esposa preferida del rey mogol, Shahan, murió.
[u78 512800-562860] Cuando su esposa murió, el rey mogol, devastado, resolvió honrarla construyendo un inmenso templo que le sirviera de tumba y descanso final.
[u79 395460-575260] Entonces su féretro, el féretro de la reina, fue colocado en el centro de una gran parcela de tierra y se inició la construcción fastuosa del templo alrededor.
[u80 575980-585100] Decidió el caballero que no iba a ahorrar en gastos para lograr que el lugar de descanso final de su reina fuera magnífico.
[u81 342430-598440] Pero cuando las semanas se convirtieron en meses, el dolor del mogol dice que fue eclipsado por su pasión por el proyecto, o sea, la pasión por construir superó el dolor que él tenía por la viudez.
[u82 395460-601080] Entonces ya no lloraba por la ausencia de ella.
[u83 336780-607320] Lo consumía la construcción, los planos, el sueño.
[u84 326740-615320] Y un día, mientras caminaba, dice la leyenda, de un lado a otro de la obra en construcción, su pierna chocó con una caja de madera.
[u85 326740-623960] Y el príncipe se sacudió, o el rey se sacudió el polvo de la pierna y ordenó a un obrero que se deshiciera de esa molesta caja.
[u86 624520-633240] Yajangir no sabía que había ordenado la eliminación del féretro escondido bajo capas de polvo y de tiempo.
[u87 326740-639400] Y olvidó a la persona ¿Que pretendía honrar a priori con el tiempo?
[u88 512320-644360] ¿Que pretendía honrar una vez que estuviera construido?
[u89 512320-647550] ¿Que pretendía honlar con semejante construcción?
[u90 326740-652670] Y cuando culminó, fue un palacio sin nadie a quien honrar.
[u91 317580-655950] Un palacio sin reina a quien honrar.
[u92 342870-661710] El propósito inicial ya no estaba ahí porque se había deshecho del ataúd.
[u93 395460-666590] Entonces, digo, ¿Podría alguien construir un palacio y olvidarse del rey?
[u94 662670-671190] ¿Podría alguien esculpir un tributo y olvidarse del héroe?
[u95 395740-396020] Ustedes.
[u96 421100-672910] Es una ironía, es una locura.
[u97 513560-699360] Dios, en su providencia divina, me permitió viajar por gran parte del mundo y he visitado cientos de congregaciones y siempre pude notar, mirándome, mirando en perspectiva, quienes vienen a la iglesia y saben quién fue crucificado y quién fue resucitado independientemente de los años que tengan de peregrinar cristiano, puedo verlos y vienen absortos por ese Cristo que resucitó.
[u98 342710-703440] No necesita que sean Semana Santa para celebrar una tumba vacía.
[u99 395460-711670] Entonces yo los puedo ver en cualquier congregación, insisto, en cualquier parte del mundo, llenos de asombro, llegan a congregarse llenos de expectativas.
[u100 356990-719469] Yo creo que mucha de la gente que está aquí llega de esta forma, por eso hacemos fila y por eso hay tanta expectativa y adoramos y cantamos a los gritos.
[u101 351870-730230] A mí me gusta cuando los adultos parece que son niños que observan mientras se desenvuelve un regalo en Navidad, cortesanos agradecidos que observan desfilar al rey.
[u102 326740-731230] Y venimos con esa.
[u103 396380-734740] Con esa expectativa que siempre, insisto, atrapa la unción.
[u104 342430-752940] Pero también he notado cientos de otros creyentes que se parecen a Shah, el rey mogol, o al Chapulín de mi historia, que solo ven el templo, el cielo raso, y no logran ver más allá del techo y sus mentes divagan, sus ojos se ponen vidriosos del sueño.
[u105 356990-753420] Yo los veo.
[u106 351870-764380] A veces estamos adorando y está como la ardillita de la era de Hielo, están así y si duermo con un ojo, se darán cuenta o pensarán que soy tuerto.
[u107 447960-770740] Otros miran el celular o están pendientes de la hora o bostezan.
[u108 395460-777420] Entonces todos los templos, todos los servicios, de hecho pierden su brillo al cabo de un tiempo.
[u109 335940-780780] En algún momento lo novedoso deja de ser novedoso.
[u110 682600-784540] Siempre, por más novedoso que sea, en un momento lo sagrado se vuelve común.
[u111 395460-789110] Entonces los adoradores de templos no tienen la intención de aburrirse.
[u112 789110-800870] ¿De hecho, casi es un insulto a vuestra inteligencia que vienes a aburrirte, porque quién prepararía a los niños o se levantaría a la madrugada y se acicalaría para venir para luego aburrirse?
[u113 356990-812480] Yo sé que hay gente que les encanta la iglesia y hasta algunos raros aman al pastor, pero las intenciones de los que se duermen no es volverse rancios.
[u114 812640-814840] Voy y me voy a dormir y me voy a aburrir.
[u115 342710-824040] No se levantan, insisto, temprano, se preparan, vienen cada domingo, pero en algún momento del peregrinar pierden de vista.
[u116 824040-829360] Perdemos de vista a quien en primera instancia pensábamos adorar.
[u117 395460-848370] Entonces los que adoran el templo los que adoran servir, los que adoran el hecho intrínseco de congregarse, los que adoran la doctrina, la sana, la supersana, la recontra hipersana o los que adoran el simplemente venir, es muy diferente a los que vienen a adorar a Dios.
[u118 346830-854730] Son muy distintos y podemos encontrar a ambos sentados en la misma congregación en cualquier sitio.
[u119 854730-858637] Pablo le escribe una carta a Roma y Dice en Romanos 1.
[u120 858637-867754] 23 Y cambiaron la gloria del Dios incorruptible en semejanza a una imagen de hombre corruptible y cambiaron la verdad de Dios.
[u121 870440-879800] Insiste el apóstol en una mentira, hablando y honrando y dando culto a criaturas antes que el Creador, el cual es bendito por los siglos.
[u122 342870-888200] Él es increíble que alguien pueda cambiar la verdad por la mentira y en vez de adorar a Dios, empiecen a adorar otras cosas que no merecen adoración.
[u123 395460-900770] Entonces cuando en algún momento, quiero pensar inconsciente, olvidamos a quien veníamos a adorar y esto no respeta la estatura espiritual de nadie.
[u124 901010-907010] Puede que tengamos 30, 40 años de creyentes, 50 años, y en algún momento lo sagrado se nos vuelve común.
[u125 326740-916800] Y ahí es cuando perdemos, al menos lo que yo creo, cuatro de nuestras principales armas que nos sostienen, que nos bendicen, que nos.
[u126 318340-921670] Que creo que son el leitmotiv, la savia de nuestra vida cristiana.
[u127 824040-930230] Perdemos de vista nuestras convicciones, perdemos de vista nuestro propósito, perdemos de vista nuestra adoración, caramba.
[u128 326740-932950] Y perdemos de vista nuestra alegría.
[u129 342710-933910] No es un tema menor.
[u130 326740-948500] Y aquí quiero hacer un paréntesis que es vital y necesario porque siempre yo sostuve que un avivamiento, que un mover de Dios, palabra que está en boga y que a veces está incluso sobreestimado.
[u131 317580-954700] Un avivamiento nunca surge de una teología novedosa, de descubrir algo novedoso.
[u132 954700-962340] Uy, en tal congregación parece que están haciendo tal cosa y hasta nos suena divertido y en ocasiones hasta es barroco.
[u133 342430-969220] Pero los avivamientos nunca surgen de una teología nueva, sino cuando regresamos a las bases bíblicas.
[u134 969540-986960] Muéstrame un avivamiento real y yo te voy a mostrar a alguien o a un grupo de gente que regresó a las bases, regresó a la oración, regresó a la búsqueda, regresó a lo que comúnmente se llama la senda antigua, tan fácilmente confundida con una doctrina externa de vestimenta.
[u135 986960-993906] Y uno de mis pasajes preferidos de la Biblia está en la segunda carta de Corintios, capítulo 11.
[u136 993906-1007365] 3, donde Pero me temo, dice Pablo, que así como la serpiente con su astucia engañó a Eva, los pensamientos de ustedes pueden que sean desviados de un compromiso puro y sincero con Jesús.
[u137 351870-1018170] A mí me fascina porque Pablo en una misma oración, es un compromiso puro y sincero el que hay que tener con el Señor.
[u138 516680-1022170] Simple, ni complejo ni complicado.
[u139 370780-1035230] Me temo que los pensamientos y esta esta cultura de tanto ruido te aparte del compromiso simple que deberías tener con el Señor.
[u140 1009490-1037030] Sincero y puro, punto.
[u141 1037590-1039110] Diáfano, transparente.
[u142 356990-1040470] Yo amo eso.
[u143 458900-1050310] Porque de otro modo nos volvemos como el rey mogol o el insecto de mi historia de la infancia, que perdemos de vista las viejas armas espirituales.
[u144 824040-1054910] Perdemos las cosas esenciales de la vida cristiana.
[u145 512800-1063870] Cuando David fue ungido como rey de Israel, subió de nivel obviamente espiritual, pero no accedió al trono de manera inmediata.
[u146 326740-1073070] Y en lugar de ahora luchar contra osos y leones, se subió al ring al poco tiempo a pelearse y a medirse con un guerrero de 3 metros llamado Goliat.
[u147 1073070-1079870] Conocemos la historia y este pequeño muchachito adolescente tenía una bolsa con piedras planas.
[u148 318540-1083550] Se dirige al sangriento campo de batalla, una piedra certera,
[u149 1086430-1088430] y el guerrero bravucón cae muerto.
[u150 1086670-1092590] El efecto especial va incluido con la ofrenda que vas a poner más tarde.
[u151 1094030-1102870] Entonces David cesa la situación decapitando a Goliat con la propia espada del gigante abatido.
[u152 1102870-1104030] Recordemos que él no tenía espada.
[u153 1086670-1105560] Él fue con una onda y las piedritas.
[u154 1105950-1110270] Así que le saca la espada y le corta la cabeza.
[u155 1111710-1113470] Esos son los más cortes de cabeza, ¿No?
[u156 1114990-1119230] Ahora, avancemos algunos años y David todavía no está en el trono.
[u157 1118550-1124870] En cambio, el celoso rey Saúl, petulante, lo está echando del palacio.
[u158 1086430-1126710] Y David tiene que huir para salvar su vida.
[u159 1126710-1128350] Estamos repasando la vida rápido.
[u160 1114990-1138460] Ahora David es un fugitivo sin preparación, sin plan a futuro, sin dinero, sin armas, sin ropa extra, sin comida enlatada, sin GPS.
[u161 1139020-1140540] ¿A dónde corre primero?
[u162 1086430-1143260] Y la Biblia narra que corre al templo.
[u163 1129390-1145100] Es el primer sitio donde va.
[u164 1118550-1149420] En su día más oscuro, David decide correr al templo.
[u165 1103470-1156140] No se fue a un bar, ni a los brazos de una mujer, ni se sumergió en los tentáculos de una adicción.
[u166 1104190-1160420] Fue donde sabía que estaba la presencia de Dios en el templo.
[u167 1095710-1163860] David, insisto, que ahora es fugitivo de su propio suegro.
[u168 1086430-1171540] Y tú pensabas que tenías problemas con tu suegro David conoce a un sacerdote llamado Abimelec.
[u169 1094030-1195800] Entonces el fugitivo David pide, El proscripto pide comida, el sacerdote lo alimenta y luego le pide a Abimelec David una cosa más y yo sé que esta es una petición poco común, estoy en un templo, pero yo tenía tanta prisa por escapar que me fui sin mis armas y puede que necesite alguna porque ahora soy un prisionero, un fugitivo.
[u170 1195800-1196400] Perdón.
[u171 1196880-1199760] ¿Tienes algún arma aquí en la casa de Dios?
[u172 1199760-1201680] ¿Tendrá algún arma guardada?
[u173 1086430-1209440] Y el sacerdote, como acto reflejo, mueve la cabeza negativamente No, David, aquí somos sacerdotes, no luchadores.
[u174 1210480-1212720] Tenemos cualquier cosa menos armas.
[u175 1186480-1221980] Pero luego el sacerdote hace memoria y espera un momento, A decir verdad, sí tenemos un arma en nuestra suerte de museo del templo.
[u176 1129390-1227260] Es la misma espada que usaste para cortarle la cabeza a Goliat.
[u177 1227660-1228900] ¿Tú crees que esa va a servir?
[u178 1118390-1234620] Está ahí de adorno, es como un memorial de lo que ocurrió en el campo de batalla en el valle de Ela.
[u179 1227660-1236220] ¿Tú crees que puede servir?
[u180 1086430-1243580] Y David se había olvidado que él mismo había llevado la espada al templo porque sabía de quién había sido la victoria.
[u181 1181780-1244940] Yo no me puedo quedar con esta esp.
[u182 1118390-1251960] Esta espada simboliza que Dios ha dado la victoria, que Jehová puso Israel por encima de los filisteos, la había llevado al templo
[u183 1254600-1259800] y ahora le ofrecen la misma espada pero para nuevas victorias.
[u184 1260040-1273240] Entonces David expresa, a esto quería llegar, esta frase magnífica, maravillosa en el primer libro de Samuel, capítulo 21, versículo 9 Ninguna como ella, Dámela.
[u185 1273710-1273950] No.
[u186 1254600-1276510] Y bueno, capaz que está media arrumbrada.
[u187 1276510-1277990] Andá, ¿Sabes si sirve?
[u188 1277990-1279190] Es la espada del enemigo.
[u189 1268200-1281310] Él ninguna como esa.
[u190 1281630-1285390] Con esa le corté la cabeza a esta bola de grasa, a este bravucón.
[u191 1260040-1287990] Entonces este es el punto.
[u192 1287990-1298830] Las armas que Dios nos proveyó en el pasado, aunque a veces parecen arcaicas, siguen funcionando hoy porque no hay nada nuevo bajo el sol, en las cosas de Dios.
[u193 1273710-1309770] No necesitamos ni empoderarnos, ni escuchar muchos coaching que nos digan qué hacer, ni profesionales que nos laven la cabeza, ni decretos apostólicos, ni declaraciones proféticas.
[u194 1268200-1314890] El mismo nombre que es sobre todo nombre, la misma sangre que fue vertida en la cruz del calvario.
[u195 1315130-1325810] Alguien tiene que celebrar por eso el mismo poder del Espíritu Santo, la oración, el ayuno, son las viejas espadas para vencer y resistir.
[u196 1273710-1326490] No ha cambiado.
[u197 1260040-1336120] Entonces a veces la gente escucha de algún mensaje por ahí, el chiste en mi caso cuando hablo de alguna suegra u otro género demoníaco, pero.
[u198 1254600-1343600] Y es un payaso, no voy autopromocionarme.
[u199 1258360-1356890] Pero yo siempre digo que no me he movido nunca en tantos años de las viejas armas, de la vieja espada, de lo que aprendí, porque aunque esos servicios cuando pequeño eran abúlicos, yo recibía y recibía algunas cositas, no entendía otras.
[u200 1277430-1373050] Sí en algún momento una palabra me tocó y eran las viejas ayunar, orar, proclamar, leer la palabra, nutrirse el espíritu, no había nada novedoso, no eran teologías novedosas, no era esperar una palabra profética, no era una declaración apostólica.
[u201 1373210-1377610] Todos estábamos con las viejas armas que funcionaban y siguen funcionando.
[u202 1254600-1384410] Y cuatro de esas viejas espadas, insisto, funcionan hace siglos y funcionan hoy.
[u203 1384410-1409970] Podría quedarme toda la mañana hablando de varias herramientas o armas que Dios nos ha dado, pero por lo menos cuatro que tienen que ver, insisto, con nuestras convicciones, nuestro propósito, nuestra adoración y nuestra alegría, que son las cuatro armas que perdemos a priori apenas empezamos a adorar el templo y nos olvidamos del Dios al que queríamos adorar en el templo.
[u204 1332680-1414520] Cuando lo sagrado se vuelve común, perdemos estas cuatro armas que son valiosas.
[u205 1414920-1431800] Dicho esto, yo voy a tomarme unos breves minutos para que repasemos junto estas cuatro viejas espadas, miles de veces predicadas, cientos de veces profesadas, pero que a menudo solemos olvidar.
[u206 1432120-1437480] Ergo, ¿Cómo perdemos la vieja espada de nuestras convicciones?
[u207 1437480-1440270] Ustedes dirán, ¿Cómo se pueden perder las convicciones?
[u208 1440350-1443870] Tengo años de peregrinar cristiano.
[u209 1274510-1461950] Bueno, si somos como el Chapulín de mi historia y toda nuestra vida está reducida a las vigas del techo del domingo, carecemos de principios que nos sostengan de lunes a sábado cuando no estamos aquí, cuando no estamos congregados, independientemente de dónde se congregue cada quien.
[u210 1277430-1476040] Si nos volvemos inconsciente o conscientemente adoradores del templo, como el rey Mogol de mi historia, sólo nos van a importar las opiniones de los que también vienen al templo el mismo día que nosotros.
[u211 1254600-1495920] Y si la opinión de los que vienen al templo determina nuestras convicciones, si repetimos como loros todo lo que incluso el pastor nos dice y no tenemos nuestra propia convicción, nuestro propio fundamento, ¿Qué ocurre cuando el pastor se equivoca, cuando la mayoría se equivoca y decimos, bueno, pero todo el mundo va para allá?
[u212 1496000-1498640] Seguir traseros de ovejas es hipnotizador.
[u213 1504720-1506640] Y uno dice, todo el mundo va para allá.
[u214 1507600-1514080] Entonces, cuando no tenemos las propias convicciones, repetimos lo que ocurre en el templo el domingo.
[u215 1504720-1515680] Y esa es toda nuestra vida espiritual.
[u216 1504720-1527060] Y hay cientos de cristianos que relativizan su relación con Dios bajo el axioma yo como estiércol porque un millón de moscas no pueden estar tan equivocadas.
[u217 1504720-1529340] Y uno dice, ¿Por qué estás haciendo tal cosa?
[u218 1504720-1534020] Y bueno, porque todo el mundo lo hace y porque lo repito y porque hay gente que vive como yo.
[u219 1534260-1540020] Pero el solo hecho de repetir, de congregarse y de hecho de creer en Dios, no nos hace cristianos.
[u220 1540500-1542940] Te dirá ¿Cómo que no nos hace cristianos creer en Dios?
[u221 1509600-1546020] No, de hecho no hay un solo demonio en el infierno que sea ateo.
[u222 1549260-1550100] Pero los demonios creen.
[u223 1550100-1551660] Claro, creen y tiemblan.
[u224 1551660-1553180] No hay un demonio que no crea en Dios.
[u225 1551020-1555660] Y sin embargo, los demonios no son convertidos necesariamente.
[u226 1556380-1558660] Digo, por si tienes un marido que mi marido cree.
[u227 1558660-1559900] Bueno, los demonios también.
[u228 1562380-1566140] Y ese es el peor síndrome que podemos padecer.
[u229 1567020-1570300] Creer en Dios y no estar dispuesto a que nos cueste algo.
[u230 1571980-1573780] Yo siempre digo ¿Que le puedo predicar?
[u231 1569060-1578820] A mí me encanta cuando hago la gira y me dicen que hay un 80% de inconversos en la sala.
[u232 1569060-1580210] A mí me gusta porque esas tierras frescas.
[u233 1563300-1593240] El problema es cuando la gente relativiza y entonces no se consideran tan afuera como para merecer un cambio, pero tampoco se consideran tan adentro como para que les cueste algo el seguir a Cristo.
[u234 1585440-1598200] Se le llama relativismo o Teología del Pluralismo.
[u235 1574340-1609230] Cuando la mayoría, incluso la mayoría de los anglos, ya que esto no salga de acá, que quede acá entre los hispanos, pero la mayoría de los anglosajones ustedes este es un país cristiano.
[u236 1609390-1612510] Sí lo es de manera etimológica.
[u237 1612990-1617390] ¿Pero el gran problema es que es muy difícil que llamemos a un vecino gringo y usted cree en Dios?
[u238 1562380-1618590] Y te no, no creo en Dios.
[u239 1569060-1619910] A mí me van a comer los gusanos.
[u240 1617470-1624310] Te van a no, no, yo creo en Dios, pero le he dado mi Jesús, Buda o Taylor Swift.
[u241 1573020-1625230] Le da lo mismo.
[u242 1627390-1638860] Todos llegamos a ese momento en la vida que tenemos que dejar de relativizar las convicciones y definir qué tan comprometida está nuestra relación con Jesús.
[u243 1638860-1642420] Independientemente, insisto, de cuántos años tengamos de convertido.
[u244 1643860-1650260] Esto nos lleva a una pregunta que nos resultaría reveladora a la mayoría de nosotros seguir a Jesús.
[u245 1628670-1657860] A los que estamos aquí presentes y no tienen que responder de manera articulada, ¿Nos ha costado algo?
[u246 1658420-1661540] ¿Te costó algo servir a Jesús, seguir a Jesús?
[u247 1663210-1674770] Porque hay gente que no le molesta de que Jesús llegue y mejore un poquito sus vidas, como quien contrata un seguro médico o se suma a Angua o Herbalife, que los prospere otro poco, que los sane de alguna otra cosita.
[u248 1674770-1679930] Entonces uno dice, Jesús, cuando puedo voy a la iglesia, es nice, es buen tipo Jesús.
[u249 1679930-1682890] Pero te dirían lo mismo de Jesús como de John Lennon, le dan lo mismo.
[u250 1633700-1688840] Y conocemos gente que cree que un poquito de maquillaje ya va a estar bien.
[u251 1679930-1692200] Pero Jesús no quiere que nos maquillemos, quiere hacernos de nuevo.
[u252 1674770-1699080] Entonces muchos queremos decorar un poquito y Jesús quiere derribarlo todo y construir desde cero.
[u253 1652460-1703560] No es que Jesús es un maquillaje, Jesús no es un tratamiento dermatológico.
[u254 1705880-1709480] Me tapo con crema, me pongo la faja, me ajusto y voy así por la vida.
[u255 1711400-1715020] Porque en un momento hay que liberar a Willy, en un momento hay que o no.
[u256 1716140-1721740] Entonces creer en Jesús no es lo mismo que tener convicciones serias.
[u257 1716940-1722860] Creer creen todos.
[u258 1722940-1731340] De hecho estamos en un país, le cuento a la gente de América Latina, en toda la región, donde en Estados Unidos, la Unión Americana, la mayoría yo no, yo creo en Dios.
[u259 1708400-1741630] Y cuando sucede un hecho como el de hace unos días atrás, de un asesinato o de un atentado, todo el mundo empieza a invocar a Dios.
[u260 1741630-1743190] Pasó lo mismo en el 911.
[u261 1719100-1746190] Es muy difícil decir, aquí nadie cree en Dios.
[u262 1734580-1747990] El problema es la relativización.
[u263 1729820-1761310] Yo siempre tuve un poco de lástima de Poncio Pilato, porque decía, el tipo se lavó las manos, el tipo no quería condenar a Jesús, pero al no decidir, decidió, al lavarse las manos, relativizó.
[u264 1761310-1762150] Dijo, es un buen tipo.
[u265 1762150-1767470] Para mí, la verdad que el tipo es nice, sí, qué sé yo, si quieren lo azoto 40 veces y lo libero.
[u266 1763510-1769670] Si quieren que lo crucifique y lo crucifico, le da lo mismo.
[u267 1770640-1771640] Eso es lavarse las manos.
[u268 1771640-1775440] Esa es la relativización que es más peligrosa que el ateísmo.
[u269 1716140-1782160] Entonces tenemos la tendencia de definir al cristianismo como el simple acto de creer.
[u270 1756550-1783600] Pero no se trata de creer.
[u271 1716940-1789160] Creer tiene que ver con una simple aceptación intelectual, cree en Jesús.
[u272 1789160-1790480] ¿Y quién no va a creer en Jesús?
[u273 1763510-1794960] Sí todo el mundo en Semana Santa incluso y en Navidad, se acuerda y cree en Jesús.
[u274 1756550-1798970] Pero creer es el primer paso, el segundo es seguir.
[u275 1708400-1809610] Y ambas palabras no son antagónicas, no son excluyentes, están de hecho conectadas, constituyen el corazón, los pulmones de la fe.
[u276 1785200-1812250] Una cosa no puede existir sin la otra.
[u277 1734580-1814730] El seguir forma parte de creer.
[u278 1814730-1818490] Muéstrame a alguien que cree y yo te tengo que mostrar alguien que sigue al Señor.
[u279 1708400-1825700] Y creer significa seguir, no es pasar al altar y repetir como loro, es creer y seguir.
[u280 1708400-1836900] Y entretanto no rompamos esa dicotomía entre creer y seguir, las iglesias se van a seguir llenando de simpatizantes, de observadores de techo como mi Chapulín.
[u281 1838340-1839220] Ay qué lindo.
[u282 1734580-1844900] El techo se va a llenar de gente así, porque creen pero no siguen.
[u283 1708400-1852630] Y si uno les hace un seguimiento tipo Big Brother durante toda la semana, se da cuenta que no es un seguidor, no es una seguidora.
[u284 1756550-1854030] Pero sí viene el domingo a creer.
[u285 1763510-1855350] Sí, pero el Chapulín también.
[u286 1857590-1861310] Me pregunto, los que se acaban de conectar, Ay, está metiendo al Chapulín Colorado.
[u287 1861310-1863589] Vaya al principio del mensaje, antes de criticar.
[u288 1864630-1874950] Entonces hemos escrito la palabra creer con mayúsculas y todo lo que tiene que ver con seguir lo escribimos como un subtítulo, como una nota al pie, como es una opción, lo principal que crea.
[u289 1875110-1877190] ¿Cuántas decisiones de fe hubo?
[u290 1877270-1878550] Oh, tres mil.
[u291 1878710-1879870] ¿Y cuántos siguieron?
[u292 1879870-1883270] Bueno, eso después con el tiempo no creer va a conseguir.
[u293 1884550-1886950] Jesús decía, no decías crean en mí, con eso basta.
[u294 1881270-1889869] Él decía síganme, similar a cuando.
[u295 1889869-1895990] Pero a veces nos comportamos como cuando compramos un celular y nos dicen ¿Desea asegurarlo por si se rompe o por si se le pierde?
[u296 1868070-1898310] Y a veces decimos no, no, no, está bien, no creo.
[u297 1868070-1900550] Y en la iglesia predicamos lo mismo por años.
[u298 1868430-1907080] Lo importante es que ya compró a Jesús, ahora si lo desea, por 20 centavos más lo puede seguir.
[u299 1907480-1908680] Agrandamos el combo.
[u300 1889869-1916040] Pero no se sienta presionado, no tiene que decidirlo ahora, piénselo, cualquier cosa, luego nos llama un líder, lo va a llamar en la semana.
[u301 1864630-1922920] Entonces tenemos que preguntarnos, insisto, seguir, además de venir los domingos, ¿Nos ha costado algo?
[u302 1923480-1927800] Porque no cuenta prepararnos y alistarnos temprano para venir el domingo.
[u303 1882390-1928680] A mí me cuesta.
[u304 1881590-1934160] No, eso no cuesta, porque así vamos también a un concierto o podemos ir a una boda o un cumpleaños.
[u305 1934960-1939680] ¿De qué manera seguirlo ha interferido con nuestra vida normal?
[u306 1934960-1935680] ¿De qué manera?
[u307 1923480-1948240] Porque no se nos permite ser seguidores encubiertos o Nicodemos visitadores de noche.
[u308 1948719-1952720] ¿Cuándo fue la última vez que seguir a Jesús nos costó una relación?
[u309 1953600-1963200] Alguien a que supuestamente amábamos o queríamos o teníamos como amigo y de repente sentíamos que era tóxico y era un impedimento para que sigamos al Señor y tuvimos que decidir.
[u310 1948719-1971440] ¿Cuándo fue la última vez que seguir a Jesús nos costó una promoción, un empleo, un ascenso, una amistad de años?
[u311 1973600-1978760] ¿Cuándo fue la última vez que nos costó unas vacaciones, pero que está mal?
[u312 1978760-1979680] No digo que esté mal.
[u313 1973600-1981480] ¿Cuándo fue la última vez que te costó unas vacaciones?
[u314 1974840-1987840] Que este dinero que tenía para las vacaciones, el Señor me ha hecho sentir que lo tengo que invertir en esto para el Señor.
[u315 1973600-1974840] ¿Cuándo fue la última vez?
[u316 1990330-1996650] ¿Entonces podemos decir realmente que estamos llevando su cruz si nunca nos costó nada?
[u317 1998170-2007170] Porque si no ha habido sacrificio, y no estoy hablando de salvación, la salvación no se paga ni en cuotas, ni el down payment no se paga, es gracia.
[u318 2000090-2011530] Estoy hablando del sacrificio de seguir, que es diferente a creer.
[u319 1994650-2017690] Si al menos nos hemos sentido un poco incómodos, capaz que no estamos llevando la cruz.
[u320 1999690-2021110] Y no deberíamos cantar de que estamos llevando la cruz.
[u321 2022230-2030150] Nadie logra sostener la vieja espada de sus convicciones si nunca ha tenido que renunciar a nada.
[u322 2010730-2037110] A veces es tiempo de calidad con la familia, a veces significa dejar de lado un empleo.
[u323 1999690-2042950] Y no estoy diciendo que eso es parte de la salvación o si agrada o agrada menos a Dios.
[u324 2034950-2045630] Significa de que creer es una parte, seguir es otra.
[u325 2039190-2046790] Eso es convicciones, gente.
[u326 1999690-2057970] Y si perdemos la vieja espada de las convicciones, tampoco vamos a tener nunca un dique que detenga el vertedero de basura que nos ofrece la cultura y la sociedad.
[u327 1998170-2060570] Porque el relativismo hace eso.
[u328 2060570-2069410] Como dije, nos volvemos amplios y decimos, ¿Quién no mira una serie de Netflix sabiendo de que un poco de basura va a consumir?
[u329 1974840-2083020] Qué es lo que nos hace al principio la sensación de rechazo, de ver algo que no está bien aún con nuestros hijos, y después anestesiarnos y que ya no nos choque al espíritu.
[u330 1978760-2092460] No hablo de doctrina, hablo de qué hace que ya no nos choque lo que a nuestros padres, no digo a los abuelos los hubiese espantado.
[u331 2093820-2099380] Cuando vemos la cantidad de basura que ingerimos a través del streaming, ¿Cuál es el filtro?
[u332 1974320-2104340] La doctrina En la vida te voy a decir qué ver y qué no ver.
[u333 2104820-2108020] Yo vengo del control y nunca me pondría en controlador.
[u334 2108660-2112420] Además, no es el control el que cambia a la gente, sino la convicción del Espíritu Santo.
[u335 2112580-2114580] Así que yo no te voy a decir qué hacer y qué no hacer.
[u336 2115140-2118420] Entonces, ¿Qué es lo que acá nos dice qué está bien y qué está mal?
[u337 2119700-2122860] Bueno, pero si lo que está mal no se puede mirar, no puedo mirar nada.
[u338 2122860-2128510] OK, pero como dije siempre, ¿Quién comería una pupusa?
[u339 2129870-2131990] ¿Noventa y nueve por ciento chicharrón?
[u340 2131990-2133150] Uno por ciento de caca.
[u341 2135870-2137190] No, pero es chicharrón.
[u342 2137190-2139310] La caca está mezclada entre el chicharrón es 1%.
[u343 2139310-2141470] ¿Quién la comería sabiendo esa información?
[u344 2142350-2150030] Entonces cuando empezamos a comer estiércol, porque un millón de moscas no podrían estar equivocadas, significa que perdimos la espada de las convicciones.
[u345 2150030-2150590] ¿Por qué?
[u346 2150590-2152010] Por ser adoradores de templo.
[u347 2144590-2154920] Porque no sabemos a quién adoramos.
[u348 2154920-2161600] Y como no sabemos a quién adoramos, no sabemos ni siquiera cómo adorar con nuestra vida.
[u349 2162560-2165680] Eso explica el proceso de la santidad.
[u350 2148030-2168040] Qué está bien, qué no está bien.
[u351 2168040-2181330] Hay un sensor interno, un autocontrol de calidad interno que nos dice qué hacer, qué decir, qué contar, qué no contar, cuándo detener un chisme, cuando parar los oídos para que no nos tiren basura de un chisme.
[u352 2135870-2183170] No hay forma de hacer una lista.
[u353 2135870-2190610] No podemos hacer 613 leyes como la Torá y que esto no lo hagas y esto no haga, porque el legalismo no funciona.
[u354 2191010-2194290] Buscaremos la manera y más que somos hispanos, siempre estamos buscando la trampa.
[u355 2194290-2196210] Todo no funciona, el legalismo.
[u356 2199330-2201170] Entonces, ¿Cuál es el control interno?
[u357 2201170-2203250] La espada de las convicciones.
[u358 2204640-2205920] Esto no me edifica.
[u359 2206320-2207440] Ya no hablamos de pecado.
[u360 2204640-2209640] Esto no me edifica, esto me atrasa en la carrera.
[u361 2209640-2213360] Dijo Pablo, despojado del pecado y de todo peso.
[u362 2212240-2216080] Y siempre estamos hablando del pecado y del peso.
[u363 2217040-2222320] ¿Quién sale a correr una maratón con botas, con un sacón, con un sombrero?
[u364 2212800-2213360] Peso.
[u365 2212800-2226320] Peso no es pecado, pero me atrasa en la carrera.
[u366 2199770-2231280] ¿Cuál es el tamiz para saber qué peso llevo y qué peso No llevo?
[u367 2202530-2203250] Convicciones.
[u368 2234160-2235720] ¿Cuáles son nuestras convicciones?
[u369 2235720-2237640] ¿Algún día yo me voy a ir o me voy a morir?
[u370 2236880-2238600] O ustedes se van a morir.
[u371 2238600-2244480] Primero, porque yo estoy más joven, entonces ¿Quién nos va a decir qué hacer y qué no decir?
[u372 2220200-2250080] Un día no tendremos la Biblia a mano, no tendremos streaming, no sé, o vendrá otra pandemia.
[u373 2250480-2253120] ¿Qué convicciones nos van a sostener?
[u374 2253680-2259770] Esa es la vieja espada que solemos perder cuando nos volvemos como el Chapulín o como el rey Mogol.
[u375 2260330-2264490] Segundo, ¿Cómo perdemos la vieja espada de nuestro propósito?
[u376 2266010-2272410] Cuentan que alguna vez un gorrión silvestre se acercó a un canario que estaba encerrado en una jaula.
[u377 2212240-2279210] Y el gorrión salvaje o silvestre le pregunta al canario en ¿Cuál es tu propósito?
[u378 2212240-2285200] Y le dice el mi propósito es comer semillas, comer alpiste.
[u379 2285200-2287200] ¿Semillas para qué?
[u380 2275130-2288640] Pregunta el gorrión de afuera.
[u381 2288640-2291680] Bueno, para poder ser fuerte, ¿Para qué?
[u382 2288640-2294880] Bueno, para poder cantar todas las mañanas, respondió el canario.
[u383 2295840-2297000] ¿Y qué pasa cuando canta?
[u384 2297000-2298960] Ah, cuando canto me das más semillas.
[u385 2199330-2301560] Entonces le dice el gorrió.
[u386 2202210-2307440] De modo que come semillas para ser fuerte, para poder cantar, para que te den más semillas, para que puedas comer.
[u387 2307840-2308560] Ajá.
[u388 2204760-2311380] No, mijo, eso no es un propósito, le dijo el gorrión.
[u389 2309200-2313860] Eso es precisamente lo que se llama esclavitud.
[u390 2314180-2316420] Eres un hámster dando vuelta en la ruedita.
[u391 2199330-2321780] Entonces es muy difícil encontrar un propósito en un cristianismo enjaulado.
[u392 2212240-2326380] Y todos nacemos con un anhelo intenso de significación.
[u393 2218040-2333620] Una vez que tenemos convicciones, queremos significación, validación, una búsqueda de sentido a nuestra existencia.
[u394 2334420-2336420] Algunos buscan la importancia en una carrera.
[u395 2281610-2341320] Mi propósito es ser médico, entonces yo soy médico.
[u396 2204760-2343440] No te dedicas a la medicina.
[u397 2200170-2346240] El doctorado no te da identidad.
[u398 2200050-2351600] Es una profesión excelente, pero difícilmente sea una justificación de tu existencia.
[u399 2353600-2360720] La gente que yo soy esto son lo que hacen, pero por consiguiente hacen mucho, porque si no hacen, no tienen validez.
[u400 2360720-2363440] Sienten que no se autovalidan.
[u401 2363600-2367280] Trabajan muchas horas porque si no lo hacen, sienten que no tienen identidad.
[u402 2359800-2373670] Tienen que trabajar porque ellos tienen su identidad asignada de lo que hacen.
[u403 2373670-2375070] Otros son los que tienen.
[u404 2375550-2381390] Creen encontrar propósito en un nuevo auto, en una nueva casa, y ahora tengo una troca.
[u405 2384350-2387070] Otros buscan significación a través de sus hijos.
[u406 2387790-2395810] Viven vicariamente a través de sus vástagos y mi razón para vivir son mis hijos, pero nadie nació para sus hijos.
[u407 2396290-2406330] Esa no puede ser nuestra significancia, porque un día los hijos se van a volar, van a dejar el nido vacío y vamos a quedar tirados en un sillón, abandonados pensando que ya no hay significado.
[u408 2406330-2418690] Por eso mucha gente empieza a morir a causa del nido vacío y otros buscan su validación sirviendo a Dios y no se dan cuenta que son un palacio sin rey a quien honrar.
[u409 2420220-2423100] Sirven, sirven, sirven, pero no adoran.
[u410 2405250-2426060] Ya perdieron las convicciones y ahora están perdiendo el propósito.
[u411 2427420-2432620] Una vez le traje a uno de mis hijos la camiseta del Barça firmada por todos sus jugadores titulares.
[u412 2432940-2435339] Costó mucha oración.
[u413 2438140-2446700] La camiseta es una de las tantas que se vende por algo de así como 80 euros en los sitios oficiales, o sea, uno puede conseguir esa camiseta en cualquier sitio.
[u414 2447370-2449210] Lo que la hace singular son las firmas.
[u415 2447370-2451530] Lo mismo ocurre con nosotros.
[u416 2443100-2457770] En el esquema de la naturaleza no somos las únicas criaturas con carne, pelo, sangre y corazones.
[u417 2447370-2465810] Lo que nos hace especiales a nosotros, a diferencia de cualquier otro animal, es la firma de Dios en nuestras vidas.
[u418 2453890-2468050] Somos una obra rubricada por Dios.
[u419 2468050-2468730] ¿Sí o no?
[u420 2438140-2471930] La firma So Nature.
[u421 2473460-2481940] Yo me acuerdo que iba a la escuela primaria y yo vivía para el privilegio de ejecutar las tareas más honrosas de la maestra.
[u422 2441180-2486900] Como nunca fui un muchacho popular, cuando la maestra decía Gebel, venga.
[u423 2460050-2491460] A mí me emocionaba apagar las luces para que la maestra pasara diapositiva.
[u424 2473460-2493180] Yo me sentía el segundo a bordo.
[u425 2443100-2501760] En el colegio, el más alto privilegio era hacer un mandado para la maestra, ir a buscar tizas, un borrador, lo que me mandara a hacer.
[u426 2501760-2503800] Aparte me tiraba onda la maestra.
[u427 2507240-2511080] Yo tenía siete años, ella tenía 72, pero había algo.
[u428 2513320-2524070] Y si la maestra me escogía para hacer el mandado, el corazón se me aceleraba y yo me acercaba a su escritorio con veneración y ella me explicaba mi misión del día y me daba el.
[u429 2513320-2527540] Y me daba un pase, un fast pass para ir por todo el colegio.
[u430 2527540-2528220] Vaya, vaya.
[u431 2513320-2530460] Y si me para alguien, vaya con el pase.
[u432 2530620-2539340] Entonces era un papelito firmado por la maestra que me hacía andar por el edificio y se me abrió un mundo nuevo para mí.
[u433 2530620-2541060] Entonces andaba con el pase.
[u434 2541060-2543100] Así tardaba en buscar la tiza.
[u435 2513320-2545860] Y si algún maestro me ¿Qué hace acá fuera de la clase?
[u436 2519840-2547020] Yo le mostraba el pase.
[u437 2553660-2556620] Si alguien me preguntaba dónde iba, yo sacaba el pase y se lo mostraba.
[u438 2557180-2560860] Imaginate, un argentino ya es agrandado de por sí con pase.
[u439 2562940-2567100] No hay nada peor que un argentino con pase o con primera fila.
[u440 2567900-2569220] Cuando vayan suban un avión.
[u441 2569220-2570700] Fíjense en los que viajan en business.
[u442 2571260-2576940] Son gente que sube así, con pechito de paloma y se sienta viendo cómo pasan los esclavos para el fondo.
[u443 2578820-2590260] Pero además van a notar cuando el que está adelante es argentino, porque cuando pasa el que viene buscando el 52 AF, le Señorita, más jugo de naranja, por favor.
[u444 2591780-2595700] Una vez que pasen esto, plebeyo, me traes un poquito de.
[u445 2580940-2597300] Es como quiere demostrar.
[u446 2597380-2600180] Yo estoy acá por argentino más que por otra cosa.
[u447 2572860-2602740] Así que imagínate lo que era yo con un pase.
[u448 2602740-2606100] Ese trozo de papel firmado por la maestra significaba que yo estaba seguro.
[u449 2574380-2614050] Y todos nosotros tenemos ese pase de Dios, aunque parezca un infantilismo colgado del corazón.
[u450 2574380-2619490] Y si confiamos alguna vez en Jesús como nuestro Salvador, la Biblia dice que estamos en Él.
[u451 2619810-2628850] Entonces, cuando alguien nos no eres lo suficientemente bueno, no das la medida, no das el ancho, no me gusta tu liderazgo, no te corresponde estar aquí, solo Hay que hacer.
[u452 2631570-2632530] ¿Qué pasó?
[u453 2634290-2635090] No manches.
[u454 2640030-2643950] Somos significativos no por lo que hacemos, sino debido a quién pertenecemos.
[u455 2644670-2658190] Entonces, cuando uno adora no al techo, sino a Dios, cuando dejamos de ser un palacio sin rey a quien honrar, no sólo recuperamos la vieja espada de las convicciones, sino la vieja espada de la significación.
[u456 2658270-2663070] Venimos y vivimos una vida con Cristo y eso nos da significado.
[u457 2641230-2667770] No importa que nos digan, no importa un cuerno lo que hablen de nosotros.
[u458 2668170-2669450] Ay, los haters.
[u459 2668170-2670610] Ay, me están atacando.
[u460 2663670-2676650] Importa un cuerno los seguidores de las redes cuando uno tiene significación en el Señor.
[u461 2677130-2680410] Tercero, ¿Cómo perdemos la vieja espada de nuestra adoración?
[u462 2680570-2684170] Ustedes dirán, ¿Y quién puede venir a la iglesia y no adorar?
[u463 2684570-2700100] Yo no sé si alguna vez escuchaste la historia del tipo que una noche buscaba la llave de su auto dentro de la casa y su esposa lo empieza a ayudar en la búsqueda, hasta que le preguntó ¿Pero de verdad no te acuerdas en dónde se te pudieron haber caído la llave del auto?
[u464 2659070-2702580] Y él sí, me acuerdo, se me cayeron afuera en la calle.
[u465 2709780-2711940] ¿Y entonces por qué lo estás buscando dentro de la casa?
[u466 2711940-2714180] Ah, porque acá adentro hay más luz, dijo el tipo.
[u467 2710060-2723800] Entonces, si estamos buscando las llaves que perdimos en la calle, hay que buscarla en el lugar donde las perdimos.
[u468 2724200-2729280] Y si estamos buscando lo sagrado, no vamos a encontrarlo el domingo debajo del techo.
[u469 2729280-2732760] Con la mentalidad de insecto visitante de templo.
[u470 2726240-2733880] No lo vamos a encontrar.
[u471 2726240-2737880] No digo que no venga, digo, no encontrarás aquí lo que perdiste el miércoles.
[u472 2726240-2742040] No vas a encontrar acá la paz que no tuviste el jueves.
[u473 2744370-2748290] El ataque de ira que tuviste el lunes por la mañana o el viernes por la noche.
[u474 2748290-2752050] No se va a ir por arte de magia dos horas el domingo.
[u475 2744890-2756690] De hecho, vamos a volver al chapulín de nuestra historia, al insecto de nuestra historia.
[u476 2756690-2763970] Imaginemos que estos insectos ortópteros son muy avanzados y se hacen preguntas filosóficas y teológicas.
[u477 2756690-2770450] Imaginemos ¿Y habrá vida más allá de las vigas del techo del templo?
[u478 2761570-2773450] Y algunos saltamontes creen que la hay.
[u479 2773770-2776370] Debe haber un creador de este lugar magnífico.
[u480 2744890-2779290] De otra manera, ¿Quién encendería las luces?
[u481 2780170-2781290] ¿De qué otra manera?
[u482 2780170-2785610] ¿De dónde vendría ese aire que sopla desde las rejillas?
[u483 2786330-2794410] Entonces algunos saltamontes, como resultado de su asombro por lo que pueden ver, adoran lo que no pueden ver.
[u484 2795290-2797850] Dicen, no, acá hay aire acondicionado, acá hay luz, hay sonido.
[u485 2797850-2799370] Tiene que haber una mano detrás de esto.
[u486 2799700-2801700] Ven todo esto y adoran lo que no pueden ver.
[u487 2801940-2814180] Otros insectos discrepan, estudian un poco y concluyen que las luces se encienden debido a la electricidad, que el aire sopla debido a los conductos de aire acondicionado.
[u488 2786330-2817420] Entonces, ya sabemos cómo funciona todo esto.
[u489 2817420-2819380] Dejen de creer en un ser superior.
[u490 2748290-2822020] No hay nada que nos asombre, insectos.
[u491 2748290-2823940] No hay nadie a quien adorar.
[u492 2799090-2828500] Esto funciona porque hay electricidad, porque hay sonido y porque hay aire acondicionado.
[u493 2829460-2831980] Ustedes dirá medio tonto este segundo insecto.
[u494 2761570-2834180] Y sí, pero nosotros cometemos el mismo error.
[u495 2818260-2853300] En un momento comprendemos cómo se forman las tormentas, cartografiamos los sistemas solares, trasplantamos corazones, medimos las profundidades de los océanos, enviamos señales a planetas distantes y nosotros, los pequeños saltamontes, estudiamos el sistema y aprendemos el funcionamiento de todo.
[u496 2761570-2856080] Y ni te cuento los pastores o predicadores.
[u497 2816060-2866520] Sabemos qué botón tocar, cuándo cortar la música, cuándo meter adoración, cuándo pedir el dinero, cuando la gente está llorando un poco y es el momento de pedir una segunda ofrenda.
[u498 2869320-2879400] Cuando aprendemos el funcionamiento, perdemos el misterio y fundamentalmente perdemos la majestad y lo sagrado se nos vuelve común.
[u499 2880560-2885760] Ustedes ¿Cómo puede ser que alguien tan ungido se transformó en un profesional?
[u500 2874120-2889880] Y no estoy en contra, yo creo que soy el tipo más profesional que conozco.
[u501 2877320-2893680] Lo que estoy diciendo cuando solamente se convirtió en un profesional.
[u502 2874120-2898880] Y es irónico, pero mientras más sabemos, menos creemos.
[u503 2874120-2903840] Y el conocimiento debería ser al revés, debería estimular nuestra adoración.
[u504 2904800-2915860] ¿Quién tiene más razones para adorar que el astrónomo que vio las estrellas, o que el cirujano que tuvo el corazón en una mano, o el oceanógrafo que estudió los abismos?
[u505 2916180-2919300] Entonces, mientras más sabemos, más deberíamos maravillarnos.
[u506 2895920-2933300] Pero es paradójico, mientras más sabemos, mientras más años de creyentes tenemos, menos adoramos, porque nos asombra descubrir el interruptor de la luz antes que descubrir al que inventor de la electricidad, el que inventó la electricidad.
[u507 2934260-2936670] Eso se llama lógica de cerebro de Chapulín.
[u508 2937460-2940780] Si yo fuera un pastor moderno, dile al que está a tu lado, no seas Chapulín.
[u509 2895920-2944980] Pero no te voy a decir eso en lugar de.
[u510 2926339-2950660] Porque a mí me reventaba que me hicieran repetir, así que nunca haré repetir a la gente, pero tengo una gana que le diga Chapulín.
[u511 2953300-2956500] En lugar de adorar al Creador, adoramos la creación.
[u512 2957220-2966980] Y dijo Pablo, y cambiaron la verdad de Dios por la mentira, honrando y dando culto a las criaturas antes que el Creador, el cual es bendito por los siglos.
[u513 2968320-2988880] Mirá, cuando yo llegué a este país, yo amaba los parques temáticos, como todos los que llegamos a este país por primera vez, yo me crié, veía imágenes de Disneyland en blanco y negro en un programa que se llamaba El mundo de Disney, y le decía a mi si alguna vez voy a ese parque, voy a vivir ahí adentro, nadie me va a sacar.
[u514 2975560-2997480] Me voy a esconder en la casita de Mickey, la de Mini, para que no hablen mal, y no voy a salir
[u515 3000840-3002840] por lo menos a morir machito, ¿No?
[u516 3005480-3012600] Y después, cada vez que venía una visita de Argentina, yo era el anfitrión encargado de mostrarle el enorme reino mágico.
[u517 3005760-3019500] Después de unas 8 o 10 visitas, empecé a perder el encanto, pensé que nunca me iba a pasar.
[u518 3005480-3024690] Y una vez, durante el recorrido, por ejemplo, de los Piratas del Caribe, contestaba el celular.
[u519 3034050-3039890] Incluso hasta me he quedado dormido, principalmente en ese jueguito de las muñequitas que hacen así,
[u520 3042050-3043290] la cuarta muñequita.
[u521 3043290-3045490] Quería incendiarlas a todas.
[u522 3055070-3056350] Y los que venían de Argentina,
[u523 3058590-3061310] yo decía tu abuela, your grandmother.
[u524 3065150-3067870] Es que para mí el parque había perdido sus secretos.
[u525 3068910-3071630] Por eso hay gente que dormita durante los servicios.
[u526 3083470-3092190] A veces nuestro director enfoca algunos rostros que obviamente no pone al aire y se ¿Por qué vienen tan temprano si se van a dormir?
[u527 3094190-3095550] Y yo tengo la respuesta.
[u528 3095790-3103640] Es que lo han visto todo, lo saben todo y de algún punto, de alguna manera, créeme, no es ironía, los entiendo.
[u529 3104440-3111320] Se han congregado algunos en docenas de iglesias, han asistido otro puñado de congresos, han cantado cientos de canciones.
[u530 3094190-3114480] Y esta canción es de fulanito.
[u531 3114480-3117800] Ah, esta es de Danilo, esta está vieja, esta no me gustó el arreglo.
[u532 3094190-3120920] Y nos volvemos degustadores de culto.
[u533 3101920-3123560] No me gustó dónde devuelven la ofrenda
[u534 3125950-3131070] y nada es sagrado y los santos se convierten en tedioso.
[u535 3131310-3139390] La constante exposición y el contacto hacia lo sagrado, a lo profano, producen callosidades en el espíritu humano.
[u536 3140590-3161540] Pablo le escribe a Timoteo en la carta, en la primera carta, capítulo 4, versículo 1, y le En los últimos tiempos algunos abandonarán la fe para seguir inspiraciones engañosas, doctrinas diabólicas y todas esas enseñanzas provienen de embusteros, de timadores, hipócritas que tienen la conciencia encallecida.
[u537 3162260-3165380] Callos en la conciencia, callos en el corazón.
[u538 3125950-3175940] Y por lo tanto podemos estar en medio de un servicio como hoy, mirando como otros adoran y sin embargo nosotros bostezar y tener la lógica de un chapulín que visita el templo.
[u539 3180110-3188830] Y uno de verdad, no estoy hablando de si sientes más, si se te nota más o menos, porque Dios respeta la estructura emocional de cada quien.
[u540 3182390-3194390] Estoy hablando de verdad, de gente que mira la hora y está esperando que termine desde que inicia.
[u541 3180110-3200510] Y uno de verdad, ¿Cómo perdemos la vieja espada de la adoración?
[u542 3180110-3203110] Y no, pero yo voy a la adoración.
[u543 3183710-3204430] Sí, pero ¿Cómo es que la perdemos?
[u544 3202070-3216940] Yo he visto pastores que durante la adoración están comiendo un sándwich o una empanada en su privado y suben a la hora de predicar, lo cual implica que cuando uno llega a cierto nivel ya no tiene que adorar con el resto.
[u545 3212300-3218860] Lo cual dice aún algo más.
[u546 3202070-3223580] Yo estoy en un nivel que no necesito adorar, no necesito estar con la gente.
[u547 3224860-3227020] Perdí la vieja espada de la adoración.
[u548 3227020-3229740] Para mí lo sagrado se me ha hecho común.
[u549 3230140-3238160] Entonces decimos, cántate unos coritos, cántate veinte minutos, cántate 20 minutos más que después voy que todavía, todavía no terminé la empanada.
[u550 3230140-3242680] Entonces uno ¿Cómo puede ser cómo que lo sagrado se volvió común?
[u551 3243240-3244000] ¿En qué momento?
[u552 3244000-3252280] Adrede, no, en un momento nos hacemos como los chapulines o como el rey mogol y somos un palacio sin rey a quien honrar.
[u553 3180110-3256360] Y cuarto, ¿Cómo perdemos la vieja espada de nuestra alegría?
[u554 3258200-3260200] ¿Usted se puede perder la alegría?
[u555 3183710-3184030] Sí.
[u556 3261240-3264350] Vuélveme el gozo de la salvación, dijo David.
[u557 3264910-3273430] Otra ¿Cuánto haces que no te ríes hasta que te duele la panza, te salten las lágrimas y me oriné?
[u558 3266430-3274190] ¿Cuánto
[u559 3277390-3278710] podemos obviar lo último?
[u560 3278710-3279070] Pero.
[u561 3283150-3285390] No aquí, no aquí, en casa.
[u562 3288190-3291150] Quizá tu respuesta es que no sientes esa alegría hace tiempo.
[u563 3292340-3296900] De ser así, quizás necesites oír esto, o capaz que sí.
[u564 3296980-3297860] Yo me río mucho.
[u565 3297860-3300900] Bueno, entonces podrías descansar y dormir durante este punto.
[u566 3302180-3310420] Pero quizás tu respuesta es hace bastante me reía así, pero la vida me fue cincelando, desgastando.
[u567 3305980-3315780] La enfermedad me robó la salud, la economía me robó el empleo.
[u568 3314940-3318700] El engaño de mi cónyuge me robó la confianza.
[u569 3305980-3322760] La muerte de mi ser querido se llevó las ganas de reírnos en familia.
[u570 3323080-3325320] Parece que la alegría es frágil.
[u571 3325880-3330840] Un día la tenemos y al día siguiente se la llevó el viento de la tormenta.
[u572 3331480-3337000] Estaba leyendo un estudio que el 33 % de la humanidad se considera feliz.
[u573 3333720-3334188] 33 %.
[u574 3289190-3347570] Es una cifra alarmante, porque en un tiempo de avances médicos de lujos tecnológicos sin precedentes, dos de cada tres personas viven tristes.
[u575 3299580-3349330] Y todos buscan la alegría.
[u576 3320920-3352530] Las empresas de marketing saben que todos buscamos la alegría.
[u577 3296980-3355650] Yo leía un analista de marketing que decía.
[u578 3355650-3364410] Los adictos a las apuestas en Las Vegas, por ejemplo, tienen una descarga de dopamina justo antes de hacer la apuesta, no después de que ganan.
[u579 3364410-3366050] Cuando ganan, ya no tienen dopamina.
[u580 3355650-3376920] Los adictos a la cocaína tienen un subidón de dopamina, de alegría, de euforia, justo cuando ven la sustancia, no después que la ingieren.
[u581 3377800-3384720] Lo mismo los adictos al sexo, se les sube la dopamina antes de consumar la relación sexual.
[u582 3363450-3365250] Después ya no.
[u583 3385320-3386760] Ni durante, ni después.
[u584 3299580-3398440] Y el marketing sabe y apunta eso a la anticipación de la recompensa, porque saben que una vez que compremos el producto, no hay dopamina, ni novedad, ni alegría.
[u585 3398760-3399360] Piensa.
[u586 3399360-3404200] ¿Cuando viste el último súper, ultra, mega, archi, mega, super HD celular?
[u587 3406210-3409890] Ay, no sabe la foto que saca está durmiendo y te saca solo.
[u588 3410850-3412130] ¿Y te lo vas a comprar?
[u589 3413330-3416370] ¿Cuántas veces después sacaste foto y lo volviste a mirar?
[u590 3416850-3417890] ¿Un día, dos días?
[u591 3419970-3422130] Las publicidades entienden eso a la perfección.
[u592 3422610-3426850] Nos abordan de todas partes para que nos suba la dopamina antes de consumir.
[u593 3427410-3434170] Y a menos que vivamos en una cueva, todos los días nos llegan un diluvio de cómprame, bébeme, cómeme, llévame puesto.
[u594 3428810-3439920] Una vez, mientras conducía por una de las autopistas, puse a prueba mi teoría.
[u595 3440080-3443040] ¿Cuántos anuncios vería en 60 segundos?
[u596 3443040-3446160] Valla publicitaria al lado de la ruta, camiones, carteles.
[u597 3446320-3449440] Conté unas 12 publicidades en un minuto.
[u598 3449440-3454207] Si extrapolamos esa cifra a la duración de mi viaje, estuve expuesto a casi 2.
[u599 3454207-3455001] 000 mensajes.
[u600 3445400-3465430] Carteles que me decían que contratara un nuevo abogado a una nueva compañía de seguros, que comiera una parrillada, que echara gasolina al auto, que votara por fulanito, que matara a la suegra.
[u601 3465430-3465870] Bueno, todo.
[u602 3469630-3471070] Y todas las promociones.
[u603 3471310-3475150] Agrande el combo por 20 centavos más y tendrá alegría.
[u604 3475390-3479230] Viste que los gringos lo que sea para agrandar, lo agrandamos.
[u605 3469630-3482670] Y los hispanos también Ay, por veinte centavos déjeme.
[u606 3469630-3483990] Y salimos así con un elefante.
[u607 3483150-3486990] Así que nos vamos que en la vida vamos a poder tomar.
[u608 3486990-3488030] No nos entra ese agua.
[u609 3486990-3490030] No vas a orinar, vas a hacer maremoto, mija.
[u610 3493220-3501620] Pero hasta las publicidades de cremas para hemorroides antes del producto muestran a un tipo con el ceño fruncido.
[u611 3501620-3502180] Lo entiendo.
[u612 3504260-3507620] Y después de la crema, desborda frescura y felicidad.
[u613 3509780-3512820] Ahora, la alegría es un tema importante en la Biblia.
[u614 3513220-3515380] Dios dice que quiere que estemos llenos de alegría.
[u615 3515380-3518440] Pero no es alegría ficticia de chapulines de domingo.
[u616 3510180-3523400] La alegría que no implica inocencia ante los desafíos de la vida.
[u617 3524040-3528120] Porque Jesús afrontó dificultades, tormentas, no obstante, nunca perdió la alegría.
[u618 3528520-3537000] Y en primera de perdón, en Juan 15 11 dijo les he dicho esto para que tengan alegría y así su alegría sea completa.
[u619 3537160-3538600] ¿Qué es una alegría completa?
[u620 3510180-3541560] La alegría que ofrece Jesús.
[u621 3541560-3543720] Diré algo casi infantil que sabemos todos.
[u622 3510860-3551620] Es diferente a las que prometen las concesionarias de automóviles, los préstamos, los paseos de compra.
[u623 3552100-3556100] Él no ofrece una alegría que depende de las circunstancias.
[u624 3556740-3559340] ¿La alegría de Jesús dependió de la aprobación de los demás?
[u625 3515460-3515540] No.
[u626 3559620-3561460] Ni siquiera su familia creía en él.
[u627 3557900-3563340] Dependió de las posesiones.
[u628 3515460-3564980] No tenía donde recostar la cabeza.
[u629 3535440-3569860] Su alegría dependía de la lealtad de la gente, de los grandes amigos que tenía.
[u630 3569860-3574960] Pedro lo negó, Judas lo traicionó, los otros salieron como ratas, los romanos lo mataron.
[u631 3574960-3575740] Hebreos 12.
[u632 3575740-3579076] 2 Por el gozo que le esperaba, soportó la cruz.
[u633 3580880-3583520] Entonces Jesús tenía una alegría resiliente.
[u634 3569860-3586800] Pedro habló de esa alegría.
[u635 3545380-3599960] A quien amáis sin haberle visto, en quien creyendo, aunque ahora no lo veáis, os alegráis con gozo inefable y glorioso, obteniendo el fin de vuestra fe, que es la salvación de vuestras almas.
[u636 3599960-3601840] Alguien tiene que celebrar más que eso, gente.
[u637 3601840-3602400] ¿Sí o no?
[u638 3509780-3608000] Ahora, ¿Sabés a quiénes les hablaba Pedro?
[u639 3545380-3609880] A los elegidos de Dios.
[u640 3513580-3630250] Dice arriba que viven como extranjeros, peregrinos en provincias como Galacia, Capodosia, Asia, Bitinia, o sea, Pablo le escribió a gente perseguida, inmigrantes ilegales, hombres y mujeres expulsados de sus ciudades, separado de sus familias, proscriptos de la ley.
[u641 3522360-3639130] Los adversarios le habían quitado sus derechos, sus propiedades, su dignidad, sus posesiones, pero no les pudieron quitar la alegría.
[u642 3639770-3641490] ¿Cuál era la fuente de esa alegría?
[u643 3572100-3645610] Como nadie podía quitarles a Jesús, nadie podía quitarles la alegría.
[u644 3580880-3658830] Entonces, mira, enterraste un sueño, enterraste un matrimonio, enterraste a un amigo, tu alegría yace en las parcelas de un panteón.
[u645 3514900-3666030] De ser así, anclaste el barco de tu alegría junto al muelle equivocado.
[u646 3524040-3672990] Porque el secreto es anclar nuestro corazón al pilar correcto, a Dios, al muelle correcto.
[u647 3672990-3676110] ¿Eso significa que no vamos a afrontar tormentas en la vida?
[u648 3515460-3677950] No, no, sí las vamos a afrontar.
[u649 3677950-3678517] Juan 16.
[u650 3678517-3681072] 33 En este mundo tendréis aflicción.
[u651 3681990-3682750] Anímense.
[u652 3683070-3684110] Yo he vencido al mundo.
[u653 3684670-3688910] ¿Significa que no vamos a atravesar las tierras áridas del dolor?
[u654 3515460-3694430] No, pero significa que esas tierras áridas no serán nuestro destino final.
[u655 3694430-3694997] Juan 16.
[u656 3694997-3697978] 20 Y la tristeza se convertirá en alegría.
[u657 3580880-3704150] Entonces la barca se va a sacudir, gente, las cosas se van a poner feas, nuestro ánimo va a fluctuar.
[u658 3704150-3706350] Sería un timador si te dijeran lo contrario.
[u659 3515460-3711990] No obstante, no vamos a quedarnos a la derima de un mar de desesperación.
[u660 3528520-3713550] Y hay algo más.
[u661 3510180-3717990] La alegría del Señor es viral, es contagiosa.
[u662 3683070-3725830] Yo aprendí en el arte del cine y de la televisión que todo el planeta puede llorar por lo mismo.
[u663 3726870-3731190] Usted pone una película, la vida Bella o Forrest Gump o cualquiera.
[u664 3528520-3737190] Y todo el mundo traducido a su idioma, todo el mundo llora por lo mismo, No todo el mundo se ríe por lo mismo.
[u665 3738220-3738820] ¿Tienen dudas?
[u666 3738820-3742420] Vayan la última entrega de los Oscar y van a ¿De qué cuernos se están riendo?
[u667 3742420-3748860] To gringo, que pase la chupitos a contar chistes y van a ver cómo se ríen.
[u668 3524040-3751780] Porque el mexicano no se ríe de lo mismo que el argentino.
[u669 3552100-3753820] El argentino no se ríe lo mismo que el guatemalteco.
[u670 3515460-3756860] No hay que ni siquiera extrapolarnos a Asia.
[u671 3522360-3758340] Los chinos no se ríen.
[u672 3676630-3759540] Si les gustó, se ríen.
[u673 3664710-3759900] Al final
[u674 3762060-3762700] de verdad.
[u675 3762700-3768320] Van guardando la risa y los aplausos hacen así como hacen negocios, son para como público.
[u676 3763620-3768720] Y al final.
[u677 3775920-3786480] Pero la risa que se contagia, independientemente de la etnia, de la raza, es la alegría que tenía la Iglesia del Nuevo Testamento, que no eran famosos por sus edificios, sino por la alegría.
[u678 3786480-3787033] Hechos 2.
[u679 3787033-3794531] 46 Partiendo el pan en la casa, comían juntos con alegría, con sencillez de corazón, teniendo el favor con todo el pueblo.
[u680 3784160-3795930] Eran alegres esos cristianos.
[u681 3784040-3799850] No debería haber cristianos que no sean alegres.
[u682 3800330-3804170] Porque la expresió es un cristiano alegre es una redundancia.
[u683 3804170-3807690] Si es cristiano, es alegre y si no es alegre, no es cristiano.
[u684 3784040-3810170] No hace falta el adjetivo cristiano alegre.
[u685 3784040-3814530] No hay un montón de cadáveres muertos, el agua está mojada.
[u686 3814530-3815730] Argentina, campeón del mundo.
[u687 3803530-3816730] Redundancia.
[u688 3820980-3827540] La semana pasada estuvo aquí un importante editor de libros y nos recorrí cientos de congregaciones.
[u689 3827540-3831860] Me sorprende que en River la gente canta y que está alegre.
[u690 3832740-3837380] Entonces yo digo cuando salgo de un cristiano tendría que me sorprende.
[u691 3828460-3839540] En River Hay gente alegre.
[u692 3839940-3841300] ¿Acaso existe otra manera?
[u693 3842100-3842380] Si.
[u694 3842380-3849310] Nuestra alegría no depende ni de Trump, ni de quien se sienta en la Casa Blanca, ni de Bukele, ni de Millet.
[u695 3842380-3852990] Nuestra alegría depende del Señor Jesucristo, ¿Sí o no?
[u696 3856670-3859070] Alguien tiene que celebrar por eso, ¿Sí o no?
[u697 3859630-3860590] Nuestra vieja.
[u698 3863230-3869710] Nuestra vieja espada de la alegría no depende de las circunstancias, de nuestra economía, de nuestra salud, de nuestra pareja.
[u699 3870840-3872160] Pregúntale a Pablo.
[u700 3872160-3875000] Quizás no tenga casa propia, dice, pero tengo fe en Dios.
[u701 3875000-3875820] Filipenses 1.
[u702 3875820-3882381] 12 Además, quiero que sepan que todo lo que me ha sucedido me ha servido para difundir la buena noticia.
[u703 3884520-3891240] Estoy contento de estar aquí en la cárcel, porque hasta el guardia del palacio sabe que estoy encadenado por causa de Cristo.
[u704 3874560-3893960] En la cárcel, alegre.
[u705 3894520-3896080] Y Pablo ¿Y si no tiene salud?
[u706 3896080-3897400] Ah, pero tengo vida eterna.
[u707 3897400-3898220] Filipenses 1.
[u708 3898220-3903077] 22 En realidad yo no sé qué es mejor, dice Pablo, y me cuesta trabajo elegir.
[u709 3887080-3909230] Porque en caso de seguir con vida, puedo serle útiles a ustedes, pero si me muero, me reúno con Jesucristo.
[u710 3881720-3912630] Para mí es mejor, pero por culpa de ustedes me voy a quedar vivo.
[u711 3914790-3917390] Pablo y quizás no duermas en sábanas de seda.
[u712 3917390-3919590] Ah sí, pero duermo con la conciencia limpia.
[u713 3919590-3920512] Filipenses 3.
[u714 3920512-3926830] 9 Y quiero que Dios me acepte, no por haber obedecido la ley, sino por confiar en Cristo.
[u715 3928450-3930850] Porque así es como Dios nos acepta.
[u716 3930850-3933010] Tener una conciencia limpia que le agrada.
[u717 3915390-3937970] Y Pablo si la billetera está vacía, bueno, pero la de mi Padre no.
[u718 3937970-3938892] Filipenses 4.
[u719 3938892-3944358] 11 No lo digo porque tenga escasez, porque me aprendí a contentar en lo poco.
[u720 3944450-3947410] Sé vivir humildemente, sé vivir en abundancia.
[u721 3916430-3951810] En todo y por todo estoy enseñado para tener hambre, para tener abundancia.
[u722 3947890-3954570] Todo lo puedo en Cristo que me fortalece.
[u723 3954570-3956270] Alguien tiene que decir amén.
[u724 3957950-3960510] El secreto del contentamiento
[u725 3962670-3964230] Tengo mucho, estoy feliz.
[u726 3962670-3965870] Tengo poco, Estoy feliz.
[u727 3965870-3966670] Adelgazo.
[u728 3969230-3970390] ¿Cuál era su secreto?
[u729 3970390-3971030] Jesucristo.
[u730 3969750-3973470] Su alegría no dependía de las cosas, dependía de Cristo.
[u731 3973790-3980670] Entonces yo estoy convencido, gente, que no necesitamos teologías novedosas, ni cumbres proféticas.
[u732 3971669-3986520] No estoy criticando, digo no las necesitamos, no son primera necesidad.
[u733 3976390-3993160] Necesitamos volver a la fuente, a las viejas bases, a las viejas armas espirituales.
[u734 3994520-4001640] Se terminó nuestro tiempo de horóscopos divinos, de empoderamiento barato, de profetas que endulzan nuestros oídos.
[u735 4002120-4004440] Tenemos que usar las viejas espadas del reino.
[u736 3972190-4009930] Las armas que Dios nos proveyó en el pasado, gente, funcionan hoy.
[u737 4007000-4013810] El mismo nombre que sobre todo nombre, lo diré otra vez.
[u738 3988120-4018730] La misma sangre vertida en la cruz, el mismo poder del Espíritu Santo.
[u739 4019290-4024370] Y cuatro de nuestras viejas espadas que funcionaron hace siglos, funcionan hoy.
[u740 4020170-4029770] Nuestras convicciones, no las pierdas, escríbelas en las tablas de tu corazón, atalas a tu cuello.
[u741 3995320-4033050] Nuestro propósito, nuestro significado en él.
[u742 4034020-4036980] Nuestra adoración genuina, no de labios, sino de corazón.
[u743 4019290-4041220] Y nuestra alegría, que no depende de las circunstancias.
[u744 4019290-4052980] Y te desafío a que usemos esas magníficas palabras de David, que hoy recuperamos esas armas y digamos ninguna como esas, dame las.
[u745 4019290-4059700] Y nos vamos armados, llenos de Dios, llenos de satisfacción Dale un aplauso al Señor de señores y al Rey de reyes.
[u746 4059700-4060420] Aleluya.
[u747 3971669-4064450] No, no, alguien tiene que celebrar más que eso.
[u748 4064450-4066330] Dar un aplauso grande al Rey.
[u749 4007000-4067610] El Rey está en la casa.
[u750 4068490-4069290] Todos, todos, todos.
[u751 4069690-4073530] Si crees que Dios habló, dale un aplauso al Rey.
[u752 4066850-4087190] Esta mañana Santo llama.
[u753 4097740-4105180] He transmitido lo que creo Dios me dijo que diga y como siempre, torpemente solo puedo llegar al intelecto de la gente.
[u754 4106540-4110260] Es el Espíritu Santo el que trae convicción y llega donde yo no puedo llegar.
[u755 4104580-4123140] De manera que si hay gente en casa o aquí que necesita hacer una de estas dos cosas, permitir que Cristo entre en su corazón y reine de verdad o reconciliarse con el Señor.
[u756 4123140-4136980] Porque hoy, wow, me cayó la moneda que a lo mejor yo soy un chapulín de templo o a lo mejor yo soy como el rey mogol que estoy atado al servir a Dios, pero soy un palacio sin rey a quien honrar.
[u757 4137700-4159569] Sea cual sea tu situación, no es necesario expresarla públicamente, pero sí delante del Señor y te invito a que tomemos unos minutos, cierres tus ojos y digas Señor, he recibido esta palabra y yo he transmitido esta palabra esta mañana y ruego que el Espíritu Santo selle con convicción lo que Dios ha hablado hoy.
[u758 4098940-4162849] Lo sagrado se nos ha vuelto común.
[u759 4170780-4181420] He pensado tantas veces en lo triste que debe ser vestirse o subir en mi caso a un avión para decir, tengo que predicar aunque no tenga ganas.
[u760 4182940-4189020] Hay momentos en que Dios me lleva a mi oración de muchacho cuando decía Señor, préstame los oídos de la gente.
[u761 4190380-4219350] Pero en algún momento entre la entre la promesa y el cumplimiento, entre la tierra prometida y el lugar de donde salimos, lo tedioso, lo abúlico, el desdén, la desidia toma lugar en nuestros corazones Y hoy quiero que todos, aún los que tengan años de convertidos en casa aquí puedan ser brutalmente honestos y decir Señor, vuélveme, quiero recuperar el gozo de la salvación,
[u762 4222140-4226540] quiero dejar de ser un crítico de cine para transformarme en parte de tu grey.
[u763 4227580-4235220] Vamos, todos los que tengan el bautismo del Espíritu intercedan como el Señor les da, los que no, abran la boca que de algo Dios la va a llenar.
[u764 4235220-4261000] Pero me encantaría que hoy no seamos pasajeros adormecidos de un tren, sino personas que digamos, quiero renovar mi compromiso porque una cosa tengo contra ti, que has perdido ese primer amor el primer amor tipifica esas ganas, esa energía, esa alegría, esas convicciones, esa adoración, eso que teníamos, que creíamos que nos íbamos a llevar el mundo por delante.
[u765 4261000-4267640] Benditos esos días de energía, de fuerzas, de fe sobrenatural.
[u766 4235220-4275440] Pero es el momento, dice el Espíritu, que hoy vuelvas, que volvamos a las convicciones.
[u767 4227580-4282720] Vamos, los que puedan levantar su mano, adorar, los que puedan poner la mano en su corazón, pero todo mundo adorando, todos, todos, todos
[u768 4285680-4304560] tomemos un tiempo para decir Señor, esta es la mañana en que tú no estás confrontando Señor, he transmitido lo que creo, me has dicho que diga, no he omitido, no he quitado nada lo que sé que es tu revelación Señor, si hay algo de mí, quítalo y que quede la savia, que quede la la esencia de lo que tú nos has hablado hoy.
[u769 4305200-4306800] Gracias Señor por esta mañana.
[u770 4305200-4324960] Gracias Dios porque puedo sentir aquí en el resto del sitio, de los sitios que están conectados, que hay una unción fresca, poderosa, trayendo convicción de arrepentimiento, una convicción que toca los tuétanos, las partes más profundas del alma y del corazón.
[u771 4325120-4343740] ¿Todos, wow, todos orando, todos clamando al Señor, Diga Señor, este es el momento donde yo puedo volver a aquello que había perdido a buscar la llave donde la perdí, dónde se te cayó el hacha, dice el Señor, en qué lugar se te cayó?
[u772 4308480-4345180] Porque ahí es donde va a flotar.
[u773 4346940-4370960] Volvamos al sitio junto al panteón, junto a la sala de cuidados intensivos, Volvamos a la corte del divorcio, volvamos al orfanato, volvamos a esa casa llena de violencia que era un cuadrilátero de boxeo al momento del abuso donde alguien robó tu inocencia para siempre Y digamos, ¿Es ese el clic?
[u774 4369280-4380760] Ese es el punto divergente donde perdí lo sagrado, donde la majestad se me hizo común Y otros no tienen que buscar en un trauma.
[u775 4332140-4384120] Yo sé que algunos tienen simplemente que ver dónde se desviaron.
[u776 4309960-4396600] El enemigo no va a querer que te vayas completamente, pero si logra que te desvíes apenas un centímetro de Jesús, habrá logrado de que seas un palacio sin rey a quien honrar.
[u777 4299640-4439130] Y en casa, los que me están viendo de otras partes del mundo, a todos aquellos con espíritu, Dios sabe que no intento insultarte, pero con una mente de insecto de templo, de creer que todo pasa bajo ese techo que son dos horas para recibir Dios, abra el techo, extienda el sitio de tu tienda y te muestre como habrán las estrellas y sepas que hay fuera propósito, significación, adoración, alegría, convicciones que hemos perdido en el altar de lo rutinario.
[u778 4440250-4450770] Cientos de miles de cristianos durante la pandemia se tuvieron que reencontrar con viejas armas Y muchos no tenían armas porque sus armas era el servicio.
[u779 4450770-4453530] Su arma era la identidad, Su arma era el título.
[u780 4387880-4457570] Pero el Señor dice, tus convicciones están allí, tómalas.
[u781 4457570-4458650] Ninguna como ellas.
[u782 4289080-4461860] Tu adoración está ahí, tómala.
[u783 4289080-4464100] Tu propósito está ahí, tómalo.
[u784 4289080-4464100] Tu alegría está ahí, tómalo.
[u785 4326000-4326640] Wow.
[u786 4327200-4328160] Todos, todos.
[u787 4468180-4468540] Vamos.
[u788 4468540-4470460] Levanta tu mano y comienza a clamar conmigo.
[u789 4470460-4476020] Dile, Señor, yo creo, yo declaro que los mejores días están por venir.
[u790 4288960-4482660] Que vienen cosas nuevas Que ojo no vio, ni oído yo, ni han subido a corazón de hombre impresionante.
[u791 4299640-4485940] Y que Dios va a traer cosas nuevas.
[u792 4286320-4489480] Un viento fresco, un viento de otra parte.
[u793 4489480-4490760] ¿Puede sentirlo?
[u794 4327200-4492760] Todos, todos, todos.
[u795 4495800-4496240] Vamos.
[u796 4496240-4499800] Los que tengan el bautismo del espíritu, intercedan como Dios les da ahora.
[u797 4501000-4503320] Intercesores, clamen conmigo ahora.
[u798 4496360-4506840] Que se corte todo lo que no es santo, todo lo que no es puro.
[u799 4496360-4515030] Que todo espíritu de rutina, que todo espíritu de desidia, de aburrimiento, de abulia se vaya ahora en el nombre del Señor.
[u800 4516150-4522310] Quita el yugo de la esclavitud y haznos libres a través de la verdad.
[u801 4523510-4524310] Todos, todos, todos.
[u802 4524550-4527190] Mira, hay gente encendida en fuego ahora.
[u803 4525510-4528950] Hay gente recibiendo ahora.
[u804 4529430-4532590] Más, más, Padre.
[u805 4497320-4537670] Del norte, del sur, del este y del oeste, viene un viento de otra parte.
[u806 4537990-4538630] Sopla.
[u807 4529430-4530150] Más, más.
[u808 4499320-4542390] Ahora
[u809 4544630-4546390] es la presencia del espíritu.
[u810 4546390-4547430] Momento, momento.
[u811 4548470-4549630] Tocándolo todo.
[u812 4549630-4550710] Pueden sentirlo.
[u813 4555430-4558870] En la gloria del Señor, llenándolo todo minuto a minuto.
[u814 4560790-4561670] Vamos, vamos, vamos.
[u815 4561670-4561990] Iglesia.
[u816 4561990-4563350] Adora, adora, adora, adora, adora.
[u817 4564480-4569600] Que el Señor escuche esa adoración que surge del alma, del corazón.
[u818 4556350-4570880] Señor, te adoro.
[u819 4573680-4577360] Perdóname por las veces que lo sagrado se me ha vuelto común.
[u820 4579760-4583760] Por las veces que vi esto como una simple profesión.
[u821 4586960-4593770] Por las veces de que tu gloria se me hizo tan normal que hasta me he dormido.
[u822 4595610-4600010] Perdóname nuestra irrespetuosidad.
[u823 4602330-4603450] Más de tu gloria.
[u824 4602330-4602690] Más.
[u825 4605370-4607770] Señor, te doy gracias por esta cuna de campeones.
[u826 4609850-4615770] Te doy gracias, Dios, por estos generales, estos obreros de primera línea, esta gente rota.
[u827 4617150-4619310] Y por providencia tuya,
[u828 4621630-4623790] tenerme al timón de esta nave insignia.
[u829 4624830-4629310] Te ruego que la mayor unción que tengas para un ser humano aquí en la tierra.
[u830 4629470-4633870] Derrames esta mañana con fuerza, con poder,
[u831 4636670-4638750] renovando, transformando.
[u832 4644920-4662200] Creo que lo diré otra vez, Las tormentas van a venir, las cosas se van a poner feas en el mundo, oiremos guerras, rumores de guerra, habrá plagas, no descartamos nuevas pandemias, Las cosas no van a mejorar si el Apocalipsis y la Biblia es real.
[u833 4663160-4666520] Pero el Señor dice que levantemos los ojos al cielo y tengamos ánimo.
[u834 4661480-4673730] La alegría no va a estar regulada por lo que ocurre en la economía, ni por las noticias de CNN o Fox.
[u835 4661480-4678530] La alegría nuestra no va a estar regulada por lo que ocurre alrededor.
[u836 4678690-4684290] Porque como dijo el Señor la semana pasada, a veces Dios calma la tormenta, pero a veces Dios calma al marinero.
[u837 4661320-4689330] Y hay veces que Dios nos calma en medio de la tormenta y sólo será esa promesa.
[u838 4689330-4702060] Paz en la tormenta, no te entregues, no te rindas, no baje los brazos, pelea por lo que amas, cree que los mejores días están por venir.
[u839 4661320-4710340] Y que Dios bendiga tu ser, tu familia, te bendiga en tu entrada, en tu salida, tu acostarte, tú levantarte, tu cruzar de las fronteras.
[u840 4703220-4715700] Bendiga a Dios tus suspiros más íntimos, tus sueños, tus visiones, tus ganas de despertar.
[u841 4715700-4728040] Tengas vientos a favor, siempre empujándote, tengas alegrías para tus hijos, tengas techo para los tuyos, comida en la mesa y nunca pierda las convicciones, la adoración, la alegría.
[u842 4724020-4737600] Nunca pierda bajo ningún punto de vista tu significación, porque estás rubricado con la firma del Señor y es tu pase para tener alegría y contentamiento.
[u843 4681050-4741920] Dios te bendiga, Dios te guarde y que haga resplandecer.
[u844 4741920-4745560] Dale un aplauso al Señor de señores y a la gente de todo el mundo.
[u845 4745880-4746440] Chau.
[u846 4678970-4747880] Cómo te ama el Señor.
[u847 4745880-4749120] Chau, chau, Chau, chau, Chau.
[u848 4749720-4750650] Bendiciones para todos.
[u849 4686210-4752600] Nos vemos en siete días.
[u850 4752600-4754240] Bendecidos para bendecir.
