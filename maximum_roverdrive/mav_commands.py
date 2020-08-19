"""
one stop shop for a subset of mavlink messages to send or save in waypoint files
duplicates some functionality from pymavlink, but abstracts away some ambiguity
using the classes below as templates, it should be easy to expose more commands
"""
from inspect import getmembers
from pymavlink.dialects.v10 import ardupilotmega as mavlink1
from pymavlink.dialects.v20 import common as mavlink2


# perhaps not the most elegant way to do things (globals), but allows use-case syntax to remain consistent
_listen_for_response = False  # if another module is grabbing messages, ACKs are unreliable here
#                               use is_listening() property to change value
_connection = None
_location = None
dialect = mavlink2
_timeout = 0.5

MAVLINK_VERSION = 2  # assume we have MAVlink 2 until proven otherwise
MAV_CMD_DO_LIST = list(filter(lambda cmd: 'MAV_CMD_DO' in cmd, [name for name, obj in getmembers(mavlink2)]))
MODES = None


def init(mavlink):
    global _connection
    global _location
    global dialect
    global _timeout
    global MODES
    global MAV_CMD_DO_LIST
    global MAVLINK_VERSION
    _connection = mavlink.connection
    _location = mavlink.location
    # TODO: determine if setting the dialect environment variable is appropriate
    MavlinkCommandLong(dialect.MAV_CMD_REQUEST_MESSAGE,
                       [dialect.MAVLINK_MSG_ID_AUTOPILOT_VERSION]).send()
    msg = _connection.recv_match(type='AUTOPILOT_VERSION', blocking=True, timeout=_timeout)
    if getattr(msg, 'capabilities') & dialect.MAV_PROTOCOL_CAPABILITY_MAVLINK2 < 2:
        dialect = mavlink1
        MAVLINK_VERSION = 1
        MAV_CMD_DO_LIST = list(filter(lambda cmd: 'MAV_CMD_DO' in cmd, [name for name, obj in getmembers(mavlink1)]))
    msg = _connection.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)  # heartbeat is only transmitted at 1Hz
    MAVLINK_VERSION += getattr(msg, 'mavlink_version') / 10
    MODES = _connection.mode_mapping().keys()


class MavlinkCommandLong:
    global _connection
    global _timeout
    global _listen_for_response

    def __init__(self, command=None, args=None):
        if command is None:
            return
        self._is_listening = _listen_for_response
        self._command = command
        self.args = [0, 0, 0, 0, 0, 0, 0]
        for x in range(7):
            try:
                self.args[x] = args[x]
            except (TypeError, IndexError):
                pass

    def description(self):
        # TODO: fully implement this in the UI
        return 'Send a custom MAVLink command'

    def to_waypoint_command_string(self, waypoint_number=0, is_home=False):
        if is_home:
            val = '0\t1\t0\t16'
        else:
            val = f'{waypoint_number}\t0\t3\t{self._command}'
        for arg in self.args:
            arg = str(arg)
            val += f'\t{arg}'
        return f'{val}\t1'

    """ default method send() is a fully composed command_long message
        child classes should override this with pymavlink native methods when available """
    def send(self):
        _connection.mav.command_long_send(_connection.target_system, _connection.target_component,
                                          self._command, 0, self.args[0], self.args[1], self.args[2],
                                          self.args[3], self.args[4], self.args[5], self.args[6])
        return self._response()

    def _response(self):
        if not self._is_listening:
            return
        ack = _connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=_timeout)
        try:
            if getattr(ack, 'command') == self._command and getattr(ack, 'result') == 0:
                return True
        except AttributeError:
            return False
        return False

    @property
    def is_listening(self):
        return self._is_listening

    @is_listening.setter
    def is_listening(self, listen):
        self._is_listening = listen


class ARM(MavlinkCommandLong):
    global _connection
    global dialect

    def __init__(self):
        super(ARM, self).__init__(dialect.MAV_CMD_COMPONENT_ARM_DISARM, [1])

    def description(self):
        return 'Arm the system\n\n(no arguments)'

    def send(self):
        _connection.arducopter_arm()
        return self._response()


class DISARM(MavlinkCommandLong):
    global _connection
    global dialect

    def __init__(self):
        super(DISARM, self).__init__(dialect.MAV_CMD_COMPONENT_ARM_DISARM, [0])

    def description(self):
        return 'Disarm the system\n\n(no arguments)'

    def send(self):
        _connection.arducopter_disarm()
        return self._response()


class REBOOT(MavlinkCommandLong):
    global _connection
    global dialect

    def __init__(self):
        super(REBOOT, self).__init__(dialect.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN)

    def description(self):
        return 'Reboot the system\n\n(no arguments)'

    def send(self):
        _connection.reboot_autopilot()
        return self._response()


class SET_MODE(MavlinkCommandLong):
    global _connection
    global dialect

    def __init__(self, mode=None):
        try:
            self.mode = mode if isinstance(mode, int) else _connection.mode_mapping()[mode]
            super(SET_MODE, self).__init__(dialect.MAV_CMD_DO_SET_MODE, [self.mode])
        except (AttributeError, KeyError):
            pass

    def description(self):
        return 'Set flight mode\n\n(arg: mode)'

    def send(self):
        _connection.set_mode(self.mode)
        return self._response()


class SET_RELAY(MavlinkCommandLong):
    global _connection
    global dialect

    def __init__(self, relay=None, state=None):
        super(SET_RELAY, self).__init__(dialect.MAV_CMD_DO_SET_RELAY, [relay, state])
        self.relay = relay
        self.state = state

    def description(self):
        return 'Set relay state\n\n(args: relay, state)'

    def send(self):
        _connection.set_relay(self.relay, self.state)
        return self._response()


class SET_HOME(MavlinkCommandLong):
    global _connection
    global dialect

    def __init__(self, lat=None, lng=None, alt=0):
        try:
            if lat is None or lng is None:
                lat = _location.lat
                lng = _location.lng
        except AttributeError:
            pass
        super(SET_HOME, self).__init__(dialect.MAV_CMD_DO_SET_HOME, [0, 0, 0, 0, lat, lng, alt])

    def description(self):
        return 'Set home position\n\n(args: lat, lng, alt)\n\nUse current position if blank'
