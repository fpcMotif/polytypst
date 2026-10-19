#set page(width: auto, height: auto, margin: 0pt)
#set text(
  font: (sys.inputs.at("font"), "STIX Two Text", "STIX Two Math"),
  size: float(sys.inputs.at("size")) * 1pt,
  weight: int(sys.inputs.at("weight")),
  number-type: "lining",
)
#include sys.inputs.at("snippet")
