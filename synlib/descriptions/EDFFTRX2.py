Desc = cellDescClass("EDFFTRX2")
Desc.properties["cell_leakage_power"] = "2329.294320"
Desc.properties["cell_footprint"] = "edfftr"
Desc.properties["area"] = "89.812800"
Desc.pinOrder = ['CK', 'D', 'E', 'IQ', 'IQN', 'Q', 'QN', 'RN', 'next']
Desc.add_arc("CK","D","setup_rising")
Desc.add_arc("CK","D","hold_rising")
Desc.add_arc("CK","E","setup_rising")
Desc.add_arc("CK","E","hold_rising")
Desc.add_arc("CK","RN","setup_rising")
Desc.add_arc("CK","RN","hold_rising")
Desc.add_arc("CK","Q","rising_edge")
Desc.add_arc("CK","QN","rising_edge")
Desc.add_param("area",89.812800);
Desc.set_pin_job("CK","clock")
Desc.add_pin("CK","input")
Desc.add_pin("E","input")
Desc.add_pin("D","input")
Desc.add_pin("IQ","output")
Desc.add_pin_func("IQ","unknown")
Desc.add_pin("next","output")
Desc.add_pin_func("next","unknown")
Desc.add_pin("Q","output")
Desc.add_pin_func("Q","unknown")
Desc.add_pin("IQN","output")
Desc.add_pin_func("IQN","unknown")
Desc.add_pin("RN","input")
Desc.add_pin("QN","output")
Desc.add_pin_func("QN","unknown")
Desc.set_job("flipflop")
CellLib["EDFFTRX2"]=Desc
