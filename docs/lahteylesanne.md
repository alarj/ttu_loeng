# Lähteülesanne: loengusalvestisest ainekavapõhise ülikoolikonspekti koostamine

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex), kasutaja kirjeldatud vajaduste, vestluses täpsustatud nõuete ning projekti registreeritud algmaterjalide põhjal.

## 2. Sisukord

- [3. Dokumendi eesmärk](#3-dokumendi-eesmärk)
- [4. Probleem](#4-probleem)
- [5. Eesmärk](#5-eesmärk)
- [6. Esmane kasutusjuht](#6-esmane-kasutusjuht)
- [7. Kasutaja põhivoog](#7-kasutaja-põhivoog)
- [8. Sisendid](#8-sisendid)
- [9. Konspekti sisulised nõuded](#9-konspekti-sisulised-nõuded)
- [10. Slaidide nõuded](#10-slaidide-nõuded)
- [11. Allikad ja jälgitavus](#11-allikad-ja-jälgitavus)
- [12. Kõnelejad ja diariseerimine](#12-kõnelejad-ja-diariseerimine)
- [13. Väljundid](#13-väljundid)
- [14. Inimese ülevaatus](#14-inimese-ülevaatus)
- [15. Mittefunktsionaalsed nõuded](#15-mittefunktsionaalsed-nõuded)
- [16. Esimese MVP ulatus](#16-esimese-mvp-ulatus)
- [17. MVP-st välja jääv](#17-mvp-st-välja-jääv)
- [18. Esimese kontrolljuhtumi vastuvõtukriteeriumid](#18-esimese-kontrolljuhtumi-vastuvõtukriteeriumid)
- [19. Edu mõõtmine](#19-edu-mõõtmine)
- [20. Edasised etapid](#20-edasised-etapid)

## 3. Dokumendi eesmärk

Käesolev dokument kirjeldab rakenduse eesmärki, kasutusjuhtu, sisendeid, väljundeid, sisulisi nõudeid ja vastuvõtukriteeriume. Tehnilised teostusotsused on eraldi dokumendis [`tehniline_spek.md`](tehniline_spek.md).

## 4. Probleem

TalTechi õppeaine ICM0032 „IT valitsemine ja juhtimine“ loengud on Echo360-s salvestatud. Loengud on enamasti pikad ja rahuliku tempoga. Kasutaja lähtehinnangu järgi ei sobi Echo360 automaatne transkriptsioon eestikeelse kõne jaoks ega anna usaldusväärset õppematerjali. 31.10.2026 dünaamilisest Echo transkripti API-st kontrollitud ICM0032 loengu 3 automaattranskript oli valdavalt ingliskeelne ja eestikeelse loengu kohta sisuliselt kasutuskõlbmatu. Ingliskeelse loengu Echo transkriptsiooni kvaliteeti ei ole kontrollitud; see võib olla kasutatav ning käesolev järeldus ei laiene sellele. Kasutaja antud näidistranskriptis nimetatud „videoloengu automaatsubtiitrite“ platvorm ei ole teada ja nende seost Echo360-ga ei eeldata.

Üliõpilasel on vaja loengust iseseisvalt loetavat ülikoolikonspekti, mis:

- ei ole pelgalt kronoloogiline transkriptsiooni kokkuvõte;
- keskendub ainekavas määratud teemadele ja alam-õpiväljunditele;
- toob esile testis või eksamil olulise materjali;
- säilitab õppejõu selgitused, näited, võrdlused ja rõhuasetused;
- sisaldab olulisi slaide või vähemalt viiteid neile;
- võimaldab kontrollida, millisest loengukohast või slaidist väide pärineb.

## 5. Eesmärk

Luua samas Ubuntu serveris töötav rakendus, mis võtab sisendiks Echo360 avaliku kursuse- või loengulingi, ainekava ja loengumaterjalid ning koostab ühe loengu kohta kvaliteetse eestikeelse konspekti.

Konspekt peab olema kasutatav iseseisva õppematerjalina. Allikaviited täiendavad konspekti ja võimaldavad kontrolli, kuid konspekti mõistmine ei tohi eeldada pidevat salvestise või slaidide avamist.

## 6. Esmane kasutusjuht

Esimene kontrolljuhtum on ICM0032 loeng 3 „Talitluspidevuse ja avariitaaste planeerimine“.

Kontrolljuhtumi materjalid:

- Echo360 avalik kursuselink: <https://echo360.org.uk/section/6f6fcb6b-cd42-4328-81db-eb3e30df9151/public>;
- kursuse Echo360 sektsioon pärast külalissessiooni loomist: `fe0e6009-e8d0-4f61-973f-4d231cbd1ff6`;
- laiendatud ainekava [`initial_materials/AINEKAVA 1.237978_Laiendatud ainekava ICM0032 2026-10-09 v9.pdf`](initial_materials/AINEKAVA%201.237978_Laiendatud%20ainekava%20ICM0032%202026-10-09%20v9.pdf);
- näidiskonspekt [`initial_materials/L03_konspekt.docx.pdf`](initial_materials/L03_konspekt.docx.pdf);
- kasutaja antud tõenäoline loengu 3 slaidipakk [`initial_materials/L03_slaidikandidaat.pptx`](initial_materials/L03_slaidikandidaat.pptx), mille täpne päritolu ja vastavus salvestises kasutatud slaididele ei ole teada;
- Echo360 salvestis, slaidid ja muud loengu juures avalikult kättesaadavad materjalid.

Näidiskonspekt on stiili, detailsuse ja katvuse võrdlusmaterjal. Seda ei käsitleta automaatselt faktilise tõeallikana. Slaidikandidaati ei käsitleta originaalslaidide ega videos kasutatud slaidiversiooni tõendina. Selle kasutamine slaidisisu allikana eeldab esmalt võrdlust loengusalvestisega; täpne ajastus tuleb seejärel kontrollida salvestisega joondamise kaudu.

## 7. Kasutaja põhivoog

1. Kasutaja lisab või valib Echo360 avaliku kursuselingi.
2. Rakendus kuvab kursuse loengute nimekirja.
3. Kasutaja valib ühe loengu.
4. Kasutaja lisab või valib kursuse ainekava.
5. Rakendus hangib loengu audio, slaidid ja metaandmed.
6. Rakendus loob eestikeelse ajatemplitega transkriptsiooni.
7. Vajaduse korral eristatakse kõnelejad.
8. Rakendus seob transkriptsiooni, slaidid ja ainekava alam-õpiväljundid.
9. Rakendus koostab konspekti mustandi ning märgib ebakindlad kohad.
10. Kasutaja saab konspekti ja selle allikaid üle vaadata.
11. Rakendus ekspordib kinnitatud konspekti Markdowni ja PDF-i.

## 8. Sisendid

### 8.1. Kohustuslikud sisendid

- Echo360 avalik `/public` juurdepääsulink või juba rakenduses registreeritud kursus;
- kasutaja valitud loeng;
- ainekava PDF või muu tekstina loetav ainekavafail.

### 8.2. Automaatselt hangitavad sisendid

- kursuse ja loengu pealkiri;
- loengu kuupäev ja kestus;
- audio- või videovoog;
- loengu slaidid või esitluse kujutised;
- loengu ja meedia tehnilised identifikaatorid.

Echo360 enda automaattranskriptsiooni rakenduse praegune eestikeelsete loengute töövoog ei hangi ega säilita. Kontrolljuhtumis oli see eestikeelse kõne kohta sisuliselt kasutuskõlbmatu ning selle laadimine ei anna konspekti koostamisele ega kvaliteedikontrollile väärtust. Ingliskeelsete loengute võimalikku teistsugust töövoogu ei ole hinnatud.

### 8.3. Valikulised sisendid

- õppejõu nimi ja kõneleja vihjed;
- terminisõnastik;
- õppejõu lisamaterjalid;
- varasem sama loengu konspekt kvaliteedi võrdlemiseks;
- inimese parandatud transkriptsioonilõigud.

## 9. Konspekti sisulised nõuded

### 9.1. Iseseisev loetavus

Konspekt peab sisaldama kogu teema mõistmiseks vajalikku põhisisu. Slaid või salvestis ei tohi olla kohustuslik puuduva seletuse asendaja.

### 9.2. Teemapõhine ülesehitus

Konspekt ei pea järgima loengu kronoloogilist järjekorda. Sama teema eri aegadel käsitletud osad võib koondada ühe peatüki alla.

Peatükkide järjestus peab lähtuma eelkõige:

1. ainekava alam-õpiväljunditest;
2. mõistete ja seoste loogikast;
3. õppimise seisukohast sobivast järjekorrast;
4. testis või eksamil olulisest fookusest.

Algse loengu kronoloogia peab säilima allikaviidetes.

### 9.3. Ainekavaga sidumine

Rakendus peab:

- eraldama valitud loengule vastavad teemad ja alam-õpiväljundid;
- näitama, millised alam-õpiväljundid on konspektis kaetud;
- tooma välja katmata või ebapiisava allikmaterjaliga punktid;
- eristama põhiloenguid, loengukimbu teste, külalisloenguid ja muud ainekavas kirjeldatud konteksti.

### 9.4. Eksamifookus

Konspekt võib sisaldada plokke „Eksamifookus“, „Peab oskama“ ja „Ei ole vaja pähe õppida“ ainult siis, kui väide tuleneb:

- õppejõu selgest ütlusest loengus;
- ainekava selgest nõudest;
- mõlemast allikast.

Rakendus ei tohi tuletada eksamifookust üksnes teema üldisest olulisusest ega keelemudeli hinnangust.

### 9.5. Õppejõu panus

Konspekt peab võimaluse korral säilitama:

- õppejõu definitsioonid ja terminieelistused;
- rõhutatud seosed ja vastandused;
- praktilised näited ja juhtumid;
- eksamijuhised;
- hoiatavad erandid ja levinud vead;
- olulised küsimused ning vastused.

Kõnekeelne kordus, pausid ja kõrvaline jutt tuleb eemaldada, kui need ei kanna õppesisu.

### 9.6. Mõisted, tabelid ja joonised

Konspekt peab sobivas vormis esitama:

- olulised definitsioonid;
- eesti- ja ingliskeelsed terminipaarid;
- võrdlused;
- protsessid ning loogilised ahelad;
- olulised tabelid;
- eksamil reprodutseeritavad või muul põhjusel kesksed joonised.

Joonist ei tohi tekstiga asendada, kui visuaalne kuju on ise õppesisu osa.

### 9.7. Kordamisküsimused

Konspekti lõpus peavad olema kordamisküsimused. Esimeses versioonis toetatakse vähemalt:

- valikvastustega küsimusi;
- õige vastuse märkimist;
- küsimuse seost ainekava punkti ja konspekti peatükiga.

Küsimuse õige vastus peab olema konspektis selgelt põhjendatav.

## 10. Slaidide nõuded

### 10.1. Slaidi lisamine konspekti

Slaid või selle asjakohane väljalõige lisatakse konspekti pildina, kui:

- slaid sisaldab olulist skeemi või joonist;
- õppejõud ütleb, et joonist peab oskama reprodutseerida;
- tabelit või seost on pildina lihtsam mõista;
- slaid ise on oluline originaalne õppematerjal.

### 10.2. Slaidile viitamine

Kui slaidi pilt pole vajalik, peab konspektis olema võimalik säilitada:

- slaidi number või püsiv identifikaator;
- slaidi pealkiri, kui see on tuvastatav;
- viide loenguosale, kus slaidi selgitatakse;
- võimalusel link rakenduse slaidivaatesse.

### 10.3. Väljajätmine

Korduvad, tehnilised, tühjad või õppesisuta slaidid võib konspektist välja jätta. Väljajätmine ei tohi põhjustada ainekava olulise teema kadumist.

## 11. Allikad ja jälgitavus

### 11.1. Üldpõhimõte

Allikaviide on kontrolli- ja süvenemisvahend. Konspekti põhitekst peab jääma ladusaks ning viiteid ei tohi esitada viisil, mis muudab teksti raskesti loetavaks.

### 11.2. Viite sisu

Olulise väite viide peab võimaluse korral sisaldama:

- loengu identifikaatorit või pealkirja;
- algus- ja lõpuaega;
- kõnelejat;
- slaidi numbrit või identifikaatorit;
- ainekava punkti;
- allika kindlust või ülevaatuse olekut.

Näide:

```text
[L03 01:14:20–01:16:05 · S27 · AK 3.d]
```

### 11.3. Loengulõigu kiire avamine

Rakenduse veebivaates peab viide võimaldama:

- avada õige slaidi;
- kuvada vastav transkriptsioonilõik;
- alustada audio või video esitamist vahetult enne viidatud kohta;
- peatada esituse pärast asjakohast lõiku või lubada kasutajal jätkata.

Eksporditud Markdownis ja PDF-is peab säilima inimloetav ajatempel ka siis, kui interaktiivne rakendus pole kättesaadav.

## 12. Kõnelejad ja diariseerimine

TalTechi loengud on valdavalt ühe õppejõuga. Diariseerimine ei ole seetõttu iga loengu kohustuslik osa.

Rakendus peab toetama vähemalt järgmisi režiime:

- `single-speaker` — vaikimisi ühe õppejõuga loeng;
- `automatic` — süsteem hindab, kas kõnelejaid on rohkem;
- `multi-speaker` — diariseerimine on teadlikult sisse lülitatud.

Mitme kõnelejaga loengus peab olema võimalik eristada vähemalt õppejõu, külalise ja auditooriumi küsimuste lõike. Automaatne isikunime määramine ei tohi olla vaikimisi usaldatud; ebakindel nimi jääb kinnitamata.

Olemasoleva `err_video_to_text` projekti pyannote’i diariseerimise ja tekstisegmentide kõnelejatega sidumise kogemust tuleb analüüsida ning võimaluse korral taaskasutada. `err_video_to_text` kasutab põhitekstina ERR-i VTT-d ega paku TalTechi loengutele vajalikku põhitranskriptsiooni.

## 13. Väljundid

### 13.1. Lõppväljundid

- UTF-8 Markdown-konspekt;
- samast Markdowni sisust genereeritud PDF;
- konspektis kasutatud slaidipildid;
- allikaviited ja interaktiivse vaate lingid.

DOCX ei kuulu väljundvormingute hulka.

### 13.2. Tööartefaktid

Rakendus peab säilitama auditeerimiseks vähemalt:

- resolveri tulemuse;
- loengu metaandmed;
- transkriptsiooni ajatemplitega;
- slaidide metaandmed;
- kõnelejainfo, kui diariseerimist kasutati;
- ainekava struktuuri;
- väidete ja allikate seosed;
- mudelite, tööriistade ja konfiguratsiooni versioonid;
- kvaliteedikontrolli tulemused;
- töö kestused ja vead.

## 14. Inimese ülevaatus

Esimese versiooni eesmärk ei ole kõrvaldada inimese kontrolli. Rakendus peab vähendama kuulamis- ja vormistamistööd ning näitama ülevaatajale eelkõige:

- madala ASR-kindlusega lõigud;
- terminoloogiliselt kahtlased kohad;
- allikata või nõrga allikaga väited;
- võimalikud vastuolud;
- eksamifookuseks märgitud väited;
- ainekava katmata punktid;
- ebaselged kõnelejavahetused.

## 15. Mittefunktsionaalsed nõuded

- Kõik projekti tekstifailid ja väljundid peavad olema UTF-8 kodeeringus.
- Rakendus töötab olemasoleval ARM64 Ubuntu serveril ilma GPU-ta.
- Rakendus peab töötama ühes või mitmes konteineris; ka esialgne CLI-põhine MVP käivitatakse konteineris.
- Projekti avalik domeen kuulub `fun-o.eu` domeeni alla. Täpne hostinimi või alamdomeen kinnitatakse enne veebiliidese avaldamist.
- Veebiserver on kõigile serveri projektidele ühine nginx. Selle praegune konfiguratsioon asub `fun_o` projektis kataloogis `/home/ubuntu/fun_o`; käesolev projekt ei juuruta eraldi avalikku nginx-serverit.
- TLS-sertifikaate haldab Let’s Encrypt. Vajaduse korral lisatakse rakenduse uus alamdomeen olemasoleva sertifikaadihalduse kaudu sertifikaadi katvusse.
- Pikk töötlusaeg on vastuvõetav; prioriteet on kvaliteet ja jälgitavus.
- CPU-rasked etapid peavad olema järjestatavad ja taastatavad.
- Vahetulemusi peab saama taaskasutada ilma kogu loengut uuesti töötlemata.
- Tasulise välise ASR- või LLM-teenuse kasutamine ei ole põhivariant.
- Mudelid ja tööriistad peavad olema versioonitud ning võimalusel avatud litsentsiga.
- Mahukaid audio-, video- ja mudelifaile ei hoita Git-repositooriumis ega andmebaasis.
- Internetist uuesti hangitavad audio- ja videofailid on ajutised tööfailid: need paiknevad välise runtime’i `work/` kataloogis ning eemaldatakse vaikimisi pärast edukat või nurjunud töötlust. Säilitamine on lubatud ainult teadliku veaotsinguvalikuga.
- Saladusi ja ligipääsutokeneid ei salvestata Git-i ega väljunditesse.
- Ühe vea tõttu ei tohi kaduda varem edukalt loodud vaheartefaktid.
- Kui rakendus vajab püsivat andmebaasi, tuleb kasutada samas pilves olemasolevat Oracle Always Free andmebaasi, mida kasutavad ka teised projektid, sealhulgas `err_video_to_text`.
- Igal projektil peab Oracle’i andmebaasis olema oma kasutaja ehk schema.
- Eri projektide schemade ristkasutus ei ole eelistatud. See on lubatud ainult põhjendatud vajaduse korral ning vajadus, ligipääsu ulatus ja vastutus peavad olema enne ristkasutuse rakendamist väga selgelt dokumenteeritud mõlema mõjutatud projekti dokumentatsioonis.

## 16. Esimese MVP ulatus

Esimene MVP on ühe loengu vertikaalne töövoog:

```text
Echo360 avalik kursuselink
→ loengu valimine
→ audio ja slaidide import
→ eestikeelne ASR
→ ainekava ja allikate sidumine
→ konspekti mustand
→ allikakontroll
→ Markdown ja PDF
```

MVP võib olla esialgu CLI-põhine. Täielik veebiliides ei ole tehnilise tuuma valideerimise eeltingimus.

## 17. MVP-st välja jääv

- kõikide õppeainete üldine universaalne tugi;
- reaalajas transkriptsioon;
- mitme loengu paralleeltöötlus;
- automaatne ja eksimatu kõneleja isikutuvastus;
- tasuline pilve-ASR või tasuline LLM API;
- Echo360 automaattranskriptsiooni laadimine, säilitamine või töötlemine praeguses eestikeelsete loengute MVP-s;
- DOCX eksport;
- mahukas RAG või eraldi vektorandmebaas;
- püsifailide viimine Oracle’i enda failisalvestusse, Oracle BLOB-idesse või AWS storage’isse;
- avalik mitmekasutajasüsteem, autentimine ja kvoodid;
- täiesti automaatne avaldamine ilma inimese ülevaatuseta.

## 18. Esimese kontrolljuhtumi vastuvõtukriteeriumid

Loengu 3 katse loetakse sisuliselt edukaks, kui:

1. avalik `/public` link loob kasutatava Echo360 külalissessiooni;
2. rakendus leiab valitud loengu audio ja slaidid;
3. tekib eestikeelne ajatemplitega transkriptsioon;
4. konspekt katab ainekava punktid 3.a–3.e või märgib tõendatult katmata punktid;
5. konspekt on iseseisvalt loetav;
6. oluline eksamijoonis või võtmeslaid on lisatud või selgelt viidatud;
7. eksamifookuse väited on seotud konkreetse tõendiga;
8. olulistel definitsioonidel ja õppejõu rõhutustel on loengu- ning slaidiviited;
9. viitest saab rakenduses kiiresti avada vastava loengulõigu;
10. konspekt sisaldab sisuga kooskõlalisi kordamisküsimusi;
11. Markdown ja PDF sisaldavad sama põhisisu;
12. ebakindlad väited on nähtavalt märgitud, mitte esitatud kindla faktina;
13. tulemus on inimese hinnangul õppimiseks kasutatav ning võrreldav näidiskonspekti detailsuse ja struktuuriga.

## 19. Edu mõõtmine

Lisaks subjektiivsele kasutatavusele hinnatakse vähemalt:

- ASR-i terminite täpsust käsitsi kontrollitud lõikudel;
- ainekava punktide katvust;
- kontrollitud faktiliste vigade arvu;
- põhjendamata eksamiväidete arvu;
- korrektsete slaidi- ja ajaviidete osakaalu;
- inimese parandustöö mahtu;
- etappide tööaega ja maksimaalset mälukasutust.

Numbrilised läved lukustatakse enne kogu loengu võrdlustesti, mitte pärast tulemuse nägemist.

## 20. Edasised etapid

Pärast loengu 3 edukat vertikaalset katset:

1. korrastatakse tööartefaktide ja allikate skeem;
2. lisatakse ülevaatus- ja pleierivaade;
3. testitakse mitme kõnelejaga loengut;
4. töödeldakse teisi sama kursuse loenguid;
5. hinnatakse üldistamist teistele õppeainetele;
6. alles seejärel otsustatakse püsiva teenuse, autentimise ja laiema kursusehalduse vajadus.
