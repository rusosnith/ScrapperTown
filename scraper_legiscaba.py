import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import os
import random
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# URL base
URL_BASE = 'https://legislatura.gob.ar/seccion/composicion-actual.html'

def obtener_legisladores():
    """Extrae la información de los legisladores usando Selenium para renderizar JavaScript"""
    try:
        print("Iniciando navegador para obtener información de legisladores...")
        
        # Configurar opciones de Chrome para GitHub Actions
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Ejecutar sin interfaz gráfica
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Crear el driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            print("Navegando a la página...")
            driver.get(URL_BASE)
            
            # Esperar a que la tabla se cargue completamente
            print("Esperando a que la tabla se cargue...")
            wait = WebDriverWait(driver, 20)
            
            # Esperar a que aparezca la tabla
            table = wait.until(EC.presence_of_element_located((By.ID, "data-integrantes")))
            
            # Esperar un poco más para que se carguen las filas
            time.sleep(5)
            
            # Intentar esperar a que aparezcan las filas
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#data-integrantes tbody tr")))
            except:
                print("Las filas no se cargaron en el tiempo esperado, continuando...")
            
            # Obtener el HTML renderizado
            html = driver.page_source
            
            # Guardar HTML para depuración
            with open('debug_pagina_selenium.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            print("HTML obtenido, procesando datos...")
            
        finally:
            driver.quit()
        
        # Ahora procesar el HTML con BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Encontrar la tabla
        table = soup.find('table', id='data-integrantes')
        
        if not table:
            print("No se encontró la tabla en el HTML renderizado")
            return []
        
        print(f"Tabla encontrada: ID={table.get('id')}")
        
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
        for i, row in enumerate(rows):
            # Detectamos si es una fila de encabezado
            if row.find('th'):
                print(f"Fila {i}: Es encabezado, saltando...")
                continue
                
            cells = row.find_all('td')
            
            # Verificamos que haya suficientes celdas
            if len(cells) < 5:
                print(f"Fila {i}: Número insuficiente de celdas: {len(cells)}")
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
            print(f"Legislador {i}: {legislator_name}, Bloque: {bloc_name}")
            
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
                # Convertir 'activo' de string a booleano
                if 'activo' in fila:
                    fila['activo'] = fila['activo'].lower() == 'true'
                legisladores.append(fila)
                
        print(f"Se cargaron {len(legisladores)} registros de legisladores desde {nombre_archivo}")
        return legisladores
        
    except Exception as e:
        print(f"Error al cargar legisladores desde {nombre_archivo}: {e}")
        return []

def combinar_legisladores_historicos(existentes, nuevos):
    """
    Combina los legisladores existentes con los nuevos, manteniendo un registro histórico.
    Si un legislador existente ya no está en la lista actual, se marca como inactivo.
    """
    # Convertir a dict para búsqueda rápida
    dict_nuevos = {leg['nombre']: leg for leg in nuevos}
    
    # Lista para el resultado combinado
    combinados = []
    
    # Contadores para estadísticas
    actualizados = 0
    inactivados = 0
    nuevos_agregados = 0
    
    # Fecha actual para marcar cuando un legislador deja de estar activo
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    # Primero procesamos los existentes
    for existente in existentes:
        nombre = existente['nombre']
        
        # Si el legislador sigue activo en la nueva lista
        if nombre in dict_nuevos:
            # Actualizar datos que pueden cambiar
            existente['bloque'] = dict_nuevos[nombre]['bloque']
            existente['bloque_url'] = dict_nuevos[nombre]['bloque_url']
            existente['imagen_url'] = dict_nuevos[nombre]['imagen_url']
            existente['fecha_extraccion'] = dict_nuevos[nombre]['fecha_extraccion']
            existente['activo'] = True
            
            # Eliminar de nuevos para no duplicar
            del dict_nuevos[nombre]
            
            actualizados += 1
        elif existente.get('activo', True):
            # Si era activo y ya no está en la lista, lo marcamos como inactivo
            existente['activo'] = False
            existente['fecha_baja'] = fecha_actual
            inactivados += 1
        
        combinados.append(existente)
    
    # Ahora agregamos los nuevos que no existían antes
    for nombre, nuevo in dict_nuevos.items():
        nuevo['activo'] = True
        nuevo['fecha_alta'] = fecha_actual
        combinados.append(nuevo)
        nuevos_agregados += 1
    
    print(f"Actualización histórica: {actualizados} actualizados, {inactivados} inactivados, {nuevos_agregados} nuevos")
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
    """Genera análisis de los datos de legisladores"""
    try:
        # Convertimos a DataFrame para análisis
        df = pd.DataFrame(legisladores)
        
        # Filtrar legisladores activos para el análisis actual
        df_activos = df[df['activo'] == True]
        
        # Análisis por bloque (legisladores activos)
        analisis_bloques = df_activos['bloque'].value_counts().reset_index()
        analisis_bloques.columns = ['Bloque', 'Cantidad']
        
        # Análisis histórico de cambios
        if 'fecha_alta' in df.columns and 'fecha_baja' in df.columns:
            # Preparar datos para análisis temporal
            df['fecha_alta'] = pd.to_datetime(df['fecha_alta'], errors='coerce')
            df['fecha_baja'] = pd.to_datetime(df['fecha_baja'], errors='coerce')
            
            # Análisis de rotación por mes
            df_rotacion = df.groupby(pd.Grouper(key='fecha_alta', freq='M')).size().reset_index()
            df_rotacion.columns = ['Mes', 'Nuevos_Legisladores']
            
            # Guardar análisis temporal
            df_rotacion.to_csv('analisis_rotacion_mensual.csv', index=False, encoding='utf-8')
        
        # Análisis por periodo de mandato
        df_activos['anio_inicio'] = df_activos['mandato_inicio'].str.extract(r'(\d{4})').astype(float)
        analisis_periodos = df_activos['anio_inicio'].value_counts().reset_index()
        analisis_periodos.columns = ['Año de inicio', 'Cantidad']
        analisis_periodos = analisis_periodos.sort_values('Año de inicio')
        
        # Guardamos los análisis
        analisis_bloques.to_csv('analisis_bloques_actuales.csv', index=False, encoding='utf-8')
        analisis_periodos.to_csv('analisis_periodos_actuales.csv', index=False, encoding='utf-8')
        
        # Análisis histórico total
        historial_bloques = df.groupby(['bloque', 'activo']).size().reset_index()
        historial_bloques.columns = ['Bloque', 'Activo', 'Cantidad']
        historial_bloques.to_csv('historial_bloques.csv', index=False, encoding='utf-8')
        
        print("Análisis generados correctamente")
        return True
        
    except Exception as e:
        print(f"Error al generar análisis: {e}")
        return False

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
