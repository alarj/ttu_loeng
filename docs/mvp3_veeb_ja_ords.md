# MVP3 veebirakenduse ja ORDS-i integratsioonileping

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja 3.11.2026 kinnitatud MVP3 otsuste, `ttu_loeng` projekti olemasoleva teostuse ning `/home/ubuntu/projektid/jenkins` ORDS API dokumentatsiooni ja koodi põhjal.

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
- Avalik aadress on `https://ttu-loeng.fun-o.eu` ning kasutatakse olemasolevat nginx veebiserverit.
- Nginx, DNS ja TLS kuuluvad MVP3 ulatusse, kuid seadistatakse eraldi hilisemas etapis pärast esimese koodiversiooni valmimist.

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

### 6.4. Korduskatsed

Võrguvea järel korratakse sama töö esitamist sama `idempotency_key` väärtusega. Kasutaja teadlik uus katse loob uue rakenduse toimingu ID ja uue idempotentsusvõtme. Rakendus ei käivita nurjunud tööd automaatselt ORDS-ist mööda minnes.

## 7. Mitme loengu kasutajavoog

1. Kasutaja sisestab Echo360 avaliku kogumiku lingi.
2. Rakendus kuvab kogumiku loengud ja nende salvestise oleku.
3. Kasutaja valib ühe või mitu loengut.
4. Kasutaja võib siduda iga valitud loenguga eraldi PPT-, PPTX- või PDF-faili.
5. Rakendus loob iga loengu jaoks eraldi loengutöötluse kirje.
6. Rakendus esitab iga loengu ASR-i töö ORDS-i.
7. Rakendus esitab iga loengu slaiditöö ORDS-i, määrates `previous_job_id` väärtuseks sama loengu ASR-i keskse ID.
8. Worker täidab ainult ORDS-i poolt claim'itud töid.
9. Kasutajaliides kuvab kõiki esitatud loenguid, nende kahte taustatööd ja valmis artefakte.

Mitme loengu korraga esitamine ei tähenda nende paralleelset töötlemist. Tegeliku järjestuse ja korraga ühe aktiivse ressursimahuka töö reegli jõustab ORDS.

## 8. Oleku autoriteet

ORDS-i tööolekud `QUEUED`, `HELD`, `CLAIMED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `INTERRUPTED`, `REMOVED` ja `UNKNOWN` on järjekorra ja täitmise autoriteetne olek.

Rakenduse püsiv olek sisaldab ainult rakenduse ärilisi seoseid, näiteks:

- loengu ja Echo360 kogumiku metaandmed;
- valikulise slaidifaili nimi, kontrollsumma ja turvaline asukoht;
- ASR-i ja slaiditöö toimingute ID-d ning ORDS-i `job_id` väärtused;
- rakendusesisese etapi diagnostika ja veainfo.

Kõik rakenduse skeemi tabelid kasutavad failis [`../db/erd.md`](../db/erd.md) kirjeldatud ühist soft delete'i reeglit. Füüsilist kustutamist ei kasutata ning suletud kirjed ei kuulu tavavoogude tulemustesse.

Rakendus ei vali selle info põhjal järgmist tööd ega säilita oma järjekorranumbrit. Kasutajale kuvatav koondolek tuletatakse ORDS-i autoriteetsest olekust ja fikseeritud kataloogistruktuuri väljundite tegelikust seisust. ASR-i vea korral kuvatakse sõltuv slaiditöö kasutajale blokeerituna, kuid rakendus ei muuda selle järjekorda ega käivita seda.

Loengutöötluse nullable ja unikaalne `public_id` on ainult avaliku read-only transkriptilingi jaoks. `NULL` tähendab, et loengut ei saa avaliku lingiga jagada. Seda UUID-d ei kasutata ORDS-i töö seostamiseks.

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

Avalik aadress on `https://ttu-loeng.fun-o.eu`. FastAPI kuulab konteineri sisevõrgus HTTP-pordil ning TLS lõpetatakse olemasolevas nginx veebiserveris. Nginx pöördproksi, DNS-i ja Let's Encrypti sertifikaadi tegelik seadistus kuulub MVP3 hilisemasse juurutusetappi ning seda ei muudeta enne esimese koodiversiooni valmimist.

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
6. Nginx pöördproksi, DNS-i ja TLS-i seadistus aadressile `ttu-loeng.fun-o.eu`.

## 13. Avatud otsused

- Kasutajaliidese autentimise viis.
- Üleslaaditud slaidifailide säilitusaeg ja kustutamisreegel.
- Kasutajale pakutava allalaadimispaketi kuju.
- ORDS-i blokeeritud sõltuva töö täpne esitus kasutajaliidese tekstides.
