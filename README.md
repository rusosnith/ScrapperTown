# ScrapperTown
Lugar donde scrapeo cosas

- scrapeo de reuniones de comision de diputados nacionales
- scrapeo de legisladores de la ciudad de buenos aires

# Scraper de Legisladores - Legislatura de Buenos Aires

Este repositorio contiene un scraper automático que extrae información sobre los legisladores de la Legislatura de la Ciudad de Buenos Aires.

## Datos extraídos

El scraper obtiene los siguientes datos:

- Nombre completo de los legisladores
- URL del perfil en el sitio oficial
- URL de la imagen
- Bloque político
- URL del bloque político
- Fecha de inicio y fin del mandato
- Correo electrónico (cuando está disponible)
- Teléfono (cuando está disponible)
- Comisiones a las que pertenece (cuando está disponible)

## Archivos generados

- `legisladores.csv`: Contiene la información completa de todos los legisladores
- `analisis_bloques.csv`: Análisis de la distribución de legisladores por bloque político
- `analisis_periodos.csv`: Análisis de la distribución de legisladores por año de inicio del mandato

## Automatización

Este scraper se ejecuta automáticamente cada semana mediante GitHub Actions, asegurando que los datos estén siempre actualizados.

## Uso local

Para ejecutar el scraper localmente:

1. Clone este repositorio
2. Instale las dependencias: `pip install requests beautifulsoup4 pandas`
3. Ejecute el script: `python scraper_legislatura.py`

## Licencia

Este proyecto está bajo la licencia MIT.
