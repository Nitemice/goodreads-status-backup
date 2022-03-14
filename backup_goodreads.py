#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""A script for backing up your Goodreads statuses."""

import argparse
import itertools
import json
import re
import os
from datetime import datetime

from bs4 import BeautifulSoup
import requests


def read_config():
    """Returns configuration for using the script.

    Configuration is read from one of two places:
     1. Command-line arguments
     2. A config file

    Command-line arguments take precedence over config file values.  If the
    config file is empty/missing, the command-line switches are required.

    """
    # Attempt to read config from the config file.
    # We will use this if there is no command-line argument.
    user_id = None
    try:
        with open("config.json", "r") as config_file:
            config_data = json.load(config_file)
            user_id = config_data.user_id
    except FileNotFoundError:
        pass

    parser = argparse.ArgumentParser(
        description='A script to back up status data from Goodreads.')

    parser.add_argument('-o',
                        '--output',
                        default=os.getcwd(),
                        help='output path for backup files')
    parser.add_argument('--user-id',
                        required=(user_id is None),
                        help='Goodreads user ID')

    config = vars(parser.parse_args())

    if config['user_id'] is None:
        config['user_id'] = user_id

    return config


def convert_date_from_page(element):
    """Convert a date string from the Goodreads statuses page into an ISO-8601
     string."""
    date_str = convert_body(element)
    # On the statuses page, dates are returned in the form:
    # "Oct 24, 2016 12:26PM"
    date_obj = datetime.strptime(date_str, '%b %d, %Y %I:%M%p')
    return str(date_obj)


def convert_page_count(element):
    try:
        return int(element.text)
    except TypeError:
        return None


def convert_body(element):
    return element.text.strip()


def convert_status_body(element):
    # Extract status text, complete with any line-breaks
    return ''.join(map(str, element.contents)).strip()


def _get_data_from_goodreads_site(user_id, page_no):
    """Retrieve data about the statuses of a given user from the Goodreads site.
    Returns a Request object if successful, raises an Exception if not.

    :param user_id: The ID of the Goodreads user.
    :param page_no: Which page of statuses to fetch.

    """
    # user_status.list gets all the statuses by a user.
    req = requests.get('https://www.goodreads.com/user_status/list/' + user_id,
                       params={'page': str(page_no)})
    if req.status_code != 200:
        raise Exception('Unexpected error code from Goodreads API: %s\n'
                        'Error message: %r' % (req.status_code, req.text))
    return req


def _extract_status_from_element(element):
    """Retrieve status information from HTML of Goodreads page.
    Parses HTML elements to extract relevant data.

    :param element: a single status, in HTML format.

    """
    status = {}

    # The Goodreads statuses page returns status information in the following format:
    #
    # <USER PHOTO>
    # <CONTENT>
    # <BOOK COVER>
    # <br/>

    content = element.div.find('div', {'class': 'left'})

    # This retrieves an element that should be structured as follows:
    # <div class="left" style="float: left; width: 495px;">
    #
    #     <span class="uitext greyText inlineblock stacked user_status_header">
    #       <a href="/user/show/1234-johnsmith">John Smith</a>
    #       is on page 18 of 216 of <a href="https://www.goodreads.com/book/show/11.The_Hitchhiker_s_Guide_to_the_Galaxy" rel="nofollow">The Hitchhiker's Guide to the Galaxy</a>
    #     </span>
    #
    #     <div class="readable body">
    #       I like reading!
    #     </div>
    #
    #     <span class="greyText uitext smallText">
    #       — <a class="greyText" href="/user_status/show/12402">Sep 06, 2008 05:25AM</a>
    #     </span>
    #     <a class="right actionLink" href="/user_status/show/12402">1 comment</a>
    #
    #   </div>

    status['status'] = convert_status_body(
        content.find('div', {'class': 'readable body'}))

    date_id_element = content.find('span', {
        'class': 'greyText uitext smallText'
    }).a
    status['date'] = convert_date_from_page(date_id_element)
    status['status_id'] = date_id_element['href'].split('/')[-1]

    progress_element = content.find('span', {'class': 'user_status_header'})
    book_title_link = progress_element.find('a', {'rel': 'nofollow'})
    status['book_title'] = convert_body(book_title_link)
    status['book_id'] = re.split('[-.]',
                                 book_title_link['href'].split('/')[-1])[0]

    # The progress string can be in one of four formats:
    # 1: User is Z% done with Book_Title
    # 2: User is on page X of Y of Book_Title
    # 3: User is reading Book_Title
    # 4: User is finished with Book_Title
    #
    # If we get #1, we know the percentage, but we don't have any page number info.
    # If we get #2, we can calculate the percentage from the page number info.
    # If we get #3, we can assume no progress yet (0% done).
    # If we get #4, we know they're finished, so 100% done.
    progress_text = convert_body(progress_element)
    progress_values = re.search(
        '.* is (?:on page )?(\d*%?) (?:of (\d*) of|done with) .*',
        progress_text, re.S)

    if not progress_values:
        if 'finished' in progress_text:
            # Format #4
            status['percentage'] = 100
        else:
            # Format #3
            status['percentage'] = 0
    elif progress_values.group(1)[-1] == '%':
        # Format #1
        status['percentage'] = int(progress_values.group(1)[:-1])
    else:
        # Format #2
        status['page_no'] = int(progress_values.group(1))
        status['total_pages'] = int(progress_values.group(2))
        status['percentage'] = int(
            int(status['page_no']) / int(status['total_pages']) * 100)

    return status


def get_statuses(user_id):
    """Generate statuses associated with a Goodreads user.

    :param user_id: The ID of the Goodreads user.

    """
    page_no = itertools.count()

    # Get an initial page, so we know how many statuses there are to get
    req = _get_data_from_goodreads_site(user_id=user_id, page_no=next(page_no))
    soup = BeautifulSoup(req.text, "html.parser")

    # The status count should be at the top of the page in the following format:
    # "Showing 1-30 of 123"
    # We only need the total count.
    page_count_text = soup.find("span", {"class": "smallText"}).string.strip()
    total_status_count = int(page_count_text.split()[-1])

    statuses = []

    # Iterate til we have all the statuses
    while len(statuses) < total_status_count:
        req = _get_data_from_goodreads_site(user_id=user_id,
                                            page_no=next(page_no))
        soup = BeautifulSoup(req.text, "html.parser")

        # Extract all statuses from this page
        status_elements = soup.findAll("div", {"class": "elementList"})
        for element in status_elements:
            # Convert status HTML to dictionary
            statuses.append(_extract_status_from_element(element))

    return statuses


def _dump_json_to_disk(data, output_dir, filename):
    """Write data to disk as JSON file.

    :param data: The data to dump to file.
    :param output_dir: The directory where the file will be created.
    :param filename: The name of the output file.

    """
    json_str = json.dumps(data, indent=2, sort_keys=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_str)


def write_statuses_to_disk(statuses, output_dir):
    """Writes status data to disk as JSON file.

    :param statuses: The status data to dump to file.
    :param output_dir: The directory where the file will be created.

    """
    _dump_json_to_disk(statuses, output_dir, 'goodreads_statuses.json')


def main():
    cfg = read_config()
    """Parse the Goodreads site and grab all statuses."""
    statuses = get_statuses(cfg['user_id'])
    write_statuses_to_disk(statuses, cfg['output'])


if __name__ == '__main__':
    main()
