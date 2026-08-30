#pragma once
#include <Arduino.h>

// Reusable dashboard fragment for the runtime event-history API.
// Kept separate from main.cpp so the UI can later be served from an embedded
// asset or included directly in the existing page without duplicating logic.
inline String eventDashboardHtml() {
  return R"HTML(
<div class="card" id="event-card">
  <b>Event history</b>
  <small id="event-summary">Loading…</small>
  <div id="event-list" style="margin-top:10px"></div>
  <button onclick="clearEvents()">Clear retained history</button>
</div>
<script>
async function loadEvents(){
  try{
    const r=await fetch('/api/events');
    if(!r.ok) throw new Error('events unavailable');
    const d=await r.json();
    const n=Array.isArray(d.events)?d.events:[];
    const total=d.total_count!==undefined?d.total_count:(d.total||0);
    eventSummary.textContent=n.length+' retained of '+(d.capacity||n.length)+'; '+total+' total';
    eventList.innerHTML=n.length?n.map(e=>{
      const t=String(e.type||'event').replace(/</g,'&lt;');
      const m=String(e.message||'').replace(/</g,'&lt;');
      return '<small><b>'+t+'</b> '+m+' <span>'+String(e.timestamp||'')+'</span></small><hr>';
    }).join(''):'<small>No events retained.</small>';
  }catch(e){eventSummary.textContent='Event history unavailable';}
}
async function clearEvents(){
  const r=await fetch('/api/events/clear',{method:'POST'});
  if(!r.ok){eventSummary.textContent='Unable to clear event history';return;}
  await loadEvents();
}
</script>
)HTML";
}
