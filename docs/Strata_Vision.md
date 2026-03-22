







STRATA
Product Vision Document

A living model of every home in Zürich.
Not a listing platform. Housing infrastructure.










Denis | March 2026
 
The Vision
Strata is a spatial intelligence platform for the Zürich housing market. It inverts the fundamental model of every existing rental platform: instead of starting from listings (what’s available right now), it starts from the built environment (what exists). Every residential unit in Zürich becomes a persistent object in a living registry, whether it’s on the market or not.
Users don’t search for apartments. They explore the city, understand neighborhoods, pin the specific units they want, and wait — with intelligent prediction and a pre-assembled application ready to fire the moment opportunity meets readiness.
Finding a home in Zürich stops feeling like a lottery and starts feeling like an informed, empowered decision — which is what it should have been all along.

Foundation: The Unit Registry
The Unit Registry is Strata’s core data asset. Not listings. Not availability. A persistent record of every residential unit in Zürich, modeled as an object with its own identity regardless of who lives there or whether it’s on the market.
Each unit record contains the physical layout, floor, orientation, approximate size, building typology (Altbau, Neubau, Genossenschaft, converted industrial), the Verwaltung responsible for it, and whatever visual or spatial data can be assembled from building permits, past listings, developer marketing, or tenant contributions.
Geographic Scope
Zürich only at launch. The data density is high enough to make the product feel complete in one city before expanding. Stadt Zürich and its immediate agglomeration (Wallisellen, Schlieren, Dietikon, Dübendorf, etc.) form the initial coverage area.

Data Acquisition: Populating the Registry
The registry is populated through four tiers of data sources, each with different coverage, reliability, and accessibility. Priority order reflects what can be done unilaterally versus what requires external cooperation.
Tier 1 — Public Records & Building Data
The Gebäude- und Wohnungsregister (GWR) is the federal register of every building and dwelling in Switzerland. It already contains unit counts per building, room counts, floor area, construction year, and building type. This is the skeleton. Layered on top:
•	Baugesuche and Baubewilligungen (building permits) for new construction and major renovations
•	Cadastral data from the Grundbuchamt for parcel boundaries and ownership structures
•	Statistisches Amt data at the Quartier level for demographic and economic context
This tier alone yields a surprisingly complete structural registry — every address, every building, every unit count, construction era, and typology — without needing anyone’s permission.
Tier 2 — Historical Listing Archaeology
Every time a unit has been listed on Homegate, Flatfox, Immoscout, or WG-Zimmer, photos, floor plans, descriptions, and pricing were publicly visible. Most of that data has disappeared from the live web, but it exists in web archives, cached pages, and can be systematically scraped going forward.
Over time, every unit that turns over even once gets enriched with interior data — photos, layout details, Ausbaustandard, sometimes 3D tours. This is a compounding asset: the longer Strata runs, the richer every unit record becomes.
Tier 3 — Tenant Contributions
Current and former tenants voluntarily adding details about their units: photos, real Nebenkosten figures, Verwaltung responsiveness, noise levels, Schimmel issues. This is the layer that makes units feel real rather than abstract database entries.
Incentive design: you contribute data about your place, you get access to richer data about places you’re considering. Reviews are anonymous by default with optional pseudonym for reputation building.
Tier 4 — Verwaltung & Genossenschaft Partnerships
Large property managers (Livit, Wincasa, Privera) and Genossenschaften (ABZ, Kraftwerk1) have detailed inventories. If Strata offers them reduced vacancy, pre-qualified pipelines, and demand analytics in return, they may share structured data: unit plans, standard finishes, turnover schedules, waitlist structures.
This tier is relationship-driven and slow to build, but it’s where the deepest, most reliable data lives. It comes last because it requires the platform to already have leverage.

Layer 1: Neighborhood Intelligence
This layer answers the question most people actually start with but no platform helps them articulate: “Where should I live?” Not which apartment. Where. The apartment comes after.
Practical Dimension
Commute time to a specific address modeled by mode and time of day using real ZVV/SBB schedule data. Walking distances to groceries, pharmacies, gyms, coworking spaces. Parking availability and cost. Proximity to specific schools or Kitas with actual availability data.
Sensory Dimension
Noise mapping from Zürich’s Lärmkarten (measured decibel levels by source: road, rail, air). Sunlight modeling using building height data and solar angle calculations per floor per season. Green space access weighted by crowding. Air quality from BAFU monitoring stations.
Social & Cultural Dimension
Demographic composition from Statistik Stadt Zürich — age distribution, household types, foreign national percentage, income brackets — presented as readable neighborhood profiles. Density and character of nightlife, restaurants, cafés, cultural venues characterized by typology, not just count.
Trajectory Dimension
Not just what a neighborhood is but where it’s going. Construction permit concentration, commercial lease activity trends, rent trajectory analysis at the Quartier level, demographic shifts year over year. Answers questions like “Is Altstetten still up-and-coming or has it peaked?”
Key Features
•	Personalized scoring: every neighborhood gets a “your match” rating based on your stated preferences and profile
•	Comparison mode: side-by-side neighborhood profiles on any dimensions, draggable like cards
•	Local insider tips: qualitative knowledge from tenant contributions surfaced contextually

Layer 2: Tenant & Demand Side
The Profile Vault
A single verified profile holding all application documents: Betreibungsauszug, Lohnausweis, employer reference, ID copy, personal introduction letter. Verified meaning the platform confirms document authenticity. The landlord sees a trust signal (“platform-verified as of this date”) rather than a raw PDF stack.
Beyond documents, the vault holds the tenant’s soft story — who they are, why they’re looking, what kind of tenant they’ll be — with the framing adapted per application based on what each Verwaltung values.
Wishlist & Watch System
Demand expressed at three levels of specificity:
•	Broad: “2.5 rooms in Kreis 3–5, under 2200 CHF, available from August.” A traditional saved search as a persistent alert.
•	Typological: “I like buildings like Zwicky or Kalkbreite.” Strata matches on structural and community attributes, not just filters.
•	Specific: “I want this unit. Watch it. Tell me when it moves.” A pin on a registry entry, connected to the prediction engine.
All three levels coexist as a layered demand profile, continuously matched against the evolving supply picture.
The Application Engine
When opportunity arises, Strata assembles a tailored application from the vault. It knows from accumulated outcome data what each Verwaltung values — document ordering, letter tone, submission timing. Over thousands of applications, it builds a model of what actually wins and feeds that intelligence back to every user.

Layer 3: Privacy & Trust Architecture
Principle 1 — Tenant Owns Their Data
Structurally, not rhetorically. Applications are presented as credential views, not document handoffs. The landlord sees verified income brackets without downloading a Lohnausweis. A clean Betreibungsauszug is confirmed without providing a copyable PDF. When an application is withdrawn, access retracts. No lingering documents in anyone’s inbox.
Principle 2 — Anonymity by Default
Demand analytics, neighborhood intelligence, application success patterns — all collective features run on aggregated, de-identified data. The aggregation layer is architecturally separated from the identity layer so that even a breach of the analytics side reveals nothing personal. Tenant contributions are anonymous by default with optional pseudonym for reputation.
Principle 3 — Transparency About Inferences
Every recommendation and score is explainable. If Strata says “your chances here are low,” you can ask why and get a real answer: “this Verwaltung has historically favored families with children and your profile is a single professional.” No black boxes. Honest about what the platform cannot protect you from — bias in human decision-making — while making that bias visible at scale.
Verification Mechanics
•	Betreibungsauszug: Ideally a real-time API query to the Betreibungsamt (Zürich is digitizing). Fallback: upload with document integrity checks against known format templates.
•	Income: Open Banking connection via bLink (SIX) confirming recurring salary deposits as a derived fact. Fallback: structured employer verification confirming status and salary band.
•	Identity: Swiss ID or Ausländerausweis verified once via standard KYC (Swisscom Digital Identity / IDnow). Persists on platform until document expiry.
•	References: Structured reference requests with specific Y/N questions rather than free-form letters. Response rate tracking builds composite confidence.
All verifications roll up into a transparency indicator: “fully verified: identity, income, debt record, two references.” Fully verified profiles are surfaced preferentially — not because they’re “better” tenants, but because verification removes uncertainty.

Layer 4: Availability & Prediction
The feature that makes Strata feel like magic. It answers: when will this apartment become available?
Signal Categories
•	Structural patterns: Student apartments near ETH/UZH cycle July–September. Expat-heavy buildings correlate with 2–3 year corporate rotation cycles. Genossenschaften turn over in predictable life-stage patterns. These form a base-rate prior per unit type and building.
•	Market & regulatory signals: Referenzzinssatz changes triggering departures, employer relocations shifting demand geography, new construction creating pull, ZVV extensions changing commute calculus.
•	Behavioral micro-signals: Furniture listings on Tutti/Ricardo, LinkedIn location changes, Nachmieter posts on WG-Zimmer. Only publicly available information, never private communications, always presented as probability.
•	Direct inputs: Current tenants who are Strata users searching for new apartments. Voluntary departure signals (“I’m moving out in three months”) formalizing the Nachmieter process as a direct handoff pipeline.
Output
A per-unit qualitative heat indicator: “low likelihood in the next 6 months,” “moderate — conditions suggest possible turnover this year,” “high — multiple signals detected.” Escalating notifications as probability shifts, giving watchers time to prepare before a listing appears.

Layer 5: Marketplace & Business Model
Tenant Side — Freemium with Pro Tier
•	Free: The map, neighborhood intelligence, basic listing alerts, simple unverified profile. Genuinely useful. Builds the user base.
•	Pro (15–25 CHF/month): Full verification suite, application engine with tailored submissions, unit watchlist with availability predictions, priority notifications, application success analytics.
Landlord/Verwaltung Side — SaaS + Placement
•	Demand Intelligence Dashboard: Pre-qualified demand for their buildings before a unit is even listed. “47 verified users are watching your building; 14 match the unit becoming available.”
•	Verified Applicant Pipeline: Pre-screened, trust-scored applicants with match rankings tailored to each Verwaltung’s known preferences. Cuts processing from 20 hours to 2 per unit.
•	Vacancy Minimization: Predictive turnover alerts plus instant pipeline activation at Kündigung. Goal: compress vacancy from weeks to days.
•	Tenant Retention Intelligence: Satisfaction signals, Nebenkosten complaints, maintenance responsiveness ratings surfaced as actionable portfolio insights.
Pricing: Monthly SaaS fee scaled by portfolio size (200–500+ CHF/month) plus per-placement fee (approximately one week’s rent per successful fill).
Data Revenue
Aggregated, anonymized demand data sold to urban planners, developers, retailers, and researchers. Genuinely anonymized, sold only in aggregate, with tenant awareness and ideally benefit-sharing (reduced subscription costs).
Principles
Never charge tenants per application. Never take commissions that inflate rent. Never sell preferential placement. Never create a pay-to-win dynamic. The moment it reproduces inequality, it has failed.

Layer 6: Financial Modeling
True Cost of Living per Unit
Every unit in the registry — available or not — gets a modeled total monthly cost: base rent (Nettomiete), estimated Nebenkosten from building data and tenant actuals, energy costs from GEAK ratings and current fuel/electricity prices, commute costs (ZVV Abo for specific zones or fuel/parking), and municipal tax impact based on Gemeinde rates at the tenant’s income level.
A 2,400 CHF apartment in a poorly insulated building in a far zone with high Nebenkosten and a high Gemeinde tax rate might cost more than a 2,700 CHF apartment in a well-connected, efficient building in a tax-favorable municipality. That insight changes decisions.

Rent Trajectory Forecasting
Forward-looking rent projections tied to Referenzzinssatz trajectory and SNB policy signals. Models legally permissible rent increases over time. For buildings with historical listing data, shows how rent has evolved across tenancy cycles — revealing whether a landlord prices aggressively at turnover.
Rent vs Buy Calculator
Swiss-specific mortgage math: Tragbarkeit calculation with actual financials, 20% Eigenkapital requirement with Pillar 2/3a sourcing, Eigenmietwert taxation, amortization, and opportunity cost of capital. Not pushing toward buying or renting — making the comparison transparent.
Budget Optimization View
Declare a total monthly housing-plus-living budget. The map recalculates to show quality-of-life-per-franc across the city — factoring unit quality, neighborhood match, commute, tax efficiency, energy, and rent stability. Reveals that stretching rent by 200 CHF for the right unit in the right location might save money net.

Layer 7: Legal Intelligence
Swiss tenancy law (OR Art. 253–274g) is one of the most tenant-protective frameworks in Europe, but almost nobody knows how to use it. Strata embeds legal intelligence into every stage of the tenancy lifecycle.
Before You Sign
Estimates whether the asking rent is legally defensible using two tests: the relative method (comparing to previous tenant’s rent adjusted for Referenzzinssatz changes) and the absolute method (Quartierüblichkeit from comparable units). Flags the 30-day window under OR Art. 270 for contesting initial rent at the Schlichtungsbehörde.
During the Tenancy
Automatic Referenzzinssatz tracking. When the rate drops, every affected tenant gets a notification with a pre-drafted Herabsetzungsbegehren — correctly calculated, properly formatted, legally cited. When a landlord sends a rent increase, Strata analyzes it against the permitted formula and flags unjustified components.
For defects (Mängel): structured Mängelrüge templates with guidance on proportional rent reduction percentages based on Schlichtungsbehörde precedents for common issues (Schimmel, heating failures, construction noise, broken appliances).
At Termination
Kündigungstermin reminders sent well in advance with registered mail deadlines. Nachmieter proposal facilitation through the platform’s pipeline (OR Art. 264). For incoming terminations: retaliatory Kündigung detection (OR Art. 271a), Erstreckung guidance (up to 4 years for residential tenancies), and Schlichtungsbehörde navigation.
Schlichtungsbehörde Navigator
Practical orientation for tenants who need the free mediation authority: what to expect, what to bring, typical outcomes, estimated timelines. Not legal advice — always with Mieterverband referral for complex cases — but demystification of an intimidating process.
Regulatory Feed
Curated feed of legislative changes, Bundesgerichtsentscheide, and policy developments translated into plain language with direct implications for users.

Interface & Experience
Map as Primary Interface
No search bar on the home screen. A full-screen map of Zürich rendered with depth — buildings with height, neighborhoods with color-coded character, streets with activity signals. Intelligence layers are toggled directly onto the map: noise, sunlight, commute isochrones, availability predictions. The transition from neighborhood to building to unit is a continuous spatial zoom, not a mode switch.
Three Modes
•	Explore Mode: No account needed. Browse neighborhoods, toggle layers, compare Quartiere side by side. Designed to be genuinely enjoyable — a way to understand the city, not a chore.
•	Watch Mode: Personal. Watched units glow with availability probability. Broad search zones highlighted. A timeline feed of events relevant to your watchlist. Designed for the long game.
•	Act Mode: Triggered by opportunity. Pre-assembled application in a review panel with Verwaltung-specific recommendations. Submit, then track: received, viewed, shortlisted, decision pending.
Platform Strategy
•	Desktop/tablet: Deep exploration. The spatial map, comparison views, unit profiles, financial modeling. The Saturday afternoon session.
•	Mobile: Reactive moments. Notifications, quick application submission, Watch Mode feed, tenant contributions (snap a Nebenkostenabrechnung, rate the Verwaltung). Three-minute interactions.
Not mobile-first or desktop-first. Mode-first. Each form factor is optimized for the moments it serves.
Visual Identity
Cartographic aesthetic rooted in Swiss design heritage — Tufte meets the Swiss topographic tradition. Restrained typography, generous whitespace, a functional color system where color always means something. Palette grounded in city tones: warm greys, muted terracotta, deep slate, with a single warm accent (amber or coral) used sparingly for significance. Real photography only, never stock. Purposeful motion — sunlight simulations that sweep, availability pulses that breathe. Brand voice: precise, confident, quietly warm. Never salesy.
Onboarding
•	Step zero: No account needed. You’re on the map within seconds, exploring neighborhood intelligence. The product’s shop window.
•	Step one: Soft prompt at first personal action (watch a unit, save a comparison). Minimal signup: email or SwissID.
•	Step two: Gradual profile build. Each piece immediately unlocks something visible: add workplace → commute overlay activates; verify income → match probabilities appear; complete vault → one-tap apply unlocks.
•	Step three: First watch. “Is there a building you already have your eye on?” Pin it, and the system comes alive.
Core anti-pattern: never gate exploration behind data collection.
Notification Philosophy
Rare, high-signal, actionable. Not “12 new listings in your area” but “Unit 4B at Geroldstrasse 8, which you’ve been watching for 5 months, just entered high-probability availability.” Rarity makes each notification feel important. The user learns that Strata only speaks when it has something worth saying.
Emotional Design
Apartment hunting is stressful, demoralizing, and often lonely. The interface respects that weight. When patience pays off, a quiet celebration. When an application is rejected, no cheerful platitudes — actionable insight and better-matched alternatives. Warm without being cute. Confident without being cold.

What Strata Is
Seven layers, one foundation. A unit registry that knows what exists. Neighborhood intelligence that helps you decide where. A profile vault and application engine that helps you compete. Privacy architecture that earns trust. Prediction that watches on your behalf. A marketplace that aligns incentives. Financial modeling that reveals true cost. Legal intelligence that levels the playing field. And an interface that makes all of it feel like a living, breathing map of possibility.

Strata is not a listing platform. It is housing infrastructure — a living model of who lives where, who wants to live where, and how to make the transition between the two as frictionless as possible.

