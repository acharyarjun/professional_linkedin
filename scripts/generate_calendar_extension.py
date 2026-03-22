#!/usr/bin/env python3
"""Append rows 101–500 to data/post_calendar.csv (run from repo root: python scripts/generate_calendar_extension.py).

For a full 500-row rebuild aligned with www.prosertek.com, use `scripts/build_prosertek_calendar.py` instead.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "post_calendar.csv"

# Deterministic variety: port automation, LNG, cranes, OT/IT, AI, Azure, field practice, Prosertek.
# Each tuple: (theme, hook, technical_angle, hashtags)
BATCH: list[tuple[str, str, str, str]] = [
    (
        "Cold-iron shore power sequencing and PLC interlocks",
        "Plug-in order is a safety story, not a cable management detail.",
        "Permissive chains aligned with vessel load shed and breaker status from SCADA.",
        "#ShorePower #PLC #Ports #Electrical #Safety",
    ),
    (
        "Ballast water treatment telemetry into terminal compliance dashboards",
        "Compliance is continuous, not a stamp at arrival.",
        "Edge buffering, timestamp integrity, and audit exports into informes-style evidence.",
        "#BallastWater #Compliance #IIoT #Ports #Traceability",
    ),
    (
        "Automatic identification of hatch cover misalignment from deck cameras",
        "A gap that looks small on paper can read huge through a lens.",
        "Edge inference with conservative false-negative policy and human confirmation queue.",
        "#ComputerVision #RoRo #Safety #EdgeAI #Ports",
    ),
    (
        "Straddle carrier fuel telemetry vs. electrification ROI narratives",
        "kWh stories need duty cycles, not brochure peaks.",
        "Energy models tied to TOS moves, maintenance windows, and tariff seasons.",
        "#Decarbonization #Analytics #TerminalOps #ROI #Ports",
    ),
    (
        "Reach stacker spreader twist-lock sensor drift",
        "Twist confidence is a loading contract.",
        "Calibration cadence, redundant sensing, and PLC permissives for lift holds.",
        "#Cranes #Instrumentation #PLC #Safety #Maintenance",
    ),
    (
        "RTG anti-collision radar vs. LiDAR in mixed weather",
        "Fog argues with every sensor differently.",
        "Sensor fusion thresholds, cleaning schedules, and maintenance-driven recalibration.",
        "#RTG #LiDAR #Radar #Ports #Automation",
    ),
    (
        "STS crane load sway models tied to operator assist limits",
        "Assist is helpful until it hides instability.",
        "Model boundaries, operator override logging, and training scenarios.",
        "#ShipToShore #Cranes #Control #HumanFactors #Ports",
    ),
    (
        "TOS integration: vessel ETA confidence intervals feeding berth planners",
        "A single ETA is optimism; an interval is operations.",
        "Quantile forecasts, weather ensembles, and berth slack policies.",
        "#TOS #Scheduling #Forecasting #Ports #Analytics",
    ),
    (
        "Container weight declaration cross-checks with crane scales",
        "Misdeclarations show up as mechanical truth.",
        "Statistical tests, exception workflows, and carrier notifications.",
        "#Container #Safety #Weights #Analytics #Ports",
    ),
    (
        "Reefer plug monitoring: alarm storms vs. actionable clusters",
        "Every reefer alarm is not an emergency; every pattern might be.",
        "Correlation windows, rack grouping, and escalation playbooks.",
        "#Reefer #AlarmManagement #IIoT #Ports #Operations",
    ),
    (
        "AGV localization in steel-heavy yards: multipath and magnetic drift",
        "GNSS is a suggestion under a gantry.",
        "Hybrid localization, landmark updates, and degraded-mode paths.",
        "#AGV #Robotics #Ports #Localization #Automation",
    ),
    (
        "Yard crane rail wear monitoring with accelerometer signatures",
        "Wear whispers in vibration before it screams in metal.",
        "Feature extraction, baseline seasons, and maintenance triggers.",
        "#ConditionMonitoring #Cranes #IIoT #Maintenance #Ports",
    ),
    (
        "Weighbridge integration: truck tare fraud checks and camera corroboration",
        "Trust, but correlate.",
        "Time-aligned weigh tickets, ANPR hooks, and exception queues.",
        "#Weighbridge #Logistics #Compliance #Ports #Integration",
    ),
    (
        "Port gate OCR misreads: confidence thresholds and manual review SLAs",
        "Automation speed without accuracy is queue creation.",
        "Confidence calibration, active learning loops, and night-shift staffing models.",
        "#OCR #Gates #Automation #Operations #Ports",
    ),
    (
        "Perimeter intrusion detection: reducing nuisance alarms from birds and waves",
        "Nature sends a lot of false positives if you listen naively.",
        "Multi-sensor fusion, zoning, and seasonal tuning.",
        "#PhysicalSecurity #AlarmManagement #Ports #Sensors #IIoT",
    ),
    (
        "Cyber range exercises for OT teams without breaking cranes",
        "Tabletops are useful; controlled injections are unforgettable.",
        "Isolated PLC benches, packet captures, and rollback images.",
        "#CyberSecurity #OT #Training #Ports #IEC62443",
    ),
    (
        "Jump host session recording for vendor remote support",
        "If you cannot replay it, you cannot improve it.",
        "Immutable logs, least-privilege tokens, and time-boxed break-glass.",
        "#OTSecurity #Governance #RemoteSupport #Compliance #Ports",
    ),
    (
        "Patch windows for Windows-based SCADA without stopping cargo",
        "Reboot politics are real politics.",
        "Redundant servers, staged clusters, and maintenance communications.",
        "#SCADA #Patching #ChangeManagement #Ports #OT",
    ),
    (
        "SNMP monitoring of industrial switches: what to poll vs. what to ignore",
        "Polling storms are self-inflicted outages.",
        "Interval policy, storm thresholds, and syslog correlation.",
        "#IndustrialNetworking #Monitoring #SNMP #Ports #OT",
    ),
    (
        "DNS and NTP hygiene on segmented OT islands",
        "Time drift is a distributed systems bug with a safety smell.",
        "Hierarchy, authentication, and monitoring for stratum and skew alarms.",
        "#OTSecurity #NTP #Network #Ports #Reliability",
    ),
    (
        "IEC 62443 zone maps that survive the next retrofit",
        "Drawings age; zones should be maintainable concepts.",
        "Living documents, conduit IDs, and periodic red-team reviews.",
        "#IEC62443 #NetworkSegmentation #Ports #CyberSecurity #Documentation",
    ),
    (
        "Siemens SCALANCE firewall rulesets: readability vs. micro-segmentation",
        "Micro-segmentation without readability becomes mystery segmentation.",
        "Naming conventions, object groups, and periodic rule audits.",
        "#SCALANCE #Firewall #OT #Ports #Security",
    ),
    (
        "Rockwell Stratix CIP Security rollout in mixed legacy I/O",
        "Security upgrades meet brownfield patience.",
        "Phased device classes, compatibility matrices, and rollback plans.",
        "#Rockwell #CIPSecurity #OT #Ports #Automation",
    ),
    (
        "Schneider EcoStruxure edge analytics for motor health",
        "Motor current is a narrative if you listen long enough.",
        "Baseline learning, alarm rationalization, and work order hooks.",
        "#EcoStruxure #Analytics #MotorControl #IIoT #Ports",
    ),
    (
        "Phoenix Contact surge protection audits near crane rails",
        "Lightning does not negotiate with your grounding sketch.",
        "Zone mapping, SPD replacement policy, and incident postmortems.",
        "#ElectricalSafety #Surge #Maintenance #Ports #Reliability",
    ),
    (
        "UPS and battery testing discipline for critical PLCs",
        "Batteries fail quietly until they fail loudly.",
        "Load tests, impedance trends, and replacement forecasting.",
        "#UPS #Power #PLC #Reliability #Ports",
    ),
    (
        "Harmonic filters after VFD fleet expansion",
        "New drives change the electrical personality of a bus.",
        "Before/after measurements, THD targets, and thermal checks on filters.",
        "#PowerQuality #Harmonics #VFD #Engineering #Ports",
    ),
    (
        "Grounding surveys for serial islands near new VFD cabinets",
        "Ground is not a slogan; it is a measured path.",
        "Impedance checks, star-point discipline, and cable routing fixes.",
        "#Grounding #Electrical #VFD #Commissioning #Ports",
    ),
    (
        "ATEX boundary walkdowns with instrument tagging consistency",
        "A missing tag is a missing conversation about ignition.",
        "Cross-check between CAD, maintenance lists, and field photos.",
        "#ATEX #Safety #Instrumentation #Compliance #Ports",
    ),
    (
        "SIL verification evidence that auditors can navigate",
        "Proof is not a pile; it is a path.",
        "Traceable test cases, signatures, and change control links.",
        "#FunctionalSafety #SIL #Validation #Compliance #Automation",
    ),
    (
        "Cause-and-effect matrices for LNG jetty upsets: readability for night shift",
        "If operators cannot rehearse it, it is not operational.",
        "Matrix structure, color semantics, and drill cadence.",
        "#CauseAndEffect #LNG #Operations #Safety #Engineering",
    ),
    (
        "Loading arm cooldown procedures encoded into permissives",
        "Cold metal and warm hurry do not mix well.",
        "Timers, temperature thresholds, and explicit operator acknowledgements.",
        "#LNG #LoadingArms #Safety #PLC #Operations",
    ),
    (
        "Vapor return line monitoring: small pressure stories, big risk",
        "Pressure oscillations can be gossip or warning.",
        "Trending, filtering, and correlation with ship manifold events.",
        "#LNG #Process #Instrumentation #Safety #Ports",
    ),
    (
        "Jetty firewater pump tests with flow provenance",
        "A pump test is also a measurement of trust.",
        "Flow meters, time-stamped logs, and deficiency workflows.",
        "#FireSafety #Pumps #Compliance #Ports #Operations",
    ),
    (
        "Ship-shore checklist digitization without losing nuance",
        "Checklists fail when they become performative tapping.",
        "Structured fields, free-text exceptions, and audit trails.",
        "#ShipShore #Digitization #Safety #Ports #Operations",
    ),
    (
        "Pilot boarding place weather limits and PLC holds",
        "Limits should be enforceable, not aspirational posters.",
        "Wind sensor fusion, conservative thresholds, and override governance.",
        "#Pilotage #Safety #Automation #Ports #Weather",
    ),
    (
        "Tug dispatch optimization vs. berth realism",
        "Optimization without berth truth is a spreadsheet fantasy.",
        "TOS integration, delay distributions, and human dispatch overrides.",
        "#TugOps #Scheduling #Ports #Analytics #Operations",
    ),
    (
        "Wave height sensors for berth operability dashboards",
        "Operators need a number they can defend, not a guess.",
        "Calibration, outlier rejection, and sensor redundancy.",
        "#Instrumentation #MarineOps #Ports #Safety #Analytics",
    ),
    (
        "Mooring line material aging and UV exposure tracking",
        "Fibers have retirement plans even if spreadsheets do not.",
        "Inspection photos, RFID tags, and replacement policies.",
        "#Mooring #Reliability #Maintenance #Ports #Safety",
    ),
    (
        "Quick release hook fleet telemetry: comparing OEMs fairly",
        "Benchmarks need identical duty cycles and maintenance histories.",
        "Normalized KPIs, failure taxonomy, and field notes.",
        "#QRH #Mooring #Analytics #Ports #Maintenance",
    ),
    (
        "Bollard pull tests and load cell traceability",
        "Pull tests are legal documents with a mechanical heart.",
        "Calibration chains, photos, and signed records into informes.",
        "#Bollards #Testing #Compliance #Ports #Traceability",
    ),
    (
        "Fender pressure monitoring vs. tactile operator intuition",
        "Sometimes the operator is right; the job is to align sensors.",
        "Human-in-the-loop calibration, drift monitoring, and training.",
        "#Berthing #HumanFactors #Instrumentation #Ports #Safety",
    ),
    (
        "Dock water level sensors and tide models for ramp angles",
        "Angles matter when vehicles meet steel.",
        "Sensor fusion with tide tables, uncertainty bands, and alarms.",
        "#RoRo #Tides #Instrumentation #Safety #Ports",
    ),
    (
        "RoRo ramp stress monitoring with strain gauges",
        "Fatigue is a slow-motion budget.",
        "Sampling rates, temperature compensation, and inspection triggers.",
        "#StructuralHealth #RoRo #Instrumentation #Ports #Risk",
    ),
    (
        "Lashing robot acceptance tests: repeatability vs. reality",
        "A demo is not a season of weather.",
        "Test matrices, wear allowances, and failure injection.",
        "#Automation #RoRo #Testing #Ports #Quality",
    ),
    (
        "Container stack stability rules encoded into TOS moves",
        "Physics is not a suggestion; it is a constraint.",
        "Rule engines, validation hooks, and exception workflows.",
        "#TOS #Safety #Containers #Software #Ports",
    ),
    (
        "Cold ironing cable management and thermal derating",
        "Current is not the only thing that heats a cable run.",
        "Routing, derating tables, and IR inspection cadence.",
        "#ShorePower #Electrical #Thermal #Ports #Maintenance",
    ),
    (
        "Port noise monitoring for community relations",
        "Decibels are diplomacy with a graph.",
        "Baseline nights, event correlation, and mitigation actions.",
        "#Community #ESG #Monitoring #Ports #Operations",
    ),
    (
        "Dust emissions from bulk handling: sensor placement pitfalls",
        "Dust is spatial; averages can lie politely.",
        "Spatial sampling, wind correlation, and mitigation triggers.",
        "#Bulk #ESG #Sensors #Ports #Operations",
    ),
    (
        "Water quality monitoring near dredging operations",
        "Turbidity is a story told in time series.",
        "Sampling rates, reference stations, and compliance reporting.",
        "#Dredging #Environment #Compliance #Ports #Monitoring",
    ),
    (
        "Berth sedimentation surveys feeding dredge planning",
        "Charts age; bottoms move.",
        "Survey integration, uncertainty, and capital planning.",
        "#Dredging #Hydrography #Ports #Planning #Operations",
    ),
    (
        "Pile integrity testing for aging dolphins",
        "Concrete has secrets; acoustics can read some of them.",
        "Testing windows, interpretation guardrails, and structural follow-up.",
        "#Infrastructure #StructuralHealth #Ports #Risk #Maintenance",
    ),
    (
        "Quay crane rail alignment surveys and GIS integration",
        "Misalignment is a maintenance accelerator.",
        "Survey cadence, tolerances, and work order automation.",
        "#Cranes #GIS #Maintenance #Ports #Engineering",
    ),
    (
        "High-mast lighting controls: glare vs. safety vs. energy",
        "Lighting is a safety instrument, not just photons.",
        "Zones, curfews, and maintenance access for lifts.",
        "#Lighting #Ports #Safety #Energy #Operations",
    ),
    (
        "Port CCTV retention policies for investigations vs. privacy",
        "Retention is not infinite; it is governance.",
        "Legal guidance, redaction workflows, and access controls.",
        "#CCTV #Privacy #Governance #Ports #Security",
    ),
    (
        "Drone surveys for stockpile volume: accuracy and repeatability",
        "A pretty mesh is not a legal volume.",
        "GCPs, ground sampling, and uncertainty statements.",
        "#Drones #Surveying #Bulk #Analytics #Ports",
    ),
    (
        "Laser scanning for retrofit clash detection",
        "Clash detection saves blood pressure and steel.",
        "Point cloud registration, tolerances, and change management.",
        "#DigitalTwin #CAD #Retrofit #Ports #Engineering",
    ),
    (
        "BIM handover to operations: what maintainers actually need",
        "A model without maintenance context is a toy.",
        "Asset IDs, spare parts links, and as-built deltas.",
        "#BIM #Handover #Maintenance #Ports #DigitalEngineering",
    ),
    (
        "API versioning for terminal partner integrations",
        "Partners drift; contracts should not surprise.",
        "Semantic versioning, deprecation windows, and compatibility tests.",
        "#API #Integration #TOS #Software #Ports",
    ),
    (
        "Idempotency keys for webhook deliveries from TOS events",
        "Exactly-once is a myth; idempotency is the adult compromise.",
        "Key design, replay testing, and dead-letter queues.",
        "#Webhooks #Reliability #TOS #Software #Ports",
    ),
    (
        "Synthetic monitoring for critical partner APIs",
        "If you do not probe it, you are guessing uptime.",
        "Canary calls, SLOs, and alerting with runbooks.",
        "#SRE #Monitoring #Integration #Ports #DevOps",
    ),
    (
        "OpenTelemetry tracing across Python services and PLC gateways",
        "A trace should survive the boundary between IT and OT.",
        "Context propagation, sampling, and redaction policies.",
        "#OpenTelemetry #Observability #IIoT #Python #Ports",
    ),
    (
        "Structured logging for commissioning events",
        "Logs are evidence when you treat them like evidence.",
        "Event schemas, correlation IDs, and export to informes.",
        "#Logging #Commissioning #Quality #Ports #Software",
    ),
    (
        "Feature flags for risky automation changes",
        "Ship fast; ship safely with toggles.",
        "Kill switches, rollout cohorts, and rollback drills.",
        "#FeatureFlags #DevOps #Automation #Ports #Software",
    ),
    (
        "Blue/green deployments for stateless services behind cranes",
        "Rolling restarts are not the same as safe cutovers.",
        "Load balancer health checks, session drains, and rollback.",
        "#BlueGreen #DevOps #Ports #Reliability #Software",
    ),
    (
        "Database migrations with zero-downtime patterns",
        "Downtime is a tax nobody wants to pay twice.",
        "Expand/contract migrations, backfills, and verification queries.",
        "#Database #Migrations #DevOps #Software #Reliability",
    ),
    (
        "Backpressure and rate limits for edge-to-cloud ingestion",
        "Cloud is patient; OT is not.",
        "Queues, batching, and offline-first buffers.",
        "#Azure #IIoT #Edge #Architecture #Ports",
    ),
    (
        "Cost governance for cloud telemetry: sampling vs. fidelity",
        "You can afford truth; you cannot afford everything at full Hz.",
        "Sampling policies, tiered storage, and KPI-driven retention.",
        "#Azure #FinOps #IIoT #Analytics #Ports",
    ),
    (
        "Private Link vs. public endpoints for OT gateways",
        "Exposure is a choice; make it explicit.",
        "Threat models, DNS, and break-glass procedures.",
        "#Azure #NetworkSecurity #OT #Ports #Cloud",
    ),
    (
        "Azure Functions cold start vs. always-on for OT integrations",
        "Cold starts are fine until they are not.",
        "Warm pools, consumption plans, and latency budgets.",
        "#Azure #Serverless #IIoT #Architecture #Ports",
    ),
    (
        "Key Vault rotation drills for service principals",
        "Rotation is a rehearsal, not a surprise party.",
        "Dual-key periods, monitoring, and rollback scripts.",
        "#Azure #Security #Secrets #DevOps #Ports",
    ),
    (
        "Defender for IoT on brownfield networks: tuning false positives",
        "Alerts without triage become wallpaper.",
        "Baseline learning, asset criticality, and suppression policies.",
        "#DefenderForIoT #CyberSecurity #OT #Ports #Azure",
    ),
    (
        "LLM-assisted post drafting with hard constraints",
        "Creativity is great; constraints are what ships.",
        "Length caps, hashtag rules, and factuality checks.",
        "#GenerativeAI #ContentOps #Governance #Ports #AI",
    ),
    (
        "RAG grounding for market insights: citation hygiene",
        "A retrieval without provenance is gossip.",
        "Chunking, source attribution, and confidence thresholds.",
        "#RAG #AI #MLOps #Ports #Trust",
    ),
    (
        "Evaluating embedding models for port maintenance notes",
        "Not all embeddings are equally salty.",
        "Benchmark tasks, multilingual coverage, and drift tests.",
        "#Embeddings #NLP #MLOps #Maintenance #Ports",
    ),
    (
        "Small language models on edge for offline assist",
        "Sometimes the cloud is a horizon away.",
        "Quantization, latency budgets, and offline update policies.",
        "#EdgeAI #LLM #IIoT #Ports #Automation",
    ),
    (
        "Bias reviews for workforce scheduling models",
        "Fairness is operational risk.",
        "Protected attributes, audits, and human-in-the-loop approvals.",
        "#ResponsibleAI #Operations #HR #Ports #Governance",
    ),
    (
        "Simulation-based stress tests for crane dispatch algorithms",
        "If you cannot break it in simulation, you will break it in production.",
        "Scenario libraries, tail metrics, and conservative rollouts.",
        "#Simulation #Algorithms #Cranes #Ports #Analytics",
    ),
    (
        "Digital twin calibration after major equipment retrofit",
        "Twins are hypotheses until they match reality.",
        "Parameter identification, sensor placement, and acceptance tests.",
        "#DigitalTwin #Calibration #Retrofit #Ports #Engineering",
    ),
    (
        "Physics-informed models for mooring line dynamics",
        "Data is not a substitute for physics; it is a partner.",
        "Hybrid modeling, uncertainty quantification, and validation data.",
        "#PhysicsML #Mooring #Simulation #Ports #AI",
    ),
    (
        "Gaussian processes for uncertainty in berth forecasts",
        "A mean without uncertainty is a bluff.",
        "Kernel choices, seasonal non-stationarity, and calibration.",
        "#GaussianProcesses #Forecasting #Ports #Analytics #ML",
    ),
    (
        "Time-series foundation models: hype vs. harbor reality",
        "Foundation models need foundations in your domain.",
        "Fine-tuning data, evaluation harnesses, and operational guardrails.",
        "#TimeSeries #AI #MLOps #Ports #Analytics",
    ),
    (
        "Coursera capstone applied to a real PLC dataset",
        "Certificates are nice; labeled datasets are nicer.",
        "Project framing, reproducibility, and field validation.",
        "#ContinuousLearning #Coursera #PLC #AI #Career",
    ),
    (
        "Spaced repetition for standards knowledge on site",
        "Standards live in memory poorly without rehearsal.",
        "Micro-drills, spaced schedules, and team quizzes.",
        "#Training #Standards #Compliance #Ports #Culture",
    ),
    (
        "Writing technical memos that survive legal review",
        "Clarity is a risk control.",
        "Structure, evidence links, and cautious language.",
        "#TechnicalWriting #Compliance #Ports #Governance",
    ),
    (
        "Post-mortems without blame: extracting durable fixes",
        "Blame ends learning early.",
        "Timeline rigor, five-whys boundaries, and action tracking.",
        "#IncidentResponse #SafetyCulture #Ports #Leadership",
    ),
    (
        "Mentoring junior engineers on commissioning nights",
        "Night shifts are classrooms with higher stakes.",
        "Pairing, checklists, and debrief rituals.",
        "#Mentoring #Commissioning #Training #Ports #Culture",
    ),
    (
        "Cross-vendor meetings: translating Siemens vs Rockwell idioms",
        "Same physics, different dialects.",
        "Glossaries, interface contracts, and integration tests.",
        "#Automation #Integration #PLC #Ports #Engineering",
    ),
    (
        "Supplier quality audits for maritime-rated enclosures",
        "An IP rating is a promise; salt fog is a test.",
        "Sample plans, test evidence, and failure taxonomy.",
        "#Quality #Procurement #Marine #Enclosures #Ports",
    ),
    (
        "Spare parts strategy for obsolete PLC modules",
        "Obsolescence is a schedule, not a surprise.",
        "Lifecycle buys, emulation options, and migration plans.",
        "#Obsolescence #PLC #Maintenance #Ports #Risk",
    ),
    (
        "Contract clauses for software updates in OT environments",
        "Updates are changes; changes need governance.",
        "Testing windows, rollback rights, and liability boundaries.",
        "#Contracts #OT #ChangeManagement #Ports #Governance",
    ),
    (
        "Insurance questionnaires: translating technical truth to forms",
        "Forms want certainty; you owe calibrated honesty.",
        "Evidence bundles, conservative claims, and appendices.",
        "#Risk #Insurance #Compliance #Ports #Engineering",
    ),
    (
        "Class society discussions on novel automation concepts",
        "Novelty needs evidence, not enthusiasm.",
        "Test plans, hazard studies, and incremental approvals.",
        "#Classification #Safety #Automation #Maritime #Engineering",
    ),
    (
        "Port authority stakeholder mapping for digital projects",
        "Projects fail on interfaces between humans.",
        "RACI clarity, cadence, and decision rights.",
        "#ProjectManagement #Stakeholders #Ports #Digital",
    ),
    (
        "Value engineering without safety compromise",
        "Cost cuts should not cut evidence.",
        "Trade-off matrices, independent checks, and documentation.",
        "#ValueEngineering #Safety #Projects #Ports #Engineering",
    ),
    (
        "Commissioning FAT vs SAT evidence separation",
        "Factory proof is not site proof.",
        "Traceable test cases, environment differences, and deltas.",
        "#FAT #SAT #Commissioning #Quality #Ports",
    ),
    (
        "Handover packages that operators will actually open",
        "If it is PDF-only, it is shelf-only.",
        "Searchable portals, short videos, and quick links.",
        "#Handover #Documentation #Operations #Ports #UX",
    ),
    (
        "informes.prosertek.com: structured evidence for mixed audiences",
        "Auditors and operators read differently; serve both.",
        "Templates, access tiers, and export formats.",
        "#Prosertek #Compliance #Documentation #Ports #Software",
    ),
    (
        "Linking SCADA alarms to PDF page anchors",
        "Context should be one click, not one meeting.",
        "Deep links, stable IDs, and maintenance of mappings.",
        "#HMI #Documentation #Operations #Ports #UX",
    ),
    (
        "Mobile field capture for photos with metadata integrity",
        "Photos without timestamps are souvenirs.",
        "EXIF policies, GPS cautions, and upload workflows.",
        "#FieldOps #Mobile #IIoT #Ports #Traceability",
    ),
    (
        "Barcode/QR workflows for spare parts in salt air",
        "Labels fade; processes should not.",
        "Material choices, reprints, and verification scans.",
        "#Maintenance #Spares #Ports #Operations #Quality",
    ),
    (
        "Voice notes for hands-free observations during rounds",
        "Hands-free is safety; transcripts are evidence.",
        "ASR quality, PII redaction, and retention hooks.",
        "#FieldOps #Speech #IIoT #Ports #Safety",
    ),
    (
        "Wearable alerts for lone worker in confined spaces",
        "Lone does not mean unmonitored.",
        "Geofencing, escalation timers, and gas integration.",
        "#Safety #LoneWorker #IIoT #Ports #Operations",
    ),
    (
        "Heat stress monitoring for stevedores in summer berths",
        "Heat is a hazard with a dose response.",
        "WBGT, work-rest policies, and hydration telemetry.",
        "#Safety #OccupationalHealth #Ports #Operations #ESG",
    ),
    (
        "Noise dosimetry for crane cabin ergonomics",
        "Noise is cumulative; controls are not optional.",
        "Dosimetry campaigns, cabin sealing, and maintenance of seals.",
        "#Ergonomics #Safety #Cranes #Ports #Health",
    ),
    (
        "Fatigue risk modeling for shift schedules",
        "Fatigue is a systems property, not a personal failing.",
        "Shift patterns, circadian science, and conservative limits.",
        "#Fatigue #Operations #Safety #Ports #HumanFactors",
    ),
    (
        "Human factors review of new HMI color palettes",
        "Color is semantics; semantics can be safety.",
        "Contrast, alarm salience, and color-blind checks.",
        "#HMI #HumanFactors #Safety #Ports #Design",
    ),
    (
        "Accessibility in terminal kiosks for diverse crews",
        "Accessibility is operational efficiency.",
        "Font sizes, contrast, multilingual toggles, and testing.",
        "#Accessibility #UX #Ports #Operations #Design",
    ),
    (
        "Gamification for safety training: rewards vs. distortion",
        "Games can teach; games can also hide truth.",
        "Metrics that align with real risk reduction.",
        "#Training #Safety #Gamification #Ports #Culture",
    ),
    (
        "Virtual reality crane simulators: fidelity budgets",
        "VR is expensive; wrong physics is expensive too.",
        "Motion cues, latency targets, and validation.",
        "#VR #Training #Cranes #Simulation #Ports",
    ),
    (
        "Serious games for emergency response drills",
        "Drills should be stressful, not chaotic.",
        "Scenarios, scoring, and debrief capture.",
        "#Training #EmergencyResponse #Ports #Simulation",
    ),
    (
        "Cross-training electricians and PLC programmers",
        "T-shaped skills reduce midnight finger-pointing.",
        "Curriculum boundaries, safety boundaries, and mentorship.",
        "#Training #Automation #Electrical #Ports #Culture",
    ),
    (
        "Writing ladder logic that your future self forgives",
        "Cleverness ages poorly; clarity ages well.",
        "Comment discipline, rung boundaries, and naming conventions.",
        "#PLC #BestPractices #Automation #Ports #Software",
    ),
    (
        "Unit tests for structured text safety interlocks",
        "Tests are not optional for interlocks.",
        "Simulation harnesses, coverage, and regression gates.",
        "#PLC #Testing #Safety #Automation #Ports",
    ),
    (
        "Static analysis for PLC codebases",
        "Bugs in logic are bugs in physics.",
        "Tooling rules, false positives, and CI integration.",
        "#PLC #StaticAnalysis #DevOps #Automation #Ports",
    ),
    (
        "Containerized CI pipelines for Python services on-prem",
        "Repeatable builds are a security posture.",
        "Image signing, SBOMs, and air-gapped registries.",
        "#DevOps #Containers #Security #Ports #Software",
    ),
    (
        "SBOM practices for OT software deliveries",
        "You cannot patch what you cannot inventory.",
        "Formats, vendor expectations, and verification.",
        "#SBOM #SupplyChain #CyberSecurity #OT #Ports",
    ),
    (
        "Signing firmware artifacts for field devices",
        "Trust chains should end in verified bits.",
        "Key management, rotation, and rollback procedures.",
        "#Firmware #Security #OT #Ports #Automation",
    ),
    (
        "Secure boot considerations for industrial PCs",
        "Boot integrity is the first line of defense.",
        "TPM usage, measured boot, and policy enforcement.",
        "#SecureBoot #OTSecurity #IIoT #Ports #CyberSecurity",
    ),
    (
        "EDR on OT servers: performance vs. coverage trade-offs",
        "Security tools can become denial-of-service.",
        "Exclusions, performance baselines, and monitoring.",
        "#EDR #OTSecurity #Windows #Ports #CyberSecurity",
    ),
    (
        "Immutable infrastructure for telemetry collectors",
        "Drift is a vulnerability class.",
        "Image builds, redeploy patterns, and config separation.",
        "#DevOps #IIoT #Security #Ports #Reliability",
    ),
    (
        "Disaster recovery drills for cloud data pipelines",
        "Backups are hypotheses until you restore.",
        "RTO/RPO targets, test cadence, and runbooks.",
        "#DR #Azure #Reliability #Ports #Operations",
    ),
    (
        "Multi-region failover for non-critical analytics",
        "Tier your availability; not everything needs the same drama.",
        "Business impact tiers, RPO realism, and cost trade-offs.",
        "#Azure #Reliability #Analytics #Ports #Architecture",
    ),
    (
        "Data residency constraints for EU port operations",
        "Law is not a cloud checkbox.",
        "Region choices, encryption, and subprocessors.",
        "#GDPR #Cloud #Compliance #Ports #Governance",
    ),
    (
        "Anonymization of crew and truck data in analytics",
        "Utility without surveillance.",
        "k-anonymity, aggregation, and policy review.",
        "#Privacy #Analytics #Ports #Governance #ESG",
    ),
    (
        "Carbon accounting for terminal energy: scope boundaries",
        "Scope confusion becomes greenwashing.",
        "Boundary definitions, metering, and audit evidence.",
        "#CarbonAccounting #ESG #Ports #Energy #Compliance",
    ),
    (
        "Scope 2 vs Scope 3 for purchased electricity vs logistics",
        "Categories matter; double counting hurts credibility.",
        "Emission factors, supplier data, and reconciliation.",
        "#ESG #Carbon #Ports #Logistics #Compliance",
    ),
    (
        "Battery storage at port sites: cycling strategies",
        "Batteries are financial instruments with chemistry.",
        "Degradation models, tariff arbitrage, and safety envelopes.",
        "#EnergyStorage #Ports #Decarbonization #Analytics #Engineering",
    ),
    (
        "Onshore power quality at berth: flicker and harmonics",
        "Ships are loads with opinions.",
        "Measurement campaigns, mitigation, and contractual limits.",
        "#PowerQuality #ShorePower #Ports #Electrical #Engineering",
    ),
    (
        "Microgrid controls for islanded port sections",
        "Island mode is a different control philosophy.",
        "Frequency stability, load shedding, and resynchronization.",
        "#Microgrid #Power #Ports #Automation #Reliability",
    ),
    (
        "EV charging for port equipment: load management",
        "Charging is not infinite; feeders are finite.",
        "Load scheduling, demand charges, and safety interlocks.",
        "#EV #Energy #Ports #Operations #Decarbonization",
    ),
    (
        "Hydrogen handling narratives: engineering vs marketing",
        "Hydrogen is simple atoms; systems are not.",
        "Safety cases, sensor suites, and conservative rollout.",
        "#Hydrogen #Safety #Ports #Energy #Engineering",
    ),
    (
        "Ammonia as fuel: sensor suites and alarm philosophy",
        "New molecules need new alarm cultures.",
        "Toxic gas detection, redundancy, and training.",
        "#AlternativeFuels #Safety #Ports #Instrumentation #Risk",
    ),
    (
        "Cyber-physical testing of new fuel interlocks",
        "Fuels change permissive stories.",
        "Integrated test plans, hazard analysis, and rollback.",
        "#FunctionalSafety #Automation #Ports #Energy #Compliance",
    ),
    (
        "Terminal throughput KPIs without gaming metrics",
        "What gets measured gets gamed; design metrics carefully.",
        "Balanced scorecards, anomaly reviews, and leadership audits.",
        "#KPIs #Operations #Ports #Analytics #Leadership",
    ),
    (
        "Queueing theory for truck gates: expectations vs reality",
        "Models are maps; tail behavior is terrain.",
        "Arrival distributions, staffing, and peak policies.",
        "#Queueing #Operations #Ports #Analytics #Logistics",
    ),
    (
        "Simulation of yard congestion under disruption scenarios",
        "Disruptions are not outliers; they are seasons.",
        "Scenario libraries, random seeds, and mitigation plans.",
        "#Simulation #YardOps #Ports #Resilience #Analytics",
    ),
    (
        "Port resilience: rerouting plans during berth outages",
        "Resilience is choreography under uncertainty.",
        "Playbooks, communications, and partner coordination.",
        "#Resilience #Operations #Ports #Risk #Planning",
    ),
    (
        "Pandemic-era lessons applied to operational continuity",
        "Some lessons should be institutionalized, not nostalgic.",
        "Remote support patterns, staffing buffers, and hygiene tech.",
        "#Continuity #Operations #Ports #Risk #Leadership",
    ),
    (
        "Union coordination for automation rollouts",
        "Automation is social change with hardware.",
        "Engagement cadence, training investment, and job redesign.",
        "#ChangeManagement #Automation #Ports #Culture #Leadership",
    ),
    (
        "KPI dashboards for maintenance backlog health",
        "Backlogs are not just counts; they are risk profiles.",
        "Age distributions, criticality weighting, and SLA realism.",
        "#Maintenance #KPIs #Ports #Analytics #Operations",
    ),
    (
        "Root cause analysis templates for intermittent faults",
        "Intermittent faults need disciplined narratives.",
        "Data capture, correlation windows, and hypothesis tracking.",
        "#RCA #Maintenance #Reliability #Ports #Engineering",
    ),
    (
        "Reliability center maintenance for rotating equipment",
        "Not every asset deserves the same policy.",
        "Criticality, failure modes, and task bundling.",
        "#RCM #Maintenance #Reliability #Ports #Engineering",
    ),
    (
        "Spare parts criticality scoring with risk matrices",
        "ABC classification is a start, not the end.",
        "Risk matrices, lead times, and operational impact.",
        "#Spares #Inventory #Risk #Ports #Operations",
    ),
    (
        "Vendor lock-in mitigation for PLC ecosystems",
        "Lock-in is a risk; document the exit ramps.",
        "Portability patterns, abstraction layers, and contract terms.",
        "#Automation #PLC #Risk #Ports #Strategy",
    ),
    (
        "Open-source tooling adoption in conservative OT",
        "Open source is not free; it is inspectable.",
        "Support models, licensing reviews, and security posture.",
        "#OpenSource #OT #Software #Ports #Governance",
    ),
    (
        "Long-term support strategies for Python runtimes",
        "Runtime drift is security drift.",
        "Pinned versions, CVE monitoring, and upgrade cadence.",
        "#Python #Security #DevOps #Ports #Software",
    ),
    (
        "Container scanning in CI for supply chain risk",
        "Images are dependencies with shells.",
        "Trivy/Grype policies, severity thresholds, and exceptions.",
        "#DevSecOps #Containers #CI #Ports #Security",
    ),
    (
        "Secrets scanning in CI for accidental commits",
        "Secrets in git are incidents waiting for a clone.",
        "Pre-commit hooks, server-side scans, and rotation playbooks.",
        "#DevSecOps #Secrets #GitHub #Ports #Security",
    ),
    (
        "Dependency pinning vs. updates for internal tools",
        "Stability is a feature; stagnation is a vulnerability.",
        "Renovate bots, test harnesses, and staged rollouts.",
        "#Dependencies #DevOps #Software #Ports #Security",
    ),
    (
        "Performance budgets for web dashboards used on tablets",
        "Slow dashboards become ignored dashboards.",
        "Bundle budgets, caching, and field testing on LTE.",
        "#WebPerf #UX #Ports #Software #Operations",
    ),
    (
        "Offline-first UX for field maintenance apps",
        "Wi-Fi is a wish, not a guarantee.",
        "Local caches, conflict resolution, and sync telemetry.",
        "#OfflineFirst #Mobile #IIoT #Ports #Software",
    ),
    (
        "Accessibility in internal engineering portals",
        "Internal tools are still professional products.",
        "WCAG targets, keyboard paths, and testing.",
        "#Accessibility #UX #Ports #Software #Operations",
    ),
    (
        "Search relevance tuning for technical document portals",
        "Search is ranking; ranking is product.",
        "Synonyms, boosting, and feedback loops from operators.",
        "#Search #UX #Documentation #Ports #Software",
    ),
    (
        "A/B testing copy for safety alerts: ethics and clarity",
        "A/B tests can be ethical if they improve comprehension.",
        "Human review, metrics, and rollback criteria.",
        "#UX #Safety #HumanFactors #Ports #Experimentation",
    ),
    (
        "Internationalization for multi-lingual crews",
        "Translation is not just words; it is context.",
        "Glossary control, review workflows, and RTL considerations.",
        "#i18n #Operations #Ports #UX #Culture",
    ),
    (
        "Time zones and DST in scheduling logs",
        "DST is a recurring bug in human time.",
        "UTC storage, local display, and test harnesses.",
        "#Software #Timezones #Operations #Ports #Reliability",
    ),
    (
        "Clock sync across distributed PLCs for event correlation",
        "Correlation requires a shared clock story.",
        "PTP vs NTP, domain boundaries, and monitoring.",
        "#TimeSync #PLC #IIoT #Ports #Diagnostics",
    ),
    (
        "Log correlation IDs across OT gateways and cloud",
        "Tracing is a team sport across layers.",
        "ID propagation, header policies, and retention alignment.",
        "#Observability #Integration #IIoT #Ports #Software",
    ),
    (
        "Dead letter queues for failed integration messages",
        "Failure should be visible, not silent.",
        "DLQ policies, replay tools, and alerting.",
        "#Messaging #Reliability #Integration #Ports #Software",
    ),
    (
        "Exactly-once illusions in MQTT at-least-once reality",
        "Engineering honesty prevents duplicate incidents.",
        "Idempotency keys, dedupe windows, and test cases.",
        "#MQTT #IIoT #Reliability #Software #Ports",
    ),
    (
        "Sparkplug B topic conventions for uniform namespaces",
        "Namespaces are contracts between vendors.",
        "Topic maps, validation, and onboarding checklists.",
        "#Sparkplug #MQTT #IIoT #Integration #Ports",
    ),
    (
        "OPC UA companion specs for cranes: adoption realities",
        "Standards accelerate when tooling exists.",
        "Mapping effort, server validation, and client testing.",
        "#OPCUA #Cranes #Interoperability #Ports #Standards",
    ),
    (
        "EtherNet/IP device description files vs. reality",
        "EDS files are promises; reality is commissioning.",
        "Staging, parameter validation, and vendor support.",
        "#EthernetIP #Commissioning #Automation #Ports #Rockwell",
    ),
    (
        "PROFINET naming consistency across large sites",
        "Names are navigation; chaos is downtime.",
        "Naming conventions, automated audits, and discovery.",
        "#PROFINET #Siemens #Networking #Ports #Automation",
    ),
    (
        "Modbus TCP mapping tables as versioned artifacts",
        "Mapping tables are code.",
        "Git workflows, review, and field verification hooks.",
        "#Modbus #Integration #DevOps #Ports #Software",
    ),
    (
        "BACnet in port buildings: HVAC vs OT boundaries",
        "Comfort systems still touch the security story.",
        "Segmentation, BACnet/SC, and monitoring.",
        "#BACnet #BuildingAutomation #OTSecurity #Ports #IIoT",
    ),
    (
        "LoRaWAN for low-power sensors in large yards",
        "Low power is not free; it is constrained physics.",
        "Gateway placement, duty cycles, and join security.",
        "#LoRaWAN #IIoT #Sensors #Ports #Networking",
    ),
    (
        "5G private networks for AGVs: latency claims vs measurements",
        "Latency marketing is not latency measurement.",
        "Field trials, jitter, and failover behaviors.",
        "#Private5G #AGV #Ports #Networking #Latency",
    ),
    (
        "Wi-Fi mesh in metal-heavy environments: design traps",
        "Metal is RF's favorite mirror.",
        "Site surveys, AP placement, and antenna choices.",
        "#WiFi #IndustrialNetworking #Ports #Commissioning",
    ),
    (
        "Satellite backup links for critical telemetry",
        "Backhaul diversity is resilience.",
        "Latency budgets, QoS, and cost controls.",
        "#Networking #Resilience #IIoT #Ports #Operations",
    ),
    (
        "Packet capture storage policies for OT investigations",
        "PCAPs are sensitive; retention is governance.",
        "Encryption, access controls, and minimization.",
        "#PCAP #OTSecurity #Governance #Ports #Diagnostics",
    ),
    (
        "Threat modeling for crane remote support",
        "Remote support is a threat surface.",
        "STRIDE workshops, mitigations, and monitoring.",
        "#ThreatModeling #OTSecurity #Cranes #Ports #CyberSecurity",
    ),
    (
        "Ransomware response playbooks for OT environments",
        "Panic is not a procedure.",
        "Isolation steps, backups, and vendor coordination.",
        "#Ransomware #OTSecurity #IncidentResponse #Ports #CyberSecurity",
    ),
    (
        "Insider risk controls for OT credentials",
        "Trust is not a credential policy.",
        "PAM, least privilege, and session reviews.",
        "#Identity #OTSecurity #Governance #Ports #CyberSecurity",
    ),
    (
        "Audit logging for OT administrator actions",
        "Who changed what and when is non-negotiable.",
        "Immutable logs, correlation, and SIEM integration.",
        "#Audit #OTSecurity #Governance #Ports #SIEM",
    ),
    (
        "SIEM use cases for OT: signal vs noise",
        "SIEM without tuning is expensive noise.",
        "Use case design, baselines, and iterative refinement.",
        "#SIEM #OTSecurity #CyberSecurity #Ports #Operations",
    ),
    (
        "Purple teaming for OT: constructive adversaries",
        "Attackers are not the only adversaries; complacency is.",
        "Scenarios, safe tooling, and remediation tracking.",
        "#PurpleTeam #CyberSecurity #OT #Ports #Training",
    ),
    (
        "Security awareness for operators: practical scenarios",
        "Awareness is not slides; it is rehearsal.",
        "Phishing sims, USB policies, and reporting culture.",
        "#SecurityAwareness #Training #OT #Ports #Culture",
    ),
    (
        "Vendor SOC coordination during incidents",
        "Incidents are cross-company puzzles.",
        "Contact trees, NDAs, and evidence sharing.",
        "#IncidentResponse #Vendors #Ports #CyberSecurity #Governance",
    ),
    (
        "Insurance-driven cybersecurity improvements: ROI reality",
        "Insurance asks for evidence, not intentions.",
        "Control mapping, gap closure, and premium impacts.",
        "#CyberInsurance #Risk #Ports #Governance #Security",
    ),
    (
        "Board-level reporting on OT cyber risk",
        "Boards need clarity, not acronyms soup.",
        "Risk registers, trends, and investment narratives.",
        "#Governance #CyberSecurity #Ports #Leadership #Risk",
    ),
    (
        "Capital planning for OT modernization",
        "Modernization is a portfolio, not a project.",
        "Prioritization, risk, and staged funding.",
        "#Strategy #OT #Ports #Investment #Leadership",
    ),
    (
        "Career paths for automation engineers in maritime",
        "Careers are systems; systems need feedback.",
        "Skill ladders, mentorship, and cross-training.",
        "#Career #Maritime #Automation #Ports #Culture",
    ),
    (
        "Publishing technical credibility on LinkedIn without oversharing",
        "Credibility is compatible with confidentiality.",
        "Abstraction, anonymization, and client respect.",
        "#LinkedIn #ThoughtLeadership #Engineering #Ports #Prosertek",
    ),
    (
        "Building a personal knowledge base from site notes",
        "Notes are assets when they are searchable.",
        "Tagging, retrieval, and weekly review habits.",
        "#KnowledgeManagement #Engineering #Ports #Productivity",
    ),
    (
        "Writing postmortems that improve vendor relationships",
        "Blameless does not mean consequence-free learning.",
        "Shared timelines, evidence, and joint actions.",
        "#VendorManagement #Quality #Ports #Engineering",
    ),
    (
        "Ethical storytelling from field engineering",
        "Stories teach; details can harm.",
        "Anonymization patterns and approval gates.",
        "#Ethics #Communications #Engineering #Ports #Leadership",
    ),
    (
        "Balancing billable work with deep learning",
        "Learning is maintenance for your brain.",
        "Time blocks, project tie-ins, and community learning.",
        "#Career #Learning #Engineering #AI #Balance",
    ),
    (
        "Teaching stakeholders what 'good' automation looks like",
        "Good automation is observable, testable, and maintainable.",
        "Demonstrations, metrics, and acceptance criteria.",
        "#Stakeholders #Automation #Ports #Leadership #Quality",
    ),
    (
        "Final checklist: moving from test runs to production posting",
        "Production is a configuration, not a mood.",
        "Secrets, dry-run toggles, and monitoring.",
        "#DevOps #Operations #Ports #Automation #Reliability",
    ),
]

# Ensure we can generate exactly 400 rows by cycling and lightly varying themes.
assert len(BATCH) >= 100  # noqa: S101


def main() -> None:
    existing: list[dict[str, str]] = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.append(row)

    last_day = max(int(r["day"]) for r in existing)
    if last_day != 100:
        raise SystemExit(f"Expected last day 100 in CSV, got {last_day}")

    out: list[dict[str, str]] = list(existing)
    for day in range(101, 501):
        base = BATCH[(day - 101) % len(BATCH)]
        theme, hook, tech, tags = base
        # Light uniqueness so adjacent rows are not identical when BATCH cycles.
        cycle = (day - 101) // len(BATCH)
        if cycle:
            theme = f"{theme} (series {cycle + 1})"
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
        writer = csv.DictWriter(f, fieldnames=["day", "theme", "hook", "technical_angle", "hashtags"])
        writer.writeheader()
        writer.writerows(out)

    print(f"Wrote {len(out)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
