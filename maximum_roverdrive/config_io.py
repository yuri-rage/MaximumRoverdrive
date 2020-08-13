from sys import float_info
from configparser import ConfigParser, NoOptionError
from collections import namedtuple, OrderedDict


class ConfigIO:
    _usage_str = '# MAV.ini for MaximumRoverdrive\n\n'\
                  '# ports:\n'\
                  '#     network: [protocol:]address[:port] (e.g., tcp:localhost:5760 or udp:127.0.0.1:14550)\n'\
                  '#     serial : <port>                    (e.g., com14 or /dev/ttyUSB0)\n#\n'\
                  '# preferences:\n'\
                  '#     mission_folder: <folder>             (e.g., C:\\Mission Planner\\Missions)\n' \
                  '#     home_lat: <float>  -- home latitude for waypoint files   (decimal degrees)\n'\
                  '#     home_lng: <float>  -- home longitude for waypoint files  (decimal degrees)\n'\
                  '#     default_altitude: <float>  -- default altitude for waypoint files (meters)\n#\n'\
                  '# messages:\n'\
                  '#     each section specifies a MAVLink message to monitor\n'\
                  '#     the format is [MESSAGE.attribute]  (e.g., [VFR_HUD.yaw] or [GPS_RAW_INT.fix_type])\n#\n'\
                  '#     options are indeed optional, <float> is a decimal value (e.g., 0.0 or 100.0):\n'\
                  '#         multiplier = <float>  -- displayed value will be multiplied by this value\n'\
                  '#         low = <float>         -- low threshold  - displayed value turns red below this\n'\
                  '#         high = <float>        -- high threshold - displayed value turns red above this'

    def __init__(self, filename=''):
        self.filename = {True: 'MAV.ini', False: filename}[len(filename) == 0]
        self.parser = ConfigParser(allow_no_value=True)
        self.parser.optionxform = str  # preserve case
        self.parser.read(self.filename)
        self.__check()

    def __check(self):
        # really stupid workaround because ConfigParser discards comments
        if not self.parser.has_section('usage'):
            self.parser.add_section('usage')
        self.parser.set('usage', self._usage_str, None)
        if not self.parser.has_section('ports'):
            self.parser.add_section('ports')
        if not self.parser.has_section('preferences'):
            self.parser.add_section('preferences')
        if not self.parser.has_option('preferences', 'mission_folder'):
            self.parser.set('preferences', 'mission_folder')
        if not self.parser.has_option('preferences', 'home_lat'):
            self.parser.set('preferences', 'home_lat')
        if not self.parser.has_option('preferences', 'home_lng'):
            self.parser.set('preferences', 'home_lng')
        if not self.parser.has_option('preferences', 'default_altitude'):
            self.parser.set('preferences', 'default_altitude')
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
        # really stupid workaround because ConfigParser tends to disregard section order
        ordered_sections = \
            OrderedDict([(k, None) for k in ['usage', 'ports', 'preferences'] if k in self.parser._sections])
        ordered_sections.update(self.parser._sections)
        self.parser._sections = ordered_sections
        f = open(self.filename, "w")
        self.parser.write(f)
        f.close()

    @property
    def ports(self):
        return self.__values('ports')

    @property
    def messages(self):
        MsgParams = namedtuple('MsgParams', 'multiplier low high')
        value = {}
        params = MsgParams(0, 0, 0)
        sections = self.parser.sections()
        sections.remove('ports')
        sections.remove('usage')
        sections.remove('preferences')
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

    @property
    def mission_folder(self):
        return self.parser.get('preferences', 'mission_folder')

    @mission_folder.setter
    def mission_folder(self, path):
        self.parser.set('preferences', 'mission_folder', path)
        self.save()

    @property
    def home_lat(self):
        return self.parser.get('preferences', 'home_lat')

    @property
    def home_lng(self):
        return self.parser.get('preferences', 'home_lng')

    @property
    def default_altitude(self):
        return self.parser.get('preferences', 'default_altitude')
