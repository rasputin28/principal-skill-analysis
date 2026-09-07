# PSA — Principal Skill Analysis · Documento de diseño

**Fecha:** 2026-09-06
**Estado:** diseño aprobado, sin implementar. Cero corridas ejecutadas.
**Repo:** `~/Desa/PSA` (local, sin remoto)

---

## 1. Problema

La discusión sobre arneses y colecciones de skills para agentes de código se resuelve hoy
por retórica: cada autor publica su framework y afirma que mejora el rendimiento, sin que
exista un instrumento común para verificarlo. Es una pregunta **empírica** tratada como
pregunta de juicio.

Tres huecos concretos:

1. **No hay atribución.** Un framework se evalúa entero o no se evalúa. Nadie sabe qué
   parte del beneficio viene de cuál de sus piezas, ni cuántas de sus piezas no aportan nada.
2. **No hay combinatoria.** Las ablaciones que existen quitan un componente a la vez, lo que
   no distingue una skill inútil de una que solo funciona acompañada.
3. **No hay comparabilidad.** Dos colecciones publicadas por dos autores distintos no se
   pueden comparar porque nadie las midió contra la misma línea base, el mismo modelo y las
   mismas semillas.

## 2. Qué es PSA

Un instrumento público. Recibe como **entrada** una o más colecciones de skills (repo git +
commit fijado) y devuelve:

- El aporte marginal de cada skill, con intervalo de confianza, y su coste asociado.
- La descomposición en ejes latentes de capacidad, y la carga de cada skill sobre esos ejes.
- La comparación entre colecciones sobre una línea base común.

El catálogo es un **parámetro**, no una constante del estudio. Este es el requisito que
convierte a PSA de estudio en herramienta y el que gobierna toda la arquitectura.

## 3. No-objetivos

- No mide modelos base ni los ordena. El modelo es una variable de control fijada.
- No mide arneses completos como caja negra *en lugar de* skills; el modo comparativo existe,
  pero el aporte del trabajo es la descomposición interna.
- No propone skills nuevas ni las edita. PSA mide lo que otros escribieron.
- No optimiza. No es una búsqueda de la mejor configuración; es una atribución de mérito.

## 4. Formulación

Sea $S = \{s_1, \dots, s_N\}$ el catálogo bajo prueba y $C \subseteq S$ una configuración (el subconjunto de
skills disponible para el agente en una corrida). Sea `T` el conjunto de tareas del benchmark
y `Y(t, C, r)` el resultado de la corrida `r` sobre la tarea `t` bajo la configuración `C`.

Función de valor:

```math
v(C) \;=\; \mathbb{E}_{t \in T,\, r}\big[\,Y(t, C, r)\,\big]
```

### 4.1 Estimando primario — valor de Shapley

```math
\varphi_i \;=\; \sum_{C \subseteq S \setminus \{i\}} \frac{|C|!\,(N-|C|-1)!}{N!}\Big[\,v(C \cup \{i\}) - v(C)\,\Big]
```

Equivalentemente, en la base de dividendos $a(T)$ del Teorema de representación:

```math
v(C) \;=\; \sum_{T \subseteq C} a(T),
\qquad
\varphi_i \;=\; \sum_{T \,\ni\, i} \frac{a(T)}{|T|},
\qquad
a(T) \;=\; \sum_{L \subseteq T} (-1)^{|T|-|L|} v(L)
```

y si $a(T) = 0$ para todo $|T| > t$, bastan $p = \sum_{j=0}^{t}\binom{N}{j} = O(N^{t})$ números.

Se elige Shapley y no un coeficiente de regresión ni una ablación simple por cuatro
propiedades, todas necesarias aquí:

- **Eficiencia:** $\sum_i \varphi_i = v(S) - v(\emptyset)$. El aporte de las partes suma exactamente la mejora
  total de la colección. Es la propiedad que hace legítimo el gráfico de Pareto ordenado por
  $\varphi$: los porcentajes suman $100\%$ por teorema, no por normalización arbitraria.
- **Jugador nulo:** una skill que nunca cambia el resultado recibe $\varphi_i = 0$ exacto.
- **Simetría:** dos skills intercambiables reciben el mismo $\varphi$.
- **Promedio sobre coaliciones:** $v(C \cup \{i\}) - v(C)$ se promedia sobre *todos* los contextos
  posibles. Una skill que solo rinde acompañada aparece aquí y no aparece en una ablación
  leave-one-out.

### 4.2 Estimando secundario — ejes latentes (el PSA propiamente dicho)

Se construye la matriz `Y ∈ R^{|T| × |C|}` (tareas × configuraciones evaluadas) y se le aplica
descomposición en componentes principales. Las componentes son **ejes latentes de demanda de
la tarea**: agrupaciones de tareas que se resuelven o fallan juntas bajo el mismo tipo de
intervención. Cada skill se proyecta sobre esos ejes.

El resultado deja de ser un número por skill y pasa a ser una posición en un espacio: qué
skills son redundantes entre sí (cargan sobre el mismo eje) y cuál es el subconjunto mínimo
que cubre el espacio. Es lo que permite responder "esta colección y aquella se solapan en
verificación pero solo una cubre exploración".

Nota metodológica que debe quedar explícita en el paper: PCA aquí opera sobre la **matriz de
resultados**, no sobre la matriz de diseño. PCA sobre la matriz de diseño solo diagnosticaría
colinealidad entre configuraciones, que es un chequeo de higiene, no un hallazgo.

### 4.3 Estimando terciario — comparación entre catálogos

Para dos catálogos `A` y `B` evaluados con el mismo agente base, mismo benchmark, mismo modelo
y mismas semillas, las cantidades comparables son:

- $v(S_A) - v(\emptyset)$ frente a $v(S_B) - v(\emptyset)$: cuánto compra cada colección sobre el agente desnudo.
- El mismo delta normalizado por coste (tokens, turnos, tiempo).
- El solape en el espacio latente de 4.2.

$\varphi_i$ individual **no** es comparable entre catálogos distintos (los repartos son internos a
cada colección); el total sí lo es. Esta distinción debe estar escrita en el reporte, porque
es la forma más probable de que alguien use mal la herramienta.

## 5. Diseño experimental

$2^N$ es inabordable por enumeración: con $N = 20$, más de un millón de configuraciones. La ruta
principal cambia de base (arriba); el cribado en dos etapas queda como respaldo de presupuesto.

### Etapa 1 — cribado (screening)

Diseño factorial fraccionado de **Resolución IV**, construido como diseño de Plackett–Burman
seguido de su reflejo (foldover). Coste en configuraciones: $2 \cdot 4\lceil (N+1)/4 \rceil$, es decir $48$
configuraciones para `N ≤ 23`.

Se descarta Resolución III pese a costar la mitad: aliasa los efectos principales con las
interacciones de dos factores, y por tanto puede eliminar exactamente la skill que solo
funciona acompañada — que es la pregunta central del trabajo. Resolución IV aliasa los
principales con interacciones de tres factores, un riesgo aceptable.

Salida: los `N` efectos principales ordenados por magnitud. Se retienen las `k` skills cuyo
efecto no es indistinguible de cero, con `k` fijado *a priori* (ver §9) para no elegir el
corte después de ver los datos.

### Etapa 2 — Shapley exacto

Sobre las $k$ supervivientes, factorial completo $2^k$. Con $k = 7$, $128$ configuraciones.
Shapley se calcula exacto: sin muestreo, sin modelo sustituto, sin aproximación que un
revisor pueda cuestionar. Las interacciones de todos los órdenes quedan capturadas.

### Validación del cribado

Muestreo por permutaciones (estimador de Shapley por muestreo, presupuesto reducido) sobre el
catálogo **completo**, para verificar que ninguna skill descartada en la etapa 1 tiene $\varphi$
alto. Es el control que responde a "¿y si tu cribado se equivocó?". Si una descartada aparece
con $\varphi$ significativo, se reporta como fallo del diseño de cribado, no se corrige en silencio.

### Presupuesto

```
corridas = (configuraciones_etapa1 + configuraciones_etapa2 + configuraciones_validación)
           × |T_efectivo| × repeticiones
```

Los tres factores se fijan antes de correr y se publican en el pre-registro.

## 6. Potencia estadística

Es la parte donde estos estudios fracasan y debe ir primero en la implementación, no al final.
`Y` es Bernoulli y el agente es estocástico; detectar un delta de pocos puntos porcentuales con
muestreo independiente exige miles de corridas por comparación.

Tres palancas, en orden de impacto:

1. **Pareo por tarea (bloqueo).** La misma tarea, la misma semilla, el mismo modelo; lo único
   que cambia es `C`. El análisis se hace sobre diferencias intra-tarea. Esto elimina la
   varianza de dificultad de tarea, que en SWE-bench es la dominante: hay tareas que resuelve
   cualquier configuración y tareas que no resuelve ninguna. Es la palanca más grande, con
   diferencia.
2. **Desenlace continuo en vez de binario.** `resolved ∈ {0,1}` desperdicia información. Se
   registran además: fracción de tests fail-to-pass que pasan, turnos hasta la solución, tokens
   consumidos, y si el parche toca los archivos correctos. El desenlace primario se declara en
   el pre-registro; los demás son secundarios.
3. **Banda informativa.** Un piloto clasifica las tareas por dificultad bajo la línea base. Las
   que se resuelven siempre y las que no se resuelven nunca no aportan información sobre skills.
   Restringir a la banda intermedia multiplica la señal por corrida. El criterio de corte se
   fija en el pre-registro y las tareas excluidas se publican.

Intervalos de confianza por bootstrap **sobre tareas** (no sobre corridas), respetando el pareo.

## 7. Controles de validez

Cuatro controles. Sin ellos el resultado es inatribuible y el paper no sobrevive revisión.

### 7.1 Placebo de longitud
Cargar una skill añade contexto al prompt. Una skill podría "funcionar" solo por alargarlo.
Se incluye en cada diseño una **skill placebo**: longitud en tokens equivalente a la mediana
del catálogo, contenido plausible pero sin instrucción accionable. Su $\varphi$ debe tener un
intervalo de confianza que contenga cero. **Si no lo contiene, el instrumento está roto y no
se reportan resultados.** Este es el control negativo que valida todo el aparato.

### 7.2 Activación real (ITT vs. tratados)
Las skills se cargan por descriptor y el agente decide invocarlas. Si nunca la invoca, se está
midiendo *disponibilidad*, no *efecto*. Se instrumenta la traza para registrar si la skill fue
efectivamente leída/invocada, y se reportan **ambas** cifras: intención de tratar (asignada) y
efecto en tratados (invocada). La brecha entre las dos es en sí un hallazgo publicable: una
skill excelente que nunca se dispara vale cero en la práctica.

### 7.3 Contaminación del benchmark
SWE-bench Verified es anterior al corte de entrenamiento de los modelos actuales. Un $\varphi$ puede
reflejar memorización y no capacidad. Mitigación: un conjunto de validación externa posterior
al corte —PRs propios o instancias recientes— sobre el que se verifica si el **orden** de los
$\varphi$ se transfiere. Si se transfiere, el hallazgo es sobre skills; si no, era memorización, y
eso también se reporta.

### 7.4 Alcance por modelo y por arnés
Los $\varphi$ pueden invertirse entre modelos. O se corren al menos dos modelos, o el alcance se
declara en el enunciado del hallazgo. Lo mismo para el arnés que aloja las skills.

## 8. Arquitectura

Siete componentes con fronteras explícitas. Cada uno se entiende y se prueba por separado.

| Componente | Entrada | Salida | Responsabilidad única |
|---|---|---|---|
| `catalog` | URL git + commit, o ruta local | `catalog.json` normalizado | Descubrir skills, extraer descriptor y conteo de tokens, fijar la procedencia |
| `design` | `N`, etapa, semilla | matriz de configuraciones | Generar el diseño (Res-IV, factorial completo, permutaciones). Determinista |
| `compile` | configuración `C` | workspace hermético | Materializar un entorno con exactamente las skills de `C` y nada más |
| `runner` | (tarea, config, semilla) | traza + desenlaces | Ejecutar el agente. Una implementación por arnés, tras una interfaz común |
| `trace` | traza cruda | registro de activación | Determinar qué skills se invocaron realmente |
| `estimate` | ledger de corridas | $\varphi$ + IC, PCA, comparativas | Todo el análisis. Sin acceso al runner |
| `report` | resultados | ficha del catálogo | Presentación honesta, incluidos los controles fallidos |

Frontera dura entre `runner` y `estimate`: el análisis debe poder correrse sobre un ledger
publicado por un tercero sin reejecutar nada. Es lo que hace verificable el resultado.

`compile` es donde se filtra la contaminación entre corridas. Debe ser hermético y verificable:
un test que confirme que en un workspace de la configuración `C` no hay ningún archivo de una
skill fuera de `C`.

### Interfaz de arnés

Comparar "el arnés de un autor contra el de otro" exige que el arnés sea sustituible. `runner`
expone una interfaz mínima —preparar workspace, ejecutar tarea, devolver traza y desenlace— y
cada arnés soportado es una implementación. Un arnés no soportado se declara no soportado; no
se aproxima.

## 9. Pre-registro

Antes de la primera corrida real se congela y se publica un documento con: catálogo y commits,
benchmark y subconjunto de tareas, modelo y versión, semillas, `k` (número de supervivientes
del cribado), desenlace primario, criterio de banda informativa, y las hipótesis. El hash del
pre-registro se cita en el paper.

Motivo: el espacio de configuraciones es enorme y siempre existe una configuración que produce
el resultado bonito. Sin pre-registro, este trabajo es indefendible.

## 10. Criterios de éxito

Verificables, en orden. El proyecto no avanza si uno falla.

1. **Control negativo:** el $\varphi$ de la skill placebo tiene IC que contiene cero.
2. **Control positivo:** una skill saboteadora deliberada (por ejemplo, "omite los tests")
   produce $\varphi$ significativamente negativo.
3. **Estabilidad:** dos réplicas independientes con semillas distintas producen órdenes de $\varphi$
   concordantes, con un umbral de concordancia (τ de Kendall) fijado en el pre-registro.
4. **Reproducibilidad por terceros:** `estimate` corrido sobre el ledger publicado reproduce las
   cifras del paper sin acceso al runner.
5. **Eficiencia:** los $\varphi$ estimados suman `v(S) − v(∅)` dentro de la tolerancia numérica.

Los criterios 1 y 2 se corren *antes* que cualquier medición de interés. Son la calibración del
instrumento; medir con un instrumento sin calibrar es lo que hace este campo hoy.

## 11. Riesgos abiertos

- **Coste.** Es el riesgo principal y no está acotado hasta que se fije el presupuesto de §5.
  Mitigación: el piloto de banda informativa se corre primero y sobre pocas tareas.
- **Efecto nulo.** Es posible que ningún $\varphi$ sea distinguible de cero con presupuesto realista.
  Ese resultado es publicable y debe reportarse tal cual; el diseño no debe empujar hacia el
  hallazgo positivo.
- **Sensibilidad al arnés.** Si los $\varphi$ cambian de signo entre arneses, el hallazgo se vuelve
  condicional y pierde fuerza. Se detecta con el factor de arnés y se reporta.
- **Citas del paper sin verificar.** Las referencias del borrador deben verificarse una a una
  contra la fuente antes de someter.

## 12. Decisiones cerradas en esta sesión

1. Benchmark principal: SWE-bench Verified; PRs propios como validación externa post-corte.
2. Tratamiento: skills individuales y sus combinatorias, con el catálogo como parámetro de entrada.
3. Estimando primario: Shapley exacto en dos etapas. No PCA sobre la matriz de diseño, no Benford.
4. Nombre y ruta: PSA — Principal Skill Analysis, `~/Desa/PSA`.
5. Género del paper: Registered Report Stage 1 (pre-registro), primera persona singular.
