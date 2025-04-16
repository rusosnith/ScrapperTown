import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin

URL_BASE = 'https://www.hcdn.gob.ar/comisiones/permanentes/'

def obtener_enlaces_comisiones():
    res = requests.get(URL_BASE)
    soup = BeautifulSoup(res.text, 'html.parser')
    enlaces = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'reuniones/listado-partes-anio.html' in href:
            nombre = href.strip('/').split('/')[2]
            url = urljoin(URL_BASE, href)
            enlaces.append((nombre, url))
    return enlaces

def obtener_reuniones(url_comision):
    res = requests.get(url_comision)
    soup = BeautifulSoup(res.text, 'html.parser')
    reuniones = []
    for li in soup.select('ul li a[href*=".pdf"]'):
        texto = li.get_text(strip=True)
        link = urljoin(url_comision, li['href'])
        reuniones.append((texto, link))
    return reuniones

def main():
    comisiones = obtener_enlaces_comisiones()
    print(f"Encontradas {len(comisiones)} comisiones.")
    total = 0
    with open('reuniones.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['comision', 'descripcion', 'url'])
        for nombre, url in comisiones:
            print(f"Visitando: {url}")
            reuniones = obtener_reuniones(url)
            for desc, link in reuniones:
                writer.writerow([nombre, desc, link])
            total += len(reuniones)
    print(f"Se guardaron {total} reuniones.")

if __name__ == '__main__':
    main()
