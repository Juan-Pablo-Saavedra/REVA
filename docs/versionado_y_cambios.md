# Versionado, ramas y gestión de cambios

## Versionado

Se usa versionado semántico `MAJOR.MINOR.PATCH`:

- **MAJOR**: cambios incompatibles en la API.
- **MINOR**: funcionalidades nuevas compatibles.
- **PATCH**: correcciones de errores.

La línea base es la versión `1.0.0` y se marca con la etiqueta anotada `v1.0.0` sobre la rama `main`.
No se usa un sufijo como `-baseline` en el nombre de la etiqueta porque, según el versionado semántico,
un sufijo con guion indica una versión de prelanzamiento (de menor precedencia que `1.0.0`).

## Ramas

| Rama | Uso |
|---|---|
| `main` | Rama estable. Solo recibe código con las pruebas en verde. |
| `feature/<nombre>` | Una funcionalidad nueva. |
| `fix/<nombre>` | Corrección de un error. |
| `test/<nombre>` · `docs/<nombre>` | Pruebas o documentación. |

Las ramas se integran en `main` con una fusión explícita (`--no-ff`) para conservar la historia.

## Mensajes de commit

Los mensajes siguen la especificación [Conventional Commits 1.0.0](https://www.conventionalcommits.org/es/v1.0.0/): `tipo(ámbito): resumen en presente`, con un cuerpo opcional separado por una línea en blanco.

| Tipo | Uso | Efecto en la versión |
|---|---|---|
| `feat` | Funcionalidad nueva. | MINOR |
| `fix` | Corrección de un error. | PATCH |
| `test` · `docs` · `chore` | Pruebas, documentación y mantenimiento. | Ninguno |

Un cambio incompatible se marca con `!` después del tipo (`feat(pedidos)!: ...`) o con el pie `BREAKING CHANGE:` y obliga a subir MAJOR. Los commits de fusión conservan el mensaje que genera Git (`Merge branch '<rama>'`).

## Cambios posteriores a la línea base

Todo cambio sobre la línea base sigue este camino:

1. Se registra como *issue* (plantilla de error o de mejora).
2. Se evalúa su impacto técnico, funcional y de esfuerzo, y se aprueba o rechaza.
3. Se implementa en una rama propia, con pruebas.
4. Se revisa mediante *pull request* y se fusiona en `main` si las pruebas pasan.
5. Se actualiza `CHANGELOG.md` y, cuando corresponda, se crea una nueva etiqueta de versión.

La etiqueta `v1.0.0` no se mueve ni se reescribe: una línea base ya aprobada solo cambia
creando una versión posterior.
