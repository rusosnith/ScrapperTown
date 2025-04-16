import requests
from bs4 import BeautifulSoup

# Base URL donde se encuentran las comisiones
URL_BASE = 'https://www.hcdn.gob.ar/comisiones/permanentes/'

# Función para obtener los enlaces de las comisiones
def obtener_enlaces_comisiones():
    res = requests.get(URL_BASE)
    
    # Verificar si la solicitud fue exitosa
    if res.status_code != 200:
        print(f"Error al obtener página: {res.status_code}")
        return []
        
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Buscar todos los enlaces que contienen 'reuniones/listado-partes-anio.html'
    enlaces = []
    for link in soup.find_all('a', href=True):
        if 'reuniones/listado-partes-anio.html' in link['href']:
            enlace_comision = link['href']
            # Extraer el nombre de la comisión desde el enlace
            # Las URLs suelen tener un formato como /comisiones/permanentes/nombre_comision/...
            partes = enlace_comision.split('/')
            # Asegurarse que hay suficientes partes en la URL para extraer el nombre
            if len(partes) > 3:
                nombre_comision = partes[3]  # Ajustado el índice para capturar el nombre correcto
                enlaces.append((nombre_comision, enlace_comision))
    
    return enlaces

# Función para obtener las reuniones de una comisión específica
def obtener_reuniones_comision(nombre_comision, anio):
    url = f"https://www.hcdn.gob.ar/comisiones/permanentes/{nombre_comision}/reuniones/listado-partes.html?year={anio}&carpeta={nombre_comision}"
    res = requests.get(url)
    
    if res.status_code != 200:
        print(f"Error al obtener reuniones: {res.status_code}")
        return []
    
    soup = BeautifulSoup(res.text, 'html.parser')
    
    reuniones = []
    for item in soup.find_all('a', href=True):
        if 'parte.html?id_reunion' in item['href']:
            # Intentar extraer la fecha considerando diferentes formatos
            texto = item.text.strip()
            if "del" in texto:
                fecha = texto.split("del")[1].strip()
            else:
                fecha = texto  # Si no sigue el formato esperado, guardar el texto completo
            
            reuniones.append({'fecha': fecha, 'enlace': item['href']})
    
    return reuniones

# Función principal para ejecutar el scraper
def main():
    print("Analizando enlaces de comisiones...")
    enlaces_comisiones = obtener_enlaces_comisiones()
    
    if enlaces_comisiones:
        print(f"Encontradas {len(enlaces_comisiones)} comisiones.")
        
        # Ahora obtenemos las reuniones para cada comisión
        for nombre_comision, enlace in enlaces_comisiones:
            print(f"Obteniendo reuniones para la comisión: {nombre_comision}")
            reuniones = obtener_reuniones_comision(nombre_comision, 2025)
            if reuniones:
                print(f"Se encontraron {len(reuniones)} reuniones para la comisión {nombre_comision}.")
                for reunion in reuniones:
                    print(f"Fecha: {reunion['fecha']}, Enlace: {reunion['enlace']}")
            else:
                print(f"No se encontraron reuniones para la comisión {nombre_comision}.")
    else:
        print("No se encontraron comisiones.")

if __name__ == '__main__':
    main()