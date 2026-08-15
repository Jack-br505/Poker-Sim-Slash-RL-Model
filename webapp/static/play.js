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
  if(state.ai_cards){
    document.getElementById('a1').src = state.ai_cards[0];
    document.getElementById('a2').src = state.ai_cards[1];
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
    log.innerHTML = state.log + '\n' + log.innerHTML;
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
  const player_chips = getChips('player_chips');
  const ai_chips = getChips('ai_chips');
  const res = await fetch('/play_action', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({action, player_chips, ai_chips})
  });
  const data = await res.json();
  if(data.player_chips !== undefined){
    setChips('player_chips', data.player_chips);
    setChips('ai_chips', data.ai_chips);
  }
  // Map returned card strings to image urls
  if(data.human_hand){
    data.human_cards = [buildCardUrl(data.human_hand[0]), buildCardUrl(data.human_hand[1])];
  }
  if(data.ai_hand){
    data.ai_cards = [buildCardUrl(data.ai_hand[0]), buildCardUrl(data.ai_hand[1])];
  }
  // community stays as strings; updateUI will map them
  updateUI(data);
}

function newHand(){
  // Request a new deal from server and show cards
  doAction('deal');
  document.getElementById('log').innerHTML = 'New hand dealt.';
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
  // Auto-deal on load so cards are face-up
  newHand();
})();