# Etapp 2: eestikeelse ASR-i benchmark

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex). Dokument põhineb 30.10.2026 samas ARM64 serveris käivitatud ASR-mõõtmistel, lukustatud kontrollkomplektil ning automaatselt loodud JSON- ja Markdown-artefaktidel. Tekstinäidete kvalitatiivne vaatlus on AI hinnang, mitte inimese kontrollitud referentstranskriptsioon.

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

Järgmise arendusetapi tehniliseks põhikonfiguratsiooniks lukustatakse tingimuslikult `taltechnlp-turbo-et-int8`, sest:

1. see oli samade parameetritega kiirem;
2. AI kvalitatiivne vaatlus näitas paremat eestikeelset loetavust ja valdkonnaterminite kuju;
3. tegemist on TalTechNLP eestikeelsele kõnele kohandatud mudeliga.

„Tingimuslikult“ tähendab, et konfiguratsiooni võib kasutada Etapp 3 tehnilise vertikaalse proovi loomiseks, kuid seda ei nimetata lõplikult kvaliteedilt kinnitatud põhimudeliks enne inimese kontrollitud referentsi ja WER/CER arvutamist.

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

Kogu loengu esimene töö käivitati 31.10.2026 kell 08:47 UTC asünkroonse konteinerina `ttu-loeng-l03-full-asr`. Töö olekut kirjeldab püsiv fail:

```text
/srv/ttu-loeng/outputs/jobs/l03/transcript/taltechnlp-turbo-et-int8/run.json
```

Käivitamise järel oli olek `running`; 113 081 307-baidine lähte-MP3 asus ajutiselt `/srv/ttu-loeng/work/transcribe/fc92af1fe35c9dd5/source.mp3`. Transkriptsiooni kestus ja tulemused dokumenteeritakse pärast töö lõppu. Audio peab siis olema eemaldatud nii väljundi `run.json` kui ka failisüsteemi kontrolli järgi.

Kasutaja antud fail [`initial_materials/L03_transkript_teine_AI.md`](initial_materials/L03_transkript_teine_AI.md) on selle enda kirjelduse järgi videoloengu automaatsubtiitritest tundmatu AI-ga korrastatud, ajamärkideta täistranskript. Fail ei nimeta automaatsubtiitrite süsteemi ega platvormi ning seost Echo360-ga ei ole tuvastatud. Toimetusmudel ei ole teada ja väide sisu täieliku säilimise kohta ei ole algsete subtiitrite või toimetuslogi puudumise tõttu kontrollitav. Faili kasutatakse tulevikus teemade, terminite, teksti normaliseerimise ja joondamise kandidaadina, mitte inimese kontrollitud referentsina. Kogu loengu TalTechNLP väljund jääb toimetamata ajastatud kihiks, mille kaudu saab väited tagasi salvestisega siduda.
