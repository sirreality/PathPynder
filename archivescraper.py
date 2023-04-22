import logging
import requests
import re
from bs4 import *


def remove_tags(html):
    return re.sub('<.*?>', '', html)


class ArchivePage:
    def __init__(self, input_data=None, block=None, html=None, url=None, id=None, type='creature'):
        self.input_data = input_data
        self.block = block
        self.html = html
        self.url = url
        self.id = id
        self.type = type
        if input_data:
            self.assign_input()
        if self.block is None:
            if self.html:
                self.set_block()
            elif self.url:
                self.set_html()
                self.set_block()
            elif self.id:
                self.set_url()
                self.set_html()
                self.set_block()
            else:
                logging.error("No information on Archive Page given.")

    def assign_input(self):
        # Check if input_data is a BeautifulSoup object
        if isinstance(self.input_data, BeautifulSoup):
            self.block = self.input_data

        # Check if input_data is a string
        elif isinstance(self.input_data, str):
            # Check if input_data is a URL (basic check)
            if 'aonprd.com' in self.input_data:
                self.url = self.input_data
            elif '<' in self.input_data:
                self.html = self.input_data
            else:
                print('Input is a string but not a url or html.')

        # Check if input_data is an integer
        elif isinstance(self.input_data, int):
            self.id = self.input_data

        else:
            print(f"Unknown input type for input_data: {type(self.input_data)}")

    def set_url(self):
        """
        Generates a URL for an entry in the Pathfinder Second Edition system.

        Args:
        id (int): The ID number of the entry to generate a URL for.
        type (str): The type of entry, defaults to 'creature'.

        Returns:
        str: The URL for the given entry ID and type, or None if no ID is provided.

        """
        urlfolders = {
            'creature': 'https://2e.aonprd.com/Monsters.aspx?ID=',
            'NPC': 'https://2e.aonprd.com/NPCs.aspx?ID='
        }

        self.url = urlfolders[self.type] + str(self.id)

    def set_html(self):
        self.html = requests.get(self.url).text

    def set_block(self):
        soup = BeautifulSoup(self.html, 'html.parser')
        self.block = soup.select_one('#ctl00_RadDrawer1_Content_MainContent_DetailedOutput')


def parse_soup(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    if block is None:
        block = get_block(input_data, html, url, id, type)
    data = {}

    data[pfs] = get_pfs(block=block)
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

    return data


def get_pfs(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    pfs = block.select_one('a[href="PFS.aspx"]').select_one('img').get('alt')
    return pfs


def get_name_long(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    name_long = block.select_one('a[href="PFS.aspx"]').select_one('img').get('alt')
    return name_long


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


def get_recall(input_data=None, block = None, html = None, url = None, id = None, type = 'creature') -> dict:
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


def get_level(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    tag = block.find('span', {'style': 'margin-left:auto; margin-right:0'})
    text = tag.text
    levelstr = text.split()[-1]
    levelint = int(levelstr)
    return levelint


def get_rarity(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    rarity = 'Common'
    if block.select_one("span.traituncommon"): rarity = 'Uncommon'
    elif block.select_one("span.traitrare"): rarity = 'Rare'
    return rarity


def get_alignment(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    alignment = block.select_one(".traitalignment a").text
    return alignment


def get_traits(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    traitslist = [t.text for t in block.select(".trait a")]
    return traitslist


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


def get_foo(input_data=None, block=None, html=None, url=None, id=None, type='creature'):
    block, html, url, id, type = process_input(input_data, block, html, url, id, type)
    foo = None
    return foo

