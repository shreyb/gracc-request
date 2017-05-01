import xml.etree.ElementTree as ET
import urllib2
import logging
import re
from copy import deepcopy


VOURL = "https://myosg.grid.iu.edu/vosummary/xml?summary_attrs_showfield_of_science=on&all_vos=on&active=on&active_value=1&oasis_value=1&sort_key=name"

class OIMVOInfo(object):
    """
    
    """
    # Put any non-nested element before the last item in this list.  The last
    # item is a dict that holds all nested elements and the structure
    wanted_attributes = ['LongName', 'Name',        # These two are examples - we don't actually need them
                         {'FieldsOfScience':        # We actually want these
                              {'PrimaryFields': 'Field',
                               'SecondaryFields': 'Field'
                               }
                          }
                         ]
    vodict = {}

    def __init__(self):
        self.xmlfile = self.__get_oim_info()
        self.__get_vo_info()

    def __get_oim_info(self):
        """
        
        :return: 
        """
        try:
            oim_xml = urllib2.urlopen(VOURL)
        except (urllib2.HTTPError, urllib2.URLError) as e:
            logging.error(e)
            return None
        return oim_xml

    def __get_vo_info(self):
        """
        
        :return: 
        """
        pathattr = re.compile('^.//(\w+)$')     # Top level elements
        pathattr_rec = re.compile('^.//.+/(\w+)/.+$')   # Nested Elements

        root = ET.parse(self.xmlfile)
        root = root.getroot()

        for voelt in root:
            VOName = voelt.find('Name').text.lower()
            if VOName not in self.vodict:
                self.vodict[VOName] = {}
            cur_dict = self.vodict[VOName]

            # Top level xpaths
            xpaths = ['.//' + attr for attr in self.wanted_attributes[:-1]]

            # Nested xpaths
            def recurse_attrs(cur_level, cur_list=[], final_list=[]):
                if not isinstance(cur_level, dict):
                    cur_list.append(cur_level)
                    final_list.append(cur_list)
                else:
                    for key in cur_level:
                        nowlist = deepcopy(cur_list)
                        nowlist.append(key)
                        recurse_attrs(cur_level[key], nowlist, final_list)
                return final_list

            xpath_list_raw = recurse_attrs(self.wanted_attributes[-1])

            xpaths.extend(['.//' + '/'.join(pathlist)
                           for pathlist in xpath_list_raw])

            # Look for info in XML file
            for path in xpaths:
                m = filter(None, (pat.match(path) for pat in (pathattr, pathattr_rec)))
                assert len(m) == 1  # One or other should be a match, not both
                if m:
                    key = m[0].group(1)
                else:
                    continue    # Skip this key
                lst = [elt.text for elt in voelt.findall(path)] # Search XML file using xpath

                if len(lst) > 1:
                    cur_dict[key] = lst  # Add to dict
                elif len(lst) == 1:
                    cur_dict[key] = lst[0]

        return

    def parse_doc(self, doc):
        """
        Parse corrected raw non-Payload doc, write VO FOS into the 
        OIM_FieldofScience field.
        
        :param dict doc:
        :return: 
        """
        if 'ResourceType' in doc and doc['ResourceType'] != 'Payload':
            if 'VOName' in doc:
                doc['OIM_FieldofScience'] = self.vodict[doc['VOName'].lower()]['PrimaryFields']

        return doc


if __name__ == '__main__':
    x = OIMVOInfo()
    # print x.vodict
    testdoc = {'VOName':'osg', 'ResourceType':'Batch'}
    print x.parse_doc(testdoc)
