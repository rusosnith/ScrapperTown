# ScrapperTown
Lugar donde scrapeo cosas

## Scrapers disponibles

### 1. Scraper de Comisiones de Diputados Nacionales
Extrae información de las comisiones de la Cámara de Diputados, incluyendo integrantes y reuniones.

**Archivos generados:**
- `comisiones_diputados.csv`: Información general de las comisiones
- `integrantes_comisiones.csv`: Histórico de integrantes con fechas de inicio y fin
- `reuniones_diputados.csv`: Reuniones de todas las comisiones

**Automatización:** Se ejecuta el 1° de cada mes

**Funcionalidad especial:** Mantiene un histórico de cambios en los integrantes. Cuando alguien es reemplazado, se cierra la fecha de fin del anterior y se agrega el nuevo con su fecha de inicio.

### 2. Scraper de Legisladores - Legislatura de Buenos Aires
Extrae información sobre los legisladores de la Legislatura de la Ciudad de Buenos Aires con seguimiento histórico.

**Datos extraídos:**
- Nombre completo, bloque político, mandatos
- URLs de perfil e imagen
- Correo electrónico y teléfono (cuando disponible)
- Comisiones de pertenencia

**Archivos generados:**
- `legisladores_historico.csv`: Registro histórico completo de todos los legisladores (activos e inactivos)
- `legisladores_activos.csv`: Solo legisladores actualmente en funciones
- Archivos de análisis por bloque y período

**Automatización:** Se ejecuta el 1° de cada mes

**Funcionalidad especial:** Sistema incremental que detecta cuando un legislador deja su cargo y registra automáticamente las fechas de baja, manteniendo un historial completo.

## Uso local

Para ejecutar cualquier scraper localmente:

1. Clone este repositorio
2. Instale las dependencias: `pip install requests beautifulsoup4 pandas`
3. Ejecute el script correspondiente:
   - `python scraper_comisiones_mejorado.py`
   - `python scraper_legiscaba.py`

## Licencia
Este proyecto está bajo la licencia MIT.
