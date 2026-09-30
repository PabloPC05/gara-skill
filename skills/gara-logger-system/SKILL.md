---
name: "gara-logger-system"
description: "Implementa o corrige logging frontend o backend de Gara usando la infraestructura existente y registros adecuados al entorno."
---

# Logging Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe evento/problema de logging e infraestructura actual; entrega cambios acotados y evidencia de niveles/redacción. Si falta acceso a un entorno, limita las pruebas a los entornos disponibles. No requiere delegación.

Inspecciona la infraestructura actual antes de crear otra. En backend usa logging y conserva filtros de redacción, especialmente tickets y credenciales; en frontend sigue los patrones del cliente API y el entorno de Vite. Acota cada cambio a la petición: retirar logging anterior o sustituir todos los console no es automático. No registres secuencias privadas, tokens, payloads sensibles o .env. Verifica desarrollo/producción y eventos de error; cubre redacción y niveles con pruebas de comportamiento.
