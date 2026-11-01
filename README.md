# TTU loengukonspekti rakendus

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex), kasutaja kinnitatud lähteülesande ja tehnilise spetsifikatsiooni põhjal.

## 2. Sisukord

- [3. Süsteemi lühikirjeldus](#3-süsteemi-lühikirjeldus)
- [4. Hetkeseis](#4-hetkeseis)
- [5. Käivitamine](#5-käivitamine)
- [6. Väljundid](#6-väljundid)
- [7. Piirangud](#7-piirangud)
- [8. Kontrollimine](#8-kontrollimine)

## 3. Süsteemi lühikirjeldus

Rakendus koostab Echo360 loengusalvestisest, ainekavast ja slaididest iseseisvalt loetava eestikeelse ülikoolikonspekti. Selle eesmärk on vähendada pika loengu läbivaatamise ja õppematerjaliks vormistamise tööd, säilitades samal ajal väidete seose loengulõikude, ajatemplite, slaidide ning ainekava nõuetega. Konteineripõhine töövoog hangib loengu materjalid, loob ajatemplitega transkripti, toimetab selle eraldi kihis ning koostab kontrollitavate tõendite alusel Markdowni ja PDF-i. Täpne eesmärk ja nõuded on kirjeldatud [lähteülesandes](docs/lahteylesanne.md) ning arhitektuur, töövoog ja mudelivalikud [tehnilises spetsifikatsioonis](docs/tehniline_spek.md).

Loengu 3 tervikliku konspekti katse kasutab lokaalset EstLLM-i ning annab mudelile ainekava asjakohase osa, kogu ajatemplitega algtranskripti ja videost eraldatud slaidiandmed. Näidiskonspekti ega toimetatud transkripti mudeli faktilise sisendina ei kasutata. Katse prompt asub failis [`prompts/konspekt.md`](prompts/konspekt.md); tulemuseks oodatakse üht terviklikku Markdown-konspekti ning konspekti mahule ei seata tokenipõhist väljundipiiri.

## 4. Hetkeseis

Teostatud on Etapp 1 Echo360 importeri spike’i esimene osa:

- avaliku `/public` kursuselingi lahendamine;
- kursuse ja loengute normaliseeritud manifest;
- Echo ajatuse lippude ning ajatemplist tuletatud oleku eraldi säilitamine;
- salvestise olemasolu määramine tegelike meediakirjete järgi;
- valitud loengu meediaallikate kirjeldus ilma sessiooniküpsiseid või signeeritud päringuid salvestamata;
- eraldi slaidimanifest.

Etapp 2 ASR benchmarki tehniline võrdlus on tehtud eraldi kolme CPU-lõimega Faster-Whisperi workeris. Lukustatud kolme viieminutilise lõiguga kontrollkomplektil võrreldi TalTechNLP eesti keelele kohandatud turbo-mudelit ja Systrani üldist medium-mudelit. TalTechNLP konfiguratsioon oli ligikaudu 19% kiirem ning AI kvalitatiivsel vaatlusel selgelt loetavam; see on järgmise etapi tingimuslik põhikonfiguratsioon. Täpne raport on failis [`docs/asr_benchmark.md`](docs/asr_benchmark.md).

ASR-worker oskab nüüd luua ka kogu loengu toimetamata ajastatud transkripti. See loob ise Echo külalissessiooni, laadib lähteaudio ainult `work/` alla, säilitab segmendi- ja sõnaajastused ning eemaldab ajutise audio pärast edukat või nurjunud töötlust. Kasutaja antud näitefail on selle enda kirjelduse järgi videoloengu automaatsubtiitritest tundmatu AI-ga korrastatud täistranskript. See on säilitatud muutmata võrdlusmaterjalina failis [`docs/initial_materials/L03_transkript_teine_AI.md`](docs/initial_materials/L03_transkript_teine_AI.md); automaatsubtiitrite süsteem ja platvorm ning toimetusmudel on teadmata, seost Echo360-ga ei ole tuvastatud ja fail ei ole inimese kinnitatud referents.

Echo transkript ei sisaldu mängija algses andmeobjektis ega `captions`-väljas. Mängija laadib selle pärast lehe avamist dünaamiliselt endpoint'ist `/api/ui/echoplayer/lessons/{lesson_id}/medias/{media_id}/transcript`. ICM0032 loengu 3 avalik vastus sisaldas 31.10.2026 automaatselt loodud (`isAutomated: true`) 2171 ajastatud tekstilõiku JSON-väljal `contentJSON.cues`. Sama sisu oli allalaaditav eraldi TXT- ja WebVTT-failina. Tekst oli valdavalt ingliskeelne ja eestikeelse loengu kohta sisuliselt kasutuskõlbmatu: väljund on kooskõlas eestikeelse kõne eksliku tuvastamisega ingliskeelsete kõla poolest sarnaste sõnadena. Avalik vastus ei nimetanud konkreetset ASR-i pakkujat, mudelit ega tuvastuskeelt, mistõttu täpset seadistust ei käsitleta tõendatuna. Ingliskeelse loengu Echo transkriptsiooni kvaliteeti ei ole selles projektis kontrollitud ning selle kohta kasutamatuse järeldust ei tehta.

Rakenduse praegune eestikeelsete loengute töövoog ei päri, laadi, säilita ega töötle Echo automaattranskripti. Seda ei kasutata ka diagnostikaks või võrdluskihina; eestikeelne ajatemplitega transkript luuakse otse audiost projekti ASR-iga. Praegune teostus vastab sellele otsusele: `src/` all puudub Echo transkripti endpoint'i kasutus.

Loengu 3 esimene täispikk TalTechNLP töö lõpetas 31.10.2026 edukalt. Tulemuses on 447 segmenti ja sõnataseme ajad kogu 02:15:29 pikkuse salvestise kohta. Kolme CPU-lõimega töö kestis 6033,696 sekundit, reaalajakordaja oli 0,7392 ning ajutine lähteaudio eemaldati. Püsivad failid asuvad `/srv/ttu-loeng/outputs/jobs/l03/transcript/taltechnlp-turbo-et-int8/` all.

Kvaliteedimõõdikuid ei fabritseerita: WER ja CER arvutatakse ainult `human_verified` referentstekstiga lõikudel. Seetõttu on tehniline võrdlus valmis, kuid Etapp 2 kvaliteedi otsustusvärav ootab inimese kontrollitud referentstranskriptsiooni.

Etapp 3 jaoks on lisatud eraldi `pipeline` konteiner. See sisaldab PDF-i tekstieralduseks PyMuPDF-i ning videost slaidikaadrite loomiseks FFmpegi ja Tesseracti; rasked mudelitööd käivitatakse vestlusest sõltumatu oleku ja logiga asünkroonselt.

Etapp 3 vertikaalse proovi jaoks on lisatud ka auditeeritava valikufaili põhjal tõendipaketi koostamine ja kohaliku Ollama kaudu peatüki mustandi genereerimine. Esimene proov kasutab ainekava punkti 3.e, TalTechNLP ASR-i lõiku `01:55:00–02:00:00` ning kolme samast videost eraldatud slaidikaadrit. Valitud lõigu katvus on teadlikult märgitud osaliseks, sest see ei kirjelda piisavalt teavituse juhtimise ega kriisisuhtluse praktilisi meetmeid.

Etapi kontrollitud sisendid, artefaktid ja otsustusvärava seis on dokumenteeritud failis [`docs/etapp3_vertikaalne_proov.md`](docs/etapp3_vertikaalne_proov.md).

Esimene `mistral:latest` vertikaalne jooks lõpetas tehniliselt edukalt 65 minuti ja 31 sekundiga, kuid valideerimise olek oli `needs_review`: viidati ainult kolmele tõendile viiest, slaidi ei lisatud ning peatükk ei olnud iseseisvalt loetav konspekt. Etapp 3 kvaliteedi otsustusvärav on seetõttu avatud.

Transkripti toimetamise kandidaat on TartuNLP ja TalTechNLP eesti keele jaoks edasi treenitud `tartuNLP/Llama-3.1-EstLLM-8B-Instruct-1125`. Projekti Ollama hoidlas on selle kogukonna loodud Q5_K_M GGUF-kvant. Toimetaja annab mudelile järjestikuse ASR-tekstilõigu tavalise tekstina ja palub lihtsa eestikeelse promptiga eemaldada tarbetud kordused ning korrastada lauselõpud. Mudel tagastab tavalise kirjakeelse teksti; algne ajatemplitega ASR-transkript jääb muutmata. Katse on kirjeldatud failis [`docs/transkripti_toimetamise_proov.md`](docs/transkripti_toimetamise_proov.md).

Esimene lihtsa promptiga katselõik oli loetav, kuid mudel jättis välja kaks erialaterminit. Sama lõigu korduskatse lisas prompti lühikese terminite säilitamise nõude; `disaster recovery` ja `Enterprise Risk Management` jäid seejärel teksti alles. Tulemus ootab inimese kinnitust enne töövoo laiendamist.

Tõendipakett säilitab slaidi runtime-asukoha kõrval Markdowni failist lähtuva suhtelise pilditee. Seetõttu on mustand koos runtime’i tööstruktuuriga avatav ka väljaspool konteinerit; generaator ei kirjuta konteinerisisest `/runtime` teed avaldatavasse Markdowni.

Kasutaja antud 88 slaidiga PowerPointi fail säilib lähtekomplektis, kuid jääb esialgsest töövoost kõrvale, sest selle täpne vastavus salvestises kasutatud slaididele pole teada. Slaidid võetakse videost: toimetatud transkript võib sisaldada kõiki tuvastatud erinevaid slaide nende kronoloogilises asukohas, konspekti valitakse ainult õppesisu toetavad skeemid, tabelid, joonised ja muud vajalikud slaidid.

## 5. Käivitamine

Rakendus käivitatakse konteineris. `err_video_to_text` projektiga sama mustri järgi asub hosti runtime `/srv/ttu-loeng` all ja konteineris `/runtime` all. Runtime peab kuuluma konteineri UID/GID kasutajale.

30.10.2026 loodi serverisse runtime-kataloogid hostikasutaja `1001:1001` omandisse ning projekti Gitist välja jäetud `.env` seob konteineri sama UID/GID-ga.

Ühekordne hostikataloogide ettevalmistus:

```bash
sudo install -d -o "$(id -u)" -g "$(id -g)" -m 0750 \
  /srv/ttu-loeng/outputs \
  /srv/ttu-loeng/work \
  /srv/ttu-loeng/models/huggingface \
  /srv/ttu-loeng/cache \
  /srv/ttu-loeng/home
```

Kopeeri `.env.example` failiks `.env` ja kontrolli hosti UID/GID väärtused.

```bash
export TTU_LOENG_RUNTIME_ROOT=/srv/ttu-loeng
export TTU_LOENG_UID="$(id -u)"
export TTU_LOENG_GID="$(id -g)"

docker compose build importer
docker compose run --rm importer \
  resolve 'https://echo360.org.uk/section/<public-id>/public' \
  --output-dir /runtime/outputs
```

Valitud loengu metaandmete import:

```bash
docker compose run --rm importer \
  ingest 'https://echo360.org.uk/section/<public-id>/public' \
  --lesson-id '<lesson-id>' \
  --download-audio \
  --output-dir /runtime/outputs
```

ASR benchmarki üks konfiguratsioon:

```bash
docker compose --profile asr build asr
docker compose --profile asr run --rm asr benchmark \
  --audio /runtime/work/ingest/<work-key>/source.mp3 \
  --dataset /app/benchmarks/datasets/lecture3_v1.json \
  --output-dir /runtime/outputs/benchmarks/asr \
  --configuration-id '<configuration-id>' \
  --model '<huggingface-model-id>' \
  --revision '<immutable-revision>' \
  --compute-type int8 \
  --language et \
  --cpu-threads 3 \
  --beam-size 5
```

Kogu loengu ajastatud TalTechNLP transkriptsiooni taustatöö:

```bash
docker compose --profile asr run -d --name ttu-loeng-l03-full-asr asr transcribe-full \
  'https://echo360.org.uk/section/6f6fcb6b-cd42-4328-81db-eb3e30df9151/public' \
  --lesson-id a18d8522-4637-4fcf-a62a-60e3b1f2e586 \
  --output-dir /runtime/outputs/jobs/l03/transcript/taltechnlp-turbo-et-int8 \
  --configuration-id taltechnlp-turbo-et-int8 \
  --model TalTechNLP/whisper-large-v3-turbo-et-verbatim \
  --revision 1ae5a487d24116955803df4d9d01df56645eb44f \
  --model-subfolder ct2 \
  --compute-type int8 \
  --language et \
  --cpu-threads 3 \
  --beam-size 5
```

Ühe teema tõendipaketi koostamine:

```bash
docker compose --profile pipeline run --rm pipeline build-evidence \
  --syllabus /runtime/outputs/jobs/l03/syllabus/raw/document.json \
  --transcript /runtime/outputs/benchmarks/asr/icm0032-l03-asr-v1/taltechnlp-turbo-et-int8/result.json \
  --frames /runtime/outputs/jobs/l03/slides/incident-management/frames.json \
  --selection /app/benchmarks/evidence/l03_3e_v1.json \
  --output-dir /runtime/outputs/jobs/l03/evidence/3e
```

Peatüki mustandi taustatöö kasutab serveris juba töötavat `Double_Check_AI` Ollamat. Uusi mudeleid ei tõmmata ning kõrvalprojekti ei muudeta:

```bash
docker compose --profile pipeline run -d --name ttu-loeng-l03-3e-notes pipeline generate-notes \
  --evidence /runtime/outputs/jobs/l03/evidence/3e/evidence.json \
  --output-dir /runtime/outputs/jobs/l03/notes/3e
```

Töö olekut ja logi saab kontrollida eraldi:

```bash
docker compose logs ttu-loeng-l03-3e-notes
cat /srv/ttu-loeng/outputs/jobs/l03/notes/3e/run.json
```

## 6. Väljundid

```text
<runtime>/
├── outputs/
│   ├── resolver.json
│   ├── jobs/l03/
│   │   ├── evidence/3e/{evidence.json,coverage.json}
│   │   ├── transcript/taltechnlp-turbo-et-int8/{run.json,transcript.json,transcript.md}
│   │   └── notes/3e/{run.json,draft.md,raw_response.json,validation.json}
│   └── lessons/<lesson-id>/
│       ├── lesson.json
│       ├── media.json
│       ├── slides.json
│       └── run.json
└── work/
    └── ingest/<work-key>/source.mp3  # ajutine
```

Manifestid kirjutatakse atomaarse failivahetusega. Sessiooniküpsiseid, CloudFronti võtmeid ega signeeritud URL-ide päringuosi manifestidesse ei salvestata.

## 7. Piirangud

- Audio laaditakse alla ainult teadliku `--download-audio` valikuga runtime’i `work/` kataloogi ja kustutatakse pärast edukat või nurjunud jooksu. `--keep-audio` säilitab selle ainult teadlikuks veaotsinguks. Täisvideot vaikimisi ei salvestata.
- Oracle’i või AWS-i failisalvestus on võimalik tulevikusuund, kuid ei kuulu praeguse MVP skoopi.
- Echo slide deck’i import pole veel teostatud; selle puudumine märgitakse eraldi olekuna.
- PPTX-slaidikandidaat on esialgsest töövoost teadlikult kõrvale jäetud; slaidiallikas on video.
- Videost tuleb veel tuvastada slaidivahetused ja eraldada puhtad kõrge kvaliteediga kaadrid kogu loengu ulatuses.
- Kohaliku LLM-i väljund on mustand, mitte kinnitatud konspekt. Deterministlik kontroll kontrollib viidete ja slaidifailide olemasolu, kuid faktiline kontroll ja ASR-i kinnitamine vajavad inimese ülevaatust.
- Transkripti toimetamise mudel ei tohi algset ASR-artefakti üle kirjutada. Toimetatud kiht peab säilitama seose algsegmentide ja ajatemplitega ning sellel on konspekti sünteesist eraldi prompt, skeem ja kontroll.
- Mustandi deterministlik kontroll nõuab ka dokumendi päritolu esimese pealkirjana, sisukorda ja kõigi tõendipaketis märgitud katvuslünkade sõnaselget esitamist.
- Ainekava 3.e esimese tõendipaketi katvus on osaline: valitud lõigust puuduvad teavituse juhtimise ja kriisisuhtluse praktilised meetmed.
- Playwrighti ei kasutata, sest kontrollitud avalikud kursused töötasid standardse HTTP-kliendi ja küpsisesessiooniga.
- ASR benchmarki WER-i ja CER-i otsustusvärav jääb avatuks, kuni lukustatud loengulõikude referentstekst on inimese poolt kontrollitud; ühe ASR-i väljundit ei kasutata teise automaatse tõena.

## 8. Kontrollimine

Võrguvabad olekuloogika testid:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

30.10.2026 konteinerikatses lahendati 16 loenguga avalik kursus ja imporditi kontroll-loengu manifestid. Kontroll-loeng tuvastati kättesaadava salvestisena, allikateks leiti üks audio- ja kaks videofaili ning eraldi slide deck’i puudumine märgiti `not_provided_by_echo` olekuna.

Samas katses laaditi kontrollimiseks ajutiselt alla kogu 113 081 307-baidine MP3. Allalaaditud suurus vastas Echo metaandmetele, arvutati SHA-256 kontrollsumma ja audio eemaldati pärast kontrolli; `work/` alla ei jäänud audiofaili. Runtime-failid loodi hostikasutaja õigustes. Manifest sisaldab auditeerimiseks küpsiste nimesid, kuid mitte nende väärtusi, CloudFronti võtmete väärtusi ega signeeritud URL-ide päringuosi.

ASR benchmarki mõõtetulemused:

| Konfiguratsioon | 15 min transkriptsiooniaeg | Reaalaja tegur | Maksimaalne RSS |
|---|---:|---:|---:|
| TalTechNLP turbo int8 | 632,909 s | 0,7032 | 4,71 GiB |
| Systran medium int8 | 779,761 s | 0,8664 | 4,25 GiB |
