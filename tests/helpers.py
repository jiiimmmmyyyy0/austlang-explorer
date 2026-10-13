"""Small helpers shared by the tests."""
from explorer.models import Language


def make_language(code="X1", name="Testname", lat=None, lon=None,
                  alternatives=(), states=(), estimated=None):
    """Build a Language quickly inside a test (all values are synthetic)."""
    return Language(
        code=code,
        name=name,
        alternative_names=tuple(alternatives),
        latitude=lat,
        longitude=lon,
        states=tuple(states),
        estimated_state=estimated,
    )
