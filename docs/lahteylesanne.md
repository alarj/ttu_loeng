# Lähteülesanne: Echo360 loengu ajatemplitega transkript koos slaididega

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja 1.11.2026 kinnitatud uue ülesandepüstituse, projekti tegelike katsetulemuste ning 3.–4.11.2026 kinnitatud MVP3 veebirakenduse, ligipääsu ja ORDS-i arhitektuuriotsuste põhjal. Dokument asendab varasema konspektirakenduse lähteülesande; varasem versioon säilib Git-ajaloos märgendi `ver0.1` all ja MVP2 seis märgendi `ver0.2` all.

## 2. Sisukord

- [3. Dokumendi eesmärk](#3-dokumendi-eesmärk)
- [4. Probleem ja kontrollitud lähteolukord](#4-probleem-ja-kontrollitud-lähteolukord)
- [5. Rakenduse eesmärk](#5-rakenduse-eesmärk)
- [6. Põhimõisted](#6-põhimõisted)
- [7. Kasutaja põhivoog](#7-kasutaja-põhivoog)
- [8. Sisendid](#8-sisendid)
- [9. Funktsionaalsed nõuded](#9-funktsionaalsed-nõuded)
- [10. Väljundid](#10-väljundid)
- [11. Välise keelemudeliga jätkamine](#11-välise-keelemudeliga-jätkamine)
- [12. Mittefunktsionaalsed nõuded](#12-mittefunktsionaalsed-nõuded)
- [13. MVP2 ulatusest välja jääv](#13-mvp2-ulatusest-välja-jääv)
- [14. Esimene kontrolljuhtum](#14-esimene-kontrolljuhtum)
- [15. Vastuvõtukriteeriumid](#15-vastuvõtukriteeriumid)
- [16. MVP3 laiendus](#16-mvp3-laiendus)

## 3. Dokumendi eesmärk

Käesolev dokument määrab rakenduse eesmärgi, ulatuse, sisendid, väljundid ja vastuvõtukriteeriumid. Jaotised 4–15 kirjeldavad MVP2 töötlusmootori alust. MVP3 muudab selle mitme loengu veebirakenduseks ja lisab serveriülese ORDS-i järjekorra integratsiooni jaotise 16 ning faili [`mvp3_veeb_ja_ords.md`](mvp3_veeb_ja_ords.md) järgi. Tehniline teostus on kirjeldatud failis [`tehniline_spek.md`](tehniline_spek.md). Slaidide tuvastamise, töötlemise ja transkriptiga sidumise detailne lahendus on eraldi failis [`slaiditootlus.md`](slaiditootlus.md).

## 4. Probleem ja kontrollitud lähteolukord

TalTechi eestikeelsed loengud on Echo360-s salvestatud, kuid kontrollitud ICM0032 loengu automaattranskript oli valdavalt ingliskeelne ja eestikeelse kõne kohta sisuliselt kasutuskõlbmatu. Echo väljundit ei kasutata praeguses eestikeelsete loengute töövoos põhiteksti ega diagnostilise võrdlusmaterjalina. Ingliskeelsete loengute Echo transkriptsiooni kvaliteeti ei ole kontrollitud ning järeldus ei laiene neile.

Projektis kontrollitud TalTechNLP mudel `TalTechNLP/whisper-large-v3-turbo-et-verbatim` koostas 2 tunni ja 15 minuti pikkusest loengust täieliku ajatemplitega transkripti 1 tunni ja 40 minutiga. Väljundis oli 15 064 sõna ja 447 segmenti. Kasutaja pistelise kuulamiskontrolli järgi oli tekst hästi loetav, kõne sisu täpselt säilinud ning eesti- ja ingliskeelsed erialaterminid korrektsed. Täielikku inimese kontrollitud sõna-sõnalist kvaliteedimõõtmist ei ole veel tehtud.

Rakendus keskendub olemasoleval serveril kontrollitud töövoole: ajatemplitega transkriptsiooni loomisele ja selle sidumisele loenguvideos nähtud slaididega.

## 5. Rakenduse eesmärk

Luua olemasoleval Ubuntu serveril konteinerites töötav rakendus, mis:

1. võtab sisendiks Echo360 avaliku loengukogumiku lingi;
2. kuvab kogumikus olevad loengud ja nende salvestise oleku;
3. loob kasutaja valitud eestikeelsest loengust TalTechNLP mudeliga täieliku ajatemplitega transkripti;
4. kontrollib, kas loeng sisaldab slaide;
5. tuvastab slaidide järjekorra ja ligikaudsed vahetusajad;
6. kasutab vaikimisi videost saadud slaidipilte;
7. võimaldab kasutajal anda sama loengu slaidid eraldi PPT-, PPTX- või PDF-failina;
8. seob kinnitatud vastavusega slaidid transkripti õigesse ligikaudsesse kohta;
9. salvestab inimesele loetava tulemuse, mida saab soovi korral anda välisele suurele keelemudelile edasiseks toimetamiseks või konspekti koostamiseks.

Rakendus ei kirjuta transkripti keeleliselt ümber ega koosta ise konspekti. Kõnetuvastust võib katsetamiseks suunata loengupõhise erialaterminite loendiga. Transkripti teksti pärast kõnetuvastust mehaaniliselt ei muudeta.

## 6. Põhimõisted

- **Echo360 loengukogumik** — avaliku `/public` lingiga Echo360 kursuse või sektsiooni vaade, mis sisaldab loengute nimekirja.
- **Transkriptsioonisegment** — TalTechNLP kõnetuvastuse loodud tekstilõik koos algus- ja lõpuajaga.
- **Slaidiviide** — transkripti lisatud tähis, mis näitab slaidi numbrit, pealkirja, ligikaudset ilmumisaega ja pildifaili.
- **Eraldi slaidifail** — kasutaja antud PPT-, PPTX- või PDF-fail, mille vastavust loenguvideos kasutatud slaididele tuleb kontrollida.
- **Staatiline slaid** — üks terviklik slaidipilt ilma PowerPointi animatsiooni vaheetappideta.

## 7. Kasutaja põhivoog

1. Kasutaja sisestab Echo360 avaliku loengukogumiku lingi.
2. Rakendus loob Echo360 avaliku külalissessiooni ja kuvab kogumiku loengud.
3. Kasutaja valib töödeldava loengu.
4. Kasutaja võib lisada sama loengu slaidid PPT-, PPTX- või PDF-failina.
5. Rakendus kontrollib, kas valitud loengul on kasutatav salvestis ja audio.
6. Rakendus käivitab TalTechNLP kõnetuvastuse taustatööna ja võib katsekonfiguratsioonis edastada valitud loengu erialaterminid mudelile hotword'idena.
7. Rakendus kontrollib eraldi, kas loeng sisaldab slaide.
8. Slaidide olemasolul tuvastab rakendus nende järjekorra ja ligikaudsed vahetusajad.
9. Eraldi slaidifaili olemasolul kontrollib rakendus selle vastavust videos nähtud slaididele.
10. Rakendus lisab slaidiviited olemasolevate transkriptsioonisegmentide vahele; segmente ei lõhuta ega muudeta.
11. Rakendus salvestab transkripti, slaidipildid, slaidide ajastuse ja töö metaandmed.
12. Ajutine audio ja video eemaldatakse nii eduka kui nurjunud töötluse järel.

## 8. Sisendid

### 8.1. Kohustuslikud sisendid

- Echo360 avalik `/public` loengukogumiku link;
- kasutaja valitud loeng.

### 8.2. Echo360-st saadavad sisendid

- kogumiku ja loengu nimi;
- loengu kuupäev ja kestus;
- loengu ning meedia tehnilised identifikaatorid;
- audioallikas;
- videoallikad;
- Echo360 eraldi slaidimaterjal, kui see on olemas.

### 8.3. Valikuline sisend

Kasutaja võib lisada sama loengu slaidid:

- PPT-vormingus;
- PPTX-vormingus;
- PDF-vormingus.

Eraldi slaidifaili olemasolu ei tõenda selle vastavust loengus kasutatud slaididele. Vastavus tuleb kontrollida video põhjal. Kui vastavust ei saa kinnitada, ei esitata eraldi faili slaide videos kasutatud slaididena.

## 9. Funktsionaalsed nõuded

### 9.1. Loengukogumiku ja salvestise leidmine

Rakendus peab:

- looma standardse HTTP-kliendiga Echo360 avaliku külalissessiooni;
- kuvama kogumiku loengute nimekirja;
- säilitama Echo algsed ajatuse lipud ning tegelikest meediakirjetest tuletatud salvestise oleku eraldi;
- lubama töötlemiseks valida ainult loengu, mille vajalik meedia on kättesaadav;
- mitte salvestama sessiooniküpsiste väärtusi ega signeeritud meedia-URL-ide saladusi.

### 9.2. Kõnetuvastus

Rakendus peab:

- kasutama eestikeelse kõne tuvastamiseks hotword'ideta `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604` mudelit;
- töötlema kogu valitud loengu audio;
- säilitama transkriptsioonisegmentide algus- ja lõpuajad;
- säilitama võimalusel sõnataseme ajad;
- säilitama mudeli loodud teksti ning segmendi ajapiirid muutmata kujul;
- salvestama hotword'ide katsekonfiguratsiooni kasutamisel loendi kontrollsumma ja kirjed;
- salvestama kasutatud mudeli, revisjoni, tööriistad, seadistuse, töö alguse, lõpu ja kestuse;
- töötama taustal nii, et kasutaja saab töö olekut eraldi kontrollida.

### 9.3. Slaidide olemasolu ja allikas

Rakendus peab enne slaiditöötlust eristama vähemalt järgmisi olukordi:

- Echo360 pakub eraldi slaidimaterjali;
- esitlusvideos on slaidid;
- video sisaldab ainult kaamerapilti või muud mitteslaidilist sisu;
- slaide ei tuvastatud;
- slaidide olemasolu jäi ebaselgeks.

Slaidide olemasolu ei otsustata üksnes videofaili või Echo slaidiikooni olemasolu põhjal.

Slaidid võetakse vaikimisi videost. Eraldi slaidifaili kasutatakse kvaliteetsema pildi ja teksti allikana ainult pärast videos nähtud slaididega vastavuse kontrollimist. Täpne töövoog on failis [`slaiditootlus.md`](slaiditootlus.md).

Video esmane slaidikontroll kasutab vaikimisi 20-sekundilise vahega kontrollkaadreid. Kontrollkaadrite võrdlus põhineb väikese halltoonides pildi digitaalsel sõrmejäljel, mitte kogu kaadri OCR-tekstil. Kui kahe järjestikuse põhikaadri vahel on pilt muutunud, otsib rakendus slaidi täpsema vahetusaja ainult selle 20-sekundilise vahemiku seest kahe-sekundilise sammuga. Mõlemad ajavahemikud peavad olema konfiguratsioonis muudetavad.

OCR käivitatakse pärast slaidikandidaadi leidmist eelkõige pealkirjaalal. Kogu slaidi OCR-i kasutatakse ainult siis, kui pealkiri, pildisarnasus ja slaidide järjekord ei võimalda eraldi slaidifailiga vastavust piisavalt kontrollida.

Teadaolev piirang on, et täielikult ühe 20-sekundilise põhivahemiku sisse jääv väga lühike slaid või sama slaidi juurde naasev ajutine vahepilt võib jääda leidmata. Piirang peab olema dokumenteeritud töö konfiguratsioonis ja tulemuses.

### 9.4. Slaidiviidete lisamine

- Iga tuvastatud slaid saab järjestikuse numbri.
- Võimaluse korral lisatakse slaidi pealkiri.
- Slaidi ligikaudne ilmumisaeg võetakse videost.
- Slaidiviide paigutatakse ajaliselt lähima transkriptsioonisegmendi piiri juurde.
- Transkriptsioonisegmenti slaidiviite tõttu ei lõhuta.
- Slaidi korduv näitamine võib viidata samale slaidile uue ilmumisajaga.
- Kui videos slaide pole, valmib transkript ilma slaidiviideteta.

## 10. Väljundid

### 10.1. Inimesele loetav põhiväljund

UTF-8 Markdown-fail, mis sisaldab:

- loengu nime ja põhilisi metaandmeid;
- ajatemplitega toimetamata transkripti;
- slaidivahetuste tähiseid;
- slaidipilte või suhtelisi viiteid pildifailidele;
- slaidide allika kirjeldust;
- nähtavaid märkusi ebaselgete või kinnitamata vastavuste kohta.

### 10.2. Tööartefaktid

Rakendus säilitab:

- loengukogumiku resolveri tulemuse;
- loengu ja meedia metaandmed;
- algse ajatemplitega transkriptsiooni masinloetaval kujul;
- slaidide olemasolu kontrolli tulemuse;
- slaidide järjekorra, pealkirjad ja ajastuse;
- püsivad slaidipildid;
- valikulise slaidifaili teisendamise ja vastavuse kontrolli tulemuse;
- mudelite, tööriistade ja konfiguratsiooni versioonid;
- töö oleku, kestuse ja vead.

Internetist uuesti hangitavat audiot ega videot püsivalt ei säilitata.

## 11. Välise keelemudeliga jätkamine

Rakenduse Markdown-väljund peab olema terviklik ja arusaadava struktuuriga, et kasutaja saaks selle soovi korral anda Gemini, OpenAI või mõne muu suure välise mudeli sisendiks.

Välise mudeli kasutamine, teenusepakkujale failide saatmine, transkripti keeleline ümberkirjutamine ja konspekti koostamine toimuvad rakendusest eraldi ning ei kuulu MVP2 töövoogu.

## 12. Mittefunktsionaalsed nõuded

- Rakendus töötab olemasoleval ARM64 Ubuntu serveril ilma GPU-ta.
- Kõik rakenduse käituskomponendid töötavad ühes või mitmes konteineris.
- Pikad tööd käivitatakse asünkroonselt ning neil on kontrollitav olek, logi ja väljund.
- Kõik projekti tekstifailid ja väljundid kasutavad UTF-8 kodeeringut.
- CPU-rasked tööd peavad olema järjestatavad.
- Valmis transkriptsiooni ei arvutata slaiditöötluse muutmise või kordamise tõttu uuesti.
- Ajutised audio- ja videofailid asuvad ainult runtime'i `work/` kataloogis ning eemaldatakse pärast töö lõppu.
- Mahukaid audio-, video- ja mudelifailide koopiaid ei salvestata Git-repositooriumi ega andmebaasi.
- MVP2 töötlusmootor kasutab failipõhist tööolekut. MVP3 veebirakendus kasutab olemasolevas Oracle Always Free andmebaasis projektile eraldatud oma skeemi kasutajate, loengutöötluste, ORDS-i tööseoste ja üleslaadimiste hoidmiseks; täpne mudel on failis [`../db/erd.md`](../db/erd.md).
- FastAPI ja worker kasutavad rakenduse skeemiga otseühendust `python-oracledb` ühenduste pooli kaudu. ORDS-i HTTP API-d kasutatakse ainult serveriülese tööjärjekorra jaoks.
- MVP3 veebiliides avaldatakse aadressil `https://ttu-loeng.fun-o.eu` olemasoleva ühise nginx-serveri kaudu. DNS-kirje, nginxi HTTP→HTTPS suunamine, nime sisaldav ühine TLS-sertifikaat ja HTTPS-pöördproksi töötavale veebikonteinerile on seadistatud.
- Saladusi, ligipääsutokeneid ja autentimisküpsiseid ei salvestata Git-i, logidesse ega väljunditesse.

## 13. MVP2 ulatusest välja jääv

- transkripti automaatne keeleline ümberkirjutamine või mehaaniline järelpuhastus;
- loengukonspekti koostamine;
- ainekava analüüsimine;
- eksamifookuse tuvastamine;
- kordamisküsimuste koostamine;
- transkripti toimetava või konspekti koostava keelemudeli kasutamine;
- välise keelemudeli API-ga ühendamine;
- Echo360 automaattranskriptsiooni laadimine ja töötlemine eestikeelse loengu põhitekstina;
- reaalajas transkriptsioon;
- mitme loengu paralleeltöötlus;
- DOCX-väljund;
- Oracle'i, Oracle'i failisalvestuse või AWS-i kasutuselevõtt;
- avalik mitmekasutajasüsteem, autentimine ja kvoodid.

## 14. Esimene kontrolljuhtum

Esimene kontrolljuhtum on ICM0032 loeng 3 „Business Continuity and Disaster Recovery Planning“.

Kontrollitud andmed:

- Echo360 avalik kogumikulink: <https://echo360.org.uk/section/6f6fcb6b-cd42-4328-81db-eb3e30df9151/public>;
- Echo lesson ID: `a18d8522-4637-4fcf-a62a-60e3b1f2e586`;
- loengu kestus: 2 tundi ja 15 minutit;
- TalTechNLP täistranskript: 15 064 sõna ja 447 segmenti;
- tegelik transkriptsiooniaeg: 1 tund ja 40 minutit;
- Echo ei paku selle loengu juures eraldi slide deck'i;
- esitlusvideo sisaldab slaide;
- kasutaja antud 88 slaidiga PPTX-faili täpne päritolu ja vastavus videole ei ole kinnitatud.

## 15. Vastuvõtukriteeriumid

MVP2 loetakse esimese kontrolljuhtumi põhjal edukaks, kui:

1. avalik Echo360 `/public` link loob kasutatava külalissessiooni;
2. rakendus kuvab kogumiku loengud ja eristab salvestise olemasolu;
3. kasutaja saab valida ühe kättesaadava salvestisega loengu;
4. rakendus loob kogu loengust eestikeelse ajatemplitega transkripti;
5. transkriptsioonitekst, segmentide ajapiirid ja sõnaajad säilivad mudeli väljundiga võrreldes muutmata;
6. transkripti saab pisteliselt võrrelda salvestisega;
7. rakendus kontrollib ja salvestab slaidide olemasolu või puudumise;
8. videost leitud slaidid saavad järjekorranumbri ja ligikaudse ilmumisaja;
9. slaidiviited lisatakse transkripti olemasolevaid segmente lõhkumata;
10. vastavaks kinnitatud PDF-, PPT- või PPTX-slaidid võivad väljundis asendada videost võetud madalama kvaliteediga pildid;
11. kontrollimata slaidifaili ei esitata videos kasutatud slaidide kinnitatud allikana;
12. transkript ja slaidid on inimesele loetavas Markdown-väljundis;
13. ajutine audio ja video eemaldatakse pärast edukat või nurjunud töötlust;
14. töö olek, kasutatud mudel, tööriistad, kestus ja võimalikud vead on kontrollitavad;
15. slaiditöötluse kordamine ei käivita valmis kõnetuvastust uuesti.

## 16. MVP3 laiendus

MVP3 peab lisama olemasolevale töötlusmootorile:

- FastAPI veebiliidese;
- võimaluse valida ja esitada korraga mitu Echo360 loengut;
- võimaluse siduda iga valitud loenguga oma PPT-, PPTX- või PDF-fail;
- kasutajavaate, mis kuvab iga loengu ASR-i ja slaiditöötluse autoriteetset ORDS-i olekut ning valmis artefakte;
- püsiva konteineriseeritud workeri, mis täidab ORDS-ist claim'itud `asr` ja `slides` töid;
- ORDS-i rakenduskoodi `ttu_loeng`;
- sama loengu slaiditöö sõltuvuse ASR-ist `previous_job_id` kaudu.
- serveri teiste rakendustega ühtse Google Identity Services ID-tokeniga sisselogimise, mille esimene edukas sisselogimine loob `USER` rolliga rakenduse kasutaja;
- ligipääsureegli, mille järgi `USER` näeb ja laadib alla kõigi tööde valmis tulemusi ning `ADMIN` võib lisaks uusi töid esitada ja avalikke linke hallata;
- administraatori võimaluse sulgeda konkreetne loengutöötlus soft delete'iga ilma sama kursuse teisi loenguid või submission'it sulgemata;
- olemasoleva kursuse valimise nime järgi uute loengute lisamisel; valitud kursuse Echo360 URL loetakse andmebaasist, samas säilib eraldi võimalus sisestada uus URL;
- aegunud sessiooniga kaitstud HTML-lehelt puhtale Google'i sisselogimisvaatele suunamise;
- sisselogimiseta slaididega ühendatud valmis Markdowni ja selle piltide ZIP-paketi allalaadimise ainult konkreetse loengu väärtustatud `public_id` otselingi kaudu; avalikku linki ei saa luua enne selle tulemuse valmimist ning tööde nimekiri ei ole anonüümselt nähtav;
- ühise teenusekihi, mida kasutavad HTML-marsruudid ja mille peale lisatakse järgmises etapis JSON API.

ORDS on ainus tööjärjekorra, järjestuse ja käivitamisloa autoriteet. Rakendus ei pea kohalikku järjekorda, ei vali ise järgmist tööd ega käivita ressursimahukat tööd ilma ORDS-i claim'ita. ORDS ei täida töö sisu: ASR-i ja slaiditöötluse protsessi, failid, logid ja artefaktid haldab `ttu_loeng` rakendus.

ASR ja slaiditöötlus kasutavad juba töötavat püsivat worker-konteinerit. Uue töö esitamine ei ehita image'it ega loo uut töötluskonteinerit. Worker on piiratud vaikimisi kolme CPU-tuumaga; ORDS väldib teiste liidestatud rakenduste mahukate tööde samaaegset aktiivseks muutumist.

MVP3 täpne tööleping, oleku autoriteet, kasutajavoog, konteinerijaotus ja etapistus on failis [`mvp3_veeb_ja_ords.md`](mvp3_veeb_ja_ords.md).
