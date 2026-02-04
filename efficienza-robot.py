"""
Robot Efficiency Analytics Suite
Analisi predittiva e reportistica per celle robotiche ABB - Industry 4.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple
import json
import warnings
warnings.filterwarnings('ignore')

# Configurazione stile
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============ CLASSI DATI ============

@dataclass
class RobotTelemetry:
    """Dati telemetrici di un robot industriale"""
    robot_id: str
    timestamp: datetime
    pezzi_prodotti: int
    tempo_ciclo_medio: float  # secondi
    tempo_fermo: int  # minuti
    errori_collisione: int
    consumo_energia: float  # kWh
    temperatura_motore: float  # °C
    ore_operative: float
    
    @property
    def efficienza(self) -> float:
        """OEE semplificato: disponibilità * performance"""
        tempo_disponibile = self.ore_operative * 60  # minuti
        tempo_produttivo = tempo_disponibile - self.tempo_fermo
        if tempo_disponibile == 0:
            return 0
        disponibilita = tempo_produttivo / tempo_disponibile
        
        # Performance: cicli teorici vs reali
        cicli_teorici = tempo_produttivo * 60 / 30  # assumiamo 30s ciclo ideale
        if cicli_teorici == 0:
            return 0
        performance = self.pezzi_prodotti / cicli_teorici
        
        return (disponibilita * performance) * 100

@dataclass
class Alert:
    """Sistema di alert predittivo"""
    robot_id: str
    tipo: str
    livello: str  # 'warning', 'critical'
    messaggio: str
    valore_attuale: float
    soglia: float

# ============ GENERATORE DATI REALISTICI ============

class RobotDataGenerator:
    """Genera dati sintetici realistici per simulazione"""
    
    def __init__(self, start_date: datetime, days: int = 30):
        self.start_date = start_date
        self.days = days
        self.robots = ['ABB_001', 'ABB_002', 'ABB_003', 'ABB_004']
        
    def generate(self) -> pd.DataFrame:
        """Genera dataset giornaliero per ogni robot"""
        records = []
        
        for day in range(self.days):
            current_date = self.start_date + timedelta(days=day)
            
            for robot in self.robots:
                # Pattern realistici: robot diversi hanno caratteristiche diverse
                base_efficiency = {
                    'ABB_001': 0.85,  # Robot nuovo, efficiente
                    'ABB_002': 0.78,  # Robot medio, qualche problema
                    'ABB_003': 0.92,  # Robot ottimizzato
                    'ABB_004': 0.65   # Robot vecchio, necessita manutenzione
                }[robot]
                
                # Variazione giornaliera
                noise = np.random.normal(0, 0.05)
                daily_eff = max(0.3, min(1.0, base_efficiency + noise))
                
                # Calcola metriche in base all'efficienza
                ore_operative = 16  # 2 turni
                tempo_fermo = int((1 - daily_eff) * ore_operative * 60 * np.random.uniform(0.5, 1.5))
                
                # Pezzi prodotti dipende dall'efficienza
                ciclo_ideale = 30  # secondi
                pezzi_teorici = (ore_operative * 3600) / ciclo_ideale
                pezzi_reali = int(pezzi_teorici * daily_eff * np.random.uniform(0.9, 1.0))
                
                # Errori correlati all'età del robot
                base_errors = {'ABB_001': 0.1, 'ABB_002': 0.3, 'ABB_003': 0.05, 'ABB_004': 0.8}
                errori = np.random.poisson(base_errors[robot] * (1 - daily_eff) * 5)
                
                # Temperatura correlata al carico
                temperatura = 45 + (1 - daily_eff) * 20 + np.random.normal(0, 3)
                
                # Energia correlata ai pezzi prodotti
                energia = pezzi_reali * 0.05 + tempo_fermo * 0.1
                
                records.append({
                    'robot_id': robot,
                    'data': current_date,
                    'pezzi_prodotti': pezzi_reali,
                    'tempo_ciclo_medio': ciclo_ideale / daily_eff,
                    'tempo_fermo_minuti': tempo_fermo,
                    'errori_collisione': errori,
                    'consumo_energia_kwh': round(energia, 2),
                    'temperatura_motore_c': round(temperatura, 1),
                    'ore_operative': ore_operative,
                    'efficienza_oee': round(daily_eff * 100, 2)
                })
        
        return pd.DataFrame(records)

# ============ ANALISI PREDITTIVA ============

class PredictiveAnalyzer:
    """Analisi predittiva e anomaly detection"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.alerts: List[Alert] = []
        
    def detect_anomalies(self) -> List[Alert]:
        """Identifica robot con performance anomale"""
        latest = self.df.groupby('robot_id').last().reset_index()
        
        for _, row in latest.iterrows():
            # Alert temperatura
            if row['temperatura_motore_c'] > 70:
                self.alerts.append(Alert(
                    row['robot_id'], 'Temperatura', 'critical',
                    f"Sovraccarico termico rilevato", 
                    row['temperatura_motore_c'], 70
                ))
            elif row['temperatura_motore_c'] > 60:
                self.alerts.append(Alert(
                    row['robot_id'], 'Temperatura', 'warning',
                    f"Temperatura elevata", 
                    row['temperatura_motore_c'], 60
                ))
            
            # Alert efficienza
            if row['efficienza_oee'] < 50:
                self.alerts.append(Alert(
                    row['robot_id'], 'Efficienza', 'critical',
                    f"OEE critico: manutenzione richiesta",
                    row['efficienza_oee'], 50
                ))
            elif row['efficienza_oee'] < 75:
                self.alerts.append(Alert(
                    row['robot_id'], 'Efficienza', 'warning',
                    f"Efficienza sotto la media",
                    row['efficienza_oee'], 75
                ))
            
            # Alert errori
            if row['errori_collisione'] > 3:
                self.alerts.append(Alert(
                    row['robot_id'], 'Collisioni', 'critical',
                    f"Pattern collisioni anomalo - verificare programma",
                    row['errori_collisione'], 3
                ))
        
        return self.alerts
    
    def predict_maintenance(self) -> Dict[str, float]:
        """Predice giorni rimanenti alla prossima manutenzione"""
        predictions = {}
        
        for robot in self.df['robot_id'].unique():
            robot_data = self.df[self.df['robot_id'] == robot].copy()
            
            # Trend efficienza ultimi 7 giorni
            if len(robot_data) >= 7:
                recent = robot_data.tail(7)['efficienza_oee'].values
                trend = np.polyfit(range(7), recent, 1)[0]  # pendenza
                
                # Se trend negativo, calcola quando scende sotto 60%
                if trend < 0:
                    current = recent[-1]
                    days_to_maintenance = (current - 60) / abs(trend)
                    predictions[robot] = max(0, round(days_to_maintenance, 1))
                else:
                    predictions[robot] = 999  # Stabile
            else:
                predictions[robot] = 999
        
        return predictions
    
    def benchmark_analysis(self) -> pd.DataFrame:
        """Confronto performance tra robot"""
        summary = self.df.groupby('robot_id').agg({
            'pezzi_prodotti': 'sum',
            'tempo_fermo_minuti': 'sum',
            'errori_collisione': 'sum',
            'consumo_energia_kwh': 'sum',
            'efficienza_oee': 'mean',
            'temperatura_motore_c': 'max'
        }).reset_index()
        
        # Ranking
        summary['ranking'] = summary['efficienza_oee'].rank(ascending=False)
        summary['costo_pezzo'] = summary['consumo_energia_kwh'] / summary['pezzi_prodotti']
        
        return summary.round(2)

# ============ VISUALIZZAZIONE ============

class EfficiencyDashboard:
    """Genera dashboard statiche per report"""
    
    def __init__(self, df: pd.DataFrame, analyzer: PredictiveAnalyzer):
        self.df = df
        self.analyzer = analyzer
        
    def generate_oee_trend(self, save_path: str = "oee_trend.png"):
        """Andamento OEE nel tempo"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('OEE Trend Analysis - Ultimi 30 Giorni', fontsize=16, fontweight='bold')
        
        robots = self.df['robot_id'].unique()
        
        for idx, robot in enumerate(robots):
            ax = axes[idx // 2, idx % 2]
            robot_data = self.df[self.df['robot_id'] == robot].sort_values('data')
            
            # Linea OEE
            ax.plot(robot_data['data'], robot_data['efficienza_oee'], 
                   marker='o', linewidth=2, markersize=4, label='OEE')
            
            # Media mobile
            if len(robot_data) >= 7:
                rolling = robot_data['efficienza_oee'].rolling(window=7).mean()
                ax.plot(robot_data['data'], rolling, '--', alpha=0.7, label='Media 7gg')
            
            # Soglie
            ax.axhline(y=85, color='green', linestyle='--', alpha=0.5, label='Target')
            ax.axhline(y=60, color='red', linestyle='--', alpha=0.5, label='Critico')
            
            ax.set_title(f'{robot}', fontweight='bold')
            ax.set_ylabel('OEE %')
            ax.legend(fontsize=8)
            ax.tick_params(axis='x', rotation=45)
            
            # Colora sfondo se critico
            latest = robot_data['efficienza_oee'].iloc[-1]
            if latest < 60:
                ax.set_facecolor('#ffcccc')
            elif latest < 75:
                ax.set_facecolor('#ffffcc')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ Salvato: {save_path}")
    
    def generate_efficiency_comparison(self, save_path: str = "efficiency_comparison.png"):
        """Confronto multi-metrico"""
        summary = self.analyzer.benchmark_analysis()
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Performance Benchmark - Robot ABB', fontsize=16, fontweight='bold')
        
        # 1. OEE Medio
        ax1 = axes[0, 0]
        colors = ['#2ecc71' if x > 85 else '#f1c40f' if x > 70 else '#e74c3c' 
                  for x in summary['efficienza_oee']]
        bars = ax1.bar(summary['robot_id'], summary['efficienza_oee'], color=colors)
        ax1.set_ylabel('OEE %')
        ax1.set_title('Efficienza Media OEE')
        ax1.axhline(y=85, color='green', linestyle='--', alpha=0.5)
        for i, v in enumerate(summary['efficienza_oee']):
            ax1.text(i, v + 1, f'{v}%', ha='center', fontweight='bold')
        
        # 2. Pezzi prodotti
        ax2 = axes[0, 1]
        ax2.bar(summary['robot_id'], summary['pezzi_prodotti'], color='#3498db')
        ax2.set_ylabel('Pezzi Totali')
        ax2.set_title('Produzione 30 Giorni')
        for i, v in enumerate(summary['pezzi_prodotti']):
            ax2.text(i, v + 50, str(v), ha='center', fontweight='bold')
        
        # 3. Tempo fermo
        ax3 = axes[1, 0]
        ax3.bar(summary['robot_id'], summary['tempo_fermo_minuti'], color='#e74c3c')
        ax3.set_ylabel('Minuti')
        ax3.set_title('Tempo Fermo Totale')
        
        # 4. Scatter: Efficienza vs Costo Energetico
        ax4 = axes[1, 1]
        scatter = ax4.scatter(summary['efficienza_oee'], summary['costo_pezzo'], 
                            s=summary['pezzi_prodotti']/10, alpha=0.6, c=range(len(summary)), cmap='viridis')
        ax4.set_xlabel('OEE %')
        ax4.set_ylabel('kWh / Pezzo')
        ax4.set_title('Efficienza vs Consumo Specifico')
        for i, robot in enumerate(summary['robot_id']):
            ax4.annotate(robot, (summary['efficienza_oee'].iloc[i], summary['costo_pezzo'].iloc[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ Salvato: {save_path}")
    
    def generate_heatmap(self, save_path: str = "correlation_heatmap.png"):
        """Heatmap correlazioni"""
        # Pivot per correlazione temporale
        pivot_eff = self.df.pivot(index='data', columns='robot_id', values='efficienza_oee')
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Heatmap efficienza nel tempo
        sns.heatmap(pivot_eff.T, annot=False, cmap='RdYlGn', center=75, 
                   vmin=50, vmax=100, ax=axes[0], cbar_kws={'label': 'OEE %'})
        axes[0].set_title('OEE Heatmap - Evoluzione Temporale')
        axes[0].set_xlabel('Data')
        
        # Correlazione tra metriche
        corr_cols = ['efficienza_oee', 'temperatura_motore_c', 'tempo_fermo_minuti', 
                     'errori_collisione', 'consumo_energia_kwh']
        corr = self.df[corr_cols].corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, ax=axes[1],
                   square=True, fmt='.2f')
        axes[1].set_title('Correlazione Metriche')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ Salvato: {save_path}")
    
    def generate_maintenance_forecast(self, save_path: str = "maintenance_forecast.png"):
        """Visualizzazione predizione manutenzione"""
        predictions = self.analyzer.predict_maintenance()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        robots = list(predictions.keys())
        days = [predictions[r] if predictions[r] < 999 else 30 for r in robots]
        colors = ['#e74c3c' if d < 7 else '#f1c40f' if d < 14 else '#2ecc71' for d in days]
        
        bars = ax.barh(robots, days, color=colors)
        ax.set_xlabel('Giorni stimati alla manutenzione')
        ax.set_title('Predictive Maintenance Forecast', fontsize=14, fontweight='bold')
        ax.axvline(x=7, color='red', linestyle='--', alpha=0.5, label='Urgente (<7gg)')
        ax.axvline(x=14, color='orange', linestyle='--', alpha=0.5, label='Pianificare (<14gg)')
        
        for i, (bar, day) in enumerate(zip(bars, days)):
            width = bar.get_width()
            label = f'{int(day)} gg' if day < 999 else 'Stabile'
            ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                   label, ha='left', va='center', fontweight='bold')
        
        ax.legend()
        ax.set_xlim(0, max(days) + 5)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ Salvato: {save_path}")

# ============ REPORT HTML ============

class HTMLReportGenerator:
    """Genera report HTML statico per il portfolio"""
    
    def __init__(self, df: pd.DataFrame, analyzer: PredictiveAnalyzer):
        self.df = df
        self.analyzer = analyzer
        
    def generate(self, output_file: str = "report.html"):
        """Crea report HTML completo"""
        summary = self.analyzer.benchmark_analysis()
        alerts = self.analyzer.detect_anomalies()
        predictions = self.analyzer.predict_maintenance()
        
        # HTML template
        html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robot Efficiency Analytics - Industry 4.0</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .kpi-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .kpi-label {{
            font-size: 0.9em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .alert-section {{
            margin: 30px 0;
        }}
        .alert {{
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 5px solid;
        }}
        .alert-critical {{
            background: #ffebee;
            border-color: #f44336;
            color: #c62828;
        }}
        .alert-warning {{
            background: #fff3e0;
            border-color: #ff9800;
            color: #ef6c00;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .chart-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-card img {{
            width: 100%;
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        th {{
            background: #2a5298;
            color: white;
            padding: 15px;
            text-align: left;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-success {{ background: #4caf50; color: white; }}
        .badge-warning {{ background: #ff9800; color: white; }}
        .badge-danger {{ background: #f44336; color: white; }}
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Robot Efficiency Analytics</h1>
            <p>Dashboard Industry 4.0 - Analisi Predittiva Celle Robotiche ABB</p>
            <p>Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="content">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">OEE Medio Impianto</div>
                    <div class="kpi-value">{summary['efficienza_oee'].mean():.1f}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Produzione Totale</div>
                    <div class="kpi-value">{summary['pezzi_prodotti'].sum():,}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Tempo Fermo Totale</div>
                    <div class="kpi-value">{summary['tempo_fermo_minuti'].sum()}m</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Alert Attivi</div>
                    <div class="kpi-value">{len([a for a in alerts if a.livello == 'critical'])}</div>
                </div>
            </div>
            
            <div class="alert-section">
                <h2>🚨 Sistema Alert Predittivo</h2>
                {self._generate_alerts_html(alerts)}
            </div>
            
            <div class="chart-grid">
                <div class="chart-card">
                    <h3>Andamento OEE</h3>
                    <img src="oee_trend.png" alt="OEE Trend">
                </div>
                <div class="chart-card">
                    <h3>Benchmark Performance</h3>
                    <img src="efficiency_comparison.png" alt="Comparison">
                </div>
                <div class="chart-card">
                    <h3>Analisi Correlazioni</h3>
                    <img src="correlation_heatmap.png" alt="Heatmap">
                </div>
                <div class="chart-card">
                    <h3>Predizione Manutenzione</h3>
                    <img src="maintenance_forecast.png" alt="Maintenance">
                </div>
            </div>
            
            <h2>📊 Tabella Performance Dettagliata</h2>
            {summary.to_html(index=False, classes='summary-table', 
                           formatters={'efficienza_oee': lambda x: f'<span class="badge {"badge-success" if x > 85 else "badge-warning" if x > 70 else "badge-danger"}">{x}%</span>'},
                           escape=False)}
            
            <h2>🔮 Predictive Maintenance</h2>
            <table>
                <tr><th>Robot</th><th>Giorni alla Manutenzione</th><th>Stato</th></tr>
                {''.join(f"<tr><td>{robot}</td><td>{int(days) if days < 999 else 'N/A'} gg</td><td>{'<span class=\'badge badge-danger\'>Urgente</span>' if days < 7 else '<span class=\'badge badge-warning\'>Pianificare</span>' if days < 14 else '<span class=\'badge badge-success\'>Stabile</span>'}</td></tr>" for robot, days in predictions.items())}
            </table>
        </div>
        
        <div class="footer">
            <p>Strumento sviluppato con Python, Pandas, Scikit-learn | Applicazione Industry 4.0</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ Report HTML generato: {output_file}")

    def _generate_alerts_html(self, alerts: List[Alert]) -> str:
        """Genera HTML per gli alert"""
        if not alerts:
            return '<div class="alert" style="background:#e8f5e9; border-color:#4caf50; color:#2e7d32;">✅ Nessun alert attivo - Sistema operativo nella norma</div>'
        
        html = ""
        for alert in alerts:
            css_class = f"alert-{alert.livello}"
            icon = "🔴" if alert.livello == "critical" else "⚠️"
            html += f'<div class="alert {css_class}">{icon} <strong>{alert.robot_id}</strong> - {alert.tipo}: {alert.messaggio} (Valore: {alert.valore_attuale:.1f}, Soglia: {alert.soglia})</div>'
        return html

# ============ MAIN ============

def main():
    print("🤖 Robot Efficiency Analytics Suite")
    print("=" * 50)
    
    # 1. Genera dati
    print("\n📊 Generazione dati storici (30 giorni)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    generator = RobotDataGenerator(start_date, days=30)
    df = generator.generate()
    print(f"   Generati {len(df)} record")
    
    # 2. Analisi
    print("\n🔍 Analisi predittiva...")
    analyzer = PredictiveAnalyzer(df)
    alerts = analyzer.detect_anomalies()
    predictions = analyzer.predict_maintenance()
    summary = analyzer.benchmark_analysis()
    
    print(f"   Alert rilevati: {len(alerts)}")
    print(f"   Previsioni manutenzione: {len([p for p in predictions.values() if p < 999])} robot in degradazione")
    
    # 3. Visualizzazioni
    print("\n📈 Generazione dashboard...")
    dashboard = EfficiencyDashboard(df, analyzer)
    dashboard.generate_oee_trend("outputs/oee_trend.png")
    dashboard.generate_efficiency_comparison("outputs/efficiency_comparison.png")
    dashboard.generate_heatmap("outputs/correlation_heatmap.png")
    dashboard.generate_maintenance_forecast("outputs/maintenance_forecast.png")
    
    # 4. Report HTML
    print("\n🌐 Generazione report HTML...")
    report_gen = HTMLReportGenerator(df, analyzer)
    report_gen.generate("outputs/report.html")
    
    # 5. Salva dati
    df.to_csv("outputs/robot_data.csv", index=False)
    print("\n💾 Dati esportati in outputs/robot_data.csv")
    
    print("\n" + "=" * 50)
    print("✅ ANALISI COMPLETATA")
    print("=" * 50)
    print("\n📁 File generati in /outputs:")
    print("   • oee_trend.png - Andamento efficienza temporale")
    print("   • efficiency_comparison.png - Benchmark robot")
    print("   • correlation_heatmap.png - Heatmap correlazioni")
    print("   • maintenance_forecast.png - Predizione manutenzione")
    print("   • report.html - Dashboard interattiva completa")
    print("   • robot_data.csv - Dataset completo")

if __name__ == "__main__":
    import os
    os.makedirs('outputs', exist_ok=True)
    main()