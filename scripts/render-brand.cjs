// Uses the supplied VERIQTA artwork verbatim; SVG viewports trim blank margins.
// Product screenshots must be captured from the running app with capture.cjs.
const fs=require('node:fs');
const sharp=require('sharp');
(async()=>{
 const source='docs/assets/brand/veriqta-supplied.png';
 const raster=await sharp(source).resize({width:640,withoutEnlargement:true}).png().toBuffer();
 const image='<image width="1254" height="1254" href="data:image/png;base64,'+raster.toString('base64')+'"/>';
 const logo=(x,y,width,height)=>'<svg x="'+x+'" y="'+y+'" width="'+width+'" height="'+height+'" viewBox="150 310 955 650" preserveAspectRatio="xMidYMid meet">'+image+'</svg>';
 const standalone='<svg xmlns="http://www.w3.org/2000/svg" width="955" height="650" viewBox="150 310 955 650"><title>VERIQTA supplied logo</title>'+image+'</svg>';
 fs.writeFileSync('docs/assets/brand/veriqta-logo.svg',standalone);
 await sharp(Buffer.from(standalone)).resize({width:320}).png().toFile('src/kubeinvestigator/static/veriqta-logo.png');
 for(const theme of ['light','dark']){
  const background=theme==='light'?'#fafbf7':'#0b3029';
  const foreground=theme==='light'?'#075745':'#c0e4cf';
  const badge='<svg xmlns="http://www.w3.org/2000/svg" width="700" height="180" viewBox="0 0 700 180"><rect width="700" height="180" rx="16" fill="'+background+'"/>'+logo(25,23,190,134)+'<text x="245" y="103" fill="'+foreground+'" font-family="sans-serif" font-size="32">KubeInvestigator</text></svg>';
  fs.writeFileSync('docs/assets/brand/project-'+theme+'.svg',badge);
 }
 let hero=fs.readFileSync('docs/assets/brand/hero.svg','utf8');
 // Retain the original banner text/layout; replace only its approximate mark.
 hero=hero.replace(/<path d="M945[\s\S]*?(?=<text)/,logo(935,72,285,194));
 // Subsequent regeneration uses the same deterministic supplied-art placement.
 hero=hero.replace(/<svg x="935"[\s\S]*?<\/svg>/,logo(935,72,285,194));
 fs.writeFileSync('docs/assets/brand/hero.svg',hero);
 await sharp(Buffer.from(hero)).png().toFile('docs/assets/brand/hero.png');
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
