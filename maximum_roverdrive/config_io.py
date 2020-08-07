from configparser import SafeConfigParser


class ConfigIO:
    def __init__(self, filename=''):
        self.filename = {True: 'MAV.ini', False: filename}[len(filename) == 0]
        self.parser = SafeConfigParser()
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

    def save_msg_config(self, messages):
        for section in self.parser.sections():
            if not section == 'ports':
                self.parser.remove_section(section)
        for msg in messages:
            self.parser.add_section(msg[0])  # TODO: pass and save message options (thresholds, multiplier, etc)
        self.save()

    def save(self):
        f = open(self.filename, "w")
        self.parser.write(f)
        f.close()

    @property
    def ports(self):
        return self.__values('ports')

    @property
    def messages(self):
        lst = self.parser.sections()
        lst.remove('ports')
        return lst


