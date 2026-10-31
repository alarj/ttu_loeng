# Etapp 3 vertikaalse proovi raport

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex), kontrollitud ICM0032 ainekava, TalTechNLP ASR-i väljundi, Echo360 videost eraldatud slaidikaadrite, rakenduse käitusartefaktide ja kohaliku Ollama katse põhjal. Ükski transkriptsioon ega genereeritud konspekt ei ole veel inimese poolt kinnitatud.

## 2. Sisukord

- [3. Eesmärk ja piir](#3-eesmärk-ja-piir)
- [4. Sisendid](#4-sisendid)
- [5. Tõendipaketi tulemus](#5-tõendipaketi-tulemus)
- [6. Konspekti genereerimine](#6-konspekti-genereerimine)
- [7. Kontroll ja otsustusvärav](#7-kontroll-ja-otsustusvärav)
- [8. Järgmised sammud](#8-järgmised-sammud)

## 3. Eesmärk ja piir

Etapp 3 eesmärk on tõendada ühe teema ulatuses ahelat:

```text
ainekava → transkriptsioon + slaidid → tõendid → viidetega Markdowni peatükk → kontroll
```

Kontrollteema on ICM0032 ainekava punkt 3.e „intsidentide haldamine, reageerimine ja suhtlus“. Kasutatud loengulõik on `01:55:00–02:00:00`. Proov ei pretendeeri veel kogu loengu ega kogu ainekavapunkti katmisele.

## 4. Sisendid

| Sisend | Kontrollitud väärtus |
|---|---|
| Loeng | „3. Business Continuity and Disaster Recovery“ |
| Echo lesson ID | `a18d8522-4637-4fcf-a62a-60e3b1f2e586` |
| Ainekava | 13 lk; punkt 3.e leheküljel 6 |
| ASR | TalTechNLP `whisper-large-v3-turbo-et-verbatim`, Faster-Whisper CPU int8 |
| ASR lõik | `l03_late_1150_1200`, 14 segmenti |
| Slaidid | videost 30-sekundilise sammuga eraldatud 10 kaadrit; tõenditeks valiti 3 |
| Slaidide ajad | `01:55:00`, `01:56:30`, `01:59:00` |

Echo ei paku selle loengu juures eraldi slide deck’i. Slaidid eraldati 360p esitlusvideost; 92 498 488-baidine ajutine video eemaldati pärast töötlust. Kasutaja lisas võimaliku loengu 3 slaidipaki pärast selle vertikaalse proovi tegemist, mistõttu käesoleva ajaloolise proovi tõendid ja tulemused põhinevad endiselt videokaadritel. Järgmises proovis tuleb esmalt võrrelda slaidikandidaati salvestises nähtuga. Alles kinnitatud vastavuse ulatuses võib selle sisu kasutada ja videokaadreid ajajoonega joondamiseks rakendada; lahknevused tuleb eraldi dokumenteerida.

## 5. Tõendipaketi tulemus

Auditeeritav valikufail on [`benchmarks/evidence/l03_3e_v1.json`](../benchmarks/evidence/l03_3e_v1.json). Käitusaegne väljund asub hostis:

```text
/srv/ttu-loeng/outputs/jobs/l03/evidence/3e/
├── evidence.json
└── coverage.json
```

Pakett sisaldab viit väitekandidaati:

1. talitluspidevuse planeerimisel tehtud ettevalmistuse kasutamine intsidendi käsitlemisel;
2. esmase reageerimise ja taastamise eristamine;
3. Gold-, Silver- ja operatiivtasandi seos meeskondade, meetodite, poliitikate ja protsessidega;
4. dokumenteerimise kasutamine protsesside hilisemaks parendamiseks;
5. ISO 22301-l põhinev ajajoon kiirest vastusest alternatiivsete protsesside kaudu algsete protsesside taastamiseni.

Iga kandidaat viitab konkreetsetele ASR-segmentidele; neli kandidaati viitavad lisaks slaidikaadrile. Ainekava kirje, PDF-i kontrollsumma, transkriptsiooni kontrollsumma, slaidimanifesti kontrollsumma ja valikufaili kontrollsumma on paketis säilitatud.

Katvus on `partial`. Valitud lõik ei anna piisavat otsest alust järgmiste aspektide konspekti kirjutamiseks:

- teavituse juhtimise konkreetne protsess;
- kriisisuhtluse meetmed ja kanalid.

Neid lünki ei tohi generaator täita üldteadmiste ega oletustega.

## 6. Konspekti genereerimine

Katse kasutab serveris projekti `/home/ubuntu/Double_Check_AI` kaudu juba töötavat Ollamat. Kõrvalprojekti ega selle mudeleid ei muudeta. Kasutatav mudel on olemasolev `mistral:latest` (7,2B, Q4_K_M); täpne digest salvestatakse `run.json` faili.

Generaator saab ainult ühe teema tõendipaketi, mitte kogu loengu transkriptsiooni. Väljundid paiknevad:

```text
/srv/ttu-loeng/outputs/jobs/l03/notes/3e/
├── run.json
├── draft.md
├── raw_response.json
└── validation.json
```

Pikk mudelitöö käivitatakse nimega taustakonteineris. `run.json` tekib enne Ollama kutset olekuga `running` ning lõpetamisel saab oleku `completed` või `failed`. Konteineri logi ja väljundid on kontrollitavad vestlusest sõltumatult.

Esimene jooks lõpetas 30.10.2026 kell 17:25:01 UTC olekuga `completed`. Mõõdetud tulemused:

| Mõõdik | Tulemus |
|---|---:|
| Kogukestus | 3930,941 s ehk 65 min 31 s |
| Mudeli laadimine | 59,083 s |
| Sisend | 6534 tokenit |
| Sisendi töötlemiskiirus | 2,450 tokenit/s |
| Väljund | 1475 tokenit |
| Genereerimiskiirus | 1,225 tokenit/s |
| Mudeli digest | `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` |
| Ollama lõpetamise põhjus | `stop` |

Jooks ei hangunud ega lõppenud ressursiveaga. Pikk kestus tulenes CPU-l töötava 7,2B mudeli aeglasest sisendi töötlemisest ja genereerimisest.

## 7. Kontroll ja otsustusvärav

Deterministlik kontroll hindab vähemalt:

- kas kõik viis tõendi-ID-d on Markdownis viidatud;
- kas tundmatuid tõendi-ID-sid ei kasutata;
- kas vähemalt üks valitud slaid on suhtelise teega lisatud;
- kas dokumendi päritolu on esimene pealkiri ja sisukord on olemas;
- kas mõlemad teadaolevad katvuslüngad on sõnaselgelt nimetatud.

See kontroll ei tõenda faktilist õigsust. ASR-i tekst, väitekandidaadid ja mudeli proosa vajavad inimese ülevaatust. Etapp 3 otsustusväravat „faktitäpne, iseseisvalt loetav ja jälgitav“ ei suleta enne mustandi sisulist kontrolli.

Esimese jooksu deterministlik tulemus on `needs_review`:

- Markdown viitab viiest tõendist kolmele; puuduvad `evidence_l03_3e_002` ja `evidence_l03_3e_005`;
- ühtki slaidi ei lisatud;
- ainekava katvuslüngad jäid sisulise selgituse asemel mudeli juhise kujul „nimed coverage.missing_aspects“;
- peatükk ei ole iseseisvalt loetav konspekt, vaid lühike tõendite loetelu;
- talitluspidevuse plaanide kasutamise väide seoti vale tõendiga ning dubleerib juhtimisstruktuuri teksti;
- mudel moodustas kontrollimata Echo URL-i päringuparameetrid `start` ja `end`, kuigi Echo deep-link’i toimimist ei ole kinnitatud;
- jooks kasutas enne hilisemaid parandusi ehitatud image’it ja tõendipaketti. Seetõttu puudusid selle runtime’i `evidence.json` failist `markdown_path` väärtused ning valideerimine sisaldas ainult tolle jooksu ajal kehtinud kolme kontrolli. Praegune lähtekood ja valikufail sisaldavad rangemaid päritolu-, sisukorra-, katvuslünga- ja suhtelise slaiditee kontrolle.

Etapp 3 otsustusvärav jäi seega avatuks. Tehniline ahel töötas lõpuni, kuid genereeritud sisu ei vasta kvaliteedinõuetele.

## 8. Järgmised sammud

1. oodata ära kogu loengu muutmata ajatemplitega TalTechNLP transkriptsioon ning kontrollida väljundid ja ajutise audio eemaldamine;
2. koostada inimese kontrollitav transkripti toimetamise katsekomplekt ning hinnata põhikandidaati `tartuNLP/Llama-3.1-EstLLM-8B-Instruct-1125` korduste ja kõnetäidete eemaldamisel, lausepiiride parandamisel ning sisu ja ajaseoste säilitamisel;
3. ehitada pipeline-image uuesti ja koostada tõendipakett praeguse skeemi järgi, et `markdown_path` väärtused jõuaksid runtime’i;
4. korrata ühe teema konspektikatset EstLLM-iga, kasutades eraldi sünteesiprompti ja praegust valideerijat; teist Mistrali jooksu ei kavandata;
5. leida loengust täiendav lõik teavituse ja kriisisuhtluse kohta või märkida need kogu loengu järel tõendatult katmata;
6. lasta inimesel kontrollida kasutatud ASR-segmendid, toimetatud transkript, väitekandidaadid ja konspekti mustand;
7. võtta eraldi konspektimudel võrdlusse ainult siis, kui EstLLM ei läbi ülesandepõhist kvaliteediväravat;
8. pärast kvaliteedivärava läbimist laiendada töövoog ainekava punktidele 3.a–3.d.
