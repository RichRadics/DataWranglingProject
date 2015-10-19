# Import required libraries
import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import codecs
import json

# Declare globals
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
### DOCNOTE regex below taken from http://stackoverflow.com/questions/164979/uk-postcode-regex-comprehensive, answer provided by Colin
### DOCNOTE tested with regex101.com
postcode_re = re.compile(r'^(GIR ?0AA|[A-PR-UWYZ]([0-9]{1,2}|([A-HK-Y][0-9]([0-9ABEHMNPRV-Y])?)|[0-9][A-HJKPS-UW]) ?[0-9][ABD-HJLNP-UW-Z]{2})$')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
## DOCNOTE : Added close/terrace to View for UK addresses
expectedStreetTypes = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Close", "Terrace", 'Grove','Crescent', 'Way', 'Mews','View']

# Utility functions to create sample files
def get_element_for_sample(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
def create_sample_file(osm_file):
    sample_file = "{0}.sample".format(osm_file)
    with open(sample_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        # Write every 10th top level element
        for i, element in enumerate(get_element_for_sample(osm_file)):
            if i % 10 == 0:
                output.write(ET.tostring(element, encoding='utf-8'))
        output.write('</osm>')
    


# Auditing functions
def audit_street_type(in_set, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expectedStreetTypes:
            in_set.add(street_name)

def audit_postcode(in_set, postcode):
    if not postcode_re.match(postcode):
        in_set.add(postcode)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")


def audit(osmfile, audit_type = 'streetnames'):
    osm_file = open(osmfile, "r")
    res = set()
    for _ , elem in ET.iterparse(osm_file, ('start',)):
        res = res
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if audit_type=='streetnames':
                    if is_street_name(tag):
                        audit_street_type(res, tag.attrib['v'])
                if audit_type=='postcodes':
                    if is_postcode(tag):
                        audit_postcode(res,tag.attrib['v'])
        elem.clear()
    return res


# Final file processing 
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node['type']=element.tag
        for el in element.iter():
            if el.tag=='tag':
                # special tag parsing
                k = el.get('k')
                v = el.get('v')
                if not problemchars.match(k):
                    if k.startswith('addr:'):
                        addr=k.split(':')
                        if len(addr)==2:
                            if 'address' not in node: node['address']={}
                            node['address'][addr[1]]=v
                    else:
                        node[k]=v
            else:
                # 'normal' elements
                for at in el.attrib:
                    if at in CREATED:
                        if 'created' not in node: node['created']={}
                        node['created'][at]=el.get(at)
                    elif at in {'lat','lon'}:
                        if 'pos' not in node: node['pos']=[]
                        node['pos'].insert(0,float(el.get(at)))
                    elif element.tag=='way' and el.tag=='nd' and at=='ref':
                        if 'node_refs' not in node: node['node_refs']=[]
                        node['node_refs'].append(el.get(at))
                    else:
                        node[at]=el.get(at)
        #pprint.pprint( node)
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def mainImport():
    #create_sample_file('liverpool_england.osm')
    #print audit('liverpool.sample.osm')
    #process_map('liverpool_england.osm')
    print audit('liverpool_england.osm', 'postcodes')

if __name__ == "__main__":
    mainImport()
    