# Slaiditöötlus: tuvastamine, vastavuse kontroll ja transkriptiga sidumine

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja kinnitatud MVP2 ülesandepüstituse, olemasoleva videokaadrite eraldamise koodi ning ICM0032 loengute 3 ja 8.1 tegelike kontrollandmete põhjal. Dokument kirjeldab slaiditöötluse nõutud käitumist, olemasolevat teostust ja veel kontrollimist vajavaid olukordi.

## 2. Sisukord

- [3. Dokumendi roll](#3-dokumendi-roll)
- [4. Põhimõisted](#4-põhimõisted)
- [5. Kontrollitud lähteolukord](#5-kontrollitud-lähteolukord)
- [6. Slaidiallikate eelistus](#6-slaidiallikate-eelistus)
- [7. Kasutatavad tööriistad](#7-kasutatavad-tööriistad)
- [8. Slaidide olemasolu kontroll](#8-slaidide-olemasolu-kontroll)
- [9. Videost slaidivahetuste leidmine](#9-videost-slaidivahetuste-leidmine)
- [10. Slaidi pealkiri ja tekstituvastus](#10-slaidi-pealkiri-ja-tekstituvastus)
- [11. Animatsioonide ja korduvate slaidide käsitlus](#11-animatsioonide-ja-korduvate-slaidide-käsitlus)
- [12. PPT-, PPTX- ja PDF-failide töötlemine](#12-ppt-pptx--ja-pdf-failide-töötlemine)
- [13. Eraldi slaidifaili vastavuse kontroll](#13-eraldi-slaidifaili-vastavuse-kontroll)
- [14. Transkriptiga sidumine](#14-transkriptiga-sidumine)
- [15. Väljundid ja olekud](#15-väljundid-ja-olekud)
- [16. Kontrollimine](#16-kontrollimine)
- [17. Teostusseis ja järgmised tööd](#17-teostusseis-ja-järgmised-tööd)

## 3. Dokumendi roll

Dokument täpsustab failide [`lahteylesanne.md`](lahteylesanne.md) ja [`tehniline_spek.md`](tehniline_spek.md) slaididega seotud osa. Slaiditöötluse eesmärk on lisada ajatemplitega algtranskripti slaidide ligikaudsed ilmumisajad ja pildid ilma transkriptsioonisegmente muutmata.

## 4. Põhimõisted

- **Slaidikandidaat** — videokaader, mis võib tähistada uue slaidi ilmumist, kuid võib olla ka animatsioon, üleminek või muu ekraanimuutus.
- **Slaidi identiteet** — otsus, millised kaadrid kujutavad sama slaidi.
- **Slaidi ilmumine** — hetk, mil kindel slaid loenguvideos nähtavaks muutub. Sama slaid võib ilmuda loengus mitu korda.
- **Staatiline slaid** — PDF-leheküljena või pildina esitatud slaid ilma animatsiooni vaheetappideta.
- **Pildi digitaalne sõrmejälg** — pildi lihtsustatud arvuline kirjeldus, millega saab võrrelda visuaalselt sarnaseid pilte ka siis, kui nende resolutsioon või tihendus erineb.
- **OCR** — pildil oleva teksti automaatne tuvastamine. Projekt kasutab selleks Tesseracti eesti ja inglise keele andmeid.

## 5. Kontrollitud lähteolukord

ICM0032 kontroll-loengu Echo360 metaandmed näitavad:

- meedia tüüp on `VideoPresentation`;
- saadaval on 640 × 360 ja 1920 × 1080 video;
- Echo ei paku eraldi slide deck'i;
- esitlusvideos on slaidid.

Olemasolev `extract-frames` käsk:

- laadib ajutiselt alla väiksema videoallika;
- võtab FFmpegiga kaadreid etteantud ühtlase ajavahemiku järel;
- käivitab igal kaadril Tesseracti eesti ja inglise keele OCR-i;
- salvestab kaadri ajamärgi, kontrollsumma, failitee ja tuvastatud teksti;
- eemaldab ajutise video.

Kogu kontroll-loengu katses võeti 271 kaadrit 30-sekundiliste vahedega. Töö kestis 2 minutit ja 17 sekundit. See katse kinnitas video hankimise, kaadrite ajatamise ja OCR-i töö, kuid ei tuvasta veel slaidivahetusi piisava täpsusega: alla 30 sekundi näidatud slaid võib jääda vahele ja vahetusaeg võib olla ebatäpne.

Loengu 8.1 esimene tervikkontroll kasutas olemasolevat `video-slides-v1` algoritmi, mis võttis 14 minuti ja 36 sekundi pikkusest videost kahe-sekundilise vahega 438 ajutist kaadrit. Töö kestis 66,792 sekundit, leidis 15 kandidaati ning moodustas kuus slaidi ja kuus ilmumist. Kasutaja antud failis oli viis slaidi. Neli slaidi sobitati automaatselt, tiitelslaid jäi ekslikult `video_only` olekusse ning neljanda slaidi videos nähtud ülemineku- ja animatsioonivaheolek loeti ekslikult eraldi slaidiks. PPTX-i neljanda slaidi XML sisaldab aeglast ülespoole lükkavat üleminekut ja mitut klikiga käivitatavat sisu ilmumise animatsiooni. PDF-is animatsiooni ei ole: PDF-i neljas lehekülg on lõplik staatiline slaid. Töö lõppes tehniliselt edukalt ja ajutised failid eemaldati, kuid slaiditulemus ei ole vastuvõtmiseks korrektne.

## 6. Slaidiallikate eelistus

Slaidide ajastus ja tegelik kasutusjärjekord pärinevad alati loenguvideost.

Pildi ja teksti allika eelistus on järgmine:

1. kasutaja antud PPT-, PPTX- või PDF-failist saadud staatiline slaid, kui selle vastavus videole on kinnitatud;
2. Echo360 eraldi slaidimaterjal, kui selle vastavus videole on kinnitatud;
3. videost eraldatud slaadipilt.

Eraldi faili ei eelistata üksnes parema pildikvaliteedi või faili olemasolu tõttu. Kui vastavus jääb ebaselgeks, kasutatakse videost saadud pilti või märgitakse slaid inimese kontrolli vajavaks.

Kui videos slaide ei ole, ei saa eraldi slaidifailile usaldusväärset ajastust automaatselt määrata. Sellist faili transkripti automaatselt ei lisata.

## 7. Kasutatavad tööriistad

### 7.1. Juba kasutusel

- **FFmpeg** — video ajutise koopia töötlemine, kaadrite eraldamine ja pildimuutuste kandidaatide leidmine.
- **Tesseract OCR** koos `est` ja `eng` keeleandmetega — slaidi pealkirja ja muu teksti tuvastamine.
- **PyMuPDF** — PDF-i lehekülgede, teksti ja metaandmete lugemine ning lehekülgede PNG-piltideks renderdamine.
- **Python** — ajamärkide, tekstide, järjestuse ja transkriptsioonisegmentide ühendamine.

### 7.2. Lisatud MVP2 teostusse

- **LibreOffice'i käsureaversioon** — PPT- ja PPTX-failide teisendamine PDF-iks ilma graafilise kasutajaliideseta.
- **Pillow** — slaidipiltide mõõtmete ühtlustamine ning digitaalse sõrmejälje ja visuaalse erinevuse arvutamine.

Üldotstarbelist ega teksti genereerivat keelemudelit slaiditöötluses ei kasutata. Mudelipõhine töö piirdub TalTechNLP kõnetuvastuse ja Tesseracti OCR-iga.

## 8. Slaidide olemasolu kontroll

Teostatud kontroll toimub enne slaidide täpset ajastamist:

1. loetakse Echo360 slaidilipud ja eraldi slide deck'i kirjed;
2. kontrollitakse esitlusvideo olemasolu ja meediatüüpi;
3. võetakse kogu videost vaikimisi iga 20 sekundi järel põhikaader;
4. iga põhikaader vähendatakse 160 × 90 RGB-punktini ning sellest moodustatakse pildi digitaalne sõrmejälg;
5. võrreldakse põhikaadrite stabiilsust, paigutust ja muutusi;
6. OCR-i ei käivitata kõigil põhikaadritel; ebaselge slaidide olemasolu korral kontrollitakse valitud stabiilsete kandidaatide pealkirjaala.

Tulemus peab olema üks järgmistest:

- `echo_slides` — Echo pakub eraldi slaidimaterjali;
- `video_slides` — videos tuvastati slaidid;
- `no_slides` — kontrollitud video ei sisalda slaide;
- `uncertain` — automaatne kontroll ei anna üheselt usaldusväärset tulemust;
- `no_video` — slaidide kontrollimiseks puudub video.

Echo lipud, video meediatüüp ja automaatse pildikontrolli tulemus säilitatakse eraldi. Üks väärtus ei kirjuta teist üle.

## 9. Videost slaidivahetuste leidmine

### 9.1. Teostatud algoritm `video-slides-v5`

1. Video jagatakse vaikimisi 20-sekundilisteks põhivahemikeks.
2. Iga põhivahemiku alguse ja lõpu põhikaadrit võrreldakse pildi digitaalse sõrmejälje abil.
3. Kui järjestikused põhikaadrid kujutavad sama slaidi, ei töödelda nendevahelist vahemikku täpsemalt.
4. Kui põhikaadrid erinevad, võetakse ainult selle 20-sekundilise vahemiku seest kaadrid vaikimisi kahe-sekundilise sammuga.
5. Täpsustuskaadritest leitakse muutuse järel esimene stabiilne uue slaidi olek.
6. Stabiilsele kandidaadile tehakse pealkirjaala OCR ning seda võrreldakse eelmise slaidi ja võimaliku eraldi slaidifailiga.
7. Ühes muutunud põhivahemikus võib olla rohkem kui üks muutus; seetõttu ei kasutata ainult ühte binaarotsingut.
8. Põhikaadrid, täpsustuskaadrid ja ajutine video eemaldatakse töö lõpus.

Põhikaadri vaikimisi samm on 20 sekundit ja muutunud vahemiku täpsustussamm kaks sekundit. Mõlemad väärtused peavad olema konfiguratsioonis muudetavad ning salvestatakse slaidimanifesti.

Analüüsiks vähendatakse pilt 160 × 90 RGB-punktini. Kahe pildi erinevus on samas asukohas olevate punase, rohelise ja sinise kanali väärtuste absoluutsete erinevuste keskmine, mis jagatakse 255-ga: `0` tähendab identseid pilte ning `1` maksimaalset kanalierinevust. Suurem sõrmejälg säilitab sama kujundusega slaidide teksti- ja joonisevahed, mis 32 × 18 kujul kaduma läksid; RGB säilitab lisaks värvierinevuse.

Teadaolev piirang: kui slaid ilmub ja kaob täielikult ühe 20-sekundilise põhivahemiku sees ning järgmine põhikaader kujutab taas sama slaidi, võib vahepealne slaid jääda leidmata. Sama piirang kehtib väga lühikese slaidi kohta. Kasutaja hinnangul on kontrollitavate loengute puhul alla 20 sekundi näidatava slaidi tõenäosus väga väike.

### 9.2. Varasemad kontrollversioonid

Varasem kood võttis kogu videost kaadreid kahe-sekundilise sammuga, kirjutas need ajutiselt kettale ning otsis nende seast pildimuutusi. See versioon ei ole enam praeguses koodis kasutusel; selle kirjeldus ja kontrolltulemused säilivad dokumentatsioonis ning Git-ajaloos võrdlusena.

Versioonis `video-slides-v1` kasutusele võetud ning hiljem kontrollitud tööväärtused on:

- uue stabiilse oleku kandidaat: erinevus eelmisest valitud olekust vähemalt `0,020`;
- stabiilsus järgmise proovikaadriga: erinevus kuni `0,025`;
- muutumatu pildi kordus: erinevus kuni `0,012`;
- sama pealkirjaga animatsiooniseis: erinevus kuni `0,18`.

Versioon `video-slides-v5` salvestab kasutatud põhikaadri- ja täpsustusvahemikud ning pildierinevuse kontrollväärtused oma slaidimanifesti. Väärtused toimisid loengu 8.1 kontrollis, kuid nende sobivust tuleb hinnata ka pikema ja teistsuguse kujundusega loengu põhjal.

### 9.3. Uuesti sidumine ja tundlikkusaste

Kinnitatud kasutajaliidese põhimõte on, et pärast ASR-i valmimist saab slaidid uuesti siduda ilma transkriptsiooni uuesti loomata. Uuesti sidumine kasutab sama video- ja ASR-artefakti ning loob uue slaiditöötluse versiooni.

Kasutajale pakutakse seitset suhtelist tundlikkusastet: `−3`, `−2`, `−1`, `0`, `+1`, `+2` ja `+3`. Aste `0` tähendab vaikimisi lävendit. Positiivne aste vähendab lävendit ja tuvastab seega väiksemaid pildimuutusi; negatiivne aste suurendab lävendit ja nõuab suuremat muutust. Üks aste muudab lävendit `0,003` võrra. Kasutajaliideses ei näidata toorväärtusi ega nimetata astet “vaikeväärtuse muutuseks”.

Vaikimisi lävend peab tulema `.env`-i võtmega `SLIDE_CHANGE_DISTANCE`; kinnitatud väärtus on `0.020`. Tehniline tuletus on: `tegelik lävend = SLIDE_CHANGE_DISTANCE − (tundlikkusaste × 0.003)`. See annab praeguse vaikeväärtuse korral astmetele `−3…+3` väärtused `0.029`, `0.026`, `0.023`, `0.020`, `0.017`, `0.014` ja `0.011`.

Praegune kood kasutab küll `160 × 90` RGB-sõrmejälge ja lävendit `0.020`, kuid lävend on veel lähtekoodi konstant. `.env`-ist lugemine, tundlikkusastme edastamine workerile ja versioonitud väljundite loomine ei ole veel teostatud; need tuleb teha koos kasutajaliidese uuesti sidumisega.

## 10. Slaidi pealkiri ja tekstituvastus

Tesseracti ei kasutata põhikaadrite muutuse tuvastamiseks. OCR käivitatakse alles stabiilsel slaidikandidaadil. Pealkirjakandidaat leitakse slaidi ülemisest osast, arvestades teksti asukohta ja suurust.

Enne võrdlemist pealkiri normaliseeritakse:

- eemaldatakse liigsed tühikud;
- suur- ja väiketähti ei käsitleta erinevusena;
- eemaldatakse juhuslikud kirjavahemärgid ja OCR-i tekitatud üksikud märgid;
- lubatakse väikeseid kirjapildierinevusi.

Pealkiri on slaidi peamine tunnus, kuid mitte ainus tunnus. Mõnel slaidil puudub pealkiri, sama pealkiri võib esineda mitmel slaidil ja OCR võib sama teksti erinevalt lugeda.

Kogu kaadri OCR-i ei tehta ilma eraldi slaidifailita. Eraldi slaidifaili olemasolul loetakse iga stabiilse videokandidaadi kogu nähtav tekst, sest rakenduse menüüd või vähese kontrastiga pealkiri võivad pealkirjaala OCR-i rikkuda, samal ajal kui slaidi põhitekst on loetav. Kogu kaadri OCR-i kasutatakse üksnes PDF-i tekstikihiga vastavuse kontrollimiseks. Kontrollimata OCR-pealkirja transkripti ei lisata.

## 11. Animatsioonide ja korduvate slaidide käsitlus

Järjestikuseid kaadreid käsitletakse sama slaidina, kui:

- pealkiri püsib sama või väga sarnane;
- slaidi põhikujundus ja taust püsivad;
- muutus puudutab ainult osa sisust, näiteks loendi järgmise rea või joonise elemendi ilmumist.

Animeeritud slaidi üksikuid vaheetappe lõppväljundis eraldi slaidideks ei nummerdata. Püsivaks pildiks valitakse sama slaidi kõige terviklikum nähtud olek, kui seda saab videost üheselt määrata.

Kui varem nähtud slaid ilmub hiljem uuesti, säilib selle slaidinumber ja lisatakse uus ilmumisaeg.

## 12. PPT-, PPTX- ja PDF-failide töötlemine

### 12.1. PPT ja PPTX

PPT- või PPTX-fail teisendatakse LibreOffice'i käsureaversiooniga PDF-iks. Teisenduse järel:

- üks PDF-lehekülg vastab ühele staatilisele slaidile;
- animatsiooni vaheetappe eraldi ei säilitata;
- teisenduse õnnestumine, tööriista versioon ja väljundi kontrollsumma salvestatakse;
- algset faili ei muudeta.

Teisendus võib muuta fonte, paigutust või animatsioonide lõppseisu. Seetõttu ei tõenda edukas teisendus veel vastavust videos kasutatud slaidile.

### 12.2. PDF

PyMuPDF:

- loeb PDF-i lehekülgede arvu ja tekstikihi;
- renderdab iga lehekülje PNG-pildiks;
- salvestab lehekülje järjekorranumbri, pildi ja kontrollsumma.

Tekstikihi puudumisel käivitatakse leheküljel Tesseract OCR.

## 13. Eraldi slaidifaili vastavuse kontroll

Video slaid ja staatiline slaid loetakse vastavaks ainult mitme tunnuse kooskõla põhjal:

1. normaliseeritud pealkiri;
2. muu tuvastatud tekst;
3. pildi digitaalne sõrmejälg ja üldine kujundus;
4. slaidide järjekord.

Kui kogu videokaadri OCR-i sõnavara kattub ühe PDF-lehekülje tekstiga selgelt rohkem kui teiste lehekülgedega, võib see anda kinnitatud vaste ka vigase pealkirja-OCR-i korral. Nõrk või mitme lehekülje vahel ebaselge tekstikattuvus ei ole vaste kinnitamiseks piisav. PDF-i esimese lehekülje pealkiri võetakse lehekülje sisust; üldine faili metaandmete pealkiri, näiteks `PowerPoint Presentation`, ei kirjuta tuvastatud slaidipealkirja üle.

Ajastus võetakse videost. Kinnitatud vastavuse korral kasutatakse lõppväljundis eraldi failist saadud kvaliteetset pilti.

Iga vastavus saab oleku:

- `matched` — automaatne võrdlus andis üheselt kooskõlalise tulemuse;
- `review_required` — mitu vastet on võimalikud või tunnused ei ole piisavad;
- `not_matched` — staatilisele slaidile ei leitud videost vastet;
- `video_only` — videost leitud slaidil ei ole eraldi failis vastet.

Automaatse vastavuse piirid määratakse kontrollmaterjali põhjal. Ebaselget vastet ei muudeta kinnitatuks oletuse põhjal.

## 14. Transkriptiga sidumine

Slaidivahetuse tõttu ei lõhuta ega kirjutata ümber olemasolevat TalTechNLP transkriptsioonisegmenti.

Iga slaidi ilmumisaeg paigutatakse ajaliselt lähima segmendipiiri juurde. Slaidiviide sisaldab:

- slaidi numbrit;
- kinnitatud eraldi slaidifaili pealkirja, kui vaste on olemas; vasteta videokaadri kontrollimata OCR-pealkirja ei kuvata;
- videost saadud ligikaudset ilmumisaega;
- suhtelist pilditeed;
- allika liiki: video, Echo slaidimaterjal või kasutaja fail.

Näide:

```markdown
[00:14:18–00:14:37] Transkriptsioonisegmendi tekst.

## Slaid 7 — Risk Chain

![Slaid 7](slides/slide_007.png)

Ligikaudne ilmumisaeg: 00:14:32

[00:14:37–00:14:55] Järgmise segmendi tekst.
```

## 15. Väljundid ja olekud

Slaiditöötlus loob vähemalt:

- slaidide olemasolu kontrolli tulemuse;
- slaidide manifesti;
- slaidipildid;
- video ajamärkide ja slaidi identiteedi seosed;
- eraldi slaidifaili teisendamise tulemuse;
- video ja staatiliste slaidide vastavuse tulemuse;
- transkriptiga ühendatud Markdown-faili.

Slaidikirje sisaldab vähemalt slaidi ID-d, numbrit, pealkirja, pilditeed, kontrollsummat, allikat, ilmumisaegu ja ülevaatuse olekut.

## 16. Kontrollimine

Slaiditöötluse kontrollkomplekt peab sisaldama vähemalt:

- sama slaidi mitut animatsiooniseisu;
- järjestikuseid erinevaid slaide sama pealkirjaga;
- pealkirjata slaidi;
- slaidi, mille OCR sisaldab viga;
- videost puuduva staatilise slaidi;
- videos oleva, kuid eraldi failist puuduva slaidi;
- sama slaidi korduvat näitamist;
- loengut või videolõiku, milles slaide ei ole.

Inimese kontroll võrdleb tuvastatud slaidide järjekorda ja ilmumisaegu otse videoga. Loengu 8.1 kontrolltulemus on dokumenteeritud allpool; enne piiride üldiseks sobivaks lugemist tuleb kontrollkomplekti täiendada teiste loengutega.

## 17. Teostusseis ja järgmised tööd

### Olemas

- Echo360 meediaallikate leidmine;
- eraldi slide deck'i olemasolu olek;
- ajutise video allalaadimine ja eemaldamine;
- FFmpegiga ühtlase ajavahemiku järel kaadrite eraldamine;
- Tesseracti eesti ja inglise OCR;
- kaadri ajamärgi, kontrollsumma ja OCR-teksti manifest;
- PDF-i tekstikihi lugemine PyMuPDF-iga.
- pildimuutuse ja stabiilsuse põhine slaidikandidaatide leidmine;
- pealkirja OCR slaidi ülemisest 30 protsendist;
- sama pealkirja ja sarnase pildiga animatsiooniseisude koondamine;
- varem nähtud slaidi korduva ilmumise sidumine sama slaidinumbriga;
- LibreOffice'i abil PPT/PPTX teisendamine PDF-iks;
- PDF-lehekülgede PNG-piltideks renderdamine;
- video ja eraldi slaidifaili teksti-, pildi- ja järjekorrapõhine vastavuse kontroll;
- slaidiviidete lisamine lähimale transkriptsioonisegmendi piirile;
- slaidimanifest ning ühendatud Markdown-väljund;
- ajutise video ja teisendusfailide eemaldamine nii edu kui vea korral.
- vaikimisi 20-sekundilised põhikaadrid;
- ainult muutunud põhivahemike kahe-sekundiline täpsustus;
- põhikaadrite võrdlus ilma OCR-ita;
- tugeva ja üheselt eristuva pildisarnasuse kasutamine OCR-i varuvariandina;
- PDF-i metaandmetest teadaolevate akronüümide taastamine OCR-pealkirjades;
- video kandidaadi sobitamine staatilise slaidiga enne slaidinumbri loomist.
- eraldi slaidifaili olemasolul kogu stabiilse videokaadri OCR-i võrdlemine PDF-i tekstikihiga;
- kontrollimata video-OCR-i pealkirjade väljajätmine transkriptist;
- PDF-i esimese lehekülje sisulise pealkirja säilitamine üldise dokumendimetaandme asemel.

Loengu 8.1 lõplik `video-slides-v2` kontroll:

- video kestus 14 minutit ja 36 sekundit;
- 44 põhikaadrit;
- kaheksa muutunud põhivahemikku;
- 89 erineva ajamärgiga analüüsitud kaadrit;
- 11 slaidikandidaati;
- viis slaidi ja viis ilmumist;
- kõik viis slaidi olekus `matched` ning pildi allikaga `user_file`;
- ligikaudsed ilmumisajad `00:00:00`, `00:00:32`, `00:04:20`, `00:06:18` ja `00:11:20`;
- töö kestus 72,560 sekundit;
- ajutine video ja kaadrid eemaldatud.

### Kontrollida ja täiendada

1. kontrollida `video-slides-v2` pikema loengu põhjal;
2. kontrollida töövoogu ilma eraldi PPTX- või PDF-failita;
3. kontrollida järjestikuseid eri slaide, millel on sama pealkiri;
4. lisada vajaduse korral eraldi olek videole, milles slaidide asemel on kaamerapilt;
5. täiendada kontrollkomplekti tegelike vigade põhjal.
