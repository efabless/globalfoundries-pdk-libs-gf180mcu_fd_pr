import gdsfactory as gf
import pya
import os

def gf_to_pya(layout, c: gf.Component, device_name: str):
    c.write_gds(str(device_name) + "_temp.gds")
    layout.read(str(device_name) + "_temp.gds")
    os.remove(str(device_name) + "_temp.gds")

    return layout.cell(c.name)