# 📊 Robot Efficiency Analytics Suite

Piattaforma di analisi predittiva per celle robotiche ABB - Industry 4.0 ready.

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
Copy

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

## Installazione

```bash
git clone https://github.com/tuousername/robot-efficiency-analytics.git
cd robot-efficiency-analytics
pip install -r requirements.txt
