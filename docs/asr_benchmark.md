# Etapp 2: eestikeelse ASR-i benchmark

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex). Dokument põhineb samas ARM64 serveris käivitatud ASR-mõõtmistel, lukustatud kontrollkomplektil, automaatselt loodud artefaktidel ning kasutaja 1.–2.11.2026 tehtud kõrvutaval lugemiskontrollil. Tekstinäidete võrdlus ei ole inimese koostatud sõna-sõnaline referentstranskriptsioon.

## 2. Sisukord

- [3. Eesmärk ja staatus](#3-eesmärk-ja-staatus)
- [4. Kontrollkomplekt](#4-kontrollkomplekt)
- [5. Võrreldud konfiguratsioonid](#5-võrreldud-konfiguratsioonid)
- [6. Ressursitulemused](#6-ressursitulemused)
- [7. Kvaliteedivaatlus](#7-kvaliteedivaatlus)
- [8. Otsus](#8-otsus)
- [9. Kordamine ja artefaktid](#9-kordamine-ja-artefaktid)
- [10. Järgmine nõutav kontroll](#10-järgmine-nõutav-kontroll)
- [11. Kogu loengu ajastatud transkript](#11-kogu-loengu-ajastatud-transkript)
- [12. Loengu 8.1 mudelivariandid](#12-loengu-81-mudelivariandid)
- [13. Loengu 8.1 Gemini sisuvõrdlus](#13-loengu-81-gemini-sisuvõrdlus)
- [14. Lõplik lokaalse mudeli valik](#14-lõplik-lokaalse-mudeli-valik)

## 3. Eesmärk ja staatus

Etapi eesmärk oli võrrelda vähemalt kaht olemasoleval neljatuumalisel ARM64 serveril töötavat eestikeelse ASR-i konfiguratsiooni ning valida järgmise arenduse tehniline põhikonfiguratsioon.

Tehniline benchmark on valmis. Kvaliteedi otsustusvärav jääb avatuks, sest kontrollkomplekti referentstekst ei ole veel inimese poolt kuulamise põhjal kontrollitud. Ühe mudeli väljundit ei käsitleta teise mudeli faktilise tõena ning WER-i ega CER-i ei esitata enne `human_verified` referentsi olemasolu.

## 4. Kontrollkomplekt

Masinloetav kirjeldus on failis [`benchmarks/datasets/lecture3_v1.json`](../benchmarks/datasets/lecture3_v1.json).

- allikas: ICM0032 loeng 3 „Business Continuity and Disaster Recovery Planning“;
- Echo lesson ID: `a18d8522-4637-4fcf-a62a-60e3b1f2e586`;
- kolm enne tulemuste vaatamist lukustatud viieminutilist lõiku;
- ajavahemikud: `00:04:00–00:09:00`, `01:00:00–01:05:00` ja `01:55:00–02:00:00`;
- heli kogukestus: 900 sekundit;
- lähteaudio SHA-256: `ad86c2611b1fc75a7a10191d7013dcb683c836c474df46e569fd389b4aba61e1`;
- referentsi olek: `locked_pending_human_reference`.

Valitud lõikudes leidus tegeliku väljundi põhjal nii eestikeelset seletust kui ka ingliskeelseid valdkonnatermineid, sealhulgas disaster recovery, business continuity management ja intsidendihaldus. Valikut ei muudetud pärast mudeliväljundite nägemist.

## 5. Võrreldud konfiguratsioonid

Mõlema konfiguratsiooni ühised parameetrid:

- Faster-Whisper `1.2.1`;
- CTranslate2 `4.8.4`;
- PyAV `18.0.0`;
- ARM64 CPU, `int8`, kolm CPU-lõime ja üks worker;
- keel `et`, beam size `5`, sõnaajastused;
- `vad_filter=false`;
- `condition_on_previous_text=false`.

Konfiguratsioon A:

- ID `taltechnlp-turbo-et-int8`;
- mudel [`TalTechNLP/whisper-large-v3-turbo-et-verbatim`](https://huggingface.co/TalTechNLP/whisper-large-v3-turbo-et-verbatim);
- revisjon `1ae5a487d24116955803df4d9d01df56645eb44f`;
- mudelirepo valmis `ct2/` alamkataloog.

Konfiguratsioon B:

- ID `systran-medium-int8`;
- mudel [`Systran/faster-whisper-medium`](https://huggingface.co/Systran/faster-whisper-medium);
- revisjon `08e178d48790749d25932bbc082711ddcfdfbc4f`.

## 6. Ressursitulemused

| Näitaja | TalTechNLP turbo | Systran medium |
|---|---:|---:|
| Heli | 900 s | 900 s |
| Puhas transkriptsiooniaeg | 632,909 s | 779,761 s |
| Kogu jooks | 684,951 s | 824,934 s |
| Reaalaja tegur | 0,7032 | 0,8664 |
| Kiirus võrreldes heliga | 1,42× | 1,15× |
| Maksimaalne RSS | 4 942 408 KiB | 4 452 980 KiB |
| Ligikaudne maksimaalne RSS | 4,71 GiB | 4,25 GiB |

TalTechNLP oli puhta transkriptsiooniaja järgi umbes 18,8% kiirem. Systran kasutas ligikaudu 478 MiB vähem maksimaalset residentset mälu. Mõlemad mahuvad olemasoleva 23 GiB RAM-iga serverisse suure varuga. Seetõttu on mälu selles võrdluses ainult auditeeritav mõõdik, mitte mudelivaliku argument. Raskete tööde järjestamise vajadus tuleneb eelkõige nelja CPU-tuuma jagamisest teiste serveriteenustega.

Reaalaja teguri lineaarne projektsioon kogu 8129,544-sekundilisele loengule on TalTechNLP puhul ligikaudu 95 minutit ja Systrani puhul ligikaudu 117 minutit. See on benchmarkil põhinev hinnang, mitte kogu loengu eraldi mõõtmine.

## 7. Kvaliteedivaatlus

Mõlemad konfiguratsioonid tuvastasid kõigis kolmes lõigus keeleks eesti keele tõenäosusega `1.0`.

AI kvalitatiivsel vaatlusel oli TalTechNLP väljund loetavam ja valdkonnaterminite kuju stabiilsem. Systrani väljundis esines nähtavalt rohkem moonutusi, näiteks „talituspidevus“, „analysi“, „incidentide halldus“ ja „tehnilisilahendusi“. TalTechNLP väljundis olid samades kohtades kujud „talitluspidevus“, „analüüs“, „intsidendihaldus“ ja „tehnilisi lahendusi“ üldiselt paremini säilinud.

See vaatlus ei ole WER ega CER ja ei tõenda, et TalTechNLP iga sõna on õige. Mõlema mudeli tekst sisaldab kõnekeelset kordust, ebatäpseid liitsõnu ning kohti, mis vajavad inimese kontrolli või hilisemat eraldi terminiparanduse kihti.

## 8. Otsus

Esialgse benchmark-etapi tehniliseks põhikonfiguratsiooniks lukustati tingimuslikult `taltechnlp-turbo-et-int8`, sest:

1. see oli samade parameetritega kiirem;
2. AI kvalitatiivne vaatlus näitas paremat eestikeelset loetavust ja valdkonnaterminite kuju;
3. tegemist on TalTechNLP eestikeelsele kõnele kohandatud mudeliga.

„Tingimuslikult“ tähendas, et konfiguratsiooni kasutati ajatemplitega transkripti loomiseks, kuid seda ei nimetatud lõplikult kvaliteedilt kinnitatud põhimudeliks enne edasisi võrdlusi. Loengu 8.1 hilisemate katsete põhjal tehtud ajakohane lokaalse mudeli valik on jaotises 14.

## 9. Kordamine ja artefaktid

Püsivad runtime-artefaktid:

```text
/srv/ttu-loeng/outputs/benchmarks/asr/icm0032-l03-asr-v1/
├── taltechnlp-turbo-et-int8/
│   ├── result.json
│   └── review.md
└── systran-medium-int8/
    ├── result.json
    └── review.md
```

`result.json` sisaldab mudeli ja runtime’i versioone, parameetreid, audio ja kontrollkomplekti kontrollsummasid, lõikude ning sõnade ajastusi, teksti, ressursimõõdikuid ja kvaliteedivärava olekut. `review.md` on inimesele loetav transkriptsioonivaade.

Mudelite vahemälu säilib `/srv/ttu-loeng/models/huggingface/` all. Internetist uuesti hangitav lähteaudio ei kuulu püsivate benchmarki artefaktide hulka.

## 10. Järgmine nõutav kontroll

Kvaliteedivärava sulgemiseks peab inimene:

1. kuulama lukustatud kolm lõiku;
2. parandama referentsteksti kuuldu järgi, kasutamata ühe mudeli väljundit automaatse tõena;
3. märkima vähemalt IT-terminid, nimed, lühendid, eksamifookuse ütlused ja ebaselged kohad;
4. määrama kontrollkomplekti lõikude olekuks `human_verified`;
5. käivitama mõlemad konfiguratsioonid sama kontrollkomplekti vastu uuesti, et arvutada WER, CER ja terminite täpsus.

Alles seejärel saab Etapp 2 kvaliteedi otsustusvärava lõplikult sulgeda.

## 11. Kogu loengu ajastatud transkript

31.10.2026 lisati ASR-workerile käsk `transcribe-full`. Käsk:

1. loob Echo360 avaliku külalissessiooni;
2. kontrollib, et lesson ID kuulub lahendatud kursusele;
3. laadib eraldi MP3-allika ajutiselt `<runtime>/work/transcribe/` alla;
4. kasutab tingimuslikku põhikonfiguratsiooni `taltechnlp-turbo-et-int8`;
5. säilitab JSON-is segmendi- ja sõnataseme ajad ning toor-ASR-i teksti;
6. loob inimesele loetava ajastatud `transcript.md` faili;
7. eemaldab ajutise audio nii edu kui vea korral;
8. kirjutab iseseisva `run.json` oleku, mida saab pika taustatöö ajal kontrollida.

Püsiv väljund:

```text
/srv/ttu-loeng/outputs/jobs/l03/transcript/taltechnlp-turbo-et-int8/
├── run.json
├── transcript.json
└── transcript.md
```

Kogu loengu esimene töö käivitati 31.10.2026 kell 08:47 UTC asünkroonse konteinerina `ttu-loeng-l03-full-asr` ja lõpetas edukalt kell 10:28 UTC. Töö olekut kirjeldab püsiv fail:

```text
/srv/ttu-loeng/outputs/jobs/l03/transcript/taltechnlp-turbo-et-int8/run.json
```

Töö tulemus sisaldab 447 segmenti kogu 8129,492-sekundilise salvestise kohta. Kogukestus oli 6033,696 sekundit, mudeli laadimine 21,947 sekundit, transkribeerimine 6008,997 sekundit ja reaalajakordaja 0,7392. Mudel oli `TalTechNLP/whisper-large-v3-turbo-et-verbatim` revisjoniga `1ae5a487d24116955803df4d9d01df56645eb44f`. `run.json` märgib `temporary_audio_removed: true` ning ajutist 113 081 307-baidist lähte-MP3 faili pärast töö lõppu failisüsteemis ei ole.

Kogu loengu TalTechNLP väljund on MVP2 muutmata ajastatud alusartefakt, mille kaudu saab teksti salvestisega võrrelda ning mille külge lisatakse slaidiviited.

## 12. Loengu 8.1 mudelivariandid

1.11.2026 loodi sama 876,414-sekundilise loengu põhjal kaks uut eraldi transkriptsiooni. Mõlemad kasutavad sama Faster-Whisperi konfiguratsiooni nagu senine variant: CPU `int8`, kolm CPU-lõime, üks worker, eesti keel, beam size `5`, sõnaajastused, `vad_filter=false` ja `condition_on_previous_text=false`.

| Variant | Mudel ja revisjon | Segmente | Kogu töö kestus | Transkribeerimise kestus |
|---|---|---:|---:|---:|
| senine | `TalTechNLP/whisper-large-v3-turbo-et-verbatim` / `1ae5a487d24116955803df4d9d01df56645eb44f` | 58 | 644,050 s | 618,767 s |
| verbatim-2604 | `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604` / `310c550922fc1d1bebf3fad41f9b33ede6652bdc` | 49 | 620,166 s | 590,448 s |
| subs | `TalTechNLP/whisper-large-v3-turbo-et-subs` / `4a64175d3e2d902984f1f50488c101699162ccbb` | 109 | 546,624 s | 516,934 s |
| verbatim-2604 + hotword'id + täitesõnade eemaldamine | `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604` / `310c550922fc1d1bebf3fad41f9b33ede6652bdc` | 51 | 697,475 s | 692,477 s |
| verbatim-2604 + üks `COBIT` hotword | `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604` / `310c550922fc1d1bebf3fad41f9b33ede6652bdc` | 56 | 627,959 s | 622,889 s |

Kõik tabelis esitatud tööd lõpetasid edukalt ja nende ajutine audio eemaldati. `verbatim-2604` ja `subs` transkript seoti sama varem kontrollitud viie slaidi ning samade videost saadud ilmumisaegadega; slaidituvastust uuesti ei käivitatud. Tööde valmimise hetkel ei olnud nende sisulist kvaliteeti hinnatud; hilisema kasutaja lugemiskontrolli järeldus on jaotises 14.

Lisaks valmis 1.11.2026 `verbatim-2604` katsetöö 25 loengupõhise hotword'i ja mehaanilise täitesõnade eemaldamisega. Sõnaajastuste põhjal eemaldati 38 eraldiseisvat `noh`, `aa…` või `ää…` vastet. Kasutaja hilisem kõrvutav lugemiskontroll näitas, et eemaldamine ei toimetanud ümbritsevat lauseehitust ega kirjavahemärgistust: teksti jäid poolikud lausealgused ja kohati halvenes arusaadavus. Lahendus lükati seetõttu tagasi ja eemaldati aktiivsest töötlusahelast. Katseväljund jääb alles ajaloolise võrdlusmaterjalina.

2.11.2026 valmis kontrollkatse, milles `verbatim-2604` sai ainsa hotword'ina sõna `COBIT` ning mehaanilist järelpuhastust ei tehtud. Töö lõpetas edukalt, kuid transkript ei sisaldanud ühtegi täpset `COBIT` vastet; endiselt esinesid kujud `COVID` ja `kovid`. Katse ei lisanud kasutaja sisulise lugemiskontrolli järgi hotword'ideta väljundile väärtust.

Uued püsivad väljundid:

```text
/srv/ttu-loeng/outputs/jobs/l08-1/transcript/
├── taltechnlp-turbo-et-verbatim-2604-int8/
│   ├── run.json
│   ├── transcript.json
│   ├── transcript.md
│   └── transcript_with_slides.md
├── taltechnlp-turbo-et-subs-int8/
    ├── run.json
    ├── transcript.json
    ├── transcript.md
    └── transcript_with_slides.md
├── taltechnlp-turbo-et-verbatim-2604-hotwords-int8/
    ├── run.json
    ├── transcript.json
    ├── transcript.md
    └── transcript_with_slides.md
└── taltechnlp-turbo-et-verbatim-2604-cobit-hotword-int8/
    ├── run.json
    ├── transcript.json
    └── transcript.md
```

## 13. Loengu 8.1 Gemini sisuvõrdlus

Kasutaja lisas sama loengu audiost Gemini abil koostatud transkripti runtime-kataloogi:

```text
/srv/ttu-loeng/outputs/jobs/l08-1/transcript/gemini/transcript.txt
```

Faili SHA-256 on `3d16ba35a3272452bda7b40066d860bc9495340da34c9ebf375b234807d7c1b1`. Kasutaja andmetel koostas transkripti `Gemini 3.5 Flash-Lite`. Fail ei sisalda kasutatud juhist ega teenuse täpset konfiguratsiooni, mistõttu neid ei oletata.

Sisuvõrdluses oli Gemini väljund hotword'ideta `verbatim-2604` väljundist selgelt parem erialaterminite ja loengu tähenduse säilitamisel. Gemini kirjutas `COBIT` õigesti 22 korda; hotword'ideta `verbatim-2604` ei kirjutanud seda õigesti kordagi ning kasutas kujusid `COVID`, `kovid` või jättis mõiste lausest välja. Gemini tundis õigesti ära ka fraasid `Accountability`, `Evaluate, Direct, Monitor`, `Align, Plan, Organize`, `Build, Acquire, Implement`, `Manage Continuity`, `Manage Service Security` ja `Performance Monitoring`, millega lokaalsel mudelil oli korduvalt raskusi.

Gemini väljund ei olnud veatu. Näiteks `Deliver, Service, Support` muutus kujule `deliver, service, port`, `Future Direction` kujule `budget direction`, `evitamisel, käitamisel` kujule `ehitamisel, käitlemisel` ning `andmetega ringikäimisest` kujule `andmetega ja curling käimisest`. Mõnes üldkeelses eestikeelses lõigus oli `verbatim-2604` täpsem. Tervikuna mõjutasid Gemini vead siiski sagedamini üksikuid sõnu või fraase, samal ajal kui lokaalse mudeli korduv `COBIT`-i kaotamine või `COVID`-iks muutmine kahjustas loengu keskset tähendust.

Projektis ei ole kontrollitud, kas sama Gemini kasutusviis suudab järjest töödelda täispikki mitmetunniseid loenguid. Tasuta kasutuse sisendi- või väljundimahu piirang võib selle katkestada, kuid seda käsitletakse kontrollimata praktilise riskina, mitte tõendatud piiranguna.

## 14. Lõplik lokaalse mudeli valik

Katsetatud lokaalsetest variantidest valitakse põhikonfiguratsiooniks hotword'ideta `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604`, revisjon `310c550922fc1d1bebf3fad41f9b33ede6652bdc`, `ct2` alamkataloog ja CPU `int8` arvutus.

Otsus põhineb kasutaja sisulisel lugemiskontrollil ja järgmistel võrdlustel:

1. varasem `verbatim` mudel ei andnud paremat terviktulemust;
2. `subs` variant oli sisu lakoonilisuse tõttu nõrgem;
3. 25 hotword'iga katse rikkus teksti ega andnud usaldusväärset terminiparandust;
4. ühe `COBIT` hotword'iga katse ei tuvastanud sõna `COBIT` õigesti kordagi;
5. mehaaniline täitesõnade eemaldamine halvendas kohati teksti arusaadavust.

Hotword'e vaikekonfiguratsioonis ei kasutata. Gemini sisutulemus oli parem, kuid Gemini ei ole lokaalse põhikonfiguratsiooni osa ning pikkade loengute järjestikuse töötlemise võime pole projektis kontrollitud.
