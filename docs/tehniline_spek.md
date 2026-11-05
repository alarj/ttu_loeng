# Tehniline spetsifikatsioon: Echo360 loengu transkriptsioon koos slaididega

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja kinnitatud MVP2 lähteülesande, projekti olemasoleva koodi, kontrollitud runtime-artefaktide ja 3.–4.11.2026 kinnitatud MVP3 arhitektuuri- ning ligipääsuotsuste põhjal. Dokument asendab varasema konspektirakenduse tehnilise spetsifikatsiooni; vana versioon säilib Git-ajaloos märgendi `ver0.1` all ja MVP2 seis märgendi `ver0.2` all.

## 2. Sisukord

- [3. Dokumendi roll](#3-dokumendi-roll)
- [4. Kontrollitud lähteolukord](#4-kontrollitud-lähteolukord)
- [5. Arhitektuuri põhimõtted](#5-arhitektuuri-põhimõtted)
- [6. Komponendid](#6-komponendid)
- [7. Töövoog](#7-töövoog)
- [8. Kõnetuvastus](#8-kõnetuvastus)
- [9. Slaiditöötlus](#9-slaiditöötlus)
- [10. Transkripti ja slaidide ühendamine](#10-transkripti-ja-slaidide-ühendamine)
- [11. Artefaktid ja kataloogistruktuur](#11-artefaktid-ja-kataloogistruktuur)
- [12. Töö olek ja korduvkasutus](#12-töö-olek-ja-korduvkasutus)
- [13. Konteinerid ja ressursikasutus](#13-konteinerid-ja-ressursikasutus)
- [14. Vead ja taastamine](#14-vead-ja-taastamine)
- [15. Turvalisus ja andmete elutsükkel](#15-turvalisus-ja-andmete-elutsükkel)
- [16. Testimine](#16-testimine)
- [17. Teostusetapid](#17-teostusetapid)
- [18. Avatud tehnilised otsused](#18-avatud-tehnilised-otsused)
- [19. MVP3 veebirakendus ja keskne tööjärjekord](#19-mvp3-veebirakendus-ja-keskne-tööjärjekord)

## 3. Dokumendi roll

Käesolev dokument kirjeldab faili [`lahteylesanne.md`](lahteylesanne.md) nõuete tehnilist teostust. Slaiditöötluse detailid on failis [`slaiditootlus.md`](slaiditootlus.md) ning MVP3 veebirakenduse ja ORDS-i täpne leping failis [`mvp3_veeb_ja_ords.md`](mvp3_veeb_ja_ords.md).

Dokument kirjeldab olemasolevat MVP2 teostust ja MVP3 kinnitatud arhitektuuri. DNS-kirje, nginxi HTTP→HTTPS suunamine, `ttu-loeng.fun-o.eu` nime sisaldav ühine TLS-sertifikaat ja HTTPS-pöördproksi töötavale veebikonteinerile on seadistatud. Dokument ei anna luba andmebaasi ega kõrvalprojektide andmete muutmiseks; sellised muudatused vajavad eraldi kasutaja kinnitust faili [`agents.md`](agents.md) järgi.

## 4. Kontrollitud lähteolukord

### 4.1. Server

- Ubuntu Linux ARM64;
- neli CPU-tuuma;
- 23 GiB mälu;
- GPU puudub;
- rakendus jagab serverit teiste projektidega;
- runtime asub hostis `/srv/ttu-loeng` ja konteineris `/runtime`.

Mälu on kontrollitud ASR-i ja slaiditöötluse jaoks piisav. CPU-töö tuleb järjestada, et serveri teised teenused jääksid kasutatavaks.

### 4.2. Echo360

Olemasolev importer suudab:

- luua avaliku `/public` lingi kaudu külalissessiooni;
- lahendada kanoonilise sektsiooni;
- lugeda loengute nimekirja;
- säilitada Echo ajatuse lipud ning tegelikest meediakirjetest tuletatud salvestise oleku eraldi;
- leida loengu audio- ja videoallikad;
- salvestada allikakirjelduse ilma sessiooniküpsiste väärtuste ja signeeritud URL-i päringuosadeta.

### 4.3. Kõnetuvastus

TalTechNLP täistranskriptsiooni töövoog on teostatud ja kontrollitud. ICM0032 kontroll-loengu tegelik tulemus:

- audio kestus 2 tundi ja 15 minutit;
- töö kestus 1 tund ja 40 minutit;
- 447 segmenti;
- 15 064 sõna;
- segmendi- ja sõnataseme ajad;
- ajutine 113 081 307-baidine MP3 eemaldati pärast töö lõppu.

### 4.4. Slaidid

Olemasolev slaiditöötluse alus suudab:

- valida Echo esitluse videoallika;
- laadida video ajutiselt alla;
- võtta FFmpegiga ajastatud kaadreid;
- käivitada Tesseracti eesti ja inglise OCR-i;
- salvestada kaadrid, ajamärgid, kontrollsummad ja OCR-teksti;
- eemaldada ajutise video;
- lugeda PDF-i tekstikihti PyMuPDF-iga.

MVP2 tööharus on teostatud pildimuutuste põhine slaidikandidaatide leidmine, animatsioonide koondamine, PPT/PPTX teisendamine, PDF-i renderdamine, staatiliste slaidide videoga sobitamine ning transkriptiga ühendatud väljund. Esimene `video-slides-v1` kontroll moodustas loengu 8.1 viie tegeliku slaidi asemel kuus, sest tiitelslaid jäi sidumata ja ülemineku- ning animatsioonivaheolek loeti eraldi slaidiks. Parandatud `video-slides-v2` kasutas 44 põhikaadrit, analüüsis pärast muutunud vahemike täpsustamist 89 erineva ajamärgiga kaadrit, moodustas viis slaidi ja sidus kõik viis PPTX-ist loodud PDF-i vastava leheküljega. Ajutine video ja kaadrid eemaldati töö lõpus.

## 5. Arhitektuuri põhimõtted

1. ASR-i lõpptranskript on alusartefakt: katsekonfiguratsioonis võib mudelit suunata salvestatud hotword-loendiga, kuid mudeli loodud teksti järelprotsessis ei muudeta.
2. Slaiditöötlus on ASR-ist eraldi korratav etapp.
3. Slaidide ajastus tuleb videost.
4. Kasutaja slaidifaili kasutatakse ainult pärast videoga vastavuse kontrollimist.
5. Slaidiviite tõttu ei lõhuta transkriptsioonisegmenti.
6. Ebaselget automaatset vastet ei muudeta oletusega kinnitatuks.
7. Audio ja video on ajutised; transkript, slaidipildid ja manifestid on püsivad.
8. Pikk töö käivitatakse asünkroonselt kontrollitava oleku ja logiga.
9. Ühe etapi viga ei kustuta varem edukalt valminud etapi väljundit.
10. Üldotstarbelist või teksti genereerivat keelemudelit põhivoos ei kasutata.

## 6. Komponendid

```text
CLI / hilisem veebiliides
          ↓
 Echo360 resolver ja importer
          ↓
 loengu ning meedia valimine
       ↙             ↘
 ASR-worker       slaidi-worker
       ↓             ↓
 ajatemplitega    slaidid ja
 transkript       ilmumisajad
       ↘             ↙
   väljundi koostaja
          ↓
 Markdown + slaidipildid
```

### 6.1. Echo360 resolver ja importer

Vastutus:

- avaliku külalissessiooni loomine;
- kursuse ja loengute nimekiri;
- salvestise tegeliku olemasolu määramine;
- audio- ja videoallikate leidmine;
- eraldi Echo slide deck'i olemasolu kirjeldamine;
- saladusteta manifestid.

### 6.2. ASR-worker

Vastutus:

- audio ajutine hankimine;
- TalTechNLP mudeli laadimine;
- loengupõhise hotword-loendi laadimine ja Faster-Whisperile edastamine;
- kogu loengu transkribeerimine;
- segmendi- ja sõnaajastuste salvestamine;
- Markdown-vaate loomine;
- ressursi- ja tööoleku salvestamine;
- ajutise audio eemaldamine.

### 6.3. Slaidi-worker

Vastutus:

- slaidide olemasolu kontroll;
- video ajutine hankimine;
- slaidivahetuste kandidaatide leidmine;
- OCR ja pildisarnasuse arvutamine;
- animatsiooniseisude koondamine;
- PPT/PPTX teisendamine PDF-iks;
- PDF-slaidide renderdamine;
- video ja staatiliste slaidide vastavuse kontroll;
- slaidipiltide ning manifesti salvestamine;
- ajutise video ja teisendusfailide eemaldamine.

### 6.4. Väljundi koostaja

Vastutus:

- valmis ASR-segmentide lugemine neid slaiditöötluses muutmata;
- slaidide ilmumisaegade lugemine;
- slaidiviidete paigutamine lähima segmendipiiri juurde;
- suhteliste pilditeedega ühe Markdown-faili loomine;
- ühendatud väljundi kontrollimine.

## 7. Töövoog

### 7.1. `RESOLVING`

Sisend on Echo360 avalik `/public` loengukogumiku link. Väljund sisaldab kogumiku identifikaatoreid, nime, loenguid ja nende algseid olekuandmeid.

### 7.2. `SELECTING_LECTURE`

Kasutaja valib loengu. Rakendus kontrollib tegelikke meediakirjeid ning eristab vähemalt olekuid `available`, `processing`, `failed` ja `not_available`.

### 7.3. `TRANSCRIBING`

ASR-worker hangib audio ajutisse `work/` kataloogi, kirjutab enne mudelitööd olekufaili, edastab katsekonfiguratsioonis mudelile valitud loengu hotword'id ja loob täieliku ajatemplitega transkripti. Mudeli loodud teksti ega segmendi ajapiire järelprotsessis ei muudeta. Audio eemaldatakse `finally`-koristuses nii edu kui vea korral.

### 7.4. `CHECKING_SLIDES`

Slaidi-worker kontrollib Echo slaidikirjeid, video olemasolu ja videopildi sisu. Video sisu esmane kontroll kasutab vaikimisi 20-sekundilise vahega põhikaadreid ja nende väikese RGB-pildi sõrmejälgi. Slaidide olek salvestatakse ka siis, kui slaide ei leita või tulemus jääb ebaselgeks.

### 7.5. `EXTRACTING_SLIDES`

Kui kahe järjestikuse 20-sekundilise põhikaadri sõrmejäljed erinevad, analüüsitakse ainult nendevahelist vahemikku kahe-sekundilise sammuga. Esimene stabiilne uue slaidi kaader annab ligikaudse vahetusaja. Alles leitud slaidikandidaadil tuvastatakse pealkiri ning sama slaidi animatsiooniseisud koondatakse. Detailne algoritm ja olekud on failis [`slaiditootlus.md`](slaiditootlus.md).

### 7.6. `PROCESSING_USER_SLIDES`

Valikulise PPT/PPTX-faili korral luuakse LibreOffice'iga ajutine PDF. PDF-i leheküljed renderdatakse staatilisteks slaidipiltideks ning nende tekst loetakse tekstikihist või OCR-iga.

### 7.7. `MATCHING_SLIDES`

Video ja staatiliste slaidide vastavust kontrollitakse pealkirja, muu teksti, pildisarnasuse ja järjekorra järgi. Ajastus tuleb videost. Ebaselge vaste jääb inimese kontrolli vajavaks.

### 7.8. `MERGING_OUTPUT`

Slaidiviited lisatakse olemasolevate transkriptsioonisegmentide vahele. Algne tekst ja ajastus ei muutu. Valmib inimesele loetav Markdown koos suhteliste slaidipiltide viidetega.

## 8. Kõnetuvastus

Põhikonfiguratsioon:

- mudel `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604`;
- lukustatud revisjon `310c550922fc1d1bebf3fad41f9b33ede6652bdc`;
- mudelirepo `ct2` alamkataloog;
- Faster-Whisper `1.2.1`;
- CTranslate2 `4.8.4`;
- PyAV `18.0.0`;
- CPU `int8` arvutus;
- eesti keel;
- kolm CPU-lõime;
- üks worker;
- segmendi- ja sõnaajastused.

Konfiguratsiooni valiku mõõtmised ja piirangud on failis [`asr_benchmark.md`](asr_benchmark.md). Mudeli väljundit ei nimetata inimese kontrollitud referentstranskriptiks.

Loengu 8.1 variantide kasutaja sisulise lugemiskontrolli põhjal annab hotword'ideta `verbatim-2604` katsetatud lokaalsetest mudelitest parima tulemuse. `subs` variant oli liiga lakooniline ning hotword'idega variandid ei parandanud termineid usaldusväärselt. Mudelite revisjonid, kestused, väljundite asukohad ja Gemini sisuvõrdlus on dokumenteeritud failis [`asr_benchmark.md`](asr_benchmark.md).

Hotword'ide tugi säilib kontrollkatsete kordamiseks, kuid põhikonfiguratsioon hotword'e ei kasuta. ICM0032 katsefailid asuvad kataloogis [`hotwords/icm0032`](../hotwords/icm0032). 25 terminiga katse halvendas teksti ning ühe `COBIT` hotword'iga katse ei tuvastanud `COBIT`-it õigesti kordagi.

Mehaanilise täitesõnade järelpuhastuse katse eemaldas küll üksikuid sõnu, kuid ei toimetanud ümbritsevat lauseehitust ega kirjavahemärgistust. Kasutaja võrdluses jäi tekst kohati poolikuks ja muutus halvemini arusaadavaks. Seetõttu on see lahendus tagasi lükatud ja aktiivsest töötlusahelast eemaldatud; katse väljund säilib võrdlusmaterjalina.

`Gemini 3.5 Flash-Lite` abil samast loengust loodud transkript säilitas erialatermineid ja loengu tähendust lokaalsest põhikonfiguratsioonist paremini. Kasutatud juhis ja teenuse täpne konfiguratsioon pole teada ning mitmetunniste loengute järjestikust töötlemist pole projektis kontrollitud. Tasuta kasutuse mahu võimalik piirang on seetõttu avatud praktiline risk, mitte tuvastatud süsteemipiirang.

## 9. Slaiditöötlus

Slaiditöötlus kasutab FFmpegi, Tesseracti, PyMuPDF-i, LibreOffice'i käsureaversiooni, Pillow'd ja Pythoni reeglipõhist loogikat. Üldotstarbelist keelemudelit ei kasutata.

Pealkiri on slaidi peamine, kuid mitte ainus tunnus. Pildisarnasus ja slaidide järjekord väldivad sama pealkirjaga erinevate slaidide ühendamist. Animatsiooni vaheetappe ei nummerdata eraldi slaidideks.

Põhivideo kontroll ei käivita igal kaadril OCR-i. Vaikimisi võrreldakse 20-sekundilise vahega põhikaadrite 160 × 90 RGB-sõrmejälgi. Muutunud põhivahemiku sees kasutatakse vaikimisi kahe-sekundilist täpsustussammu. OCR piirdub ilma eraldi slaidifailita leitud stabiilse slaidikandidaadi ülemise pealkirjaalaga. Eraldi slaidifaili olemasolul loetakse stabiilselt videokaadrilt ka kogu nähtav tekst ning võrreldakse seda PDF-i tekstikihiga. Selge tekstikattuvus peab eristuma järgmisest võimalikust vastest; alles seejärel võib kasutada PDF-i lehekülge ja selle pealkirja. Kontrollimata video-OCR-i teksti transkripti slaidipealkirjana ei väljastata.

Kõik detailid, terminid, olekud, vastavuse kontroll ja testjuhtumid on failis [`slaiditootlus.md`](slaiditootlus.md).

Slaidimuutuse vaikimisi lävend peab tulema `.env`-ist, mitte lähtekoodi konstandist. Selle konfiguratsioonivõtme nimi on `SLIDE_CHANGE_DISTANCE` ja kinnitatud vaikeväärtus on `0.020`. Uuesti sidumise kasutajavalik on täisarvuline tundlikkusaste `−3…+3`; aste `0` kasutab vaikeväärtust, iga positiivne aste vähendab tegelikku lävendit `0.003` võrra ning iga negatiivne aste suurendab seda `0.003` võrra. Seega on tegelikud väärtused vastavalt `0.029`, `0.026`, `0.023`, `0.020`, `0.017`, `0.014` ja `0.011`. Neid kümnendväärtusi ei näidata kasutajaliideses.

Slaidide uuesti sidumine on uus sama loengutöötluse `slides`-toiming, mis sõltub olemasolevast edukast ASR-i toimingust ega loo uut ASR-i toimingut. Toiming peab säilitama kasutaja valitud tundlikkusastme, tegeliku lävendi ning kasutatud konfiguratsiooni manifestis. Igal toimingul on oma väljundkataloog ja ühendatud Markdown; varasemat slaiditulemust ei kirjutata üle.

## 10. Transkripti ja slaidide ühendamine

Ühendaja töötab kahe valmis artefaktiga:

- ajatemplitega transkriptsioonisegmendid;
- slaidide identiteedid ja videost saadud ilmumisajad.

Iga slaidi ilmumisaeg seotakse ajaliselt lähima segmendipiiriga. Segmenti ei jagata isegi siis, kui slaid vahetus segmendi keskel. Slaidiviite väike ajaline erinevus on lubatud, sest väljundi eesmärk on inimesele arusaadav kronoloogiline seos, mitte kaadripõhine sünkroniseerimine.

Algne `transcript.json` ja `transcript.md` jäävad muutmata. Ühendatud väljund kirjutatakse eraldi faili.

## 11. Artefaktid ja kataloogistruktuur

Git-repositoorium sisaldab koodi, konfiguratsiooni, võrguvabu teste ja dokumentatsiooni. Käitusaegsed failid asuvad hostis `/srv/ttu-loeng` ning konteineris `/runtime`.

```text
/srv/ttu-loeng/
├── outputs/
│   ├── resolver.json
│   ├── lessons/<lesson-id>/
│   │   ├── lesson.json
│   │   ├── media.json
│   │   ├── slides.json
│   │   └── run.json
│   └── jobs/<job-id>/
│       ├── run.json
│       ├── transcript/
│       │   ├── run.json
│       │   ├── transcript.json
│       │   └── transcript.md
│       ├── slides/
│       │   ├── run.json
│       │   ├── slides.json
│       │   └── images/
│       └── result/
│           └── transcript_with_slides.md
├── work/<job-id>/
├── models/huggingface/
├── cache/
└── home/
```

Konteinerid kirjutavad hosti mitte-root kasutaja UID/GID-ga. Püsiva väljundi failid kirjutatakse võimaluse korral atomaarse failivahetusega.

## 12. Töö olek ja korduvkasutus

Iga etapp kirjutab vähemalt:

- oleku `running`, `completed` või `failed`;
- algus- ja lõpuaja;
- kestuse;
- sisendite kontrollsummad;
- kasutatud mudeli või tööriistade versioonid;
- veateate ilma saladusteta.

Korduvkasutuse võti sisaldab sisendi kontrollsummat ja tulemust mõjutavat konfiguratsiooni:

- resolver: avalik URL ja resolveri versioon;
- ASR: audio kontrollsumma, mudel, revisjon ja ASR-i seadistus;
- video slaidid: video kontrollsumma ja slaiditöötluse konfiguratsioon;
- staatilised slaidid: sisendfaili kontrollsumma ja teisendustööriista versioon;
- ühendatud väljund: transkripti ja slaidimanifesti kontrollsummad.

Slaiditöötluse või Markdown-vormistuse muutmine ei käivita ASR-i uuesti.

Uuesti sidumine loob sama loengu jaoks järgmise `slides`-toimingu katse. Selle korduvkasutuse võti sisaldab lisaks videole, valikulisele slaidifailile ja slaiditöötluse versioonile ka tundlikkusastet ning sellest tuletatud tegelikku muutuselävendit. Slaiditulemuse väljunditee peab olema seotud toimingu identifikaatori või katse numbriga, mitte ainult loengu identifikaatoriga.

## 13. Konteinerid ja ressursikasutus

MVP2 kasutab vähemalt järgmisi rolle:

- `importer` — Echo360 resolver ja meediaimport;
- `asr` — TalTechNLP kõnetuvastus;
- `slides` — video, OCR, PDF ja PowerPointi slaiditöötlus.

Rollid võivad hiljem tehniliselt jaguneda teisiti, kuid konteinerite arv ei ole funktsionaalne nõue.

Ressursireeglid:

- vaikimisi töötab üks CPU-raske etapp korraga;
- ASR kasutab praeguse kontrollitud konfiguratsiooni järgi kolme CPU-lõime;
- slaiditöötlus ei käivita ASR-i mudelit;
- internetist hangitav audio ja video eemaldatakse pärast etappi;
- pika töö protsess ei sõltu vestlusakna ega terminaliseansi elus püsimisest.

## 14. Vead ja taastamine

Rakendus eristab vähemalt järgmisi vigu:

- vigane avalik link;
- avaliku külalissessiooni loomise viga;
- kogumikku või loengut ei leitud;
- valitud loengul puudub kasutatav salvestis;
- audio või video allalaadimine nurjus;
- kõnetuvastus nurjus;
- slaidide olemasolu jäi ebaselgeks;
- videos ei tuvastatud slaide;
- PPT/PPTX teisendamine nurjus;
- PDF-i lugemine nurjus;
- eraldi slaidid ei vasta videole;
- ühendatud Markdowni loomine nurjus.

Slaidide puudumine või slaiditöötluse viga ei muuda edukat transkriptsiooni nurjunuks. Sellisel juhul säilib transkript ning slaiditöötluse olek märgitakse eraldi.

## 15. Turvalisus ja andmete elutsükkel

- Töödeldakse ainult avaliku Echo360 lingi kaudu kättesaadavaid või kasutaja antud faile.
- Resolver ei proovi autentimispiiranguid mööda minna.
- Sessiooniküpsised püsivad ainult protsessi mälus.
- Signeeritud meedia-URL-i päringuosi ei kirjutata väljundisse.
- Hugging Face'i võimalikud ligipääsutokenid tulevad välisest konfiguratsioonist ja neid ei logita.
- Kasutaja PPT-, PPTX- ja PDF-failide kontrollsummad salvestatakse, kuid algfaile ei muudeta.
- Audio, video ja ajutine teisendatud PDF asuvad `work/` kataloogis ning eemaldatakse pärast etappi.
- Slaidipildid ja transkript säilivad püsiva väljundina.
- Enne veebiliidese avaldamist tuleb eraldi hinnata loengumaterjalide säilitamise ja jagamise õigusi.

MVP2 töötlusmootor ei vaja andmebaasi. MVP3 veebirakendus kasutab Oracle Always Free andmebaasis projektile eraldatud oma skeemi loengutöötluste, ORDS-i tööseoste ja üleslaadimiste hoidmiseks. FastAPI ja worker ühenduvad sama rakenduse skeemiga otse `python-oracledb` ühenduste pooli kaudu; ORDS-i HTTP API-d kasutatakse ainult serveriülese tööjärjekorra jaoks. Mahukad failid jäävad fikseeritud kataloogistruktuuriga failisüsteemi ja neid kirjeldavad olemasolevad manifestid. Andmemudel on failis [`../db/erd.md`](../db/erd.md).

## 16. Testimine

### 16.1. Võrguvabad testid

- Echo ajatuse ja salvestise oleku loogika;
- runtime-failiteede kontroll;
- transkripti ajatemplite vormistus;
- ASR-i kvaliteedimõõdikud ainult inimese referentsi olemasolul;
- videoallika valik;
- slaidi pealkirja normaliseerimine;
- pildisarnasuse arvutamine;
- animatsiooniseisude koondamine;
- staatiliste ja video slaidide vastavuse olekud;
- slaidiviite paigutamine lähima segmendipiiri juurde;
- ajutiste failide koristamine.

### 16.2. Integratsioonitestid

- avalik link → loengute nimekiri;
- loeng → audio ja videoallikad;
- audio → täielik ajatemplitega transkript;
- video → slaidide olemasolu olek;
- video → slaidid ja ilmumisajad;
- PPT/PPTX → PDF → staatilised slaidid;
- staatilised slaidid + video → vastavused;
- transkript + slaidid → ühendatud Markdown.

Live-Echo360 katsed hoitakse võrguvabadest testidest eraldi.

## 17. Teostusetapid

### Etapp 1 — MVP1 tulemuse kinnistamine

- Echo360 resolver;
- salvestise oleku tuvastamine;
- TalTechNLP täistranskript;
- ajutise audio eemaldamine;
- töö olek ja auditandmed.

Seis: teostatud ja kontrollitud.

### Etapp 2 — slaidide olemasolu kontroll

- Echo eraldi slaidimaterjali kontroll;
- videovoo olemasolu kontroll;
- video sisu proovikaadrid;
- olekud slaidide olemasolu, puudumise või ebaselguse kohta.

### Etapp 3 — videost slaidide tuvastamine

- 20-sekundilise vahega põhikaadrid ja slaidide olemasolu kontroll;
- põhikaadrite pildisõrmejälgede võrdlus;
- ainult muutunud 20-sekundiliste vahemike kahe-sekundiline täpsustus;
- pealkirja OCR;
- pildisarnasus;
- animatsiooniseisude koondamine;
- slaidide järjekord ja ilmumisajad.

### Etapp 4 — kasutaja slaidifail

- PPT/PPTX teisendamine PDF-iks;
- PDF-lehekülgede renderdamine;
- teksti eraldamine;
- video ja staatiliste slaidide vastavuse kontroll.

### Etapp 5 — ühendatud väljund

- slaidiviited segmendipiiridel;
- suhtelised pilditeed;
- inimesele loetav Markdown;
- inimese pisteline kontroll.

Etapid 2–5 on loengu 8.1 ja kasutaja antud PPTX-faili põhjal tervikahelana teostatud. Enne lahenduse üldiseks sobivaks lugemist tuleb seda kontrollida ka pikema loengu, eraldi slaidifailita loengu ja teiste failivariantidega.

## 18. Avatud tehnilised otsused

Loengu 8.1 kontroll määras praegused tööväärtused. Enne nende üldiseks sobivaks lugemist tuleb tegelike lisakontrollmaterjalidega hinnata:

1. põhikaadrite ja täpsustuskaadrite pildimuutuse tundlikkus;
2. pealkirjade sarnasuse hindamise piir;
3. piltide sarnasuse hindamise piir;
4. sama slaidi animatsiooniseisude koondamise täpsed reeglid;
5. milline videoresolutsioon sobib tuvastuseks ja milline lõpliku pildi allikaks;
6. kuidas märgitakse osaliselt kattuv või erineva versiooniga slaidifail;
7. MVP2 käsurea lõplik leping;
8. järgmises etapis lisatava masinliidese autentimise viis.

Neid otsuseid ei tehta dokumenteerimata oletuse ega ühe näite põhjal.

## 19. MVP3 veebirakendus ja keskne tööjärjekord

MVP3 lisab vähemalt kaks püsivat konteinerit: FastAPI veebiteenuse ja ühe püsiva workeri. Worker sisaldab nii ASR-i kui ka slaiditöötluse registreeritud adapterit ning kasutab hosti püsivaid runtime- ja mudelivahemälu volume'eid. Ühegi töö jaoks ei ehitata uut image'it ega käivitata uut töötluskonteinerit.

Ressursimahukad tööliigid on ORDS-is `application_code=ttu_loeng` all `asr` ja `slides`. Sama loengu slaiditöö `previous_job_id` viitab selle loengu ASR-i ORDS-i `job_id` väärtusele. ORDS on ainus järjekorra ja käivitamisloa autoriteet; rakendus ei pea kohalikku järjekorda. Rakenduse püsiv olek seob loengu, kasutaja slaidifaili ja ORDS-i tööde ID-d, kuid seda ei kasutata järgmise töö valimiseks.

Eduka ASR-i järel võib administraator luua täiendava `slides`-toimingu. See kasutab sama ASR-i `previous_job_id` väärtust nagu esimene slaiditöö, kuid on uus ORDS-i töö ja uus rakenduse toiming. Toimingu sisendina säilitatakse tundlikkusaste `−3…+3`; worker tuletab sellest `.env`-i `SLIDE_CHANGE_DISTANCE` väärtuse suhtes tegeliku lävendi. Loengu detailvaade näitab iga edukat slaiditulemust eraldi versioonina.

ORDS-i järjekorra API autentimine kasutab OAuth `client_credentials` voogu. `ttu_loeng` rakendusel on oma OAuth-klient; kliendi ID ja saladus tulevad `.env` failist ning access tokenit hoitakse ainult mälus. Kõik järjekorra API kutsed kasutavad Bearer-tokenit.

Kasutaja saab korraga valida mitu loengut ja siduda iga loenguga oma valikulise slaidifaili. Veebiliides kuvab iga loengu ASR-i, sõltuva slaiditöö ja valmis tulemuse. Iga taustatöö olekut näidatakse ühe ORDS-i olekumärgisega; dubleeriva kohaliku tulemuse teksti asemel kuvatakse `BACKGROUND_OPERATIONS.LOCAL_STARTED_AT` ja `LOCAL_COMPLETED_AT`. UTC-ajad edastatakse ISO 8601 kujul brauserile, mis teisendab need oma ajavööndisse ja kuvab 24-tunnisel kujul `dd.mm.yyyy hh:mm:ss`. ORDS-i olek on järjekorra ja täitmise tõeallikas; rakenduse artefaktide olemasolu ja sisemised vead on rakenduse tõeallikas.

Brauserikasutaja autentimine toimub Google Identity Services ID-tokeniga samal põhimõttel nagu serveri `fun-o.eu` ja `haldus` rakendustes. Backend kontrollib tokenit Google'i `tokeninfo` teenuse kaudu, võrdleb `aud` väärtust `GOOGLE_CLIENT_ID` seadistusega ning nõuab kinnitatud e-posti aadressi. Esmakordsel edukal sisselogimisel luuakse `USER` rolliga `APP_USERS` kirje; rakendus ei halda kohalikke paroole. Aegunud või puuduva sessiooniga kaitstud HTML-päring suunatakse avalehe puhtale Google'i sisselogimisvaatele. `USER` näeb ja laadib alla kõigi aktiivsete tööde tulemusi, kuid uusi töid ja avalikke jagamislinke haldab ainult `ADMIN`. Rolli `ADMIN` määramine toimub otse andmebaasis. Avalikku jagamist pakutakse ja `LECTURE_PROCESSINGS.public_id` saab väärtustada alles pärast slaididega ühendatud `slides/transcript_with_slides.md` valmimist. Sisselogitud ja anonüümne allalaadimine väljastavad sama ZIP-paketi ega lange tagasi ASR-i toortranskriptile; anonüümne kasutaja ei näe tööde nimekirja. ZIP luuakse päringu ajal, selle juurkataloogi ja Markdown-faili nimi tuletatakse failisüsteemi jaoks turvaliseks tehtud loengu nimest ning `images/` sisaldab kõiki Markdownis viidatud slaidipilte. Paketti ei säilitata püsiva artefaktina.

Markdown-vaates teisendatakse transkriptsioonisegmentide ajavahemikud videolinkideks. Link juhib ühe modali ülaosas paikneva HTML5-videopleieri vastava segmendi algusajale; segmendi lõppaeg ei peata videot. Videoallikaks valitakse Echo360 väikseim esitusvariant. Kuna Echo meediaallikas nõuab avaliku kursusesessiooni küpsist, ei anta meedia URL-i brauserile otse. Autenditud videoendpoint vahendab brauseri ühte baitvahemikku kirjeldava `Range`-päise Echo360-le ja tagastab `206 Partial Content` vastuse voona. Videot ei kirjutata runtime-kataloogi ega puhverdata rakenduses tervikuna.

Loengu detailvaate eraldi videonupp kasutab sama autenditud videoendpoint'i ja avab video oma modalis; sellega ei avata Echo360 kasutajaliidest ega nõuta brauserilt Echo küpsist. Modalis kuvatakse lisaks algne `https://echo360.org.uk/lesson/<lesson-id>/classroom` URL koos selgitusega, et Echo classroom-vaate avamiseks peab brauseris juba olema kehtiv Echo360 sessioon. Videomodali sulgemisel peatatakse esitus ja eemaldatakse pleieri allikas.

Sisselogitud kasutaja avaleht rühmitab loengud `SUBMISSIONS.ECHO_CANONICAL_SECTION_ID` järgi kursusteks. Kursuse kuvatav nimi pärineb `SUBMISSIONS.COURSE_TITLE` väljast ning kursused järjestatakse selle järgi. Valitud kursuse loengud järjestatakse `LECTURE_PROCESSINGS.LECTURE_TITLE` järgi ja kuvatakse kompaktses nimekirjas. Nii loengute nimekirjas kui detailvaates kuvatakse andmebaasikirje lisamisaja asemel Echo360-st saadud tegelik loengu toimumisaeg `LECTURE_PROCESSINGS.LECTURE_START_AT`, et sama pealkirjaga loenguid saaks eristada. Administraator võib detailvaatest soft delete'iga sulgeda konkreetse loengutöötluse alles pärast loengu nime kuvavas modalis `Jah` valimist; see ei sulge kursuse teisi loenguid ega submission'it.

Loengute lisamise leht pakub olemasolevaid aktiivseid kursusi nime järgi ning eraldi välja uue Echo360 `/public` URL-i sisestamiseks. Dropdowni väärtus on kanoonilise sektsiooni ID, mitte URL. Backend leiab valitud kursuse viimase aktiivse submission'i salvestatud URL-i. Mõlemal sisendil on eraldi „Kuva loengud” nupp, mis on aktiivne ainult vastava valiku või sisendi olemasolul.

FastAPI HTML-marsruudid kasutavad eraldi teenusekihti. Järgmise etapi JSON API peab kasutama samu teenuseid, et tööde loomise, õiguste, ORDS-i registreerimise ja tulemuste leidmise reeglid ei dubleeruks. Masinliidese autentimisviis ei kuulu käesolevasse etappi.

ORDS-i claim'i, heartbeat'i ja OAuth-tokeni uuendamise intervallid ning kasutajaliidese olekuvärskendus tulevad `.env` konfiguratsioonist. Vaikeväärtused on vastavalt 300, 300, 60 ja 30 sekundit.

Avalik aadress on `https://ttu-loeng.fun-o.eu`. DNS-kirje, nginxi HTTP→HTTPS suunamine, nime sisaldav ühine TLS-sertifikaat ja HTTPS-pöördproksi `ttu-loeng-web:8000` konteinerile on seadistatud. Täielik leping ja etapistus on failis [`mvp3_veeb_ja_ords.md`](mvp3_veeb_ja_ords.md).
