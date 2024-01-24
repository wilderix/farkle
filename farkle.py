# Import 3rd Party Libraries
import pandas as pd
import streamlit as st
from streamlit import session_state as ss

# Import Built-in Libraries
from collections import Counter
from copy import deepcopy
from random import randint


# TODO:
# 1. Add ENDGAME threshold to setup - DONE
#    1a. Add ENDGAME functionality
# 3. Fix bug that lets player keep unkeepable dice and go into HOT DICE illegally
#    3a. Don't give any buttons (roll/bank/hotdice) besides the keepers/rollers if the current keep_set is not legal


st.set_page_config(
    page_title="This is a test" # ,
    # layout="wide",
)

INTIALIZED_TURN = {
    'rolls_left': 3,
    'rollers': [],
    'roller_lock': True,
    'keepers': [[], [], []],
    'keepers_score': 0,
    'farkle': False
}


# Initialize Session State
if 'menu_choice' not in ss:
    ss['menu_choice'] = 'Setup'
if 'menu_choice_index' not in ss:
    ss['menu_choice_index'] = 0
if 'scoreboard_starting_threshold' not in ss:
    ss['scoreboard_starting_threshold'] = 500
if 'endgame_threshold' not in ss:
    ss['endgame_threshold'] = 10000
if 'three_farkle_penalty' not in ss:
    ss['three_farkle_penalty'] = 1000
if 'number_of_players' not in ss:
    ss['number_of_players'] = 1
if 'players' not in ss:
    ss['players'] = {1: {'name': 'Player 1', 'score': 0, 'farkles': 0, 'threshold_met': False, 'endgame_turn': 0}}
if 'active_player_number' not in ss:
    ss['active_player_number'] = 1
if 'player_to_beat' not in ss:
    ss['player_to_beat'] = 0
if 'turn' not in ss:
    ss['turn'] = deepcopy(INTIALIZED_TURN)
if 'valid_keepers' not in ss:
    ss['valid_keepers'] = False
if 'default_scoring_parameters' not in ss:
    ss['default_scoring_parameters'] = {
        'Single 1': {'rule': '100', 'help': "Each individual [1] will be worth 100 points unless it is part of a more valuable set"},
        'Single 5': {'rule': '50', 'help': "Each individual [5] will be worth 50 points unless it is part of a more valuable set"},
        '3 of a kind': {'rule': '{face} * 100', 'help': "Ex: [3][3][3] would be worth 300"},
        '4 of a kind': {'rule': '{face} * 200', 'help': "Ex: [3][3][3][3] would be worth 600"},
        '5 of a kind': {'rule': '{face} * 300', 'help': "Ex: [3][3][3][3][3] would be worth 900"},
        '6 of a kind': {'rule': '{face} * 400', 'help': "Ex: [3][3][3][3][3][3] would be worth 1200"},
        'straight': {'rule': '2500', 'help': "Rolling [1][2][3][4][5][6] when all 6 dice are in play"},
        '4 of a kind and a pair': {'rule': '1500', 'help': "Ex: Rolling [2][2][2][2][3][3] when all 6 dice are in play"},
        '3 pairs': {'rule': '1500', 'help': "Ex: Rolling [1][1][3][3][4][4] when all 6 dice are in play"},
        '2 triplets': {'rule': '1500', 'help': "Ex: Rolling [1][1][1][6][6][6] when all 6 dice are in play"}
    }
if 'scoring_parameters' not in ss:
    ss['scoring_parameters'] = deepcopy(ss['default_scoring_parameters'])

if 'rules' not in ss:
    scoring_text = ""
    for condition, rule_dict in ss['scoring_parameters'].items():
        rule = rule_dict['rule']
        help = rule_dict['help']

        # try to convert rules to ints where we can
        try:
            rule = f"{int(rule):,}"
        except Exception as e:
            pass

        scoring_text += f"* **{condition} = {rule} points**\n"
        scoring_text += f"  * {help}\n"
    ss['rules'] = f"""
## Rules
    
Farkle is a press-your-luck dice rolling game. Each player will roll 6 dice, initially. Each time they roll, they must keep some scoring dice set aside to get points on their turn. If they do not have any dice that qualify as scoring, they 'Farkle' and forfeit their turn and any score they have accumulated on their turn. At any point, the player may choose to bank their turn score and pass play to the next player.

On each player's turn, they are allowed to reroll any dice they did not set aside to try for more points, up to 3 rolls total.

## Scoring

Scoring is based on sets (or individual dice, in the case of 1's and 5's) as such:

{scoring_text}

In order to start accumulating a score, you must earn at least {ss['scoreboard_starting_threshold']} points in a single turn. Until you reach this threshold for the first time the first time, play will simply pass to the next player, and you will remain at 0 points on the scoreboard.

**Note:** You may go to the "Scoring" page in the menu on the sidebar to change the scoring rules above, but doing so will reset the game.

## Hot Dice

Hot Dice is when all 6 dice have been set aside as scoring. You may then roll all 6 dice again as if taking a new turn while still maintaining and adding to the score you have accumulated on your turn so far. However, rolling a Farkle will wipe out the entire score for the turn.

## Farkle Penalty

For every 3 farkles you get, you will lose {ss['three_farkle_penalty']} points. However, you can never go below 0 points.
"""


# Callback Functions
def callback_basic(old, new):
    ss[old] = ss[new]


def callback_bank(player_id):

    turn_value = ss['turn']['keepers_score']
    for kl, keeper_list in enumerate(ss['turn']['keepers']):
        turn_value += evaluate_scoring_sets(keeper_idx=kl)

    if turn_value >= ss['scoreboard_starting_threshold']:
        ss['players'][player_id]['threshold_met'] = True
    ss['players'][player_id]['score'] += turn_value

    # Are we in the endgame?
    # if ss['players'][player_id]['score'] >= 
    
    
    ss['turn'] = deepcopy(INTIALIZED_TURN)
    advance_active_player_number()


def callback_hot_dice():
    keepable_score = 0
    for k in range(3):
        keepable_score += evaluate_scoring_sets(keeper_idx=k)
    ss['turn']['keepers_score'] += keepable_score
    ss['turn']['rolls_left'] = 3
    ss['turn']['keepers'] = [[], [], []]
    callback_roll(6)


def callback_keep_rollers(form):
    # Whick keeper list do we put these in?
    keepers_index = 2 - ss['turn']['rolls_left']
    rollers_len = len(ss['turn']['rollers'])

    # Go through the checkboxes and put them in a list
    rollers_to_save = []
    rollers_to_reroll = []
    for d in range(rollers_len):
        if ss.get(f'roller-check-{d}'):
            rollers_to_save.append(ss['turn']['rollers'][d])
        else:
            rollers_to_reroll.append(ss['turn']['rollers'][d])

    ss['turn']['keepers'][keepers_index] = rollers_to_save[:]
    ss['turn']['rollers'] = rollers_to_reroll[:]
    ss['turn']['roller_lock'] = True
    ss['valid_keepers'] = False


def callback_keeper_return(keep_set_idx, keeper_idx):
    current_keeper_set = 2 - ss['turn']['rolls_left']
    if keep_set_idx != current_keeper_set:
        pass
    else:
        pop = ss['turn']['keepers'][keep_set_idx].pop(keeper_idx)
        ss['turn']['rollers'].append(pop)
    ss['turn']['rollers'].sort()


def callback_keep_single(die_index):
   
    keepers_index = 2 - ss['turn']['rolls_left']
    pop = ss['turn']['rollers'].pop(die_index)
    ss['turn']['keepers'][keepers_index].append(pop)
    
    # If we used all the rollers, we have hot dice
    if len(ss['turn']['rollers']) == 0:
        ss['turn']['rolls_left'] = 3


def callback_check_rollers_to_keep(form):

    ss['valid_keepers'] = False

    # Go through the checkboxes and put them in a list
    rollers_to_check = []
    for d in range(6):
        if ss.get(f'roller-check-{d}'):
            rollers_to_check.append(ss['turn']['rollers'][d])
    if not rollers_to_check:
        form.warning("You didn't check any dice")
    else:
        # Check the potential keepers to see whether they are valid
        # Basically check for singles/doubles that are not 1/5
        # after checking for special 6-die rolls
        validated = []
        my_counter = Counter(rollers_to_check)

        # 6-die combinations that are valid
        if list(my_counter.keys()) == [1, 2, 3, 4, 5, 6]:
            validated = [1 for _ in range(6)]
        elif list(sorted(my_counter.values())) == [2, 4]:
            validated = [1 for _ in range(6)]
        elif list(my_counter.values()) == [2, 2, 2]:
            validated = [1 for _ in range(6)]
        elif list(my_counter.values()) == [3, 3]:
            validated = [1 for _ in range(6)]
        else:
            for k, v in my_counter.items():
                if v >= 3:
                    validated.extend([1 for _ in range(v)])
                elif v < 3 and k in (1, 5):
                    validated.extend([1 for _ in range(v)])
                elif v < 3 and k not in (1, 5):
                    validated.extend([0 for _ in range(v)])

        value = evaluate_scoring_sets(list_to_evaluate=rollers_to_check)
        form.write(f"UPPER: Your keepers have a value of {value}")
        if sum(validated) < len(rollers_to_check):
            form.warning(f"Sets of 1 or 2 dice that are not [1]s or [5]s cannot be set aside. Uncheck them and press the button again.")
        else:
            ss['valid_keepers'] = True
            form.write(f"LOWER: Your keepers have a value of {value}")



def callback_next_player():
    if ss['players'][ss['active_player_number']]['farkles'] == 3:
        farkle_penalty_score_reduction()
    advance_active_player_number()


def callback_player_name_update(idx, new_key):
    ss['players'][idx]['name'] = ss[new_key]


def callback_player_number(old, new):
    callback_basic(old, new)
    ss['players'] = {
        p: {'name': f'Player {p}', 'score': 0, 'farkles': 0, 'threshold_met': False, 'engame_turn': 0}
        for p in range(1, ss['number_of_players'] + 1)
    }
    ss['turn'] = deepcopy(INTIALIZED_TURN)
    ss['active_player_number'] = 1


def callback_repick_rollers(form):
    ss['valid_keepers'] = False
    ss['roller_lock'] = False


def callback_roll(dice):
    ss['turn']['rollers'] = [randint(1, 6) for d in range(dice)]
    ss['turn']['rollers'].sort()
    ss['turn']['rolls_left'] -= 1
    check_for_farkle()
    ss['turn']['roller_lock'] = False


def callback_scoring_parameters(condition, new_rule):
    ss['scoring_parameters'][condition]['rule'] = ss[new_rule]
    # Also reset the game


def callback_scoring_parameters_reset():
    ss['scoring_parameters'] = deepcopy(ss['default_scoring_parameters'])


# Local Functions
def advance_active_player_number():
    ss['turn'] = deepcopy(INTIALIZED_TURN)
    if ss['active_player_number'] == max(ss['players']):
        ss['active_player_number'] = 1
    else:
        ss['active_player_number'] += 1


def check_for_farkle():
    roller_counter = Counter(ss['turn']['rollers'])
    roller_faces = list(roller_counter.keys())
    roller_counts = list(roller_counter.values())

    if sorted(roller_faces) == [1, 2, 3, 4, 5, 6]:
        pass
    elif sorted(roller_counts) == [2, 4]:
        pass
    elif roller_counts == [2, 2, 2]:
        pass
    elif roller_counts == [3, 3]:
        pass
    elif 3 in roller_counts or 4 in roller_counts or 5 in roller_counts or 6 in roller_counts:
        pass
    elif 1 in roller_faces or 5 in roller_faces:
        pass
    else:
        ss['turn']['farkle'] = True
        ss['players'][ss['active_player_number']]['farkles'] +=1

        if ss['players'][ss['active_player_number']]['farkles'] == 3:
            st.warning(f"You had 3 farkles! You lose {ss['three_farkle_penalty']} from your score.")


def farkle_penalty_score_reduction():
    ss['players'][ss['active_player_number']]['score'] -= ss['three_farkle_penalty']
    if ss['players'][ss['active_player_number']]['score'] < 0:
        ss['players'][ss['active_player_number']]['score'] = 0
    ss['players'][ss['active_player_number']]['farkles'] = 0


def evaluate_scoring_sets(keeper_idx=None, list_to_evaluate=None):
    if keeper_idx is not None:
        list_to_evaluate = ss['turn']['keepers'][keeper_idx]
    keeper_counter = Counter(list_to_evaluate)
    die_face = list(keeper_counter.keys())
    die_count = list(keeper_counter.values())
    current_value = 0

    # Calculate special 6-dice scorings before regular sets
    if sorted(die_face) == [1, 2, 3, 4, 5, 6]:
        current_value += eval(ss['scoring_parameters']['straight']['rule'])
    elif sorted(die_count) == [2, 4]:
        current_value += eval(ss['scoring_parameters']['4 of a kind and a pair']['rule'])
    elif die_count == [2, 2, 2]:
        current_value += eval(ss['scoring_parameters']['3 pairs']['rule'])
    elif die_count == [3, 3]:
        current_value += eval(ss['scoring_parameters']['2 triplets']['rule'])
    # Calculate X-of-a-kind and single or double 1s and 5s
    else:
        for dc_idx, dc in enumerate(die_count):
            df = die_face[dc_idx]
            if dc >= 3 and df != 1:  # X-of-a-kind
                rule = ss['scoring_parameters'][f"{dc} of a kind"]['rule']
                rule = rule.format(face=df)
                current_value += eval(rule)
            elif df in (1, 5):  # single/double 1s/5s
                rule = eval(ss['scoring_parameters'][f"Single {df}"]['rule'])
                current_value += rule * dc

    return current_value


def play_your_turn(player_id=1):

    player = ss['players'][player_id]

    if not ss['turn']['farkle']:
        
        # How many dice are available to roll
        dice = len(ss['turn']['rollers'])
        if dice == 0:
            dice = 6

        if ss['turn']['rolls_left'] > 0 and not ss['turn']['farkle']:
            disabler = False
            if sum(sum(k) for k in ss['turn']['keepers']) and not ss['turn']['rollers']:
                disabler = True
            st.button(
                label="Roll",
                disabled=disabler,
                on_click=callback_roll,
                kwargs={'dice': dice}
            )
        
        if ss['turn']['rollers']:
            roller_columns = st.columns((1, 1, 1, 1, 1, 1, 7))
            for d, die in enumerate(ss['turn']['rollers']):
                roller_columns[d].button(
                    label=str(die),
                    key=f"roller-{d}",
                    on_click=callback_keep_single,
                    kwargs={'die_index': d}
                )
            # pick_rollers_to_keep = st.form('pick_rollers_to_keep')
            # with pick_rollers_to_keep:
            #     st.write("You rolled these dice:")
            #     roller_columns = st.columns((1, 1, 1, 1, 1, 1, 6))
            #     disable_the_rollers = ss['valid_keepers'] or ss['turn']['roller_lock']
            #     for d, die in enumerate(ss['turn']['rollers']):

            #         roller_columns[d].checkbox(
            #             label=str(die),
            #             key=f'roller-check-{d}',
            #             disabled=disable_the_rollers
            #         )
            #     st.write("Check the dice you want to set aside, then click the button.")

            #     if not ss['valid_keepers']:
            #         st.form_submit_button(
            #             label="Check these dice",
            #             on_click=callback_check_rollers_to_keep,
            #             kwargs={'form': pick_rollers_to_keep}
            #             )
            #     else:
            #         st.form_submit_button(
            #             label="Keep these dice",
            #             type='primary',
            #             on_click=callback_keep_rollers,
            #             kwargs={'form': pick_rollers_to_keep}
            #         )
            #         st.form_submit_button(
            #             label="Reset chosen dice",
            #             on_click=callback_repick_rollers,
            #             kwargs={'form': pick_rollers_to_keep}
            #         )

        
        st.write("Keepers")
        keepers_value = 0
        active_keep_set = 2 - ss['turn']['rolls_left']
        for ks, keep_set in enumerate(ss['turn']['keepers']):
            disable_keeper = True
            if ks == active_keep_set:
                disable_keeper = False
            if keep_set:
                keep_set_columns = st.columns((3, 1, 1, 1, 1, 1, 1))
                keep_set_value = evaluate_scoring_sets(keeper_idx=ks)
                keepers_value += keep_set_value
                keep_set_columns[0].write(f"Roll {ks+1} is worth {keep_set_value}")
                for k, keeper in enumerate(keep_set):
                    keep_set_columns[k+1].button(
                        label=str(keeper),
                        key=f"keeper-{ks}-{k}",
                        on_click=callback_keeper_return,
                        kwargs={'keep_set_idx': ks, 'keeper_idx': k},
                        disabled=disable_keeper
                    )
            else:
                keep_set_value = 0
        
        # Offer BANK if we have keeprs and are not in Hot Dice (all the rollers have turned into keepers)
        if (
            sum(sum(k) for k in ss['turn']['keepers'])  # we have any keepers
            and ss['turn']['rollers']  # we have any rollers (i.e., we're not in "hot dice")
            and (player['threshold_met']  # player is already on the scoreboard
                 or keepers_value + ss['turn']['keepers_score'] >= ss['scoreboard_starting_threshold'])  # player could get on the scoreboard now
        ):
            st.button(
                label=f"Bank {keepers_value + ss['turn']['keepers_score']}",
                on_click=callback_bank,
                kwargs={'player_id': player_id}
            )
        elif sum(sum(k) for k in ss['turn']['keepers']) and not ss['turn']['rollers']:
            st.write("You have set asice all 6 dice, therefore you must press your luck!")
            st.write("Press the Hot Dice! button to roll again!")
            st.write(f"Don't worry, we'll hold onto the {keepers_value + ss['turn']['keepers_score']} points and add them to whatever else you set aside. Just in case you don't Farkle!")
            st.button(
                label=f"Hot Dice!",
                on_click=callback_hot_dice
                # kwargs={'keepers_value': keepers_value}
            )
        else:
            if sum(sum(k) for k in ss['turn']['keepers']):
                st.write(f"Your turn score of {keepers_value + ss['turn']['keepers_score']} doesn't meet the {ss['scoreboard_starting_threshold']} threshold to get on the scoreboard.")
                st.button(
                    label='Next Player',
                    on_click=callback_next_player
                )
                

    else:

        st.warning("Farkle!")
        farkle_roller_columns = st.columns((1, 1, 1, 1, 1, 1, 6))
        for d, die in enumerate(ss['turn']['rollers']):
            farkle_roller_columns[d].button(
                label=str(die),
                disabled=True,
                key=f"roller-{d}"
            )
        st.button(
            label='Next Player',
            on_click=callback_next_player
        )

    return player['name']


# Sidebar
with st.sidebar:
    st.selectbox(
        label="Menu",
        options=['Setup', 'Play', 'Scoring'],
        index=ss['menu_choice_index'],
        key='menu_choice_new',
        on_change=callback_basic,
        kwargs={'old': 'menu_choice', 'new': 'menu_choice_new'}
    )

    if ss['menu_choice'] in ('Setup', 'Play'):
        st.subheader("Scoreboard")
        # for idx, player in ss['players'].items():
        #     st.write(f"({idx}) {player['name']}: Score: {player['score']}, Farkles: {player['farkles']}")
        player_df = pd.DataFrame.from_dict(ss['players'])
        st.dataframe(
            player_df.T,
            hide_index=True,
            use_container_width=False,
            column_order=('name', 'score', 'farkles')
        )

    if st.checkbox("Show Session State"):
        ss
    
    if st.checkbox("Show Rules"):
        st.markdown(ss['rules'])


# Main Screen
# st.header("Farkle")
st.subheader(ss['menu_choice'])

# Setup
if ss['menu_choice'] == 'Setup':

    # Scoreboard starting threshold
    setup_a_col1, setup_a_col2 = st.columns((1, 4))
    setup_a_col1.number_input(
        label="Scoreboard starting threshold:",
        min_value=50,
        step=50,
        value=ss['scoreboard_starting_threshold'],
        key='threshold_score_new',
        on_change=callback_basic,
        kwargs={'old': 'scoreboard_starting_threshold', 'new': 'threshold_score_new'}
    )
    setup_a_col2.write("")
    setup_a_col2.write("")
    setup_a_col2.write("Players have to meet this threshold in a single turn before they can get on the scoreboard")
    st.markdown("---")

    # 3 Farkle Penalty
    setup_b_col1, setup_b_col2 = st.columns((1, 4))
    setup_b_col1.number_input(
        label="3 Farkle Penalty:",
        min_value=0,
        step=50,
        value=ss['three_farkle_penalty'],
        key='three_farkle_penalty_new',
        on_change=callback_basic,
        kwargs={'old': 'three_farkle_penalty', 'new': 'three_farkle_penalty_new'}
    )
    setup_b_col2.write("")
    setup_b_col2.write("")
    setup_b_col2.write("Each time a player gets 3 farkles, they lose this many points.")
    st.markdown("---")

    # Endgame Threshold
    setup_c_col1, setup_c_col2 = st.columns((1,4))
    setup_c_col1.number_input(
        label="Endgame Threshold:",
        min_value=5000,
        step=1000,
        value=ss['endgame_threshold'],
        key='endgame_threshold_new',
        on_change=callback_basic,
        kwargs={'old': 'endgame_threshold', 'new': 'endgame_threshold_new'}
    )
    setup_c_col2.write("")
    setup_c_col2.write("")
    setup_c_col2.write("When a player crosses this threshold in a turn, it starts the End Game, and every other playler has once chance to beat the top score.")
    st.markdown("---")

    # Players
    setup_z_col1, setup_z_col2 = st.columns((1, 4))
    setup_z_col1.number_input(
        label="How many players?",
        min_value=1,
        max_value=5,
        value=ss['number_of_players'],
        step=1,
        key='number_of_players_new',
        on_change=callback_player_number,
        kwargs={'old': 'number_of_players', 'new': 'number_of_players_new'}
    )
    setup_z_col2.write("")
    setup_z_col2.write("")
    setup_z_col2.write("Changing this number will reset player names that you may have edited below and reset the scoreboard.")

    st.markdown("---")
    st.write("You can change the players' names at any point. Nothing will be reset except the player's name.")

    for idx, player in ss['players'].items():
        new_key = f'player_name_new_{idx}'
        st.text_input(
            label=f"Player {idx}",
            value=player['name'],
            max_chars=12,
            key=new_key,
            on_change=callback_player_name_update,
            kwargs={'idx': idx, 'new_key': new_key}
        )


# Scoring
elif ss['menu_choice'] == 'Scoring':

    st.write("Note: Any adjustments to the scoring rules will reset the current game.")

    st.markdown("""---""")
    settings_header_col_1, settings_header_col_2 = st.columns([3, 7])
    settings_header_col_1.write("**Setting**")
    settings_header_col_2.write("**Default Setting Example**")
    st.markdown("""---""")

    for condition, rule_dict in ss['scoring_parameters'].items():
        
        rule = rule_dict['rule']
        help = rule_dict['help']
        my_key = f"sp-{condition}-{rule}"

        settings_col_1, settings_col_2 = st.columns([3, 7])

        settings_col_1.text_input(
            label=f"**{condition}**",
            value=rule,
            key=my_key,
            on_change=callback_scoring_parameters,
            kwargs={'condition': condition, 'new_rule': my_key}
        )
        settings_col_2.write("")
        settings_col_2.write("")
        settings_col_2.write(help)

        st.markdown("""---""")

    st.button(
        label="Reset Defaults",
        key='Reset Defaults',
        on_click=callback_scoring_parameters_reset
        )


# Play
elif ss['menu_choice'] == 'Play':

    player_name = ss['players'][ss['active_player_number']]['name']
    st.write(f"It's {player_name}'s turn")
    this_player = play_your_turn(ss['active_player_number'])

else:
    st.subheader("What just happened?")