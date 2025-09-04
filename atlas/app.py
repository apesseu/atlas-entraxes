"""
Atlas Entraxes - Visualisation des altitudes maximales par département

Application Dash pour afficher une carte interactive des limites d'altitude
pour différentes configurations de serres selon les zones vent/neige.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np
import functools
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import argparse
import warnings

import dash
from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import plotly.graph_objects as go

from config import (
    check_required_files, 
    GEOJSON_PATH, ZONES_PATH, RULES_PATH,
    ZONES_DTYPES, RULES_DTYPES
)
from utils import compute_centroids, build_modern_color_palette

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Atlas Entraxes - Visualisation des altitudes maximales par département'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=8050,
        help='Port du serveur (défaut: 8050)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Adresse d\'écoute (défaut: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Active le mode debug'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Supprime les warnings pandas'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Désactive le cache LRU'
    )
    
    return parser.parse_args()

def setup_logging(quiet=False):
    if quiet:
        warnings.filterwarnings("ignore", category=FutureWarning)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

def initialize_app(use_cache=True):
    check_required_files()

    geojson = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    zones = pd.read_csv(ZONES_PATH, dtype=ZONES_DTYPES)
    rules = pd.read_csv(RULES_PATH, dtype=RULES_DTYPES)

    details = pd.DataFrame()
    details_lock = threading.Lock()

    try:
        from config import DETAILS_PATH
        if DETAILS_PATH.exists():
            detail_dtypes = {
                "Config": "string", "Type_Serre": "string", "Hauteur_Poteau": "string",
                "Largeur": "string", "Toiture": "string", "Facade": "string", 
                "Traverse": "string", "Materiau": "string", "Resistance_Vent": "string",
                "Date_Creation": "string", "Version": "string"
            }
            details = pd.read_csv(DETAILS_PATH, dtype=detail_dtypes)
            print(f"✅ Détails chargés : {len(details)} configurations")
            print(f"📋 Configurations disponibles : {', '.join(details['Config'].unique())}")
        else:
            print(f"⚠️ Fichier de détails introuvable : {DETAILS_PATH}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement des détails : {e}")
        details = pd.DataFrame()

    cent_df = compute_centroids(geojson)

    all_configs = sorted(rules["Config"].dropna().unique())
    all_entraxes = ["AltMax_3m", "AltMax_2_5m"]

    precomputed_data = {}
    precomputed_stats = {}
    precomputed_colors = {}

    if use_cache:
        @functools.lru_cache(maxsize=16)
        def get_color_palette_cached(labels_tuple):
            return build_modern_color_palette(list(labels_tuple))

        @functools.lru_cache(maxsize=50)
        def create_base_choropleth_cached(config, entraxe_col, labels_tuple, df_hash):
            key = (config, entraxe_col)
            df = precomputed_data[key]
            labels_order = list(labels_tuple)
            cmap = get_color_palette_cached(labels_tuple)
            
            fig = px.choropleth(
                df,
                geojson=geojson,
                locations="Dept",
                featureidkey="properties.code",
                color="Label",
                category_orders={"Label": labels_order},
                color_discrete_map=cmap,
                hover_name="Nom",
                hover_data={"Dept": True, "AltMax_sel": ":.0f"},
            )

            fig.update_traces(
                marker_line_color="#ffffff",
                marker_line_width=0.5,
                selector=dict(type="choropleth"),
                hoverinfo="none",
            )
            
            fig.update_geos(
                showframe=False,
                showcoastlines=False,
                projection_type="mercator",
                lonaxis_range=[-5.5, 9.5],
                lataxis_range=[41.0, 51.5],
                bgcolor='#ffffff',
                showocean=True,
                oceancolor='#ffffff',
                showlakes=True,
                lakecolor='#ffffff',
                showland=True,
                landcolor='#ffffff',
                resolution=50
            )
            
            fig.update_layout(
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor='#ffffff',
                paper_bgcolor='#ffffff',
                height=None,
                showlegend=True,
                uirevision='constant',
                autosize=True,
                dragmode='pan',
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=1.02,
                    xanchor="center", 
                    x=0.5,
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#e2e8f0",
                    borderwidth=1,
                    font=dict(size=12, color="#1e293b")
                )
            )
            
            return fig

        @functools.lru_cache(maxsize=100)
        def get_detail_values_cached(config):
            detail_values = {
                "Type_Serre": "—",
                "Hauteur_Poteau": "—", 
                "Largeur": "—",
                "Toiture": "—",
                "Facade": "—",
                "Traverse": "—"
            }

            with details_lock:
                if not details.empty and "Config" in details.columns:
                    matching_configs = details[details["Config"] == config]
                    if not matching_configs.empty:
                        config_row = matching_configs.iloc[0]
                        for key in detail_values.keys():
                            if key in config_row.index:
                                value = config_row[key]
                                if pd.notna(value) and str(value).strip() != "":
                                    detail_values[key] = str(value)
            
            return detail_values

        @functools.lru_cache(maxsize=10)
        def get_usage_panel_cached():
            return html.Div([
                html.P("Calculs: Catégorie de terrain II (EN 13031)", style={'color': '#374151', 'margin': '0 0 6px 0'}),
                html.P("Catégorie I: étude BE obligatoire", style={'color': '#b91c1c', 'fontWeight': '600', 'margin': '0 0 8px 0'}),
                html.P("Altitude max = Vent × Neige pour la configuration affichée.", style={'color': '#6b7280', 'margin': '0 0 4px 0'}),
                html.P("Outil d'aide commerciale — ne remplace pas une note de calcul.", style={'color': '#6b7280', 'margin': 0})
            ])

        @functools.lru_cache(maxsize=10)
        def get_conditions_panel_cached():
            return html.Div([
                html.Div("Portée", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Carte d'aide à la vente indiquant l'altitude maximale admissible par département pour la configuration sélectionnée."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Hypothèses de calcul", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Norme EN 13031."),
                    html.Li("Catégorie de terrain II (site relativement plat et dégagé)."),
                    html.Li("Sans particularités locales ni corrections d'effet de site."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Définitions", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Altitude max: valeur indicative issue du croisement Zones Vent × Neige pour la configuration affichée."),
                    html.Li("Non admissible: aucune règle ne permet un entraxe conforme pour cette configuration dans le département."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Cas non couverts / limites", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Catégorie de terrain I (sites très exposés: littoral, plateaux ouverts, etc.)."),
                    html.Li("Relief marqué, couloirs de vent, bords de falaises, effets d'obstacles/bâtiments voisins."),
                    html.Li("Microclimats, altitude du site élevée, règles locales particulières, matériaux/charges spécifiques."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Responsabilités", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Outil d'aide commerciale; ne remplace pas une note de calcul."),
                    html.Li("En cas de doute, de site exposé (Cat. I) ou de condition non couverte, solliciter le bureau d'études avant toute offre."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Données et mise à jour", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Zones Vent/Neige selon sources en vigueur à la date de mise à jour indiquée."),
                    html.Li("Les évolutions réglementaires peuvent modifier les résultats; vérifier la version la plus récente."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Avertissement important", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li(html.Span([html.Span("Catégorie I: ", style={'fontWeight': '700', 'color': '#b91c1c'}), "la carte n'est pas applicable; étude BE obligatoire avant toute décision."]))
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Dernière mise à jour: JJ/MM/AAAA", style={'marginTop': '10px', 'color': '#6b7280', 'fontSize': '12px'})
            ])
    else:
        def get_color_palette_cached(labels_tuple):
            return build_modern_color_palette(list(labels_tuple))

        def create_base_choropleth_cached(config, entraxe_col, labels_tuple, df_hash):
            key = (config, entraxe_col)
            df = precomputed_data[key]
            labels_order = list(labels_tuple)
            cmap = get_color_palette_cached(labels_tuple)
            
            fig = px.choropleth(
                df,
                geojson=geojson,
                locations="Dept",
                featureidkey="properties.code",
                color="Label",
                category_orders={"Label": labels_order},
                color_discrete_map=cmap,
                hover_name="Nom",
                hover_data={"Dept": True, "AltMax_sel": ":.0f"},
            )

            fig.update_traces(
                marker_line_color="#ffffff",
                marker_line_width=0.5,
                selector=dict(type="choropleth"),
                hoverinfo="none",
            )
            
            fig.update_geos(
                showframe=False,
                showcoastlines=False,
                projection_type="mercator",
                lonaxis_range=[-5.5, 9.5],
                lataxis_range=[41.0, 51.5],
                bgcolor='#ffffff',
                showocean=True,
                oceancolor='#ffffff',
                showlakes=True,
                lakecolor='#ffffff',
                showland=True,
                landcolor='#ffffff',
                resolution=50
            )
            
            fig.update_layout(
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor='#ffffff',
                paper_bgcolor='#ffffff',
                height=None,
                showlegend=True,
                uirevision='constant',
                autosize=True,
                dragmode='pan',
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=1.02,
                    xanchor="center", 
                    x=0.5,
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#e2e8f0",
                    borderwidth=1,
                    font=dict(size=12, color="#1e293b")
                )
            )
            
            return fig

        def get_detail_values_cached(config):
            detail_values = {
                "Type_Serre": "—",
                "Hauteur_Poteau": "—", 
                "Largeur": "—",
                "Toiture": "—",
                "Facade": "—",
                "Traverse": "—"
            }

            with details_lock:
                if not details.empty and "Config" in details.columns:
                    matching_configs = details[details["Config"] == config]
                    if not matching_configs.empty:
                        config_row = matching_configs.iloc[0]
                        for key in detail_values.keys():
                            if key in config_row.index:
                                value = config_row[key]
                                if pd.notna(value) and str(value).strip() != "":
                                    detail_values[key] = str(value)
            
            return detail_values

        def get_usage_panel_cached():
            return html.Div([
                html.P("Calculs: Catégorie de terrain II (EN 13031)", style={'color': '#374151', 'margin': '0 0 6px 0'}),
                html.P("Catégorie I: étude BE obligatoire", style={'color': '#b91c1c', 'fontWeight': '600', 'margin': '0 0 8px 0'}),
                html.P("Altitude max = Vent × Neige pour la configuration affichée.", style={'color': '#6b7280', 'margin': '0 0 4px 0'}),
                html.P("Outil d'aide commerciale — ne remplace pas une note de calcul.", style={'color': '#6b7280', 'margin': 0})
            ])

        def get_conditions_panel_cached():
            return html.Div([
                html.Div("Portée", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Carte d'aide à la vente indiquant l'altitude maximale admissible par département pour la configuration sélectionnée."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Hypothèses de calcul", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Norme EN 13031."),
                    html.Li("Catégorie de terrain II (site relativement plat et dégagé)."),
                    html.Li("Sans particularités locales ni corrections d'effet de site."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Définitions", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Altitude max: valeur indicative issue du croisement Zones Vent × Neige pour la configuration affichée."),
                    html.Li("Non admissible: aucune règle ne permet un entraxe conforme pour cette configuration dans le département."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Cas non couverts / limites", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Catégorie de terrain I (sites très exposés: littoral, plateaux ouverts, etc.)."),
                    html.Li("Relief marqué, couloirs de vent, bords de falaises, effets d'obstacles/bâtiments voisins."),
                    html.Li("Microclimats, altitude du site élevée, règles locales particulières, matériaux/charges spécifiques."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Responsabilités", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Outil d'aide commerciale; ne remplace pas une note de calcul."),
                    html.Li("En cas de doute, de site exposé (Cat. I) ou de condition non couverte, solliciter le bureau d'études avant toute offre."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Données et mise à jour", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li("Zones Vent/Neige selon sources en vigueur à la date de mise à jour indiquée."),
                    html.Li("Les évolutions réglementaires peuvent modifier les résultats; vérifier la version la plus récente."),
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Avertissement important", style={'fontWeight': '600', 'margin': '8px 0 4px 0', 'color': '#374151'}),
                html.Ul([
                    html.Li(html.Span([html.Span("Catégorie I: ", style={'fontWeight': '700', 'color': '#b91c1c'}), "la carte n'est pas applicable; étude BE obligatoire avant toute décision."]))
                ], style={'margin': 0, 'paddingLeft': '18px'}),
                html.Div("Dernière mise à jour: JJ/MM/AAAA", style={'marginTop': '10px', 'color': '#6b7280', 'fontSize': '12px'})
            ])

    def build_map_df(config: str, entraxe_col: str) -> pd.DataFrame:
        sel = rules.loc[rules["Config"] == config, ["Zone_Vent", "Zone_Neige", entraxe_col]].copy()
        if sel.empty:
            df = zones.copy()
            df["AltMax_sel"] = np.nan
            df["Label"] = "Non admissible"
            return df
        m = zones.merge(sel, on=["Zone_Vent", "Zone_Neige"], how="left")
        m["AltMax_sel"] = pd.to_numeric(m[entraxe_col], errors="coerce")
        m["Label"] = m["AltMax_sel"].apply(lambda x: f"{int(x)} m" if pd.notna(x) else "Non admissible")
        return m

    def precompute_all_data():
        nonlocal precomputed_data, precomputed_stats, precomputed_colors
        
        print("Pré-calcul des données...")
        
        for config in all_configs:
            for entraxe in all_entraxes:
                key = (config, entraxe)
                
                df = build_map_df(config, entraxe)
                precomputed_data[key] = df
                
                vals = sorted(
                    df.loc[df["Label"] != "Non admissible", "AltMax_sel"].dropna().unique().tolist(),
                    reverse=True,
                )
                labels_order = [f"{int(v)} m" for v in vals]
                if (df["Label"] == "Non admissible").any():
                    labels_order += ["Non admissible"]
                
                cmap = get_color_palette_cached(tuple(labels_order))
                precomputed_colors[key] = cmap
                
                n_total = zones.shape[0]
                admissible = df[df["Label"] != "Non admissible"].copy()
                n_adm = admissible.shape[0]
                p_adm = round(100 * n_adm / n_total) if n_total else 0
                counts = admissible["Label"].value_counts()
                n_non = int((df["Label"] == "Non admissible").sum())
                p_non = round(100 * n_non / n_total) if n_total else 0
                
                precomputed_stats[key] = {
                    'labels_order': labels_order,
                    'n_total': n_total,
                    'n_adm': n_adm,
                    'p_adm': p_adm,
                    'counts': counts,
                    'n_non': n_non,
                    'p_non': p_non,
                    'no_match': df["AltMax_sel"].isna().all(),
                    'df': df
                }
        
        print(f"Pré-calcul terminé : {len(precomputed_data)} combinaisons")

    precompute_all_data()

    app = Dash(__name__)
    app.title = "Atlas Entraxes 2025"

    app.layout = html.Div([
        html.Div([
            html.H1("Atlas Entraxes", style={
                'fontSize': '2rem',
                'fontWeight': '700',
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'WebkitBackgroundClip': 'text',
                'WebkitTextFillColor': 'transparent',
                'marginBottom': '0.5rem'
            }),
            html.P("Visualisation moderne des altitudes maximales par département", style={
                'color': '#6b7280',
                'fontSize': '1rem',
                'margin': '0'
            })
        ], style={
            'textAlign': 'center',
            'marginBottom': '1rem'
        }),
        
        html.Div([
            html.Div([
                html.Label("Configuration", style={
                    'fontWeight': '600',
                    'color': '#374151',
                    'marginBottom': '0.5rem',
                    'display': 'block'
                }),
                dcc.Dropdown(
                    id="cfg",
                    options=[{"label": c, "value": c} for c in all_configs],
                    value=all_configs[0],
                    clearable=False,
                    style={
                        'borderRadius': '8px',
                        'border': '1px solid #d1d5db'
                    }
                ),
            ], style={
                'flex': '1',
                'marginRight': '2rem',
                'minWidth': '250px'
            }),
            
            html.Div([
                html.Label("Entraxe", style={
                    'fontWeight': '600',
                    'color': '#374151',
                    'marginBottom': '0.5rem',
                    'display': 'block',
                    'fontSize': '0.95rem'
                }),
                dcc.RadioItems(
                    id="entraxe",
                    options=[
                        {"label": "3.00 m", "value": "AltMax_3m"},
                        {"label": "2.50 m", "value": "AltMax_2_5m"},
                    ],
                    value="AltMax_3m",
                    inline=True,
                    style={
                        'display': 'flex',
                        'gap': '1.5rem'
                    },
                    inputStyle={
                        'marginRight': '0.5rem',
                        'accentColor': '#2563eb'
                    }
                ),
            ], style={
                'flex': '1',
                'minWidth': '250px'
            }),
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'marginBottom': '2rem',
            'gap': '1.25rem',
            'paddingTop': '1rem',
            'paddingBottom': '1rem',
            'minHeight': '160px'
        }),

        html.Div([
            html.Div([
                html.H3("Statistiques carte", style={'margin': '0 0 8px 0', 'fontSize': '16px', 'color': '#374151'}),
                html.Div(id="stats-panel")
            ], style={'width': '300px', 'minWidth': '260px', 'background': 'white', 'border': '1px solid #e2e8f0', 'borderRadius': '8px', 'padding': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}),

            html.Div([
                dcc.Graph(
                    id="map", 
                    config={
                        "displayModeBar": True,
                        "modeBarButtonsToAdd": ['drawline', 'drawopenpath', 'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'],
                        "toImageButtonOptions": {
                            "format": "svg",
                            "filename": "atlas_entraxes",
                            "height": 800,
                            "width": 1200,
                            "scale": 1
                        }
                    },
                    style={'height': '90vh', 'width': '100%', 'backgroundColor': '#ffffff'}
                ),
                html.Div(id="legend-compact", style={'marginTop': '1rem'})
            ], style={'flex': '1', 'minWidth': '480px'}),

            html.Div([
                html.H3("Détails configuration", style={'margin': '0 0 8px 0', 'fontSize': '16px', 'color': '#374151'}),
                html.Div(id="details-panel", style={'marginBottom': '12px'}),
                html.Details([
                    html.Summary("Règles d'usage", style={'cursor': 'pointer', 'fontWeight': '600', 'color': '#1f2937'}),
                    html.Div(id="usage-panel", style={'marginTop': '8px'})
                ], open=False),
                html.Details([
                    html.Summary("Conditions d'utilisation (détaillées)", style={'cursor': 'pointer', 'fontWeight': '600', 'color': '#1f2937'}),
                    html.Div(id="conditions-panel", style={'marginTop': '8px'})
                ], open=False)
            ], style={'width': '320px', 'minWidth': '260px', 'background': 'white', 'border': '1px solid #e2e8f0', 'borderRadius': '8px', 'padding': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'})
        ], style={'display': 'flex', 'gap': '12px'}),

    ], style={
        'padding': '1rem',
        'fontFamily': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        'minHeight': '100vh'
    })

    @app.callback(
        Output("map", "figure"),
        Input("cfg", "value"),
        Input("entraxe", "value"),
    )
    def update_map(config, entraxe_col):
        key = (config, entraxe_col)
        stats = precomputed_stats[key]
        df = stats['df']
        labels_order = stats['labels_order']
        cmap = precomputed_colors[key]
        
        df_hash = hash(tuple(df['Label'].values))
        fig = create_base_choropleth_cached(config, entraxe_col, tuple(labels_order), df_hash)
        
        if not cent_df.empty:
            labels_df = df.merge(cent_df, on="Dept", how="left")
            fig.add_trace(
                go.Scattergeo(
                    lat=labels_df["lat"],
                    lon=labels_df["lon"],
                    text=labels_df["Dept"],
                    mode="text",
                    textfont=dict(size=10, color="#1f2937", family="Inter"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        if not cent_df.empty:
            df_clean = df.copy()
            df_clean["Nom"] = df_clean["Nom"].fillna("Nom manquant")
            df_clean["Label"] = df_clean["Label"].fillna("Non disponible")
            
            hover_df = df_clean.merge(cent_df, on="Dept", how="left")
            hover_points = []
            for _, row in hover_df.iterrows():
                for lat_offset in [-0.2, 0, 0.2]:
                    for lon_offset in [-0.2, 0, 0.2]:
                        hover_points.append({
                            'lat': row['lat'] + lat_offset,
                            'lon': row['lon'] + lon_offset,
                            'Nom': row['Nom'],
                            'Dept': row['Dept'],
                            'Label': row['Label']
                        })
            
            hover_df_expanded = pd.DataFrame(hover_points)
            fig.add_trace(
                go.Scattergeo(
                    lat=hover_df_expanded["lat"],
                    lon=hover_df_expanded["lon"],
                    mode="markers",
                    marker=dict(size=20, color="rgba(0,0,0,0)"),
                    hovertemplate="<b>%{customdata[0]} (%{customdata[1]})</b><br>Altitude max: %{customdata[2]}<extra></extra>",
                    customdata=np.stack([hover_df_expanded["Nom"], hover_df_expanded["Dept"], hover_df_expanded["Label"]], axis=-1),
                    showlegend=False,
                    hoverlabel=dict(
                        bgcolor="#374151",
                        font=dict(size=14, family="Tahoma", color="white")
                    )
                )
            )

        if stats['no_match']:
            fig.add_annotation(
                text="Aucune règle ne correspond à cette configuration.",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16, color="#9a3412"),
                bgcolor="rgba(255,247,237,0.95)",
                bordercolor="#fdba74",
                borderwidth=1,
                borderpad=8
            )

        return fig

    @app.callback(
        Output("legend-compact", "children"),
        Input("cfg", "value"),
        Input("entraxe", "value"),
    )
    def update_legend(config, entraxe_col):
        key = (config, entraxe_col)
        stats = precomputed_stats[key]
        cmap = precomputed_colors[key]
        labels_order = stats['labels_order']
        
        legend_items = []
        for label in labels_order:
            legend_items.append(
                html.Div([
                    html.Div(style={
                        'width': '20px',
                        'height': '20px',
                        'backgroundColor': cmap[label],
                        'borderRadius': '4px',
                        'display': 'inline-block',
                        'marginRight': '8px',
                        'verticalAlign': 'middle',
                        'border': '1px solid #e2e8f0',
                        'flexShrink': '0'
                    }),
                    html.Span(label, style={
                        'fontSize': '14px',
                        'fontWeight': '500',
                        'color': '#374151',
                        'verticalAlign': 'middle',
                        'whiteSpace': 'nowrap'
                    })
                ], style={
                    'display': 'inline-flex',
                    'alignItems': 'center',
                    'marginRight': '20px',
                    'marginBottom': '8px'
                })
            )

        notif = None
        if stats['no_match']:
            notif = html.Div(
                "Aucune règle ne correspond à cette configuration.",
                style={
                    'background': '#fff7ed',
                    'color': '#9a3412',
                    'border': '#fdba74 1px solid',
                    'borderRadius': '6px',
                    'padding': '10px',
                    'marginBottom': '10px',
                    'textAlign': 'center',
                    'fontWeight': '600'
                }
            )

        legend_children = [
            html.Div(f"Configuration: {config} | Entraxe: {entraxe_col.replace('AltMax_', '').replace('m', ' m')}", style={
                'fontSize': '14px',
                'color': '#6b7280',
                'marginBottom': '10px',
                'fontWeight': '500',
                'textAlign': 'center'
            })
        ]
        if notif is not None:
            legend_children.append(notif)
        legend_children.append(
            html.Div(legend_items, style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        )
        
        return html.Div(legend_children, style={
            'background': 'white',
            'padding': '15px',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'border': '1px solid #e2e8f0',
            'marginTop': '15px',
            'position': 'relative',
            'zIndex': '10',
            'width': '100%',
            'boxSizing': 'border-box'
        })

    @app.callback(
        Output("stats-panel", "children"),
        Input("cfg", "value"),
        Input("entraxe", "value"),
    )
    def update_stats(config, entraxe_col):
        key = (config, entraxe_col)
        stats = precomputed_stats[key]
        cmap = precomputed_colors[key]
        labels_order = stats['labels_order']
        
        lines = []
        for lab in labels_order:
            if lab == "Non admissible":
                continue
            n = int(stats['counts'].get(lab, 0))
            p = round(100 * n / stats['n_adm']) if stats['n_adm'] else 0
            lines.append(
                html.Div([
                    html.Div(style={'width': '10px', 'height': '10px', 'backgroundColor': cmap[lab], 'borderRadius': '2px', 'border': '1px solid #e5e7eb', 'marginRight': '8px'}),
                    html.Div(lab, style={'flex': '1', 'color': '#374151'}),
                    html.Div(f"{n} dép ({p}%)", style={'color': '#6b7280'})
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px', 'padding': '6px 0', 'borderBottom': '1px solid #f1f5f9'})
            )

        bar_inner = html.Div(style={'width': f"{stats['p_adm']}%", 'height': '8px', 'background': '#2563eb', 'borderRadius': '999px'})
        bar = html.Div([bar_inner], style={'height': '8px', 'background': '#f1f5f9', 'borderRadius': '999px'})

        return html.Div([
            html.Div([
                html.Span("Couverture", style={'fontWeight': '600', 'color': '#374151'}),
                html.Span(f"  {stats['n_adm']} / {stats['n_total']} dép ({stats['p_adm']}%)", style={'float': 'right', 'color': '#1f2937'})
            ], style={'marginBottom': '6px'}),
            bar,
            html.Div(lines, style={'marginTop': '10px'}),
            html.Div(f"Non admissibles: {stats['n_non']} dép ({stats['p_non']}% sur France)", style={'marginTop': '8px', 'color': '#6b7280'})
        ])

    @app.callback(
        Output("details-panel", "children"),
        Input("cfg", "value"),
    )
    def update_details(config):
        detail_values = get_detail_values_cached(config)
        
        def row(label, value):
            return html.Div([
                html.Span(label, style={'color': '#6b7280'}),
                html.Span(value, style={'fontWeight': '600', 'color': '#1f2937'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'padding': '6px 0', 'borderBottom': '1px solid #f1f5f9'})

        return html.Div([
            row("Référence du modèle", config or "—"),
            row("Type de serre", detail_values["Type_Serre"]),
            row("Hauteur de poteau", detail_values["Hauteur_Poteau"]),
            row("Largeur", detail_values["Largeur"]),
            row("Toiture", detail_values["Toiture"]),
            row("Façade", detail_values["Facade"]),
            row("Traverse", detail_values["Traverse"]),
        ])

    @app.callback(
        Output("usage-panel", "children"),
        Input("cfg", "value"),
    )
    def update_usage(config):
        return get_usage_panel_cached()

    @app.callback(
        Output("conditions-panel", "children"),
        Input("cfg", "value"),
    )
    def update_conditions(config):
        return get_conditions_panel_cached()

    return app

def main():
    args = parse_arguments()
    
    setup_logging(quiet=args.quiet)
    
    app = initialize_app(use_cache=not args.no_cache)
    
    print(f"Application chargée avec succès")
    print(f"Ouverture sur http://{args.host}:{args.port}/")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == "__main__":
    main()