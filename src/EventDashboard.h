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
<script>
(function(){
  const eventSummary=document.getElementById('event-summary');
  const eventList=document.getElementById('event-list');
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
  window.clearEvents=async function(){
    try{
      const r=await fetch('/api/events/clear',{method:'POST',cache:'no-store'});
      if(!r.ok) throw new Error('clear failed');
      await window.loadEvents();
    }catch(e){eventSummary.textContent='Unable to clear event history';}
  };
})();
</script>
)HTML";
}
