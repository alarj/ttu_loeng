# Dokumendi päritolu

Koostaja: AI (Cline), projekti tööreeglite kohaselt. Alusmaterjal: projekti tehniline analüüs ja kasutaja juhised.

# TODO

- [x] Rakenduse (`ttu_loeng`) worker arvestab ORDS-i poolt claim'itud tööga, mille aktiivset kohalikku toimingut enam ei ole (näiteks loeng on soft-delete'itud). Worker ei käivita protsessi ning lõpetab keskse töö olekuga `INTERRUPTED`, et täitmiskoht ja järjekord vabaneksid.
- [x] 2026-11-10 — Eduka slaiditöö järel eemaldab worker versioonikataloogist renderdatud `reference/` võrdluspildid. Algne kasutaja üles laaditud slaidifail säilib, mistõttu järgmisel sidumisel saab `reference/` kausta uuesti luua; ebaõnnestunud töö korral vaheartefakte ei eemaldata.
- [x] 2026-11-10 — Loengu detailmodali versioonivalikus on ka algne slaidideta ASR-transkript. Sisselogitud kasutaja ZIP-allalaadimine järgib valitud tulemust: algne transkript sisaldab ainult Markdowni, slaididega versioon Markdowni ja viidatud pilte. Avalik otselink kasutab jätkuvalt ainult vaike-slaidiversiooni.
- [ ] Transkriptsioonimodalis kontrollida ja muuta slaidipiltide laadimine töökindlaks: praegune HTML lisab piltidele `loading="lazy"`, kuid eraldi keritavas modalis võib brauser jätta osa juba transkriptsioonis nähtavale jõudnud slaidipilte esimesel avamisel joonistamata. Artefaktid ja serveri vastused võivad samal ajal olemas olla (loeng 18, versioon 30: `slide_021.png`–`slide_023.png` olid OCI ZIP-is, serveri vahemälus ning vastasid `200 OK`). Hinnata lazy loadingu eemaldamist selles vaates või piltide laadimise usaldusväärset kliendipoolset juhtimist.

