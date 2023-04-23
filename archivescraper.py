import logging
import requests
from typing import Optional, List, Dict
import re
from bs4 import *
from bs4 import Tag, NavigableString, PageElement

logging.basicConfig(level=logging.INFO)




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


class ArchivePageParser:
    def __init__(self, archive_page: ArchivePage):
        self.page = archive_page
        self.soup = self.page.block
        self.data = {}
        self.process_page()

    def process_page(self):
        logging.info('I am starting to process the Archive Page.')
        h1list = split_by_tag(self.soup, 'h1')
        logging.info(f'I found {len(h1list)} main headers.')
        for section in h1list:
            header = section.find('h1')

            if header:

                if header.find('a', {'href': 'PFS.aspx'}):
                    logging.info('This header is description.')
                    self.process_header_flavor(section)

                elif 'Creature ' in header.text:
                    logging.info('This header is Stat Block.')
                    self.process_header_stats(section)

                elif header.find('a', href=lambda href: href.startswith('MonsterFamilies')):
                    logging.info('This header is Monster Families.')
                    self.process_header_family(section)

    def process_header_flavor(self, section):
        soup = section
        h1 = soup.find('h1', {'class': 'title'})
        recall_tag = soup.find('a', {'href': 'Rules.aspx?ID=563'})
        h2 = h1.find_next_sibling('h2')

        pfs = h1.select_one('img').get('alt')
        self.save('pfs', pfs)

        title = h1.get_text()
        self.save('title', title)

        description = ''
        nextsib = h1.next_sibling
        while nextsib is not None:
            if str(recall_tag) in str(nextsib):
                break
            description += str(nextsib)
            nextsib = nextsib.next_sibling
        clean_description = re.sub(r'<br\s*/?>\s*', '\n', description)
        self.save('description', clean_description)

        recallsection = ''
        while nextsib is not h2:
            recallsection += str(nextsib)
            if nextsib:
                nextsib = nextsib.next_sibling
            else:
                break
        recallsoup = BeautifulSoup(recallsection, 'html.parser')
        recalldict = {}
        for bold in recallsoup.find_all('b'):
            key = bold.text.strip().rstrip(':').lstrip('Recall Knowledge - ')
            value = bold.next_sibling.split('DC')[-1].strip()
            recalldict[key] = value
        self.save('recall', recalldict)

    def process_header_stats(self, section):
        soup = section
        header = section.find('h1')

        name, level = header.text.split('Creature ')
        self.save('name', name)
        self.save('level', int(level))

        if soup.select_one("span.traituncommon"):
            rarity = 'Uncommon'
        elif soup.select_one("span.traitrare"):
            rarity = 'Rare'
        else:
            rarity = 'Common'
        self.save('rarity', rarity)

        alignment = soup.select_one(".traitalignment a").text
        self.save('alignment', alignment)

        size = soup.select_one(".traitsize a").text
        self.save('size', size)

        # other traits
        traitslist = [t.text for t in soup.select(".trait a")]
        self.save('traits',traitslist)

        # List of lines
        last_trait = None
        for span in soup.find_all('span', class_='trait'):
            last_trait = span
        # TODO pick up here

    def process_header_family(self, section):
        pass

    def save(self, key, value):
        value_length_limit = 30
        if len(str(value)) < value_length_limit:
            logging.info(f'I am saving to {key}: {value}.')
        else:
            logging.info(f'I am saving to {key}: {len(str(value))} characters.')
        self.data[key] = value


def remove_tags(html):
    return re.sub('<.*?>', '', html)


def split_by_tag(soup: BeautifulSoup, tag: str = 'h1') -> List[BeautifulSoup]:
    """
    Splits a BeautifulSoup object into sections just before each occurrence of the specified tag.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object to split.
        tag (str): The tag name to split the soup by (default 'h1').

    Returns:
        List[BeautifulSoup]: A list of BeautifulSoup objects representing the sections split just before the specified tag.
    """
    sections = []
    current_section = []

    for element in soup:
        if isinstance(element, Tag) and element.name == tag:
            if current_section:
                sections.append(BeautifulSoup(''.join(map(str, current_section)), 'html.parser'))
                current_section = []
        if isinstance(element, Tag) or isinstance(element, NavigableString):
            current_section.append(element)

    if current_section:
        sections.append(BeautifulSoup(''.join(map(str, current_section)), 'html.parser'))

    return sections


def split_by_attr(soup: BeautifulSoup, attrs: Dict[str, str]) -> List[BeautifulSoup]:
    """
        Splits a BeautifulSoup object into sections just before each specified attribute(s).

        Args:
            soup (BeautifulSoup): A BeautifulSoup object to split.
            attrs (Dict[str, str]): A dictionary of attribute(s) to split the soup by.

        Returns:
            List[BeautifulSoup]: A list of BeautifulSoup objects representing the sections split just before the tag(s) with the specified attribute(s).
        """
    def dfs(soup: PageElement, attrs: Dict[str, str]):
        """
        Performs a depth-first search to split the soup object into sections based on the specified attribute(s).

        Args:
            soup (PageElement): The current BeautifulSoup PageElement to traverse.
            attrs (Dict[str, str]): A dictionary of attribute(s) to split the soup by.
        """
        nonlocal current_section, sections
        for element in soup.children:
            if (isinstance(element, Tag) and
                    all(
                        element.get(attr) == value if attr != 'class'
                        else element.get('class') == value.split()
                        for attr, value in attrs.items()
                    )):
                if current_section:
                    sections.append(BeautifulSoup(''.join(map(str, current_section)), 'html.parser'))
                    current_section = []
            if isinstance(element, Tag) or isinstance(element, NavigableString):
                current_section.append(element)
            if isinstance(element, Tag):
                dfs(element, attrs)

    sections = []
    current_section = []
    dfs(soup, attrs)

    if current_section:
        sections.append(BeautifulSoup(''.join(map(str, current_section)), 'html.parser'))

    return sections


def soup_from_strings(elements: List[str]) -> BeautifulSoup:  # deprecated
    """
    Create a BeautifulSoup object from a list of strings.

    Args:
        elements (List[str]): A list of HTML strings.

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the parsed HTML.
    """
    html = ''.join(map(str, elements))
    soup = BeautifulSoup(html, 'html.parser')
    return soup
