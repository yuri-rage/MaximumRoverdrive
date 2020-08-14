"""
one stop shop for a subset of mavlink messages to send or save in waypoint files
duplicates some functionality from pymavlink, but abstracts away some ambiguity
using the classes below as templates, it should be easy to provide access to more commands
"""
from pymavlink.dialects.v10 import ardupilotmega as mavlink1
from pymavlink.dialects.v20 import common as mavlink2

_connection = None
_dialect = mavlink2
_timeout = 0.5
MODES = None


def init(mavlink_connection):
    global _connection
    global _dialect
    global _timeout
    global MODES
    _connection = mavlink_connection
    # TODO: determine if setting the dialect environment variable is appropriate
    MavlinkCommandLong(_dialect.MAV_CMD_REQUEST_MESSAGE,
                       [_dialect.MAVLINK_MSG_ID_AUTOPILOT_VERSION]).send()
    msg = _connection.recv_match(type='AUTOPILOT_VERSION', blocking=True, timeout=_timeout)
    if getattr(msg, 'capabilities') & _dialect.MAV_PROTOCOL_CAPABILITY_MAVLINK2 < 2:
        _dialect = mavlink1
    MODES = _connection.mode_mapping().keys()


class MavlinkCommandLong:
    global _connection
    global _timeout

    def __init__(self, command=None, args=None):
        if command is None:
            return
        self._command = command
        self.args = [0, 0, 0, 0, 0, 0, 0]
        for x in range(7):
            try:
                self.args[x] = args[x]
            except (TypeError, IndexError):
                pass

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
        ack = _connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=_timeout)
        try:
            if getattr(ack, 'command') == self._command and getattr(ack, 'result') == 0:
                return True
        except AttributeError:
            return False
        return False


class ARM(MavlinkCommandLong):
    global _connection
    global _dialect

    def __init__(self):
        super(ARM, self).__init__(_dialect.MAV_CMD_COMPONENT_ARM_DISARM, [1])

    def send(self):
        _connection.arducopter_arm()
        return self._response()


class DISARM(MavlinkCommandLong):
    global _connection
    global _dialect

    def __init__(self):
        super(DISARM, self).__init__(_dialect.MAV_CMD_COMPONENT_ARM_DISARM, [0])

    def send(self):
        _connection.arducopter_disarm()
        return self._response()


class REBOOT(MavlinkCommandLong):
    global _connection
    global _dialect

    def __init__(self):
        super(REBOOT, self).__init__(_dialect.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN)

    def send(self):
        _connection.reboot_autopilot()
        return self._response()


class SET_MODE(MavlinkCommandLong):
    global _connection
    global _dialect

    def __init__(self, mode):
        self.mode = mode if isinstance(mode, int) else _connection.mode_mapping()[mode]
        super(SET_MODE, self).__init__(_dialect.MAV_CMD_DO_SET_MODE, [self.mode])

    def send(self):
        _connection.set_mode(self.mode)
        return self._response()


class SET_RELAY(MavlinkCommandLong):
    global _connection
    global _dialect

    def __init__(self, relay, state):
        super(SET_RELAY, self).__init__(_dialect.MAV_CMD_DO_SET_RELAY, [relay, state])
        self.relay = relay
        self.state = state

    def send(self):
        _connection.set_relay(self.relay, self.state)
        return self._response()


class SET_HOME(MavlinkCommandLong):
    global _connection
    global _dialect

    def __init__(self, lat=None, lng=None, alt=0):
        if lat is None:
            lat = _connection.location().lat
        if lng is None:
            lng = _connection.location().lng
        super(SET_HOME, self).__init__(_dialect.MAV_CMD_DO_SET_HOME, [0, 0, 0, 0, lat, lng, alt])
