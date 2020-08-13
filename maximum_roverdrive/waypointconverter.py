from enum import Enum


class Filetype(Enum):
    waypoint = 0
    poly = 1


class BadFileFormat(Exception):
    pass


class WaypointConverter:
    """ converts files between Mission Planner waypoint and poly files """
    def __init__(self, filename=None, home_lat=33.44, home_lng=-112.0, default_altitude=30.48):
        if filename is None:
            pass  # allow instantiation of "empty" class
        else:
            self._error = None
            self._filename = filename
            self._home_lat = 33.44 if home_lat is None else home_lat  # defaults to PHX Sky Harbor...cuz why not?
            self._home_lng = -112.0 if home_lng is None else home_lng
            self._default_altitude = 30.48 if home_lng is None else default_altitude  # defaults to 30.48m (100')
            try:
                self._filetype = self.__read_file(self._filename)
            except FileNotFoundError:
                self._error = FileNotFoundError
                return
            except BadFileFormat:
                self._error = BadFileFormat
                return
            if self._filetype == Filetype.waypoint:
                self._output_filename = self._filename.split('.')[0] + '_PY.poly'
                self.__make_poly_file()
            else:
                self._output_filename = self._filename.split('.')[0] + '_PY.waypoints'
                self.__make_wp_file()

    def __read_file(self, filename):
        with open(filename, "r") as f:  # TODO: debug context manager to make sure it works as expected
            self._lines = f.readlines()
        if len(self._lines) < 2:  # any file worth processing needs more lines
            raise BadFileFormat
        if (len(self._lines[1].split())) == 2:     # poly files just list lat/long
            return Filetype.poly
        elif (len(self._lines[1].split())) == 12:  # wp files have 12 fields
            return Filetype.waypoint
        raise BadFileFormat  # should have returned by now, so file is bad

    def __make_poly_file(self):
        f = open(self._output_filename, "w")
        del self._lines[0]  # eliminate comment/version(?) line
        del self._lines[0]  # eliminate home waypoint
        output_lines = ['# auto-generated by Python WaypointConverter\n']
        for line in self._lines:
            line = line.split()
            try:
                if line[3] == '16':  # command 16 is waypoint - ignore all others
                    output_lines.append(line[8] + ' ' + line[9] + '\n')
            except IndexError:  # happens on newlines near EOF (or badly formatted lines)
                pass
        f.writelines(output_lines)
        f.close()

    def __make_wp_file(self):
        f = open(self._output_filename, "w")
        del self._lines[0]  # eliminate comment line
        output_lines = ['QGC WPL 110\n',  # Mission Planner writes this QGC line, so let's do so, too
                        f'0\t1\t0\t16\t0\t0\t0\t0\t'
                        f'{self._home_lat}\t{self._home_lng}\t0\t1\n']
        wp_number = 1
        for line in self._lines:
            line = line.split()
            try:
                # formatted string looks wild, but it's just a bunch of tab delimiters
                output_lines.append(f'{wp_number}\t0\t3\t16\t0\t0\t0\t0\t'
                                    f'{line[0]}\t{line[1]}\t{self._default_altitude}\t1\n')
                wp_number += 1
            except IndexError:  # happens on newlines near EOF (or badly formatted lines)
                pass
        f.writelines(output_lines)
        f.close()
        # TODO: allow for addition of start/stop mission commands for relay control to offload Pixhawk scripts

    def convert(self, filename, home_lat=33.44, home_lng=-112.0, default_altitude=30.48):
        """ allow for additional file conversion without re-instantiation """
        self.__init__(filename, home_lat, home_lng, default_altitude)

    @property
    def output_filename(self):
        return self._output_filename

    @property
    def error(self):
        return self._error
