const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

const URL_BASE = 'https://www.hcdn.gob.ar/comisiones/permanentes/';

async function obtenerListadoComisiones() {
  const { data } = await axios.get(URL_BASE);
  const $ = cheerio.load(data);
  const enlaces = [];

  $('a').each((i, el) => {
    const href = $(el).attr('href');
    if (href && href.includes('/comisiones/permanentes/') && href.includes('reuniones/listado-partes-anio.html')) {
      const nombre = href.split('/')[3]; // ej: caconstitucionales
      const urlCompleta = new URL(href, URL_BASE).href;
      enlaces.push({ nombre, url: urlCompleta });
    }
  });

  return enlaces;
}

async function obtenerReuniones(comision) {
  const { nombre, url } = comision;
  try {
    const { data } = await axios.get(url);
    const $ = cheerio.load(data);
    const resultados = [];

    $('a').each((i, el) => {
      const href = $(el).attr('href');
      const texto = $(el).text().trim();
      if (href && href.includes('ver-partes')) {
        resultados.push({
          comision: nombre,
          url,
          href: new URL(href, url).href,
          fecha: texto,
        });
      }
    });

    console.log(`→ Encontradas ${resultados.length} reuniones para ${nombre}`);
    return resultados;
  } catch (e) {
    console.warn(`Error accediendo a ${url}`);
    return [];
  }
}

async function main() {
  const comisiones = await obtenerListadoComisiones();
  console.log(`Encontradas ${comisiones.length} comisiones.`);

  const todasLasReuniones = [];

  for (const comision of comisiones) {
    console.log(`Visitando: ${comision.url}`);
    const reuniones = await obtenerReuniones(comision);
    todasLasReuniones.push(...reuniones);
  }

  fs.writeFileSync('reuniones.json', JSON.stringify(todasLasReuniones, null, 2));
  console.log(`Se guardaron ${todasLasReuniones.length} reuniones.`);
}

main();
