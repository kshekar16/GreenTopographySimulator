# Golf Green Rules & Standards — Research Notes

Background research for the GreenTopographySimulator. It collects the rules, construction standards, playability guidelines and ball-roll physics that a putting-green simulator needs.

> **Confidence key.** **[Rule]** = Rules of Golf (USGA/R&A), binding. **[USGA rec]** = official USGA recommendation, not a rule. **[Guideline]** = industry or architect rule of thumb. **[Derived]** = worked out in these notes from the sources, not quoted from them. Items marked ⚠ had conflicting or secondhand sources. Check them against the primary source before relying on them.

---

## 1. Rules of Golf: the hole and the green

| Item | Value | Status |
|---|---|---|
| Hole diameter | **4.25 in (108 mm)** | [Rule] |
| Hole depth | **≥ 4 in (101.6 mm)** | [Rule] |
| Hole liner (cup) | If used, sunk **≥ 1 in (25 mm)** below the green surface; outer diameter ≤ 4.25 in | [Rule] |
| Flagstick | Must be centred in the hole and circular in cross-section. ⚠ Sources disagree on diameter (≈0.5–1 in). Not needed for a putting sim except as an obstacle. | [Rule] ⚠ |
| Golf ball (for reference) | Diameter ≥ **1.68 in (42.67 mm)**, mass ≤ **1.620 oz (45.93 g)** | [Rule] |
| Putting green | The area on the hole being played that is specially prepared for putting, or that the Committee has defined as the putting green. | [Rule] definition |

- The 4.25 in size dates to the R&A's 1891 rules, which copied a drain pipe used at Musselburgh.
- Since 2019 there has been no penalty when a putted ball hits an unattended flagstick left in the hole. A simulator may need to model ball/flagstick contact if the flag can stay in.
- A ball is **holed** when it comes to rest in the hole and all of it is below the level of the green surface. A ball resting against the flagstick counts as holed if any part of it is below the surface.

## 2. Green size and shape

| Item | Typical value | Status |
|---|---|---|
| Average U.S. green area | **≈ 5,500 ft² (≈ 510 m²)** | USGA study |
| Typical range | Roughly 2,500–10,000+ ft². Shape is free-form, often kidney or oval. | [Guideline] |
| Mowing height (modern) | **0.100–0.156 in (2.5–4 mm)**. Most greens are cut at or below 0.125 in (3.2 mm). | USGA / Penn State |
| Creeping bentgrass | 5/32–3/16 in typical (lower for tournaments) | Penn State Ext. |
| Turf types | Creeping bentgrass, bermudagrass (ultradwarf), Poa annua. Grain is a significant factor on bermudagrass. | — |

Over the last 40 years, mowing heights have dropped from about 0.25 in to as low as 0.10 in. That is one main reason greens are faster today and can carry less slope.

## 3. Construction standard: USGA method (2018 revision)

The USGA *Recommendations for a Method of Putting Green Construction* (first published 1960, revised in 2004 and 2018) is the industry standard. Seen from the bottom up:

1. **Subgrade**: compacted native soil, shaped to follow the finished surface contours (about ±1 in).
2. **Drainage pipe**: laid in trenches in the subgrade, often in a herringbone or gridiron pattern.
3. **Gravel drainage layer**: **4 in** thick.
4. **Root zone**: **12 in ± 1 in** of sand-based mix (mostly sand, often with peat or other organic matter). Particle size and physical properties (porosity, infiltration rate) must fall within the USGA tables. The 2018 revision kept the 2004 physical-property values.

The subgrade follows the surface contours and the root zone depth is uniform. The finished **surface topography is designed first** and the layers are built to match it. A simulator can therefore treat the green as a single height field `z = f(x, y)`.

(Some researchers argue for variable root-zone depth on contoured greens to even out moisture. That only matters for moisture or firmness modelling.)

## 4. Slope and topography guidelines

There is **no rule** on green slope. These values are design guidelines and depend mainly on green speed.

### 4.1 Hole-location (pinnable) areas

| Green speed (Stimpmeter) | Recommended max slope in pin areas | Status |
|---|---|---|
| ~8–9 ft (slow) | ≈ 3.5–4 % | [Guideline] |
| ~10 ft (medium) | ≈ 3–3.5 % | [Guideline] |
| ~14 ft (very fast) | **≈ 2.9 %** (marginal up to ~3.85 %) | Jerry Lemons chart ⚠ |

- Architect Kurt Bowman says a **3 % maximum** in pinning areas is high by modern standards but workable.
- Another method allows a hole location only where **fall-line slope + cross slope < 5.5 %**.
- The faster the green, the less slope it can have before a ball cannot stop near the hole.
- Slopes are usually much steeper *outside* pin areas: on banks, tiers, false fronts and run-offs.

### 4.2 Drainage

Surface drainage needs some slope everywhere. A common figure is **≥ 1–2 %**, with water shed off the green in **several directions** and not across the entire surface.

⚠ This is a widely repeated rule of thumb. I didn't find a citable USGA figure for it.

### 4.3 Hole location guidelines (course set-up)

| Guideline | Value | Status |
|---|---|---|
| Distance from green edge | **≥ 4 paces (≈ 12 ft)** from any edge. Older guidance says 5 paces. More distance is needed near bunkers or where the ground falls away. | [USGA rec] |
| Level area around hole | About **2–3 ft radius** as level as possible, with no change of slope inside it | [USGA rec] |
| Severe slopes | Not within about 3 paces of a very severe slope | [USGA rec] |
| Rotation | Spread over the green's front, middle and back and its left, centre and right parts. Balance difficulty across the round. | [USGA rec] |

These map directly to a "valid pin location" check in the simulator: local slope, slope variance in a 3 ft radius, and distance to the boundary polygon.

## 5. Green speed: the Stimpmeter

### 5.1 Device specification (USGA)

| Item | Value |
|---|---|
| Length | 36 in, aluminium |
| Groove | V-groove with a 145° included angle. The ball rests on two points. |
| Width | 1.75 in |
| Release notch | 30 in from the tapered end (alternate "2X" notch at 14 in, for half-length runs) |
| Release angle | ⚠ ≈ 20–22° (USGA 2013 description says ~22°). The ball releases under gravity as the bar is slowly raised. |
| Ball speed at the bottom | **≈ 6 ft/s (≈ 1.83 m/s)** |

### 5.2 Measurement procedure

1. Pick the flattest area available, about 10 ft × 10 ft or larger.
2. Roll 3 balls in one direction and note where they stop. If the stopping points are more than 8 in apart, re-roll.
3. Roll 3 balls back in the opposite direction from the first set's average stopping point.
4. Average each set, then average the two directions. The result is the speed in feet.

### 5.3 Slope correction: Brede formula

On a slope, a plain average of the two directions is biased. A. Douglas Brede (USGA Green Section Record, 1990) gives:

```
Speed = 2·S↑·S↓ / (S↑ + S↓)        (harmonic mean of the uphill and downhill distances)
```

Brede reports it holds on uniform slopes up to about 6 %. It assumes rolls along the fall line on a planar (not concave or convex) surface.

[Derived] This formula follows exactly from a constant-deceleration model (see §6). Uphill distance is `S↑ = v₀²/2(a+g')` and downhill distance is `S↓ = v₀²/2(a−g')`, so `2S↑S↓/(S↑+S↓) = v₀²/2a`. That is the flat-ground distance. This is a useful check for the simulator's physics.

### 5.4 Typical speeds

| Context | Stimp (ft) |
|---|---|
| Slow | ~8 |
| Medium (regular play) | ~10 |
| Fast (regular play) | ~12 |
| Major championship (e.g. U.S. Open) | 12–14+ |

## 6. Ball-roll physics (for the simulation core)

**Phases of a putt.** After impact the ball first **skids** (slides while rolling) for about the first 10–20 % of its path. It then **rolls without slipping**. A first version of the simulator can ignore the skid phase.

**Rolling-friction model.** On a flat green the ball decelerates at a roughly constant rate `a`. The Stimpmeter fixes `a` [Derived]:

```
a = v₀² / (2·S)        v₀ ≈ 1.83 m/s, S = stimp reading in metres
```

| Stimp | S (m) | a (m/s²) |
|---|---|---|
| 8 ft | 2.44 | ≈ 0.69 |
| 10 ft | 3.05 | ≈ 0.55 |
| 12 ft | 3.66 | ≈ 0.46 |
| 14 ft | 4.27 | ≈ 0.39 |

**Gravity on slopes.** For a solid sphere rolling without slipping (`I = 2/5·m·r²`, close enough for a golf ball), the downhill acceleration from a surface tilted at angle θ is `(5/7)·g·sin θ`. A full 2D model of the ball moving over the height field `z = f(x, y)` is therefore:

```
dv/dt = −(5/7)·g·∇z_projected  −  a_roll · v̂
```

`a_roll` acts opposite to the direction of travel. The ball stops when `|v|` reaches 0 *and* the slope pull `(5/7)·g·|∇z|` is less than the static rolling resistance. Otherwise it keeps creeping downhill.

**Refinements in the literature:**
- ⚠ **Penner** models the rolling-friction coefficient as speed-dependent: `ρ = (0.7028/s)·(1 + 0.0065·v²)`, where s is the stimp reading. This is quoted secondhand from a patent and the units have not been verified. Check against A. R. Penner, *"The physics of putting"*, Can. J. Phys. (2002).
- **Hubbard & Alaways (1999)** found that deceleration varies with velocity and is not quite constant.
- Grain (especially on bermudagrass), moisture, mowing height and time of day all change the effective `a_roll`, and can make it direction-dependent.

**Capture at the hole (to model).** Whether a ball drops depends on its speed at the lip and its offset from the hole centre. Penner gives capture-speed limits: roughly 1.3 m/s for a dead-centre hit, falling to zero at the edge. ⚠ I didn't verify these figures in this pass. Look them up before building the capture logic.

## 7. Implications for the simulator: suggested parameters

| Parameter | Default | Valid range |
|---|---|---|
| Green area | 5,500 ft² (510 m²) | 2,500–10,000 ft² |
| Grid resolution for height field | ~5–10 cm | — |
| Stimp speed | 10 ft | 7–14 ft |
| Max slope in pin areas | 3 % | flag > 3.5 % at stimp ≥ 10, > 2.9 % at stimp ≥ 13 |
| Min surface slope (drainage) | 1 % | 1–2 % |
| Max slope anywhere on putting surface | — | ⚠ tiers/banks can exceed 5–6 %. Flag where the ball cannot stop (`(5/7)·g·sin θ > a_roll`). |
| Pin: min edge distance | 12 ft (4 paces) | — |
| Pin: level radius | 3 ft | — |
| Hole diameter / depth | 108 mm / ≥ 101.6 mm | fixed by Rules |
| Ball diameter / mass | 42.67 mm / 45.93 g | fixed by Rules |
| Stimp launch speed | 1.83 m/s | — |

**Useful [Derived] check.** At stimp `S`, a ball can come to rest on a slope only where `(5/7)·g·sin θ < a_roll`. At 10 ft, `a_roll ≈ 0.55 m/s²`, giving `sin θ < 0.078` (about **7.8 %**). At 14 ft the limit is about **5.6 %**. Above this the ball cannot settle and rolls off. The pin-area guidelines (about 3 %) sit well inside this limit, so a ball that stops near the hole is not left on the verge of rolling away.

⚠ Note: a constant-rolling-resistance model treats static and dynamic resistance as the same. Real turf likely has higher static resistance, so these limits are conservative. Tune them against real data.

---

## Sources

**Rules and equipment**
- [Golf Monthly: What size is the golf hole and why](https://www.golfmonthly.com/features/what-size-is-the-golf-hole-and-why)
- [National Club Golfer: Is there a limit to how deep a hole can be?](https://www.nationalclubgolfer.com/rules/how-deep-can-a-golf-hole-go/)
- [National Club Golfer: Ball holed rules explained](https://www.nationalclubgolfer.com/rules/golf-ball-holed-rules-explained/)
- [USGA For the Golfer (2020-05-01, MSU archive)](https://archive.lib.msu.edu/tic/usgamisc/ftg/2020-05-01.pdf)
- [rec.sport.golf thread quoting the Rules appendix](https://groups.google.com/g/rec.sport.golf/c/wTaLCmBOhFM)
- [The Golf News Net: Golf ball 1.68 in / hole 4.25 in](https://thegolfnewsnet.com/golfnewsnetteam/2022/11/01/what-size-golf-ball-1-68-inches-golf-hole-4-25-inches-74425/)

**Construction**
- [USGA Recommendations for a Method of Putting Green Construction, 2018 (MSU archive)](https://archive.lib.msu.edu/tic/usgamisc/monos/2018recommendationsmethodputtinggreen.pdf)
- [USGA: Decades of research fuel new specs for putting greens](https://www.usga.org/content/usga/home-page/articles/2018/02/decades-of-research-fuel-new-specs-for-putting-greens.html)
- [GCM: 2018 revisions to the USGA method](https://gcmonline.com/research/news/usga-putting-green-construction)
- [USGA: Not all sand-based greens are USGA greens](https://www.usga.org/content/usga/home-page/course-care/green-section-record/62/issue-03/not-all-sand-based-greens-are-usga-greens.html)
- [USGA: Aging USGA putting greens](https://usga.org/course-care/turfgrass-and-environmental-research/research-updates/aging-usga-putting-greens.html)
- [MSU: USGA white paper draft (variable depth)](https://www.canr.msu.edu/psm/uploads/files/USGA%20White%20Paper%20draft.pdf)
- [UNL: Revisiting a groundbreaking putting green study](https://agronomy.unl.edu/news/revisiting-groundbreaking-putting-green-study/)

**Size and mowing**
- [USGA: When it comes to putting greens, there's no such thing as keeping up…](https://www.usga.org/course-care/forethegolfer/2018/when-it-comes-to-putting-greens-there-is-no-such-thing-as-keepin.html)
- [USGA: Understanding mowing heights](https://www.usga.org/course-care/forethegolfer/2018/understanding-mowing-heights.html)
- [Penn State Extension: Factors affecting green speed](https://extension.psu.edu/factors-affecting-green-speed)
- [Golf.com: Backyard putting green guidelines](https://golf.com/lifestyle/backyard-putting-green-guidelines-questions)

**Slope and hole locations**
- [Golf Course Industry: Green slopes](https://www.golfcourseindustry.com/article/green-slopes-golf)
- [Golf Course Architecture: Too fast for furious?](https://www.golfcoursearchitecture.net/content/too-fast-for-furious)
- [Golf Course Architecture, Issue 73](https://www.golfcoursearchitecture.net/digital/magazine/issue73/40/)
- [Golf Monthly: What makes the perfect green?](https://www.golfmonthly.com/features/the-game/what-makes-the-perfect-green-73855)
- [GolfClubAtlas forum thread](https://golfclubatlas.com/forum/index.php/topic,71924.0/prev_next,prev.html)
- [USGA: Hole location, location, location](https://usga.org/course-care/forethegolfer/2018/hole-location--location--location.html)
- [USGA Handicap Manual, Section 15: Course set-up](https://www.usga.org/etc/designs/usga/content/rule-book/handicap-manual/rule-14399.html)
- [Golf.com: How to avoid disaster hole locations](https://golf.com/lifestyle/how-avoid-disaster-hole-location/?amp=1)
- [Golf Digest: 2026 PGA Championship hole locations explainer](https://www.golfdigest.com/story/2026-pga-championship-hole-locations-fair-unfair-explainer)
- [Greenkeeper International, Feb 2009 (MSU archive)](https://archive.lib.msu.edu/tic/bigga/gki/article/2009feb56.pdf)
- [USGA Green Section Record, 1973 (MSU archive)](https://gsr.lib.msu.edu/1970s/1973/730509.pdf)
- [USGA bulletin, Jul 1988 (MSU archive)](https://archive.lib.msu.edu/tic/bulls/article/1988jul14b.pdf)

**Stimpmeter and green speed**
- [Wikipedia: Stimpmeter](https://en.wikipedia.org/wiki/Stimpmeter)
- [USGA: USGA introduces updated Stimpmeter (2013)](https://www.usga.org/content/usga/home-page/articles/2013/01/usga-introduces-updated-stimpmeter-21474853935.html)
- [USGA: Impact of technique and tools on green speed measurements](https://usga.org/content/usga/home-page/course-care/green-section-record/62/issue-08/the-impact-of-technique-and-tools-on-green-speed-measurements.html)
- [Golf.com: What is stimp?](https://golf.com/instruction/what-is-stimp-stimpmeter-how-work/)
- [Golf Monthly: What is a Stimpmeter?](https://www.golfmonthly.com/features/the-game/what-is-a-stimpmeter-and-how-does-it-work-137700)
- [CaddieHQ: How to stimp a golf green](https://www.caddiehq.com/resources/how-to-stimp-a-golf-green)
- [Asian Turfgrass Center: The Brede equation](https://www.asianturfgrass.com/post/the-brede-equation/)
- [OTC Golf blog: Measuring green speed (Brede reprint)](https://otcgolf.blogspot.com/2010/10/measuring-green-speed-stimpmeter.html)
- [US Patent 7225663: Apparatus for measuring green-speed](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7225663)

**Ball-roll physics**
- [US Patent 7713148: Topography linked golf aid (Penner formula, rolling model)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7713148)
- [Penn State: WSCG abstract (velocity-dependent deceleration)](https://www.me.psu.edu/sommer/workarea/WSCG_abstract.pdf)
- [Sports Engineering (Springer) s12283-015-0186-2](https://link.springer.com/content/pdf/10.1007/s12283-015-0186-2.pdf)
