# ICM0032 IT valitsemine ja juhtimine — Loeng 3

## Talitluspidevuse ja avariitaaste planeerimine (Business Continuity and Disaster Recovery Planning)

*Korrastatud täistranskript. Videoloengu automaatsubtiitrid on toimetatud täislauseteks ja loogilisteks lõikudeks; täitesõnad, kordused ja kõrvalised vahelesegamised on eemaldatud, sisu on säilitatud täies mahus. Nurksulgudes on toimetaja märkused. Vahepealkirjad on lisatud lugemise hõlbustamiseks ja järgivad slaidide järjekorda.*

---

### Sissejuhatus

Kursuse järgmine osa on *business continuity and disaster recovery planning*, eesti keeles äri talitluspidevuse ja avariitaaste planeerimine. Need valdkonnad on strateegia väljatöötamise mõjutamisel üsna olulised ja neid me järgnevalt vaatame. Alustame talitluspidevusest (*business continuity*).

### Kindluse mentaliteet (*fortress mentality*)

Siin on veel kord kindluse mentaliteet. Me eeldame, et meil on ilus loss, selle ümber on kõikvõimalikud vallid ja kraavid ning siin midagi halba juhtuda ei saa. Kui analüüsida, mis on selle häda tänapäeva mõttes, siis kogu see asi on staatiline. Kõik, mida selle parandamiseks või tõhusamaks tegemiseks võiks ette võtta, võtab hirmus palju aega. Kõik protsessid on väga aeglased ja seetõttu ka mitte eriti tõhusad ega efektiivsed. Me peame tegema suuri kulutusi selleks, et saada üsna vähe turvalisust.

Me elame tänapäeval kiiresti muutuvas maailmas. Seetõttu peame ohtudega võideldes arvestama, et maailm ei ole enam selline nagu mõned sajandid tagasi. Kui loss ehitati, siis võisid vaenlased mitusada aastat ainult selle ümber käia ja oodata. Tänapäeval muutub kõik kiiresti ning ohud, mis homme tekivad, võivad kõikidest vallidest ja kraavidest üle saada. Me peame muutuva keskkonnaga kiiresti kohanema — see on meile kindlasti vajalik.

Meie ressursid on kindlasti väga piiratud. Vaadake neid lossiehitajaid ja seda, mida nad endale kokku on ehitanud. Olen väike matkaja ja olen Euroopas näinud mõnda lossi, mis on ehitatud sellise mäe otsa, et ei kujuta ettegi, kuidas sinna üldse minna, rääkimata sellest, kuidas sinna kõik need kivid on veetud. Päris imesarnane. Selliseid ressursse meil loomulikult ei ole. Me peaksime suutma end kaitsta suhteliselt vähe kulutades, kuid väga tõhusalt. Efektiivsus on meile väga tähtis.

### Talitluspidevuse ajalugu

Talitluspidevuse ajalugu ei ole inimkonna ajalooga võrreldav ega väga pikk. Kunagi alustati küsimusest, mida teha siis, kui meie põhiarvutuskeskus ei toimi. Mida peale hakata, kui meie süsteemid on kokku kukkunud? Mida oleks võimalik ette võtta?

Seejärel hakati vaatama ärilist taastamist ehk seda, mida me nimetame *disaster recovery*'ks. See puudutab IT-süsteeme ja muid tehnilisi lahendusi. Algselt mõeldi, kuidas äri veel ajada, kui meie põhilised äritegemise viisid ei kõlba. Kuna tehnikale oli juba küllalt suurt rõhku pandud, vaadati seejärel, millised võiksid olla tehnilised plaanid, mis võimaldaksid hädaolukordadest üle saada.

Edasi — samamoodi, nagu eelmises osas vaatasime ettevõtte riskijuhtimist (*enterprise risk management*) — hakati tegema kogu ettevõtet hõlmavaid plaane, et tagada ettevõtte toimimine ja jätkusuutlikkus. Kõige viimane tase, mis iseloomustab tänapäeva, on see, et meil on olemas plaanid kõikideks olukordadeks ning need on terviklikud, kontrollitud ja testitud.

See näitab, et algselt mõeldi ettevõtte üksikute külgede töö tagamisele, kuid lõppkokkuvõttes on jõutud ettevõtte tervikliku käsitluseni, et suuta igasuguste äparduste, õnnetuste, rünnete ja muu puhul tagada ettevõtte toimimise jätkusuutlikkus.

### Riskiahel: enne ja pärast sündmust

Siin on veel kord pilt, mida näitasin teile ka eelmises osas. Eelmises osas pühendusime peamiselt sellele, mida teha enne, kui mingi halb sündmus toimub: püüda minimeerida selle tõenäosust ja vähendada võimalikult palju kahju, kui halb sündmus aset leiab.

Selles osas keskendume sellele, mida teha siis, kui halb sündmus on ikkagi aset leidnud. Esiteks: kuidas olla võimalikult tõrkekindel ja taluda võimalikult hästi lööke, mida kuri saatus meile saadab. Teiseks: kui oleme pihta saanud, kuidas oleks võimalik oma toimivus võimalikult kiiresti taastada, kas või osaliselt. Kui me ei suuda end täielikult taastada, siis kuidas suudaksime taastada vähemalt oma põhifunktsioonid.

### Talitluspidevuse halduse eesmärk

Talitluspidevuse halduse (*business continuity management*, BCM) illustreerimiseks on meil ühel teljel ärivõimekus ja teisel teljel aeg. Roheline joon näitab, et kõik läheb väga hästi: meie äriline võimekus kasvab ilusti, kuid siis toimub mingi halb sündmus, mis lööb meid vähemalt ajutiselt rivist välja. See pilt kujutab olukorda, kus talitluspidevuse haldus on paigas: kõik on korras ja testitud, kõik plaanid on olemas. Meil on väike ajutine tagasilöök, kuid kosume kiiresti ja jätkame teed paremate äriliste saavutuste poole.

Teine variant on see, kui talitluspidevuse haldus puudub. Siis võib arvata, et halb sündmus lööb meid rivist välja palju tõsisemalt. Meie äriline võimekus väheneb väga oluliselt, võib-olla isegi nullini, ja taastumine — isegi kui see mingil määral toimub — ei ole piisav. Võib juhtuda, et ettevõte on sunnitud tegevusest üldse loobuma. Ka see ei ole haruldane, et katastroofid või hädaolukorrad mõjutavad ettevõtet nii, et see ei suudagi oma tegevust jätkata. Siin on mingi kriitiline punkt: kui ettevõte ei ole suutnud saavutada teatud võimekust, kas esialgset või vähemalt mingit mõõdetavat, võib tema edasine toimimine olla küsimärgi all.

Võimalik on ka kolmas stsenaarium: ettevõttel ei ole talitluspidevuse plaane, kuid mõnel inimesel ja mõnel ettevõttel veab. Selliseid õnnelike õnnetuste näiteid on olemas. Talitluspidevuse plaanide puudumine ei pruugi tingimata tähendada lõplikku katastroofi — see võib kuidagi hästi minna ja mõnel lähebki. Aga võib ka halvasti minna. Parem on, kui orienteerime oma ettevõtte vähemalt teoorias rohelisele joonele, mitte punasele, lootes, et äkki realiseerub kollane. Siin on kõik valgusfoori tunnused olemas.

### Talitluspidevuse halduse põhikomponendid

Näete, millised on talitluspidevuse halduse põhikomponendid. Esimene osa on väga sarnane riskihaldusele ehk meie kursuse eelmisele osale ja teatud määral isegi sisaldab seda. Selles talitluspidevuse tagamise protsessis on meil tegemist asjaga, mida nimetatakse *business impact analysis* (BIA) — äriliste mõjude analüüs. See on teatud mõttes riskihindamise (*risk assessment*) paariline, kuid pisut teisest vaatenurgast.

Üldiselt peaks äriliste mõjude analüüs koos riskihindamisega näitama meile kõikide halbade olukordade puhul, millised võiksid olla tagajärjed. Paljudel juhtudel, kui mitte enamikul, ei ole need tagajärjed meile vastuvõetavad. Riskihalduses oli meil ka stsenaarium, kus me ei teinud midagi ja lihtsalt aktsepteerisime riske. Põhimõtteliselt on ka siin võimalus aktsepteerida, kuid kui vaatame, millised oleksid meie kriitiliste sündmuste ärilised tagajärjed, saame määratleda nõuded, mis tuleks püstitada oma äritegevuse kaitsmiseks.

Siin ongi kaks valdkonda: kas tugevdada kontrolle, mis on riskihalduse põhimõtete rakendamine, või teha talitluspidevuse planeerimist (*business continuity planning*), mis seisneb selles, et mõtleme välja, mida teeme siis, kui oleme pihta saanud. Vasak pool tähendab, et püüame mitte pihta saada ja mitte valu tunda; parem pool — kuidas valust üle saada.

Äri talitluspidevuse puhul püüame analüüsida, mis halba võiks ikkagi juhtuda, ja anda sellele hinnangu. Seejärel planeerime, mida ette võtta: kas leida kaitsemehhanisme, mis ei lase halval olukorral tekkida, või leida, mida teha, et halvast olukorrast võimalikult kiiresti ja tõhusalt üle saada. Need on kaks teed.

### Talitluspidevuse planeerimine ja selle kolm jalga

Vaatame nüüd, mis kuulub talitluspidevuse planeerimise hulka. See on äärmiselt mahukas ettevõtmine. Usun, et teid ei üllata, et pankadelt nõutakse selles osas väga palju. Finantsinspektsioon ei laseks meil hetkekski lõdvestuda, kui mõni asi, mida ta on ette näinud, oleks tegemata. See kõik on vajalik, sest pangad on Eesti Vabariigis äärmiselt tähtsad ettevõtted, elutähtsa teenuse osutajad. Muide, kolm Eesti panka on nimeliselt elutähtsa teenuse osutajate nimekirjas: Swedbank, SEB Eesti ja Luminor. Ülejäänud pangad ei kuulu elutähtsa teenuse osutajate hulka, mis tähendab, et nende jaoks ei ole nii riskihalduse kui ka eriti talitluspidevuse nõuded nii karmid. Ülejäänutel on suhteliselt vabam elu.

Kohustuslikke plaane on mitmesuguseid. Sellel taburetil on talitluspidevuse planeerimine, mis toetub järgmistele jalgadele. Esimene on hädaolukorrale reageerimine (*emergency response*): kui on mingi häda tekkinud, mida tuleb kõigepealt kiiresti ette võtta. Keskel on äritegevuse jätkamine (*business resumption*), mis on kõige viimane faas: püüame taastada algse olukorra. Vahepeal on avariitaaste (*disaster recovery*) — see roheline jalake —, mis on suunatud peamiselt IT-le: taastada infrastruktuur, rakendused, andmed, kogu tehniline pool.

Seega, kui vaatame talitluspidevust, siis see osa, mis otseselt IT-d puudutab, on avariitaaste. Äritegevuse jätkamine ja hädaolukorrale reageerimine on need talitluspidevuse osad, mis on äripoole vastutusel: äripool peab neid plaanima, harjutama, treenima ja läbi viima.

### Reageerimise ja taastamise faasid

Siin on lihtsustatud ajaline esitus. Kui midagi halba on juhtunud, mida siis tuleks teha? Kõigepealt on hädaolukorrale reageerimine: kiiresti tuleb midagi ette võtta. Siin on kõige olulisem, et unustame kõik tehnilised seadmed ja muud väärtused ning pühendume sellele, mis on kõige tähtsam — inimeludele. Kui on juhtunud õnnetus, mis seab ohtu inimelud, siis on esikohal ohutus (*safety*). Eriti selgeks saab see, kui mõtlete laevale. Kui laevaga midagi juhtub, on reisijate ohutus kõige kõrgema prioriteediga; kõik muu tuleb hiljem.

Hädaolukorrale reageerimine sisaldab lisaks elude päästmisele, mida püütakse teha kohe, ka arusaamise tekitamist sellest, mis õieti juhtus. Neid ajalisi parameetreid ärge võtke väga tõsiselt, sest need sõltuvad väga palju sellest, kui suur on ettevõte, millises riigis ta asub ja millises valdkonnas ta tegutseb. See on ainult näide — slaid on kopeeritud ja mingi konkreetse ettevõtte puhul võiksid need olla sellised. Võin teile kunagi rääkida, millised need on SEB Eesti puhul, kuid need sõltuvad väga palju ettevõttest, tema suurusest, tegevusvaldkonnast ja muust.

Kui oleme halvale olukorrale esmaselt reageerinud — püüdnud päästa inimesi, seejärel võib-olla ka seadmeid, ja kuidagi leevendada juhtunut —, siis järgmisena peaksime vaatama lühiajalist taastamist (*short-term recovery*). Kuidas leida võimalus taastada kõige olulisem funktsionaalsus? Seda nimetatakse sageli ka möödapääsuks (*workaround*) ehk alternatiivseks lahenduseks. Paljudel juhtudel tähendab see alternatiivsete töökohtade kasutamist. Näiteks kui raalinduskeskus, kus serverid asuvad, ei ole käideldav ja on rivist väljas, kolitakse lihtsalt sekundaarsesse raalinduskeskusesse. Kunagi tuleb päevakorda ka esialgse olukorra taastamine.

Meil on seega kaks või isegi kolm olulist taastamise sammu. Kõigepealt vaadata, et katastroof edasi ei hargneks, ja püüda vältida selle edasist levikut. Seejärel leida möödapääs ehk alternatiivne lahendus, et kas või osaliselt oma funktsioone täita. Lõpuks taastada need funktsioonid, mis meil algselt olid.

### Situatsiooniplaneerimise neli R-i, RTO ja RPO

**See pilt, mida praegu näete, on praktiliselt selline, mida peaksite oskama eksamil reprodutseerida.** Eksamiks vajalikke asju ei ole väga palju, kuid see on üks neist. Graafiliselt näitab see seda, millest ma juba rääkisin.

Näete: *business as usual* — äri toimub nii, nagu ta toimus. Nüüd toimub — see punane asi — midagi halba. Meie äriline võimekus langeb oluliselt. Millega on meil tegemist? Meil on intsidendihaldus: toimus intsident ja me peame sellele reageerima ehk meil on hädaolukorrale reageerimine. Intsidendihalduse protsessi tulemusel oleme võimelised käivitama alternatiivse äriprotsessi — võib-olla teises, sekundaarses asukohas, võib-olla hoopis kuidagi teistmoodi. Mõnel juhul on äripool näiteks võimeline tegema tööd pliiatsi ja paberiga.

Olin 1999. aastal Eesti Ühispanga aasta 2000 projekti projektijuht, kuna see puutus minu valdkonda. Testisime eraldi kõiki seadmeid, et näha, mis nendega võiks juhtuda, kui aastaarvu kaks viimast numbrit muutuvad 99-st 00-ks, sest paljudes süsteemides olid algselt ainult kahekohalised aastaarvud. Tegelikult ei juhtunud midagi, kuid saime oma seadmetest väga põhjaliku inventuuri ja kõiki seadmeid testiti ka eraldi. Mul oli pikk riiul testimisprotokolle täis, iga protokoll omaette kaustas.

Mis oli aasta 2000 oodatava hädaolukorra puhul erilist? Selle erilisus seisnes selles, et oli täpselt teada, millal see saabub: siis, kui 1999 muutub 2000-ks — nüüd võivad süsteemid lolliks minna. Tavaliselt ei tea keegi meist, millal halb sündmus aset leiab. Aasta 2000 ettevalmistuste hulgas oli näiteks see, et kõikides Ühispanga kontorites prinditi õhtul välja kõikide eraisikute kontode seisud. Tellerid olid valmis küünlavalgel inimestele raha välja andma. See oli võimalik, sest teadsime täpselt, millal halb sündmus võib aset leida, kui see üldse leiab. Tegelikult ei juhtunud midagi. Üldiselt on talitluspidevuse puhul aga olukord selline, et me ei tea, millal see plahvatus ehk halb sündmus aset leiab.

Pange tähele, et sellel pildil on veel üks asi, millest kohe pikemalt räägime: RTO ehk *recovery time objective* — taasteaja eesmärk. See on väga oluline parameeter, kui tahame mingit protsessi planeerida. Kui tahame realiseerida mingit äriteenust, peame ette nägema, millise aja jooksul suudame hädaolukorra korral midagi alternatiivset käivitada.

Aastal 2000 oli olukord, kus pangasüsteem ei töötanud, ja alternatiivne protsess oli anda välja sularaha küünlavalgel väljatrükitud kontosaldode järgi. Kõikide äriprotsesside planeerimisel, loomisel ja arendamisel peame määrama, millise aja jooksul peaksime hädaolukorra korral suutma selle protsessi puhul alternatiivse protsessi käivitada. Teie kui tulevased arhitektid peate ülesande püstitamisel arvestama, et see on strateegiline parameeter: kauem ei tohi see protsess maas olla.

Muidugi, mis siis teha, kui ta on ikkagi kauem maas? Näiteks on meil küllalt selge piir: kui meie pangakaardid ei ole meie süül käideldavad kauem kui pool tundi ehk 30 minutit, peame andma pressiteate. Siis oleme väga pahad — oleme ise enda peale kurjad ja kõik ülejäänud on meie peale ka kurjad.

Pärast RTO-d peab olema käivitunud alternatiivne äriprotsess, mis on väiksema võimekusega: midagi osalist, võib-olla mitte täielikku, võib-olla aeglasemat — osalise võimekusega äriprotsess. Kui see protsess on käima pandud, vabanevad ressursid, mis olid alguses hõivatud hädaolukorrast kiire ülesaamise, intsidendihalduse ja seejärel alternatiivse protsessi käivitamisega. Nüüd alustame esialgse protsessi taastamist (*business resumption*) ja see viib meid tagasi *business as usual* seisu.

Kokkuvõttes: toimub halb sündmus; avariitaaste ajaks on taasteaja eesmärk; mingist hetkest alates käivitatakse alternatiivne protsess; algab äritegevuse jätkamine ja lõpuks taastame esialgse olukorra.

Siia on lisatud ka sõnade võimalikud tõlked: *resume* — uuesti algatama, jätkama (*business resumption*); *recover* — ellu ärkama, paranema; *restore* — ennistama, taastama.

Eriti tähtis on siin *recovery time objective*: ajavahemik, mille jooksul süsteemid, rakendused või funktsioonid tuleb pärast katkestust taastada. *Recovery* tähendab siin, et need võivad töötada ka osalise funktsionaalsusega.

On ka teine oluline parameeter, mis on slaidil heledamalt, sest see on pisut — mitte palju — vähem tähtis: *recovery point objective* (RPO) — taastepunkti eesmärk. Praktiliselt, mitte definitsioonina, tähendab see seda, kui kaua aega tagasi on tehtud viimane varukoopia. Teiste sõnadega: kui räägime pangast, kui palju tehinguid võib viimasest varukoopiast alates kaduma minna? Paljudel juhtudel, eriti finantsasutuste puhul, on RPO null — midagi ei tohi kaduma minna. Mõnel juhul on see aga võimalik.

Siin on väike tabel. *Contingency* — ettenägematu asjaolu; *contingency planning* — situatsiooniplaneerimine. Need on enam-vähem ametlikud tõlked. Talitluspidevuse planeerimise osad on avariitaaste (*disaster recovery*), äriline taastamine (*business recovery*), äritegevuse jätkamine (*business resumption*) ja situatsiooniplaneerimine (*contingency planning*). Nende eesmärgid on vastavalt: avariitaastel kriitilised arvutirakendused, ärilisel taastamisel kriitilised äriprotsessid, äritegevuse jätkamisel äri ennistamine ja situatsiooniplaneerimisel protsessi möödapääs. Seda tabelit ei ole vaja pähe õppida ja see ei ole eksami osa, kuid võite sellele pilgu heita. Väikesel pildil olev on aga suures osas eksami osa.

### Talitluspidevuse dokumendid

Siin on näha, millised peaksid olema IT ja äri dokumendid. Sündmusest taastumise poolel on IT-l avariitaaste plaan (*disaster recovery plan*), IT situatsiooniplaan (*IT contingency plan*) ja küberintsidendile reageerimise plaan (*cyber incident response plan*). Talitluspidevuse poolel on äril talitluspidevuse plaan (*business continuity plan*) ja pikemaajaliste katkestuste jaoks tegevuse jätkamise plaan (*continuity of operations plan*).

Pange palun tähele, et olen siia tabelisse pannud sellise punase ratta: IT-l tegelikult ei ole talitluspidevuse plaani. IT-l on peamiselt avariitaaste plaan ehk hädaolukorrast taastamise plaan.

### ERM ja BCM — ajendid

Siin on mingil määral võrreldud ettevõtte riskijuhtimist (ERM) ja talitluspidevuse haldust (BCM). Mõlemad tegelevad halbade asjade juhtumisega. Vaadeldud on tervet rida atribuute — vastavus regulatsioonidele (*regulatory compliance*), maine kaitse (*reputation protection*) jne —, mida ei ole vaja pähe õppida. Ettevõtte riskijuhtimine käsitleb kõiki tabelis olevaid atribuute.

Vaatame, mida talitluspidevuse haldus ei käsitle. BCM ei vaatle äri ja IT joondamist (*business-IT alignment*) ega programmide ja protsesside tõhusust (*program/process efficiencies*) — efektiivsus on sekundaarne, kõige olulisem on taastada funktsionaalsus. Samuti ei vaatle BCM kapitali optimeerimist (*capital optimization*) ehk seda, kuidas ressursse ja kapitali võimalikult tõhusalt kasutada.

Ja siis riski tõenäosuse haldamine (*manage risk likelihood*). Kõikide riskihaldusmeetodite puhul arvestame riskide prioritiseerimisel seda, et korrutame mõju — kui palju võime kahju saada — tõenäosusega. Kuigi kahju võib olla suur, on risk suhteliselt väike, kui tõenäosus on väga väike. Olete nõus? **Talitluspidevuse plaane tehes me aga mõju tõenäosusega läbi ei korruta. Kui võime saada suurt kahju, peab meil olema talitluspidevuse plaan olenemata sellest, millise tõenäosusega see sündmus võib aset leida.** On arusaadav? See alumine rida on kõige olulisem. Ülejäänud võite lasta ühest kõrvast sisse ja teisest välja, kuid seda on väga oluline tähele panna.

Muide, sedasama loogikat kasutavad paljudel juhtudel ka audiitorid, kes annavad auditileidudele hinnangu, kas tegemist on kriitilise, katastroofilise või kergema sündmusega. Reeglina ei vaata auditid ka paljudel juhtudel puhtalt riskihalduse vaatenurgast, kui tõenäoline ühe või teise halva sündmuse esinemine võiks olla.

### Reageerimise tasemed

Intsidentide astmestus on üsna lähedane sellele, mis oli ettevõtte riskijuhtimise puhul. Vaatame intsidente, mis on seotud strateegiliste plaanide täitmisega — ehk intsidente, mis mõjutavad otseselt strateegilisi plaane —, intsidente, mis mõjutavad taktikalisi plaane, ja neid, mis mõjutavad meie igapäevast toimimist. See on lihtsustatud. On selge, et olenevalt hädaolukorra astmest on meil ka erinevad meeskonnad, kes seda haldavad — kriisimeeskonnad sõltuvalt kriisi olemusest.

### Standardid ja PDCA tsükkel

Vaatasime ühte slaidi, kus oli väga palju seadusi, määrusi ja standardeid, mis mõjutavad suuremal või vähemal määral talitluspidevuse käsitlust. Nagu sellelt slaidilt näete, on 22300 seerias ka kolm standardit, mis on otseselt suunatud talitluspidevusele. Neid numbreid ei ole vaja eksamiks meelde jätta, kuid teadmiseks: ISO 22301 määrab, milliseid nõudeid esitatakse talitluspidevuse juhtimissüsteemile, ISO 22313 annab juhised ja on ka tehnilised spetsifikatsioonid.

Nagu kõikjal IT-s — ja mitte ainult, vaid ettevõtetes üldiselt —, kasutatakse ka siin Plan-Do-Check-Act ratast ehk tsüklit, mis pärineb Edwards Demingilt 1950. aastate Jaapanist. Seda kasutavad väga paljud IT juhtimise materjalid, nii standardid kui ka muud vahendid. See on üldine skeem protsesside parendamiseks: teha plaan, viia see ellu, vaadata, mida saavutasime, ja vajaduse korral plaani korrigeerida. PDCA-d kasutatakse IT-s ja ettevõtetes üldiselt väga laialdaselt ning konkreetselt ka talitluspidevuse puhul.

On selge, et peame millestki lähtuma. Lähtume sellest, et peame oma ettevõtte protsesside analüüsi põhjal koostama esialgse talitluspidevuse plaani. Seejärel tuleb see plaan rakendada. Talitluspidevuse ning hädaolukorra- ja kriisiplaanide puhul on väga oluline, et need plaanid oleksid reaalselt testitud ja et nende järgi oleks toimunud õppused.

Kui räägime näiteks tarkvaraarendusest, siis mingit toimingut tehes on meil tõenäoliselt aega mõelda, kas teeme nii või naa, pidada aru, kaaluda alternatiive ja teha lahendusi ilma suurema kiirustamiseta. Hädaolukordade ja kriiside lahendamisel ei ole aga reeglina enam aega mõelda. Mõtlemine tuleb teha varem ning kinnistada see treeningute ja õppustega. Oluline on, et inimesed toimiksid tõhusalt, hästi ja väga kiiresti. Pikaks mõtisklemiseks, kas teha nii või naa, reeglina aega ei ole ja seetõttu ongi treeningud, õppused ja kõikide asjade praktiline läbitegemine väga olulised.

Siin on näidatud, mida ISO 22301 PDCA tsükkel endas sisaldab. *Establish* ehk *Plan*: kehtestada talitluspidevuse poliitika, eesmärgid, sihid, kontrollid, protsessid ja protseduurid. *Implement* ehk *Do*: rakendada ja käitada talitluspidevuse poliitikat, kontrolle, protsesse ja protseduure. *Monitor and review* ehk *Check*: jälgida ja üle vaadata tulemuslikkust võrreldes talitluspidevuse poliitika ja eesmärkidega. *Maintain and improve* ehk *Act*: vajaduse korral parendada. Iseenesest on see üsna sirgjooneline, ilma kavalusteta Demingi tsükli rakendamine selles keskkonnas.

### NIST SP 800-34

Siin on viidatud — seda ei ole vaja pähe õppida — ühele USA riikliku standardite ja tehnoloogia instituudi (NIST) standardile, antud juhul SP 800-34. Viitan sellele peamiselt seetõttu, et NIST-i välja antud standardid on paljudes IT valdkondades — infoturve, talitluspidevus, küberkaitse ja paljud teised — äärmiselt head. Need on lakoonilised ja väga selge väljendusega ning paljudele inimestele, sealhulgas mulle, meeldivad need võib-olla rohkemgi kui Euroopas traditsioonilisemad ISO standardid. Pidage meeles, et paljudel juhtudel saab asja palju paremini selgeks just NIST-i standardeid vaadates.

Siin on ring, mis näitab, kuidas talitluspidevuse plaani koostada. Siin on küberintsidendile reageerimise plaan (*cyber incident response plan*), IT situatsiooniplaan (*IT contingency plan*), avariitaaste plaan (*disaster recovery plan*), äritegevuse taastamise või jätkamise plaan (*business recovery/resumption plan*), kriisikommunikatsiooni plaan (*crisis communication plan*) ja hoones viibijate hädaolukorra plaan (*occupant emergency plan*). Need plaanid on standardis täpsemalt kirjeldatud. Kui ettevõte vajab ühe või teise valdkonna lakoonilist, kuid kõikehõlmavat käsitlust, on see väga hea. Siniselt on märgitud need, mis puudutavad IT-d: küberintsidendile reageerimine, IT situatsiooniplaan ja avariitaaste plaan. Ülejäänud puudutavad äri ja mitmesuguseid muid vahendeid.

### Standard kui kristalliseerunud kogemus

Millised peavad olema talitluspidevuse plaanid ja millistest osadest need peaksid koosnema? On arusaadav, et siin on väga pikk praktika. Seda peetakse igat tüüpi organisatsioonidele nii tähtsaks, et on proovitud nii ühtmoodi kui ka teistmoodi.

Mis on standard? Standard ei ole midagi muud kui kristalliseerunud kogemus. Kui teete midagi hästi, näiteks korraldate oma lapse sünnipäeva, ja olete väga põhjalik, võite üles kirjutada, mida tegite hästi ja mida halvasti. Kui laps saab aasta vanemaks, õpite sellest ja teete paremini. Kui hakkate aasta-aastalt lapse sünnipäevi järjest õigemini, korrektsemalt ja meeldivamalt korraldama, võib öelda, et olete loonud oma pere praktika. Kui võtaksite kokku mingi linna lapsevanemad, analüüsiksite, kuidas lapse sünnipäeva pidada, ja töötaksite välja üldise kokkuleppe ehk tava, võiks öelda, et olete loonud selles linnas kehtiva lapse sünnipäeva standardi. Kui üldistate seda veel riigile ja lõpuks kogu maailmale, olete saanud lapse sünnipäeva pidamise üldkehtiva standardi. Paljud standardid ei olegi midagi muud ja nii tulebki neisse suhtuda: need on kristalliseerunud ja üldistatud kogemused. Tavaliselt on olemas mingi standardit kehtestada võiv organ (*standard body*), näiteks NIST või ISO (*International Organization for Standardization*).

### Talitluspidevuse planeerimise viis faasi

Talitluspidevuse puhul on viis lihtsat sammu. Väga oluline on algus — kuidas seda asja teha. Riskihalduse puhul nimetasime seda kontekstiks: määrata keskkond, milles talitluspidevuse plaani rakendatakse.

Seejärel on kesksel kohal äriliste mõjude analüüs (*business impact analysis*), mis vastab teatud mõttes riskide määratlemisele — riskihindamisele. Mis on äriliste mõjude analüüs? Midagi halba juhtub — mida see meie ärile tähendab? See analüüsisamm on väga tähtis, sest selle põhjal saame teada, kui hullu asjaga on tegemist. Siin tahame kindlaks teha, kui ohtlik ja halb see on ning milline on äriline mõju. Kui ärimõju on väike, ei pea me suurt midagi tegema. Kui ärimõjud on suured ja protsessid kriitilised, nii et nende katkemine oleks ettevõttele ohtlik, peame reageerima väga kiiresti.

Vastavalt BIA väljundile peame määratlema, kuidas edasi toimime: millised on meie äriprotsesside taastamise strateegiad, mida tegelikult tahame saavutada, millised on eesmärgid ja kõige üldisemalt nõuded neile protsessidele. Seejärel tuleb planeerida, kuidas peaksime toimima.

Viimane samm on testimine, hooldus, teadlikkus ja koolitus. Teadlikkus tähendab siin, et väga paljud inimesed peavad vajaduse korral osalema talitluspidevuse plaanide reaalses elluviimises. On selge, et sellest ei piisa, kui inimesed on vastava raamatukese või eeskirja läbi sirvinud. Kindlasti on vaja, et kõik oleksid selle ka reaalselt ja praktiliselt läbi teinud. Kuna võib arvata, et sellised mälestused väga kaua ei püsi, tuleb õppusi korrata kord või mitu korda aastas, olenevalt sellest, kui kriitiliste protsessidega üks või teine inimene, inimeste rühm või osakond tegeleb. Samuti on vaja testida nii seadmete kui ka inimeste toimimist.

SEB Eestis ehk endises Ühispangas on meil kaks raalinduskeskust, nimetame neid A-ks ja B-ks, ning mõlemad on töötavad keskused. Võiks ka olla nii, et üks töötab ja teine on varukeskus, mis ootab, kuni esimesega midagi juhtub, kuid meil töötavad mõlemad. Kaks korda aastas teeme aga sellise eksperimendi: kevadel kolime kõik protsessid keskusest A keskusse B ja jääme tööle ühe keskusega — muidugi väiksema võimekuse ja tõhususega ning võib-olla mitte kõikide protsessidega, kuid ikkagi täiesti toimiva pangana. Sügisel teeme vastupidi. Seda ümberkolimist tehakse igal aastal kaks korda.

Olen käinud mitmel Euroopas korraldataval tippkohtumisel, mõned korrad ka *Next Generation Information Security* tippkohtumistel. Kui olen rääkinud väga suurte Euroopa pankade inimestega, siis näiteks nende teine keskus asub mitmesaja kilomeetri kaugusel ning mitu korda aastas tellitakse bussid ja viiakse inimesed füüsiliselt punktist A punkti B.

Meil on ka selline katse, kus inimesed lähevad varutöökohtadele, üldiselt kord aastas. Olukord on umbes selline: teatatakse, et Tornimäe majale tehti pommiähvardus või on seal tulekahju või ei ole maja muul põhjusel kasutatav. Siis peavad kõik töökohtadelt lahkuma. Registreeritakse, et kedagi majja ei jäänud, nagu hädaolukorra puhul ikka. Need, keda hädaolukorras vaja ei ole, lähevad rahulikult koju. Teised istuvad bussidesse ja viiakse varutöökohtadele. Mida suurem ja võimsam organisatsioon, seda suurejoonelisemad on muide need õppused. Euroopa kolleegidega rääkides võib öelda, et meil on need veel suhteliselt tagasihoidlikud, kuigi meil endil on neist üritustest väga hea arvamus.

Vaatame samu samme pisut konkreetsemalt. Alustuseks tuleb teha ettevalmistusi ettevalmistuste ettevalmistusteks. Kõige olulisem ja tähelepanuväärsem samm kogu protsessis on aga äriliste mõjude analüüs, et saaksime aru, mida peame tegema. See on väga lähedane riskianalüüsile, kuid mitte sama: see aitab mõista, millised hädad meid ähvardavad, kui meie äriprotsessidega peaks midagi juhtuma. Edasi tuleb mõelda, mida võiks teha ja kuidas halbadest olukordadest üle saada: midagi on juhtunud — mida peaksime ette võtma ja kuidas toimima? Seejärel tuleb see täpsete plaanidena kirja panna ja nagu öeldakse: testida, testida, testida ning harjutada, harjutada, harjutada.

Tarkvaraarenduses võime paljudel juhtudel rahulikult mõelda, võtta aega maha ja mitte tormata — tark ei torma — ning püüda tõsise analüüsi tulemusel õige lahendus leida. Hädaolukordade ja talitluspidevuse puhul võib mõtlemise aeg olla aga üsna piiratud ning peame suutma tegutseda kiiresti ja operatiivselt. See omakorda tähendab, et kõik tuleb varem valmis mõelda, varem läbi proovida ja harjutada, et hädaolukorra tekkides oleksime võimelised tegutsema peaaegu kohe.

### Äriliste mõjude analüüsi sammud

Siin on ettevalmistav slaid selle kohta, millised sammud BIA-s võiksid olla. Pange tähele, et talitluspidevuse plaanide, sealhulgas äriliste mõjude analüüsi puhul tuleb paljuski ajada juttu äriinimestega ja püüda neist aru saada. Selliseid asju on väga vahetult raske mõõta ja seepärast ongi siin intervjuud: kellelt tuleks küsida ja kes need inimesed on. Paljudel juhtudel on see hästi teada: on äriprotsesside omanikud, kes vastutavad ja tunnevad äriprotsesse läbi ja lõhki. Nendega koos tuleks määrata, millistele küsimustele tahame vastuseid saada. Kui oleme küsimused esitanud, püüame kindlaks teha, mis on oluline ja mis mitte. Need on ettevalmistavad sammud, mida üks ettevõte võib teha ühtmoodi ja teine teistmoodi; midagi võib olla varem valmis tehtud ja seda saab ära kasutada. Neid ei ole otseselt vaja meelde jätta.

Mida tuleks kindlasti meelde jätta: meil on funktsioone, mida meie huvi all olevad äriprotsessid peavad täitma. Neid on üsna palju ja peaksime analüüsima kõiki neid protsesse eraldi, eriti selle seisukohast, millised neist on ajakriitilised, sest nendega on hädaolukorras vaja kiiresti tegutseda.

Siin on kindlasti ka strateegiline parameeter — maksimaalne talutav seisakuaeg (*maximum tolerable downtime*, MTD) — iga olulise ärifunktsiooni jaoks eraldi. Millist aega suudame välja kannatada, ilma et meie äritegevus oluliselt kahjustuks? Kõikide ärifunktsioonide kohta hindame maksimaalse aja, mille jooksul see protsess või funktsioon võib maas olla. Kuna ärifunktsioone on meil üldiselt palju — nagu IT-s ikka on kõike palju, ka riske —, ei jõua me kõikidega tegeleda. Seepärast ongi MTD-d aluseks sellele, kuidas ärifunktsioone prioritiseerime. Need, mis tohivad kõige vähem aega maas olla ehk kõige vähem aega mittekäideldavad olla, nendega tuleks esmajärjekorras midagi ette võtta. Edasi tuleb koostada ettepanekud, dokumendid jne.

[Siin on loengusalvestuses lühike vahelesegamine ekraanile ilmunud teate tõttu; see on välja jäetud.]

Neid slaidil olevaid mummukesi ei pea eksamiks pähe õppima. Kuid BIA puhul ja ka järgnevatel slaididel, kus seda korratakse, on oluline see, et vaatame ärifunktsioonide maksimaalset talutavat seisakuaega, prioritiseerime nende alusel ja selle prioritiseerimise põhjal määrame strateegia, kuidas hädaolukorras toimida. Kõige olulisem on siin see, et määrame MTD-d. Seda on tähtis meelde jätta.

### Äriliste mõjude analüüs (BIA)

Mul on isegi terve lõik äriliste mõjude analüüsist. Järgmistelt slaididelt ei tule väga palju uut, kuid selle sektsiooni lisamise mõte on teha teile võimatuks BIA unustamine. Tahan rõhutada, et kogu talitluspidevuse käsitlus põhineb väga suurel määral äriliste mõjude analüüsil.

Mida me tegelikult tahame saavutada? Meie eesmärk on tagada, et äri saaks võimalikult vähe kahjustatud. Tahame aru saada, mis mõjutab meie äri kõige rohkem. Siin on selline loosungitaoline tõdemus: kui te ei ole oma talitluspidevuse käsitlust sidunud BIA-ga, ei ole see lühidalt öeldes päris tõsine ettevõtmine. [Slaidil: talitluspidevuse plaan, mis ei põhine BIA tulemustel ega lähtu neist, on parimal juhul oletus, puudulik ega pruugi tegeliku taastamise ajal toimida nii, nagu peaks.]

Kui võtta lühidalt kokku, mida eelmisel pikal slaidil nägime, siis BIA eesmärgid on: prioritiseerida äriprotsessi kriitilised funktsioonid, määrata kriitiliste funktsioonide nõuded ja hinnata nende maksimaalne talutav seisakuaeg (MTD). Siin ei ole võrreldes eelmise slaidiga midagi otseselt uut, kuid seda on väga tähtis veel kord rõhutada.

### Sündmuste kategooriad, MTBF ja MTTR

Kui tahame analüüsida, peaksime lähtuma sellest, millised halvad sündmused võiksid aset leida. Siin on need jaotatud kolme kategooriasse: teenuse katkestus ehk mitte-katastroof, katastroof ja suurõnnetus. Mõnel juhul on kategooriaid rohkem. Neid ei ole vaja meelde jätta.

Maksimaalne talutav seisakuaeg oli meie põhiparameeter. Sellega on üsna vahetult seotud ka sellised suurused nagu keskmine tõrgetevaheline aeg (*mean time between failures*, MTBF) — milline on oodatav aeg kahe tõrke vahel — ja keskmine parandusaeg (*mean time to repair*, MTTR) — millise ajaga võime loota rikkega seadme parandamist. Neid parameetreid ei ole vähemalt eksami jaoks vaja meelde jätta. Küll aga maksimaalne talutav seisakuaeg: see on see, millel kõik põhineb, iga ärifunktsiooni kohta eraldi.

### Talitluspidevuse mõõdikud ajateljel

Nüüd on üks tore pilt, kus on üsna palju olulist infot. Seda pilti ei ole vaja eksamil korrata, kuid tasub see siiski üle käia ja tuletada meelde talitluspidevuse olulised faasid ning selle, mis ajas toimub.

Ühel teljel on äriline võimekus (*capacity*) ja teisel aeg. Oleme sajaprotsendilise ärilise võimekusega, meie protsess toimib. Teatud hetkel, mis on siin noolega näidatud, toimub mingi halb sündmus, mille tõttu protsess lakkab töötamast. Näete, selle võimekus langeb sajalt protsendilt nullini — protsess enam ei toimi.

Milliseid ajavahemikke siin vaadeldakse? Kõigepealt on reaktsiooniaeg: kui oleme teada saanud, et midagi halba juhtus, kulub aega, kuni vastavad spetsialistid — või automaatse protsessi puhul automaatika — on end kokku reguleerinud. Siin on vaja inimese sekkumist. Selle reaktsiooniaja vältel ei toimu midagi; tehakse ettevalmistusi taastamise (*recovery*) alustamiseks. Taastamisprotsessi tulemusel on meil möödapääs: käivitame alternatiivse protsessi. Selle võimekus on siin joonistatud pooleks esialgsest, kuid sõnum on see, et see võib olla oluliselt väiksem. See ei pruugi olla esialgsega samaväärne, kuid suudame siiski seda ärifunktsiooni kas osaliselt või aeglasemalt, halvemate parameetritega täita.

Nüüd hakkavad kulgema hädaolukorra toimingud (*emergency operation*). Paljudel juhtudel, näiteks SEB Eesti puhul, käivitatakse need protsessid üldse sekundaarses raalinduskeskuses. See ei pruugi alati nii olla — see võib toimuda ka samas keskuses, kuid võib ka alternatiivses.

Kui personal on suutnud alternatiivse protsessi käivitada, on võtmepersonal, kes on selle protsessiga tegelemiseks piisavalt kompetentne, vabanenud. Nüüd algavad ettevalmistused esialgse protsessi taastamiseks (*restoration*). Need ettevalmistused võivad alata — ei pruugi, kuid võivad — isegi juba siis, kui alternatiivne protsess ei ole veel käivitunud. Kui esialgse protsessi taastamise ettevalmistused on lõpule jõudnud ja oleme teinud kõik, et saaksime minna tagasi esialgse protsessi juurde, toimub esialgse protsessi ennistamine — tavatööle naasmine. Pärast seda on isegi võimalik, et meie võimekus ületab ajutiselt algset, sest peame täitma veel mitmesuguseid lisaülesandeid (*post-emergency tasks*).

Seega: esialgu kukume nulli, siis toibume ja töötab alternatiivne protsess, seejärel on taastamine lõpule jõudnud ja ennistame esialgse protsessi.

Siin on veel mõned olulised parameetrid. Kõigepealt aeg alates sellest, kui protsessi võimekus kukkus nulli, kuni hetkeni, mil suutsime alternatiivse protsessi käivitada. See on aeg, mil protsess oli täielikult seisatud (*blackout*), ehk taasteaja eesmärk (RTO), mis on antud protsessi jaoks strateegiline parameeter. Edasi on hädaolukorra toimingute aeg (*emergency operation time*): kui kaua on alternatiivne hädaolukorra protsess käigus. Aeg alates nulli kukkumisest kuni ennistamiseni on kogu taasteaeg (*restore time*). Siia on märgitud ka maksimaalne lubatav andmekadu (*maximum allowable data loss*), mis ei ole midagi muud kui taastepunkti eesmärk (RPO).

Sellel pildil on kõik need asjad olemas, kuid endiselt ei ole selle pildi kordamine eksamiküsimus. Oluline oleks aga, et te neid mõisteid teaksite — nii selleks, et mõista, millist tähtsust need omavad strateegilisel planeerimisel ja strateegia elluviimisel, kui ka IT-töös üldiselt.

### RTO ja RPO täpsemalt

Eraldi on veel rõhutatud kahte strateegilist parameetrit: taasteaja eesmärki (RTO) ja taastepunkti eesmärki (RPO). Sellel slaidil ei ole palju uut, kuid pange tähele, et siin on näidatud kaks RTO väärtust.

Esimene on minimaalne RTO (*RTO min SLA*), mis vastab teenustaseme lepingus (*service level agreement*, SLA) fikseeritule. See on aeg, mil protsess on seisatud ja mille jooksul suudame pärast hädasündmust püsti tõsta alternatiivse protsessi SLA-kohase minimaalse võimekusega.

Teine on RTO (*normal operation*) — aeg, mille jooksul oleme suutnud saavutada esialgse võimekuse. Kui võrdlete eelmise pildiga, näete, et RTO võib olla defineeritud ka maksimaalsena, nii et see vastab eelmise pildi *restore time*'ile. Kindlasti tuleb silmas pidada, kuidas definitsioonid on antud.

### Maksimaalse talutava seisakuaja näited ja käideldavus

MTD on oluline suurus, mille järgi määrame erinevate ärifunktsioonide ja protsesside prioriteedid. Siin on näidatud, kuidas prioritiseerimine võib toimuda. Neid arve ei ole vaja pähe õppida. Kuid nagu näete, on isegi võimalik, et mõnd funktsiooni taastatakse kuu aja jooksul. Kui mõne äriprotsessiga juhtub tõsine katastroof, võidakse selle taastamiseks jätta küllalt palju aega, sest IT-l ja inimestel on palju tähtsamaid asju teha. Kui protsess ei ole eluliselt oluline, võime selle taastamise jätta küllaltki pikaks ajaks. Kriitiliste protsesside puhul võib aga olla lubatud mõni minut või äärmisel juhul mõni tund.

Siin on veel kord pilt keskmisest tõrgetevahelisest ajast: süsteem töötab, juhtub midagi, parandatakse, töötab jälle, parandatakse jne. Siin on see graafiliselt kujutatud.

Veel üks illustreeriv slaid näitab käideldavuse numbreid. Kui käideldavus on 98%, on nädalas veidi üle kolme tunni seisakuaega. Kui käideldavus on 99,999%, mis on ülikõrge käideldavus, on nädalas seisakut kuus sekundit. Aga 99,9999%? Ma ei ole kuulnudki, et siin lähiümbruses oleks kusagil sellise käideldavusega süsteeme, kuid põhimõtteliselt on see võimalik. Siis on nädalas lubatud seisakuaega 0,6 sekundit. Selliseid nõudeid võidakse esitada näiteks väga suurtele börsiettevõtetele või pankadele Deutsche Banki või Citigroupi tasemel või mõnele energeetikaettevõttele, kus on ka äärmiselt oluline tõrgeteta töö.

### ISO 22317 — äriliste mõjude analüüs

Võib arvata, et talitluspidevuse-sugusel alal ei peaks iga ettevõte ise jalgratast leiutama. Selleks kuluks kindlasti palju aega, enne kui keegi jõuaks oma kurbade kogemuste põhjal äratundmisele, millised on talitluspidevuse ja hädaolukordadest ülesaamise nõuded, kuidas need kirja panna, kuidas protsessid üles ehitada ja mida üldse on vaja teha.

Seepärast ei ole ka imeks panna, et äriliste mõjude analüüsi kohta on olemas omaette ISO standard 22317. Selle kursuse puhul ei pea te seda standardit aga kuidagi peast teadma: ei pea teadma numbreid ega sisu. See on teile lihtsalt teadmiseks, et BIA määratlemiseks on olemas eraldi ISO standard. See rõhutab selle protsessi tähtsust.

Siin on näitena selle standardi sisukord. Põhiline on BIA läbiviimine (*performing the BIA*) ning toodete ja teenuste prioritiseerimine (*product and service prioritization*). Kõik algab sellest, et tahame saada selge prioritiseerimise ja määratleda, millised ärifunktsioonid ja teenused on kõige kõrgema prioriteediga, sest nendega tuleb esmajärjekorras midagi peale hakata. Edasi on mitmesugused muud punktid. Kuid veel kord: see ei ole eksamiküsimus.

Standardi definitsiooni järgi analüüsib BIA protsess häiriva intsidendi tagajärgi organisatsioonile ning selle väljund on talitluspidevuse nõuete põhjendus. Siit saame MTD-de alusel tuletada prioritiseeritud protsessid.

### Mõjukategooriad

BIA juurde kuulub ka see, millest me pole veel otseselt rääkinud, kuid mis on üsna loomulik — ja jällegi ei ole see eksamiküsimus: milles võib halva sündmuse äriline mõju avalduda ja milliseid kategooriaid peaksime vaatlema. Need on väga loomulikud ja raketiteadusega pole siin midagi pistmist.

Kõigepealt finantsiline kategooria: kui äriprotsess ei toimi, võime saada väga selget rahalist kahju. Edasi on maine. Panga puhul ei ole seda raske ette kujutada: kui teil on vaja poes kaardiga maksta, kuid SEB kaardid meie süül ei toimi, saate niisuguse panga peale väga kurjaks ja võite kergesti panka vahetada. Mainekahjule väga lähedane on see, kui kahjustuvad seadusest tulenevad nõuded: näiteks Finantsinspektsioon saab kohe kurjaks, kui me teatud tingimusi ei täida.

Pisut pehmem, kuid eelmisele lähedane on lepinguline kategooria. Näiteks Eesti Energia on meiega sõlminud lepingu, et tagab meile elektri. Mõned aastad tagasi juhtus aga selline lugu — see on mulle hästi meelde jäänud, sest Ühispank oli Tallinnas reserveerinud terve „Mamma Mia!" etenduse. Eesti Energia tegi mingeid remonditöid ja neil õnnestus selle käigus läbi lõigata kaks sõltumatut kaablit, nii et meie maja jäi elektrita. Alguses rakendus UPS ja kui UPS hakkas tühjaks saama, pidi automaatika käivitama generaatori. Kurb lugu oli aga selles, et UPS andis veel viimase impulsi, mida generaator tõlgendas nii, et UPS siiski elab, ja generaator ei käivitunud. Inimesed olid selleks ajaks „Mamma Mia!" etenduselt juba panka jõudnud ja oleksid tahtnud midagi ette võtta, kuid midagi teha ei saanud, sest tegemist oli täisautomaatikaga. Tulemus oli see, et suur hulk IT-inimesi pidi etenduse lõpuni nautimise asemel parandama hub'e, switch'e ja kõike muud, mis paljudel korrustel valesti läks. Pärast seda paigaldati serveriruumi käsitsi tõmmatav lüliti, millega saab generaatori käivitada automaatikast sõltumata. Sel korral see puudus ja see tekitas sellise olukorra.

Lõpuks: millised ärieesmärgid jäävad saavutamata? See on juba otseselt seotud strateegiaga. Ka seda ei ole vaja pähe õppida, kuid selle slaidi sõnum on, et peaksime püüdma väga mitmekülgselt hinnata mõjusid, mida ühe või teise teenuse katkemine kaasa toob. Need mõjud, mida peame analüüsima ja arvestama, võivad olla väga mitmesugused. Ja nagu juba räägitud, võivad mainekahjud väga kergesti ja enamasti lõppkokkuvõttes väljenduda ka rahaliselt. Paljud probleemid, mis on algselt mõnes teises kategoorias, võivad lõpuks mõjutada ka finantsnäitajaid.

### Mitmetasandiline prioritiseerimine

Kogu meie BIA käsitluse aluseks on mitmetasandiline prioritiseerimine. Kõigepealt tuleb prioritiseerida meie tooted ja teenused. Panga puhul tähendavad teenus ja toode sageli sama või lähedast asja, kuid mitte alati. Kui räägime näiteks saapavabrikust, võib toode olla üks asi, kuid teenus, mida saapavabrik osutab, võib olla hoopis midagi muud.

Jätame tooted esialgu kõrvale. Äri osutab teatud teenuseid ja neid teenuseid osutatakse seetõttu, et toimuvad mingid äriprotsessid. Kõigepealt prioritiseerime teenused — paneme need MTD-de alusel tähtsuse järjekorda: millised on kõige olulisemad, millised vähem olulised jne. Seejärel uurime iga teenust täpsemalt: millised äriprotsessid mõjutavad ühte või teist teenust, millised rohkem, millised vähem ja millised üldse mitte. Protsessid omakorda toimuvad mitmesuguste tegevuste (*activities*) ehk protsessisammude kaudu: millised sammud on kõige prioriteetsemad ja millistele tuleb esmajärjekorras tähelepanu pöörata? Siin tuleb arvestada, et iga protsessi sooritamiseks on vaja mitmesuguseid ressursse, ning vaadata nende ressursside kättesaadavust ja toimimist. Otseselt eksamiks on siit küsimusi aga vähe.

### Pärast BIA-d: taastestrateegiad

Kui äriliste mõjude analüüs on tehtud, oleme suutnud prioritiseerida oma teenused ja neid tagavad protsessid ning nendele protsessidele vastavad sammud ja faasid. Nüüd peaksime mõtlema, milliseid alternatiivseid ressursse võiksime kasutada hädaolukorra mõjude pehmendamiseks ja leevendamiseks. Seejärel vaatame võimalikke taastestrateegiaid.

Taastestrateegiad on otseselt seotud sellega, milliste ressursside taastamisest räägime, ja neid ressursse tuleks vaadelda eraldi — alates inimestest kuni andmete, süsteemide ja mitmesuguste seadmeteni. Kõiki neid tuleb arvesse võtta. Kõik muu on meie käsitluses alati alluv: meie, IT-inimesed, eksisteerime selleks, et äriinimesed oleksid õnnelikud. See tähendab, et meie tegelik eesmärk on äriprotsessi ja äriteenuse taastamine. Sellest lähtudes on äriline taastamine koos maksimaalse talutava seisakuajaga kõige olulisemad näitajad.

### Plaani koostamine

Kuidas edasi toimime? Neljas faas on plaani koostamine; tuleme sammude juurde tagasi. Jätame ettevalmistavad sammud kõrvale. Siin on kriitilised süsteemid, mille taastamise strateegiad võiksid olla käsitletud kõigepealt — kuigi võib-olla hoopis mõnes teises järjekorras. Seejärel vaatame mittekriitiliste süsteemide taastamise strateegiaid, mida võib käsitleda hiljem, kui aega saame. Siis ärifunktsioonid ja kokkuvõttes kogu ettevõtte vastavad ärifunktsioonid. Hea uudis on endiselt see, et selles osas on otseseid eksamiküsimusi suhteliselt vähe.

Siin on illustreeriv slaid protsesside MTD järgi prioritiseerimise kohta. Näeme, et võiksime jagada protsessid kolme, nelja või rohkemasse rühma ning vaadata neile püstitatud nõudeid ja strateegiaid, mida tuleb rakendada. On selge, et punaseks värvitud, kriitilise mõjuga protsessid tuleb käsitleda kohe, äärmiselt lühikese aja jooksul.

Siin on näidatud ka kaks tähtsat strateegilist parameetrit, RPO ja RTO: millised võiksid olla RTO nõuded minutites, tundides, päevades või nädalates ja milline tehniline vahend võimaldaks seda reaalselt saavutada. Edasi RPO: kui palju andmekadu võime endale lubada. Pankade ja pangatehingute puhul ei saa me enamasti lubada mingit andmete kadumist ega tehingute kaotamist; enamikul juhtudel on see null. Mõne protsessi puhul võib see olla sekundeid või minuteid, kuni tundide ja isegi päevadeni. Pangas võib muidugi leida mõne protsessi, mille puhul on teatud andmete kaotamine lubatud, kuid need on abiprotsessid. Kõik pangatehingute töötlemisega seotud protsessid ei saa endale midagi sellist lubada.

### Testimine ja hooldus

Viimane faas oli testimine: kas kõik plaani osad töötavad? Plaani ennast tuleks teatud perioodilisusega üle vaadata, sest kõik muutub. Siin on ka talitluspidevuse plaanide viimine kõikide töötajateni. Muide, finantsasutuste ja pankade puhul on kindel nõue, et kõik töötajad peavad nendest plaanidest teadlikud olema.

### Talitluspidevuse halduse elutsükkel

Sellel tiitelslaidil on näidatud, et alguses on meil mitmesugused tegevused, mis on suunatud sellele, et vältida halva sündmuse esinemise võimalust üldse. Need on ennetavad tegevused: ehitada võimalikult tugev kindlus, et halvad sündmused ei suudaks meid kahjustada. Seejärel on kolm kõige olulisemat etappi: esiteks reageerimine halvale sündmusele, teiseks alternatiivsete protsesside käivitamine ja lõpuks esialgsete protsesside taastamine ja ennistamine. See on lihtne üldine elukaare kujutis.

### Tüüpiline talitluspidevuse planeerimise protsess

Järgmistel slaididel on sama esitatud pisut täpsemalt. Muide, see on küllalt lähedane sellele talitluspidevuse protsessile, mida SEB pank tegelikkuses kasutab — mitte täpne koopia, kuid küllalt lähedane.

Esimene samm on vastava projekti algatamine. Kõikide projektide puhul on oluline mõista — usun, et projektijuhtimise kursusel on seda teile piisavalt rõhutatud, ja talitluspidevuse projekt ei ole mingis mõttes erand —, millised ressursid on meie käsutuses ja milliste ressurssidega peame oma tegevused läbi viima.

Edasi tuleb, nagu projektide puhul üldiselt, määrata, mis jääb projekti sisse: mida käsitleme selles projektis, mida võib-olla järgmistes projektides ja mis jääb projektist üldse välja. See on projekti ulatuse määratlemine.

Tähtsal kohal on püüda mõista, millised on meie kaitsevõimed — kui tugeva kindluse oleme suutnud ehitada — ning millised on riskihalduse ja riskide määratlemise tulemused. Talitluspidevuse planeerimine lähtub ka sellest, millised kaitsed meil on millistele riskidele juba olemas.

Edasi on punaste tähtedega märgitud äriliste mõjude analüüs, mis on talitluspidevuse planeerimise ja ka vastava projekti tuum. See viiakse läbi nii, nagu rääkisime. Sealt tulevad sisendid taastestrateegiate väljatöötamisse, mis arvestavad, millised mõjud olid äriprotsessidele ja millised kaitsed millistele riskidele meil olemas olid. Sellest lähtudes töötame välja strateegiad ja testime neid. Edasi tulevad juhtkonna teadlikkus ja koolitus, ülevaatused, testimine ja verifitseerimine ning hooldus ja muudatuste haldus. Seda skeemi ei ole vaja eksamil osata korrata. See on talitluspidevuse üldine käsitlus.

Kui veel kord kokku võtta: BIA, MTD, prioritiseerimine. Kui need võtmesõnad ja nende tõlgendus on teile arusaadavad, on teil põhiline olemas, et mõista kursust strateegia seisukohast.

### Intsidentide haldus

Talitluspidevusega on äärmiselt lähedalt seotud intsidentide haldus, mis on teatud mõttes selle täiendus. Kõigepealt on halb sündmus — meil on tegemist intsidendiga — ja peame sellest kuidagi üle saama. Talitluspidevuse raames on tehtud mitmesuguseid plaane, kuid nüüd oleme silmitsi konkreetse hädaolukorraga. Esimesel pildil on kiri „Meie intsidendimeeskond võtab oma tööd väga tõsiselt!". Üldiselt on väga positiivne, kui oleme nii meelestatud.

Siin on talitluspidevuse juhtimissüsteemid ja äriliste mõjude analüüs, millest oli juttu seoses standardiga 22317. On näha, et see standard viitab mitmele teisele standardile. Teatud määral võime nimetada ISO 22317 raamstandardiks, millega seotud abistavad standardid on näiteks NIST SP 800-61 (*Computer Security Incident Handling Guide*), üldine infoturbestandard ISO 27001 või ISO 27035, mis käsitleb otseselt intsidente.

Siin on väike loosungitaoline fraas: on kahte sorti ettevõtteid — need, keda on häkitud, ja need, keda on häkitud, kuid kes seda veel ei tea. Mõte on selles, et tänapäeval ei ole võimalik saada absoluutset kaitset pahatahtlike tegelaste vastu ja me ei pruugi alati olla teadlikud sellest, kui halvas olukorras tegelikult oleme.

Intsidendi enam-vähem formaalne definitsioon: vaenulikud sündmused, mis ohustavad arvutisüsteemide ja -võrkude turvalisust. Kui meenutada infoturbe kursust, siis mõistame turvalisust üsna üldises mõttes käideldavuse, konfidentsiaalsuse ja terviklikkuse kaudu. Intsident on sündmus, mis kahjustab üht neist olulistest parameetritest — terviklikkust, konfidentsiaalsust või käideldavust — või mingit nende kombinatsiooni. Sündmused on sellised, mida suudame märgata ja millest saame aru, et midagi halba on juhtunud — need on jälgitavad. Vaenulike sündmuste hulka kuuluvad, nagu näete, ka igasugused tõrked. Paljud intsidendid taanduvad, nagu juba räägitud, sellele, et kahjustatud on kas käideldavus, terviklikkus, konfidentsiaalsus või mingi nende kombinatsioon.

Intsidente püütakse uurida. Jällegi on olemas terve rida standardeid, mille hulgas oli juba mainitud ISO 27035, mis käsitleb otseselt intsidentide haldust. Lisaks on küberturvet ja äri talitluspidevust käsitlevad standardid jne. ISO standardeid on terve rida ja sõnum on jällegi väga lihtne: neid ei ole vaja pähe õppida, selleks pole mingit mõtet. Valdkond on aga äärmiselt oluline ja me ei saa loota, et kõik ettevõtted avastavad oma kurbadest kogemustest, et on vaja toimida ühel, teisel või kolmandal viisil. Need tarkused on kõik juba avastatud ja kristalliseerunud mitmesugustes standardites, millest lähtuvad konkreetsed ettevõtted, sealhulgas SEB. Ja kui me ise selle peale ei tule, siis Eesti Finantsinspektsioon ütleb meile: „Te peate juhinduma sellest standardist." Ja kõik. Nad auditeerivad ja teevad kindlaks, kas me vastame nõuetele või mitte.

### Intsidentide halduse tegevused

Millised toimingud ja tegevused kuuluvad intsidentide halduse juurde? Olen ka varem öelnud, et sõna *management* võib olenevalt kontekstist tõlkida eesti keelde kas juhtimiseks või halduseks. „Intsidentide juhtimine" kõlab pisut kummaliselt, sest me ei saa kuidagi mõjutada, kas intsident tekib või mitte — see sündmus ei allu meie kontrollile. Selles mõttes oleks minu soovitus, kuigi mitte absoluutne nõue, tõlkida see pigem „halduseks".

Esiteks: mäletate seda veidi naljakat slaidi, et osa ettevõtteid on küll rünnatud, kuid nad ei teagi seda. Paljude intsidentide puhul, mis puudutavad konfidentsiaalsust, terviklikkust ja käideldavust — neid võib lühidalt nimetada turvaintsidentideks, kuigi need ei pruugi olla seotud väga selgete rünnetega —, tuleb kõigepealt aru saada, et üldse on midagi halba juhtunud. See on teadete vastuvõtmine (*receive notifications*).

Siin on muide meie endine kolleeg Risto Vaarandi, kes kaitses kümmekond aastat tagasi doktoritöö ja töötas välja praktilise tarkvara *Simple Event Correlator* (SEC). Seda kasutavad — võite veebilehte ise vaadata — väga paljud organisatsioonid üle maailma, välja arvatud SEB grupp. Risto lahkus mõni aeg tagasi SEB-st, kuna ei leidnud seal piisavat tuge, ja on nüüd Tehnikaülikooli hingekirjas ning õpetab siin; olen teda näinud ka IT Kolledži majas. Veebilehel on näha Risto Vaarandi enda nimi, kuid SEC-iga seotud kaastööd tehakse üle maailma väga palju. Algataja oli kümmekond aastat tagasi Risto, kuid kõik läheb edasi ja väga paljud suured firmad kasutavad Risto metoodikat.

Kui võrrelda näiteks SEB seireruumiga Rissnes Stockholmis: seal on — ma ei ole kokku lugenud — vähemalt sada mitmesugust teleriekraani suurust kuvarit, kus on näha SEB Rootsi võrgus toimuvad sündmused. Muidugi on neil suurarvutid ja ka võrk on suurem, kuid meie seireruumis ei ole kahtkümmendki kuvarit ja meil on sealt täielik ülevaade sellest, mis meie võrkudes toimub. See on just tänu Risto metoodika järjekindlale rakendamisele.

Esimene samm — üldse aru saada, et midagi on juhtunud — eeldab seiresüsteemide olemasolu. Reaktsioone on väga mitmesuguseid. Näiteks kui meie võrgus toimub öösel midagi halba, suudab süsteem saata vastavale inimesele SMS-i või isegi helistada. Reaktsioonid võivad olla mitmesugused, kuid kõige olulisem on teada saada, et üldse midagi on juhtunud.

Intsidendi määratlemiseks ja väljakuulutamiseks ei ole vaja väga suuri volitusi: piisab seiretöötajast, kes saab vastava tasemega häire. Kui räägime aga hädaolukorra ehk katastroofi (*disaster*) väljakuulutamisest, siis panga puhul teeb seda panga kriisikomitee juht, kes paljudel juhtudel peaks olema panga president.

Edasi on eriti kriisiolukorras oluline määratleda, kuidas suhelda üldsusega. Näiteks kui me ei suuda meie süül pangakaarte teenindada kauem kui pool tundi, peame andma pressiteate. See on küllalt tõsine, kuid mõne teise häire puhul ei pruugi see vajalik olla. Kindlasti on oluline, et kõik, mis on seotud tõsiste intsidentide ja kriisiolukordadega, oleks väga selgelt dokumenteeritud: kes avastas, mida tehti, kuidas toimiti jne.

### Intsidendi ajajoon ja kolmetasandiline struktuur

Näete, et ajaline esitus ei ole keeruline. Intsidentide haldus on väga lähedalt seotud talitluspidevuse haldusega selles mõttes, et talitluspidevuse halduse ja plaanide järeldusi kasutatakse tegelikult konkreetse intsidendiga tegelemisel. Ettevalmistav töö on tehtud talitluspidevuse plaanide koostamisel ja kui intsident esineb, võime vaadata väga paljusid samme, võib-olla isegi kümneid. Need toimingud jagunevad aga kahte suurde rühma. Esimene on see, kuidas intsidendile kõigepealt reageerida — intsidendile reageerimine (*incident response*). Kui oleme esialgse reaktsiooni suutnud teha ja kõige hädapärasemad tegevused sooritanud, hakkame vaatama, kuidas halvast olukorrast välja tulla ja esialgne olukord taastada.

Siin on mingis mõttes näidatud ka seda, et olenevalt intsidendi tasemest on meil vastavad meeskonnad, meetodid, poliitikad ja protsessid. Kuldne ehk strateegiline tase (*gold/strategic*) hõlmab sündmusi, mis takistavad või pärsivad strateegiliste eesmärkide saavutamist — see on kõige kõrgem tase, kus intsidendid takistavad panga ja ettevõtte eesmärkide saavutamist. Edasi on hõbedane ehk taktikaline tase (*silver/tactical*): taktikalised eesmärgid on need, mille kaudu strateegia realiseerub. Lõpuks on igapäevaste operatsioonide tase (*bronze/operational*), kus on ohus igapäevane tegevus. Vastavalt sellele on ka mitmesugused meeskonnad, kes nendega tegelema peavad.

[Vastus kuulaja küsimusele:] Arvan, et vastasite oma küsimusega tegelikult ise. Mõlemad pooled on tähtsad. Kui dokumenteerite piisavalt hästi, et tehniliselt oleks selge, mis toimus ja kuidas seda lahendati, siis fikseeritud raporti ülevaatamise ja üldistamise tulemusel võidakse muuta nii protsessi ennast, mille puhul intsident toimus, kui ka seda tüüpi intsidentide käsitlemise protsessi kui sellist. Võib olla mõlemat pidi.

Siis on meile juba tuntud standard ISO 22301. Siin on veel kord näidatud needsamad lihtsad sammud: juhtus mingi halb sündmus ja on vaja anda esialgne kiire vastus, et leida tee sellest üle saamiseks. Edasi läheme teele, kus käivitame mitmesugused alternatiivsed protsessid, ja lõpuks ennistame esialgsed protsessid. Ühesõnaga: vastus (*response*) ehk reageerimine intsidendile, püüdes mõista, mis toimus; taastamine (*recovery*) — ressursside määramine ja alternatiivsete protsesside kasutamine; ning lõpuks esialgsete protsesside ennistamine (*resumption*).

### Intsidentide prioriteedid

See lihtne intsidentide klassifikatsioon on muide sama, mida kasutab ka SEB. Intsidentide puhul vaadatakse siin ainult kahte telge: kui paljusid kliente ehk kasutajaid see mõjutab ja kui paljusid süsteeme see mõjutab. See on äärmiselt lihtsustatud, ainult kahetasemeline: kas palju süsteeme või üks süsteem ning palju kasutajaid või vähe kasutajaid. Ei ole välistatud, et mõni ettevõte kasutab näiteks kolm korda kolm või isegi viis korda viis maatriksit, kuid siin on prioritiseerimine äärmiselt lihtne.

Palju kasutajaid ja palju süsteeme — äärmiselt kõrge prioriteet (*extreme high*). Kui intsident puudutab palju kasutajaid ja üht süsteemi või vähe kasutajaid ja palju süsteeme, on prioriteet kas kõrge või tavaline — kasutajad on siin primaarsed: kui kasutajaid on palju, on prioriteet kõrgem. Kui ühe süsteemi tõrge puudutab ühte ainsat või äärmiselt vähest arvu kasutajaid, on prioriteet madal. Vastavalt intsidendi prioriteedile tuleb toimida.

Järgmistel slaididel on välja kirjutatud, mida tuleks teha, kuid seda ei ole vaja eksamiks õppida. Äärmiselt kõrge prioriteet: väga kriitiliste kesksüsteemide ja rakenduste tõrge, suured teenused ei ole kättesaadavad, mõjutatud on palju kasutajaid — ja toodud on mõned näited, millised tehnilised sündmused võivad selle taga olla. Neid ei ole vaja pähe õppida; need ei ole eksamiküsimus. Kõrge prioriteet: kesksüsteemide või kriitiliste perifeersüsteemide ja rakenduste tõrge, mis hõlmab vähe süsteeme — näiteks kontori, kõnekeskuse või teeninduskeskuse katkestus — ja mida sellisel juhul teha tuleb. Tavaline prioriteet: mittekriitilised süsteemid, üks süsteem või rakendus ei ole kättesaadav. Madal prioriteet: kindlasti mittekriitilised süsteemid, üks süsteem või rakendus ei ole kättesaadav ja mõjutatud on üks kasutaja.

### Teenuse sihttasemed

On kokku lepitud, millised peaksid olema vastavad ajad. Reageerimisaeg (*response time*) — millise ajaga tuleb reageerida. Oluline on, et oleks määratletud, mida reageerimisaeg tegelikult tähendab ja mis selle aja jooksul peab toimuma.

Mul on reageerimisaja kohta üks kunagine näide, vist nõukogude ajast. Mul juhtus korteris kraaniga mingi pahandus. Helistasin majavalitsusse või mis selle asja nimi tol ajal oli. Tunni jooksul santehnik reageeris: tuli kohale, käed taskus, vaatas, et kraaniga on lugu halb, ja millalgi tuli ja parandas selle ka ära. Aga selline reageerimine, kus veeavariile reageeritakse nii, et vaadatakse, mis õieti juhtus, ei ole päris see, mida silmas peame. Reageerimisaja all peame silmas, et selle aja jooksul tehakse vähemalt väga korralikud ettevalmistused alternatiivse protsessiga alustamiseks.

Lahendusaeg (*resolution time*) — millise ajaga peaks probleem olema kõrvaldatud. See sõltub väga selgelt SLA-st ehk teenustaseme lepingust.

Siin on ka valmisolekuajad ehk ajad, mil vastavale protsessile on tugi olemas. Need on muide olulised, kui ostate näiteks servereid või süsteemitarkvara. Teil on võimalik sõlmida erineva teenustasemega lepinguid; neid nimetatakse enamasti *Gold*- või mõnikord ka *Platinum*-tasemeks, mis tähendab, et teatud tugi nende süsteemide tõrgete puhul on teile kättesaadav praktiliselt 24/7 ja väga kiiresti. Kui teil on aga sõlmitud lahjemad teenuslepingud, võib reageerimisaeg olla üsna pikk.

### Katastroofid

Intsident võib olla kergem või olulisem. Mõned intsidendid on katastroofilise iseloomuga (*disaster*). Neid iseloomustab reeglina see, et nende esinemise tõenäosus on küll üsna väike, kuid mõju võib olla ettevõttele katastroofiline. Järgmisel slaidil on näidatud mitmesugused kriitilised katastroofilised sündmused; neid ei ole vaja eksamiks õppida. Siin on veel näidatud, millised võiksid olla eri õnnetuste puhul seatud tingimused ja millised võiksid olla mõistlikud taastamise võimalused. Jällegi ei ole seda vaja pähe õppida.

### Talitluspidevus ja avariitaaste

Kui räägime IT seisukohast, siis meenutame veel kord, et meie, IT-inimesed, eksisteerime ainult selleks, et teha äriinimesed õnnelikuks. Talitluspidevus on see, mida me IT-inimestena tahame tagada: äriteenuste toimimise tagamine ja selle planeerimine. See, mis puudutab otseselt meid, IT-inimesi, on avariitaaste (*disaster recovery*) — hädaolukorrale reageerimine ja hädaolukorrast taastumine. Sellega tegeleme reaalselt meie.

Siin on võrdlus. Talitluspidevuse planeerimine (BCP) hõlmab tegevusi, mis on vajalikud organisatsiooni kriitiliste äriprotsesside jätkumise tagamiseks. Talitluspidevuse planeerimisel lähtume sellest, millised on kriitilised äriprotsessid, ja tahame tagada nende toimimiseks alternatiivsed võimalused. See hõlmab sageli ka mitte-IT aspekte — võib-olla ei ole siin üldse tegemist IT-probleemidega. Kui räägime aga avariitaastest (DRP), peame silmas seda, kuidas taastada IT-süsteeme. Need on omavahel seotud, kuid ei ole samad. Nii nagu äri on IT suhtes ülemuslik, on ka talitluspidevuse plaan avariitaaste plaani suhtes ülemuslik. Seda ei ole aga vaja pähe õppida.

### Kui intsident juhtub

Nüüd intsident: kutsutakse turvajuht (*security officer*), turvajuht kuulutab välja hädaolukorra ja järgib eelnevalt kehtestatud protokolli. Näete, siis tegutseb hädaolukorra meeskond ja käivitub kõnepuu (*phone tree*).

Kui räägime IT avariitaaste plaanist, siis see kõnepuu — kes peab millistel juhtudel kellele helistama — on üks kõige põhilisemaid dokumente. Sellest on väga lihtne aru saada. Kui meie tippspetsialistid on kohal — kui nad on voodist välja tõstetud ja panka sõidutatud —, võib arvata, et nad tulevad probleemidega toime, sest tunnevad süsteeme küllalt hästi. Kui me aga ei saa õigel ajal õigeid inimesi kätte, ei suuda neid üles leida ega teavitada, ei ole midagi head loota.

### Avariitaaste tehnoloogiad ja strateegiad

Avariitaaste puhul on taastepunkti eesmärk ja taasteaja eesmärk tähtsad strateegilised parameetrid. Kui palju andmete kadumist lubame? Nagu öeldud, on see pangatehingute puhul praktiliselt null. Taasteaeg: millise aja jooksul peavad alternatiivsed protsessid olema käivitatud? Siin on vastavalt RTO-le ja RPO-le näidatud, millised tehnilised lahendused võiksid tagada teatud nõuete täitmise.

### Talitluspidevuse ja avariitaaste plaani olulised küsimused

Edasi on veel mitmesuguseid asju, mida tuleks arvestada. Evakuatsiooniplaan: näiteks Tornimäe majas tehakse igal aastal üks ette teatamata evakuatsiooniõppus, kus keegi ei saa kasutada lifte, kõik peavad peakontorist lahkuma treppe mööda ja need, kellele see on ette nähtud, lähevad varutöökohtadele. Edasi hädaolukorra väljakuulutamine (*disaster declaration*): kes seda üldse teha võib? On selge, et seda peaks tegema küllaltki autoriteetne panga inimene. Vastutus: kes täidab vajalikud avariitaaste funktsioonid — personaalsed vastutused. Millised on protsessid ja millised oleksid alternatiivsed protsessid? Siin on ka üldised äri- ja IT-spetsiifilised funktsioonid ning kes mille eest vastutab. Jällegi ei ole seda vaja pähe õppida.

### Lõpetuseks

Selle osa lõpetuseks ilus pilt. Esimene taasteplaan oli Noal, kui maailm pidi hukka minema ja ta tahtis teatud tegelased ära päästa. Tema teadis, millal hädaolukord juhtub. Miks ta seda teadis? Tal olid väga head sidemed kõrgemale poole. Tavaliselt me ei tea, millal halvad sündmused aset võivad leida, ja see raskendab meie tegevust.

Siin on ka mõned naljad. „Jenkins, kas meie IT avariitaaste plaan on paigas?" — „Jah, söör!" — ja näidatakse plaani kui dokumenti. Paljudel juhtudel on sellest dokumendist, isegi kui see on suhteliselt hästi koostatud, vähe kasu, kui seda ei ole kõikidele töötajatele kommunikeeritud ega harjutatud.

Veel üks väike nali: „Mul ei ole kunagi aega kõiki neid plaane harjutada." Plaane on tohutult palju. Tuleb silmas pidada, et plaanid oleksid koostatud nii, et põhitegevused mahuksid ühele A4-lehele. Kui on tõepoolest tegemist hädaolukorra või katastroofiga, ei ole kellelgi aega pikki dokumente lugeda. Selline lühike konspekt oleks aga hädaolukorra lahendamisel abiks.

Ja siin on see vana tuntud jutt: meie ressursid on piiratud ning peame saavutama tasakaalu tõhususe ja riski ning tõhususe ja seadustele vastavuse vahel.
