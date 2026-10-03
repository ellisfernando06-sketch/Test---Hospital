# -*- coding: utf-8 -*-
EXAMENES = {}
try:
    from cert_examenes_p0 import PART as _p0
    EXAMENES.update(_p0)
except Exception:
    pass
try:
    from cert_examenes_p1 import PART as _p1
    EXAMENES.update(_p1)
except Exception:
    pass
try:
    from cert_examenes_p2 import PART as _p2
    EXAMENES.update(_p2)
except Exception:
    pass
