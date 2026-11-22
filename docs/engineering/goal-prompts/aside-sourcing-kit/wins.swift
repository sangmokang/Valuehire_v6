import CoreGraphics
let l = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as! [[String:Any]]
for w in l { if let o = w["kCGWindowOwnerName"] as? String, o.contains("Aside") { let b = w["kCGWindowBounds"] as? [String:Any] ?? [:]; print(w["kCGWindowNumber"]!, w["kCGWindowName"] ?? "", w["kCGWindowLayer"]!, w["kCGWindowIsOnscreen"] ?? "", b["Width"] ?? "", b["Height"] ?? "") } }
