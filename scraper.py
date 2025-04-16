import requests
from bs4 import BeautifulSoup

# Base URL donde se encuentran las comisiones
URL_BASE = 'https://www.hcdn.gob.ar/comisiones/permanentes/'

# Función para obtener los enlaces de las comisiones
def obtener_enlaces_comisiones():
    res = requests.get(URL_BASE)
    
    # Imprimir el contenido de la respuesta para depurar
    print(res.text)  # Ver contenido completo de la página
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Buscar todos los enlaces que contienen 'reuniones/listado-partes-anio.html'
    enlaces = []
    for link in soup.find_all('a', href=True):
        if 'reuniones/listado-partes-anio.html' in link['href']:
            enlace_comision = link['href']
            # Extraer el nombre de la comisión desde el enlace
            nombre_comision = enlace_comision.split('/')[2]
            # Guardar los enlaces completos
            enlaces.append((nombre_comision, enlace_comision))
    
    return enlaces

# Función para obtener las reuniones de una comisión específica
def obtener_reuniones_comision(carpeta, anio):
    url = f"https://www.hcdn.gob.ar/comisiones/permanentes/{carpeta}/reuniones/listado-partes.html?year={anio}&carpeta={carpeta}"
    res = requests.get(url)
    
    # Imprimir el contenido de la respuesta para depurar
    print(f"Contenido de {url}:")
    print(res.text)  # Ver contenido de la página de reuniones
    
    soup = BeautifulSoup(res.text, 'html.parser')
    
    reuniones = []
    for item in soup.find_all('a', href=True):
        if 'parte.html?id_reunion' in item['href']:
            fecha = item.text.strip().split("del")[1].strip()
            reuniones.append({'fecha': fecha, 'enlace': item['href']})  # Se cerró el paréntesis aquí
    
    return reuniones

# Función principal para ejecutar el scraper
def main():
    print("Analizando enlaces de comisiones...")
    enlaces_comisiones = obtener_enlaces_comisiones()
    
    if enlaces_comisiones:
        print(f"Encontradas {len(enlaces_comisiones)} comisiones.")
        
        # Ahora obtenemos las reuniones para cada comisión
        for comision, carpeta in enlaces_comisiones:
            print(f"Obteniendo reuniones para la comisión: {comision}")
            reuniones = obtener_reuniones_comision(carpeta, 2025)  # Puedes ajustar el año si lo deseas
            if reuniones:
                print(f"Se encontraron {len(reuniones)} reuniones para la comisión {comision}.")
                for reunion in reuniones:
                    print(f"Fecha: {reunion['fecha']}, Enlace: {reunion['enlace']}")
            else:
                print(f"No se encontraron reuniones para la comisión {comision}.")
    else:
        print("No se encontraron comisiones.")

if __name__ == '__main__':
    main()
