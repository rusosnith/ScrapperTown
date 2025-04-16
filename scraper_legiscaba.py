import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import os
import random
import pandas as pd
import re

# URL base
URL_BASE = 'https://legislatura.gob.ar/seccion/composicion-actual.html'

def obtener_legisladores():
    """Extrae la información de los legisladores desde la página principal"""
    try:
        # Hacemos la solicitud HTTP con encabezados más realistas
        print("Obteniendo información de legisladores...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(URL_BASE, headers=headers)
        
        # Guardamos el HTML para depuración
        with open('debug_pagina.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        if response.status_code != 200:
            print(f"Error al obtener la página: {response.status_code}")
            return []
        
        # Añadimos una pausa para evitar sobrecargar el servidor
        time.sleep(random.uniform(1, 3))  # Pausa aleatoria entre 1 y 3 segundos
            
        # Parseamos el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Primero, intentemos encontrar la tabla por ID
        table = soup.find('table', id='data-integrantes')
        
        # Si no encontramos por ID, intentemos otros métodos
        if not table:
            print("No se encontró la tabla por ID, intentando por clase...")
            table = soup.find('table', class_='table-hover')
        
        # Otro intento por atributos data-*
        if not table:
            table = soup.find('table', attrs={'data-role': 'grid'})
        
        # Si todavía no encontramos, buscamos cualquier tabla con 'legislador' en alguna parte
        if not table:
            print("Intentando encontrar cualquier tabla con información de legisladores...")
            tables = soup.find_all('table')
            for t in tables:
                if t.find(string=re.compile('legislador|Legislador|diputado|Diputado', re.IGNORECASE)):
                    table = t
                    break
        
        if not table:
            print("No se encontró ninguna tabla de legisladores en el HTML")
            print("Guardando HTML completo para depuración en 'debug_pagina.html'")
            return []
        
        # Imprimimos información sobre la tabla encontrada para depuración
        print(f"Tabla encontrada: ID={table.get('id')}, Clase={table.get('class')}")
        
        # Intentar encontrar las filas de la tabla
        tbody = table.find('tbody')
        if not tbody:
            print("No se encontró el cuerpo de la tabla, usando la tabla directamente")
            rows = table.find_all('tr')
        else:
            rows = tbody.find_all('tr')
        
        print(f"Se encontraron {len(rows)} filas en la tabla")
        
        legisladores = []
        
        # Iteramos por cada fila de la tabla, saltando la cabecera si existe
        for row in rows:
            # Detectamos si es una fila de encabezado
            if row.find('th'):
                continue
                
            cells = row.find_all('td')
            
            # Verificamos que haya suficientes celdas
            if len(cells) < 5:
                print(f"Fila con número insuficiente de celdas: {len(cells)}")
                continue
            
            # Obtener imagen
            img_tag = cells[0].find('img')
            img_url = img_tag['src'] if img_tag else None
            
            # Obtener nombre del legislador
            legislator_cell = cells[1]
            legislator_link = legislator_cell.find('a')
            
            if legislator_link:
                legislator_name = legislator_link.text.strip()
                legislator_url = legislator_link['href']
            else:
                legislator_name = legislator_cell.text.strip()
                legislator_url = None
            
            # Limpiar el nombre (quitar saltos de línea y espacios extra)
            if legislator_name:
                legislator_name = re.sub(r'\s+', ' ', legislator_name.replace('\n', ' ')).strip()
            
            # Obtener bloque político
            bloc_cell = cells[2]
            bloc_link = bloc_cell.find('a')
            
            if bloc_link:
                bloc_name = bloc_link.text.strip()
                bloc_url = bloc_link['href']
            else:
                bloc_name = bloc_cell.text.strip()
                bloc_url = None
            
            # Obtener fechas de mandato
            mandate_start = cells[3].text.strip().replace('<center>', '').replace('</center>', '')
            mandate_end = cells[4].text.strip().replace('<center>', '').replace('</center>', '')
            
            # Imprimir para depuración
            print(f"Legislador encontrado: {legislator_name}, Bloque: {bloc_name}")
            
            # Crear un diccionario con la información
            legislador = {
                'nombre': legislator_name,
                'perfil_url': legislator_url,
                'imagen_url': img_url,
                'bloque': bloc_name,
                'bloque_url': bloc_url,
                'mandato_inicio': mandate_start,
                'mandato_fin': mandate_end,
                'fecha_extraccion': datetime.now().strftime("%Y-%m-%d"),
                'activo': True  # Indicador de si el legislador está actualmente en funciones
            }
            
            legisladores.append(legislador)
            
        print(f"Se encontraron {len(legisladores)} legisladores")
        return legisladores
        
    except Exception as e:
        print(f"Error al obtener los legisladores: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# El resto del código permanece igual...

def main():
    # Definimos los archivos CSV
    archivo_legisladores = 'legisladores_historico.csv'
    
    # Obtiene la información de los legisladores actuales
    nuevos_legisladores = obtener_legisladores()
    
    if not nuevos_legisladores:
        print("No se encontraron legisladores. Abortando operación.")
        return
    
    # Si existen legisladores previos, los cargamos
    legisladores_existentes = cargar_legisladores_existentes(archivo_legisladores)
    
    # Obtener detalles solo para nuevos legisladores
    if os.environ.get('OBTENER_DETALLES', 'true').lower() == 'true':
        # Creamos un conjunto con los nombres de legisladores existentes
        nombres_existentes = {leg['nombre'] for leg in legisladores_existentes}
        
        print("Obteniendo detalles de legisladores nuevos...")
        for legislador in nuevos_legisladores:
            # Solo obtenemos detalles para los que no existen aún
            if legislador['nombre'] not in nombres_existentes and legislador['perfil_url']:
                detalles = obtener_detalles_legislador(
                    legislador['perfil_url'], 
                    legislador['nombre']
                )
                # Actualizamos el diccionario con los detalles obtenidos
                legislador.update(detalles)
    
    # Combinamos los legisladores existentes con los nuevos, manteniendo historial
    todos_legisladores = combinar_legisladores_historicos(legisladores_existentes, nuevos_legisladores)
    
    # Definimos los campos para el CSV
    campos = ['nombre', 'perfil_url', 'imagen_url', 'bloque', 'bloque_url', 
             'mandato_inicio', 'mandato_fin', 'fecha_extraccion', 
             'email', 'telefono', 'comisiones', 'activo', 'fecha_alta', 'fecha_baja']
    
    # Guardamos todos los legisladores en un archivo CSV
    guardar_csv(todos_legisladores, archivo_legisladores, campos)
    
    # Generamos análisis de los datos
    generar_analisis(todos_legisladores)
    
    # Generamos un CSV solo con legisladores activos para fácil consulta
    legisladores_activos = [leg for leg in todos_legisladores if leg.get('activo', False)]
    guardar_csv(legisladores_activos, 'legisladores_activos.csv', campos)

if __name__ == '__main__':
    main()