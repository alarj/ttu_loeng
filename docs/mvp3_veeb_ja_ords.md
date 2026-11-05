# MVP3 veebirakenduse ja ORDS-i integratsioonileping

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja 3.–4.11.2026 kinnitatud MVP3 otsuste, `ttu_loeng` projekti olemasoleva teostuse ning `/home/ubuntu/projektid/jenkins` ORDS API dokumentatsiooni ja koodi põhjal.

## 2. Sisukord

- [3. Dokumendi eesmärk](#3-dokumendi-eesmärk)
- [4. Kinnitatud piirid](#4-kinnitatud-piirid)
- [5. Vastutusjaotus](#5-vastutusjaotus)
- [6. ORDS-i tööleping](#6-ords-i-tööleping)
- [7. Mitme loengu kasutajavoog](#7-mitme-loengu-kasutajavoog)
- [8. Oleku autoriteet](#8-oleku-autoriteet)
- [9. Konteinerid ja ressursid](#9-konteinerid-ja-ressursid)
- [10. Veebiliides ja avaldamine](#10-veebiliides-ja-avaldamine)
- [11. ORDS-i registreeringu seis](#11-ords-i-registreeringu-seis)
- [12. MVP3 etapistus](#12-mvp3-etapistus)
- [13. Avatud otsused](#13-avatud-otsused)

## 3. Dokumendi eesmärk

Dokument fikseerib MVP3 veebirakenduse, rakenduse workeri ja serveriülese ORDS-i tööjärjekorra vahelise lepingu. ASR-i ja slaiditöötluse sisuline algoritm jääb failides [`tehniline_spek.md`](tehniline_spek.md), [`asr_benchmark.md`](asr_benchmark.md) ja [`slaiditootlus.md`](slaiditootlus.md) kirjeldatud rakenduse vastutuseks.

Rakenduse Oracle'i püsiv andmemudel on failis [`../db/erd.md`](../db/erd.md). FastAPI ja worker kasutavad rakenduse oma skeemi otse `python-oracledb` ühenduste pooli kaudu; ORDS-i HTTP API jääb ainult serveriülese tööjärjekorra jaoks.

## 4. Kinnitatud piirid

- Rakenduse ORDS-i `application_code` on `ttu_loeng`.
- ORDS-is registreeritavad ressursimahukad tööliigid on `asr` ja `slides`.
- ORDS on ainus tööjärjekorra, tööde järjestuse ja käivitamisloa autoriteet.
- Rakendus ei pea ega tohi pidada paralleelset kohalikku tööjärjekorda.
- ORDS ei käivita ega täida rakenduse protsesse. Rakenduse püsiv worker täidab ORDS-ist claim'itud töö ise.
- ASR-i ja slaiditöötluse tegelik CPU piirang määratakse rakenduse konteinerile. ORDS väldib eri rakenduste ressursimahukate tööde samaaegset käivitamist.
- Kasutaja võib ühe tegevusega esitada mitu loengut ja siduda iga loenguga oma valikulise PPT-, PPTX- või PDF-faili.
- Rakendus töötab konteinerites. Ühegi ASR-i ega slaiditöötluse töö jaoks ei ehitata uut image'it ega looda uut töötluskonteinerit.
- Veebikiht tehakse FastAPI abil.
- Brauserikasutaja autentimine toimub samal Google Identity Services ID-tokeni põhimõttel nagu serveri `fun-o.eu` ja `haldus` rakendustes; kohalikku kasutajanime ega parooli ei ole.
- Esmakordne sisselogimine loob `USER` rolliga kasutaja ning `ADMIN` roll määratakse otse andmebaasis.
- `USER` näeb ja laadib alla kõigi aktiivsete tööde valmis tulemusi; tööde esitamine ja avalike otselinkide haldamine nõuab `ADMIN` rolli.
- Sisselogimata kasutaja saab slaididega ühendatud valmis Markdowni ja selle viidatud slaidipildid ZIP-paketina alla laadida ainult konkreetse väärtustatud `public_id` otselingiga ega näe tööde nimekirja. Avalikku linki saab lubada alles siis, kui `slides/transcript_with_slides.md` on olemas.
- Avalik aadress on `https://ttu-loeng.fun-o.eu` ning kasutatakse olemasolevat nginx veebiserverit.
- DNS-kirje, nginxi HTTP→HTTPS suunamine, `ttu-loeng.fun-o.eu` nime sisaldav ühine TLS-sertifikaat ja HTTPS-pöördproksi konteinerile `ttu-loeng-web:8000` on seadistatud.

## 5. Vastutusjaotus

### 5.1. ORDS

ORDS:

- registreerib rakenduse esitatud töö;
- hoiab serveriülest FIFO-järjekorda;
- kontrollib registreeritud rakendust ja tööliiki;
- arvestab `previous_job_id` sõltuvust;
- annab rakenduse workerile claim'i kaudu käivitamisloa;
- välistab korraga rohkem kui ühe aktiivse ressursimahuka töö;
- talletab keskse oleku, täitmiskatse, heartbeat'id ja lõpptulemuse.

ORDS ei tunne ASR-i või slaiditöötluse sisemisi etappe, ei käivita konteinereid ega halda rakenduse tööartefakte.

### 5.2. FastAPI veebirakendus

Veebirakendus:

- lahendab Echo360 avaliku kogumiku ja kuvab loengud;
- võtab vastu mitme loengu valiku ning loengupõhised slaidifailid;
- loob iga loengu jaoks rakenduse enda töötluskirje ja kaks taustatöö toimingut;
- esitab ASR-i ja slaiditöötluse töö ORDS-i;
- seob slaiditöö ASR-i keskse `job_id` väärtusega;
- kuvab ORDS-ist pärineva järjekorra- ja täitmisoleku ning rakenduse artefaktid;
- ei käivita ressursimahukat tööd veebipäringus ega FastAPI `BackgroundTasks` mehhanismiga.

### 5.3. Rakenduse worker

Püsiv worker:

- kutsub käivitumisel `/worker/startup`;
- küsib jõudeolekus `/worker/claim`;
- valib adapteri ainult `job_type_code` järgi;
- käivitab claim'itud `asr` või `slides` töö enda konteineris;
- saadab `/start` alles pärast tegeliku protsessi edukat käivitamist;
- saadab töö ajal iga viie minuti järel heartbeat'i;
- saadab lõpus `/complete` tulemusega `SUCCEEDED`, `FAILED`, `INTERRUPTED` või `UNKNOWN`;
- ei käivita tööd kohaliku oleku ega kasutajaliidese käsu põhjal ilma ORDS-i claim'ita.

## 6. ORDS-i tööleping

ORDS-i järjekorra API kasutab OAuth `client_credentials` autentimist. `ttu_loeng` kasutab oma OAuth-klienti, mille ID ja saladus tulevad `.env` failist. Token küsitakse `/oauth/token` endpoint'ist, seda hoitakse ainult mälus ning kõik järjekorra API päringud kasutavad Bearer-tokenit. Rakendusepõhised OAuth-kliendid võimaldavad samal kesksel järjekorrahalduril teenindada eri rakendusi eraldi mandaatidega.

### 6.1. Ühised tunnused

- `application_code`: `ttu_loeng`;
- `application_job_id`: `BACKGROUND_OPERATIONS.operation_id` tekstikujul; eraldi veergu selle jaoks ei looda;
- `idempotency_key`: sama toimingu korduses muutumatu võti;
- `parameters.lecture_processing_id`: rakenduse loengutöötluse numbriline primaarvõti.

Rakenduse loengutöötluse ID seob ühe kasutajale kuvatava loengu, selle slaidifaili, ASR-i toimingu ja slaiditöötluse toimingu. `application_job_id` ei ole kohaliku järjekorra tunnus.

### 6.2. ASR

```json
{
  "application_code": "ttu_loeng",
  "job_type_code": "asr",
  "application_job_id": "456",
  "idempotency_key": "ttu_loeng:asr:456",
  "previous_job_id": null,
  "parameters": {
    "lecture_processing_id": 123
  }
}
```

Worker leiab `lecture_processing_id` kaudu rakenduse püsivast olekust Echo360 avaliku lingi, lesson ID, fikseeritud ASR-konfiguratsiooni ja väljundkataloogi. ORDS-i parameetrites ei edastata suvalist shellikäsku ega kasutaja määratud failisüsteemiteed.

### 6.3. Slaiditöötlus

```json
{
  "application_code": "ttu_loeng",
  "job_type_code": "slides",
  "application_job_id": "789",
  "idempotency_key": "ttu_loeng:slides:789",
  "previous_job_id": 123,
  "parameters": {
    "lecture_processing_id": 123
  }
}
```

`previous_job_id` on sama loengu ASR-i ORDS-i `job_id`. ORDS ei paku slaiditööd täitmiseks enne, kui eelnev ASR on olekus `SUCCEEDED`. Kui ASR lõpeb muu lõppolekuga, ei muutu sellest sõltuv slaiditöö claim'itavaks.

Worker kontrollib lisaks enne slaiditöötlust transkripti olemasolu ja sobivust. See on rakenduse sisendi tervikluse kontroll, mitte kohalik järjekorraotsus.

### 6.4. Kordusesitamine ja ajapiir

Loengute valimise vorm sisaldab serveris loodud submission'i päringu UUID-d, mida hoitakse `SUBMISSIONS.PUBLIC_ID` veerus. Sama vormi korduv `POST /submissions` tagastab juba loodud submission'i ega loo uusi loengutöötlusi või ORDS-i töid.

Ühe ORDS-i HTTP-katse ajapiir on `ORDS_REQUEST_TIMEOUT_SECONDS`, vaikimisi 1,5 sekundit. Võrguvea, `429` või ajutise `5xx` vastuse järel tehakse kõige rohkem üks lühikese viivitusega korduskatse sama idempotentsusvõtmega. Vana kolme 30-sekundilise katsega ahelat ei kasutata: aeglane või kättesaamatu ORDS ei tohi hoida brauseri päringut minutiteks avatuna.

Iga ORDS-i HTTP-katse logitakse eraldi. Logikirje sisaldab endpoint'i ilma päringuparameetriteta, HTTP-meetodit, katse numbrit, vastuse staatust või vealiiki, kestust ning korduskatse otsust ja viivitust. Logisse ei kirjutata OAuthi kliendisaladust, access tokenit, `Authorization` päist, päringu keha, `execution_token` väärtust ega ORDS-i vastuse sisu.

## 7. Mitme loengu kasutajavoog

1. Kasutaja valib nime järgi olemasoleva kursuse või sisestab Echo360 avaliku kogumiku lingi. Olemasoleva kursuse valikul kasutab backend selle viimase aktiivse submission'i salvestatud `echo_public_url` väärtust; URL-i dropdownis ei kuvata.
2. Rakendus kuvab kogumiku loengud kompaktses üherealises nimekirjas koos kuupäeva, kellaaja ja salvestise olekuga; valikulise slaidifaili nupp asub rea paremas servas.
3. Kasutaja valib ühe või mitu loengut.
4. Kasutaja võib siduda iga valitud loenguga eraldi PPT-, PPTX- või PDF-faili.
5. Rakendus loob iga loengu jaoks eraldi loengutöötluse kirje.
6. Rakendus esitab iga loengu ASR-i töö ORDS-i.
7. Rakendus esitab iga loengu slaiditöö ORDS-i, määrates `previous_job_id` väärtuseks sama loengu ASR-i keskse ID.
8. Worker täidab ainult ORDS-i poolt claim'itud töid.
9. Kasutajaliides kuvab esmalt `SUBMISSIONS.COURSE_TITLE` järgi järjestatud kursused.
10. Kursuse valimisel kuvab kasutajaliides selle loengud `LECTURE_PROCESSINGS.LECTURE_TITLE` järgi järjestatud kompaktses ja mobiili- ning tahvlivaatele kohanduvas nimekirjas. Sama nimega loengute eristamiseks kuvatakse nime järel `LECTURE_PROCESSINGS.LECTURE_START_AT` kuupäev. Administraator võib konkreetse loengutöötluse detailvaatest sulgeda soft delete'iga. Kustutamisnupp avab esmalt loengu nimega kinnitusmodali ning kustutamise POST-päring võetakse vastu ainult selgesõnalise `Jah` kinnituse järel.
11. Loengu kompaktne ja responsiivne detailvaade kuvab iga taustatöö ühe autoriteetse olekumärgise ning selle kõrval rakenduse tegeliku algus- ja lõpuaja. UTC-väärtused teisendatakse brauseri ajavööndisse ja kuvatakse 24-tunnisel kujul `dd.mm.yyyy hh:mm:ss`; lõpetamata töö lõppaeg jääb tühjaks. Vaates saab avada vormindatud Markdown-transkripti koos suurendatavate slaidipiltidega modalis, laadida tervikliku transkripti ZIP-paketi alla ja avada algse Echo360 loengu uuel vahelehel. Transkriptsioonisegmendi ajavahemik on link: selle vajutamisel kuvatakse modali ülaosas väike videopleier ning Echo360 video käivitub segmendi algusajast. Järgmine ajamärgilink kasutab sama pleierit ja hüppab uuele ajale; pausil, video lõppemisel või modali sulgemisel pleier peidetakse.
12. Brauser küsib videot autentitud rakenduse endpoint'ilt baitvahemikena. Rakendus loob Echo360 avaliku kursusesessiooni, edastab `Range`-päringu Echo videoallikale ja voogedastab vastuse brauserile. Videot ei salvestata kettale ega loeta enne esitamist tervikuna mällu; Echo URL-i ja sessiooniküpsiseid brauserile ei väljastata.
12. Loengute lisamise vorm kuvab submission'i salvestamise ja ORDS-i registreerimise ajal nähtavat laadimisolekut ning väldib korduvat esitamist. Olemasoleva kursuse ja käsitsi sisestatud URL-i kummalgi real on oma nupp, mis aktiveerub alles vastava väärtuse valimisel või sisestamisel.

Mitme loengu korraga esitamine ei tähenda nende paralleelset töötlemist. Tegeliku järjestuse ja korraga ühe aktiivse ressursimahuka töö reegli jõustab ORDS.

## 8. Oleku autoriteet

ORDS-i tööolekud `QUEUED`, `HELD`, `CLAIMED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `INTERRUPTED`, `REMOVED` ja `UNKNOWN` on järjekorra ja täitmise autoriteetne olek.

Rakenduse püsiv olek sisaldab ainult rakenduse ärilisi seoseid, näiteks:

- loengu ja Echo360 kogumiku metaandmed;
- valikulise slaidifaili nimi, kontrollsumma ja turvaline asukoht;
- ASR-i ja slaiditöö toimingute ID-d ning ORDS-i `job_id` väärtused;
- rakendusesisese etapi diagnostika ja veainfo.

Kõik rakenduse skeemi tabelid kasutavad failis [`../db/erd.md`](../db/erd.md) kirjeldatud ühist soft delete'i reeglit. Füüsilist kustutamist ei kasutata ning suletud kirjed ei kuulu tavavoogude tulemustesse. Loengu detailvaate administraatori kinnitatud kustutamistoiming väärtustab ainult valitud `LECTURE_PROCESSINGS` rea `end_date` ja `last_updated`; teisi sama kursuse loenguid ega submission'it ei suleta.

Rakendus ei vali selle info põhjal järgmist tööd ega säilita oma järjekorranumbrit. Kasutajale kuvatav koondolek tuletatakse ORDS-i autoriteetsest olekust ja fikseeritud kataloogistruktuuri väljundite tegelikust seisust. ASR-i vea korral kuvatakse sõltuv slaiditöö kasutajale blokeerituna, kuid rakendus ei muuda selle järjekorda ega käivita seda.

Loengutöötluse nullable ja unikaalne `public_id` on ainult avaliku read-only transkriptilingi jaoks. `NULL` tähendab, et loengut ei saa avaliku lingiga jagada. Teenusekiht lubab `public_id` väärtustada ja anonüümse ZIP-paketi väljastada ainult siis, kui sama loengu `slides/transcript_with_slides.md` on olemas; poolelioleva ASR-i ega üksiku toortranskripti jaoks jagamist ei pakuta. ZIP sisaldab loengu nimega juurkataloogi, sama nimega Markdown-faili ja `images/` kataloogis kõiki Markdownis viidatud slaidipilte. Seda UUID-d ei kasutata ORDS-i töö seostamiseks.

## 9. Konteinerid ja ressursid

MVP3 esimene koodiversioon kasutab vähemalt kaht püsivat teenust:

```text
ttu-loeng-web
└── FastAPI, HTML-kasutajaliides ja kerged Echo360 päringud

ttu-loeng-worker
├── ORDS-i workeri tsükkel
├── ASR-i adapter ja sõltuvused
└── slaiditöötluse adapter ja sõltuvused
```

Worker-image ehitatakse juurutamisel siis, kui muutub kood või sõltuvus. Iga uue töö jaoks kasutatakse juba töötavat worker-konteinerit; uut image'it ega konteinerit ei ehitata ega käivitata. Mudelivahemälu, rakenduse püsiv olek, sisendid ja väljundid asuvad hosti püsivatel volume'itel.

Worker-konteineri CPU piirang on vaikimisi kolm tuuma. ORDS ei reserveeri CPU-tuumi, vaid tagab, et serveri teise liidestatud rakenduse mahukas töö ei ole samal ajal aktiivne.

## 10. Veebiliides ja avaldamine

FastAPI serveerib serveripoolselt renderdatud HTML-kasutajaliidest. Kasutajaliidese tekstid tulevad tõlgetest. Eraldi JavaScripti SPA ei ole kinnitatud nõue.

HTML-marsruudid kasutavad kasutajaliidesest sõltumatut teenusekihti. Järgmises etapis lisatav JSON API kasutab sama teenusekihti loengute esitamiseks, tööde pärimiseks ja tulemuste väljastamiseks; masinliidese autentimisviis otsustatakse selles järgmises etapis.

Brauser laadib Google Identity Services kliendi, saab Google'ilt ID-tokeni ja saadab selle `POST /api/auth/google` endpoint'i. Backend kontrollib tokenit Google'i `tokeninfo` teenuse kaudu, nõuab õiget `aud` väärtust ja kinnitatud e-posti aadressi ning loob seejärel rakenduse oma sessiooni. Aegunud või puuduva sessiooniga kaitstud HTML-lehe päring suunatakse puhtale sisselogimisvaatele. Google Console'i Authorized JavaScript origins loendis peab olema `https://ttu-loeng.fun-o.eu`; Client Secretit, redirect URI-t ega OAuth callback'i ei kasutata. Ühine TLS-sertifikaat ja HTTPS-pöördproksi on seadistatud; terviklikku sisselogimist saab kontrollida brauseris.

Avalik aadress on `https://ttu-loeng.fun-o.eu`. FastAPI kuulab konteineri sisevõrgus HTTP-pordil ning TLS lõpetatakse olemasolevas nginx veebiserveris. DNS-kirje on olemas ning `/home/ubuntu/fun_o/nginx/default.conf` sisaldab eraldiseisvat HTTP-serveriplokki, mis teenindab ACME challenge'it ja suunab muud HTTP-päringud vastavale HTTPS-aadressile. Ühist Let's Encrypti `fun-o.eu` sertifikaati laiendati nii, et see sisaldab ka `octave.fun-o.eu` ja `ttu-loeng.fun-o.eu` nimesid. Certboti taimer kasutab kõigi nimede jaoks püsivat webroot-seadistust ning deploy-hook valideerib ja reload'ib Nginxi pärast edukat uuendamist. Eraldiseisev HTTPS-serveriplokk suunab päringud ühises `funo_net` võrgus töötavale `ttu-loeng-web:8000` konteinerile; Nginx ei piira üleslaadimise mahtu. TTU upstream kasutab Docker DNS-i resolverit `127.0.0.11`, jagatud upstream-tsooni ja `resolve` parameetrit, et Nginx uuendaks veebikonteineri IP-aadressi automaatselt pärast konteineri recreate'i. Uvicorn usaldab selle sisevõrgu pöördproksi päiseid, et HTTPS-päringus genereeritud URL-id jääksid HTTPS-skeemiga.

## 11. ORDS-i registreeringu seis

Kasutaja kinnitas 3.11.2026, et ORDS-i süsteemis on registreeritud:

- rakendus `ttu_loeng`;
- selle aktiivne tööliik `asr`;
- selle aktiivne tööliik `slides`.

Jenkinsi repositooriumi kontrollitud SQL-failides ei ole rakenduste algandmete sisestamise skripti, mistõttu registreeringu tegelik andmemuudatus ei ole selle repositooriumi kaudu korratav. `ttu_loeng` projekt käsitleb kasutaja kinnitatud ORDS-i registreeringut integratsioonitesti välise eeltingimusena ega halda seda oma kohaliku skeemi või järjekorrana.

## 12. MVP3 etapistus

1. ORDS-i kliendi, töölepingu valideerimise ja püsiva workeri teostus.
2. Failis [`../db/erd.md`](../db/erd.md) kirjeldatud loengutöötluste, üleslaadimiste ja toimingute Oracle'i skeem ning migratsioonid.
3. FastAPI veebikiht ja mitme loengu esitamise kasutajaliides.
4. ASR-i ja slaiditöötluse olemasoleva koodi ühendamine workeri adapteritega.
5. Võrguvabad testid, ORDS-i integratsioonitest ja terviklik kontroll mitme loenguga.
6. DNS-kirje, nginxi HTTP→HTTPS suunamine, nime sisaldav TLS-sertifikaat ja HTTPS-pöördproksi on seadistatud ning veebikonteiner töötab.

## 13. Avatud otsused

- Üleslaaditud slaidifailide säilitusaeg ja kustutamisreegel.
- ORDS-i blokeeritud sõltuva töö täpne esitus kasutajaliidese tekstides.
- Järgmise etapi JSON API autentimisviis.
