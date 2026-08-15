from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sys
import os
import random
random.seed()  # Set random seed

# Ensure project root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import existing simulation and RL agent
many_games = None
SIM_IMPORT_ERROR = None
try:
    import importlib.util
    sim_dir = os.path.join(ROOT, 'Base_Sim')
    sim_path = os.path.join(sim_dir, 'Game.py')
    # Ensure Base_Sim directory is importable so Deck_Hand and others can be resolved
    if sim_dir not in sys.path:
        sys.path.insert(0, sim_dir)
    if os.path.exists(sim_path):
        spec = importlib.util.spec_from_file_location('base_sim_game', sim_path)
        sim_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sim_mod)
        many_games = getattr(sim_mod, 'many_games', None)
        QuickGame = getattr(sim_mod, 'quick_game', None)
    else:
        SIM_IMPORT_ERROR = f"Simulation module not found at {sim_path}"
except Exception as e:
    many_games = None
    SIM_IMPORT_ERROR = str(e)
    QuickGame = None

# Import RL agent modules from folder with space using importlib
PokerEnv = None
AdvancedPokerEnv = None
RL_IMPORT_ERROR = None
try:
    import importlib.util
    rl_dir = os.path.join(ROOT, 'RL Agent')
    rl_path = os.path.join(rl_dir, 'Preflop.py')
    flop_path = os.path.join(rl_dir, 'Flop.py')
    if rl_dir not in sys.path:
        sys.path.insert(0, rl_dir)
    if os.path.exists(rl_path):
        spec = importlib.util.spec_from_file_location('rl_preflop', rl_path)
        rl_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rl_mod)
        # PokerEnv class expected in that module
        PokerEnv = getattr(rl_mod, 'PokerEnv', None) or getattr(rl_mod, 'game', None)
        # If class named differently, try to find PokerEnv-like class
        if PokerEnv is None:
            for attr in dir(rl_mod):
                obj = getattr(rl_mod, attr)
                try:
                    if callable(obj) and hasattr(obj, 'make_decision'):
                        PokerEnv = obj
                        break
                except Exception:
                    pass

        if os.path.exists(flop_path):
            flop_spec = importlib.util.spec_from_file_location('rl_flop', flop_path)
            flop_mod = importlib.util.module_from_spec(flop_spec)
            flop_spec.loader.exec_module(flop_mod)
            AdvancedPokerEnv = (
                getattr(flop_mod, 'AdvancedPokerEnv', None)
                or getattr(flop_mod, 'advancedPokerEnv', None)
            )
    else:
        RL_IMPORT_ERROR = f"RL module not found at {rl_path}"
except Exception as e:
    PokerEnv = None
    AdvancedPokerEnv = None
    RL_IMPORT_ERROR = str(e)

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), 'static')), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), 'templates'))

# Card helpers
VALUES = ['A','K','Q','J','10','9','8','7','6','5','4','3','2']
SUITS = ['Spades','Hearts','Diamonds','Clubs']
# Deck of Cards API uses '0' for 10
VALUE_CODE = {v: ('0' if v == '10' else v) for v in VALUES}
SUIT_CODE = {'Spades':'S','Hearts':'H','Diamonds':'D','Clubs':'C'}
# Face-down/back card image
BACK_IMG_URL = 'https://deckofcardsapi.com/static/img/back.png'

def card_to_code(card_str: str):
    # card_str expected like 'A-Spades' or empty
    if not card_str:
        return None
    try:
        val, suit = card_str.split('-')
        return f"{VALUE_CODE[val]}{SUIT_CODE[suit]}"
    except Exception:
        return None

def card_to_api_url(card_str: str):
    code = card_to_code(card_str)
    if not code:
        return None
    return f"https://deckofcardsapi.com/static/img/{code}.png"

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, 'index.html', {"request": request, "values": VALUES, "suits": SUITS, "sim_error": SIM_IMPORT_ERROR, "rl_error": RL_IMPORT_ERROR})

@app.post('/simulate', response_class=HTMLResponse)
async def simulate(request: Request,
                   player_count: int = Form(...),
                   card1: str = Form(''),
                   card2: str = Form(''),
                   comm0: str = Form(''),
                   comm1: str = Form(''),
                   comm2: str = Form(''),
                   comm3: str = Form(''),
                   comm4: str = Form(''),
                   sims: int = Form(100000)):
    # Build community dict
    community_inputs = [comm0, comm1, comm2, comm3, comm4]
    community = {}
    revealed_cards = 0

    for i, c in enumerate(community_inputs):
        if c:
            try:
                val, suit = c.split('-')
                community[i] = [val, suit]
                revealed_cards += 1
            except Exception:
                community[i] = None
        else:
            community[i] = None

    
    # Parse hole cards
    hole1 = None
    hole2 = None
    if card1:
        v,s = card1.split('-')
        hole1 = [v, s]
    if card2:
        v,s = card2.split('-')
        hole2 = [v, s]

    sim_results = None
    sim_error = None
    if many_games is None:
        sim_error = f"Simulation import failed: {SIM_IMPORT_ERROR}"
    else:
        try:
            # run simulations (may take time)
            info = many_games(sims, players=player_count, card1=hole1, card2=hole2, community=community, print_output=False)
            sim_results = info
        except Exception as e:
            sim_error = str(e)

    suggestion = None
    rl_error = None
    if PokerEnv is None:
        rl_error = f"RL import failed: {RL_IMPORT_ERROR}"
    #If community cards are provided use the q_table_after_flop.pkl model for decision making
    elif revealed_cards >= 3:
        try:
            env = AdvancedPokerEnv()
            # Attempt to load pre-trained model if present in RL Agent models
            model_path = os.path.join(ROOT, 'RL Agent', 'models', 'q_table_after_flop.pkl')
            if os.path.exists(model_path):
                try:
                    env.load_model(model_path)
                except Exception:
                    pass
            # Decision uses hole cards and community cards
            if hole1 and hole2:
                suggestion = env.make_decision(hole1, hole2, community)
            else:
                suggestion = 'Provide both hole cards for AI suggestion.'
        except Exception as e:
            print("Error in AdvancedPokerEnv decision making:", e)
            rl_error = str(e)
    else:
        try:
            env = PokerEnv()
            # Attempt to load pre-trained model if present in RL Agent models
            model_path = os.path.join(ROOT, 'RL Agent', 'models', 'pre_flop_q_table.pkl')
            if os.path.exists(model_path):
                try:
                    env.load_model(model_path)
                except Exception:
                    pass
            # Preflop decision only uses hole cards
            if hole1 and hole2:
                suggestion = env.make_decision(hole1, hole2, text=True)
            else:
                suggestion = 'Provide both hole cards for AI suggestion.'
        except Exception as e:
            rl_error = str(e)

    # Prepare image URLs
    hole1_img = card_to_api_url(card1)
    hole2_img = card_to_api_url(card2)
    comm_imgs = [card_to_api_url(c) for c in community_inputs]

    return templates.TemplateResponse(request, 'result.html', {"request": request, "sim_results": sim_results, "sim_error": sim_error, "suggestion": suggestion, "rl_error": rl_error, "hole1_img": hole1_img, "hole2_img": hole2_img, "comm_imgs": comm_imgs, "player_count": player_count, "sims": sims, "back_img": BACK_IMG_URL})

# --- New endpoints for play-vs-model ---
from fastapi.responses import JSONResponse

@app.get('/play', response_class=HTMLResponse)
async def play(request: Request):
    return templates.TemplateResponse(request, 'play.html', {"request": request, "back_img": BACK_IMG_URL})

@app.post('/play_action')
async def play_action(request: Request):
    data = await request.json()
    action = data.get('action', 'deal')
    try:
        player_chips = int(data.get('player_chips', 30))
    except Exception:
        player_chips = 30
    try:
        ai_chips = int(data.get('ai_chips', 30))
    except Exception:
        ai_chips = 30

    # Helpers to format card lists
    def hand_to_strs(h):
        try:
            return [f"{h.card1[0]}-{h.card1[1]}", f"{h.card2[0]}-{h.card2[1]}"]
        except Exception:
            return None

    # Create a fresh deck and deal hands + community
    try:
        from Deck_Hand import deck as DeckClass, hand as HandClass
        d = DeckClass()
        human_hand = HandClass(d)
        ai_hand = HandClass(d)
        # draw 5 community cards
        comm = [d.draw_card() for _ in range(5)]
        community_all = [f"{c[0]}-{c[1]}" for c in comm]
    except Exception:
        # fallback fixed cards
        human_hand = type('H', (), {'card1': ['A','Spades'], 'card2': ['K','Hearts']})()
        ai_hand = type('H', (), {'card1': ['Q','Clubs'], 'card2': ['J','Diamonds']})()
        community_all = [None, None, None, None, None]

    human_hand_strs = hand_to_strs(human_hand)
    ai_hand_strs = hand_to_strs(ai_hand)

    # If action is just 'deal', return hands and hidden community (face-down)
    if action == 'deal':
        return JSONResponse({
            'player_chips': player_chips,
            'ai_chips': ai_chips,
            'human_hand': human_hand_strs,
            'ai_hand': ai_hand_strs,
            'community': [None, None, None, None, None],
            'log': 'Dealt hands. Place your action.'
        })

    # Otherwise simulate ante and process a staged hand (preflop -> flop -> turn -> river)
    ante = 1
    player_chips -= ante
    ai_chips -= ante
    pot = ante * 2

    small = 1
    big = 3
    user_map = {'fold':'Fold','call':'Call','raise_small':'Raise Small','raise_big':'Raise Big'}
    user_act_text = user_map.get(action, 'Call')

    events = []
    winner = None
    outcome = ''

    # Preflop AI decision uses PokerEnv if available
    ai_action = None
    try:
        if PokerEnv is not None:
            env = PokerEnv()
            model_path = os.path.join(ROOT, 'RL Agent', 'models', 'pre_flop_q_table.pkl')
            if os.path.exists(model_path):
                try:
                    env.load_model(model_path)
                except Exception:
                    pass
            ai_action = env.make_decision(ai_hand.card1, ai_hand.card2, text=True)
        else:
            ai_action = random.choice(['Fold','Call','Raise Small','Raise Big'])
    except Exception:
        ai_action = random.choice(['Fold','Call','Raise Small','Raise Big'])

    events.append({'stage':'preflop','ai_action':ai_action,'player_action':user_act_text,'pot':pot})

    if user_act_text == 'Fold':
        ai_chips += pot
        winner = 'ai'
        outcome = 'You folded. AI wins the pot.'
        return JSONResponse({'player_chips':player_chips,'ai_chips':ai_chips,'human_hand':human_hand_strs,'ai_hand':ai_hand_strs,'community':[None,None,None,None,None],'log':outcome})

    # helper adders
    def ai_add(amount):
        nonlocal ai_chips, pot
        amt = min(int(amount), max(0, ai_chips))
        ai_chips -= amt
        pot += amt
        return amt
    def player_add(amount):
        nonlocal player_chips, pot
        amt = min(int(amount), max(0, player_chips))
        player_chips -= amt
        pot += amt
        return amt

    # Apply initial raise/call exchange
    if user_act_text == 'Raise Small':
        player_add(small)
        if ai_action == 'Fold':
            player_chips += pot; winner='player'; outcome=f'You raised small and AI folded. You win {pot}.'
        elif ai_action == 'Call':
            ai_add(small)
        else:
            if ai_action == 'Raise Small': ai_add(small); player_add(small)
            else: ai_add(big); player_add(big)
    elif user_act_text == 'Raise Big':
        player_add(big)
        if ai_action == 'Fold':
            player_chips += pot; winner='player'; outcome=f'You raised big and AI folded. You win {pot}.'
        elif ai_action == 'Call': ai_add(big)
        else:
            if ai_action == 'Raise Small': ai_add(small); player_add(small)
            else: ai_add(big); player_add(big)
    elif user_act_text == 'Call':
        if ai_action == 'Fold': player_chips += pot; winner='player'; outcome='AI folded after your call. You win the pot.'
        elif ai_action == 'Call': pass
        elif ai_action == 'Raise Small': ai_add(small); player_add(small)
        else: ai_add(big); player_add(big)

    if winner is not None:
        return JSONResponse({'player_chips':player_chips,'ai_chips':ai_chips,'human_hand':human_hand_strs,'ai_hand':ai_hand_strs,'community':[None,None,None,None,None],'log':outcome})

    # Stage progression: reveal flop, turn, river. At/after flop use AdvancedPokerEnv for AI decisions.
    stages = [ ('flop',3), ('turn',4), ('river',5) ]
    revealed = [None,None,None,None,None]

    for stage, count in stages:
        # reveal next community cards
        for i in range(count):
            if revealed[i] is None:
                revealed[i] = community_all[i]
        # Determine AI decision (after flop use AdvancedPokerEnv if available)
        try:
            if stage == 'flop' or stage == 'turn' or stage == 'river':
                if AdvancedPokerEnv is not None and count >= 3:
                    env2 = AdvancedPokerEnv()
                    model_path2 = os.path.join(ROOT, 'RL Agent', 'models', 'q_table_after_flop.pkl')
                    if os.path.exists(model_path2):
                        try:
                            env2.load_model(model_path2)
                        except Exception:
                            pass
                    ai_stage_action = env2.make_decision(ai_hand.card1, ai_hand.card2, {0: revealed[0],1:revealed[1],2:revealed[2],3:revealed[3],4:revealed[4]})
                else:
                    # Fallback to PokerEnv or random
                    if PokerEnv is not None:
                        envp = PokerEnv()
                        ai_stage_action = envp.make_decision(ai_hand.card1, ai_hand.card2, text=True)
                    else:
                        ai_stage_action = random.choice(['Fold','Call','Raise Small','Raise Big'])
        except Exception:
            ai_stage_action = random.choice(['Fold','Call','Raise Small','Raise Big'])

        # Apply AI action
        if ai_stage_action == 'Fold':
            player_chips += pot
            winner = 'player'
            outcome = f'AI folded on {stage}. You win {pot}.'
            events.append({'stage':stage,'community':list(revealed),'ai_action':ai_stage_action,'pot':pot,'outcome':outcome})
            break
        elif ai_stage_action == 'Call':
            events.append({'stage':stage,'community':list(revealed),'ai_action':ai_stage_action,'pot':pot})
        elif ai_stage_action == 'Raise Small':
            added = ai_add(small)
            # assume player auto-calls for continuation
            player_add(small)
            events.append({'stage':stage,'community':list(revealed),'ai_action':ai_stage_action,'pot':pot,'added':added})
        else: # Raise Big
            added = ai_add(big)
            player_add(big)
            events.append({'stage':stage,'community':list(revealed),'ai_action':ai_stage_action,'pot':pot,'added':added})

    # If no winner by folding, resolve showdown
    if winner is None:
        # Very simple showdown: estimate winner by random weighted by preflop strength if available
        human_win_prob = 0.5
        try:
            if PokerEnv is not None:
                env3 = PokerEnv()
                hw = env3._preflop_strength(human_hand)
                aw = env3._preflop_strength(ai_hand)
                if hw is None: hw = 0.5
                if aw is None: aw = 0.5
                total = hw + aw
                if total > 0:
                    human_win_prob = hw / total
        except Exception:
            human_win_prob = 0.5

        if random.random() < human_win_prob:
            player_chips += pot
            winner = 'player'
            outcome = f'You win showdown and get {pot} chips.'
        else:
            ai_chips += pot
            winner = 'ai'
            outcome = f'AI wins showdown and gets {pot} chips.'

    # Return final state including community (some entries may remain None if never revealed)
    player_chips = max(0, int(player_chips))
    ai_chips = max(0, int(ai_chips))

    return JSONResponse({
        'player_chips': player_chips,
        'ai_chips': ai_chips,
        'human_hand': human_hand_strs,
        'ai_hand': ai_hand_strs,
        'community': revealed,
        'events': events,
        'pot': pot,
        'winner': winner,
        'log': outcome
    })

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
