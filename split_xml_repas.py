#!/usr/bin/python3

""" 
Split a big xml file with a lot of repas to multiples xml with one repas
per file 
"""

import xml.dom.minidom
import sys

# perhaps the XML file must have a <root> element. 

with open(sys.argv[1]) as f:
    xml_datas = f.read()

dom = xml.dom.minidom.parseString(xml_datas)

repas = dom.getElementsByTagName('repas')
for d in repas:
    offset = int(d.getAttribute('offset'))
    type_ = d.getAttribute('type').replace('é','e')
    filename = '{:02d}'.format(offset)+type_.replace(' ','-')+'.xml'
    with open(filename, 'w') as f:
        f.write(d.toxml())
