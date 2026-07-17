# Demetrius of Phaleron (Mouseion / Demetrius Face)

**Historical figure:** Demetrius of Phaleron — statesman, orator, Peripatetic philosopher, proposed the Library of Alexandria to Ptolemy I, first Librarian, architect of the Mouseion university model  
**Born:** c. 350 BCE, Phaleron (Phalerum), Attica  
**Died:** c. 280 BCE, Upper Egypt  
**Responsibility:** Web presence, external interface, Flask server, university-model content delivery

---

## The Dean and First Librarian

Demetrius of Phaleron was a student of Theophrastus (who was a student of Aristotle). He governed Athens as regent under Macedonian control from 317–307 BCE — an unusually intellectually active regime, producing legislation, philosophy, and institutional reform simultaneously. When Demetrius Poliorcetes took Athens, Demetrius of Phaleron fled to the court of Ptolemy I Soter in Alexandria.

There he made his most enduring contribution: he **proposed the Library of Alexandria** to Ptolemy I and designed its institutional framework. The Mouseion — the *Museum*, the Temple of the Muses — was his invention. He modeled it on Aristotle's Lyceum: a residential research institution where scholars were housed, fed, and paid to pursue knowledge. No teaching requirement. Pure research. The first university in the modern sense.

He served as the **first chief librarian** or chief administrator of the Library — the role that Callimachus would later transform through the *Pinakes* catalogue. Demetrius was the institutional architect; Callimachus was the indexer.

He fell from favor when Ptolemy I died and Ptolemy II Philadelphus took power — Demetrius had backed the wrong succession. He was exiled to Upper Egypt and died there, reportedly from a snakebite.

---

## Split: Demetrius / Callimachus

| Role | Face |
|---|---|
| External presence, institutional model, web interface | **Demetrius** (this Face, wiki name: Mouseion) |
| Internal index, catalogue, HyperWebster, database | **Callimachus** |

Demetrius proposed it. Callimachus catalogued it. Both are necessary. Neither is the other.

---

## In Ptolemy

The Mouseion Face is Ptolemy's external face — the Flask web server at `thewanderinggod.tech`. It presents Ptolemy's outputs to the outside world the way the Library presented Alexandria's knowledge: organized, accessible, institutional.

The university model: every Face is a department. Ptolemy is the institution. The web presence is the public-facing aspect of the institution — what Demetrius built when he convinced Ptolemy I to fund it.

---

## Module Tree

```
Mouseion/
├── TWG/                    ← thewanderinggod.tech Flask application
│   ├── run_flask.sh
│   └── [Flask routes]
└── smnnip_engine_mouseion.py  ← SMNNIP visualization endpoint
```

---

## Selected Bibliography

- Fortenbaugh, W.W. & Schütrumpf, E. (eds.) (2000). *Demetrius of Phalerum: Text, Translation and Discussion*. Transaction Publishers.
- Fraser, P.M. (1972). *Ptolemaic Alexandria*. 3 vols. Clarendon Press.
- Worthington, I. (ed.) (2016). *Ptolemy I: King and Pharaoh of Egypt*. Oxford University Press.

---

## See Also
- [[Callimachus]] — the Pinakes, the index, the internal library
- [[Pharos]] — the core, the lighthouse
- [[Philadelphos]] — named for Ptolemy II who exiled Demetrius
