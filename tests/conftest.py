import os
import pytest

from openswallow import open_api


@pytest.fixture
def open_apis(request):
    d = os.path.join(os.path.dirname(__file__), 'data')
    output = []
    for sd in os.listdir(d):
        sd = os.path.join(d, sd)
        for fn in os.listdir(sd):
            ext = fn.split('.')[-1].lower()
            if ext in ('json', ):
                with open(
                    os.path.join(sd, fn),
                    mode='r',
                    encoding='utf-8'
                ) as f:
                    output.append(open_api(f))
    return tuple(output)