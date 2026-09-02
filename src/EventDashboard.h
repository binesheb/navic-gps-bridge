#pragma once
#include <Arduino.h>

// Reusable dashboard fragment for the runtime event-history API.
// Kept separate from main.cpp so the UI can later be served from an embedded
// asset or included directly in the existing page without duplicating logic.
inline String eventDashboardHtml() {
  return R"HTML(
<div class="card" id="event-card">
  <b>Event history</b>
  <small id="event-summary" aria-live="polite">Loading…</small>
  <div id="event-list" style="margin-top:10px"></div>
  <button type="button" onclick="clearEvents()">Clear retained history</button>
</div>
<div class="card" id="geofence-card">
  <b>Geofence status</b>
  <div class="grid" style="margin-top:10px">
    <div><div class="label">State</div><div id="geofence-state" class="value">—</div></div>
    <div><div class="label">Transitions</div><div id="geofence-events" class="value">—</div></div>
  </div>
  <small id="geofence-summary" aria-live="polite">Loading…</small>
</div>
<script>
(function(){
  const eventSummary=document.getElementById('event-summary');
  const eventList=document.getElementById('event-list');
  const geofenceState=document.getElementById('geofence-state');
  const geofenceEvents=document.getElementById('geofence-events');
  const geofenceSummary=document.getElementById('geofence-summary');
  function escapeHtml(value){
    return String(value??'').replace(/[&<>"']/g,ch=>({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[ch]));
  }
  window.loadEvents=async function(){
    try{
      const r=await fetch('/api/events',{cache:'no-store'});
      if(!r.ok) throw new Error('events unavailable');
      const d=await r.json();
      const n=Array.isArray(d.events)?d.events:[];
      // EventApi exposes the lifetime count as `count`. Keep the fallback for
      // older payloads so the dashboard remains compatible during upgrades.
      const total=d.count!==undefined?d.count:(d.total_count!==undefined?d.total_count:(d.total||0));
      eventSummary.textContent=n.length+' retained of '+(d.capacity||n.length)+'; '+total+' total';
      eventList.innerHTML=n.length?n.map(e=>{
        const t=escapeHtml(e.type||'event');
        const m=escapeHtml(e.message||'');
        const ts=escapeHtml(e.timestamp||'');
        return '<small><b>'+t+'</b> '+m+' <span>'+ts+'</span></small><hr>';
      }).join(''):'<small>No events retained.</small>';
    }catch(e){
      eventSummary.textContent='Event history unavailable';
      eventList.innerHTML='';
    }
  };
  window.loadGeofence=async function(){
    try{
      const [liveResponse,configResponse]=await Promise.all([
        fetch('/api/live',{cache:'no-store'}),
        fetch('/api/config',{cache:'no-store'})
      ]);
      if(!liveResponse.ok||!configResponse.ok) throw new Error('diagnostics unavailable');
      const d=await liveResponse.json();
      const c=await configResponse.json();
      const enabled=Boolean(c.geofence_enabled);
      const inside=Boolean(d.geofence_inside);
      const transitions=Number(d.geofence_events||0);
      geofenceState.textContent=!enabled?'DISABLED':(inside?'INSIDE':'OUTSIDE');
      geofenceState.className='value '+(!enabled?'':(inside?'ok':'bad'));
      geofenceEvents.textContent=String(transitions);
      geofenceSummary.textContent=enabled
        ? (transitions+' boundary transition'+(transitions===1?'':'s')+' recorded')
        : 'Enable a geofence to monitor boundary transitions';
    }catch(e){
      geofenceState.textContent='UNAVAILABLE';
      geofenceState.className='value bad';
      geofenceSummary.textContent='Live diagnostics unavailable';
    }
  };
  window.clearEvents=async function(){
    try{
      const r=await fetch('/api/events/clear',{method:'POST',cache:'no-store'});
      if(!r.ok) throw new Error('clear failed');
      await window.loadEvents();
    }catch(e){eventSummary.textContent='Unable to clear event history';}
  };
  const originalLoad=window.loadEvents;
  window.loadEvents=async function(){
    await originalLoad();
    await window.loadGeofence();
  };
})();
</script>
)HTML";
}
