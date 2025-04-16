import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import os
import random

# URL base
URL_BASE = 'https://www.hcdn.gob.ar/comisiones/permanentes/'

def obtener_comisiones():
    """Extrae la información de las comisiones desde la página principal"""
    try:
        # Hacemos la solicitud HTTP
        print("Obteniendo información de comisiones...")
        response = requests.get(URL_BASE)
        
        if response.status_code != 200:
            print(f"Error al obtener la página: {response.status_code}")
            return []
        
        # Añadimos una pausa para evitar sobrecargar el servidor
        time.sleep(random.uniform(1, 3))  # Pausa aleatoria entre 1 y 3 segundos
            
        # Parseamos el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontramos la tabla de comisiones
        tabla = soup.find('table', class_='table-responsive')
        
        if not tabla:
            print("No se encontró la tabla de comisiones en el HTML")
            return []
        
        comisiones = []
        
        # Iteramos por cada fila de la tabla, saltando la cabecera
        for fila in tabla.find('tbody').find_all('tr'):
            celdas = fila.find_all('td')
            
            # Extraemos los datos de cada celda
            orden = celdas[0].text.strip()
            
            # Extraemos el nombre y la URL de la comisión
            link_comision = celdas[1].find('a')
            nombre = link_comision.text.strip()
            url_comision = f"https://www.hcdn.gob.ar{link_comision['href']}"
            codigo_comision = link_comision['href'].split('/')[-1]
            
            tipo = celdas[2].text.strip()
            horario = celdas[3].text.strip()
            secretario = celdas[4].text.strip()
            
            # La última celda contiene información de contacto
            sede_contacto = celdas[5].text.strip().replace('\n', ' ').replace('\t', ' ')
            while '  ' in sede_contacto:
                sede_contacto = sede_contacto.replace('  ', ' ')
            
            # Creamos un diccionario con la información
            comision = {
                'orden': orden,
                'nombre': nombre,
                'codigo': codigo_comision,
                'url': url_comision,
                'tipo': tipo,
                'horario': horario,
                'secretario': secretario,
                'sede_contacto': sede_contacto,
                'fecha_extraccion': datetime.now().strftime("%Y-%m-%d")
            }
            
            comisiones.append(comision)
            
        print(f"Se encontraron {len(comisiones)} comisiones")
        return comisiones
        
    except Exception as e:
        print(f"Error al obtener las comisiones: {e}")
        return []

def obtener_reuniones_comision(codigo_comision, nombre_comision, anios):
    """Obtiene todas las reuniones de una comisión para los años especificados"""
    todas_reuniones = []
    
    for anio in anios:
        # Construimos la URL para las reuniones del año
        url = f"https://www.hcdn.gob.ar/comisiones/permanentes/{codigo_comision}/reuniones/listado-partes.html?year={anio}&carpeta={codigo_comision}"
        
        try:
            print(f"Obteniendo reuniones de {nombre_comision} para el año {anio}...")
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"Error al obtener la página de reuniones: {response.status_code}")
                continue
            
            # Añadimos una pausa para evitar sobrecargar el servidor
            time.sleep(random.uniform(1.5, 4))  # Pausa aleatoria entre 1.5 y 4 segundos
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos la sección de partes
            seccion_partes = soup.find('section', class_='partes')
            if not seccion_partes:
                print(f"No se encontró la sección de partes para {nombre_comision} en {anio}")
                continue
                
            # Buscamos todos los enlaces a partes de reuniones
            enlaces = seccion_partes.find_all('a', href=True)
            
            for enlace in enlaces:
                if 'parte.html?id_reunion=' in enlace['href']:
                    # Extraemos la información del enlace
                    texto = enlace.text.strip()
                    url_parte = f"https://www.hcdn.gob.ar/comisiones/permanentes/{codigo_comision}/reuniones/{enlace['href']}"
                    
                    # Extraemos el ID de la reunión y la fecha
                    id_reunion = enlace['href'].split('id_reunion=')[1].split('&')[0]
                    fecha = enlace['href'].split('fecha=')[1] if 'fecha=' in enlace['href'] else None
                    
                    # Si no pudimos extraer la fecha del parámetro, intentamos extraerla del texto
                    if not fecha and 'del ' in texto:
                        fecha = texto.split('del ')[1].strip()
                    
                    # Creamos un diccionario con la información de la reunión
                    reunion = {
                        'comision_nombre': nombre_comision,
                        'comision_codigo': codigo_comision,
                        'id_reunion': id_reunion,
                        'fecha': fecha,
                        'anio': anio,
                        'texto': texto,
                        'url': url_parte,
                        'fecha_extraccion': datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    todas_reuniones.append(reunion)
            
            print(f"Se encontraron {len(enlaces)} enlaces para {nombre_comision} en {anio}")
            
        except Exception as e:
            print(f"Error al obtener reuniones de {nombre_comision} para {anio}: {e}")
    
    return todas_reuniones

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

def cargar_reuniones_existentes(nombre_archivo):
    """Carga las reuniones existentes desde un archivo CSV"""
    reuniones = []
    
    if not os.path.exists(nombre_archivo):
        return reuniones
        
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            reader = csv.DictReader(archivo)
            for fila in reader:
                reuniones.append(fila)
                
        print(f"Se cargaron {len(reuniones)} reuniones existentes desde {nombre_archivo}")
        return reuniones
        
    except Exception as e:
        print(f"Error al cargar reuniones desde {nombre_archivo}: {e}")
        return []

def combinar_reuniones(reuniones_existentes, nuevas_reuniones):
    """Combina las reuniones existentes con las nuevas, evitando duplicados"""
    # Creamos un conjunto con los IDs de las reuniones existentes
    ids_existentes = set()
    for reunion in reuniones_existentes:
        id_clave = f"{reunion['comision_codigo']}_{reunion['id_reunion']}"
        ids_existentes.add(id_clave)
    
    # Filtramos las nuevas reuniones para excluir las que ya existen
    reuniones_unicas = []
    for reunion in nuevas_reuniones:
        id_clave = f"{reunion['comision_codigo']}_{reunion['id_reunion']}"
        if id_clave not in ids_existentes:
            reuniones_unicas.append(reunion)
            ids_existentes.add(id_clave)  # Añadimos a existentes para no duplicar
    
    # Combinamos las existentes con las nuevas únicas
    todas_reuniones = reuniones_existentes + reuniones_unicas
    
    print(f"Se encontraron {len(reuniones_unicas)} nuevas reuniones únicas")
    print(f"Total de reuniones después de combinar: {len(todas_reuniones)}")
    
    return todas_reuniones

def main():
    # Definimos los archivos CSV
    archivo_comisiones = 'comisiones_diputados.csv'
    archivo_reuniones = 'reuniones_diputados.csv'
    
    # Verificamos si es primera ejecución o actualización
    es_primera_ejecucion = not (os.path.exists(archivo_comisiones) and os.path.exists(archivo_reuniones))
    
    # Definimos los años a escanear
    anio_actual = datetime.now().year
    if es_primera_ejecucion:
        anios_a_escanear = list(range(2017, anio_actual + 1))
        print(f"Primera ejecución detectada: escaneando años 2017-{anio_actual}")
    else:
        anios_a_escanear = [anio_actual]
        print(f"Actualización detectada: escaneando solo el año actual ({anio_actual})")
    
    # Obtiene la información de las comisiones
    comisiones = obtener_comisiones()
    
    # Guarda la información de comisiones en un archivo CSV
    if comisiones:
        campos_comisiones = ['orden', 'nombre', 'codigo', 'url', 'tipo', 'horario', 
                            'secretario', 'sede_contacto', 'fecha_extraccion']
        guardar_csv(comisiones, archivo_comisiones, campos_comisiones)
        
        # Cargamos las reuniones existentes (si las hay)
        reuniones_existentes = cargar_reuniones_existentes(archivo_reuniones)
        
        # Ahora obtenemos las reuniones para cada comisión
        nuevas_reuniones = []
        
        for comision in comisiones:
            # Obtenemos las reuniones para esta comisión
            reuniones_comision = obtener_reuniones_comision(
                comision['codigo'], 
                comision['nombre'],
                anios_a_escanear
            )
            
            nuevas_reuniones.extend(reuniones_comision)
            
            # Mostramos cuántas reuniones encontramos
            print(f"Total de reuniones para {comision['nombre']}: {len(reuniones_comision)}")
        
        # Combinamos las reuniones existentes con las nuevas
        todas_reuniones = combinar_reuniones(reuniones_existentes, nuevas_reuniones)
        
        # Guardamos todas las reuniones en un archivo CSV
        if todas_reuniones:
            campos_reuniones = ['comision_nombre', 'comision_codigo', 'id_reunion', 'fecha', 
                               'anio', 'texto', 'url', 'fecha_extraccion']
            guardar_csv(todas_reuniones, archivo_reuniones, campos_reuniones)

if __name__ == '__main__':
    main()