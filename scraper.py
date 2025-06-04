import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import os
import random
import re

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

def obtener_integrantes_comision(codigo_comision, nombre_comision):
    """Obtiene los integrantes de una comisión específica"""
    # Construimos la URL para los integrantes de la comisión
    url_integrantes = f"https://www.hcdn.gob.ar/comisiones/permanentes/{codigo_comision}/integrantes.html"
    
    try:
        print(f"Obteniendo integrantes de {nombre_comision}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url_integrantes, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al obtener integrantes de {nombre_comision}: {response.status_code}")
            return []
        
        # Añadimos una pausa para evitar sobrecargar el servidor
        time.sleep(random.uniform(1.5, 4))  # Pausa aleatoria entre 1.5 y 4 segundos
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos la tabla de integrantes
        tabla = soup.find('table', id='tablaintegrantes')
        
        # Si no encontramos por ID, buscamos por clase
        if not tabla:
            tabla = soup.find('table', class_='tablaIntegrantes')
        
        # Si aún no encontramos, buscamos cualquier tabla con información de diputados
        if not tabla:
            tablas = soup.find_all('table')
            for t in tablas:
                if t.find(string=re.compile('diputado|Diputado|cargo|Cargo', re.IGNORECASE)):
                    tabla = t
                    break
        
        if not tabla:
            print(f"No se encontró la tabla de integrantes para {nombre_comision}")
            return []
        
        integrantes = []
        
        # Buscamos el tbody o usamos directamente las filas de la tabla
        tbody = tabla.find('tbody')
        if tbody:
            filas = tbody.find_all('tr')
        else:
            filas = tabla.find_all('tr')
        
        # Iteramos por cada fila, saltando encabezados
        for fila in filas:
            # Saltamos filas de encabezado
            if fila.find('th'):
                continue
                
            celdas = fila.find_all('td')
            
            # Verificamos que haya suficientes celdas
            if len(celdas) < 4:  # Mínimo necesario: imagen, cargo, nombre, bloque
                continue
            
            # Extraer cargo
            cargo = celdas[1].text.strip()
            
            # Extraer nombre y URL del perfil
            nombre_cell = celdas[2]
            link_diputado = nombre_cell.find('a')
            
            if link_diputado:
                nombre_completo = link_diputado.text.strip()
                codigo_diputado = link_diputado['href'].split('/')[-1] if '/' in link_diputado['href'] else None
            else:
                nombre_completo = nombre_cell.text.strip()
                codigo_diputado = None
            
            # Extraer bloque político
            bloque = celdas[3].text.strip()
            
            # Extraer distrito (si existe)
            distrito = celdas[4].text.strip() if len(celdas) > 4 else None
            
            # Crear diccionario con la información del integrante
            integrante = {
                'comision_codigo': codigo_comision,
                'comision_nombre': nombre_comision,
                'codigo_diputado': codigo_diputado,
                'nombre_completo': nombre_completo,
                'cargo': cargo,
                'bloque': bloque,
                'distrito': distrito,
                'fecha_extraccion': datetime.now().strftime("%Y-%m-%d")
            }
            
            integrantes.append(integrante)
        
        print(f"Se encontraron {len(integrantes)} integrantes en {nombre_comision}")
        return integrantes
        
    except Exception as e:
        print(f"Error al obtener integrantes de {nombre_comision}: {e}")
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

def cargar_integrantes_existentes(nombre_archivo):
    """Carga los integrantes existentes desde un archivo CSV"""
    integrantes = []
    
    if not os.path.exists(nombre_archivo):
        return integrantes
        
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            reader = csv.DictReader(archivo)
            for fila in reader:
                integrantes.append(fila)
                
        print(f"Se cargaron {len(integrantes)} registros de integrantes desde {nombre_archivo}")
        return integrantes
        
    except Exception as e:
        print(f"Error al cargar integrantes desde {nombre_archivo}: {e}")
        return []

def actualizar_integrantes_con_fechas(existentes, nuevos):
    """
    Actualiza los integrantes con fechas de inicio y fin.
    - Si el integrante sigue: actualiza fecha_fin
    - Si el integrante cambió: cierra el anterior y agrega el nuevo
    """
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    # Crear diccionario para búsqueda rápida: clave = comision_codigo + nombre_completo + bloque
    # Esto maneja casos donde hay personas con el mismo nombre en diferentes bloques
    dict_nuevos = {}
    for integrante in nuevos:
        clave = f"{integrante['comision_codigo']}_{integrante['nombre_completo']}_{integrante['bloque']}"
        dict_nuevos[clave] = integrante
    
    # Crear diccionario de existentes por clave similar
    dict_existentes = {}
    for integrante in existentes:
        clave = f"{integrante['comision_codigo']}_{integrante['nombre_completo']}_{integrante['bloque']}"
        dict_existentes[clave] = integrante
    
    resultado = []
    
    # Procesar integrantes existentes
    for clave, existente in dict_existentes.items():
        if clave in dict_nuevos:
            # La misma persona del mismo bloque sigue en la misma comisión
            nuevo = dict_nuevos[clave]
            
            # Actualizar datos que pueden cambiar (cargo puede cambiar, bloque se mantiene en la clave)
            existente['cargo'] = nuevo['cargo']  # El cargo puede haber cambiado
            existente['distrito'] = nuevo['distrito']  # El distrito puede haber cambiado
            existente['fecha_fin'] = fecha_actual  # Actualizar fecha fin
            
            resultado.append(existente)
            
            # Remover de nuevos para no duplicar
            del dict_nuevos[clave]
        else:
            # La persona ya no está en la comisión con ese bloque, cerrar
            if not existente.get('fecha_fin') or existente.get('fecha_fin') == existente.get('fecha_inicio'):
                existente['fecha_fin'] = fecha_actual
            resultado.append(existente)
    
    # Agregar todos los nuevos integrantes que no existían antes
    for clave, nuevo in dict_nuevos.items():
        nuevo['fecha_inicio'] = fecha_actual
        nuevo['fecha_fin'] = fecha_actual
        resultado.append(nuevo)
    
    print(f"Actualización de integrantes: {len(existentes)} existentes, {len(nuevos)} nuevos, {len(resultado)} total final")
    
    return resultado

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

def main():
    # Definimos los archivos CSV
    archivo_comisiones = 'comisiones_diputados.csv'
    archivo_reuniones = 'reuniones_diputados.csv'
    archivo_integrantes = 'integrantes_comisiones.csv'
    
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
        
        # Cargamos los integrantes existentes (si los hay)
        integrantes_existentes = cargar_integrantes_existentes(archivo_integrantes)
        
        # Cargamos las reuniones existentes (si las hay)
        reuniones_existentes = cargar_reuniones_existentes(archivo_reuniones)
        
        # Ahora obtenemos las reuniones e integrantes para cada comisión
        nuevas_reuniones = []
        nuevos_integrantes = []
        
        for comision in comisiones:
            # Obtenemos los integrantes para esta comisión
            integrantes_comision = obtener_integrantes_comision(
                comision['codigo'], 
                comision['nombre']
            )
            
            nuevos_integrantes.extend(integrantes_comision)
            
            # Obtenemos las reuniones para esta comisión
            reuniones_comision = obtener_reuniones_comision(
                comision['codigo'], 
                comision['nombre'],
                anios_a_escanear
            )
            
            nuevas_reuniones.extend(reuniones_comision)
            
            # Mostramos cuántos integrantes y reuniones encontramos
            print(f"Total de integrantes para {comision['nombre']}: {len(integrantes_comision)}")
            print(f"Total de reuniones para {comision['nombre']}: {len(reuniones_comision)}")
        
        # Actualizamos los integrantes con fechas de inicio y fin
        todos_integrantes = actualizar_integrantes_con_fechas(integrantes_existentes, nuevos_integrantes)
        
        # Guardamos todos los integrantes en un archivo CSV
        if todos_integrantes:
            campos_integrantes = ['comision_codigo', 'comision_nombre', 'codigo_diputado', 
                                'nombre_completo', 'cargo', 'bloque', 'distrito', 
                                'fecha_inicio', 'fecha_fin', 'fecha_extraccion']
            guardar_csv(todos_integrantes, archivo_integrantes, campos_integrantes)
        
        # Combinamos las reuniones existentes con las nuevas
        todas_reuniones = combinar_reuniones(reuniones_existentes, nuevas_reuniones)
        
        # Guardamos todas las reuniones en un archivo CSV
        if todas_reuniones:
            campos_reuniones = ['comision_nombre', 'comision_codigo', 'id_reunion', 'fecha', 
                               'anio', 'texto', 'url', 'fecha_extraccion']
            guardar_csv(todas_reuniones, archivo_reuniones, campos_reuniones)

if __name__ == '__main__':
    main()
