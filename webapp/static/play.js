// Manage chips in localStorage and handle actions via /play_action
const DEFAULT_CHIPS = 30;
function getChips(key){
  const v = localStorage.getItem(key);
  return v ? parseInt(v,10) : DEFAULT_CHIPS;
}
function setChips(key,val){
  localStorage.setItem(key, String(val));
}
function updateUI(state){
  document.getElementById('player-chips').textContent = state.player_chips;
  document.getElementById('ai-chips').textContent = state.ai_chips;
  if(state.human_cards){
    document.getElementById('p1').src = state.human_cards[0];
    document.getElementById('p2').src = state.human_cards[1];
  }
  // Reveal AI cards when provided by server
  if(state.ai_cards){

    document.getElementById('a1').src = buildCardUrl(state.ai_cards[0]);
    document.getElementById('a2').src = buildCardUrl(state.ai_cards[1]);
    
  }
  if(state.community){
    for(let i=0;i<5;i++){
      const el = document.getElementById('c'+i);
      if(!el) continue;
      if(state.community[i]) el.src = buildCardUrl(state.community[i]);
      else el.src = 'https://deckofcardsapi.com/static/img/back.png';
    }
  }
  if(state.log){
    const log = document.getElementById('log');
    // Reset log on each user input and show server-provided log
    log.innerText = state.log;
  }
}

function buildCardUrl(cardStr){
  if(!cardStr) return null;
  const parts = cardStr.split('-');
  let v = parts[0];
  if(v === '10') v = '0';
  const suit = parts[1][0].toUpperCase();
  return `https://deckofcardsapi.com/static/img/${v}${suit}.png`;
}

async function doAction(action){
  // reset the log on each user input and show server-provided log
  const log = document.getElementById('log');
  log.innerText = '';
  // include stage and community_all if present
  const stage = window.stage || 0;
  const community_all = window.community_all || null;
  const player_chips = getChips('player_chips');
  const ai_chips = getChips('ai_chips');
  // When dealing a new hand, hide the New Hand button and enable action buttons
  if(action === 'deal'){
    showNewHand(false);
    setActionButtonsEnabled(true);
    // hide AI cards until round end
    document.getElementById('a1').src = 'https://deckofcardsapi.com/static/img/back.png';
    document.getElementById('a2').src = 'https://deckofcardsapi.com/static/img/back.png';
  }

  const res = await fetch('/play_action', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({action, player_chips, ai_chips, stage, community_all})
  });
  const data = await res.json();
  if(data.player_chips !== undefined){
    setChips('player_chips', data.player_chips);
    setChips('ai_chips', data.ai_chips);
  }
  // Store/refresh community_all and stage for staged play
  if(data.community_all) window.community_all = data.community_all;
  if(data.stage !== undefined && data.stage !== null) window.stage = data.stage;

  // Map returned card strings to image urls for human only
  if(data.human_hand){
    data.human_cards = [buildCardUrl(data.human_hand[0]), buildCardUrl(data.human_hand[1])];
  }
  // community stays as strings; updateUI will map them
  updateUI(data);

  // Determine if this response is a final/round-end state
  const logText = (data.log || '').toLowerCase();
  const isFinal = (data.winner !== undefined) ||
                  logText.includes('showdown') ||
                  logText.includes('wins') ||
                  logText.includes('folded') ||
                  logText.includes('tie');

  if(isFinal){
    // Reveal AI cards (if provided by server on final state)
    if(data.ai_hand){
      const aiCards = [buildCardUrl(data.ai_hand[0]), buildCardUrl(data.ai_hand[1])];
      document.getElementById('a1').src = aiCards[0];
      document.getElementById('a2').src = aiCards[1];
    }
    // Disable action buttons until user clicks New Hand
    setActionButtonsEnabled(false);
    showNewHand(true);
  } else {
    // Not final: enable action buttons so user can decide next stage
    setActionButtonsEnabled(true);
    showNewHand(false);
  }
}

function setActionButtonsEnabled(enabled){
  document.getElementById('btn-fold').disabled = !enabled;
  document.getElementById('btn-call').disabled = !enabled;
  document.getElementById('btn-raise-small').disabled = !enabled;
  document.getElementById('btn-raise-big').disabled = !enabled;
}

function showNewHand(visible){
  const el = document.getElementById('btn-new-hand');
  if(!el) return;
  el.style.display = visible ? 'inline-block' : 'none';
}

function newHand(){
  const log = document.getElementById('log');
  log.innerText = 'New hand dealt.';
  doAction('deal');
}

// Initialize UI from storage
(function(){
  const p = getChips('player_chips');
  const a = getChips('ai_chips');
  document.getElementById('player-chips').textContent = p;
  document.getElementById('ai-chips').textContent = a;
  document.getElementById('btn-fold').addEventListener('click', ()=> doAction('fold'));
  document.getElementById('btn-call').addEventListener('click', ()=> doAction('call'));
  document.getElementById('btn-raise-small').addEventListener('click', ()=> doAction('raise_small'));
  document.getElementById('btn-raise-big').addEventListener('click', ()=> doAction('raise_big'));
  document.getElementById('btn-new-hand').addEventListener('click', newHand);
  // Hide New Hand until round finishes and ensure action buttons enabled
  showNewHand(false);
  setActionButtonsEnabled(true);
  // Auto-deal on load so cards are face-up
  newHand();
})();