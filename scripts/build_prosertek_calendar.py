#!/usr/bin/env python3
r"""
Rebuild data/post_calendar.csv from www.prosertek.com positioning:
- Manufacturer of harbor equipment since 1990; global references.
- BAS / DockMoor (Dockmoor-BM, -MS, -HDT, -ER, -FP, -LD, -RR, -WEB).
- Quick release hooks (QRH), Dockmoor-RR, coatings (ISO 12944 C5-M, NORSOK M-501), capstans.
- Marine gangways, boarding bridges, port cranes, fenders, bollards.
- Services: NDT bollard tests (BollardScan, Lloyd's Register), underwater maintenance,
  Portable Pilot Unit, engineering / R+D+i, technical assistance, turnkey.

Run from repo root: python scripts/build_prosertek_calendar.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "post_calendar.csv"

# 100 unique rows; calendar repeats 5× (500 days) with cycle label on themes 101–500.
ROWS: list[tuple[str, str, str, str]] = [
    (
        "Why a Berthing Aid System (BAS) is more than a pretty mimic panel",
        "When the quay and the bridge argue, DockMoor is the shared picture worth paying for.",
        "DockMoor visualises approach and mooring in real time—distance, speed, angle—so corrective action is data-led, not anecdote-led.",
        "#Prosertek #DockMoor #BAS #Berthing #PortSafety",
    ),
    (
        "Dockmoor-BM: bow/stern speed and angle against the fender line",
        "Berthing is geometry with consequences; a scale image beats a gut feeling in squall season.",
        "BM measures ship–berth geometry to build a live manoeuvre view: alerts, history, and replay for incident learning.",
        "#DockmoorBM #Berthing #Prosertek #BAS #MarineOps",
    ),
    (
        "Dockmoor-MS: mooring stress where QRH load cells actually live",
        "Mooring lines do not fail in the spreadsheet; they fail at the hook.",
        "MS tracks rope tension, hook status, fender compression—often via load cells integrated in QRH bolts—with overload alarms operators can trust.",
        "#DockmoorMS #Mooring #QuickReleaseHooks #Prosertek #BAS",
    ),
    (
        "Dockmoor-HDT: hardware diagnostics over UDP—no poetry, just state",
        "If a device is silent on the network, it is still telling you something—usually the wrong story.",
        "HDT communicates via UDP to surface panels, lasers, load cells, loading arms, and weather kits—one diagnostic layer for the whole manoeuvre chain.",
        "#DockmoorHDT #Prosertek #BAS #Diagnostics #UDP",
    ),
    (
        "Dockmoor-ER: when the berth needs weather and sea state in the same UI",
        "Wind shifts and swell periods are part of the berthing equation, not footnotes.",
        "ER ties compact stations to wind, waves, humidity, pressure—and can extend to visibility or radiation where the facility demands it.",
        "#DockmoorER #Weather #Ports #Prosertek #BAS",
    ),
    (
        "Dockmoor-FP: fender deflection in the last approach metres",
        "A fender that looks ‘fine’ can still be storing asymmetric energy.",
        "FP archives deflection, triggers audio/visual alarms on excessive deformation, and keeps history for claims and design feedback.",
        "#DockmoorFP #Fenders #Prosertek #BAS #Berthing",
    ),
    (
        "Dockmoor-LD: loading-arm drift monitoring during mooring",
        "Hydrocarbon arms do not forgive casual geometry.",
        "LD tracks arm drift in real time with configurable alarms—measurements stay available for later analysis and reporting.",
        "#DockmoorLD #LoadingArms #LNG #Prosertek #BAS",
    ),
    (
        "Dockmoor-RR: local, remote, and emergency firing philosophy for QRH",
        "Release is a safety function; convenience must never outrank procedure.",
        "RR combines interactive monitoring of line tension and hook status with control desks for local/remote release—including emergency sequences.",
        "#DockmoorRR #QuickReleaseHooks #Prosertek #Automation #Safety",
    ),
    (
        "Dockmoor-WEB: BAS in the browser without inventing a new VPN horror story",
        "If the superintendent needs the manoeuvre on a tablet, ship it securely—not ‘just RDP to someone’s laptop’.",
        "WEB serves DockMoor over LAN or Internet to PCs, tablets, and phones—access becomes an ops decision, not an IT science project.",
        "#DockmoorWEB #Prosertek #BAS #RemoteOps #Maritime",
    ),
    (
        "From alarms to evidence: reports, replay, and past manoeuvres in DockMoor",
        "Auditors love screenshots; engineers love time-synchronized replay.",
        "BAS registers events and supports playback—turning ‘what happened?’ into a traceable narrative for insurers and internal learning.",
        "#Prosertek #DockMoor #Compliance #Ports #Operations",
    ),
    (
        "Quick release hooks: why integrated load paths beat ‘smart rope’ theatre",
        "Mooring is mechanical first; telemetry is there to protect people and steel.",
        "Prosertek QRH assemblies anchor mooring lines with remote/local release options and sensible paths for tension sensing—paired with Dockmoor-RR when automation is in scope.",
        "#QuickReleaseHooks #Prosertek #Mooring #Ports #Safety",
    ),
    (
        "QRH coatings: C5-M ISO 12944-6 and NORSOK M-501 in real project language",
        "Salt fog does not read datasheets; it reads welds and edges.",
        "Epoxy systems target abrasion, seawater, oils, and hydrocarbon spills—with C5-M / NORSOK-class options when the environment demands it.",
        "#Prosertek #QRH #Corrosion #Marine #Engineering",
    ),
    (
        "Materials honesty: cast steel hooks, rolled bases, heat-treated shafts",
        "A QRH is not a single ‘part’; it is a stack of metallurgical decisions.",
        "Prosertek publishes material splits—cast bodies/teeth, rolled structural sections, machined and heat-treated shafts—so FAT/SAT debates stay factual.",
        "#QuickReleaseHooks #Materials #Prosertek #Quality #Manufacturing",
    ),
    (
        "Capstans on QRH: pedal-activated, oil-filled reducers, hands-free line handling",
        "Hands belong on guardrails, not wrestling lines at the wrong moment.",
        "Integrated capstans favour reversible rotation, stretched drums for fairlead, and pedal control—often bundled with hook assemblies in live projects.",
        "#Capstan #Mooring #Prosertek #QRH #Operations",
    ),
    (
        "Double, triple, quadruple QRH configurations: matching tonnage to reality",
        "Catalogues sell ‘units’; berths sell ‘load cases’.",
        "Prosertek supplies multi-hook assemblies (e.g., 75–150 T-class references on major LNG and product terminals) sized to client mooring plans.",
        "#QuickReleaseHooks #Mooring #LNG #Prosertek #Terminals",
    ),
    (
        "Marine gangways: telescopic bridges for dock-to-ship under harsh conditions",
        "Passenger patience is finite; mechanical margin is not optional.",
        "Tower or column configurations extend Prosertek gangways across air gaps with designs aimed at tough environments and repeatable operations.",
        "#MarineGangways #Prosertek #Ports #Passenger #Safety",
    ),
    (
        "Boarding bridges: weather protection as part of the transit experience",
        "If people are exposed, operations slow down—then risk compounds.",
        "Boarding bridges target adaptable transit between ship and shore under severe conditions, with layouts that suit different vessel interfaces.",
        "#BoardingBridges #Prosertek #Ports #Operations #Safety",
    ),
    (
        "Port cranes on gangways and towers: load paths the whole system must respect",
        "A crane is never ‘just’ an accessory; it is a dynamic load on a walking path.",
        "Prosertek positions cranes as integrated harbour equipment—range, structure, and accessories depend on the gangway/tower concept.",
        "#PortCranes #Prosertek #MaterialHandling #Ports #Engineering",
    ),
    (
        "Fender systems: absorbing berthing energy without pretending physics is negotiable",
        "Good fender selection is energy accounting, not brand preference.",
        "Prosertek supplies docking fender systems to protect vessels and structures—Dockmoor-FP closes the loop with deflection monitoring during operations.",
        "#Fenders #Berthing #Prosertek #DockMoor #Ports",
    ),
    (
        "Bollards as mooring anchors: when ‘old iron’ needs an honest conversation",
        "A bollard is not immortal; concrete and anchors age invisibly.",
        "Prosertek’s bollard portfolio underpins conventional mooring; pairing design knowledge with field testing culture keeps assumptions honest.",
        "#Bollards #Mooring #Prosertek #Ports #Safety",
    ),
    (
        "Non-destructive bollard testing: vibration, sensors, and invisible cracks",
        "You cannot manage what you pretend is still ‘probably fine’.",
        "Prosertek performs NDT on installed bollards—wave-based excitation and sensors—to reveal cracks, wear, and foundation issues before they become headlines.",
        "#BollardTest #NDT #Prosertek #Ports #Risk",
    ),
    (
        "BollardScan + Lloyd’s Register: third-party credibility for mooring assurance",
        "A method approved by class is a shared language with insurers and authorities.",
        "Prosertek works with BollardScan’s long maritime track record; verification aligns with Lloyd’s Register expectations and yields detailed reporting.",
        "#BollardScan #LloydsRegister #Prosertek #Mooring #Compliance",
    ),
    (
        "Recommended workload and 3-year certificate narrative: turning scans into policy",
        "A number without a maintenance story is just a moment in time.",
        "NDT packages aim at recommended workloads, monitoring guidance, and a certificate package that supports wharf governance—not just a PDF trophy.",
        "#Prosertek #BollardTest #Maintenance #Ports #Governance",
    ),
    (
        "Underwater maintenance as part of harbour civil health",
        "What you cannot see still loads your mooring plan.",
        "Prosertek lists underwater maintenance among services—complementing topside automation with substructure reality.",
        "#UnderwaterMaintenance #Ports #Prosertek #Infrastructure #Risk",
    ),
    (
        "Portable Pilot Unit (PPU): piloting assistance as a Prosertek service line",
        "Pilots bridge the gap between chart and quay; tools should bridge pilot and port data.",
        "PPU appears as a dedicated offering alongside hardware—worth pairing with BAS narratives for shared situational awareness.",
        "#PPU #Pilotage #Prosertek #Navigation #Ports",
    ),
    (
        "Engineering and R+D+i: why turnkey is a systems problem, not a SKU list",
        "Clients rarely buy ‘a hook’; they buy a verified mooring story.",
        "Prosertek highlights 20+ years of maritime equipment experience, internal R+D+i, and turnkey delivery from design through installation—coordination beats cost drift from role fragmentation.",
        "#Prosertek #Engineering #R&D #Turnkey #Ports",
    ),
    (
        "Technical Assistance Service (SAT): keeping DockMoor and hooks operationally honest",
        "Software without support ages into folklore; mechanics without records age into incidents.",
        "SAT is the long arc after commissioning—aligned with Prosertek’s global technical assistance positioning on product pages.",
        "#TechnicalAssistance #Prosertek #AfterSales #Ports #Reliability",
    ),
    (
        "Spanish Atlantic and Mediterranean references: BAS modules in real energy ports",
        "If your system survives Cartagena weather and LNG cadence, it has stories worth telling.",
        "Public references cite combinations of Dockmoor-BM/MS/ER/HDT/FP/LD/RR/WEB across major Spanish ports and energy clients—use them as evidence, not vibes.",
        "#Prosertek #BAS #Spain #Ports #LNG",
    ),
    (
        "LNG and oil & gas terminals: where BAS modules stack for risk reduction",
        "Energy berths punish both hurry and hesitation—visibility must be simultaneous.",
        "Prosertek positions BAS across LNG and O&G sectors; module stacks reflect jetty complexity (environment, mooring stress, arms, hooks).",
        "#LNG #OilAndGas #Prosertek #DockMoor #Safety",
    ),
    (
        "Commercial vs tourist ports: same physics, different operational tempo",
        "A ferry berth and an LNG jetty share equations; they do not share patience.",
        "BAS configurability per port type is the product point—DockMoor modules scale from compact marinas to large commercial harbours.",
        "#Ports #Prosertek #BAS #Operations #Tourism",
    ),
    (
        "Brochures that match the engineering: BAS catalog and hooks brochure",
        "Marketing should be a compressed FAT, not a fairy tale.",
        "Prosertek offers downloadable BAS and QRH brochures—use them as the canonical vocabulary for client conversations.",
        "#Prosertek #DockMoor #SalesEngineering #Ports #Documentation",
    ),
    (
        "New technologies in port equipment: the guide download as a learning spine",
        "If ‘innovation’ is not tied to mooring physics, it is just slide filler.",
        "Prosertek promotes a guide on new technologies in port equipment—pair it with DockMoor module talk to keep hype grounded.",
        "#Prosertek #HarborEquipment #Innovation #Ports #Education",
    ),
    (
        "Integrating AIS context with DockMoor—without confusing display with control",
        "Awareness layers should converge; authority boundaries should remain boringly clear.",
        "Field discussions often blend AIS/DGPS ship data with BAS—Prosertek’s value is measured manoeuvre + mooring telemetry, not replacing COLREG thinking.",
        "#AIS #DockMoor #Prosertek #BAS #Navigation",
    ),
    (
        "PLC interlocks around QRH release: permissives that respect hot work and weather holds",
        "Automation should refuse unsafe releases without refusing the operator’s agency to document why.",
        "Dockmoor-RR sits in real projects alongside local safety culture—tie release logic to maintenance windows, ESD states, and training drills.",
        "#PLC #QuickReleaseHooks #Prosertek #Safety #Automation",
    ),
    (
        "Alarm rationalisation when BM, MS, FP, and ER all talk at once",
        "Alarm floods are a UX failure as much as a sensor failure.",
        "Prosertek’s modular BAS invites prioritisation layers—suppress noise, escalate physics-backed risk, and log operator acknowledgements.",
        "#AlarmManagement #DockMoor #Prosertek #BAS #Operations",
    ),
    (
        "Environmental limits in Dockmoor-ER: from comfort to operational go/no-go",
        "A pretty weather widget is useless if limits are not contractually and operationally defined.",
        "ER supports wind, waves, humidity, pressure—and optional visibility—so limits can be tied to pilotage, loading arms, or gangway rules.",
        "#DockmoorER #Weather #Limits #Prosertek #Operations",
    ),
    (
        "Fender energy and Dockmoor-FP: correlating deflection with approach speed",
        "If BM says the approach is hot, FP should tell you where energy went.",
        "Cross-module narratives turn berthing into a closed-loop story—useful for claims, training, and design feedback.",
        "#Fenders #DockMoor #Prosertek #Berthing #Analytics",
    ),
    (
        "Loading arm drift (LD) vs mooring line tension (MS): coupling stories",
        "Hydrocarbon hardware and mooring hardware share time but not always causality.",
        "LD+MS together help separate ship motion effects from arm control issues—critical on product and LNG jetties.",
        "#LoadingArms #DockMoor #Prosertek #LNG #Operations",
    ),
    (
        "Cyber-physical access control for Dockmoor-WEB: LAN vs Internet exposure",
        "Remote visibility is powerful; remote misconfiguration is a category error.",
        "Treat WEB access like OT remote ops: segmentation, MFA, session logging, and least privilege—Prosertek supplies the application; the port supplies the governance.",
        "#OTSecurity #DockMoorWEB #Prosertek #CyberSecurity #Ports",
    ),
    (
        "Data registers and manoeuvre replay: turning BAS into an operational learning system",
        "Replay is training material and dispute material—handle retention policy accordingly.",
        "Prosertek emphasises registers and reproduction of manoeuvres—pair with internal data governance for GDPR and port security rules.",
        "#DockMoor #Prosertek #Training #Compliance #Ports",
    ),
    (
        "Hook tooth, retention lever, and structural base: vocabulary for maintenance crews",
        "Words matter when you order spares at 02:00.",
        "QRH pages split cast steel bodies/teeth and levers from rolled bases—maintenance plans should mirror that taxonomy.",
        "#QRH #Maintenance #Prosertek #Mooring #Reliability",
    ),
    (
        "Epoxy wetting and impact resistance: what ‘marine grade’ actually argues about",
        "Coatings fail at edges and repairs—plan inspections there first.",
        "Prosertek details epoxy behaviour against abrasion, seawater, oils, and spills—match inspection checklists to those failure modes.",
        "#Corrosion #Coatings #Prosertek #QRH #Maintenance",
    ),
    (
        "Gangway tower vs column: footprint, stiffness, and integration with cranes",
        "Every gangway concept is a compromise between reach, stiffness, and capex.",
        "Prosertek offers tower/column configurations—selection should start from vessel interface and environmental design cases.",
        "#MarineGangways #Prosertek #Ports #Engineering #Cranes",
    ),
    (
        "Boarding bridges and passenger safety: interlocks that respect weather holds",
        "People will push ‘go’—design the system to make ‘not yet’ understandable.",
        "Pair boarding bridge controls with ER limits and clear HMI narratives—Prosertek’s product framing emphasises severe conditions and adaptability.",
        "#BoardingBridges #Safety #Prosertek #Weather #Ports",
    ),
    (
        "Fender selection dialogue: energy absorption vs quay reaction force",
        "Rubber compounds are not interchangeable once berthing energy is honest.",
        "Prosertek supplies fender systems engineered for energy management—tie selection to ship sizes, approach angles, and BM/FP feedback loops.",
        "#Fenders #Berthing #Prosertek #Engineering #Ports",
    ),
    (
        "Bollard pull and NDT: when static capacity is unknowable without a test campaign",
        "Assume less; measure more—especially where concrete age is measured in decades.",
        "Prosertek’s NDT methodology targets anchors, concrete, and steel state—use results to reconcile mooring plans with actual capacity.",
        "#BollardTest #NDT #Prosertek #Mooring #Risk",
    ),
    (
        "Worldwide references: Dunkerque, Genova, Taboguilla alongside Spanish hubs",
        "Global equipment stories beat ‘we are unique’ claims—show receipts.",
        "Prosertek publishes reference lists across Europe and the Americas—use them to anchor sales conversations in evidence.",
        "#Prosertek #Ports #References #Maritime #Engineering",
    ),
    (
        "Energy clients on the record: Enagás, Repsol, Petronor, BP-class narratives",
        "If your hook list matches a major jetty’s reality, say it with humility and specificity.",
        "Public QRH reference tables include major energy terminals—translate tonnage and hook counts into maintenance and BAS module planning.",
        "#LNG #Energy #Prosertek #QRH #Ports",
    ),
    (
        "DockMoor module mix for complex jetties: when clients stack BM through WEB",
        "Complexity is not ‘more screens’—it is more variables under one reproducible timeline.",
        "References show multi-module deployments (e.g., BM+MS+HDT+ER+FP+LD+RR+WEB)—that is systems integration, not a single sensor sale.",
        "#DockMoor #Prosertek #BAS #SystemsIntegration #Ports",
    ),
    (
        "Operator training: turning DockMoor replay into competency evidence",
        "Training records should be as inspectable as torque sheets.",
        "Use manoeuvre history and alarm timelines as drill inputs—Prosertek’s BAS story is partly ‘human in the loop with better instruments’.",
        "#Training #DockMoor #Prosertek #Competency #Ports",
    ),
    (
        "Insurance and claims: structured DockMoor exports vs screenshots in email",
        "Evidence density wins disputes; opinions do not.",
        "Position BAS registers and module archives as part of operational risk management—not only operations.",
        "#Compliance #DockMoor #Prosertek #Risk #Ports",
    ),
    (
        "Integration workshops: port authority, construction firm, OEM—Prosertek’s stated triangle",
        "Turnkey fails when interfaces are ‘someone else’s problem’.",
        "Engineering pages stress collaboration with authorities, constructors, and engineering firms—run workshops with explicit RACI and interface tables.",
        "#Prosertek #Engineering #Turnkey #ProjectManagement #Ports",
    ),
    (
        "Customization vs product catalog discipline",
        "Ports are bespoke; engineering should still be traceable.",
        "Prosertek sells configurable BAS modules and customised mechanical packages—document deviations as controlled changes, not one-off folklore.",
        "#Prosertek #Engineering #Configuration #Quality #Ports",
    ),
    (
        "Salt, UV, and cyclic loading: why Prosertek emphasises long-lasting designs",
        "Harbour equipment is fatigue and corrosion with a schedule.",
        "The homepage promise—solid, long-lasting designs—should show up in inspection cadence, coating touch-ups, and NDT intervals.",
        "#Reliability #Marine #Prosertek #Maintenance #Ports",
    ),
    (
        "From brochure PDF to commissioning SAT: closing the vocabulary gap",
        "Sales promises and FAT scripts should share nouns.",
        "Use Prosertek brochures as glossary sources for test cases—module names, limits, and interfaces should match.",
        "#Commissioning #Prosertek #Quality #BAS #Documentation",
    ),
    (
        "Prosertek USA and DockMoor: aligning brand entities in client conversations",
        "Legal entities matter for contracts; users care about support continuity.",
        "Site copy references Prosertek USA for DockMoor software—be precise in proposals about supply, service, and spares.",
        "#Prosertek #DockMoor #Maritime #Business #Engineering",
    ),
    (
        "QRH emergency release: choreography between Dockmoor-RR and people on the quay",
        "Emergency paths must be drill-simple; normal paths can be rich.",
        "Prosertek’s RR narrative includes general emergency firing—tie drills to communications, camera coverage, and manual overrides.",
        "#EmergencyResponse #DockmoorRR #Prosertek #Safety #Ports",
    ),
    (
        "Mooring line monitoring without pretending it replaces deck judgement",
        "Telemetry supports decisions; it should not infantilise crew.",
        "Dockmoor-MS is an instrument layer—pair readings with clear procedures for line tending and communications with ship.",
        "#Mooring #DockMoor #Prosertek #HumanFactors #Operations",
    ),
    (
        "Berthing approach limits: translating BM parameters into pilot and bridge language",
        "Different roles use different words for the same metres per second.",
        "Prosertek BM supplies speed/angle context—build shared limit tables for pilotage, tug plans, and BAS alarms.",
        "#Pilotage #DockMoorBM #Prosertek #Berthing #Communications",
    ),
    (
        "DockMoor in small ports: proportionate modules vs enterprise overkill",
        "Not every marina needs every module—credibility is fit-for-purpose.",
        "Prosertek lists small ports among sectors—sell the smallest defensible module stack, then expand with evidence.",
        "#Marinas #Prosertek #DockMoor #RightSizing #Ports",
    ),
    (
        "Logistics and shipbuilding sectors: BAS as a cross-industry mooring monitor",
        "Mooring stress stories extend beyond commercial quays.",
        "Prosertek mentions logistics firms and shipbuilding—use DockMoor where manoeuvre monitoring adds safety or throughput.",
        "#Shipbuilding #Logistics #Prosertek #BAS #Maritime",
    ),
    (
        "Hydrocarbon spill scenarios and QRH coatings: matching material specs to real risk",
        "A coating spec is a scenario statement.",
        "Prosertek lists resistance to oils and petrol-like spills—tie inspection to realistic leak scenarios, not generic checklists.",
        "#QRH #Coatings #Prosertek #Risk #Terminals",
    ),
    (
        "Concrete cancer near old bollards: NDT as civil diagnostics, not ‘magic scans’",
        "Interpretation matters as much as acquisition.",
        "Prosertek’s NDT narrative includes foundation and surface assessment—pair vendor reports with structural follow-up.",
        "#NDT #Concrete #Prosertek #BollardTest #Infrastructure",
    ),
    (
        "Service contracts: what ‘technical assistance’ should include for DockMoor and hooks",
        "A phone number is not a service; response metrics are.",
        "Define SLAs for software updates, calibration support for load paths, and field visits—aligned with Prosertek’s services positioning.",
        "#AfterSales #Prosertek #DockMoor #Service #Ports",
    ),
    (
        "Spare parts and hooks: traceability from castings to installed fleet",
        "Fleet thinking beats one-off hero repairs.",
        "Prosertek’s reference-heavy QRH lists invite fleet normalization—standardize hook families where possible to simplify spares.",
        "#Spares #QRH #Prosertek #Maintenance #Fleet",
    ),
    (
        "Underwater works and topside automation: one risk register",
        "A clever BAS cannot compensate for a compromised dolphin foundation.",
        "Pair underwater maintenance with bollard NDT and fender inspections—Prosertek offers both lines explicitly.",
        "#UnderwaterMaintenance #Prosertek #Infrastructure #Risk #Ports",
    ),
    (
        "Portable Pilot Unit in the sales story: bridging navigation and berth execution",
        "PPU complements pilotage; DockMoor complements berth execution—together they reduce translation errors.",
        "Prosertek lists PPU as a service—use it in proposals where pilotage data should meet jetty monitoring.",
        "#PPU #Pilotage #Prosertek #DockMoor #Ports",
    ),
    (
        "R+D+i department: translating research into shippable harbour equipment",
        "Innovation is not a slide; it is a drawing revision with a test plan.",
        "Prosertek highlights internal R+D+i—connect it to module roadmap (WEB security, sensor fusion, diagnostics) with evidence.",
        "#Innovation #Prosertek #R&D #HarborEquipment #Engineering",
    ),
    (
        "Turnkey contracting: eliminating cost hikes from fragmented roles",
        "Every hand-off is a budget line item waiting to argue.",
        "Prosertek markets turnkey as coordinated management—proposal structure should show single-threaded accountability.",
        "#Turnkey #Prosertek #ProjectDelivery #Ports #Engineering",
    ),
    (
        "Client evidence: Petronor-class module stacks as architecture references",
        "Named references are design precedents, not name dropping.",
        "Use published client/module combinations to justify integrated BAS architectures in new projects.",
        "#Prosertek #References #BAS #Energy #Ports",
    ),
    (
        "DockMoor and class society narratives: Lloyd’s on bollard testing as a pattern",
        "What gets class-approved becomes easier to insure.",
        "Position NDT and structured reporting as part of a broader assurance story alongside equipment supply.",
        "#LloydsRegister #Prosertek #Compliance #Mooring #Risk",
    ),
    (
        "Berthing damage reduction: the economic argument Prosertek makes explicit",
        "Safety and cost reduction belong in the same paragraph.",
        "Prosertek claims BAS can reduce operational costs and damage to port, fenders, and ships—build simple before/after narratives with conservative assumptions.",
        "#ROI #DockMoor #Prosertek #Berthing #Ports",
    ),
    (
        "Real-time monitoring vs after-the-fact investigations",
        "Investigations are expensive; prevention is engineering.",
        "BAS emphasis on registers and monitoring supports proactive operations—sell it as fewer surprises, not only compliance.",
        "#Operations #DockMoor #Prosertek #Safety #Ports",
    ),
    (
        "Configuration flexibility: same DockMoor spine, different port personalities",
        "Modules are LEGO with physics constraints.",
        "Prosertek stresses flexible configuration—capture each port’s module rationale in the commissioning record.",
        "#Configuration #DockMoor #Prosertek #BAS #Engineering",
    ),
    (
        "Audio/visual alarms on FP and LD: designing for night operations",
        "Alarms must win against wind noise and fatigue.",
        "Prosertek modules reference audio/visual alarms—tune with human factors testing, not only default HMI templates.",
        "#HumanFactors #DockMoor #Prosertek #Operations #Safety",
    ),
    (
        "UDP in HDT: network design implications for firewalls and diagnostics",
        "Diagnostics love broadcast-friendly protocols; security loves deny-by-default.",
        "Document UDP flows for HDT explicitly in OT segmentation designs—Prosertek names UDP; your network design must name zones.",
        "#OTSecurity #DockmoorHDT #Prosertek #Networking #Diagnostics",
    ),
    (
        "Laser and oceanographic sensors in HDT: calibration and obsolescence",
        "A laser rangefinder is a recurring calibration relationship.",
        "Prosertek lists lasers and oceanographic sensors under HDT—plan periodic verification and spares.",
        "#Instrumentation #DockmoorHDT #Prosertek #Maintenance #Ports",
    ),
    (
        "Weather stations vs compact environmental kits in Dockmoor-ER",
        "Complex stations are powerful when maintenance matches ambition.",
        "Prosertek allows compact to complex—match sensor count to maintenance capacity.",
        "#DockmoorER #Weather #Prosertek #Maintenance #Ports",
    ),
    (
        "Visibility and radiation add-ons: niche but decisive for some terminals",
        "Some limits are human; some are optical.",
        "Prosertek mentions visibility and solar radiation as optional—use where operations or safety cases require them.",
        "#DockmoorER #Visibility #Prosertek #Operations #Safety",
    ),
    (
        "Dockmoor-WEB on smartphones: usability and authentication realities",
        "Mobile access is convenient until it becomes credential sprawl.",
        "Prosertek enables phone/tablet access—enforce device policies and MFA for remote paths.",
        "#DockmoorWEB #Prosertek #Mobile #Security #Ports",
    ),
    (
        "Comparing DockMoor to ‘generic SCADA screens’: integrated manoeuvre narrative",
        "SCADA without manoeuvre context is just tags with anxiety.",
        "Prosertek’s BAS story is integrated visualization—position against bolt-on dashboards that lack BM/MS/FP coherence.",
        "#DockMoor #Prosertek #SCADA #BAS #Integration",
    ),
    (
        "Hook status and line tension on one RR desk: operator ergonomics",
        "If the desk is confusing, training cannot fix it forever.",
        "Prosertek RR includes interactive monitoring of tension and hook status—validate UI flows with operators, not only with engineers.",
        "#DockmoorRR #UX #Prosertek #Operations #Safety",
    ),
    (
        "General emergency firing: testing without courting chaos",
        "Emergency features deserve the most boring test reports.",
        "Prosertek references general emergency firing—write explicit test scripts and witness records.",
        "#Testing #DockmoorRR #Prosertek #Safety #Commissioning",
    ),
    (
        "Mooring line collection ergonomics: QRH value in commercial terminals",
        "Efficiency matters because time on the berth is money and risk.",
        "Prosertek highlights easier line collection—translate to operational metrics where possible.",
        "#Mooring #QRH #Prosertek #TerminalOps #Efficiency",
    ),
    (
        "Prosertek’s harbour equipment catalog: fenders, cranes, gangways as one ecosystem",
        "Customers buy systems; maintainers live with interfaces.",
        "Homepage groups BAS, QRH, gangways, boarding bridges, cranes, fenders, bollards—proposal narratives should mirror that completeness.",
        "#Prosertek #HarborEquipment #Ports #Engineering #Sales",
    ),
    (
        "Contact and quote flows: engineering intake done seriously",
        "A quote request should read like a mini engineering brief.",
        "Prosertek pushes request-a-quote—train sales engineers to ask for limits, modules, and interface ownership early.",
        "#Prosertek #SalesEngineering #Ports #Business",
    ),
    (
        "Downloadable guides: using Prosertek PDFs as training anchors",
        "If the team has not read the brochure, the FAT will be improvisational.",
        "General catalog + technology guide + module brochures—make them required reading before factory tests.",
        "#Documentation #Prosertek #Training #Quality #Ports",
    ),
    (
        "Language coverage: English / Spanish / French sites and global clients",
        "Technical accuracy must survive translation.",
        "Prosertek runs multilingual sites—ensure spec sheets and alarm texts stay consistent across languages in multinational projects.",
        "#Prosertek #Localization #Maritime #Engineering #Documentation",
    ),
    (
        "Prosertek since 1990: longevity as a warranty of institutional memory",
        "Time in market is not automatic expertise—but it is not irrelevant either.",
        "Use company history carefully: cite processes (R+D+i, SAT, references) rather than slogans.",
        "#Prosertek #Maritime #Engineering #Heritage #Ports",
    ),
    (
        "Closing the loop: from DockMoor data to safer mooring culture",
        "Data should make humility easier, not arrogance cheaper.",
        "Prosertek’s BAS promise is safer, more effective operations—measure success in near-miss reduction and repeatable manoeuvres, not only uptime.",
        "#DockMoor #Prosertek #SafetyCulture #Ports #Leadership",
    ),
    (
        "Field engineer mindset: representing Prosertek hardware without overselling certainty",
        "The jetty always has one variable you did not model.",
        "Ground public LinkedIn storytelling in Prosertek’s real modules and services—BAS, QRH, gangways, NDT, engineering—avoid fictional products.",
        "#Prosertek #FieldEngineering #Integrity #Maritime #Leadership",
    ),
    (
        "Linking www.prosertek.com resources to client workshops",
        "A website should be a shared reference, not a secret.",
        "Use downloadable brochures and service pages as agenda anchors for design reviews—Prosertek’s site is structured for that.",
        "#Prosertek #SalesEngineering #Ports #Documentation #Training",
    ),
    (
        "Prosertek equipment and class discussions: evidence bundles",
        "Class and insurers like traceable artifacts.",
        "Combine FAT/SAT records, NDT certificates, and DockMoor exports into one evidence bundle—Prosertek’s portfolio spans hardware and monitoring.",
        "#Compliance #Prosertek #Classification #Ports #Engineering",
    ),
    (
        "Future-facing: where DockMoor could absorb new sensor classes responsibly",
        "New sensors are easy; validated limits are hard.",
        "Prosertek’s modular BAS philosophy sets expectations—pilot new sensing under HDT with explicit uncertainty and rollback.",
        "#Innovation #DockMoor #Prosertek #Instrumentation #Ports",
    ),
    (
        "Honest limitations: what Prosertek does not claim on the website",
        "Credibility is also what you do not promise.",
        "Stay aligned with published scope—harbour equipment, DockMoor modules, services—avoid inventing features not described publicly.",
        "#Prosertek #Ethics #Engineering #Trust #Maritime",
    ),
    (
        "Your next site visit: a checklist grounded in Prosertek’s lines of business",
        "Walk the jetty with module names—BM, MS, FP, RR—and you will see integration opportunities faster.",
        "Tie observations to DockMoor modules and physical equipment (QRH, fenders, gangways) so recommendations stay vendor-truthful.",
        "#Prosertek #DockMoor #Commissioning #Ports #Checklist",
    ),
    (
        "Prosertek in one sentence: mooring and berthing equipment with monitoring that earns trust",
        "If the sentence needs acronyms to sound impressive, rewrite it.",
        "Manufacturer since 1990; DockMoor BAS; QRH; gangways; bridges; cranes; fenders; bollards; services including NDT and engineering—say that plainly.",
        "#Prosertek #HarborEquipment #DockMoor #Mooring #Ports",
    ),
    (
        "General catalog vs module brochures: matching the buyer to the right PDF",
        "Nobody should read 80 pages to find the QRH torque note.",
        "Prosertek offers a general catalog plus BAS and hooks brochures—use the right document for the decision at hand (design review vs hook FAT).",
        "#Prosertek #Documentation #SalesEngineering #Ports #BAS",
    ),
    (
        "Oil & gas and offshore: BAS sectors Prosertek calls out explicitly",
        "Sector labels help clients see themselves in the story.",
        "Alongside commercial ports, Prosertek lists O&G, LNG, and offshore platforms—tie module stacks to hydrocarbon manoeuvre risk.",
        "#OilAndGas #LNG #Offshore #Prosertek #DockMoor",
    ),
    (
        "International maritime organisations: where standards meet procurement",
        "Standards are a table; the jetty is still a physical system.",
        "Prosertek mentions international maritime organisations among sectors—pair standards talk with site-specific BAS configuration evidence.",
        "#Maritime #Standards #Prosertek #Ports #Engineering",
    ),
]

assert len(ROWS) == 100  # noqa: S101


def main() -> None:
    out: list[dict[str, str]] = []
    for day in range(1, 501):
        idx = day - 1
        theme, hook, tech, tags = ROWS[idx % 100]
        cycle = idx // 100
        if cycle:
            theme = f"{theme} (cycle {cycle + 1})"
        out.append(
            {
                "day": str(day),
                "theme": theme,
                "hook": hook,
                "technical_angle": tech,
                "hashtags": tags,
            }
        )

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["day", "theme", "hook", "technical_angle", "hashtags"])
        w.writeheader()
        w.writerows(out)

    print(f"Wrote {len(out)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
