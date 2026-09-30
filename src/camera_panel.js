// Camera position inventory and explicitly hypothetical proximity, never visibility.
const CAMERAS=DATA.cameras;
let cameraMarkers=null,cameraCircles=null;
const cameraCellCounts=new Map();
const cameraFeatureKeys=new WeakMap();
function cameraGridKey(g){return g.join(',');}
// Grid keys are supplied by preparation, avoiding a browser projection dependency.
function crimeCellKey(f){return cameraGridKey(cameraFeatureKeys.get(f));}
function cameraPositionsForCell(f){return cameraCellCounts.get(crimeCellKey(f))||0;}
function updateCameraLayers(){
 if(!CAMERAS)return;
 if(cameraMarkers)map.removeLayer(cameraMarkers);
 if(cameraCircles)map.removeLayer(cameraCircles);
 const enabled=document.getElementById('camera-toggle').checked&&currentView==='crime';
 const radius=Number(document.getElementById('camera-radius').value);
 document.getElementById('camera-radius-label').textContent=radius+' m';
 if(!enabled)return;
 cameraCircles=L.layerGroup();cameraMarkers=L.layerGroup();
 let pairs=0;const overlapping=new Set();
 for(let i=0;i<CAMERAS.positions.length;i++){
  const p=CAMERAS.positions[i];
  for(let j=0;j<i;j++){const q=CAMERAS.positions[j];if(Math.hypot(p.x-q.x,p.y-q.y)<2*radius){pairs++;overlapping.add(i);overlapping.add(j);}}
  const labels=[...new Set(p.records.map(r=>r.label))];
  L.circleMarker([p.lat,p.lon],{radius:5,color:'#fff',weight:1,fillColor:'#087f83',fillOpacity:1}).bindPopup('<b>'+escapeText(labels.slice(0,4).join(' / '))+'</b><br>'+fmt(p.records.length)+' source records at this position<br>Coverage and operating dates: unknown<br>Source: Bristol City Council').addTo(cameraMarkers);
  if(document.getElementById('camera-proximity').checked)L.circle([p.lat,p.lon],{radius,color:'#387da7',weight:1,fillOpacity:.025,interactive:false}).addTo(cameraCircles);
 }
 cameraCircles.addTo(map);cameraMarkers.addTo(map);
 const affected=DATA.geojson.features.filter(f=>cameraPositionsForCell(f)>0);
 const records=affected.reduce((sum,f)=>sum+value(f),0);
 document.getElementById('camera-stats').textContent=fmt(affected.length)+' occupied crime cells contain a listed position; '+fmt(records)+' July records in the selected category across those entire cells. This is cell co-location, not incidents captured.';
 document.getElementById('camera-overlap').textContent=document.getElementById('camera-proximity').checked?fmt(pairs)+' pairs of distinct positions have overlapping '+radius+' m scenario circles; '+fmt(overlapping.size)+' positions participate. This does not measure actual viewing overlap.':'Actual viewing overlap is unknown. Enable scenario circles to explore distance assumptions.';
}
if(CAMERAS){
 document.getElementById('camera-controls').hidden=false;
 const cm=CAMERAS.metadata;
 DATA.geojson.features.forEach((f,i)=>cameraFeatureKeys.set(f,DATA.camera_grid_keys[i]));
 for(const p of CAMERAS.positions){const k=cameraGridKey(p.grid);cameraCellCounts.set(k,(cameraCellCounts.get(k)||0)+1);}
 document.getElementById('camera-receipt').textContent=fmt(cm.distinct_positions)+' distinct positions · '+fmt(cm.source_record_count)+' source records. Retrieved '+cm.retrieved_at.slice(0,10)+'. Includes some South Gloucestershire positions; this is not a complete camera census.';
 document.getElementById('camera-source').href=cm.source_page;
 document.getElementById('camera-focus').addEventListener('click',()=>{if(currentView!=='crime')switchView('crime');document.getElementById('camera-toggle').checked=true;updateCameraLayers();map.fitBounds(L.latLngBounds(CAMERAS.positions.map(p=>[p.lat,p.lon])),{padding:[25,25]});});
 for(const id of ['camera-toggle','camera-proximity','camera-radius'])document.getElementById(id).addEventListener('input',updateCameraLayers);
 selector.addEventListener('change',updateCameraLayers);
 for(const id of ['court-view','crime-view'])document.getElementById(id).addEventListener('click',updateCameraLayers);
 map.attributionControl.addAttribution('CCTV positions: Bristol City Council / OS 2026');
 const crimeRender=render;
 render=function(){crimeRender();for(const l of layer.getLayers()){const n=cameraPositionsForCell(l.feature);l.setPopupContent(l.getPopup().getContent()+'<hr><b>CCTV position inventory</b><br>'+fmt(n)+' listed distinct positions in this '+(meta.cell_m/1000)+' km cell.<br>'+(n?'Actual viewing coverage: unknown.':'No positions listed in this source; camera presence unknown.'));}updateCameraLayers();};
 render();
}
