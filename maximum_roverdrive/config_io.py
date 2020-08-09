from sys import float_info
from configparser import ConfigParser, NoOptionError
from collections import namedtuple


class ConfigIO:
    def __init__(self, filename=''):
        self.filename = {True: 'MAV.ini', False: filename}[len(filename) == 0]
        self.parser = ConfigParser()
        self.parser.optionxform = str  # preserve case
        self.parser.read(self.filename)
        self.__check()

    def __check(self):
        if not self.parser.has_section('ports'):
            self.parser.add_section('ports')
        self.save()

    def __values(self, section):
        """ return all values (not options) in a section """
        options = []
        for index in self.parser.options(section):
            options.append(self.parser.get(section, index))
        return options

    def add_port(self, port):
        """ add a port to the top of the ports section """
        lst = self.ports
        if lst.count(port) > 0:
            lst.remove(port)
        lst.insert(0, port)
        for option in self.parser.options('ports'):
            self.parser.remove_option('ports', option)
        for prt in lst:
            self.parser.set('ports', str(lst.index(prt)), prt)
        self.save()

    def add_msg(self, msg, attr, multiplier=1.0, low=0.0, high=0.0):
        section = msg + '.' + attr
        if section not in self.messages.keys():
            self.parser.add_section(section)
        self.parser.set(section, 'multiplier', str(multiplier))
        self.parser.set(section, 'low', str(low))
        self.parser.set(section, 'high', str(high))
        self.save()

    def del_msg(self, msg, attr):
        section = msg + '.' + attr
        if section in self.messages.keys():
            self.parser.remove_section(section)
        self.save()

    def save(self):
        f = open(self.filename, "w")
        self.parser.write(f)
        f.close()

    @property
    def ports(self):
        return self.__values('ports')

    @property
    def legacy_messages(self):  # TODO: delete this if the new one works
        sections = self.parser.sections()
        sections.remove('ports')
        return sections

    @property
    def messages(self):
        MsgParams = namedtuple('MsgParams', 'multiplier low high')
        value = {}
        params = MsgParams(0, 0, 0)
        sections = self.parser.sections()
        sections.remove('ports')
        for section in sections:
            try:
                params = params._replace(multiplier=self.parser.getfloat(section, 'multiplier'))
            except NoOptionError:
                params = params._replace(multiplier=1.0)
            try:
                params = params._replace(low=self.parser.getfloat(section, 'low'))
            except NoOptionError:
                params = params._replace(low=float_info.max * -1.0)
            try:
                params = params._replace(high=self.parser.getfloat(section, 'high'))
            except NoOptionError:
                params = params._replace(high=float_info.max)
            value.update({section: params})
        return value
