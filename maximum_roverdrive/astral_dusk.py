"""
    incredibly simple function to determine if it's dark by using
    latitude, longitude, elevation, and (implicitly) time
 """

from astral import Observer
from astral.sun import elevation

_DUSK_ELEVATION = -6.0


def is_dark(lat, lng, alt=0):
    obs = Observer(lat, lng, alt)
    if elevation(obs) < _DUSK_ELEVATION:
        return True
    else:
        return False
