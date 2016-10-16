import re
import requests

from bs4 import BeautifulSoup


# since we are only dealing with the form, we and include the
# unchanged part of the path in the BASE_URL, otherwise, it
# should only be the host 'http://isa.epfl.ch/'
BASE_URL = 'http://isa.epfl.ch/imoniteur_ISAP/!GEDPUBLICREPORTS'

# header dict for our URL extracted postman
# Use Postman to catch headers for one fetch, then we can use
# this header for further use
# 'refer' field is removed though
HEADERS = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) \
     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4',
    'Cookie': 'LANGUE_LOGIN=en; _gat=1; __utmt_epfl=1; __utmb=33657086.4.10.1476264841; \
     __utma=33657086.1815151521.1470316729.1476270997.1476275339.60; __utmc=33657086; \
     __utmz=33657086.1476270997.59.21.utmcsr=google|utmccn=(organic)|utmcmd=organic| \
     utmctr=(not%20provided); _ga=GA1.2.1815151521.1470316729; _gat_epfl=1; \
     _ga=GA1.2.1815151521.1470316729; __utma=33657086.1815151521.1470316729.1476275339.1476295350.61;\
     __utmc=33657086; __utmz=33657086.1476270997.59.21.utmcsr=google|utmccn=(organic)| \
     utmcmd=organic|utmctr=(not%20provided)',
    'Cache-Control': 'no-cache',
}

# We pre-defined some values because they are invariants among all
# requests: such as we always get HMTL format result, which leads
# to report_model always to be some preset value
DEFAULT_PARAMS = {
    'ww_i_reportmodel': 133685247,
    'ww_i_reportModelXsl': 133685270,
    'ww_b_list': 1
}

# we map our function paramater names to HTTP request parameter names
# so we don't need to hard-code parameter names
NAME_MAP = {
    'unit': 'ww_x_UNITE_ACAD',
    'academic_year': 'ww_x_PERIODE_ACAD',
    'period': 'ww_x_PERIODE_PEDAGO',
    'semester_type': 'ww_x_HIVERETE'
}

# column index of student table
# to reduce hard-code columns in code
COLUMN_INDEX = {
    'gender': 0,
    'name': 1,
    'specialization': 4,
    'minor': 6,
    'status': 7,
    'sciper': 10
}

# periods that we care about
BACHELOR_PERIODS = [
    'Bachelor semestre 1',
    'Bachelor semestre 2',
    'Bachelor semestre 3',
    'Bachelor semestre 4',
    'Bachelor semestre 5',
    'Bachelor semestre 6'
]

MASTER_PERIODS = [
    'Master semestre 1',
    'Master semestre 2',
    'Master semestre 3',
    'Projet Master automne',
    'Projet Master printemps',
]

def get_filter_value():
    """
    get all option values, i.e. ww_x_* code for further search
    we do this one-time query and store it in a variable so that
    we don't need to query the code for each condition

    return:
        dict: a nested dict containing all options for 4 selects
    """

    url = BASE_URL + '.filter'

    filter_values = {}

    # remove ww_b_list from params, otherwise all filters will be returned
    new_param = DEFAULT_PARAMS.copy()
    new_param.pop('ww_b_list')
    res = requests.get(url, headers=HEADERS, params=new_param)
    html = BeautifulSoup(res.text,'lxml')
    # get all values for all options in 4 select tags
    for dict_name, html_name in NAME_MAP.items():
        # find all options first
        options = html.find('select', {'name': html_name}).find_all('option')
        # key is select tag name, i.e. names of unit/period, value is the value field in the tag
        option_dict = {option.string: option['value'] for option in options if option.string}
        filter_values[dict_name] = option_dict

    return filter_values


def get_GPS_code(filter_values, **filters):
    """
    get GPS code for further fetching student table
    GPS code field will be used in next HTTP query to get student list

    Params:
        filter_values (dict): containing all numbers for each select
        filters (dict): containing potential params of filters
    Potential params are following:
        unit (string): academic unit, e.g. Informatique
        academic_year (string): target academic year, e.g. 2016-2017
        period (string): target period, e.g. bachelor semestre 1
        semester_type (string): autumn or spring semester
    """
    url = BASE_URL + '.filter'
    codes = {}

    params = DEFAULT_PARAMS.copy()
    if filters:  # at least one filter is specified
        for k, v in filters.items():
            params[NAME_MAP[k]] = filter_values[k][v]

        res = requests.get(url, headers=HEADERS, params=params)
        html = BeautifulSoup(res.text,'lxml')
        gps_elements = html.find_all('a', class_='ww_x_GPS')

        for e in gps_elements[1:]:  # remove the first one, Tous
            try:
                # extract GPS number
                codes[e.string] = re.findall('ww_x_GPS=(\d+)', e['onclick'])[0]
            except:
                print('No GPS code found')
    return codes


def get_student_table(gps_codes):
    """
    fetch student table with gps codes

    params:
        gps_codes (dict): containing gps codes for target student list

    return (dict): containing all students info according to gps_codes
                    keys are the same as gps_codes, values are a list of student
                    info, which is a dict for each student
    """
    url = BASE_URL + '.html'
    student_tables = {}

    for name, code in gps_codes.items():
        params = DEFAULT_PARAMS.copy()
        # add gps code to request parameter
        params.update({'ww_x_GPS': code})
        res = requests.get(url, headers=HEADERS, params=params)
        html = BeautifulSoup(res.text,'lxml')

        student_table = html.find('table').find_all('tr')[2:]  # remove first two header rows
        stduent_list = []

        for student in student_table:
            columns = student.find_all('td')
            student_info = {}  # info about one person is stored as a dict
            for col_name, col_index in COLUMN_INDEX.items():
                student_info[col_name] = columns[col_index].string
                if student_info[col_name]:  # replace unicode space character with space
                    student_info[col_name] = student_info[col_name].replace('\xa0', ' ')
                else:
                    student_info[col_name] = ''  # avoid None
            stduent_list.append(student_info)  # a list of all people under current filters

        student_tables[name] = stduent_list
    return student_tables


def get_all_student_list(stu_type):
    # check input parameter
    if stu_type not in ['bachelor', 'master']:
        print('Not a valid student type')
        return None

    filter_values = get_filter_value()
    gps_codes = {}
    periods = BACHELOR_PERIODS if stu_type == 'bachelor' else MASTER_PERIODS

    for p in periods:
        # get all gps codes for one period could save some network requests
        # so we don't specify academic_year here
        temp_gps = get_GPS_code(filter_values, unit='Informatique', period=p)
        for k in list(temp_gps.keys()):
            # temp_gps' keys would be like 'Informatique, 2007-2008, Bachelor semestre 2'
            # so split the key into three parts by ', ', then split the second part by '-'
            # finally we could use the first year to find out if it's later than 2007
            # remove undesirable ones
            if k.split(', ')[1].split('-')[0] < '2007':
                temp_gps.pop(k)
        gps_codes.update(temp_gps)

    return get_student_table(gps_codes)
