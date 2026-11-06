# Dokumendi päritolu

Koostaja: AI (Cline), projekti tööreeglite kohaselt. Alusmaterjal: projekti tehniline analüüs ja kasutaja juhised.

# TODO

- [ ] Rakenduse (`ttu_loeng`) worker peab oskama arvestada, et tööjärg antakse ORDS-i poolt tööle, mida `ttu_loeng` poolel enam ei eksisteeri (nt on kustutatud/soft-deleted). Sel puhul peab rakendus töö ORDS-i poolel korrektselt lõpetama (nt staatus `INTERRUPTED`), et see järjekorrast eemaldada.

