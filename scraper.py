import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

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

def guardar_csv(comisiones, nombre_archivo='comisiones_diputados.csv'):
    """Guarda la información de las comisiones en un archivo CSV"""
    try:
        if not comisiones:
            print("No hay comisiones para guardar")
            return False
            
        # Definimos los campos que queremos guardar
        campos = ['orden', 'nombre', 'codigo', 'url', 'tipo', 'horario', 
                  'secretario', 'sede_contacto', 'fecha_extraccion']
        
        # Creamos el archivo CSV
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as archivo:
            writer = csv.DictWriter(archivo, fieldnames=campos)
            writer.writeheader()
            writer.writerows(comisiones)
            
        print(f"Se ha guardado la información en {nombre_archivo}")
        return True
        
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")
        return False

def main():
    # Obtiene la información de las comisiones
    comisiones = obtener_comisiones()
    
    # Guarda la información en un archivo CSV
    if comisiones:
        guardar_csv(comisiones)
        
        # Mostrar algunos ejemplos de los datos extraídos
        print("\nEjemplos de comisiones extraídas:")
        for i in range(min(5, len(comisiones))):
            print(f"{i+1}. {comisiones[i]['nombre']} - {comisiones[i]['url']}")

if __name__ == '__main__':
    main()