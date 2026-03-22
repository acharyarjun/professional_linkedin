#!/usr/bin/env python3
"""Rebuild data/post_calendar.csv with neutral, practitioner-scholar topics.

No company promotion or criticism—industry concepts, sound engineering judgment,
and field experience framed as personal understanding. Run: python scripts/build_post_calendar.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "post_calendar.csv"

# 100 unique rows × 5 cycles = 500 days. Themes 101–500 add (cycle N) for distinction.
ROWS: list[tuple[str, str, str, str]] = [
    (
        "Berthing aid systems: when shared visualization actually aligns quay and bridge",
        "I’ve watched the same approach feel ‘fine’ on the radio and ‘tight’ on the fender line—alignment beats optimism.",
        "A good BAS ties distance, speed, and angle to one manoeuvre picture so corrections are debated against data, not against egos.",
        "#Berthing #PortAutomation #MarineOps #Safety #Engineering",
    ),
    (
        "Measuring bow/stern speed and approach angle against the fender plane",
        "Berthing is geometry with consequences; squalls don’t forgive casual eyeballing.",
        "Laser or radar-derived geometry plus time sync gives you alerts, history, and replay—useful for training and for post-incident honesty.",
        "#Berthing #Navigation #Instrumentation #Ports #Safety",
    ),
    (
        "Mooring line tension at the hook: why the spreadsheet is never where failure lives",
        "Lines fail at steel, rope, and human limits—not in the planning meeting.",
        "Load paths through quick-release hooks with integrated sensing can expose overload before narrative does; alarms need operator trust, not novelty.",
        "#Mooring #LoadCells #Instrumentation #Ports #Safety",
    ),
    (
        "Hardware diagnostics across panels, lasers, arms, and weather kits",
        "A silent fieldbus is not peace—it’s missing telemetry you assumed you had.",
        "UDP-style diagnostic layers are common; the design win is naming devices, timeouts, and failure modes so maintenance doesn’t grep blindly.",
        "#Diagnostics #Fieldbus #IIoT #Ports #Maintenance",
    ),
    (
        "Bringing wind, waves, and sea state into the same decision context as approach",
        "Limits written only in knots miss the period of the swell.",
        "Environmental modules matter when gangways, pilot windows, or loading arms share the same hour as the manoeuvre.",
        "#Weather #MarineOps #Ports #Safety #Instrumentation",
    ),
    (
        "Fender deflection in the last metres: energy has to go somewhere",
        "A fender can look idle while storing asymmetric load into the dolphin line.",
        "Deflection monitoring supports alarm rationalisation and post-event reconstruction—less ‘who said what’, more ‘what the structure did’.",
        "#Fenders #Berthing #StructuralHealth #Ports #Engineering",
    ),
    (
        "Loading arm drift during mooring: hydrocarbon hardware and ship motion couple",
        "Arms don’t forgive casual geometry—especially when product is moving.",
        "Drift limits with time-stamped traces beat one-off observations when you argue with maintenance or with the ship.",
        "#LoadingArms #LNG #ProcessSafety #Ports #Instrumentation",
    ),
    (
        "Remote and local release on quick-release hooks: permissives before convenience",
        "Release is a safety function; ‘easier’ should never mean ‘less traceable’.",
        "Good designs separate monitoring, authority to release, and emergency paths—with logging that survives audits.",
        "#Mooring #Automation #FunctionalSafety #Ports #Operations",
    ),
    (
        "Browser access to berthing data: convenience without turning OT into the public internet",
        "If superintendents need tablets, solve identity and segmentation first.",
        "HTTPS, MFA, and least-privilege beats ‘RDP to someone’s laptop’ as a long-term operations pattern.",
        "#OTSecurity #RemoteOps #Maritime #Architecture #Ports",
    ),
    (
        "From alarms to evidence: registers, replay, and dispute resolution",
        "Screenshots age badly; synchronized timelines age better.",
        "Event registers that support replay turn arguments into reconstruction—which insurers and internal reviews actually need.",
        "#Operations #Compliance #Ports #Instrumentation #Governance",
    ),
    (
        "Quick-release hooks: mechanical truth before ‘smart rope’ storytelling",
        "Telemetry should clarify load paths, not replace them.",
        "Hooks that give solid anchor points and clean load introduction beat gadgets that decorate weak mechanics.",
        "#Mooring #MechanicalEngineering #Ports #Safety #Engineering",
    ),
    (
        "Marine coatings: ISO 12944 categories and what salt fog actually tests",
        "Datasheets are aspirations; edges and welds are where corrosion wins.",
        "Epoxy systems for abrasion, seawater, and spill exposure need inspection plans that match failure modes, not paint schedules alone.",
        "#Corrosion #Marine #Materials #Maintenance #Ports",
    ),
    (
        "Metallurgy at the hook: cast bodies, rolled bases, heat-treated shafts",
        "A hook is a stack of material decisions—not a single part number.",
        "Understanding bodies, teeth, and shafts separately helps FAT/SAT conversations stay factual when something cracks or wears.",
        "#Materials #Mooring #Quality #Engineering #Ports",
    ),
    (
        "Capstans: pedal control, drum geometry, and hands-free line handling",
        "Hands belong on guardrails at the wrong moment—not wrestling line unnecessarily.",
        "Integrated capstan design is ergonomics plus mechanical advantage; it’s underrated until night berthing in bad weather.",
        "#Mooring #Ergonomics #Ports #Operations #Safety",
    ),
    (
        "Sizing multi-hook assemblies against declared line loads and contingency cases",
        "Catalogue tonnage is a starting point; mooring plans and failures modes finish the argument.",
        "Engineering reviews should line up hook counts, fleet behaviour, and maintenance history—not brochure peaks.",
        "#Mooring #StructuralEngineering #Ports #Risk #Engineering",
    ),
    (
        "Telescopic gangways: reach, stiffness, and tower vs column trade-offs",
        "Every gangway is a compromise between footprint, stiffness, and capex.",
        "Selection should start from vessel interface, environmental design case, and evacuation assumptions—not from a default drawing.",
        "#Gangways #Ports #StructuralEngineering #Safety #Design",
    ),
    (
        "Boarding bridges: weather protection and throughput under stress",
        "Passenger patience is finite; mechanical margin isn’t optional.",
        "Adaptable transit geometry matters when schedules conflict with wind limits.",
        "#Passenger #Ports #Operations #Safety #Design",
    ),
    (
        "Cranes on gangway structures: dynamic loads on a walking path",
        "A crane isn’t an accessory—it’s load and fatigue on shared steel.",
        "Integrated design reviews should include maintenance access and deflection limits people actually feel.",
        "#MaterialHandling #Cranes #Ports #StructuralEngineering #Safety",
    ),
    (
        "Fender selection as energy accounting, not brand preference",
        "Rubber compounds and layouts answer to berthing energy and quay reaction—physics first.",
        "Good selection ties ship sizes, approach angles, and monitoring (if any) into one coherent story.",
        "#Fenders #Berthing #Engineering #Ports #Physics",
    ),
    (
        "Bollards and ageing quays: when ‘it held last year’ stops being an argument",
        "Concrete and anchors age invisibly until they don’t.",
        "Honest mooring plans acknowledge uncertainty in old infrastructure—tests or conservative limits beat hope.",
        "#Bollards #Infrastructure #Risk #Ports #Safety",
    ),
    (
        "Non-destructive bollard assessment: vibration, sensors, and invisible cracks",
        "You can’t manage what you pretend is still ‘probably fine’.",
        "Wave-based methods and structured reporting can reveal cracks and foundation issues before they become headlines.",
        "#NDT #StructuralHealth #Mooring #Ports #Engineering",
    ),
    (
        "Third-party verification and class contexts for mooring assurance",
        "A recognised method gives insurers and authorities a shared vocabulary.",
        "I treat certificates as inputs to maintenance policy—not as substitutes for judgment when conditions change.",
        "#Compliance #Classification #Mooring #Risk #Ports",
    ),
    (
        "Turning NDT results into workload limits and inspection cadence",
        "A number without a maintenance story is a moment in time.",
        "Recommended loads and monitoring should connect to ropes, winches, and operational rules—not sit in a PDF alone.",
        "#Maintenance #Mooring #Governance #Ports #Reliability",
    ),
    (
        "Underwater works and topside automation: one risk register",
        "Clever monitoring can’t compensate for a compromised dolphin foundation.",
        "I pair substructure inspections with fender and bollard logic—interfaces matter.",
        "#Infrastructure #Ports #Risk #Maintenance #Engineering",
    ),
    (
        "Portable pilot units and berth execution: translating navigation into jetty reality",
        "PPU complements pilotage; the jetty still needs its own limits and communications.",
        "Useful when pilotage data should meet mooring plans without translation errors.",
        "#Pilotage #Navigation #Ports #Operations #Safety",
    ),
    (
        "Turnkey project interfaces: authorities, EPCs, and OEM boundaries",
        "Cost hikes often trace to hand-offs, not to the colour of the HMI.",
        "Single-threaded accountability and explicit interface tables beat heroic integration at commissioning.",
        "#ProjectManagement #Engineering #Ports #Commissioning #Leadership",
    ),
    (
        "Field support after commissioning: software updates vs mechanical reality",
        "Software without support culture ages into folklore; mechanics without records age into incidents.",
        "I care about SLAs for calibration, spares, and regression tests—not only phone numbers.",
        "#AfterSales #Reliability #Ports #Maintenance #Engineering",
    ),
    (
        "Energy terminals: module stacks when LNG or product jetties punish hurry",
        "High-consequence berths need simultaneous visibility—mooring, environment, arms, hooks.",
        "Integration thinking beats a pile of unrelated alarms.",
        "#LNG #Terminals #Safety #Operations #Engineering",
    ),
    (
        "Commercial vs ferry vs marina tempo: proportionate automation",
        "Not every berth needs enterprise complexity; credibility is fit-for-purpose.",
        "Right-sizing saves money and operator attention—both are safety variables.",
        "#Ports #Operations #Automation #HumanFactors #Design",
    ),
    (
        "Using manufacturer brochures as engineering vocabulary—not as faith",
        "If the team hasn’t read the limits, FAT becomes improvisation.",
        "Brochures should align with test scripts; mismatched nouns become midnight defects.",
        "#Commissioning #Quality #Documentation #Engineering #Ports",
    ),
    (
        "‘New technologies in port equipment’: separating signal from slide filler",
        "Innovation has to survive mooring physics and maintenance culture.",
        "I pilot new sensing under explicit uncertainty budgets and rollback—hype isn’t a control strategy.",
        "#Innovation #Ports #Instrumentation #Engineering #Judgment",
    ),
    (
        "AIS and bridge context next to jetty monitoring: convergence without confusion",
        "Awareness layers can converge; authority boundaries should stay boring.",
        "Integrated displays shouldn’t blur who may command motion vs who advises limits.",
        "#AIS #Navigation #Berthing #HumanFactors #Maritime",
    ),
    (
        "PLC interlocks around hook release: hot work, weather holds, maintenance windows",
        "Automation should refuse unsafe releases without erasing documented overrides.",
        "Permissives tied to ESD state, procedures, and training beat ‘because the screen said so’.",
        "#PLC #Safety #Automation #Ports #Operations",
    ),
    (
        "Alarm rationalisation when geometry, loads, weather, and fenders all speak at once",
        "Alarm floods are often a UX failure, not only a sensor failure.",
        "Prioritisation, suppression policies, and operator acknowledgement separate noise from physics-backed risk.",
        "#AlarmManagement #HMI #Operations #Ports #Safety",
    ),
    (
        "Environmental limits: from comfort metrics to operational go/no-go",
        "A weather widget is useless if limits aren’t defined operationally and contractually.",
        "Wind, swell, and visibility ties to pilotage, gangways, and arms should be explicit—not implied.",
        "#Weather #Operations #Ports #Safety #Governance",
    ),
    (
        "Correlating approach energy with fender deflection: closing the berthing loop",
        "If approach telemetry says ‘hot’, fender telemetry should say where energy went.",
        "Cross-checking modules reduces arguments after the fact.",
        "#Berthing #Fenders #Instrumentation #Ports #Analytics",
    ),
    (
        "Mooring tension vs loading-arm drift: correlation is not causation",
        "Ship motion can move both lines and arms—separate effects need separate hypotheses.",
        "Useful when product arms and mooring share a timeline on tricky berths.",
        "#LoadingArms #Mooring #LNG #Operations #Diagnostics",
    ),
    (
        "Segmentation and identity for remote visibility into berthing systems",
        "Remote access is powerful; flat OT networks age poorly in public terminals.",
        "MFA, least privilege, and session logging are part of the safety story—not only IT hygiene.",
        "#OTSecurity #CyberSecurity #Ports #Architecture #Governance",
    ),
    (
        "Data retention: replay for training vs privacy and security reality",
        "Replay is training material and dispute material—policy should say which, for how long, and who may access.",
        "I align retention with port rules and labour agreements, not only disk size.",
        "#Governance #Compliance #Operations #Ports #Data",
    ),
    (
        "Spares vocabulary: hook tooth, lever, base—words maintenance needs at 02:00",
        "Ambiguous part language becomes downtime.",
        "Taxonomy in manuals should match work orders and stores systems.",
        "#Maintenance #Reliability #Ports #Operations #Quality",
    ),
    (
        "Inspection plans for coatings: edges, repairs, and spill exposure",
        "Coatings fail where reality concentrates stress and chemistry.",
        "Checklists should follow failure modes—abrasion, UV, oils—not generic calendar colour.",
        "#Corrosion #Maintenance #Ports #Quality #Engineering",
    ),
    (
        "Gangway structural choices: footprint vs stiffness vs integration",
        "There is no free lunch in steel and hydraulics.",
        "Walk the trade-offs with fatigue and deflection—not only first-cost.",
        "#Gangways #StructuralEngineering #Ports #Design #Safety",
    ),
    (
        "Boarding bridges: interlocks that people won’t defeat casually",
        "If the interlock feels rude, people route around it—design courteous enforcement.",
        "Clear narratives for weather holds and maintenance modes beat mystery lights.",
        "#HumanFactors #Safety #Interlocks #Ports #Design",
    ),
    (
        "Fender design dialogue: reaction force vs energy absorption",
        "Compound elasticity is not interchangeable once ship masses and approach angles change.",
        "Tie monitoring and maintenance to the design case you actually operate.",
        "#Fenders #Berthing #Engineering #Ports #Physics",
    ),
    (
        "Bollard testing: from scan results to mooring policy",
        "Assumed capacity is a liability when infrastructure is old.",
        "I use structured tests to reconcile fleet plans with wharf reality—conservatively.",
        "#Mooring #Infrastructure #Risk #Ports #Engineering",
    ),
    (
        "International references: evidence beats adjectives in technical posts",
        "Named projects help—but only when details are shareable and accurate.",
        "I prefer patterns and lessons over name-dropping without context.",
        "#Engineering #Ports #Professionalism #Communication #Judgment",
    ),
    (
        "Energy-terminal mooring narratives: tonnage, contingencies, and humility",
        "Big hooks and big ships still lose to bad procedures.",
        "Engineering stories should centre limits, training, and maintenance—not heroics.",
        "#LNG #Mooring #Safety #Operations #Culture",
    ),
    (
        "Stacking monitoring modules: systems integration vs screen count",
        "Complexity isn’t more dashboards—it’s coherent variables under one timeline.",
        "Integration discipline shows up in commissioning and in night-shift usability.",
        "#SystemsIntegration #Ports #Commissioning #UX #Operations",
    ),
    (
        "Operator training: replay as competency evidence, not entertainment",
        "Drills should produce inspectable outcomes—briefs, sign-offs, gaps identified.",
        "Replay archives are inputs to competence systems when used deliberately.",
        "#Training #Safety #Operations #Ports #Leadership",
    ),
    (
        "Insurance and disputes: structured exports vs opinion chains",
        "Evidence density beats rhetorical confidence.",
        "Time-aligned logs and signed procedures matter when claims arrive.",
        "#Risk #Compliance #Operations #Ports #Governance",
    ),
    (
        "Interface workshops: who owns sensor, power, network, and software?",
        "Turnkey fails when RACI is vague.",
        "I like explicit interface tables early—saves money later.",
        "#ProjectManagement #Commissioning #Engineering #Ports #Leadership",
    ),
    (
        "Customization vs catalogue discipline: traceability either way",
        "Ports are bespoke; engineering should still be testable.",
        "Document deviations as controlled changes—not as one-off mythology.",
        "#Engineering #Quality #Ports #Configuration #Compliance",
    ),
    (
        "Salt, UV, and cyclic loading: why ‘long-lasting’ is a maintenance hypothesis",
        "Time in service is not automatic proof—inspection cadence is.",
        "I connect environmental reality to inspection and NDT triggers.",
        "#Reliability #Maintenance #Marine #Ports #Engineering",
    ),
    (
        "From PDF to SAT: closing the vocabulary gap between sales and commissioning",
        "If nouns don’t match, tests don’t match.",
        "Align brochures, IO lists, and test scripts before the team flies in.",
        "#Commissioning #Quality #Documentation #Engineering #Ports",
    ),
    (
        "Legal entities and support continuity: what procurement should clarify",
        "Contracts matter for spares and updates—not only for hardware arrival.",
        "I ask who supports software, who supports steel, and how upgrades regress.",
        "#Procurement #AfterSales #Engineering #Ports #Governance",
    ),
    (
        "Emergency release: drills boring enough to survive audit",
        "Emergency features deserve the most disciplined test reports—not hero demos.",
        "Witnessed steps, signatures, and rollback criteria.",
        "#Safety #EmergencyResponse #Testing #Ports #Compliance",
    ),
    (
        "Line tension monitoring: support for deck decisions, not a replacement for seamanship",
        "Telemetry should clarify risk—not infantilise crew communication.",
        "Pair readings with procedures for line tending and ship/shore dialogue.",
        "#Mooring #HumanFactors #Operations #Maritime #Safety",
    ),
    (
        "Shared limit tables: pilots, tugs, and jetty alarms speaking similar numbers",
        "Different roles describe the same metres per second with different words.",
        "Harmonising limits reduces ‘green light’ misunderstandings.",
        "#Pilotage #Berthing #Communications #Safety #Ports",
    ),
    (
        "Smaller ports: proportionate monitoring without enterprise theatre",
        "Right-sized systems save operator attention—attention is a safety resource.",
        "I’d rather a smaller truthful stack than an unused enterprise suite.",
        "#Ports #Automation #HumanFactors #Design #Judgment",
    ),
    (
        "Shipbuilding and logistics: mooring stress stories beyond commercial quays",
        "Mooring monitoring ideas travel—duty cycles and risk profiles don’t.",
        "Translate carefully across sectors; physics changes with operation.",
        "#Maritime #Engineering #Judgment #Ports #Logistics",
    ),
    (
        "Spill scenarios and coating choices: specs as scenario statements",
        "A coating discussion is partly a chemical risk discussion.",
        "Inspection and compatibility follow the realistic exposure—not the prettiest datasheet row.",
        "#Risk #Materials #Maintenance #Ports #ProcessSafety",
    ),
    (
        "Concrete and anchors: interpretation as engineering, not magic",
        "Scans are inputs; structural follow-up is still a decision.",
        "I avoid treating any single method as oracle—combine evidence.",
        "#Infrastructure #NDT #Engineering #Ports #Judgment",
    ),
    (
        "Service contracts: metrics that matter—response, calibration, regression",
        "A hotline isn’t a service; measurable outcomes are.",
        "Define what ‘fixed’ means for software and for mechanics.",
        "#Reliability #Maintenance #Governance #Ports #Engineering",
    ),
    (
        "Fleet normalisation of hook families: spares economics and training",
        "Variety is expensive at 03:00 in the rain.",
        "Where safe, standardising mechanical families reduces cognitive load and stores burden.",
        "#Maintenance #Fleet #Operations #Ports #Engineering",
    ),
    (
        "Substructure and topside: one risk conversation",
        "Monitoring the deck doesn’t stabilise the dolphin.",
        "Pair underwater and topside programmes where corrosion and loading interact.",
        "#Infrastructure #Risk #Ports #Maintenance #Engineering",
    ),
    (
        "Pilotage data meeting jetty execution: reducing translation errors",
        "Useful when pilots and berth operators share timelines and limit language.",
        "Still respect authority boundaries—awareness isn’t command.",
        "#Pilotage #Navigation #Operations #Safety #Maritime",
    ),
    (
        "R&D culture: from slides to drawing revisions with test plans",
        "Innovation is traceable change—not a buzzword.",
        "I like internal R&D when it shows up as versioned evidence and rollback.",
        "#Innovation #Engineering #Quality #Judgment #Manufacturing",
    ),
    (
        "Turnkey as coordination: fewer hand-offs, clearer accountability",
        "Fragmentation taxes budget and schedule—and sometimes safety.",
        "Integrated delivery needs explicit systems engineering, not only a single vendor logo.",
        "#ProjectDelivery #Engineering #Ports #Leadership #SystemsEngineering",
    ),
    (
        "Named references as design precedents—humility required",
        "A reference proves a pattern existed—not that it copies to your site.",
        "Site conditions win; analogies are starting points.",
        "#Engineering #Judgment #Ports #Professionalism #Design",
    ),
    (
        "Class and insurer language: evidence bundles that travel",
        "Third-party methods help when they create shared artefacts.",
        "I combine class contexts with local regulations and owner requirements—no single stamp replaces thinking.",
        "#Compliance #Risk #Engineering #Ports #Governance",
    ),
    (
        "Economic framing: damage reduction without pretending ROI is exact",
        "Safety and cost belong in the same paragraph—assumptions should be conservative.",
        "Before/after stories need honest baselines, not marketing curves.",
        "#Operations #Risk #Ports #Leadership #Analytics",
    ),
    (
        "Investigations vs prevention: registers as learning systems",
        "Replay supports prevention when organisations actually review.",
        "I value monitoring that feeds retrospectives—not only dashboards.",
        "#Safety #Operations #Learning #Ports #Culture",
    ),
    (
        "Configuration flexibility: modular thinking without modular chaos",
        "Modules help when interfaces and responsibilities stay explicit.",
        "Otherwise you get screens, not a system.",
        "#SystemsEngineering #Ports #Automation #Design #Engineering",
    ),
    (
        "Audio/visual alarms: designing for night noise and fatigue",
        "Alarms must win against wind and tired brains—human factors are engineering.",
        "Test with real operators, not only with default HMI templates.",
        "#HumanFactors #AlarmManagement #Operations #Ports #Safety",
    ),
    (
        "UDP diagnostics: document flows for firewalls and OT segmentation",
        "Diagnostics love reachability; security loves deny-by-default.",
        "Name zones and ports; don’t hand-wave ‘it works on my laptop’.",
        "#Networking #OTSecurity #Diagnostics #Ports #Engineering",
    ),
    (
        "Laser and oceanographic sensors: calibration and obsolescence planning",
        "A rangefinder is a relationship with calibration, not a one-time purchase.",
        "Plan verification intervals and spare strategies.",
        "#Instrumentation #Maintenance #Ports #Reliability #Engineering",
    ),
    (
        "Weather stations: complexity vs maintainability",
        "Rich stations are powerful when maintenance matches ambition.",
        "Sometimes fewer sensors with reliable service beats a fragile observatory.",
        "#Weather #Instrumentation #Maintenance #Ports #Judgment",
    ),
    (
        "Visibility and radiation add-ons: niche limits that matter for some sites",
        "Some go/no-go questions are optical or thermal—not only mechanical.",
        "Add sensors when limits truly depend on them; otherwise you buy noise.",
        "#Operations #Safety #Instrumentation #Ports #Judgment",
    ),
    (
        "Mobile access: convenience vs credential sprawl",
        "Phones are normal; security policies should be too.",
        "Device management and MFA belong in the ops conversation.",
        "#CyberSecurity #Mobile #Operations #Ports #Governance",
    ),
    (
        "Integrated manoeuvre narrative vs tag soup SCADA",
        "Tags without manoeuvre context create anxiety, not awareness.",
        "Integration is a story arc—geometry, loads, environment—within one timeline.",
        "#SCADA #Integration #Operations #Ports #UX",
    ),
    (
        "Hook desk ergonomics: tension and status without cognitive overload",
        "If the UI confuses, training can’t save it forever.",
        "Validate workflows with operators under realistic scenarios.",
        "#UX #Operations #Safety #HumanFactors #Ports",
    ),
    (
        "Emergency release testing: scripted, witnessed, boring",
        "Boring tests are the ones that hold up in court and in culture.",
        "Explicit steps beat improvised heroics.",
        "#Testing #Safety #Compliance #Ports #Culture",
    ),
    (
        "Mooring efficiency: time on berth vs risk—no free lunch",
        "Faster isn’t safer unless procedures and hardware align.",
        "Measure what you optimise; sometimes the metric is risk, not minutes.",
        "#Operations #Risk #Mooring #Ports #Judgment",
    ),
    (
        "Harbor equipment as a system: interfaces beat siloed purchases",
        "Customers feel interfaces; vendors feel modules.",
        "Whole-jetty thinking shows up in commissioning and in storms.",
        "#SystemsThinking #Ports #Engineering #Commissioning #Leadership",
    ),
    (
        "Quote requests as engineering intake",
        "A good brief beats a fast price.",
        "Limits, interfaces, and ownership early—saves everyone later.",
        "#Procurement #Engineering #Ports #Professionalism #Communication",
    ),
    (
        "PDFs and training: if the team skipped the manual, the FAT will improvise",
        "Documentation is part of quality—especially when multilingual teams commission.",
        "Make reading part of the plan, not a shameful secret.",
        "#Documentation #Training #Quality #Commissioning #Ports",
    ),
    (
        "Multilingual projects: consistency across alarm text and procedures",
        "Translation errors become operational risk at night.",
        "Glossaries and review workflows matter as much as code.",
        "#i18n #Operations #Safety #Ports #Quality",
    ),
    (
        "Experience in the field: what ‘years’ actually means",
        "Tenure helps when it produces testable habits—not when it produces certainty without evidence.",
        "I stay suspicious of slogans, including my own.",
        "#Professionalism #Engineering #Learning #Maritime #Humility",
    ),
    (
        "Neutral LinkedIn practice: teach mechanics, not tribal warfare",
        "I share patterns I’ve seen—without turning posts into competitor battles.",
        "Credibility is compatible with confidentiality and respect.",
        "#ThoughtLeadership #Engineering #Ethics #Maritime #Communication",
    ),
    (
        "Workshops with authorities, EPCs, and OEMs: shared nouns",
        "Integration fails on vocabulary before it fails on wiring.",
        "Early alignment meetings are cheaper than late rewiring.",
        "#Stakeholders #Commissioning #Engineering #Ports #Communication",
    ),
    (
        "Evidence bundles for class discussions: traceability, not trophy hunting",
        "Bundles should tell a coherent story—tests, limits, changes, responsibilities.",
        "A stamp is one input among many.",
        "#Compliance #Engineering #Quality #Ports #Governance",
    ),
    (
        "Piloting new sensors: uncertainty budgets and rollback",
        "Novelty belongs under explicit limits until validated.",
        "I’d rather slow adoption with honest metrics than fast adoption with blind trust.",
        "#Innovation #Instrumentation #Risk #Ports #Judgment",
    ),
    (
        "Honest scope: what I won’t claim from a product page",
        "Field engineering needs truth boundaries—especially online.",
        "I stick to published scope and my own observations; speculation belongs in questions, not headlines.",
        "#Ethics #Engineering #Communication #Trust #Professionalism",
    ),
    (
        "Site walk mindset: observe before recommending",
        "The jetty teaches what slides cannot.",
        "Module names are less important than load paths, people, and maintenance reality.",
        "#FieldEngineering #Ports #Leadership #Judgment #Commissioning",
    ),
    (
        "One-line professional identity: mooring physics, monitoring, and humility",
        "If the sentence needs acronyms to sound smart, rewrite it.",
        "I aim for clarity—berthing and mooring as systems, not as slogans.",
        "#MarineEngineering #Ports #Professionalism #Communication #Learning",
    ),
    (
        "General vs module brochures: choose the document for the decision",
        "Nobody should read eighty pages to find one torque note.",
        "Match depth to review stage—concept, design, test, maintain.",
        "#Documentation #Engineering #Communication #Ports #Quality",
    ),
    (
        "Sector labels (LNG, O&G, offshore): same physics, different tempo and risk",
        "Labels help buyers find themselves; they don’t replace site analysis.",
        "Translate sector patterns carefully—hazard profiles differ.",
        "#LNG #Offshore #Ports #Risk #Engineering",
    ),
    (
        "Standards and procurement: useful tables, still physical jetties",
        "Standards coordinate paperwork; waves coordinate reality.",
        "I use standards as guardrails, not as substitutes for site thinking.",
        "#Standards #Engineering #Ports #Judgment #Compliance",
    ),
    (
        "Supplier diversity in port projects: comparing options without tribal warfare",
        "Engineering decisions need criteria—price, support, evidence, fit—not cheerleading.",
        "I write requirements and test plans first; names second.",
        "#Procurement #Engineering #Professionalism #Ports #Leadership",
    ),
    (
        "Writing publicly: share principles, protect client detail",
        "Useful posts teach patterns; they don’t leak site-specific secrets.",
        "Anonymise, abstract, and stay humble about what you didn’t witness.",
        "#Communication #Ethics #Engineering #Maritime #Privacy",
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

    print(f"Wrote {len(out)} neutral rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
