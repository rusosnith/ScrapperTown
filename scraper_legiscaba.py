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
        # Hacemos la solicitud HTTP
        print("Obteniendo información de legisladores...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL_BASE, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al obtener la página: {response.status_code}")
            return []
        
        # Añadimos una pausa para evitar sobrecargar el servidor
        time.sleep(random.uniform(1, 3))  # Pausa aleatoria entre 1 y 3 segundos
            
        # Parseamos el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontramos la tabla de legisladores
        table = soup.find('table', id='data-integrantes')
        
        if not table:
            print("No se encontró la tabla de legisladores en el HTML")
            return []
        
        legisladores = []
        
        # Iteramos por cada fila de la tabla, saltando la cabecera
        for row in table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            
            # Obtener imagen
            img_tag = cells[0].find('img')
            img_url = img_tag['src'] if img_tag else None
            
            # Obtener nombre del legislador
            legislator_cell = cells[1]
            legislator_link = legislator_cell.find('a')
            legislator_name = legislator_link.text.strip() if legislator_link else None
            legislator_url = legislator_link['href'] if legislator_link else None
            
            # Limpiar el nombre (quitar saltos de línea y espacios extra)
            if legislator_name:
                legislator_name = re.sub(r'\s+', ' ', legislator_name.replace('\n', ' ')).strip()
            
            # Obtener bloque político
            bloc_cell = cells[2]
            bloc_link = bloc_cell.find('a')
            bloc_name = bloc_link.text.strip() if bloc_link else None
            bloc_url = bloc_link['href'] if bloc_link else None
            
            # Obtener fechas de mandato
            mandate_start = cells[3].text.strip().replace('<center>', '').replace('</center>', '')
            mandate_end = cells[4].text.strip().replace('<center>', '').replace('</center>', '')
            
            # Crear un diccionario con la información
            legislador = {
                'nombre': legislator_name,
                'perfil_url': legislator_url,
                'imagen_url': img_url,
                'bloque': bloc_name,
                'bloque_url': bloc_url,
                'mandato_inicio': mandate_start,
                'mandato_fin': mandate_end,
                'fecha_extraccion': datetime.now().strftime("%Y-%m-%d")
            }
            
            legisladores.append(legislador)
            
        print(f"Se encontraron {len(legisladores)} legisladores")
        return legisladores
        
    except Exception as e:
        print(f"Error al obtener los legisladores: {e}")
        return []

def obtener_detalles_legislador(url_perfil, nombre_legislador):
    """Obtiene información detallada del perfil de un legislador"""
    detalles = {}
    
    if not url_perfil:
        return detalles
        
    try:
        print(f"Obteniendo información detallada de {nombre_legislador}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url_perfil, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al obtener el perfil de {nombre_legislador}: {response.status_code}")
            return detalles
        
        # Añadimos una pausa para evitar sobrecargar el servidor
        time.sleep(random.uniform(1.5, 4))  # Pausa aleatoria entre 1.5 y 4 segundos
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer correo electrónico (ejemplo, ajustar según la estructura real)
        email_element = soup.find('a', href=lambda href: href and 'mailto:' in href)
        if email_element:
            detalles['email'] = email_element['href'].replace('mailto:', '')
        
        # Extraer teléfono (ejemplo, ajustar según la estructura real)
        telefono_element = soup.find('span', class_='telefono')
        if telefono_element:
            detalles['telefono'] = telefono_element.text.strip()
            
        # Extraer información de comisiones (ejemplo, ajustar según la estructura real)
        comisiones_section = soup.find('div', id='comisiones') or soup.find('section', class_=lambda c: c and 'comisiones' in c)
        if comisiones_section:
            comisiones = []
            for comision_item in comisiones_section.find_all(['li', 'div', 'p']):
                comision_texto = comision_item.text.strip()
                if comision_texto:
                    comisiones.append(comision_texto)
            
            if comisiones:
                detalles['comisiones'] = "|".join(comisiones)
        
        return detalles
        
    except Exception as e:
        print(f"Error al obtener detalles de {nombre_legislador}: {e}")
        return detalles

def cargar_legisladores_existentes(nombre_archivo):
    """Carga los legisladores existentes desde un archivo CSV"""
    legisladores = []
    
    if not os.path.exists(nombre_archivo):
        return legisladores
        
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            reader = csv.DictReader(archivo)
            for fila in reader:
                legisladores.append(fila)
                
        print(f"Se cargaron {len(legisladores)} legisladores existentes desde {nombre_archivo}")
        return legisladores
        
    except Exception as e:
        print(f"Error al cargar legisladores desde {nombre_archivo}: {e}")
        return []

def combinar_legisladores(existentes, nuevos):
    """Combina los legisladores existentes con los nuevos, actualizando datos"""
    # Creamos un diccionario con los legisladores existentes usando el nombre como clave
    dict_existentes = {leg['nombre']: leg for leg in existentes}
    
    # Lista para el resultado combinado
    combinados = []
    
    # Contador de actualizaciones
    actualizados = 0
    nuevos_agregados = 0
    
    # Procesamos los nuevos legisladores
    for nuevo in nuevos:
        nombre = nuevo['nombre']
        
        # Si ya existe, actualizamos algunos campos y conservamos otros
        if nombre in dict_existentes:
            legislador = dict_existentes[nombre].copy()
            
            # Campos que siempre actualizamos
            legislador['bloque'] = nuevo['bloque']
            legislador['imagen_url'] = nuevo['imagen_url']
            legislador['fecha_extraccion'] = nuevo['fecha_extraccion']
            
            # Añadimos el legislador combinado
            combinados.append(legislador)
            actualizados += 1
        else:
            # Es un legislador nuevo
            combinados.append(nuevo)
            nuevos_agregados += 1
    
    print(f"Actualización completada: {actualizados} legisladores actualizados, {nuevos_agregados} nuevos agregados")
    return combinados

def guardar_csv(datos, nombre_archivo, campos):
    """Guarda la información en un archivo CSV"""
    try:
        if not datos:
            print(f"No hay datos para guardar en {nombre_archivo}")
            return False
        
        # Creamos el archivo CSV
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as archivo:
            writer = csv.DictWriter(archivo, fieldnames=campos)
            writer.writeheader()
            writer.writerows(datos)
            
        print(f"Se ha guardado la información en {nombre_archivo}")
        return True
        
    except Exception as e:
        print(f"Error al guardar el archivo CSV {nombre_archivo}: {e}")
        return False

def generar_analisis(legisladores):
    """Genera un análisis básico de los datos de legisladores"""
    try:
        # Convertimos a DataFrame para análisis
        df = pd.DataFrame(legisladores)
        
        # Análisis por bloque
        analisis_bloques = df['bloque'].value_counts().reset_index()
        analisis_bloques.columns = ['Bloque', 'Cantidad']
        
        # Análisis por periodo de mandato
        df['anio_inicio'] = df['mandato_inicio'].str.extract(r'(\d{4})').astype(float)
        analisis_periodos = df['anio_inicio'].value_counts().reset_index()
        analisis_periodos.columns = ['Año de inicio', 'Cantidad']
        analisis_periodos = analisis_periodos.sort_values('Año de inicio')
        
        # Guardamos los análisis
        analisis_bloques.to_csv('analisis_bloques.csv', index=False, encoding='utf-8')
        analisis_periodos.to_csv('analisis_periodos.csv', index=False, encoding='utf-8')
        
        print("Análisis generado correctamente")
        return True
        
    except Exception as e:
        print(f"Error al generar análisis: {e}")
        return False

def main():
    # Definimos los archivos CSV
    archivo_legisladores = 'legisladores.csv'
    
    # Verificamos si es primera ejecución o actualización
    es_primera_ejecucion = not os.path.exists(archivo_legisladores)
    
    # Obtiene la información de los legisladores
    nuevos_legisladores = obtener_legisladores()
    
    if nuevos_legisladores:
        # Si existen legisladores previos, los cargamos
        legisladores_existentes = cargar_legisladores_existentes(archivo_legisladores)
        
        # Si es primera ejecución o queremos detalles completos
        if es_primera_ejecucion or os.environ.get('OBTENER_DETALLES', 'false').lower() == 'true':
            print("Obteniendo detalles de cada legislador...")
            for legislador in nuevos_legisladores:
                if legislador['perfil_url']:
                    detalles = obtener_detalles_legislador(
                        legislador['perfil_url'], 
                        legislador['nombre']
                    )
                    # Actualizamos el diccionario con los detalles obtenidos
                    legislador.update(detalles)
        
        # Combinamos los legisladores existentes con los nuevos
        todos_legisladores = combinar_legisladores(legisladores_existentes, nuevos_legisladores)
        
        # Definimos los campos para el CSV
        campos = ['nombre', 'perfil_url', 'imagen_url', 'bloque', 'bloque_url', 
                 'mandato_inicio', 'mandato_fin', 'fecha_extraccion', 
                 'email', 'telefono', 'comisiones']
        
        # Guardamos todos los legisladores en un archivo CSV
        guardar_csv(todos_legisladores, archivo_legisladores, campos)
        
        # Generamos análisis de los datos
        generar_analisis(todos_legisladores)

if __name__ == '__main__':
    main()