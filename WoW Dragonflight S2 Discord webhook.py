import requests
import json
import time
import math
import urllib3
from datetime import datetime



# Add Discord webhook URL
webhook_url = ''

# create a file to store latest run times (Can be renamed to WHATEVER.json)
data_file = 'latest_runs.json'

def load_latest_run_times():
    try:
        with open(data_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
# remove the #<--- to make this functional!
# Change 'CharacterName' (line25)        
            'CharacterName': -1,
#           'CharacterName1': -1,
#           'CharacterName2': -1,
#           'CharacterName3': -1,
        }
def save_latest_run_times(latest_run_times):
    with open(data_file, 'w') as f:
        json.dump(latest_run_times, f)

#Dungeon Image URL's
dungeon_images = {
    "Freehold": "https://cdn.raiderio.net/images/dungeons/expansion7/base/freehold.jpg?1",
    "Neltharion's Lair": "https://cdn.raiderio.net/images/dungeons/expansion6/base/neltharions-lair.jpg?1",
    "The Vortex Pinnacle": "https://cdn.raiderio.net/images/dungeons/expansion3/base/the-vortex-pinnacle.jpg?1",
    "The Underrot": "https://cdn.raiderio.net/images/dungeons/expansion7/base/the-underrot.jpg?1",
    "Brackenhide Hollow": "https://cdn.raiderio.net/images/dungeons/expansion9/base/brackenhide-hollow.jpg?1",
    "Uldaman: Legacy of Tyr": "https://cdn.raiderio.net/images/dungeons/expansion9/base/uldaman-legacy-of-tyr.jpg?1",
    "Halls of Infusion": "https://cdn.raiderio.net/images/dungeons/expansion9/base/halls-of-infusion.jpg?1",
    "Neltharus": "https://cdn.raiderio.net/images/dungeons/expansion9/base/neltharus.jpg?1"
}

#sets API to gather character name
def fetch_character_runs(character):
    api_url = f'https://raider.io/api/v1/characters/profile?region=us&realm=area-52&name={character}&fields=mythic_plus_recent_runs'
    response = requests.get(api_url)
    data = response.json()
    return data['mythic_plus_recent_runs']
    
def format_clock (time):
    time_seconds = math.floor(time / 1000)
    seconds = time_seconds % 60
    if seconds < 10:
        seconds = '0' + str(seconds)
    return f'{math.floor(time_seconds / 60)}:{seconds}'

#sets API to gather all player names from the group ID called from fetch_character_runs

def get_group(url):
    parsed_url = urllib3.util.parse_url(url)
    path_array = parsed_url.path.split('/')
    season = path_array[2]
    run_id = path_array[3].split('-')[0]
    
    api_url = f'https://raider.io/api/v1/mythic-plus/run-details?season={season}&id={run_id}'
    response = requests.get(api_url)
    data = response.json()
    
    characters = []
    for entry in data['roster']:
        character = entry['character']
        characters.append({
            "name": character['name'],
            "role": character['spec']['role'],
            "char_class": character['class']['name'],
            "char_spec": character['spec']['name'],
            "score": entry['ranks']['score'],
            "path": character['path'],
            "realm": character['realm']['name'],
        })
    affixes = []
    weekly_modifiers = data['weekly_modifiers']
    for affix in weekly_modifiers:
        affixes.append({
            "affix": affix['name'],
        })

    affixes_active = data['num_modifiers_active']
    active_modifier_names = []
    if affixes_active == 3:
        active_modifier_names.append({
            "first_affix": weekly_modifiers[0]['name'], 
            "second_affix": weekly_modifiers[1]['name'],
            "third_affix": weekly_modifiers[2]['name'],
        })
    elif affixes_active == 2:
        active_modifier_names.append({
            "first_affix": weekly_modifiers[0]['name'], 
            "second_affix": weekly_modifiers[1]['name'],
        })
    elif affixes_active == 1:
        active_modifier_names.append({
            "first_affix": weekly_modifiers[0]['name'], 
        })

    return characters, affixes, active_modifier_names

def send_notification(character, run):
    dungeon = run['dungeon']
    level = run['mythic_level']
    score = run['score']
    url = run['url']
    clear_time = format_clock(run['clear_time_ms'])
    par_time = format_clock(run['par_time_ms'])
    characters,affixes,active_modifier_names = get_group(url)

#sort roles - 1. tank  2. healer 3.DPS 
    characters.sort(key=lambda char_info: (char_info['role'] != 'tank', char_info['role'] != 'healer'))
    role_emojis = {
        'tank': '🛡️',
        'healer': '💚',
        'dps': '⚔️'
    }
#Makes 'name/role/spec/class - io' message display as one line, to prevent text wrapping on discord
    abbreviations = {
    "Affliction": "Afflic",
    "Assassination": "Assassin",
    "Augmentation": "Aug",
    "Beast Mastery": "Beast M.",
    "Brewmaster": "Brew",
    "Demonology": "Demon",
    "Destruction": "Destro",
    "Devastation": "Deva",
    "Discipline": "Disc",
    "Elemental": "Ele",
    "Enhancement": "Enhance",
    "Marksmanship": "Marksman",
    "Mistweaver": "Mist",
    "Preservation": "Pres",
    "Protection": "Prot",
    "Retribution": "Ret",
    "Restoration": "Resto",
    "Windwalker": "Wind",
    "Death Knight": "D.Knight",
    "Demon Hunter": "D.Hunter",
    }
#creates the "message" var, before the next (large) function
    message = ""

    for char_info in characters:
        char_name = char_info['name']
        quick_link = char_info['path']
        realm_name = char_info['realm']
        raider_io_url = f"https://raider.io{quick_link}"
        linked_name = f"[{char_name}-{realm_name}]({raider_io_url})"
        char_role = char_info['role']
        char_score = char_info['score']
        role_emoji = role_emojis.get(char_role, char_role)
        char_class = abbreviations.get(char_info['char_class'], char_info['char_class'])
        char_spec = abbreviations.get(char_info['char_spec'], char_info['char_spec'])
        char_sc = f"{char_spec} {char_class}"
    #capitalize DPS or first letter of role name
        if char_role == 'dps':
            char_role = char_role.upper()
        else:
            char_role = char_role.capitalize()
    #Pulls the dict.values() from the weekly affixes affecting the latest run
        affix_names = ""
        for affix_dict in active_modifier_names:
            affix_names += ", ".join(affix_dict.values())
    #Pulls the dict.values() from the overall weekly rotating affixes
            weekly_affix_names = ", ".join(affix['affix'] for affix in affixes)
    ### prints the message
        message += f"\n{role_emoji} {linked_name}-**{char_role}**-({char_sc}) - **Score:  {char_score}**"
        payload = {
                'embeds': [
                    {
                        "title":f"{character}'s Latest Mythic+ Run!\n+{level} {dungeon}",
                        "url":url,
                        "description":f"Dungeon cleared in {clear_time}/{par_time}\nDungeon cleared for a total of {score} points!\nActive Affixes: **{affix_names}**" ,
                        'timestamp': run['completed_at'],
                        "fields": [{
                            "name": "_Group Details_",
                            "value": message,
                        }],
                        "footer": {
                            "text": f"Weekly Affixes: {weekly_affix_names}"
                        },
                "image": {
                            "url": dungeon_images.get(dungeon, "")
                        },
                }
            ]
        }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)

    if response.status_code == 204:
        print(f"Notification sent successfully for {character}")
    else:
        print(f"Failed to send notification for {character}. Status code: {response.status_code}")

# Load existing latest run IDs
latest_run_times = load_latest_run_times()

# Main loop
while True:
    for character in latest_run_times:
        runs = fetch_character_runs(character)
        if runs:
            new_run = runs[0]
            if new_run['completed_at'] != latest_run_times[character]:
                send_notification(character, new_run)
                latest_run_times[character] = new_run['completed_at']
                save_latest_run_times(latest_run_times)
    time.sleep(90)  # Check every 1.5 minute
