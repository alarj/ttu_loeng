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

- Ärireeglid peavad elama võimalikult tsentraalselt ja järjekindlalt; väldi reeglite dubleerimist eri kihtides.
- Muudatused peavad olema minimaalsed, sihitud ja kooskõlas olemasoleva arhitektuuriga.
- Töötavat koodi ei tohi igaks juhuks muuta ega ennetavalt parandada. Kui mingi osa töötab ja ei ole uuritava vea tõendatud juurpõhjus, siis seda ei muudeta.
- Ära muuda kõrvalisi faile ega paranda mitteseotud probleeme.
- Kõrge mõjuga otsuste puhul eelista juurpõhjuse parandamist, mitte lokaalseid ümberkäike.
- Pikad ASR-i, diariseerimise, mudelite laadimise ja muud rasked protsessid tuleb käivitada asünkroonselt nii, et vestlusaken jääb kasutajale vabaks. Protsessil peab olema hiljem kontrollitav olek, logi ja väljund; pelgalt terminaliseansi elus püsimisele ei tohi tugineda.

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
- Serveri piiratud ressursi tõttu tuleb ASR, diariseerimine ja lokaalse keelemudeli töö vaikimisi järjestada.
- API teenused peavad tagastama konkreetse kasutusjuhtumi jaoks vajaliku minimaalse andmehulga.
- Kui lisatakse püsiv andmebaas, on autoriteetne aeg UTC ning kasutajaliides kuvab aja kasutaja lokaalses ajavööndis.
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
- [`docs/asr_benchmark.md`](asr_benchmark.md) — Etapp 2 kontrollkomplekt, mudelivõrdlus, mõõtetulemused ja otsus.
- [`docs/etapp3_vertikaalne_proov.md`](etapp3_vertikaalne_proov.md) — Etapp 3 ühe teema tõendipaketi, kohaliku LLM-i katse, kontrolli ja katvuslünkade raport.

### Lähte- ja võrdlusmaterjalid

- [`docs/initial_materials/AINEKAVA 1.237978_Laiendatud ainekava ICM0032 2026-10-09 v9.pdf`](initial_materials/AINEKAVA%201.237978_Laiendatud%20ainekava%20ICM0032%202026-10-09%20v9.pdf) — ICM0032 laiendatud ainekava.
- [`docs/initial_materials/L03_konspekt.docx.pdf`](initial_materials/L03_konspekt.docx.pdf) — loengu 3 näidiskonspekt.
- [`docs/initial_materials/L03_slaidikandidaat.pptx`](initial_materials/L03_slaidikandidaat.pptx) — kasutaja antud muutmata PowerPointi fail, mis pealkirja, kirjelduse ja põgusa sisukontrolli järgi on tõenäoliselt loengu 3 slaidipakk; faili täpne päritolu ja vastavus salvestises kasutatud slaididele ei ole teada.
- [`docs/initial_materials/L03_slaidikandidaat.origin.md`](initial_materials/L03_slaidikandidaat.origin.md) — slaidikandidaadi teadaolev päritolu, struktuur, kontrollsumma ja kasutuspiir.
- [`docs/initial_materials/L03_transkript_teine_AI.md`](initial_materials/L03_transkript_teine_AI.md) — kasutaja antud, faili kirjelduse järgi videoloengu automaatsubtiitritest tundmatu AI-ga korrastatud loengu 3 täistranskript; subtiitrite süsteem ja platvorm ning toimetusmudel on teadmata, seost Echo360-ga ei ole tuvastatud ja materjal ei ole kinnitatud referents.
- [`docs/initial_materials/L03_transkript_teine_AI.origin.md`](initial_materials/L03_transkript_teine_AI.origin.md) — kasutaja antud transkripti päritolu, kontrollsumma ja kasutuspiir.
- Echo360 avalik kursuselink, kursuse metaandmed, loengusalvestised ja slaidid.
- `err_video_to_text` dokumentatsioon ja kood ainult nende komponentide analüüsimisel, mida käesolevas projektis soovitakse taaskasutada.
- `/home/ubuntu/fun_o/nginx/default.conf` ja `/home/ubuntu/fun_o/docker-compose.yml` ühise nginx-veebiserveri või `funo_net` võrguga integratsiooni kavandamisel ja muutmisel.

### Teostuse põhilised allikad

- [`src/lecture_notes/echo360.py`](../src/lecture_notes/echo360.py) — Echo360 avalik sessioon, kursuse resolver ja olekute normaliseerimine.
- [`src/lecture_notes/config.py`](../src/lecture_notes/config.py) — välise runtime-kataloogi seadistus ja väljunditee kontroll.
- [`src/lecture_notes/manifests.py`](../src/lecture_notes/manifests.py) — loengu-, meedia- ja slaidimanifestid ning atomaarne kirjutamine.
- [`src/lecture_notes/cli.py`](../src/lecture_notes/cli.py) — konteineris kasutatava CLI käsud.
- [`src/lecture_notes/asr_benchmark.py`](../src/lecture_notes/asr_benchmark.py) — ASR-i lukustatud kontrollkomplekti töötlus, kogu loengu ajastatud transkriptsioon, kvaliteedimõõdikud ja ressursimõõtmine.
- [`compose.yaml`](../compose.yaml) ja [`Dockerfile`](../Dockerfile) — importeri konteinerpakendus.
- [`Dockerfile.asr`](../Dockerfile.asr) — Faster-Whisperi sõltuvustega eraldatud ASR-workeri konteinerpakendus.
- [`Dockerfile.pipeline`](../Dockerfile.pipeline) — PDF-i, video, OCR-i ja Etapp 3 töötluse eraldatud konteinerpakendus.
- [`src/lecture_notes/stage3.py`](../src/lecture_notes/stage3.py) — Etapp 3 ainekava, allikate joondamise, tõendite ja peatüki töövoog.
- [`benchmarks/datasets/lecture3_v1.json`](../benchmarks/datasets/lecture3_v1.json) — loengu 3 lukustatud ASR-kontrollkomplekti masinloetav kirjeldus.
- [`benchmarks/evidence/l03_3e_v1.json`](../benchmarks/evidence/l03_3e_v1.json) — Etapp 3 esimese vertikaalse proovi auditeeritav tõendi- ja slaidivalik ning teadaolev katvuslünk.
- [`.env.example`](../.env.example) — runtime’i, konteineri kasutaja ja kodukataloogi seadistuse mall.
- [`tests/test_echo360.py`](../tests/test_echo360.py) — olekuloogika võrguvabad kontrollid.
- [`tests/test_asr_benchmark.py`](../tests/test_asr_benchmark.py) — ASR-i kvaliteedimõõdikute võrguvabad kontrollid.

Registrit tuleb täiendada kohe, kui projektile lisandub README, andmeskeem, API leping, konteinerite kirjeldus, hindamisandmete register või muu asjakohane allikas. Registrisse kuulumine ei anna allikale teiste ees ülimuslikkust.

## 10. Millal mida kindlasti lugeda

- Enne igat sisulist vastust loe vähemalt käesolev juhend ja ülesandega seotud põhidokumendi osad; koodi olemasolul kontrolli vastavat teostust.
- Kui muudad rakenduse eesmärki, ulatust, väljundeid või vastuvõtukriteeriume, loe `docs/lahteylesanne.md` ja `docs/tehniline_spek.md`.
- Kui muudad arhitektuuri, andmemudelit, tööde järjekorda, konteinerite vastutusi või ressursikasutust, loe `docs/tehniline_spek.md`, asjakohane konfiguratsioon ja kogu mõjutatud töötlusahel.
- Kui muudad avalikku hostinime, TLS-i, pöördproksit, veebiliidese serveerimist või ühise Docker-võrgu kasutust, loe enne `/home/ubuntu/fun_o/nginx/default.conf`, `/home/ubuntu/fun_o/docker-compose.yml` ja mõlema mõjutatud projekti juurutusdokumentatsioon.
- Kui muudad Echo360 resolverit või meediaallikate salvestamist, kontrolli toimivat avaliku sessiooni loomise voogu, tegelikke võrgupäringuid ja olemasolevaid resolveri artefakte.
- Kui muudad ASR-i, diariseerimist või tekstisegmentide sidumist, loe vastavad mudeli- ja hindamisdokumendid, olemasolev teostus ning kontrollandmed. `err_video_to_text` taaskasutuse korral loe enne selle projekti asjakohased allikad.
- Kui muudad konspekti sünteesi, loe ainekava, näidiskonspekt, allikate andmemudel ja vähemalt üks tegelik transkriptsiooni/slaidide komplekt.
- Kui kasutad protsessiandmeid kvantitatiivseks analüüsiks või mudeli õpetamiseks, peab enne olema dokumenteeritud andmete kasutusluba ja hindamiskomplekti ulatus.

## 11. Väljundi ootused

- Kui töö sisaldab vea parandust, too kokkuvõttes eraldi välja juurpõhjus ja paranduse loogika.
- Kui töö tugineb oletusele, nimeta oletus selgelt ning küsi enne muudatuse tegemist luba.
- Kui avastad allikate vahel lahknevuse, peata seda küsimust puudutav sisuline töö kohe, too vastuolu välja ja küsi enne jätkamist täiendavaid juhtnööre. Vastuolu ei tohi jätta ainult töö lõpu kokkuvõttesse.
