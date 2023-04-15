import requests
import re
from bs4 import *


def also_known_as(*names):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        for name in names:
            globals()[name] = wrapper
        return wrapper

    return decorator


def remove_tags(html):
    return re.sub('<.*?>', '', html)


def assign_input(input_data):
    """
    Assign the input_data to the appropriate variable based on its type.

    :param input_data: Input data, which can be a BeautifulSoup object, a string (URL or HTML), or an integer.
    :return: A tuple containing the values for (block, html, url, id), where one of them will have the input_data value.
    """

    # Initialize variables
    block = html = url = id = None

    # Check if input_data is a BeautifulSoup object
    if isinstance(input_data, BeautifulSoup):
        block = input_data

    # Check if input_data is a string
    elif isinstance(input_data, str):
        # Check if input_data is a URL (basic check)
        if 'aonprd.com' in input_data:
            url = input_data
        elif '<' in input_data:
            html = input_data
        else:
            print('Input is a string but not a url or html.')

    # Check if input_data is an integer
    elif isinstance(input_data, int):
        id = input_data

    else:
        print("Unknown input.")

    return (block, html, url, id)


def process_input(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    """
    Take any kind of input and return the beautifulsoup object of the stat block of the entry.

    :param input_data: Optional, can be a BeautifulSoup object, a string (URL or HTML), or an integer.
    :param block: Optional BeautifulSoup object.
    :param html: Optional HTML string.
    :param url: Optional URL string.
    :param id: Optional integer representing the creature ID.
    :param type: Optional string representing the type of data, default is 'creature'.
    :return: A tuple containing the processed values for (block, html, url, id, type).
    """
    # check if we have to identify the input data
    if input_data is not None:
        block, html, url, id = assign_input(input_data)

    # escalate given data to the level of a bs4 object
    if block is None:
        if html is None:
            if url is None:
                if id is None:
                    print("No input provided.")
                url = get_url(id=id, type=type)
            html = get_html(url=url)
        block = get_block(html=html)
    return block, html, url, id, type


@also_known_as('url')
def get_url(id=None, type='creature'):
    """
    Generates a URL for an entry in the Pathfinder Second Edition system.

    Args:
    id (int): The ID number of the entry to generate a URL for.
    type (str): The type of entry, defaults to 'creature'.

    Returns:
    str: The URL for the given entry ID and type, or None if no ID is provided.

    """
    monsterurl = 'https://2e.aonprd.com/Monsters.aspx?ID='
    if id is None:
        return None
    if type == 'creature':
        url = monsterurl + str(id)
        return url


@also_known_as('html')
def get_html(input_data=None, url=None, id=None, type='creature'):
    """
    Retrieve the HTML content from a given URL or creature ID.

    :param input_data: Optional data to be processed, can be a string (URL), or an integer.
    :param url: Optional URL string.
    :param id: Optional integer representing the creature ID.
    :param type: Optional string representing the type of data, default is 'creature'.
    :return: HTML content as a string.
    """
    # check if we have to parse the input data
    if input_data is not None:
        block, html, url, id = assign_input(input_data)

    if url is None:
        url = get_url(id=id, type=type)
    response = requests.get(url)
    html = response.text
    return html


@also_known_as('block')
def get_block(input_data=None, html=None, url=None, id=None, type='creature'):
    """
    Get the stat block of the desired html content by providing the HTML, URL, or ID.

    :param html: The HTML content to search for the block. (default: None)
    :param url: The URL of the web page to fetch and search for the block if no html is provided. (default: None)
    :param id: The ID used to generate the URL if no URL or HTML is provided. (default: None)
    :param type: The type of content (e.g., 'creature') to be used when generating the URL. (default: 'creature')
    :return: The desired HTML block as a BeautifulSoup element.
    """
    # check if we have to parse the input data
    if input_data is not None:
        block, html, url, id = assign_input(input_data)

    # escalate information to html level
    if html is None:
        if url is None:
            if id is None:
                print("No input provided.")
            url = get_url(id=id, type=type)
        html = get_html(url=url)

    soup = BeautifulSoup(html, 'html.parser')
    block = soup.select_one('#ctl00_RadDrawer1_Content_MainContent_DetailedOutput')
    return block


class Pathfinder2eMonster:
    def __init__(self, html=None, id=None, ):
        self.name = ''
        self.level = int
        self.size = str
        self.type = str
        self.alignment = str
        self.stats = {}
        self.abilities = {}
        self.actions = []
        self.skills = {}
        self.traits = []
        self.spells = []
        self.description = ''

        if html is None:
            if id is not None:
                html = get_monster_block(id)

        self.interpret_html(self, html)

    def interpret_html(self, html):
        block = html

    def add_stat(self, stat_name, stat_value):
        self.stats[stat_name] = stat_value

    def add_ability(self, ability_name, ability_desc):
        self.abilities[ability_name] = ability_desc

    def add_action(self, action_name, action_desc):
        self.actions.append((action_name, action_desc))

    def add_skill(self, skill_name, skill_value):
        self.skills[skill_name] = skill_value

    def add_trait(self, trait_name):
        self.traits.append(trait_name)

    def add_spell(self, spell_name):
        self.spells.append(spell_name)

    def set_description(self, description):
        self.description = description


def create_monster_instance(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    if block is None:
        block = get_block(input_data, html, url, id, type)

    pfs = get_pfs(block=block)
    namelong = get_name_long(block=block)
    description = get_description(block=block)
    recall = get_recall(block=block)
    name = get_name(block=block)
    level = get_level(block=block)
    rarity = get_rarity(block=block)
    alignment = get_alignment(block=block)
    size = block.select_one(".traitsize a").text
    traits = get_traits(block=block)
    perception = None
    languages = None
    skills = None
    ability_modifiers = None
    items = None
    interaction_abilities = None
    ac = None
    saving_throws = None
    hp = None
    immunities = None
    weaknesses = None
    resistances = None
    automatic_abilities = None
    reactive_abilities = None
    speed = None
    melee_attacks = None
    ranged_attacks = None
    spells = None
    innate_spells = None
    focus_spells = None
    rituals = None
    offensive_abilities = None
    proactive_abilities = None


    return Monster(name, level, alignment, size, traits)


@also_known_as('pfs')
def get_pfs(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    pfs = block.select_one('a[href="PFS.aspx"]').select_one('img').get('alt')
    return pfs


@also_known_as('name2', 'namelong')
def get_name_long(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    name_long = block.select_one('a[href="PFS.aspx"]').select_one('img').get('alt')
    return name_long


@also_known_as('desc', 'get_desc')
def get_description(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)

    h1 = block.find('h1', {'class': 'title'})
    h2 = h1.find_next_sibling('h2')
    description = ''
    nextsib = h1.next_sibling
    while nextsib is not h2:
        description += str(nextsib)
        nextsib = nextsib.next_sibling
    description = remove_tags(description)
    description = description.split('Recall Knowledge')[0]
    return description


@also_known_as('recall')
def get_recall(input_data=None, block: object = None, html: str = None, url: str = None, id: int = None, type: str = 'creature') -> dict:
    """
    Retrieves the Recall Knowledge information from a monster's stat block and returns it as a dictionary.

    Args:
        input_data (object, optional): Any of the below, which will be assigned determined on type.
        block (object, optional): The BeautifulSoup object representing the monster's stat block. Defaults to None.
        html (str, optional): The HTML content of the monster's stat block. Defaults to None.
        url (str, optional): The URL of the monster's stat block. Defaults to None.
        id (int, optional): The ID of the monster in the Pathfinder 2e SRD. Defaults to None.
        type (str, optional): The type of the entity to retrieve (e.g. "creature", "hazard"). Defaults to 'creature'.

    Returns:
        dict: A dictionary of Recall Knowledge information, where the bolded text is the key and the following unbolded
        text is the value.
    """

    block, html, url, id, type = process_input(input_data, block, html, url, id, type)

    h1 = block.find('h1', {'class': 'title'})
    h2 = h1.find_next_sibling('h2')
    description = ''
    nextsib = h1.next_sibling
    while nextsib is not h2:
        description += str(nextsib)
        nextsib = nextsib.next_sibling

    recall = description.partition(r'<b><u><a href="Rules.aspx?ID=563">')
    if len(recall) == 1:
        return None
    if len(recall) == 3:
        recall = recall[1] + recall[2]

    soup = BeautifulSoup(recall, 'html.parser')
    recalldict = {}
    for bold in soup.find_all('b'):
        key = bold.text.strip().rstrip(':').lstrip('Recall Knowledge - ')
        value = bold.next_sibling.split('DC')[-1].strip()
        recalldict[key] = value

    return recalldict


@also_known_as('name')
def get_name(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)

    monster_link = block.find(lambda tag: tag.name == 'a' and
                                          tag.has_attr('href') and
                                          tag['href'].startswith('Monsters.aspx?ID=') and
                                          tag.parent.name == 'h1' and
                                          tag.parent.get('class') == ['title'] and
                                          not tag['href'].endswith('=True'))
    monster_name = monster_link.text
    return monster_name


@also_known_as('level', 'lvl')
def get_level(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    tag = block.find('span', {'style': 'margin-left:auto; margin-right:0'})
    text = tag.text
    levelstr = text.split()[-1]
    levelint = int(levelstr)
    return levelint


@also_known_as('rarity')
def get_rarity(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    rarity = 'Common'
    if block.select_one("span.traituncommon"): rarity = 'Uncommon'
    elif block.select_one("span.traitrare"): rarity = 'Rare'
    return rarity


@also_known_as('alignment', 'align')
def get_alignment(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    alignment = block.select_one(".traitalignment a").text
    return alignment

@also_known_as('traits')
def get_traits(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    traitslist = [t.text for t in block.select(".trait a")]
    return traitslist


@also_known_as('blocksplit')
def split_block(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    # find the first time a trait appears
    tag_trait = block.find(lambda t:
                           t.name == 'span' and
                           t.get('class', [])[0].startswith('trait'))
    # find the next line break after the trait is given
    next_line_break = tag_trait.find_next('br')
    content_after_line_break = []
    for element in next_line_break.next_siblings:
        if 'title' in element.get('class', []):  # stop if you get to a title
            break
        if isinstance(element, NavigableString):
            content_after_line_break.append(element)
        else:
            content_after_line_break.append(element.prettify())
    new_html = ''.join(content_after_line_break)
    html_by_sections = new_html.split(r'<hr>')
    for html in html_by_sections:
        #TODO convert each html in list to soup
        pass

    return foo


@also_known_as('foo')
def get_foo(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    foo = None
    return foo
