# Tehniline spetsifikatsioon: ainekavapõhise loengukonspekti rakendus

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex), kasutaja kirjeldatud vajaduste, lähteülesande, kontrollitud projektimaterjalide ja analüüsitud tehnilise lähteolukorra põhjal.

## 2. Sisukord

- [3. Dokumendi roll](#3-dokumendi-roll)
- [4. Kontrollitud lähteolukord](#4-kontrollitud-lähteolukord)
- [5. Arhitektuuri põhimõtted](#5-arhitektuuri-põhimõtted)
- [6. Kavandatud komponendid](#6-kavandatud-komponendid)
- [7. Töövoog](#7-töövoog)
- [8. Artefaktid ja kataloogistruktuur](#8-artefaktid-ja-kataloogistruktuur)
- [9. Andmemudel](#9-andmemudel)
- [10. Cache ja korduvkasutus](#10-cache-ja-korduvkasutus)
- [11. Ressursipoliitika](#11-ressursipoliitika)
- [12. Mudelite ja tööriistade valiku benchmark](#12-mudelite-ja-tööriistade-valiku-benchmark)
- [13. Vead ja taastamine](#13-vead-ja-taastamine)
- [14. Turvalisus ja andmekaitse](#14-turvalisus-ja-andmekaitse)
- [15. Testimisstrateegia](#15-testimisstrateegia)
- [16. Etapid ja otsustusväravad](#16-etapid-ja-otsustusväravad)
- [17. Avatud tehnilised otsused](#17-avatud-tehnilised-otsused)
- [18. Esimene soovitatav teostustöö](#18-esimene-soovitatav-teostustöö)

## 3. Dokumendi roll

Käesolev dokument kirjeldab faili [`lahteylesanne.md`](lahteylesanne.md) nõuete kavandatud tehnilist teostust. Dokument eristab:

- kinnitatud arhitektuurilisi põhimõtteid;
- esialgseid tehnoloogiakandidaate;
- enne lukustamist benchmarki või spike’i vajavaid otsuseid.

Dokument ei anna luba andmebaasi, juurutuse ega kõrvalprojektide muutmiseks. Sellised tegevused vajavad eraldi kasutaja kinnitust vastavalt failile [`agents.md`](agents.md).

## 4. Kontrollitud lähteolukord

### 4.1. Server

Kontrollitud 30.10.2026:

- operatsioonisüsteem: Ubuntu Linux;
- arhitektuur: ARM64 (`aarch64`);
- CPU: 4 × ARM Neoverse-N1, üks lõim tuuma kohta;
- mälu: 23 GiB, kontrolli ajal ligikaudu 20 GiB saadaval;
- swap: puudub;
- GPU: puudub;
- vaba kettaruum: ligikaudu 73 GiB;
- rakendus töötab samas serveris teiste projektidega.

Järeldus: mälu võimaldab keskmise suurusega lokaalseid mudeleid, kuid CPU on peamine pudelikael. ASR-i, diariseerimist ja LLM-i ei käivitata vaikimisi samaaegselt. Töötlus võib kesta kaua; reaalajalisus ei ole nõue.

### 4.2. Echo360 ligipääs

Kontrollitud toimiv voog:

1. kasutaja või rakendus avab avaliku juurdepääsulingi
   `https://echo360.org.uk/section/6f6fcb6b-cd42-4328-81db-eb3e30df9151/public`;
2. Echo360 vastab ümbersuunamisega ning loob anonüümse külalissessiooni;
3. brauser jõuab kursuse kanoonilisele aadressile
   `https://echo360.org.uk/section/fe0e6009-e8d0-4f61-973f-4d231cbd1ff6/home`;
4. sama sessiooniga on kättesaadavad kursuse loengute nimekiri, loenguvaade, slaidid, dünaamiline transkriptsiooni endpoint ja meediavood.

Kanooniline `/home` link ei loo uues sessioonis külalisõigust. Resolver peab seetõttu säilitama nii kasutaja sisestatud `/public` lingi kui ka pärast ümbersuunamist saadud sektsiooni ID ja sessiooni metaandmed.

Kontrollitud näidisloeng „Avalik loeng AI Governance and Audit“ avanes sama külalissessiooniga. Kättesaadavad olid loenguvaade, slaidivaade, kaks meediavoogu, transkriptsiooni endpoint ja allalaadimise info. 31.10.2026 kinnitati ICM0032 loengu 3 põhjal endpoint'i kuju `/api/ui/echoplayer/lessons/{lesson_id}/medias/{media_id}/transcript`. Mängija algne `captions`-väli ja transkriptsioon on erinevad allikad: transkript laaditakse dünaamiliselt pärast mängija käivitamist. Endpoint on dokumenteeritud uurimistulemusena, kuid rakenduse praegune eestikeelsete loengute töövoog seda ei kutsu ega hangi Echo360 automaattranskriptsiooni.

30.10.2026 tehtud kahe avaliku kursuse võrdlus näitas lisaks:

- `/public` külalissessioon, ümbersuunamine ja `/section/{id}/syllabus` API töötavad standardse HTTP-kliendi ning küpsisesessiooniga; Playwright ei ole kontrollitud voos vajalik;
- avaliku lingi sektsiooni ID ja kanoonilise kursuse sektsiooni ID võivad erineda ning mõlemad tuleb säilitada;
- `hasVideo=true` ei tõenda salvestise olemasolu, sest sama lipp esineb ka tulevastel sisuta ajakavakirjetel;
- valmis salvestise tugevad tunnused on tegelik meediakirje, `isAvailable=true`, `isProcessing=false`, `isFailed=false`, detailvaate `hasAvailableVideo=true` ja olemasolev `video` objekt;
- `isPast` ja `isFuture` ei ole kursusteüleselt usaldusväärsed: käsitsi varem loodud meedia võib olla avaldatud hilisema kuupäevaga loengusse ning olla kättesaadav sõltumata ajatuse lippudest;
- kontroll-loeng „3. Business Continuity and Disaster Recovery“ sisaldab eraldi MP3-audioallikat ning 360p ja 1080p videofaile, kuid Echo ei paku selle juures eraldi slide deck’i.

### 4.3. Õppematerjalid

Analüüsitud lähtefailid:

- [`initial_materials/AINEKAVA 1.237978_Laiendatud ainekava ICM0032 2026-10-09 v9.pdf`](initial_materials/AINEKAVA%201.237978_Laiendatud%20ainekava%20ICM0032%202026-10-09%20v9.pdf) — ICM0032 laiendatud ainekava, 13 lehekülge;
- [`initial_materials/L03_konspekt.docx.pdf`](initial_materials/L03_konspekt.docx.pdf) — loengu 3 näidiskonspekt, 20 lehekülge.

Ainekava sisaldab teemade alam-õpiväljundeid, testide ja eksami konteksti ning õppematerjali prioriteete. Näidiskonspekt sisaldab eksamifookust, 22 nummerdatud teemajaotist, definitsioone, tabeleid, slaidijoonist, õppejõu näiteid ja 20 valikvastustega kordamisküsimust.

31.10.2026 lisas kasutaja PowerPointi faili, mis pealkirja, kirjelduse ja põgusa sisukontrolli järgi on tõenäoliselt loengu 3 slaidipakk. Muutmata koopia asub [`initial_materials/L03_slaidikandidaat.pptx`](initial_materials/L03_slaidikandidaat.pptx) ning sisaldab 88 slaidi ja 48 märkmelehte. Faili täpne päritolu ja vastavus salvestises kasutatud slaididele ei ole teada. PPTX säilib lähtekomplektis, kuid on esialgsest töövoost kõrvale jäetud; slaidid võetakse videost.

### 4.4. `err_video_to_text` taaskasutuse piir

Kontrollitud kõrvalprojekt:

- kasutab ERR-i olemasolevat VTT-d põhitekstina;
- hangib audio ja teeb pyannote’i abil kõnelejate diariseerimise;
- ühendab tekstisegmendid kõnelejate ajavahemikega;
- säilitab anonüümsed speaker-ID-d, kattuvuse, kindluse ja ülevaatusmaterjali;
- võimaldab rakendada käsitsi kinnitatud nimede kaarti diariseerimist kordamata;
- eraldab CPU-rasked tööd worker’isse ja piirab diariseerimiste samaaegsust vaikimisi üheni;
- hoiab mudelid, audio ja tööfailid välises runtime-kataloogis.

Käesoleva projekti eestikeelsete loengute töövoog ei kasuta ERR-i VTT-põhist transkriptsiooniloogikat, sest kontrollitud Echo360 eestikeelne automaattranskript on kasutuskõlbmatu. Töövoog ei päri Echo transkripti endpoint'i ega laadi, töötle või säilita selle JSON-, TXT- ega WebVTT-väljundit. Ingliskeelsete loengute Echo transkriptsiooni kvaliteeti ega võimalikku kasutamist ei ole hinnatud. Taaskasutuse kandidaat on diariseerimise, segmentide kõnelejatega sidumise, cache’i, metaandmete ja ülevaatuse muster. Tegelik koodi taaskasutus otsustatakse pärast moodulite liideste eraldi auditit.

## 5. Arhitektuuri põhimõtted

1. Esmalt ehitatakse ühe loengu vertikaalne CLI-töövoog.
2. Iga kallis etapp loob versioonitud ja taaskasutatava vaheartefakti.
3. Tööetapid on järjestikused ning neid saab eraldi uuesti käivitada.
4. Põhitekst, allikatõendid ja esitlusvorm hoitakse lahus.
5. Konspekti väide ei tohi kaotada sidet salvestise, slaidi ega ainekavaga ka siis, kui sisu järjestatakse ümber.
6. Keelemudel ei otsusta üksi, mis on eksamimaterjal.
7. Kvaliteedikontroll on eraldi tööetapp, mitte ainult generaatori prompt.
8. Mahukad failid asuvad väljaspool Git-repositooriumi.
9. Mudelid, tööriistad, promptide versioonid ja sisendite kontrollsummad salvestatakse töö metaandmetesse.
10. Kõik rakenduse käituskomponendid töötavad ühes või mitmes konteineris; esialgne CLI ei ole sellest nõudest erand.
11. Esialgne lahendus ei vaja püsivat andmebaasi ega vektorandmebaasi.
12. Kui püsiv andmebaas muutub vajalikuks, kasutatakse samas pilves olemasolevat Oracle Always Free andmebaasi ja sellele projektile eraldatud kasutajat ehk schemat.
13. Teise projekti schema kasutamine vajab eraldi põhjendust ning ligipääsu, vastutuse ja mõju selget dokumenteerimist mõlemas mõjutatud projektis enne ristkasutuse rakendamist.
14. Võimalik veebiliides või API avaldatakse `fun-o.eu` domeeni all serveri ühise nginx’i kaudu; projekt ei lisa eraldi avalikku veebiserverit.

## 6. Kavandatud komponendid

```text
CLI / hilisem veebiliides
          ↓
     tööde orkestreerija
          ↓
  Echo360 resolver ja importer
          ↓
 audio ettevalmistus + slaidide import
          ↓
        ASR worker
          ↓
 valikuline diariseerimise worker
          ↓
 transkriptsiooni, slaidide ja ainekava joondaja
          ↓
 tõendite eraldaja ja teemaplaneerija
          ↓
 lokaalne konspekti generaator
          ↓
 reeglipõhine ja mudelipõhine kontroll
          ↓
 Markdown → PDF + interaktiivne ülevaatus
```

### 6.1. CLI

Esialgne kasutuskuju võib olla:

```bash
lecture-notes resolve "<echo-public-url>"
lecture-notes ingest --lesson "<lesson-id>" --output-dir "<runtime-dir>"
lecture-notes transcribe --job "<job-dir>"
lecture-notes build --job "<job-dir>" --syllabus "<ainekava.pdf>"
lecture-notes review --job "<job-dir>"
lecture-notes export --job "<job-dir>" --format markdown
lecture-notes export --job "<job-dir>" --format pdf
```

Konkreetne käsurea leping lukustatakse enne teostust. Etappide eraldi käsud on vajalikud, et kallist ASR-i ei peaks konspekti prompti või kujundust muutes kordama.

### 6.2. Orkestreerija

MVP-s piisab failipõhisest tööolekust. Iga etapp:

- kontrollib eeltingimusi;
- võrdleb konfiguratsiooni ja sisendite kontrollsummasid;
- kasutab kehtivat cache’i või loob uue artefakti;
- kirjutab tulemuse atomaarse failivahetusega;
- märgib alguse, lõpu, kestuse, tulemuse ja vea;
- ei kustuta varasemate edukate etappide väljundeid.

Hiljem võib sama etappide mudeli viia worker’i ja API taha. MVP jaoks ei lisata Oracle’it ega muud serverandmebaasi, kui failipõhine olek katab kontrolljuhtumi vajadused. Kui püsiv andmebaas osutub vajalikuks, rakendub lähteülesandes määratud Oracle Always Free ja projektipõhise schema nõue.

### 6.3. Konteinerid

Esimene importeri spike, CLI ja kõik järgnevad töötluskomponendid käivitatakse konteineris. Ühe või mitme konteineri lõplik jaotus otsustatakse komponentide sõltuvuste, ressursikasutuse ja tööde eraldamise vajaduse põhjal. Mahukad käitusandmed ja mudelivahemälud hoitakse hosti runtime-kataloogis ning ühendatakse konteineritesse volume’itena. Konteinerid peavad kirjutama hosti mitte-root kasutaja õigustes.

Kui hiljem lisatakse Oracle’i ühendus, antakse vajalik ühenduskonfiguratsioon ja saladused konteinerile välise konfiguratsiooni kaudu; neid ei ehitata image’isse ega salvestata Git-repositooriumi.

Veebiliidese või API lisamisel ühendatakse selle sisemine teenus olemasoleva välise Docker-võrguga `funo_net`. Avalikud pordid 80 ja 443, TLS-i lõpetamine, staatiliste failide serveerimine ning pöördproksi reeglid jäävad `/home/ubuntu/fun_o` projektis hallatava ühise nginx’i vastutusse. TLS-sertifikaate haldab Let’s Encrypt ning vajaduse korral lisatakse uus alamdomeen olemasoleva sertifikaadihalduse kaudu sertifikaadi katvusse. Rakenduse sisemist teenust ei avaldata eraldi hostipordiga, kui selleks ei teki dokumenteeritud vajadust.

## 7. Töövoog

### 7.1. `RESOLVING`

Sisend on Echo360 `/public` link.

Tegevused:

1. luuakse uus standardse HTTP-kliendi küpsisesessioon;
2. avatakse `/public` link;
3. järgitakse ümbersuunamist kanoonilisele sektsioonile;
4. sessiooniküpsiseid hoitakse ainult protsessi mälus; manifesti salvestatakse üksnes küpsiste nimed ja aegumise koondinfo, mitte väärtused;
5. loetakse kursuse metaandmed ja loengute nimekiri;
6. salvestatakse resolveri versioon ja vastuste põhjal saadud identifikaatorid.

Playwright lisatakse ainult siis, kui mõni toetatav Echo360 avalik voog ei tööta HTTP-kliendiga ja vajadus on tegeliku näite põhjal tõendatud.

Väljund `resolver.json` sisaldab vähemalt:

- algset avalikku URL-i;
- kanoonilist sektsiooni URL-i ja ID-d;
- kursuse pealkirja;
- loengute identifikaatoreid, pealkirju, kuupäevi ja kestusi;
- resolveri versiooni;
- loomisaega;
- sessiooni küpsiste nimede ja aegumise kohta teada olevat saladusteta koondinfot;
- veakoode ja hoiatusi.

Sessioonisaladusi ei kirjutata konspekti, logidesse ega Git-i.

Iga loeng säilitab eraldi Echo algsed ajatuse lipud, ajatemplist tuletatud oleku, üldise sisuoleku ja salvestise oleku. Kui Echo ajatuse lipud ning ajatemplid ei ühti, lisatakse `ECHO_TIME_STATUS_CONFLICT`; kumbagi väärtust ei kirjutata teisega üle.

### 7.2. `INGESTING`

Valitud loengu puhul hangitakse:

- loengu lehe metaandmed;
- audio jaoks sobiv meediavoog;
- slaidivaade ja slaidiressursid;
- posterid või muud vajalikud pildid;
- olemasolu korral esitlusfail või slaidide tekstikiht;
- võimalusel slaidi ja ajajoone seos.

Salvestise olemasolu ei otsustata `hasVideo`, `isPast`, `isFuture`, ikooni värvi ega „LIVE“ sildi põhjal. `recording_status` tuletatakse tegelikest `Video` või `Audio` meediakirjetest järgmiste olekutena: `available`, `processing`, `failed` või `not_available`. Detailmanifest säilitab eraldi `hasAvailableVideo` ja muud Echo lipud.

Kui Echo ei paku eraldi slide deck’i, võetakse slaidid esitlusvideost. Tuvastatud erinevad slaidid seotakse nende videos näitamise ajavahemikuga. Toimetatud transkript võib kuvada kõik erinevad slaidid kronoloogiliselt; konspekti valitakse ainult teema mõistmiseks või õppimiseks vajalikud slaidid. PPTX-slaidikandidaati esialgses töövoos ei kasutata.

Täisvideot ei laadita vaikimisi püsivalt alla. Audio eraldatakse voost ning teisendatakse ASR-ile sobivaks mono 16 kHz vorminguks. Pika loengu audio jagatakse loogilisteks või kindla ülekattega tehnilisteks lõikudeks.

Internetis olemasolev audio ja sellest loodud WAV-id või lõigud paiknevad ainult `<runtime-root>/work/` all. Need eemaldatakse `finally` cleanup’is nii eduka kui nurjunud töötluse järel. Püsivalt säilitatakse allika taastamiseks vajalikud identifikaatorid, lähtefaili suurus ja kontrollsumma. Ajutise audio säilitamine vajab teadlikku `--keep-audio` valikut.

Slaidid säilitatakse originaalkujul või kadudeta pildina. Igal slaidil on püsiv töö-sisene ID, järjekorranumber, kontrollsumma ja võimalusel allika URL.

### 7.3. `TRANSCRIBING`

ASR loob:

- segmenditaseme teksti;
- algus- ja lõpuajad;
- võimalusel sõnataseme ajad;
- keele ja kindluse metaandmed;
- lõigu töötlusparameetrid.

Kogu loengu ajastatud transkriptsiooni käsk hangib Echo MP3 ise ajutisse `work/transcribe/` kataloogi, kirjutab enne pikka mudelitööd kontrollitava `run.json` oleku ning eemaldab audio `finally`-koristuses. Püsiv `transcript.json` sisaldab toimetamata segmendi- ja sõnaajastusi; `transcript.md` on sama väljundi loetav vaade. Videoloengu automaatsubtiitritest tundmatu AI-ga korrastatud ajamärkideta transkripti võib kasutada ainult normaliseerimise ja joondamise kandidaadina, mitte algse ajastatud ASR-kihi asendajana. Näitefail ei nimeta automaatsubtiitrite platvormi ega loo seost Echo360-ga. Kui algsed automaatsubtiitrid ja toimetuslogi puuduvad, ei saa korrastatud faili väidet sisu täieliku säilimise kohta automaatselt kinnitada.

31.10.2026 avaliku mängija kontrollis tagastas mängija algobjekt ICM0032 ja ICM0035 kontrollitud loengutel `captions = null`, kuid see ei kirjelda transkripti olemasolu. ICM0032 loengu 3 transkript saadi sama külalissessiooniga eraldi dünaamilisest JSON-endpoint'ist. Vastuse kontrollitud omadused olid:

- transkripti ID `de0f922c-5902-4f11-b723-b6263cb7ce11`;
- loomisaeg `2024-09-07T13:27:47Z`, olek `Available` ja `isAutomated: true`;
- 2171 ajastatud vihjet vahemikus `00:00:05.310–02:15:29.140`;
- 11 457 tühikutega eraldatud sõnalaadset ühikut ja 59 416 tekstimärki;
- kõnelejasildid: 2168 korda `Speaker 0`, kaks korda `Unknown` ja üks kord `Speaker 1`;
- Echo vihjete confidence'i keskmine `80,82`, mediaan `84`, miinimum `2` ja maksimum `100`; 846 vihjet olid märgitud `needsWork: true`;
- sama sisu TXT- ja WebVTT-eksport endpoint'ist `/transcript-file?format=text|vtt`.

Tekst on valdavalt ingliskeelne ning ei anna eestikeelsest loengust arusaadavat transkriptsiooni. Näiteks algus „These courses are here for business continuity and disaster recovery planning“ jätkub kiiresti semantiliselt seosetu ingliskeelse tekstiga. Väljund on kooskõlas olukorraga, kus eestikeelset kõnet püütakse tuvastada ingliskeelsete kõla poolest sarnaste sõnadena. [Echo ametlik keelesätete kirjeldus](https://support.echo360.com/hc/en-us/articles/360054629352-EchoVideo-Configuring-Transcription-Language-Settings) ütleb samuti, et vales põhikeeles kõne muutub transkriptis seosetuks tekstiks ning vaikekeel on inglise keel. Konkreetse loengu avalik vastus ei sisalda siiski ASR-i pakkuja, mudeli ega tuvastuskeele välja, mistõttu ei käsitleta selle tegelikku seadistust tõendatuna. Echo confidence on teenuse enda mõõdik ja ei näita selle loengu puhul sisulist kasutatavust. Ingliskeelse loengu kvaliteeti ei ole kontrollitud ning selle kasutatavuse kohta järeldust ei tehta.

Projekti otsus eestikeelsete loengute kohta: Echo automaattranskripti ei kasutata ka diagnostilise või auditeeritava võrdluskihina. Rakenduse praegune töövoog ei päri, laadi, säilita ega töötle seda, sest see kulutaks aega, võrku, salvestusruumi ja töötlusressurssi ilma kasutatava sisulise väljundita. Eestikeelne ajatemplitega põhitranskript luuakse otse loengu audiost projekti ASR-iga. See otsus ei anna hinnangut ingliskeelsete loengute Echo transkriptsiooni kvaliteedile.

ASR-i tehnoloogiakandidaadid:

1. TalTechNLP eestikeelsele kõnele kohandatud Whisper large-v3-turbo;
2. `whisper.cpp` GGML-mudel ARM64 CPU-l;
3. sama mudeli CTranslate2-versioon `faster-whisper`iga, kui ARM64 jõudlus ja pakendamine on sobiv.

Mudel, kvantimine ja runtime ei ole veel lukustatud. Enne valikut tehakse benchmark loengu 3 käsitsi kontrollitud lõikudega.

ASR-i terminivihjed või järelparanduse sõnastik koostatakse vähemalt:

- ainekava terminitest;
- slaididelt eraldatud terminitest;
- kursusepõhisest lühendite loendist;
- käsitsi kinnitatud nimedest.

Keelemudel ei tohi algset ASR-teksti märkamatult üle kirjutada. Kõik parandused peavad olema eraldi kihis ning säilitama algse teksti ja paranduse põhjuse.

#### Toimetatud täistranskript

Pärast kogu loengu toimetamata ajatemplitega ASR-transkripti valmimist luuakse sellest eraldi toimetatud täistranskript. See ei ole veel kokkuvõte ega konspekt. Algne `transcript.json` ja `transcript.md` jäävad muutmata ning toimetatud kiht peab olema nende juurde tagasi viidav.

Toimetamisel on lubatud:

- eemaldada sisuta kõnetäiteid ja ilmseid suulisi kordusi, näiteks „ja ja ja“;
- ühendada pausist või ASR-i segmentimisest põhjendamatult eraldatud lauseosi;
- parandada kirjavahemärke ja lausepiire;
- eemaldada pooleli jäetud ütluse fragment ainult siis, kui sama mõte esitatakse vahetult terviklikult uuesti;
- kujundada loetavad lõigud ilma õppesisu ümber järjestamata või koondamata.

Toimetamisel ei tohi:

- kokku võtta, üldistada, lisada ega sisuliselt ümber sõnastada;
- eemaldada näiteid, definitsioone, erandeid, rõhuasetusi, eksamijuhiseid ega terminipaare;
- parandada ebakindlat terminit oletuse põhjal;
- kaotada seost algsete segmentide ja ajatemplitega.

Mudelile antakse järjestikustest ASR-segmentidest ühendatud mõistliku pikkusega tekstilõik. Segmendid on tehnilised ajastusüksused, mitte eraldi toimetamisülesanded. Mudel saab tavalise eestikeelse juhise korrastada tekst kirjakeelseks, eemaldada tarbetud kordused ja vaadata üle lauselõpud ning tagastab tavalise teksti. Lõigu algus- ja lõpuaeg säilitatakse rakenduses; mudel ei pea ajatemplite ega tehniliste ID-dega tegelema.

Transkripti toimetamise kandidaat on `tartuNLP/Llama-3.1-EstLLM-8B-Instruct-1125`. Ollama töötab projekti enda `llm-ollama` teenusena ja kasutab projekti hostikasutaja UID/GID-d. Mudel lukustatakse töövoogu alles pärast seda, kui inimene on lihtsa promptiga katselõigu alg- ja lõppteksti võrrelnud.

### 7.4. `DIARIZING`

Diariseerimisrežiimid:

- `single-speaker`: diariseerimist ei käivitata; kõik põhisegmendid seotakse õppejõu rolliga, kuid auditooriumi küsimusi võib ülevaatuses eraldi märkida;
- `automatic`: esmalt hinnatakse odavalt, kas kõnelejavahetusi on tõenäoliselt vaja analüüsida; otsuse reegel vajab spike’i;
- `multi-speaker`: käivitatakse pyannote’i diariseerimine.

Pyannote’i tulemuse ja ASR-segmentide sidumisel rakendatakse `err_video_to_text` projektist kontrollitud põhimõtteid:

- anonüümne `speaker_id` on eraldi isiku nimest;
- speaker-ID ei ole eri tööde vahel püsiv identiteet;
- segment seotakse suurima ajalise kattuvusega kõnelejaga;
- talletatakse kattuvussuhe ja kindlus;
- ebapiisava kattuvuse korral jääb segment `unassigned`;
- käsitsi nimede kaart peab olema rakendatav diariseerimist kordamata;
- ebakindlad või segakõnega lõigud lähevad inimese ülevaatusse.

Diariseerimine käib ASR-ist ja LLM-ist eraldi protsessina. PyTorch/pyannote vabastatakse enne järgmise raske mudeli laadimist.

### 7.5. `PARSING_SYLLABUS`

Ainekavast eraldatakse struktureeritud kujule vähemalt:

- aine nimi ja versioon;
- loengute numbrid ning teemad;
- alam-õpiväljundid;
- loengukimpude testid;
- eksami üldreeglid;
- külalisloengute staatus;
- õppejõu kirjeldatud teadmised ja oskused;
- terminid ja standardid.

Automaatne parser loob mustandi. Loengu ja ainekava teema seos peab olema inimesele nähtav ning parandatav.

### 7.6. `ALIGNING_SOURCES`

Joondaja loob seosed:

- transkriptsioonisegment ↔ audio ajavahemik;
- transkriptsioonisegment ↔ aktiivne või lähedane slaid;
- segment/slaid ↔ ainekava punkt;
- segment ↔ kõneleja;
- sama teema eri ajakohtade segmendid ↔ ühine teemaplokk.

Kui Echo360 ei anna slaidide täpset ajastust, kasutatakse järjestikku:

1. Echo360 enda slaidi- või esitluse metaandmeid;
2. videos nähtava slaidi vahetuse tuvastamist valitud kaadritest;
3. transkriptsiooni ja slaiditeksti terminikattuvust;
4. inimese kinnitust.

OCR-i ei käivitata kogu video kõikidel kaadritel. OCR-i kasutatakse slaididel ainult siis, kui tekstikihti pole muul viisil võimalik saada.

### 7.7. `EXTRACTING_EVIDENCE`

Konspekti koostamisel peab mudel leidma sisendmaterjalidest vähemalt järgmise õppesisu:

- definitsioon;
- oluline väide;
- protsessi samm;
- võrdlus;
- näide või juhtum;
- terminipaar;
- õppejõu rõhutus;
- eksamijuhis;
- „ei pea teadma“ juhis;
- oluline slaid või joonis;
- küsimus ja vastus;
- vastuolu või ebakindlus.

Olulised väited peavad olema seostatavad vähemalt ühe sisendallikaga. Eksamijuhis vajab ainekava või õppejõu selget ütlust, mitte ainult mudeli järeldust. Eraldi struktureeritud kandidaatide või teemakaardi loomine ei ole konspekti koostamise kohustuslik vaheetapp.

### 7.8. `PLANNING_NOTES`

Konspekti peatükkide ülesehitus lähtub ainekavast ja loengu sisust. Kava ei pea järgima loengu ajajoont.

Planeerija peab:

- koondama sama teema eri ajakohtadest;
- säilitama iga alamteema allikad;
- vältima sama väite kordamist eri peatükkides;
- märkima ainekava katmata punktid;
- valima slaidid, mis tuleb lisada pildina;
- eristama põhisisu, lisaselgitust ja eksamifookust.

### 7.9. `GENERATING_NOTES`

Töötluse tulemus peab olema üks terviklik ja iseseisvalt loetav konspekt. Mudelikutsete arv ega sisemine jaotus ei ole funktsionaalne nõue ning seda ei määrata oletuse põhjal ette. Esimene tervikkatse annab EstLLM-ile ühe sisendpaketina ainekava asjakohase osa, kogu ajatemplitega algtranskripti ja videost eraldatud slaidiandmed ning palub väljastada ühe tervikliku Markdown-konspekti.

Konspekti mahule ei seata tokenipõhist väljundipiiri. Sisuline vastuvõtukriteerium on lähteülesandes nõutud katvus, iseseisev loetavus ning näidiskonspektiga võrreldav detailsus ja struktuur. Mudeli tehnilisi kontekstipiire käsitletakse käituskeskkonna omadusena, mitte konspekti soovitud pikkuse mõõduna.

Kohaliku LLM-i liides peab olema teenusepakkujast sõltumatu. Esialgne käitusviis on lokaalne Ollama või vajaduse korral `llama.cpp`-põhine endpoint.

Konspekti sünteesi põhikandidaat on sama `tartuNLP/Llama-3.1-EstLLM-8B-Instruct-1125`, mida hinnatakse transkripti toimetamisel. Ühe mudeli kasutamine ei ühenda tööetappe: transkripti toimetamisel ja konspekti sünteesil on eraldi prompt, sisendpakett, väljund ja kvaliteedikontroll. Konspekti sisendiks on ainekava asjakohane osa, kogu ajatemplitega algtranskript ja videost eraldatud slaidiandmed; toimetatud proosat ega näidiskonspekti ei kasutata konspekti faktilise sisendina.

Eraldi konspektimudel lisatakse ainult siis, kui EstLLM-i ülesandepõhine katse ei saavuta faktilise kooskõla, sisusäilituse, eesti keele või juhiste järgimise kvaliteediväravat. Sellisel juhul võrreldakse sama lukustatud tõendipaketi peal teist lokaalset avatud mudelit; suurema mudeli valikut ei põhjendata üksnes parameetrite arvuga.

Esimene Etapp 3 vertikaalne proov kasutas muutmata kujul serveris projekti `/home/ubuntu/Double_Check_AI` kaudu juba töötavat Ollama teenust hostipordil `11434` ja olemasolevat `mistral:latest` mudelit. See oli ajalooline tehnilise ahela katse ega ole järgmise sisukatse mudelivalik. Mudeli nimi, digest, kvantimine, prompti kontrollsumma, tõendipaketi kontrollsumma ja ajakulu säilitatakse jooksu metaandmetes.

### 7.10. `VALIDATING`

Kontroll toimub eraldi kihtidena:

#### Deterministlik kontroll

- kõik viidatud segmentide ja slaidide ID-d on olemas;
- ajavahemikud jäävad loengu kestusse;
- kõik ainekava punktid on kaetud või märgitud katmata;
- slaidipildid on olemas;
- Markdowni siselingid on kehtivad;
- kordamisküsimuse vastus on konspektist leitav.
- peatüki esimene pealkiri kirjeldab dokumendi päritolu, sisukord on olemas ning kõik tõendipaketis märgitud katvuslüngad on tekstis sõnaselgelt nimetatud.

#### Tõendipõhine kontroll

- eksamifookuse väitel on nõutud allikatüüp;
- „õppejõud rõhutas“ väitel on kõnesegment;
- numbrilisel või normatiivsel väitel on otsene allikas;
- vastuolulised allikad ei ole vaikimisi üheks faktiks silutud.

#### Mudelipõhine kontroll

Teine mudelikäik võrdleb peatükki ainult selle tõendipaketiga ja tagastab:

- toetamata väited;
- puuduva olulise sisu;
- võimalikud terminivead;
- kordused;
- ebapiisavalt selgitatud mõisted.

Mudelikontroll ei kinnita ise väidet lõplikult; kahtlane tulemus jääb inimese ülevaatusse.

### 7.11. `REVIEWING`

Esimene MVP võib väljastada staatilise HTML-ülevaate. Hilisem veebivaade sisaldab:

- konspekti redaktorit;
- ainekava katvuse paneeli;
- valitud väite tõendite paneeli;
- slaidikuva;
- transkriptsioonilõiku;
- audio- või videopleierit;
- nuppu viidatud lõigu esitamiseks;
- kinnitamise, parandamise ja tagasilükkamise olekut.

Rakenduse pleier avab viite algusajast mõni sekund varem ning võib lõpuajas peatuda. Echo360 enda ajatempli deep-linki ei eeldata enne selle toe eraldi kontrollimist.

### 7.12. `EXPORTING`

Kanooniline avaldamisallikas on Markdown.

Markdown sisaldab:

- YAML või JSON front matter’it töö ja allikate metaandmetega;
- peatükke;
- tabeleid;
- slaidipilte;
- kompaktseid allikaviiteid;
- kordamisküsimusi;
- vajaduse korral lõpuviiteid.

PDF genereeritakse samast Markdownist. PDF peab säilitama:

- peatükihierarhia;
- pildid ja tabelid;
- inimloetavad ajatemplid;
- klikitavad lingid, kui rakenduse URL on olemas;
- leheküljenumbrid ja sobiva murdumise.

DOCX-i ei genereerita.

PDF-i tööriistakandidaat lukustatakse ARM64 serveris tehtava spike’i järel. Võimalikud variandid on Pandoc koos sobiva PDF-mootoriga või HTML/CSS → PDF. Valik peab toetama eesti tähemärke ja slaidipilte.

## 8. Artefaktid ja kataloogistruktuur

Git-repositooriumis paiknevad kood, skeemid, promptide mallid, testfiksuurid ja dokumentatsioon. Käitusaegsed failid paiknevad hostis `/srv/ttu-loeng` all ning konteineris `/runtime` all. Paigutus järgib `err_video_to_text` projekti mustrit:

```text
/srv/ttu-loeng/
├── outputs/
├── work/
├── models/huggingface/
├── cache/
└── home/
```

Kataloogid kuuluvad `.env` failis määratud hosti `TTU_LOENG_UID:TTU_LOENG_GID` kasutajale. Konteiner ei kasuta `sudo` ega `chown`-i, ei kirjuta projekti checkout’i ning käivitub sama UID/GID-ga.

30.10.2026 loodi serverisse kirjeldatud kataloogid `/srv/ttu-loeng` alla hostikasutaja `1001:1001` omandisse. Projekti lokaalne, Gitist välja jäetud `.env` kasutab sama UID/GID-d.

Tulevikus võib püsifailide hoidmiseks hinnata Oracle’i enda failisalvestust, Oracle BLOB-e või AWS storage’it. See ei kuulu praeguse MVP skoopi ega muuda tänast `/srv/ttu-loeng` runtime’i lahendust. Enne sellist muudatust tuleb eraldi analüüsida vajadust, kulusid, ligipääsuõigusi, andmete elutsüklit, taastatavust ja olemasolevate failide migratsiooni.

Etapp 1 spike kasutab enne täieliku töökataloogi skeemi lukustamist järgmist tegelikku struktuuri:

```text
<runtime-root>/
├── outputs/
│   ├── resolver.json
│   └── lessons/<lesson-id>/
│       ├── lesson.json
│       ├── media.json
│       ├── slides.json
│       └── run.json
└── work/
    └── ingest/<work-key>/source.mp3  # ajutine
```

`resolver.json` sisaldab mõlemat sektsiooni ID-d, normaliseeritud loengunimekirja ja vastuoluhoiatusi. `media.json` sisaldab URL-i päringuosadeta allikakirjeldusi ning audio kontrollimisel allalaaditud faili kontrollsummat, suurust ja cleanup’i tulemust. Sessiooniküpsiste väärtusi ei kirjutata runtime’i. Kõik manifestid ja ajutine audiofail kirjutatakse atomaarse failivahetusega. `run.json` sisaldab kestust ja protsessi maksimaalset RSS-mälu. Ajutine audio ei asu `outputs/` all.

30.10.2026 integraatsioonikatses laadis konteiner kontroll-loengu 113 081 307-baidise MP3 täielikult alla, võrdles suurust Echo metaandmetega, arvutas SHA-256 kontrollsumma ning eemaldas lähtefaili pärast kontrolli. `work/` alla ei jäänud audiofaili. Katse kinnitas ka selle, et konteineri UID/GID peab vastama runtime-kataloogide hosti omanikule.

Kavandatud tööstruktuur:

```text
<runtime-root>/jobs/<job-id>/
├── job.json
├── resolver/
│   └── resolver.json
├── source/
│   ├── lesson.json
│   ├── audio/
│   ├── slides/
│   └── slide_manifest.json
├── transcript/
│   ├── raw_asr.json
│   ├── normalized_transcript.json
│   └── terminology_review.json
├── diarization/
│   ├── speakers.json
│   └── speaker_review.json
├── syllabus/
│   └── syllabus.json
├── evidence/
│   ├── evidence.json
│   └── coverage.json
├── notes/
│   ├── outline.json
│   ├── draft.md
│   ├── validation.json
│   └── review.md
└── export/
    ├── conspect.md
    ├── conspect.pdf
    └── assets/
```

Ajutised WAV- ja videolõigud asuvad eraldi `work/` kataloogis ning kustutatakse pärast etapi edukat või nurjunud lõpetamist, kui `keep`-valikut pole teadlikult kasutatud.

## 9. Andmemudel

### 9.1. Töö metaandmed

```json
{
  "schema_version": "1.0",
  "job_id": "...",
  "source_public_url": ".../public",
  "section_id": "...",
  "lesson_id": "...",
  "title": "...",
  "language": "et",
  "stages": [],
  "models": {},
  "tools": {},
  "input_checksums": {},
  "created_at": "...Z",
  "updated_at": "...Z"
}
```

### 9.2. Transkriptsioonisegment

```json
{
  "id": "seg_000123",
  "start_ms": 4460000,
  "end_ms": 4525000,
  "text_raw": "...",
  "text_normalized": "...",
  "asr_confidence": null,
  "speaker_id": "SPEAKER_00",
  "speaker_name": "Paul Leis",
  "speaker_name_source": "course_metadata",
  "attribution_status": "assigned",
  "attribution_confidence": "high",
  "slide_ids": ["slide_0027"],
  "flags": []
}
```

### 9.3. Tõend

```json
{
  "id": "evidence_000456",
  "kind": "definition",
  "claim_candidate": "RTO määrab aja, mille jooksul peab alternatiivne protsess käivituma.",
  "lesson_id": "...",
  "segment_ids": ["seg_000123"],
  "start_ms": 4460000,
  "end_ms": 4525000,
  "slide_ids": ["slide_0027"],
  "syllabus_items": ["3.d"],
  "speaker_id": "SPEAKER_00",
  "confidence": "high",
  "review_status": "unreviewed"
}
```

### 9.4. Konspekti peatükk

```json
{
  "id": "section_rto_rpo",
  "title": "RTO ja RPO",
  "syllabus_items": ["3.d"],
  "evidence_ids": ["evidence_000456"],
  "embedded_slide_ids": ["slide_0027"],
  "body_markdown": "...",
  "review_status": "unreviewed"
}
```

Skeemid versionitakse. Väljade täpne loetelu lukustatakse pärast esimese kontrollandmestiku koostamist.

## 10. Cache ja korduvkasutus

Cache’i võtmed peavad sisaldama sisendi kontrollsummat ja etappi mõjutavat konfiguratsiooni.

Näited:

- resolver: avalik URL + resolveri versioon;
- slaidid: loengu ID + allika ETag/versioon + importeri versioon;
- audio: meedia ID + voo identifikaator + ettevalmistuse parameetrid;
- ASR: audio kontrollsumma + mudeli ID/revisjon + runtime + parameetrid;
- diariseerimine: audio kontrollsumma + mudeli revisjon + speaker-vihjed;
- ainekava: PDF kontrollsumma + parseri versioon;
- toimetatud transkript: algse transkripti kontrollsumma + mudeli ID/revisjon + kvantimine + prompti ja väljundskeemi versioon + lõigustamise parameetrid;
- tõendid: transkriptsiooni, slaidimanifesti ja ainekava kontrollsummad + prompti versioon;
- konspekt: tõendipaketi kontrollsumma + kava + mudel + prompti versioon.

Odavaid etappe võib uuesti käivitada. ASR-i ja diariseerimist ei korrata pelgalt PDF-i kujunduse või konspekti sõnastuse muutmise tõttu.

## 11. Ressursipoliitika

- Vaikimisi üks aktiivne raske töö korraga.
- ASR kasutab kuni kolme CPU-lõime; üks tuum jäetakse süsteemile ja teistele teenustele. Täpne arv mõõdetakse.
- Diariseerimine kasutab olemasoleva serveri tõestatud konfiguratsiooni lähtepunktina kuni kolme CPU-lõime.
- LLM käivitatakse alles pärast ASR-i ja pyannote’i protsessi lõpetamist ning mälu vabastamist.
- Chromium suletakse pärast meediaallikate ja vajaliku sessiooniinfo hankimist.
- Swap’i puudumise tõttu kontrollitakse enne mudeli laadimist vaba mälu ning OOM-i vältimiseks ei hoita suuri mudeleid paralleelselt residentsetena.
- Töötlemise ajal mõõdetakse seinakella aega, CPU-aega, maksimaalset RSS-mälu ja kettakasutust.
- Töötlusaja SLA-d ei määrata enne benchmarki.

## 12. Mudelite ja tööriistade valiku benchmark

### 12.1. Kontrollandmestik

Loengu 3 põhjal koostatakse enne võrdlust lukustatud kontrollkomplekt:

- mitu käsitsi parandatud 5–10 minuti helilõiku loengu algusest, keskelt ja lõpust;
- vähemalt üks ingliskeelsete IT-terminitega lõik;
- üks slaidiskeemi selgitus;
- üks eksamifookuse ütlus;
- üks näide või jutustus;
- võimaluse korral kõnelejavahetus.

Etapp 2 teostus kasutab masinloetavat kontrollkomplekti `benchmarks/datasets/lecture3_v1.json`. Kolm viieminutilist lõiku loengu algusest, keskelt ja lõpust lukustati enne benchmarki väljundite vaatamist. Kontrollkomplekti olek on `locked_pending_human_reference`: ajavahemikke ei muudeta tulemuse parandamiseks, kuid kvaliteedi otsustusväravat ei suleta enne inimese kontrollitud referentsteksti lisamist.

### 12.2. ASR mõõdikud

- sõna- ja märgitaseme veamäär, kui käsitsi tõde on olemas;
- kursuse terminite täpsus;
- nimede ja lühendite täpsus;
- segmentide ajastuse kasutatavus;
- tööaeg;
- maksimaalne mälu;
- väljundi stabiilsus pikkadel lõikudel.

Benchmark käib eraldi `asr` Compose’i workeris. Esimese võrdluse mõlemad konfiguratsioonid kasutasid Faster-Whisper 1.2.1, CTranslate2 4.8.4 CPU int8 arvutust, kolme lõime, üht worker’it, eesti keelt, beam size 5, sõnaajastusi ning väljalülitatud VAD-i ja eelmise lõigu konteksti.

30.10.2026 mõõdetud tulemused 900 sekundi heli kohta:

| Konfiguratsioon | Mudeli revisjon | Transkriptsiooniaeg | RTF | max RSS |
|---|---|---:|---:|---:|
| TalTechNLP `whisper-large-v3-turbo-et-verbatim` int8 | `1ae5a487d24116955803df4d9d01df56645eb44f` | 632,909 s | 0,7032 | 4 942 408 KiB |
| Systran `faster-whisper-medium` int8 | `08e178d48790749d25932bbc082711ddcfdfbc4f` | 779,761 s | 0,8664 | 4 452 980 KiB |

Tehniliseks põhikonfiguratsiooniks valiti tingimuslikult TalTechNLP mudel: see oli ligikaudu 19% kiirem ning AI kvalitatiivsel vaatlusel oli eestikeelne tekst ja terminoloogia selgelt loetavam. Mõlema konfiguratsiooni mäluvajadus on olemasoleva 23 GiB RAM-i juures väike ega erista kandidaate; RSS jääb auditeeritavaks mõõdikuks, mitte valikuargumendiks. Kvaliteedivärav jääb avatuks, kuni lukustatud lõikudel on inimese kontrollitud referentstekst ja arvutatud WER/CER. Täielik raport ja otsuse piirangud on failis [`asr_benchmark.md`](asr_benchmark.md).

### 12.3. LLM mõõdikud

- toimetatud transkripti sisusäilitus;
- korduste ja täitesõnade eemaldamise täpsus;
- lausepiiride ja kirjavahemärkide kvaliteet;
- terminite, nimede ja ingliskeelsete väljendite säilimine;
- algsegmentide ja ajatemplite seose täielikkus;
- väljundskeemi ja muutmispiirangute järgimine;
- faktiline kooskõla tõenditega;
- ainekava katvus;
- toetamata väidete arv;
- põhjendamata eksamiväidete arv;
- eestikeelse stiili ja terminoloogia kvaliteet;
- korduste hulk;
- inimese parandustöö maht;
- tööaeg ja mälu.

Esimene LLM-i põhikandidaat on `tartuNLP/Llama-3.1-EstLLM-8B-Instruct-1125`. Sama mudelit hinnatakse kahes eraldi katses: esmalt toimetatud täistranskripti lõikudel ja seejärel ühe tervikliku konspektiteema tõendipaketil. Transkripti katse referents on inimese kontrollitud toimetus; konspekti katse sisend ja hindamine jäävad tõendipõhiseks. Mudeli üldised eesti keele benchmarkid toetavad kandidaadi valikut, kuid ei asenda projekti ülesandepõhist kontrolli.

Mudel lukustatakse vastava etapi jaoks alles pärast seda, kui inimese ülevaatus kinnitab, et sisulisi väiteid ei lisatud ega kaotatud ning eesti keel, terminid ja viidatavus vastavad nõuetele. Kui EstLLM lävendit ei täida, võrreldakse sama lukustatud materjali peal järgmist lokaalset avatud kandidaati. Mudelite numbrilised lävendid ja hindamisjuhend määratakse enne kogu loengu toimetatud või sünteesitud tulemuse loomist.

## 13. Vead ja taastamine

Masinloetavad veaklassid peavad eristama vähemalt:

- `INVALID_PUBLIC_URL`;
- `PUBLIC_SESSION_FAILED`;
- `SECTION_NOT_FOUND`;
- `LESSON_NOT_FOUND`;
- `MEDIA_NOT_FOUND`;
- `SLIDES_NOT_FOUND`;
- `DOWNLOAD_FAILED`;
- `ASR_FAILED`;
- `DIARIZATION_FAILED`;
- `SYLLABUS_PARSE_FAILED`;
- `SOURCE_ALIGNMENT_FAILED`;
- `GENERATION_FAILED`;
- `VALIDATION_FAILED`;
- `PDF_EXPORT_FAILED`.

Vea kirje sisaldab etappi, lühikest sõnumit, erandi tüüpi, taaskäivitatavuse hinnangut ja logiviidet. Saladusi, küpsiseid ega täielikke signeeritud meedia-URL-e ei kirjutata veateatesse.

Etapi korduskäivitus kasutab viimast kehtivat eelnevat artefakti. Pooleliolev fail kirjutatakse ajutise nimega ja nimetatakse lõplikuks alles pärast edukat valideerimist.

## 14. Turvalisus ja andmekaitse

- Töödeldakse ainult kasutajale õiguspäraselt kättesaadavaid Echo360 materjale.
- Resolver ei proovi autentimispiiranguid mööda hiilida; kasutatakse avalikku `/public` külalissessiooni.
- Sessiooniküpsised on ajutised saladused.
- Hugging Face’i või muud tokenid tulevad `.env`-ist ning neid ei logita.
- Võimaliku Oracle’i schema kasutajatunnused ja ühenduskonfiguratsioon tulevad välisest saladuste konfiguratsioonist ning neid ei logita ega salvestata image’isse.
- Avaliku veebiliidese TLS lõpetatakse ühises nginx’is ja sertifikaati haldab Let’s Encrypt. Hostinimi peab kuuluma sertifikaadi katvusse; vajaduse korral lisatakse uus alamdomeen enne nginx’i serveriploki aktiveerimist.
- Väliseid tasulisi ASR- või LLM-teenuseid ei kasutata vaikimisi.
- Enne avaliku teenuse loomist tuleb eraldi hinnata loengusalvestiste, slaidide ja tuletatud konspektide säilitamise ning jagamise õigusi.
- Käitusaegsed failid peavad kuuluma mitte-root hostikasutajale.

## 15. Testimisstrateegia

### 15.1. Üksustestid

- Echo URL-i ja identifikaatorite parsimine;
- ajatemplite teisendamine;
- segmentide ja speaker-spanide kattuvus;
- ainekava struktuuri normaliseerimine;
- allikaviidete vormistamine;
- cache’i võtmed;
- Markdowni linkide ja varade kontroll;
- skeemide valideerimine.

### 15.2. Fiksuurtestid

- salvestatud Echo360 metaandmete vastused;
- minimaalne kursuse ja loengu manifest;
- näidisslaidid;
- lühike käsitsi kontrollitud ASR-lõik;
- ühe ja mitme kõnelejaga näidis;
- ainekava väljavõte;
- tõendipakett ja oodatud viited.

Fiksuurid ei tohi sisaldada saladusi ega põhjendamatult mahukat autoriõigusega kaitstud materjali.

### 15.3. Integratsioonitestid

- avalik link → kursuse nimekiri;
- loeng → audio ja slaidid;
- audio → transkriptsioon;
- transkriptsioon + ainekava + slaidid → tõendid;
- tõendid → Markdown;
- Markdown → PDF;
- viide → pleieris õige ajavahemik.

Live-Echo360 testid peavad olema eristatavad võrguvabadest testidest.

### 15.4. Kuldtest

Loengu 3 tulemust võrreldakse:

- käsitsi kontrollitud transkriptsioonilõikudega;
- ainekava punktidega 3.a–3.e;
- näidiskonspekti struktuuri ja detailsusega;
- inimese hinnanguga faktitäpsusele ja õppimiskasutusele.

Näidiskonspekti ei kopeerita ega kasutata automaatse faktilise tõena.

## 16. Etapid ja otsustusväravad

### Etapp 0 — dokumentatsioon

- lähteülesanne;
- tehniline spetsifikatsioon;
- tööreeglid;

Valmis, kui dokumentides pole teadaolevaid sisulisi vastuolusid ja kasutaja on ulatuse kinnitanud.

### Etapp 1 — Echo360 importeri spike

- konteineris käivitatav importer;
- `/public` sessioon;
- kursuse nimekiri;
- ühe loengu audio- ja slaidimanifest;
- auditeeritav resolveri väljund.

Otsustusvärav: vajalikud allikad on automaatselt ja korratavalt hangitavad.

### Etapp 2 — ASR benchmark

- kontrollandmestiku kirjeldus ja lukustatud kontrollandmestik;
- vähemalt kaks runtime’i või konfiguratsiooni;
- kvaliteedi- ja ressursiraport;
- lukustatud põhikonfiguratsioon.

Otsustusvärav: eestikeelne transkriptsioon on konspekti jaoks piisavalt kasutatav.

Seis 30.10.2026: kontrollkomplekt, kaks konfiguratsiooni, ressursiraport ja tingimuslik tehniline põhikonfiguratsioon on valmis. Otsustusvärav ei ole lõplikult suletud, sest inimese kontrollitud referentstekst ning sellest arvutatavad WER, CER ja terminite täpsus puuduvad.

### Etapp 3 — tõendite ja ainekava vertikaalne proov

- ainekava parser;
- slaidi/transkriptsiooni seosed;
- ühe teema tõendipakett;
- ühe peatüki konspekt koos viidetega.

Otsustusvärav: peatükk on faktitäpne, iseseisvalt loetav ja jälgitav.

Esimese vertikaalse proovi teemaks valiti ainekava punkt 3.e „intsidentide haldamine, reageerimine ja suhtlus“. Teema kattub TalTechNLP kontrolllõiguga `01:55:00–02:00:00`. Kuna Echo ei paku loengu 3 juures eraldi slide deck’i, eraldab `pipeline` konteiner sama ajavahemiku slaidikaadrid 360p esitlusvideost, rakendab neile eesti- ja ingliskeelse OCR-i ning eemaldab internetist uuesti hangitava ajutise video pärast töötlust.

Vertikaalse proovi auditeeritav käsitsi kureeritud valik asub failis [`benchmarks/evidence/l03_3e_v1.json`](../benchmarks/evidence/l03_3e_v1.json). Valik seob ainekava lehekülje, TalTechNLP ASR-i segmendid, kolm slaidikaadrit ja viis väitekandidaati. Valitud lõik katab reageerimise, taastamise, juhtimistasemed ja dokumenteerimise, kuid mitte piisavalt teavituse juhtimise ega kriisisuhtluse meetmeid. Seetõttu peab katvus jääma olekusse `partial`; generaator ei tohi puuduvaid aspekte üldteadmistega täiendada.

Slaidikirje säilitab nii auditeeritava runtime-failitee kui ka peatüki asukohast arvutatud suhtelise `markdown_path` väärtuse. Markdowni generaator peab kasutama viimast, et pilt toimiks ka hostis või hilisemas ekspordis ega sõltuks konteinerisisesest `/runtime` juurest.

### Etapp 4 — kogu loeng 3

- punktide 3.a–3.e katvus;
- slaidid;
- eksamifookus;
- kordamisküsimused;
- Markdown ja PDF;
- inimese ülevaatusraport.

Otsustusvärav: tulemus vastab faili `lahteylesanne.md` vastuvõtukriteeriumidele.

### Etapp 5 — ülevaatusliides

- konspekt, slaid, transkriptsioon ja pleier ühes vaates;
- klõpsatav allikaviide;
- paranduste ja kinnituste salvestamine.

### Etapp 6 — laiendamine

- teised sama kursuse loengud;
- mitme kõnelejaga test;
- kursusepõhine tööde haldus;
- vajaduse korral püsifailide välise salvestuse eraldi arhitektuuriotsus;
- alles vajaduse korral püsiv API, autentimine ja andmebaas.

## 17. Avatud tehnilised otsused

Enne teostuse lukustamist vajavad mõõtmist või kinnitamist:

1. `whisper.cpp` versus `faster-whisper` TalTechi mudeliga ARM64 CPU-l;
2. ASR-i optimaalne kvantimine ja lõigu pikkus;
3. automaatse diariseerimisvajaduse tuvastamise reegel;
4. Echo360 slaidide täpse ajastuse allikas;
5. sobiv 3–8B lokaalne eestikeelset sünteesi tegev mudel;
6. kas eraldi aeglane 14B redigeerimiskäik annab piisava kvaliteedivõidu;
7. PDF-i genereerimise tööriist ARM64 serveril;
8. `err_video_to_text` koodi taaskasutamise täpne moodulipiir;
9. interaktiivse pleieri kasutatav meediaallikas ja sessiooni uuendamise loogika;
10. numbrilised vastuvõtuläved;
11. rakenduse komponentide lõplik jaotus ühe või mitme konteineri vahel;
12. millises arendusetapis, kui üldse, muutub püsiv Oracle’i schema vajalikuks;
13. rakenduse täpne hostinimi või alamdomeen `fun-o.eu` all ning selle TLS-sertifikaadi katvus.

Neid punkte ei tohi dokumenteerimata oletusega lõplikuks otsuseks muuta.

## 18. Esimene soovitatav teostustöö

Esimene kooditöö peab olema piiratud konteineris töötava Echo360 importeri spike’iga. See ei tohi veel koostada ASR-i kontrollandmestikku ega ehitada tervet veebiliidest või kogu konspektigeneraatorit.

Spike’i tulemuseks peab olema:

- korratav `/public` sessiooni loomine;
- kursuse ja loengu masinloetav manifest;
- loengu 3 audio või selle korratavalt hangitav allikakirjeldus;
- slaidimanifest ja slaidipildid;
- ressursi- ning vealogi;
- piisav sisend Etapp 2 kontrollandmestiku kirjeldamiseks ja ASR-i võrdlustesti alustamiseks.
