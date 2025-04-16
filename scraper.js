const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

const BASE_URL = 'https://www.hcdn.gob.ar/comisiones/permanentes/';

async function main() {
  const { data: html } = await axios.get(BASE_URL);
  const $ = cheerio.load(html);

  const comisiones = [];

  $('a[href*="/comisiones/permanentes/"]').each((i, el) => {
    const href = $(el).attr('href');
    const nombre = $(el).text().trim();
    if (href && /^\/comisiones\/permanentes\/[^\/]+$/.test(href)) {
      const urlBase = new URL(href, BASE_URL).href;
      const reunionesUrl = urlBase + '/reuniones/listado-partes-anio.html';
      comisiones.push({ nombre, url: reunionesUrl });
    }
  });

  console.log(`Encontradas ${comisiones.length} comisiones.`);

  const resultados = [];

  for (const { nombre, url } of comisiones) {
    console.log(`Visitando: ${url}`);
    try {
      const { data: html } = await axios.get(url);
      const $ = cheerio.load(html);

      $('a[href*="ver-partes"]').each((i, el) => {
        const texto = $(el).text().trim();
        resultados.push({
          comision: nombre,
          url,
          fecha: texto,
        });
      });
    } catch (err) {
      console.warn(`Error con ${url}: ${err.message}`);
    }
  }

  fs.writeFileSync('reuniones.json', JSON.stringify(resultados, null, 2));
  console.log(`Se guardaron ${resultados.length} reuniones.`);
}

main();
