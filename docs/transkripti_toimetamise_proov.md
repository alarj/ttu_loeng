# Transkripti toimetamise proov

## 1. Dokumendi päritolu

Koostaja: AI (OpenAI Codex), kasutaja kinnitatud töövoo, valminud TalTechNLP täistranskripti ja projekti tehnilise spetsifikatsiooni põhjal. Katsetulemusi ei ole inimene veel sisuliselt kinnitanud.

## 2. Sisukord

- [3. Eesmärk](#3-eesmärk)
- [4. Katse](#4-katse)
- [5. Ülevaatus](#5-ülevaatus)

## 3. Eesmärk

Katse eesmärk on kontrollida, kas EstLLM suudab muuta TalTechNLP automaattranskriptsiooni lihtsa juhise põhjal normaalseks kirjakeelseks tekstiks. Algne ajatemplitega transkript jääb muutmata.

## 4. Katse

Esimeses proovis kasutatakse loengu algusest ligikaudu kahe ja poole minuti pikkust järjestikust tekstilõiku. Tehnilised ASR-segmendid ühendatakse enne mudelile andmist üheks tavaliseks tekstiks.

Prompt on:

> See on automaatne loengu transkriptsioon -- koostatud salvestise põhjal.
> Koosta selle alusel normaalne kirjakeelne tekst, eemalda tarbetud kordused ja vaata üle lauselõpud.
> Säilita erialaterminid ja ingliskeelsed terminid.

Mudel tagastab tavalise teksti. Katse kasutab kohalikku EstLLM-i ning töötab asünkroonselt projekti Ollama teenuses.

## 5. Ülevaatus

Esimene lihtne katse lõpetas edukalt 7 minuti ja 50 sekundiga. Tulemus oli loetav, kuid jättis välja terminid `disaster recovery` ja `Enterprise Risk Management`. Sama lähtetekstiga korduskatse lisas prompti nõude säilitada erialaterminid ja ingliskeelsed terminid ning lõpetas 7 minuti ja 53 sekundiga. Mõlemad terminid säilisid ja toimetatud tekst oli loetav. Tulemus ootab inimese kinnitust enne järgmiste lõikude või kogu loengu töötlemist.
