# TTU loengutranskriptsiooni rakendus

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex) kasutaja kinnitatud MVP2 ülesandepüstituse, projekti kontrollitud teostuse ja 3.11.2026 kinnitatud MVP3 arhitektuuriotsuste põhjal.

## 2. Sisukord

- [3. Lühikirjeldus](#3-lühikirjeldus)
- [4. Hetkeseis](#4-hetkeseis)
- [5. Käivitamine](#5-käivitamine)
- [6. Väljundid](#6-väljundid)
- [7. Piirangud](#7-piirangud)

## 3. Lühikirjeldus

Rakendus leiab avalikust Echo360 loengukogumikust loengud ja nende meedia ning loob valitud eestikeelsest loengust hotword'ideta TalTechNLP `verbatim-2604` kõnetuvastusmudeliga täieliku ajatemplitega transkripti. Rakendus tuvastab videost slaidid, seob need transkriptsioonisegmentidega ja võimaldab kasutada kasutaja antud PDF-, PPT- või PPTX-faili parema slaidipildi allikana. Hotword'ide tugi säilib kontrollkatseteks, kuid mudeli loodud teksti mehaaniliselt ei järelpuhastata; keelelist toimetamist ega konspekti koostamist rakendus ei tee. Täpne ulatus on failis [`docs/lahteylesanne.md`](docs/lahteylesanne.md), arhitektuur failis [`docs/tehniline_spek.md`](docs/tehniline_spek.md), MVP3 veebirakenduse ja ORDS-i leping failis [`docs/mvp3_veeb_ja_ords.md`](docs/mvp3_veeb_ja_ords.md), andmemudel failis [`db/erd.md`](db/erd.md) ning slaiditöötlus failis [`docs/slaiditootlus.md`](docs/slaiditootlus.md).

## 4. Hetkeseis

Valmis ja kontrollitud on:

- Echo360 avaliku külalissessiooni loomine, loengute nimekirja lugemine ning audio- ja videoallikate leidmine;
- TalTechNLP mudeliga kontroll-lõikude ja kogu loengu transkribeerimine;
- segmendi- ja sõnataseme ajatemplitega JSON- ning Markdown-väljund;
- ajutise audio eemaldamine pärast töötlust;
- loengupõhise hotword-loendi edastamine Faster-Whisperile;
- videost kaadrite võtmine, pildimuutuste põhine slaidikandidaatide leidmine ja Tesseracti OCR;
- animatsiooniseisude koondamine ja korduvate slaidide sidumine;
- PPT/PPTX teisendamine PDF-iks ning PDF-slaidide renderdamine;
- eraldi slaidifaili videoga sobitamine;
- slaidiviidete lisamine transkripti segmendipiiridele ja ühendatud Markdown-väljund.

Eraldi slaidifaili olemasolul võrreldakse stabiilse videokaadri kogu tuvastatud teksti PDF-i tekstikihiga. Transkriptis kuvatakse slaidi pealkiri ainult kinnitatud PDF-vastest; kontrollimata video-OCR-i teksti pealkirjana ei kasutata.

ICM0032 kontroll-loengu pikkus oli 2 tundi ja 15 minutit. Täistranskriptsioon valmis 1 tunni ja 40 minutiga ning sisaldas 447 segmenti ja 15 064 sõna. Kasutaja pistelise kuulamiskontrolli järgi oli tulemus hästi loetav ja sisult täpne.

Slaiditöötluse `video-slides-v2` tervikahel on teostatud ja loengu 8.1 põhjal kontrollitud. Töövoog kasutab 20-sekundilist põhikontrolli, pildisõrmejälgede võrdlust ning ainult muutunud põhivahemiku kahe-sekundilist täpsustust. Lõplik kontroll leidis videost viis slaidi ja sidus kõik viis kasutaja PPTX-ist loodud PDF-i vastava staatilise leheküljega; ülemineku- ja animatsioonivaheolekud ei tekitanud lisaslaide. Detailne seis ja algoritm on failis [`docs/slaiditootlus.md`](docs/slaiditootlus.md).

Loengust 8.1 võrreldi senist `whisper-large-v3-turbo-et-verbatim`, uuemat `whisper-large-v3-turbo-et-verbatim-2604`, subtiitrite koostamiseks treenitud `whisper-large-v3-turbo-et-subs` mudelit ning hotword'idega katseid. Kasutaja sisulise lugemiskontrolli järgi annab lokaalsetest variantidest parima tulemuse hotword'ideta `verbatim-2604`; see on nüüd põhikonfiguratsioon.

Lisaks on loengust 8.1 alles `verbatim-2604` katsevariant, mis kasutas 25 loengupõhist hotword'i ja mehaanilist täitesõnade järelpuhastust. Kasutaja võrdluses muutis järelpuhastus teksti kohati halvemini arusaadavaks ning lahendus eemaldati aktiivsest töötlusahelast. Katseväljund säilib võrdlusmaterjalina.

Sama audio `Gemini 3.5 Flash-Lite` transkript säilitas `COBIT`-i ja teisi erialatermineid lokaalsest mudelist selgelt paremini. Kasutatud juhist ega teenuse täpset konfiguratsiooni pole failis dokumenteeritud ning pikkade loengute järjestikust töötlemist pole kontrollitud. Tasuta kasutuse mahu võimalik piirang jääb seetõttu kontrollimata praktiliseks riskiks.

MVP3 arendus toimub harus `mvp3`. Teostatud on FastAPI HTML-liides, Google Identity Services ID-tokeni põhine autentimine, Oracle'i hoidla, ORDS OAuth-klient, mitme loengu esitamine, valmis slaididega transkripti avalik Markdowni otselink ja püsiv worker. ORDS on ainus järjekorra ja käivitamisloa autoriteet; rakendus täidab claim'itud `asr` ja `slides` töö sisu ise. HTML-liides kasutab eraldi teenusekihti, mida saab järgmises etapis kasutada JSON API. Domeeni `ttu-loeng.fun-o.eu` DNS-kirje, nginxi HTTP→HTTPS suunamine, nime sisaldav ühine TLS-sertifikaat ja HTTPS-pöördproksi konteinerile `ttu-loeng-web:8000` on seadistatud. Veebikonteiner töötab ühises `funo_net` võrgus ning Nginx lahendab selle muutuva konteineri-IP Docker DNS-i kaudu dünaamiliselt.

MVP2 käigus valminud L03 ja L08.1 tulemused on lisatud rakenduse andmebaasi ajalooliste loengutena. L03 kasutab olemasolevat põhitranskripti ning L08.1 slaididega ühendatud Markdowni ja olemasolevat PPTX-slaidiallikat. Neile ei ole loodud tagantjärele ORDS-i operatsioone, sest algsed töötlused ei toimunud keskse järjekorra kaudu.

Sisselogitud kasutaja valib esmalt `SUBMISSIONS.COURSE_TITLE` järgi järjestatud kursuse. Kursuse vaates kuvatakse selle loengud `LECTURE_PROCESSINGS.LECTURE_TITLE` järgi järjestatud kompaktses nimekirjas koos Echo360 tegeliku toimumiskuupäevaga. Administraator saab sulgeda konkreetse loengutöötluse soft delete'iga. Uue loengu lisamisel võib administraator valida olemasoleva kursuse nime järgi või sisestada uue Echo360 avaliku kursuselingi.

## 5. Käivitamine

Kopeeri `.env.example` failiks `.env`, täida Oracle'i ja ORDS-i saladused, määra `GOOGLE_CLIENT_ID` ning genereeri `SESSION_SECRET`. Google Console'i Authorized JavaScript origins loendis peab olema `https://ttu-loeng.fun-o.eu`. Google Client Secretit ega redirect URI-t see autentimisvoog ei kasuta.

Püsiva veebirakenduse ja workeri käivitamine:

```bash
docker compose up -d --build web worker
```

DNS, nginxi HTTP→HTTPS suunamine, `ttu-loeng.fun-o.eu` nime sisaldav TLS-sertifikaat ja HTTPS-pöördproksi on seadistatud. Avalik aadress vastab HTTPS-i kaudu ning Google'i autentimise tervikkontrolli saab teha brauseris.

Echo360 lingi kontroll:

```bash
docker compose run --rm importer resolve \
  https://echo360.org.uk/section/SECTION_ID/public \
  --output-dir /runtime/outputs/jobs/JOB_ID/import
```

Loengu meedia manifesti loomine:

```bash
docker compose run --rm importer ingest \
  https://echo360.org.uk/section/SECTION_ID/public \
  --lesson-id LESSON_ID \
  --output-dir /runtime/outputs/jobs/JOB_ID/import
```

Kogu loengu transkribeerimine hotword'ideta `verbatim-2604` põhikonfiguratsiooniga:

```bash
docker compose --profile asr run --rm asr transcribe-full \
  https://echo360.org.uk/section/SECTION_ID/public \
  --lesson-id LESSON_ID \
  --output-dir /runtime/outputs/jobs/JOB_ID/transcript/taltechnlp-turbo-et-verbatim-2604-int8 \
  --model TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604 \
  --revision 310c550922fc1d1bebf3fad41f9b33ede6652bdc \
  --model-subfolder ct2 \
  --configuration-id taltechnlp-turbo-et-verbatim-2604-int8
```

Olemasolev slaidikaadrite tehniline proov:

```bash
docker compose --profile slides run --rm slides extract-frames \
  https://echo360.org.uk/section/SECTION_ID/public \
  --lesson-id LESSON_ID \
  --output-dir /runtime/outputs/jobs/JOB_ID/slides/sample \
  --start-seconds 0 \
  --end-seconds 600 \
  --interval-seconds 30
```

Slaidide tuvastamine ning transkriptiga ühendamine:

```bash
docker compose --profile slides run --rm slides process \
  https://echo360.org.uk/section/SECTION_ID/public \
  --lesson-id LESSON_ID \
  --transcript /runtime/outputs/jobs/JOB_ID/transcript/taltechnlp-turbo-et-int8/transcript.json \
  --output-dir /runtime/outputs/jobs/JOB_ID/slides \
  --slides-input /runtime/inputs/JOB_ID/slides.pptx
```

`--slides-input` jäetakse ära, kui kasutaja eraldi PPT-, PPTX- või PDF-faili ei anna. Slaidide ajastus pärineb mõlemal juhul videost.

## 6. Väljundid

Püsivad tööartefaktid asuvad OCI Object Storage'i ämbris `ttu_loeng_files`: sisendid prefiksi `inputs/` ja tulemused prefiksi `outputs/` all. Brauser ei saa OCI PAR-aadresse; FastAPI loeb artefakte serveripoolel. OCI prefix-PAR-id seadistatakse `.env`-is võtmetega `OCI_INPUTS_R`, `OCI_INPUTS_RW`, `OCI_OUTPUTS_R` ja `OCI_OUTPUTS_RW`.

```text
outputs/jobs/<lecture_processing_id>/
├── import/
├── transcript/<configuration_id>/
│   ├── run.json
│   ├── transcript.json
│   └── transcript.md
└── slides/<operation_id>/
    ├── run.json
    ├── slides.json
    ├── transcript_with_slides.md
    └── images/                    # lõplikud Markdownis viidatud pildid
```

Kui kasutaja on lisanud slaidifaili, on see OCI `inputs/<lecture_processing_id>/` all. Worker laeb selle ja ASR-i JSON-i töö ajaks lokaalsesse `work/` kataloogi, renderdab `reference/` võrdluspildid lokaalselt ning eemaldab need eduka slaiditöö järel. OCI-sse jõuavad ainult lõplikud JSON-, Markdown- ja `images/`-failid; internetist uuesti hangitavat audiot ega videot ei säilitata pärast töö lõppu.

## 7. Piirangud

- Echo360 eestikeelne automaattranskript ei ole kontrollitud kursuse puhul kasutatav ja seda töövoog ei laadi.
- Ingliskeelsete loengute Echo360 transkriptsiooni kvaliteeti ei ole hinnatud.
- 20-sekundiline põhikontroll võib jätta leidmata slaidi, mis ilmub ja kaob täielikult ühe põhivahemiku sees nii, et mõlemad põhikaadrid kujutavad sama slaidi. Kasutaja hinnangul on kontrollitavate loengute puhul alla 20 sekundi näidatava slaidi tõenäosus väga väike.
- Kasutaja antud slaidifaili ei loeta loenguga vastavaks enne videopõhist kontrolli.
- Transkripti keeleline ümberkirjutamine, mehaaniline järelpuhastus ja konspekti koostamine jäävad rakendusest välja.
- Gemini andis loengu 8.1 sisuvõrdluses parema erialaterminite tulemuse, kuid pikkade loengute järjestikuse töötlemise sobivust ja tasuta kasutuse mahupiire pole projektis kontrollitud.
