// Requires sharp. Only rasterises original SVG art; product screenshots use capture.cjs.
const fs=require('node:fs');
const sharp=require('sharp');
(async()=>{
 await sharp('docs/assets/brand/hero.svg').resize(1280,640,{fit:'contain',background:'#0b3029'}).png().toFile('docs/assets/brand/social-preview.png');
 const labels=['Python','FastAPI','Kubernetes','SQLite'];
 let contents='<svg xmlns="http://www.w3.org/2000/svg" width="740" height="64" viewBox="0 0 740 64"><rect width="740" height="64" rx="8" fill="#edf4ec"/>';
 for(let i=0;i<labels.length;i++){
  const raw=fs.readFileSync('docs/assets/third-party/'+labels[i].toLowerCase()+'.svg','utf8');
  const paths=raw.match(/<path[^>]+>/g)?.join('')||'';
  contents+='<g transform="translate('+(20+i*180)+',20)" fill="#075745">'+paths+'</g><text x="'+(54+i*180)+'" y="37" font-family="sans-serif" font-size="15" fill="#294d3b">'+labels[i]+'</text>';
 }
 contents+='</svg>';fs.writeFileSync('docs/assets/brand/technology-strip.svg',contents);
})();
