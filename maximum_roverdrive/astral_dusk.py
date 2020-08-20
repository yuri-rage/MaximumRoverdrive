"""
    incredibly simple function to determine if it's dark by using
    latitude, longitude, elevation, and (implicitly) time
 """

from astral import Observer
from astral.sun import elevation


def is_dark(lat, lng, alt=0):
    obs = Observer(lat, lng, alt)
    if elevation(obs) < -6.0:
        return True
    else:
        return False
