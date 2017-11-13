Desc = cellDescClass("NOR2BX4")
Desc.properties["cell_leakage_power"] = "1328.275422"
Desc.properties["cell_footprint"] = "nor2b"
Desc.properties["area"] = "26.611200"
Desc.pinOrder = ['AN', 'B', 'Y']
Desc.add_arc("AN","Y","combi")
Desc.add_arc("B","Y","combi")
Desc.add_param("area",26.611200);
Desc.add_pin("Y","output")
Desc.add_pin_func("Y","unknown")
Desc.add_pin("B","input")
Desc.add_pin("AN","input")
CellLib["NOR2BX4"]=Desc
