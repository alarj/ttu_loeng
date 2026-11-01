# Tehniline spetsifikatsioon: Echo360 loengu transkriptsioon koos slaididega

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja kinnitatud MVP2 lähteülesande, projekti olemasoleva koodi ja kontrollitud runtime-artefaktide põhjal. Dokument asendab varasema konspektirakenduse tehnilise spetsifikatsiooni; vana versioon säilib Git-ajaloos märgendi `ver0.1` all.

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

## 3. Dokumendi roll

Käesolev dokument kirjeldab faili [`lahteylesanne.md`](lahteylesanne.md) nõuete tehnilist teostust. Slaiditöötluse detailid on failis [`slaiditootlus.md`](slaiditootlus.md).

Dokument kirjeldab olemasolevat teostust ja veel kontrollimist vajavaid MVP2 olukordi. See ei anna luba andmebaasi, ühise nginx-serveri, TLS-i ega kõrvalprojektide muutmiseks; sellised muudatused vajavad eraldi kasutaja kinnitust faili [`agents.md`](agents.md) järgi.

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

1. ASR-i lõpptranskript on alusartefakt: mudelit suunatakse salvestatud hotword-loendiga ning sellest eemaldatakse ainult kokkulepitud eraldiseisvad täitesõnad. Eraldi toortranskripti ei looda.
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
- kokkulepitud eraldiseisvate täitesõnade eemaldamine sõnaajastuste põhjal;
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

ASR-worker hangib audio ajutisse `work/` kataloogi, kirjutab enne mudelitööd olekufaili, edastab mudelile valitud loengu hotword'id ja loob täieliku ajatemplitega transkripti. Sõnaajastuste põhjal eemaldatakse täpselt `noh`, vähemalt kahest `a`-st koosnevad häälitsused ja vähemalt kahest `ä`-st koosnevad häälitsused. Segmendi ajapiire ei muudeta. Audio eemaldatakse `finally`-koristuses nii edu kui vea korral.

### 7.4. `CHECKING_SLIDES`

Slaidi-worker kontrollib Echo slaidikirjeid, video olemasolu ja videopildi sisu. Video sisu esmane kontroll kasutab vaikimisi 20-sekundilise vahega põhikaadreid ja nende väikese halltoonides pildi sõrmejälgi. Slaidide olek salvestatakse ka siis, kui slaide ei leita või tulemus jääb ebaselgeks.

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

- mudel `TalTechNLP/whisper-large-v3-turbo-et-verbatim`;
- lukustatud revisjon `1ae5a487d24116955803df4d9d01df56645eb44f`;
- Faster-Whisper `1.2.1`;
- CTranslate2 `4.8.4`;
- PyAV `18.0.0`;
- CPU `int8` arvutus;
- eesti keel;
- kolm CPU-lõime;
- üks worker;
- segmendi- ja sõnaajastused.

Konfiguratsiooni valiku mõõtmised ja piirangud on failis [`asr_benchmark.md`](asr_benchmark.md). Mudeli väljundit ei nimetata inimese kontrollitud referentstranskriptiks.

Loengu 8.1 põhjal on eraldi kandidaatväljunditena käivitatud ka `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604` ja `TalTechNLP/whisper-large-v3-turbo-et-subs`. Mõlemad tehnilised tööd lõpetasid edukalt, kuid põhikonfiguratsiooni ei muudeta enne kasutaja sisulist lugemiskontrolli. Mudelite revisjonid, kestused ja väljundite asukohad on dokumenteeritud failis [`asr_benchmark.md`](asr_benchmark.md).

Hotword'id loetakse UTF-8 tekstifailist, üks termin või fraas real. Tühjad read, kommentaarid ja tõstutundetult korduvad kirjed jäetakse välja. Faster-Whisper saab ülejäänud kirjed ühe `hotwords` tekstina. Väljund salvestab loendi failinime, kontrollsumma, kirjete arvu ja kirjed. ICM0032 esialgsed loengupõhised loendid asuvad kataloogis [`hotwords/icm0032`](../hotwords/icm0032).

Täitesõnade eemaldamine toimub sama lõpptranskripti loomisel, mitte eraldi toimetamisetapina. Eemaldamine võrdleb tervet sõna pärast ümbritsevate kirjavahemärkide eemaldamist; seetõttu ei eemaldata näiteks sõnu `nohu` ega `äär`. Kui täitesõna oli segmendi alguses, muudetakse järgmise allesjäänud sõna algustäht suureks. Kui segment sisaldas ainult eemaldatavaid täitesõnu, jäetakse tühi segment väljundist välja.

## 9. Slaiditöötlus

Slaiditöötlus kasutab FFmpegi, Tesseracti, PyMuPDF-i, LibreOffice'i käsureaversiooni, Pillow'd ja Pythoni reeglipõhist loogikat. Üldotstarbelist keelemudelit ei kasutata.

Pealkiri on slaidi peamine, kuid mitte ainus tunnus. Pildisarnasus ja slaidide järjekord väldivad sama pealkirjaga erinevate slaidide ühendamist. Animatsiooni vaheetappe ei nummerdata eraldi slaidideks.

Põhivideo kontroll ei käivita igal kaadril OCR-i. Vaikimisi võrreldakse 20-sekundilise vahega põhikaadrite 32 × 18 halltoonides sõrmejälgi. Muutunud põhivahemiku sees kasutatakse vaikimisi kahe-sekundilist täpsustussammu. OCR piirdub esmalt leitud stabiilse slaidikandidaadi ülemise pealkirjaalaga; kogu slaidi OCR on varuvariant ebaselge vastavuse korral.

Kõik detailid, terminid, olekud, vastavuse kontroll ja testjuhtumid on failis [`slaiditootlus.md`](slaiditootlus.md).

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

MVP2 ei vaja andmebaasi. Kui püsiv andmebaas osutub hiljem vajalikuks, kasutatakse Oracle Always Free andmebaasi ning projektile eraldatud oma schemat. Ristkasutus teise projekti schemaga vajab eraldi põhjendust ja dokumentatsiooni mõlemas projektis.

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
8. võimalik veebiliidese hostinimi ja selle TLS-sertifikaadi katvus.

Neid otsuseid ei tehta dokumenteerimata oletuse ega ühe näite põhjal.
