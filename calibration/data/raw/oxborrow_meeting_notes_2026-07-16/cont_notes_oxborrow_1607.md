# Contemporaneous meeting notes — Oxborrow supervision meeting, 2026-07-16

**Source:** `cont_notes_oxborrow_1607.docx` (archived alongside, byte-verbatim)
**Author (docx core properties):** Sharif, Aaryan
**Created:** 2026-07-16T12:49:00Z — **Modified:** 2026-07-16T14:01:00Z (docx core properties; contemporaneous with the meeting)
**Transcript:** paragraph-faithful extraction of `word/document.xml` — all paragraphs in document order; the docx's one bullet list (bullet glyph "-") rendered as markdown "-" items; two empty paragraphs carried as paragraph breaks; spellings, typos, and trailing spaces preserved verbatim; no editorial changes. The docx contains no images, tables, hyperlinks, or tracked changes.

---

Pc:ptp crystal placement, alignment, tolerances

Whether cylindrical interface is conducting heat or not. Simplest thing to say is “no”. no heat flow. Heat flow must be tangential to surface, so gradient must be tangential to surface. Hot source and cold source, top and bottom. 

If you just do that, surely a solution to the equations (w/o thermal transport down there) 1 dimensional? 

Inside this ‘blob of stuff’ we know the thermal conductivity at any point in it. ‘each piece’ has a known conductivity. If we know the temperature on the boundary, and the thermal conductivity at any point in side, we can ask comsol to solve it. Or if there’s symmetry, we can do it analytically (expanding Laplacian in cylindrical, sepvar). 

Power  condition on boundaries, this surface here is going to suck at least 1W of power out of it for example. Most natural is to impose fixed T boundary conditions. Side surface, suppose we are blowing air on it really hard. Would that not mean the ‘outer crust’ has the same temperature of the air. That’s a way of imposing boundary conditions. Air must be blowing fast and replacing the old air quickly, otherwise air warms up slowly. 

Stagnant air can be represented by thermal conductivity. Amount of temperature that can be removed from this piece of solid material on the surface, that surface will be able to dissipate or remove a certain amount of heat i.e. a power. Power that can be removed from the hot surface is proportional to the area of that surface, the temperature difference between surface and the air, factor that might depend on how irregular and smooth the surface is. Newton’s law. Not completely correct. Amount of power is non linear. At low temp, when delta T IS SMALL, WE JUST HAVE STAAGNANT AIR, CERTAIN AMOUNT OF POWER DISSIPATED, ONCE THE TEMP DIFFERENCE GOES OVER CERTAIN THRESHOLD YOU START CONVECTING SO Power loss increases a lot more.

Assume linear in stagnant or convective regime? Coefficient depends on what regime one is in. 

Assume everything’s (CRYSTAL AND STO) is centered. What we often have in rigs is ptp with dielectric ring around it, and then add Vaseline in the gap between the crystal and the sto. No air gap between sto and crystal, replaced with Vaseline. Thermally substrates the sample onto something, so it gets less hot. Also prevents reflections. Vaseline is thixotropic. Its soft but it doesn’t ooze. Something that is spreadable, but won’t deform afterwards. 

Thermal paste between copper box and the sto/crystal. 

What would be interesting is to do this. Some ideas from oxborrow:

- What I want you to do is think deep, not about details. 

- Ballpark estimates

- Blown air. S1. Imposed temp on top and sides. Ttop, t everywhere eels. T everywhere else includes the bottom and the sides. Substration on the sides

- S0 would be 1d with non conductive sides, Ttop and Tbottom

- S3

- In s1, hot on the top, blown on the sides version. Oxborrow would be interested in: in the old days, we did S4: heat comes in from sides i.e. side firing, cool would have been top and bottom. 

- S5: steam engine analogy. Why can’t we have holes in the ptp? Holey? Send forced air through it, or perflurohexane. The tube surfaces would then be at room temp too. Bc: outside cylinder is cold, surface of all the heat transfer tubes inside the ptp are cold. How to decide how many holes? What’s the tradeoff between holes. 

- Filling factor

- Invade the active space with cooling pipes..? 

- Trade off between filling factor and cooling.

- If you can keep it substantially cooler by only sacrificing a small volume, its worth it. 

How is the heat in the h14 and d14 being substrated away. Is all of the sample geometry even being heated up. Top few hundred microns of the ptp? First approx. hot surface on the top

Work out how much power. Certain mW of laser power absorbed in the first few hundred microns of crystal. Where does the heat flow? Cold substrate – flows down into substrate, 

Important: how good is that gap? Using rubber cement as the gap between the crystal and the slide. Has a certain thermal conductivity. Thin layer. Structure has some metal bits, also fiberglass board. Copper tracks on the board are quite highly conductive, but the fiberglass is less so. 

Coplanar waveguide. Strip of copper on the fiberglass board, other strips of copper next to it. Sideon view. Vias go through board to make sure that electromagnetically, the bottom of the oard is at the same potential as the sides. Middle part is not via’ed/’to ground’. 

Less wide sample that cant touch the vias will get way hotter than a wider sample that can touch the vias. 

Orientation of the sample on the coplanar waveguide could also make a big difference. 
