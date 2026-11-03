# Projekti tööreeglid

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex), kasutaja juhiste järgi. Käesoleva dokumendi esimene versioon põhines projekti `err_video_to_text` tööjuhendil; seda on käesoleva projekti jaoks kohandatud ja täiendatud.

## 2. Sisukord

- [3. Charset ja failivorming](#3-charset-ja-failivorming)
- [4. Peamine tööreegel: enne vastamist tutvu olemasoleva olukorraga](#4-peamine-tööreegel-enne-vastamist-tutvu-olemasoleva-olukorraga)
- [5. Tööpõhimõtted](#5-tööpõhimõtted)
- [6. Projekti dokumentide koostamine](#6-projekti-dokumentide-koostamine)
- [7. Vea käsitlemise juhis](#7-vea-käsitlemise-juhis)
- [8. Mittefunktsionaalsed ootused](#8-mittefunktsionaalsed-ootused)
- [9. Dokumentatsiooni ja tõeallikate register](#9-dokumentatsiooni-ja-tõeallikate-register)
- [10. Millal mida kindlasti lugeda](#10-millal-mida-kindlasti-lugeda)
- [11. Väljundi ootused](#11-väljundi-ootused)

## 3. Charset ja failivorming

- Kõik kood, konfiguratsioon ja dokumentatsioon peavad olema UTF-8 kodeeringus.
- Uute failide loomisel ja olemasolevate failide muutmisel tuleb säilitada UTF-8.
- Kui failis esineb kodeeringuprobleem, tuleb see käsitleda veana ja parandada juurpõhjus, mitte peita sümptomit.

## 4. Peamine tööreegel: enne vastamist tutvu olemasoleva olukorraga

- Enne igat sisulist vastust, hinnangut, kavandamist või muudatust tuleb tutvuda ülesandega seotud olemasoleva dokumentatsiooni, koodi ja andmetega.
- Seda nõuet tuleb järgida ka siis, kui kasutaja küsib ainult selgitust või plaani: vastus peab põhinema projekti tegelikul olukorral, mitte üldisel oletusel.
- Enne muudatuste kavandamist tuleb läbi lugeda kõik dokumendid ja koodiosad, mis puudutavad muudetavat ala. Vajaduse korral tuleb kontrollida ka olemasolevaid tööartefakte, logisid, konfiguratsiooni ja näidisandmeid.
- Olemasolev dokumentatsioon, kood, konfiguratsioon, logid ja andmed ei ole iseenesest õiged ega valed. Iga allikas kirjeldab seda, mis projektis on kirjas, teostatud või vaadeldav; selle olemasolu ei tõenda veel väite õigsust ega allika ülimuslikkust.
- Dokumentatsiooni olemasolu ei vabasta koodi ja tegelike andmete kontrollimisest. Samuti ei tohi toimivat koodi või olemasolevaid andmeid automaatselt pidada dokumentatsioonist õigemaks.
- Kui dokumentide eneste, dokumentatsiooni ja koodi, dokumentatsiooni ja andmete, koodi ja andmete või muude allikate vahel esineb vastuolu, ei tohi iseseisvalt otsustada, milline allikas on õigem või ajakohasem.
- Vastuolu avastamisel tuleb sisuline töö selles küsimuses peatada, kirjeldada kasutajale täpselt vastuolus olevad väited või vaatlused ning küsida enne jätkamist kasutaja otsust. Ka näiliselt ilmset vastuolu ei tohi vaikimisi lahendada.
- Kui vajalik allikas puudub või töö käigus tekib kahtlus, ei tohi lünka oletusega peita. Kontrolli olemasolevat materjali ning kui kontroll ei anna üheselt kooskõlalist tulemust, peatu ja küsi üle.

## 5. Tööpõhimõtted

- Ülesannet ei tohi iseseisvalt laiendada ega kitsendada. Kui ülesande laiendamine või kitsendamine tundub vajalik, tuleb enne muudatuse tegemist kasutajalt küsida.
- Kasutusele ei tohi võtta enda välja mõeldud mõisteid ega termineid, mille sisu ei ole inimesele arusaadavalt lahti seletatud.
- Kasutada ei tohi mõõtühikuid, mida ei ole kasutajaga kokku lepitud ja mille olemus ei ole inimesele üheselt arusaadav.
- Ärireeglid peavad elama võimalikult tsentraalselt ja järjekindlalt; väldi reeglite dubleerimist eri kihtides.
- Muudatused peavad olema minimaalsed, sihitud ja kooskõlas olemasoleva arhitektuuriga.
- Töötavat koodi ei tohi igaks juhuks muuta ega ennetavalt parandada. Kui mingi osa töötab ja ei ole uuritava vea tõendatud juurpõhjus, siis seda ei muudeta.
- Ära muuda kõrvalisi faile ega paranda mitteseotud probleeme.
- Kõrge mõjuga otsuste puhul eelista juurpõhjuse parandamist, mitte lokaalseid ümberkäike.
- Pikad ASR-i, video- ja slaiditöötluse ning muud rasked protsessid tuleb käivitada asünkroonselt nii, et vestlusaken jääb kasutajale vabaks. Protsessil peab olema hiljem kontrollitav olek, logi ja väljund; pelgalt terminaliseansi elus püsimisele ei tohi tugineda.

### Dokumentatsiooni ajakohastamine

- Pärast iga muudatust tuleb alati uuendada ka muudatuse piirkonda kirjeldavat dokumentatsiooni.
- Eraldi tuleb kontrollida kõiki projekti dokumente, mida muudatus võib mõjutada, ning veenduda, et muudatuse otsene ja kaudne mõju on neis arvesse võetud.
- Muudatust ei loeta lõpetatuks enne, kui see dokumentatsiooni mõjukontroll on tehtud ja vajalikud dokumendimuudatused on rakendatud.

### Git ja juurutus

- `git commit` vajab kasutaja iga töökorra jaoks eraldi luba.
- `git push` vajab kasutaja iga töökorra jaoks eraldi luba.
- Kuna rakendus töötab samas serveris, piisab testimiseks koodi muutmisest ning
  vajaliku konteineri ehitamisest ja taaskäivitamisest; commit'i ega push'i ei
  tohi eeldada juurutuse eeltingimusena.

### Testimine ja andmete muutmine

- Ilma kasutaja eraldi loata ei tohi käivitada teste ega kontrollskripte, mis
  kirjutavad andmebaasi või muudavad olemasolevaid andmeid.
- Ilma sellise loata on lubatud ainult dry-run'id, lugemispäringud ja muud
  mitte-muteerivad kontrollid.
- Mistahes andmeid või andmestruktuuri muutvat tegevust ei tohi teha ilma
  kasutaja eelneva eraldi loata — mitte kunagi. See hõlmab nii andmeridade
  lisamist, muutmist ja kustutamist kui ka tabeli, veeru, indeksi, piirangu või
  sequence'i lisamist, muutmist või kustutamist ning migratsiooni rakendamist.
- Kui kontroll eeldab andmete muutmist, tuleb enne peatuda ja küsida kasutajalt
  eraldi luba.

## 6. Projekti dokumentide koostamine

- Projekti dokumentide vaikevorming on Markdown (`.md`), kui kasutaja ei ole sõnaselgelt nõudnud teistsugust vormingut.
- Dokumendi esimene jaotis peab alati olema „Dokumendi päritolu“. Selles tuleb märkida, kas dokumendi koostas inimene või AI; vajaduse korral kirjeldatakse lühidalt ka alusmaterjale ja inimese panust.
- Dokumendi teine jaotis on üldjuhul „Sisukord“.
- Sisukorra võib ära jätta ainult siis, kui dokument sisaldab alla kolme sisulise punkti ja on lühem kui neli lehekülge. Muudel juhtudel on sisukord kohustuslik.
- Dokumendi päritolu jaotist sisukorda ei lisata.

## 7. Vea käsitlemise juhis

- Vea või regressiooni korral uuri esmalt juurpõhjust.
- Uuri kogu ahelat, mitte ainult vea esinemise kohta.
- Ära piirdu ainult sümptomit eemaldava parandusega, kui juurpõhjus jääb alles.
- Tee veast, selle põhjustest ja võimalikest parandusvariantidest kokkuvõte ning küsi nõusolek parandamiseks.
- Vastuses või töö kokkuvõttes kirjelda võimalusel lühidalt:
  1. mis oli juurpõhjus;
  2. miks viga tekkis;
  3. kuidas tehtud parandus selle kõrvaldab;
  4. milline jääkrisk või eeldus alles jääb.
- Kui loogiline koht on olemas, lisa või uuenda test, mis kinnitab parandust.

## 8. Mittefunktsionaalsed ootused

- Hoia API, andmemudeli, tööartefaktide ja ärireeglite käitumine eri klientide jaoks järjekindel.
- Väldi lahendusi, mis suurendavad põhjendamatult CPU-, mälu-, ketta-, võrgu- või andmebaasikoormust.
- Serveri jagatud CPU-ressursi tõttu tuleb ASR ning video- ja slaiditöötluse rasked tööd vaikimisi järjestada.
- API teenused peavad tagastama konkreetse kasutusjuhtumi jaoks vajaliku minimaalse andmehulga.
- Kui lisatakse püsiv andmebaas, on autoriteetne aeg UTC ning kasutajaliides kuvab aja kasutaja lokaalses ajavööndis.
- Kõik rakenduse skeemi tabelid kasutavad `start_date`, `end_date`, `created` ja `last_updated` veerge. Füüsilist kustutamist ei kasutata ning suletud kirjed ei tohi tavavoogudes nähtavale jääda.
- Kasutajaliidese tekstid peavad olema tõlgetest, mitte kõvakodeeritud.
- Eelista korduvate väärtuste puhul eeldefineeritud konstante ja ühist äriloogikat.
- Saladused, ligipääsutokenid ja autentimisküpsised peavad tulema `.env`-ist või muust saladuste hoidlast ning neid ei tohi kirjutada Git-i, logidesse ega väljunditesse.
- Mahukaid audio-, video-, mudeli- ega ajutisi tööfaile ei salvestata Git-repositooriumi ega andmebaasi. Andmebaasis hoitakse vajaduse korral ainult viiteid, kontrollsummasid ja metaandmeid.
- Kõik olulised mudeli-, tööriista- ja skeemiversioonid peavad olema väljundis auditeeritavad.

## 9. Dokumentatsiooni ja tõeallikate register

### Projekti põhidokumendid

- [`README.md`](../README.md) — rakenduse hetkeseis, käivitamine, väljundid ja piirangud.
- [`docs/agents.md`](agents.md) — projekti siduvad tööreeglid.
- [`docs/lahteylesanne.md`](lahteylesanne.md) — rakenduse eesmärk, ulatus ja vastuvõtukriteeriumid.
- [`docs/tehniline_spek.md`](tehniline_spek.md) — tehniline arhitektuur, andmemudel, töövoog ja etapistus.
- [`docs/mvp3_veeb_ja_ords.md`](mvp3_veeb_ja_ords.md) — MVP3 veebirakenduse, püsiva workeri, ORDS-i töölepingu ja mitme loengu kasutajavoo kinnitatud arhitektuur.
- [`db/erd.md`](../db/erd.md) — MVP3 Oracle'i andmemudel, Mermaid ER-diagramm, tabelite veerud, seosed, soft delete ning ORDS-i ja rakenduse oleku piir.
- [`db/schema/001_core_schema.sql`](../db/schema/001_core_schema.sql) — MVP3 Oracle'i sequence'ide, tabelite, seoste, unikaalsuste ja indeksite loomise skript.
- [`docs/slaiditootlus.md`](slaiditootlus.md) — slaidide olemasolu kontrolli, tuvastamise, sobitamise ja transkriptiga sidumise detailne lahendus.
- [`docs/asr_benchmark.md`](asr_benchmark.md) — Etapp 2 kontrollkomplekt, mudelivõrdlus, mõõtetulemused ja otsus.

### Lähte- ja võrdlusmaterjalid

- [`docs/initial_materials/L03_slaidikandidaat.pptx`](initial_materials/L03_slaidikandidaat.pptx) — kasutaja antud muutmata PowerPointi fail, mis pealkirja, kirjelduse ja põgusa sisukontrolli järgi on tõenäoliselt loengu 3 slaidipakk; faili täpne päritolu ja vastavus salvestises kasutatud slaididele ei ole teada.
- [`docs/initial_materials/L03_slaidikandidaat.origin.md`](initial_materials/L03_slaidikandidaat.origin.md) — slaidikandidaadi teadaolev päritolu, struktuur, kontrollsumma ja kasutuspiir.
- Echo360 avalik kursuselink, kursuse metaandmed, loengusalvestised ja slaidid.
- `/home/ubuntu/projektid/jenkins/docs/api.md`, `/home/ubuntu/projektid/jenkins/docs/tehniline_spek_ords.md`, `/home/ubuntu/projektid/jenkins/db/schema/001_core_schema.sql` ja `/home/ubuntu/projektid/jenkins/db/api/002_jobs_api_package.sql` — serveriülese ORDS-i järjekorra API, sõltuvused, registreeringud ja claim'i autoriteetne teostus.
- `err_video_to_text` dokumentatsioon ja kood ainult nende komponentide analüüsimisel, mida käesolevas projektis soovitakse taaskasutada.
- `/home/ubuntu/fun_o/nginx/default.conf` ja `/home/ubuntu/fun_o/docker-compose.yml` ühise nginx-veebiserveri või `funo_net` võrguga integratsiooni kavandamisel ja muutmisel.

### Teostuse põhilised allikad

- [`src/lecture_notes/echo360.py`](../src/lecture_notes/echo360.py) — Echo360 avalik sessioon, kursuse resolver ja olekute normaliseerimine.
- [`src/lecture_notes/config.py`](../src/lecture_notes/config.py) — välise runtime-kataloogi seadistus ja väljunditee kontroll.
- [`src/lecture_notes/manifests.py`](../src/lecture_notes/manifests.py) — loengu-, meedia- ja slaidimanifestid ning atomaarne kirjutamine.
- [`src/lecture_notes/cli.py`](../src/lecture_notes/cli.py) — konteineris kasutatava CLI käsud.
- [`src/lecture_notes/asr_benchmark.py`](../src/lecture_notes/asr_benchmark.py) — ASR-i lukustatud kontrollkomplekti töötlus, kogu loengu ajastatud transkriptsioon, kvaliteedimõõdikud ja ressursimõõtmine.
- [`src/lecture_notes/slides.py`](../src/lecture_notes/slides.py) — videokaadrite, OCR-i ja PDF-i praegune slaiditöötluse alus.
- [`compose.yaml`](../compose.yaml) ja [`Dockerfile`](../Dockerfile) — importeri konteinerpakendus.
- [`Dockerfile.asr`](../Dockerfile.asr) — Faster-Whisperi sõltuvustega eraldatud ASR-workeri konteinerpakendus.
- [`Dockerfile.slides`](../Dockerfile.slides) — FFmpegi, Tesseracti ja PyMuPDF-iga slaiditöötluse konteinerpakendus.
- [`benchmarks/datasets/lecture3_v1.json`](../benchmarks/datasets/lecture3_v1.json) — loengu 3 lukustatud ASR-kontrollkomplekti masinloetav kirjeldus.
- [`hotwords/icm0032/l03.txt`](../hotwords/icm0032/l03.txt) ja [`hotwords/icm0032/l08-1.txt`](../hotwords/icm0032/l08-1.txt) — varasemates katsetes kasutatud loengupõhised erialaterminid; [`hotwords/icm0032/l08-1-cobit.txt`](../hotwords/icm0032/l08-1-cobit.txt) — loengu 8.1 kontrollkatse üksiku `COBIT` hotword'iga.
- [`.env.example`](../.env.example) — runtime’i, konteineri kasutaja, kodukataloogi ja Oracle'i ühenduse saladusteta seadistusmall.
- [`tests/test_echo360.py`](../tests/test_echo360.py) — olekuloogika võrguvabad kontrollid.
- [`tests/test_asr_benchmark.py`](../tests/test_asr_benchmark.py) — ASR-i kvaliteedimõõdikute ja videoallika valiku võrguvabad kontrollid.

Registrit tuleb täiendada kohe, kui projektile lisandub README, andmeskeem, API leping, konteinerite kirjeldus, hindamisandmete register või muu asjakohane allikas. Registrisse kuulumine ei anna allikale teiste ees ülimuslikkust.

## 10. Millal mida kindlasti lugeda

- Enne igat sisulist vastust loe vähemalt käesolev juhend ja ülesandega seotud põhidokumendi osad; koodi olemasolul kontrolli vastavat teostust.
- Kui muudad rakenduse eesmärki, ulatust, väljundeid või vastuvõtukriteeriume, loe `docs/lahteylesanne.md` ja `docs/tehniline_spek.md`.
- Kui muudad arhitektuuri, andmemudelit, tööde järjekorda, konteinerite vastutusi või ressursikasutust, loe `docs/tehniline_spek.md`, asjakohane konfiguratsioon ja kogu mõjutatud töötlusahel.
- Kui muudad MVP3 veebirakendust, ORDS-i lepingut, workeri adaptereid või taustatööde olekute kuvamist, loe `docs/mvp3_veeb_ja_ords.md` ja Jenkinsi projekti autoriteetsed ORDS-i allikad.
- Kui muudad rakenduse püsivat andmemudelit, loe `db/erd.md` ning ajakohasta diagramm, tabelikirjeldused ja kõik mõjutatud migratsioonid koos.
- Kui muudad avalikku hostinime, TLS-i, pöördproksit, veebiliidese serveerimist või ühise Docker-võrgu kasutust, loe enne `/home/ubuntu/fun_o/nginx/default.conf`, `/home/ubuntu/fun_o/docker-compose.yml` ja mõlema mõjutatud projekti juurutusdokumentatsioon.
- Kui muudad Echo360 resolverit või meediaallikate salvestamist, kontrolli toimivat avaliku sessiooni loomise voogu, tegelikke võrgupäringuid ja olemasolevaid resolveri artefakte.
- Kui muudad ASR-i või tekstisegmentide ajastust, loe vastavad mudeli- ja hindamisdokumendid, olemasolev teostus ning kontrollandmed. `err_video_to_text` taaskasutuse korral loe enne selle projekti asjakohased allikad.
- Kui muudad slaidide olemasolu kontrolli, tuvastamist, sobitamist või transkriptiga sidumist, loe `docs/slaiditootlus.md`, olemasolev teostus, tegelik meediamanifest, kontrollvideo andmed ja seotud testid.
- Kui kasutad protsessiandmeid kvantitatiivseks analüüsiks või mudeli õpetamiseks, peab enne olema dokumenteeritud andmete kasutusluba ja hindamiskomplekti ulatus.

## 11. Väljundi ootused

- Kui töö sisaldab vea parandust, too kokkuvõttes eraldi välja juurpõhjus ja paranduse loogika.
- Kui töö tugineb oletusele, nimeta oletus selgelt ning küsi enne muudatuse tegemist luba.
- Kui avastad allikate vahel lahknevuse, peata seda küsimust puudutav sisuline töö kohe, too vastuolu välja ja küsi enne jätkamist täiendavaid juhtnööre. Vastuolu ei tohi jätta ainult töö lõpu kokkuvõttesse.
