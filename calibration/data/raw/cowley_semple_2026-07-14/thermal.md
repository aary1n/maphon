# Re: Thermal Paraterphenyl //  Today follow-up: a few questions I didn't get to ask

**From:** "Angus Cowley-Semple (PGR)" <a.cowley-semple.1@research.gla.ac.uk>
**To:** "Oxborrow, Mark" <m.oxborrow@imperial.ac.uk>, "Ussalim, Vanessa C" <vanessa.ussalim24@imperial.ac.uk>, "Sharif, Aaryan" <aaryan.sharif24@imperial.ac.uk>
**CC:** Sam Bayliss <Sam.Bayliss@glasgow.ac.uk>, Sarah Mann <Sarah.Mann@glasgow.ac.uk>, "Huang, Ziqiu C" <ziqiu.huang19@imperial.ac.uk>, Max Attwood <attwoodm@mit.edu>
**Date:** Tue, 14 Jul 2026 13:55:10 +0000

---

P {margin-top:0;margin-bottom:0;} 













CAUTION: This message came from outside Imperial. Do not click links or open attachments unless you recognise the sender and were expecting this email.


















Hi Mark, Vanessa, and Aaryan,















Hope you're doing well and sorry for the delay only got back on Monday.















Previously I attached a figure showing the ODMR resonance shifting with laser power. I accidently attached the 0.1% d14-pentacene: d14 PTP rather than h14-pentacene: h14 PTP. Please find both the graph showing the ODMR shifts vs laser power for h14 and d14:















d14 Pc:PTP:







![Embedded image](images/d14%20pcptp.png)






h14 Pc:PTP:







![Embedded image](images/h14%20pcptp.png)






I've plotted the resonance frequency vs laser power for both samples:







![Embedded image](images/resonance%20frequency%20vs%20laser%20power%20for%20both%20samples.png)






It seems to me that the d14 sample is more sensitive to the laser power than the h14 sample. I wonder if you can include whether it's deuterated to your simulation. 















I'll try to answer some of the question from the previous email:






- 


**The size and shape of the crystal**:






- 


I've attached photos of both d14 and h14:




- 


d14:






- 


![Embedded image](images/d14%20picture%201.png)




- 


![Embedded image](images/d14%20in%20some%20bracket.png)




- 


![Embedded image](images/d14%20measured%20at%201.12mm.png)







- 


h14:






- 


![Embedded image](images/h14%20picture%201.png)




- 


![Embedded image](images/h14%20in%20some%20bracket.png)




- 


![Embedded image](images/h14%20measured%20at%201.79mm.png)







- 


**Size**: d14 seems to be around 1 mm and h14 seems to be around 2 mm. It's quite difficult to measure; I tried with the calipers. 




- 


**Shape**: you can check the photos but they look somewhere between a square and a circle.







- 


**Substrates and how the crystals are attached to the PCB**:






- 


Both crystals are

[

glued](https://www.discountmagic.co.uk/shop/new/elmers-rubber-cement-4oz/)[

](https://www.discountmagic.co.uk/shop/new/elmers-rubber-cement-4oz/)to a glass substrate.




- 


The substrate is glued on a PCB with a

[

LeadFree HASL](https://www.protoexpress.com/kb/lead-free-hasl/) surface finish with copper underneath and a [

FR-4 dielectric layer](https://en.wikipedia.org/wiki/FR-4). 







- 


**Air/Liquid**:






- 


The experiment is run at ambient condition. Temperature: 20 degrees Celsius.




- 


The experiment is in an enclosure so there shouldn't any drafts hitting the sample.







- 


**Laser power**:






- 


It's noted on the graph.




- 


We used [

15 mW 520nm pigtail laser](https://www.thorlabs.com/item/LP520-SF15A) to excite the sample.







- 


**Experimental parameters**:






- 


I've did a quick drawing of the excitation path including the part names of the lens and multimode fibre:






- 


![Embedded image](images/angus%20drawing%20of%20excitation%20path.png)




- 


You could assume the spot size is 400 um?
























If you need anything else feel free to email me.















Regards,






Angus




















**From:** Oxborrow, Mark <m.oxborrow@imperial.ac.uk>


**Sent:** 10 July 2026 08:37


**To:** Angus Cowley-Semple (PGR) <a.cowley-semple.1@research.gla.ac.uk>


**Cc:** Ussalim, Vanessa C <vanessa.ussalim24@imperial.ac.uk>; Sharif, Aaryan <aaryan.sharif24@imperial.ac.uk>


**Subject:** Re: Thermal Paraterphenyl // Today follow-up: a few questions I didn't get to ask




 









Hi Angus,















I stupidly left thermal modeller Aaryan's email address off my original email.






Just correcting this here.















Cheers















Mark 















[Sorry Aaryan!]


















**written without AI**














**From:** Oxborrow, Mark <m.oxborrow@imperial.ac.uk>


**Sent:** 08 July 2026 23:09


**To:** Angus Cowley-Semple (PGR) <a.cowley-semple.1@research.gla.ac.uk>


**Cc:** Max Attwood <attwoodm@mit.edu>; Sarah Mann <sarah.mann@glasgow.ac.uk>; Sam Bayliss <sam.bayliss@glasgow.ac.uk>; Ussalim, Vanessa C <vanessa.ussalim24@imperial.ac.uk>; Huang, Ziqiu C <ziqiu.huang19@imperial.ac.uk>


**Subject:** Thermal Paraterphenyl // Today follow-up: a few questions I didn't get to ask




 









Dear Angus (Cc: Sarah, Max and Sam),















I have a summer UROP student here, Aaryan Sharif, who is trying to model, both analytically and computationally (= COMSOL) how flakes, chunks or cylinders of pentacene-doped para-terphenyl (ptc:ptp) heat up upon exposure to (laser) light. We see thermal effects

 during masing,  I showed him your ODMR peak-shifting plot from last week as another example (potentially), and he has read the various published papers (including a recent one from Ashok Ajoy's group) indicating the minus 0.1 MHz per celsius temperature dependance

 on the X-Z transition. 















He would be happy to model your system(s). Including conductive, radiative and convective thermal transport.  















To calculate the temperature profile (through/across the sample), Aaryan needs to know the experiment's geometry (roughly): the size and shape of the ptc:ptp sample and how it is thermally connected to its surrounding. Namely: the nature (composition + geometry)

 of  the substrate (glass, sapphire ...?) , how the sample is stuck (presumably) to it (with what?), and what in the way of air/liquid is wafting around it.  And of course the power and transverse profile / focus of the pump beam.  If the set-up has an axis

 of rotational symmetry, that would be a bonus. 















If you could share with Aaryan any existing pictures or written descriptions (from an existing PhD/master's thesis?) that inform on these thermal aspects of your ODMR measurements, that would be jolly helpful for accurate/realistic modelling. Maybe there is

 a published paper that already provides this info (in its supplementary material), but we have just not found it.  















The spatial distribution of the absorbed optical pump power (which is what matters thermally) needs to be modelled prior to the thermal simulation.   I have another UROP student, Vanessa Ussalim (Cc-ed), who is working on that using a ray-tracing code (pvtrace). 















Thank you for fielding this weird one.















Regards















Mark  



























**written without AI**


























**From:** Sharif, Aaryan <aaryan.sharif24@imperial.ac.uk>


**Sent:** Wednesday, July 08, 2026 13:53


**To:** Oxborrow, Mark <m.oxborrow@imperial.ac.uk>


**Subject:** Today follow-up: a few questions I didn't get to ask















Hi Mark,















Here are a few things from today I'd like to follow up with, because we were tight on time and I started blanking:















- 


I would still like to pin the pump geometry down. The thermal model I've built right now assumes end-fire, I'd need to extend the model before using it for any prediction if we go for side-fire (it will need

 azimuthal formulation). 




- 


Operating temperature envelope. I am calculating df_cavity/dT over a range of 17K (293-310K) but this range was one I just assumed. Should I stick with it for the STO itself, or widen/shrink it?




- 


I used placeholders for emissivity (0.80-0.95) and convection (5-20 W/m^2 K) (from Incropera and DeWitt, Fundamentals of Heat and Mass Transfer). Happy to run with these unless there are better numbers you could

 point me towards?


















Thank you for looping me in with Angus btw 😅
