# Re: STO cavity tuning mechanism

**From:** "Oxborrow, Mark" <m.oxborrow@imperial.ac.uk>
**To:** "Sharif, Aaryan" <aaryan.sharif24@imperial.ac.uk>
**CC:** "Ussalim, Vanessa C" <vanessa.ussalim24@imperial.ac.uk>
**Date:** Fri, 17 Jul 2026 21:23:58 +0000

---

P {margin-top:0;margin-bottom:0;}

Hi Aaryan,

There is no write or wrong answer: 

At present, my model uses the Kalea Booth-derived TE 01 delta geometry: a cylindrical copper enclosure of radius 12.28mm, height of 18.42mm, with an STO torus of major radius 6.14mm and minor radius 2.456mm. This is different to the geometry you described in
 your email, so for the current build, do you think I should replace both the STO and enclosure with the geometry you specified here? Or, should I retain Kalea Booth's geometry?

There is not right or wrong answer.  Kalea's design looks pretty typical. Though I would
**recommend basing your simulation on a published geometry that you can then cite**. 

One reference "reference" geometry of pentacene-doped paraterpheyl maser is shown in 

[https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.127.053604](https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.127.053604)

at its supplementary material

[https://journals.aps.org/prl/supplemental/10.1103/PhysRevLett.127.053604/Cooling_PRL_SM_Proof.pdf](https://journals.aps.org/prl/supplemental/10.1103/PhysRevLett.127.053604/Cooling_PRL_SM_Proof.pdf)

Here the STO is 12 mm in diameter, 8.6 mm height, 4 mm inner diameter. We still have this STO ring. 

The surrounding cavity around it is  18 mm heigh, 28 mm in ID . The STO is 3 mm above the deck (and thus 18 - 8.6 - 3 = 6.4 mm from the ceiling (= tuning plate). 

We have copper cavities in the lab with internal diameter equal to 60 mm and 30 mm. 

Also, is the 5-10mm plate to STO gap the full, usable tuning range? Or, just the typical operating separation.

The typical separation when the cavity is tuned to 1.45 GHz. One can screw the cavity's ceiling higher. 

Finally, you mentioned that the STO is supported on a poorly conducting 5mm polystyrene column. I'd also noted though, from yesterday, that there may be thermal paste as an interface between the copper box and the STO/crystal. Which contact arrangement applies
 to the current build? Or, are these at separate interfaces?

We have generally just placed the STO ring on a plastic spacer and not bothered with paste. 

One could make the spacer out of a highly thermal conductive low dielectric loss material such as sapphire.

We have never yet bothered to do so. 

Regards

m

**written without AI**

**From:** Sharif, Aaryan <aaryan.sharif24@imperial.ac.uk>

**Sent:** 17 July 2026 14:53

**To:** Oxborrow, Mark <m.oxborrow@imperial.ac.uk>

**Cc:** Ussalim, Vanessa C <vanessa.ussalim24@imperial.ac.uk>

**Subject:** Re: STO cavity tuning mechanism

 

<!--
p
	{margin-top:0;
	margin-bottom:0}
-->

Hello Mark,

Thanks for this. This is really useful. Just wanted to clarify some other details.

At present, my model uses the Kalea Booth-derived TE 01 delta geometry: a cylindrical copper enclosure of radius 12.28mm, height of 18.42mm, with an STO torus of major radius 6.14mm and minor radius 2.456mm. This is different to the geometry you described in
 your email, so for the current build, do you think I should replace both the STO and enclosure with the geometry you specified here? Or, should I retain Kalea Booth's geometry?

Also, is the 5-10mm plate to STO gap the full, usable tuning range? Or, just the typical operating separation.

Finally, you mentioned that the STO is supported on a poorly conducting 5mm polystyrene column. I'd also noted though, from yesterday, that there may be thermal paste as an interface between the copper box and the STO/crystal. Which contact arrangement applies
 to the current build? Or, are these at separate interfaces?

Aaryan

**From:** Oxborrow, Mark <m.oxborrow@imperial.ac.uk>

**Sent:** 16 July 2026 22:36

**To:** Sharif, Aaryan <aaryan.sharif24@imperial.ac.uk>

**Cc:** Ussalim, Vanessa C <vanessa.ussalim24@imperial.ac.uk>

**Subject:** Re: STO cavity tuning mechanism

 

<!--
p
	{margin-top:0;
	margin-bottom:0}
-->

Hi Aaryan,

The gap between the circular tuning plate and the top of the STO crystal is typically between 5 mm and 10 mm. 

There is sometimes a bore hole running down the tuning screw's axis (this threaded screw holds the plate that is suspended from it) to allow optical axis onto the top of the maser crystal.  Diameter of bore hole: typical 5 mm. Outer diameter of screw 10 mm.
 Diameter of circular plate 38 mm.

Inner diameter (ID) of copper cavity 40 mm.  

Not sure about the tuning sensitivity. Something like -10 MHz per mm with height of ceiling (does not vary linear). 

Height of STO above the copper deck: 5 mm --usually on a column made of plastic (polystyrene) --not very thermally conducting. 

STO: 12 mm outer diameter (OD), 4 mm ID, 8 mm high

Height of STO above the copper deck: 5 mm --usually on a column made of plastic (polystyrene) --not very thermally conducting. 

[https://www.nature.com/articles/ncomms7215](https://www.nature.com/articles/ncomms7215)

[https://www.nature.com/articles/nature11339](https://www.nature.com/articles/nature11339) —larger sapphire dielectric ring. 

![Embedded image](stogeometry_assets/image.png)

Regards

m

**written without AI**

**From:** Sharif, Aaryan <aaryan.sharif24@imperial.ac.uk>

**Sent:** 16 July 2026 21:53

**To:** Oxborrow, Mark <m.oxborrow@imperial.ac.uk>

**Cc:** Ussalim, Vanessa C <vanessa.ussalim24@imperial.ac.uk>

**Subject:** STO cavity tuning mechanism

 

<!--
p
	{margin-top:0;
	margin-bottom:0}
-->

Hello Mark,

I had one follow up that I missed during our meeting. It's regarding the STO cavity tuning plate. From the existing papers, I understand that it's a screw driven internal metal ceiling above the STO ring, moving axially to tune the TE 01 delta resonance. 

For the particular cavity geometry I am modelling, do you know approximately what nominal plate-to-STO gap and mechanical travel range I should use? It would also be useful to know whether the plate is simply flat across the cavity, or has any extruded/relieved
 features that may matter electromagnetically.

If there's a dimensioned drawing, bench measurement, or frequency vs. displacement calibration for this build, that'd be super helpful.

Aaryan
