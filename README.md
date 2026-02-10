# 📊 Robot Efficiency Analytics Suite

Piattaforma di analisi predittiva per celle robotiche ABB - Industry 4.0

## Panoramica

Sistema completo di monitoraggio OEE (Overall Equipment Effectiveness) con anomaly detection, predictive maintenance e dashboard automatiche. Trasforma dati grezzi di produzione in insight actionable per la manutenzione proattiva.

## Architettura
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Input Dati     │────▶│  Analytics Engine │────▶│  Dashboard HTML │
│  (CSV/API/DB)   │     │  (Pandas/Scikit)  │     │  (Statica)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
│
▼
┌──────────────────┐
│  Alert System    │
│  + Predictions   │
└──────────────────┘

## Funzionalità

### 🔍 Analisi Descrittiva
- OEE calcolato con formula completa: Disponibilità × Performance × Qualità
- Benchmark comparativo multi-robot
- Trend temporali con medie mobili

### ⚠️ Anomaly Detection
- Soglie dinamiche per temperatura motore (>60°C warning, >70°C critical)
- Pattern errori collisione anomali
- Degradazione efficienza sotto 75%

### 🔮 Predictive Maintenance
- Regressione trend efficienza ultimi 7 giorni
- Predizione giorni rimanenti alla soglia critica (60% OEE)
- Prioritizzazione interventi

### 📈 Visualizzazione
- Heatmap correlazioni (temperatura vs errori vs efficienza)
- Scatter plot efficienza vs consumo energetico
- Forecast manutenzione con color coding

  ## Utilizzo


1. Genera dati demo (per test)


```
python efficiency_analytics.py
```
2. Usa dati reali (vedi sezione sotto)
Modifica la fonte dati in main():

Python

Opzione A: Da CSV
```
df = pd.read_csv('dati_realiproduzione.csv')
```

Opzione B: Da API SCADA
```
df = fetch_scada_data(start_date, end_date)
```

Rinomina colonne se necessario
```
df = df.rename(columns={
    'Robot': 'robot_id',
    'DataOra': 'data',
    'Pezzi': 'pezzi_prodotti',
    'FermoMin': 'tempo_fermo_minuti',
    'TempMot': 'temperatura_motore_c'
    # ... altre colonne
})
```

## Output

oee_trend.png	Grafico	    Andamento OEE 30 giorni per robot <br>
efficiency_comparison.png	    Grafico	Benchmark KPI multi-metrica <br>
correlation_heatmap.png	    Grafico	Matrice correlazioni <br>
maintenance_forecast.png	    Grafico	Timeline predittiva manutenzione <br>
report.html  	  Dashboard	Report interattivo completo <br>
robot_data.csv	    Dataset	Dati processati esportati <br>

## Struttura Dati Richiesta

Per utilizzare dati reali, il sistema si aspetta un DataFrame pandas con queste colonne:

| Colonna                | Tipo     | Descrizione                    | Esempio               |
| ---------------------- | -------- | ------------------------------ | --------------------- |
| `robot_id`             | string   | Identificativo univoco robot   | "ABB\_001"            |
| `data`                 | datetime | Timestamp registrazione        | "2024-01-15 08:30:00" |
| `pezzi_prodotti`       | int      | Pezzi buoni prodotti nel turno | 245                   |
| `tempo_ciclo_medio`    | float    | Tempo ciclo medio in secondi   | 28.5                  |
| `tempo_fermo_minuti`   | int      | Minuti di fermo macchina       | 15                    |
| `errori_collisione`    | int      | Numero collisioni rilevate     | 0                     |
| `consumo_energia_kwh`  | float    | Energia consumata in kWh       | 12.5                  |
| `temperatura_motore_c` | float    | Temperatura motore °C          | 58.2                  |
| `ore_operative`        | float    | Ore turno operative            | 8.0                   |

Campo calcolato automaticamente: efficienza_oee (se non presente)

## Formato File Input

CSV (Raccomandato)
```
robot_id,data,pezzi_prodotti,tempo_ciclo_medio,tempo_fermo_minuti,errori_collisione,consumo_energia_kwh,temperatura_motore_c,ore_operative 
ABB_001,2024-01-15 06:00:00,180,32.5,20,0,15.2,55.0,8 
ABB_001,2024-01-15 14:00:00,195,30.2,10,1,14.8,58.5,8 
ABB_002,2024-01-15 06:00:00,210,28.0,5,0,13.1,52.0,8 
```

## Integrazione Dati Reali

Estrazione da Controller ABB

RobotStudio: Esportazione log di produzione <br>
OPC UA: Lettura realtime variabili RAPID <br>
FTP dal controller: File di log ciclici <br>

Esempio parsing log ABB reale
```
def parse_abb_log(file_path):
    """
    Estrae dati da log controller ABB (formato testo)
    """
    records = []
    with open(file_path, 'r') as f:
        for line in f:
            if 'Cycle completed' in line:
                # Parsing linea log
                timestamp = extract_timestamp(line)
                cycle_time = extract_cycle_time(line)
                pieces = extract_piece_count(line)
                
                records.append({
                    'data': timestamp,
                    'tempo_ciclo_medio': cycle_time,
                    'pezzi_prodotti': pieces,
                    # ... altri campi
                })
    return pd.DataFrame(records)
```

## Connessione Database Aziendale
```
import sqlalchemy

def fetch_from_db(start_date, end_date):
    engine = sqlalchemy.create_engine('postgresql://user:pass@host/db')
    query = f"""
    SELECT robot_id, timestamp as data, 
           pezzi_prodotti, tempo_ciclo, 
           tempi_fermo, errori_count,
           consumo_kw, temp_motore
    FROM produzione.robot_logs
    WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
    """
    return pd.read_sql(query, engine)
```
    

KPI Calcolati
| KPI               | Formula                                                                 | Target Industriale |
| ----------------- | ----------------------------------------------------------------------- | ------------------ |
| **OEE**           | (TempoProduttivo/TempoDisponibile) × (CicloIdeale/CicloReale) × Qualità | > 85%              |
| **Disponibilità** | (OreOperative - Fermo) / OreOperative                                   | > 90%              |
| **Performance**   | PezziTeorici / PezziEffettivi                                           | > 95%              |
| **Costo/Pezzo**   | kWhConsumati / PezziProdotti                                            | Minimizzare        |

Dashboard HTML
Il file report.html generato include:
✅ KPI cards aggiornate
✅ Sistema alert visivo
✅ Grafici interattivi (immagini)
✅ Tabelle performance
✅ Predictive maintenance timeline

## Installazione

```bash
git clone https://github.com/tuousername/robot-efficiency-analytics.git
cd robot-efficiency-analytics
pip install -r requirements.txt
