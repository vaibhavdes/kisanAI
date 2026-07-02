from common import print_ok, require_package

require_package("ee", "pip install -r requirements-google.txt && earthengine authenticate")

import ee


ee.Initialize()
point = ee.Geometry.Point([75.299, 21.245])
buffer = point.buffer(500)
area = buffer.area().getInfo()
print_ok(f"Earth Engine initialized. Demo buffer area: {round(area)} sq m")

