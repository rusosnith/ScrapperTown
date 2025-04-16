const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

// URL de la página principal
const BASE_URL = 'https://www.hcdn.gob.ar/comisiones/permanentes/';

async function main() {
  // 1. Descargar la página principal
  const { data: html } = await axios.get(BASE_URL);
  const $ = cheerio.load(html);

  const links = [];

  // 2. Buscar enlaces a comisiones
  $('a[href*="/comisiones/permanentes/"]').each((i, el) => {
    const href = $(el).attr('href');
    if (href && href.includes('/reuniones/')) {
      links.push(new URL(href, BASE_URL).href);
    }
  });

  console.log(`Encontrados ${links.length} enlaces de reuniones.`);

  const resultados = [];

  // 3. Visitar cada página de reuniones
  for (const url of links) {
    console.log(`Visitando: ${url}`);
    try {
      const { data: html } = await axios.get(url);
      const $ = cheerio.load(html);

      // 4. Buscar fechas (esto depende del HTML, puede variar)
      $('a[href*="ver-partes"]').each((i, el) => {
        const texto = $(el).text().trim();
        resultados.push({
          url,
          fecha: texto,
        });
      });
    } catch (err) {
      console.warn(`Error con ${url}: ${err.message}`);
    }
  }

  // 5. Guardar resultados
  fs.writeFileSync('reuniones.json', JSON.stringify(resultados, null, 2));
  console.log(`Se guardaron ${resultados.length} reuniones.`);
}

main();
