# LDES Light Application

Een lichtgewicht LDES-applicatie geschreven in Python met FastAPI, ontworpen om RDF-data op te slaan en te exposen volgens de LDES-specificatie.

## Functionaliteiten
- Ontvangt RDF-data in alle RDF-formaten.
- Groepeert data per named node (URI) met bijbehorende blank nodes.
- Schrijft data naar pagina's van maximaal 250 objecten.
- Voegt LDES-specifieke metadata toe aan elke pagina.
- Exposeert RDF-pagina's via HTTP.
- `/finalize` endpoint om resterende data weg te schrijven.

## Installatie en Gebruik

### Docker Build en Run
```bash
docker-compose build
docker-compose up
```

### RDF Data Ingest
```bash
curl -X POST -H "Content-Type: text/turtle" --data-binary "@yourfile.ttl" http://localhost:8000/ingest
```

### Finalize de data
```bash
curl -X POST http://localhost:8000/finalize
```

### Bekijk de LDES Stream
```bash
curl http://localhost:8000/ldes
```
