# -*- coding: utf-8 -*-
import os
import cairosvg
D=r"D:/06_Hermes/articles/glm53-hisparse-vllm-part1"
pairs=[("pareto-occupancy","pareto-occupancy"),("one-pool-two-requests","pool-two-requests"),("three-residency-states","residency-states")]
for svg,out in pairs:
    src=os.path.join(D,svg+".svg")
    dst=os.path.join(D,out+".png")
    cairosvg.svg2png(url=src, write_to=dst, output_width=1100, background_color="white")
    from PIL import Image
    print(out, Image.open(dst).size)
