---
name: "gara-logger-system"
description: "Implementa o corrige logging frontend o backend de Gara con la infraestructura existente y niveles adecuados al entorno; usar cuando falten, sobren o filtren datos sensibles los registros de un evento o error."
---

# Logging Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe el evento o problema de logging y la infraestructura actual; entrega cambios acotados y evidencia de niveles y redacción. Si falta acceso a un entorno, limita las pruebas a los disponibles. Al terminar, devuelve lo hecho y espera instrucciones: no encadena otras skills ni hace commit.

Inspecciona la infraestructura actual antes de crear otra. En backend usa `logging` y conserva los filtros de redacción, en especial tickets y credenciales; en frontend sigue los patrones del cliente API y el entorno de Vite. Acota cada cambio a la petición: retirar logging anterior o sustituir todos los `console` no es automático. No registres secuencias privadas, tokens, payloads sensibles ni `.env`. Verifica desarrollo y producción y los eventos de error; cubre redacción y niveles con pruebas de comportamiento.
