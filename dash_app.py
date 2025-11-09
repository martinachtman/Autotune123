import os
import json
import dash
from dash import html
from dash import dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import dcc
from datetime import datetime

# Modern Python-based autotune implementation (now the main implementation)
from autotune import Autotune
print("✅ Using modern Python-based autotune implementation")

from layout.step2 import step2
from layout.step3_graph import step3_graph
from data_processing.table_calculations import sum_column
from layout.styles import table_style, cell_style, header_style
from dateutil.parser import parse
from datetime import timedelta, datetime
from data_processing.data_preperation import data_preperation
from datetime import datetime as dt
from definitions import development, github_link
# from counter import counter1  # Removed unused counter module
from flask import jsonify
from flask_restful import Api, Resource, reqparse
from api.api import autotune_api
# from profile_manager import ProfileManager  # Removed unused module
# VARIABLES
autotune = Autotune()
# profile_manager = ProfileManager()  # Removed unused module
df = pd.DataFrame()


def get_system_timezone():
    """
    Get timezone from system, preferring /etc/localtime over environment variables.
    /etc/localtime contains all necessary timezone information including rules.
    This is more reliable in Docker containers and system deployments.
    """
    try:
        import os
        
        # Primary method: Read timezone from /etc/localtime symlink (most reliable)
        if os.path.islink('/etc/localtime'):
            # /etc/localtime is usually a symlink like /usr/share/zoneinfo/Europe/Amsterdam
            link_target = os.readlink('/etc/localtime')
            if '/zoneinfo/' in link_target:
                timezone = link_target.split('/zoneinfo/')[-1]
                print(f"Detected timezone from /etc/localtime symlink: {timezone}")
                return timezone
        
        # Check if /etc/localtime exists as regular file (contains timezone data)
        elif os.path.exists('/etc/localtime'):
            print("Found /etc/localtime file (timezone data available, but name detection limited)")
            # /etc/localtime exists but timezone name detection requires parsing binary data
            # Fall through to environment variable or UTC
        
        # Fallback to /etc/timezone file (less common, mainly Debian/Ubuntu)
        try:
            with open('/etc/timezone', 'r') as f:
                timezone = f.read().strip()
                if timezone:
                    print(f"Detected timezone from /etc/timezone: {timezone}")
                    return timezone
        except (FileNotFoundError, IOError):
            pass
        
        # Final fallback to environment variable or UTC
        timezone = os.environ.get('TIMEZONE', 'UTC')
        print(f"Using timezone from environment/default: {timezone}")
        return timezone
        
    except Exception as e:
        print(f"Error detecting timezone, falling back to UTC: {e}")
        return 'UTC'


def init_dashboard(server):
    # START APP
    app = dash.Dash(__name__,
                    title="Autotune123",
                    suppress_callback_exceptions=True,
                    external_stylesheets=[dbc.themes.FLATLY]
                    )

    # API
    @app.server.route("/api/", methods=['GET',"POST"])
    def get():
        json_object = autotune_api()
        return json_object


    # LAYOUT
    def serve_layout():
        return html.Div([
        dbc.NavbarSimple(
            children=[
                dbc.DropdownMenu(
                    children=[
                        dbc.DropdownMenuItem("Autotune123", id="about", href="#"),
                        dbc.DropdownMenuItem("Savitzky-Golay filter", id="info-savgol_filter", href="#"),
                        dbc.DropdownMenuItem("Autotune applications", id="autos", href="#"),
                    ],
                    nav=True,
                    in_navbar=True,
                    label="About",
                ),
                dbc.NavItem(dbc.NavLink("Report an issue", href="https://github.com/KelvinKramp/Autotune123/issues", target="_blank")),
                dbc.NavItem(dbc.NavLink("GitHub", href="https://github.com/KelvinKramp/Autotune123", target="_blank")),
            ],
            brand="Autotune123",
            brand_href="/",
            color="primary",
            dark=True,
            sticky="top",
        ),

        # Hidden storage for original autotune recommendations
        dcc.Store(id='original-recommendations-store', data=None),
        
        dbc.Row(children=[html.Div(" .", id="step-0")]),
        html.H3("", id='title', style={'textAlign': 'center', }),
        html.H4("", id='subtitle', style={'textAlign': 'center'}),
        html.Br(),
        dcc.Loading(
            id="loading-1",
            fullscreen=True,
            type="circle",
            color="#2c3e50",
            style={'backgroundColor': 'transparent',
                   # 'height': '50%',
                   # 'width': '50%',
                   'text-align': 'center',
                   'margin': 'auto',
                   'justify-content':'center'
                   },
            children=
        dbc.Row([
            html.Div(children=[
                # STEP 1
                ################################################################################################################
                html.Div(id="step-1", hidden=False, children=[
                    dbc.Row([
                        dcc.Input(
                            id="input-url", type="url", placeholder="NightScout URL", required=True,
                            value=os.environ.get('NS_SITE', ''),  # Pre-fill from config.env
                            style={'marginBottom': '1.5em', 'text-align': 'center'},
                        ),
                        html.Br(),
                        html.Br(),
                        dcc.Input(
                            id="token", type="password", placeholder="API secret", required=False,
                            value="••••••••••••••••" if os.environ.get('API_SECRET') else '',  # Show masked if configured
                            style={'text-align': 'center'},
                        ),
                    ], style={'text-align': 'center', 'margin': 'auto', 'width': '40%'},
                        className='justify-content-center'),
                    html.Div("(Only required if the NightScout url is locked)", style={'text-align': 'center'}
                             ),
                    html.Br(),
                    html.Div(
                        [
                            dbc.Label("Insulin type"),
                            dbc.RadioItems(
                                options=[
                                    {"label": "Rapid Acting (Humalog/Novolog/Novorapid) 1", "value": "rapid-acting"},
                                    {"label": "Ultra Rapid (Fiasp)", "value": "ultra-rapid"},
                                ],
                                value="rapid-acting",
                                id="radioitems-insulin",
                            ),
                        ],
                        style={'text-align': 'center', 'margin': 'auto', 'width': '40%'}, className='justify-content-center'),
                    
                    # Autotune Mode Selection
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Autotune Mode"),
                            dbc.Checklist(
                                options=[
                                    {"label": " Enable Aggressive Mode (More sensitive adjustments)", "value": "aggressive"}
                                ],
                                value=[],
                                id="aggressive-mode-checkbox",
                                inline=True,
                                style={'margin': '10px 0'}
                            ),
                            dbc.Collapse(
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Autotune Mode Comparison", className="card-title"),
                                        html.P([
                                            html.Strong("Standard Mode (Original oref0-autotune):"), html.Br(),
                                            "• Requires ±20 mg/dL deviation threshold", html.Br(),
                                            "• Needs minimum 3 data points per time period", html.Br(),
                                            "• Conservative adjustments, follows original OpenAPS logic"
                                        ]),
                                        html.P([
                                            html.Strong("Aggressive Mode (Modified):"), html.Br(),
                                            "• Requires ±10 mg/dL deviation threshold", html.Br(),
                                            "• Needs minimum 2 data points per time period", html.Br(),
                                            "• More sensitive to smaller BG variations"
                                        ]),
                                        html.P([
                                            "📖 Learn more about autotune: ",
                                            html.A("OpenAPS Autotune Documentation", 
                                                  href="https://openaps.readthedocs.io/en/latest/docs/Customize-Iterate/autotune.html",
                                                  target="_blank")
                                        ])
                                    ])
                                ], color="info", outline=True),
                                id="mode-info-collapse",
                                is_open=False,
                            ),
                            dbc.Button("ℹ️ Show Mode Details", id="mode-info-button", size="sm", color="info", outline=True, style={'margin-top': '5px'})
                        ], width=8),
                    ], justify='center'),
                    html.Br(),
                    
                    # Profile Selection Section
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Profile to Modify:", style={'font-weight': 'bold', 'margin-bottom': '10px'}),
                            dcc.Dropdown(
                                id="profile-selection-dropdown",
                                placeholder="Choose a profile or load current profile...",
                                style={'text-align': 'left', 'margin-bottom': '15px'},
                                value=None
                            ),
                        ], width=8),
                    ], justify='center'),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button('Load Current Profile', id='load-profile', n_clicks=0, color="primary"),
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button('Load Selected Profile', id='load-selected-profile', n_clicks=0, color="success", disabled=True),
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button('Browse All Profiles', id='browse-profiles', n_clicks=0, color="secondary"),
                        ], width="auto"),
                    ], style={'text-align': 'center'}, justify='center'),
                    html.Br(),
                ]),
                
                # NEW PROFILE BROWSER SECTION
                html.Div(id="profile-browser", hidden=True, children=[
                    html.H4("Profile Browser & Comparison", style={'textAlign': 'center'}),
                    html.Hr(),
                    
                    # Profile list table
                    html.H5("Available Profiles"),
                    html.Div(id="profile-list-container", children=[
                        dash_table.DataTable(
                            id='profile-list-table',
                            columns=[],
                            data=[],
                            style_table=table_style,
                            style_cell=cell_style,
                            style_header=header_style,
                            row_selectable='multi',
                            selected_rows=[],
                        )
                    ]),
                    html.Br(),
                    
                    # Profile comparison section
                    dbc.Row([
                        dbc.Col([
                            dbc.Button('Compare Selected', id='compare-profiles', n_clicks=0, 
                                     color="info", disabled=True),
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button('Back to Step 1', id='back-to-step1', n_clicks=0, 
                                     color="secondary"),
                        ], width="auto"),
                    ], justify='center'),
                    html.Br(),
                    
                    # Comparison results
                    html.Div(id="comparison-results", children=[]),
                    html.Br(),
                ]),
                
                # NEW GENERATED PROFILE SECTION
                html.Div(id="generated-profile-section", hidden=True, children=[
                    html.H4("Generated Autotune Profile", style={'textAlign': 'center'}),
                    html.Hr(),
                    
                    # Profile JSON Display
                    html.H5("Profile JSON (Nightscout Compatible)"),
                    html.Div([
                        dcc.Textarea(
                            id='profile-json-display',
                            value='',
                            style={'width': '100%', 'height': '300px', 'fontFamily': 'monospace'},
                            readOnly=True
                        ),
                    ]),
                    html.Br(),
                    
                    # Download and Upload Section
                    dbc.Row([
                        dbc.Col([
                            dbc.Button('Download JSON', id='download-profile-json', n_clicks=0, 
                                     color="success"),
                            dcc.Download(id="download-profile"),
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button('Show Upload Instructions', id='show-upload-instructions', n_clicks=0, 
                                     color="info"),
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button('Back to Results', id='back-to-results', n_clicks=0, 
                                     color="secondary"),
                        ], width="auto"),
                    ], justify='center'),
                    html.Br(),
                    
                    # Upload Instructions Modal
                    dbc.Modal([
                        dbc.ModalHeader(dbc.ModalTitle("Nightscout Profile Upload Instructions")),
                        dbc.ModalBody(id="upload-instructions-body"),
                        dbc.ModalFooter(
                            dbc.Button("Close", id="close-upload-instructions", className="ms-auto", n_clicks=0)
                        ),
                    ], id="upload-instructions-modal", is_open=False, size="lg"),
                    
                    html.Br(),
                ]),
                ################################################################################################################

                # STEP 2
                ################################################################################################################
                html.Div(id="step-2", hidden=False, children=[
                    step2()]),
                ################################################################################################################

                # STEP 3
                ################################################################################################################
                dbc.Row(children=[
                    html.Div(id="step-3", hidden=False, children=[
                    dbc.Row([
                        html.H5("3A: Apply filter to smooth calculated recommendations (optional)"),
                        dbc.Row(children=[html.Div(children=step3_graph),]),
                        html.Br(),
                        html.Hr(),
                        html.H5("3B: Review and adjust recommendations (optional)"),
                        html.H6(
                            "Scroll through the table to review all values. The Autotune column is automatically adjusted based on the filter selected in 3A. "
                            "Always check whether the recommendations make sense based on your personal experience. "
                            "If a correction is needed, double click on the table cells to adjust an Autotune recommendation value and press enter."),
                        dbc.Row(children=[html.Div(children=[
                            dash_table.DataTable(
                                id='title-table-recommendations',
                                columns=[{"name": i, "id": i} for i in ["Time", "Current", "Autotune", "Days Missing"]],
                                data=[],
                                style_table=table_style,
                                # style cell
                                style_cell=cell_style,
                                # style header
                                style_header=header_style,
                                editable=False,
                            ),

                            dash_table.DataTable(
                                id='table-recommendations',
                                columns=[],
                                data=[],
                                style_table=table_style,
                                # style cell
                                style_cell=cell_style,
                                # style header
                                style_header={'display': 'none'},
                                editable=True,
                            ),
                            html.Div(id="total_amounts_2"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Button("Download log file", id="btn_text"),
                                            dcc.Download(id="download-dataframe-text"),
                                        ],
                                        width={"size": "auto", "offset": 0},
                                    ),
                                    dbc.Col(
                                        [
                                        dbc.Button("Download CSV", id="btn_csv"),
                                        dcc.Download(id="download-dataframe-csv"),
                                        ],
                                        width={"size": "auto", "offset": 0},
                                    ),
                                    dbc.Col(
                                        [
                                        dbc.Button("Download Excel", id="btn_xlsx"),
                                        dcc.Download(id="download-dataframe-xlsx"),
                                        ],
                                        width={"size": "auto", "offset": 0},
                                    ),
                                    dbc.Col(
                                        [
                                        dbc.Button("Show Profile JSON", id="show-generated-profile", color="info"),
                                        ],
                                        width={"size": "auto", "offset": 0},
                                    ),
                                ],style={'justify-content': 'right', "text-align": "right"}
                            ),
                            dbc.Row([
                                html.Div([
                                    dbc.Alert(
                                        id="alert-auto-autotune",
                                        is_open=False,
                                        duration=2000,
                                        color="success",
                                        style={'textAlign': 'center', }
                                    ),
                                ],
                                    style={"width": "50%", 'justify-content': 'center'}
                                ), ],
                                justify='center'),
                        ]
                        ), ]),
                    ]),
                    html.Br(),
                    html.Hr(),
                    dbc.Row([
                        html.H5("3C: Upload to NightScout:", style={'color': '#ff8c00'}),  # Orange color
                        html.Div(children=[
                            "Enter your API secret, choose profile name, and click the activate button. The API secret is not saved on the server. "
                            "They might be saved in your browser autocomplete or password manager if you have one. If you don't want to use this website for activating recommendations, you can "
                            "download the code from ",github_link," and run it locally on your computer."
                            ]
                            ),
                        html.Div(id="api-permission-warning", children=[
                            dbc.Alert([
                                html.Strong("⚠️ API Secret Requirements:"), html.Br(),
                                "• Your API secret must have READ/WRITE permissions", html.Br(),
                                "• Read-only API secrets will fail with 401 Unauthorized error", html.Br(),
                                "• For updating existing profiles, enter your API secret again (don't reuse cached values)"
                            ], color="warning", style={'margin-top': '10px'})
                        ]),
                    ]),
                    html.Br(),
                    
                    # Profile Name Selection Section
                    dbc.Row([
                        dbc.Col([
                            html.Label("Profile Name:", style={'font-weight': 'bold'}),
                            dcc.RadioItems(
                                id="profile-name-option",
                                options=[
                                    {'label': 'Create New Profile', 'value': 'new'},
                                    {'label': 'Update Existing Profile', 'value': 'existing'}
                                ],
                                value='new',
                                inline=True,
                                style={'margin': '10px 0'}
                            ),
                        ], width=12),
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            # New Profile Name Input (shown when 'new' selected)
                            html.Div(id="new-profile-input", children=[
                                dcc.Input(
                                    id="new-profile-name",
                                    type="text",
                                    placeholder="Enter new profile name (e.g., 'Autotune-2025-11-07')",
                                    style={'width': '100%', 'text-align': 'center'},
                                    value=f"Autotune-{datetime.now().strftime('%Y-%m-%d')}"
                                ),
                            ]),
                            
                            # Existing Profile Dropdown (shown when 'existing' selected)
                            html.Div(id="existing-profile-dropdown", children=[
                                dcc.Dropdown(
                                    id="existing-profile-select",
                                    placeholder="Select existing profile to update...",
                                    style={'text-align': 'center'}
                                ),
                            ], style={'display': 'none'}),
                        ], width=8, style={'margin': '0 auto'}),
                    ]),
                    html.Br(),
                    
                    dbc.Row([
                        dcc.Input(
                            id="input-API-secret", type="password", placeholder="Nightscout API secret (READ/WRITE permissions required)", required=True,
                            value="••••••••••••••••" if os.environ.get('API_SECRET') else '',  # Show masked if configured
                            style={'text-align': 'center'},
                        ),
                    ], style={'text-align': 'center', 'margin': 'auto', 'width': '50%'},
                        className='justify-content-center'),
                    
                    dbc.Row([
                        html.Small(
                            "Note: When updating existing profiles, please re-enter your API secret to ensure proper permissions.",
                            style={'color': '#666', 'text-align': 'center', 'margin-top': '5px'}
                        )
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Button('Activate Profile', id='activate-profile', n_clicks=0, disabled=False, color="warning"),
                    ], style={'text-align': 'center', 'margin': 'auto', 'width': '30%'},
                        className='justify-content-center'),
                ]),]),
                ################################################################################################################
                html.Br(),
                dbc.Alert(id="result-alert",
                          color="success",
                          dismissable=True,
                          fade=False,
                          is_open=False,
                          ),
            ],
                style={"width": "70%", 'justify-content': 'center'}
            ), ],
            justify='center'),),
        dbc.Modal(
            [
                dbc.ModalBody(
                    dcc.Markdown("""
                #### What is Autotune?
                Autotune is a tool to help calculate potential adjustments to ISF, carb ratio, and basal rates.
                \n\n
                "Autotune is a work in progress tool. Do not blindly make changes to your pump settings without careful 
                consideration. You may want to print the output of this tool and discuss any particular changes with your 
                care team. Make note that you probably do not want to make long-term changes based on short term (i.e. 24 hour) data. 
                Most people will choose to make long term changes after reviewing carefully autotune output of 3-4 weeks 
                worth of data." \n
                [Open APS - Understanding Autotune page](https://openaps.readthedocs.io/en/latest/docs/Customize-Iterate/understanding-autotune.html)

                #### What is Autotune123?
                Autotune123 is a web application for type 1 diabetics to configure their insuline pump basal rate
                in three steps. It relies on the open source OpenAPS Autotune algorithm, the Savitzky-Golay filter, and uses
                 data from a personal NightScout websites as input to propose a 24-hour basal curve.\n\n

                Autotune123 only works if:
                - You have a NightScout account properly setup.
                - You have logged your carbs accurately in amount and time.
                - You digitally disconnect your pump when your pump is physically disconnected (e.g. during showering or blockage of infusion set).
                
                The profile activation in step 3 only works if (in preferences->NS settings -> synchronisation): 
                - "Upload data to nightscout" is turned on.
                - "Receive profile store" is turned on.
                - "Receive profile switches" is turned on.
                """)),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
            size="xl",  # "sm", "lg", "xl" = small, large or extra large
            backdrop=True,  # Modal to not be closed by clicking on backdrop
            scrollable=True,  # Scrollable in case of large amount of text
            centered=True,  # Vertically center modal
            keyboard=True,  # Close modal when escape is pressed
            fade=True,  # True, False
            # style={"max-width": "none", "width": "50%",}
        ),
        dbc.Modal(
            [
                dbc.ModalBody([
                    dcc.Markdown("""
#### Overview of different open source applications to tune basal profiles
| |[Autotune](https://openaps.readthedocs.io/en/latest/docs/Customize-Iterate/autotune.html)  | [Autotuneweb](https://autotuneweb.azurewebsites.net/) |[NightScoutsuggestions](https://nightscoutsuggestions.com/) | [Autotune123](http://autotune123.com/)|
|---|--- | --- |--- | --- |
|Year of creation|2016|2018|2021|2022|
|Computer terminal|+|-|-|-|
|Visualisation of recommendations|-|-|+|+|
|Download log files |+|+|-|+|
|Download recommendations|+|+|-|+|
|E-mail recommendations|-|+|-|-|
|See old results|+|+|-|-|
|Use different time zones|+|-|+|-|
|Get profiles in json file|+|+|-|-|
|Adjust min. 5 minutes carb impact|+|+|-|-|
|Direct activation of recommendations on pump|-|-|-|+|
|Change individual basal values in real-time|-|-|-|+|
|Apply smoothing filters|-|-|-|+|
|Switch between fast-acting and fiasp|?|+|-|+|
|UAM option|+|+|-|+|
|Clean calculations based on fasting periods|-|-|+|-|
*UAM = a function that allows the moments in which a glucose increase that is not registered as a meal input by the user to be defined by the loop as a unregistered meal, consequently letting the loop administer small boluses of insulin.

            """)],style={"margin":"auto","padding":"2px","justify-content":"space-between",}),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-autos", className="ml-auto")
                ),
            ],
            id="modal-autos",
            size="xl",  # "sm", "lg", "xl" = small, large or extra large
            backdrop=True,  # Modal to not be closed by clicking on backdrop
            scrollable=True,  # Scrollable in case of large amount of text
            centered=True,  # Vertically center modal
            keyboard=True,  # Close modal when escape is pressed
            fade=True,  # True, False
            # style={"max-width": "none", "width": "50%",}
        ),
        html.Div(id="empty-div-autotune"),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        )
    ])

    app.layout = serve_layout

    # PROFILE BROWSER CALLBACKS
    @app.callback(
        Output('profile-browser', 'hidden'),
        Output('profile-list-table', 'columns'),
        Output('profile-list-table', 'data'),
        Output('compare-profiles', 'disabled'),
        [Input('browse-profiles', 'n_clicks'),
         Input('back-to-step1', 'n_clicks'),
         Input('profile-list-table', 'selected_rows')],
        State('input-url', 'value'),
        State('token', 'value'),
    )
    def manage_profile_browser(browse_clicks, back_clicks, selected_rows, ns_url, token):
        ctx = dash.callback_context
        interaction_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Use environment variable if form shows masked placeholder
        if token == "••••••••••••••••":
            token = os.environ.get('API_SECRET', '')
        
        if interaction_id == 'browse-profiles' and browse_clicks and ns_url:
            # Download profiles from Nightscout using enhanced function
            try:
                from get_profile import get_all_profiles
                
                # Format token for API call
                token_param = f"token={token}" if token and not token.startswith("token=") else token
                
                all_profiles = get_all_profiles(ns_url, token_param)
                
                if all_profiles:
                    # Create a more user-friendly table with profile information
                    profile_data = []
                    for profile in all_profiles:
                        # Get some basic info from the profile data
                        basal_count = len(profile['data'].get('basal', []))
                        carb_ratio = 'Multiple' if len(profile['data'].get('carbratio', [])) > 1 else str(profile['data'].get('carbratio', [{}])[0].get('value', 'N/A'))
                        isf_sensitivity = 'Multiple' if len(profile['data'].get('sens', [])) > 1 else str(profile['data'].get('sens', [{}])[0].get('value', 'N/A'))
                        
                        profile_data.append({
                            'Profile Name': profile['name'],
                            'Start Date': profile['startDate'][:10] if profile['startDate'] else 'Unknown',
                            'Is Default': '✓' if profile['isDefault'] else '',
                            'Basal Segments': basal_count,
                            'Carb Ratio': carb_ratio,
                            'ISF/Sensitivity': isf_sensitivity,
                            'DIA': str(profile['data'].get('dia', 'N/A')),
                            'Units': profile['data'].get('units', 'N/A'),
                            'Timezone': profile['data'].get('timezone', 'N/A')[:20] + ('...' if len(profile['data'].get('timezone', '')) > 20 else '')
                        })
                    
                    # Sort by name and whether it's default
                    profile_data.sort(key=lambda x: (not x['Is Default'], x['Profile Name']))
                    
                    columns = [{"name": i, "id": i} for i in profile_data[0].keys()] if profile_data else []
                    
                    # Enable compare button if 2 profiles selected
                    compare_disabled = len(selected_rows or []) != 2
                    
                    return False, columns, profile_data, compare_disabled
                else:
                    return False, [], [{'Error': 'No profiles found in Nightscout'}], True
                    
            except Exception as e:
                error_data = [{'Error': f'Failed to load profiles: {str(e)}'}]
                error_columns = [{"name": "Error", "id": "Error"}]
                return False, error_columns, error_data, True
        
        elif interaction_id == 'back-to-step1':
            return True, [], [], True
        
        elif interaction_id == 'profile-list-table':
            # Update compare button state based on selection
            compare_disabled = len(selected_rows or []) != 2
            return dash.no_update, dash.no_update, dash.no_update, compare_disabled
            
        return True, [], [], True

    # @app.callback(
    #     Output('comparison-results', 'children'),
    #     [Input('compare-profiles', 'n_clicks')],
    #     State('profile-list-table', 'selected_rows'),
    #     State('profile-list-table', 'data'),
    #     State('input-url', 'value'),
    #     State('token', 'value'),
    # )
    # def compare_selected_profiles(compare_clicks, selected_rows, table_data, ns_url, token):
    #     # Profile comparison functionality disabled - requires profile_manager module
    #     return html.Div([
    #         dbc.Alert("Profile comparison feature is currently disabled.", color="info")
    #     ])
        
        # Use environment variable if form shows masked placeholder
        if token == "••••••••••••••••":
            token = os.environ.get('API_SECRET', '')
        
        try:
            # Download fresh profile data for comparison
            profiles = profile_manager.download_profiles(ns_url, token, limit=20)
            if len(profiles) > max(selected_rows):
                profile1 = profiles[selected_rows[0]]
                profile2 = profiles[selected_rows[1]]
                
                # Compare profiles
                differences = profile_manager.compare_profiles(profile1, profile2)
                
                # Create comparison display
                comparison_content = [
                    html.H5("Profile Comparison Results"),
                    html.Hr(),
                    
                    # Metadata
                    dbc.Row([
                        dbc.Col([
                            html.H6(f"Profile 1: {differences['metadata']['profile1_name']}"),
                            html.P(f"Date: {differences['metadata']['profile1_date']}")
                        ], width=6),
                        dbc.Col([
                            html.H6(f"Profile 2: {differences['metadata']['profile2_name']}"),
                            html.P(f"Date: {differences['metadata']['profile2_date']}")
                        ], width=6),
                    ]),
                    html.Hr(),
                ]
                
                # Basic settings differences
                if differences['basic_settings']:
                    basic_data = []
                    for field, diff in differences['basic_settings'].items():
                        basic_data.append({
                            'Setting': field.replace('_', ' ').title(),
                            'Profile 1': diff['profile1'],
                            'Profile 2': diff['profile2'],
                            'Difference': diff['difference'],
                            'Change %': f"{diff['percent_change']:.1f}%" if isinstance(diff['percent_change'], (int, float)) else diff['percent_change']
                        })
                    
                    comparison_content.extend([
                        html.H6("Basic Settings Differences"),
                        dash_table.DataTable(
                            columns=[{"name": i, "id": i} for i in ['Setting', 'Profile 1', 'Profile 2', 'Difference', 'Change %']],
                            data=basic_data,
                            style_table=table_style,
                            style_cell=cell_style,
                            style_header=header_style,
                        ),
                        html.Br(),
                    ])
                
                # Basal rate differences
                if differences['basal_differences']:
                    basal_df = profile_manager.basal_comparison_to_dataframe(differences)
                    if hasattr(basal_df, 'columns'):  # pandas DataFrame
                        columns = [{"name": i, "id": i} for i in basal_df.columns]
                        data = basal_df.to_dict('records')
                    else:  # list of dicts
                        if basal_df:
                            columns = [{"name": i, "id": i} for i in basal_df[0].keys()]
                            data = basal_df
                        else:
                            columns = []
                            data = []
                    
                    comparison_content.extend([
                        html.H6("Basal Rate Differences"),
                        dash_table.DataTable(
                            columns=columns,
                            data=data,
                            style_table=table_style,
                            style_cell=cell_style,
                            style_header=header_style,
                        ),
                        html.Br(),
                    ])
                
                # Summary stats
                stats = differences['summary_stats']
                comparison_content.extend([
                    html.H6("Summary Statistics"),
                    dbc.Row([
                        dbc.Col([
                            html.P(f"Total Daily Basal 1: {stats['total_daily_basal_1']:.2f}U"),
                            html.P(f"Total Daily Basal 2: {stats['total_daily_basal_2']:.2f}U"),
                        ], width=6),
                        dbc.Col([
                            html.P(f"Daily Basal Difference: {stats['total_daily_basal_difference']:.2f}U"),
                            html.P(f"Number of Changes: {stats['number_of_basal_changes']} basal, {stats['number_of_setting_changes']} settings"),
                        ], width=6),
                    ]),
                ])
                
                return html.Div(comparison_content)
                
        except Exception as e:
            return html.Div([
                dbc.Alert(f"Error comparing profiles: {str(e)}", color="danger")
            ])
        
        return html.Div()

    # AUTOTUNE CALLBACKS
    @app.callback(
        Output('table-current-non-basals', 'columns'),
        Output('table-current-non-basals', 'data'),
        Output('table-current-basals', 'columns'),
        Output('table-current-basals', 'data'),
        Output('step-1', 'hidden'),
        Output('step-2', 'hidden'),
        Output('step-3', 'hidden'),
        Output('table-recommendations', 'columns'),
        Output('table-recommendations', 'data'),
        Output('subtitle', 'children'),
        Output("graph", "children"),
        Output("total_amounts", "children"),
        Output("total_amounts_2", "children"),
        Output('original-recommendations-store', 'data'),
        Output('filter-status', 'children'),
        [Input('load-profile', 'n_clicks'),
         Input('load-selected-profile', 'n_clicks'),
         Input('run-autotune', 'n_clicks'),
         Input("radioitems-insulin", "value"),
         Input("dropdown", "value"),
         Input('table-recommendations', 'data'),
         Input('back-to-step2', 'n_clicks'),
         ],
        State("checklist", "value"),
        State('input-url', 'value'),
        State('date-picker-range', 'start_date'),
        State('date-picker-range', 'end_date'),
        State('token', 'value'),
        State('profile-selection-dropdown', 'value'),
        State('aggressive-mode-checkbox', 'value'),
        State('original-recommendations-store', 'data'),
    )
    def load_profile(load, load_selected, run_autotune, insulin_type, dropdown_value, table_data, back_step2, checklist_value, NS_HOST, start_date, end_date, token, selected_profile_name, aggressive_mode, original_recommendations):
        # counter1()  # Removed unused counter call
        # identify the trigger of the callback and define as interaction_id
        ctx = dash.callback_context

        interaction_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # check uam checkbox
        if checklist_value == 1:
            uam = True
        else:
            uam = False

        # some extra code to prevent bug in callback when dash runs on AWS ubuntu VM
        if token == None:
            token = ""
        
        # Use environment variable if form shows masked placeholder
        if token == "••••••••••••••••":
            token = os.environ.get('API_SECRET', '')

        # check if dateperiod is not > 14 days to prevent server overload
        diff = (parse(end_date) - parse(start_date))
        if diff.days > 14:
            start_date = (parse(end_date) - timedelta(days=14)).date().strftime("%Y-%m-%d")
            extra_text = "A date period > 14 days was chosen. To avoid excessive calculation time the Autotune input" \
                         " was restricted to input from ({} until {}).".format(parse(start_date).strftime("%d-%m-%Y"),
                                                                               parse(end_date).strftime("%d-%m-%Y"))
        else:
            extra_text = "Input from {} until {}.".format(parse(start_date).strftime("%d-%m-%Y"),
                                                                               parse(end_date).strftime("%d-%m-%Y"))

        # STEP 1: GET PROFILE (Current Default)
        if (interaction_id == "load-profile") or (interaction_id == "back-to-step2"):
            df_basals, df_non_basals, _ = autotune.get(NS_HOST, token, insulin_type)
            return [{"name": i, "id": i} for i in df_non_basals.columns], df_non_basals.to_dict('records'), \
                   [{"name": i, "id": i} for i in df_basals.columns], df_basals.to_dict('records'), \
                   True, False, True, [], [], "Step 2: Pick time period", html.Div(children=[]), "", "", None

        # STEP 1b: GET SELECTED PROFILE
        if interaction_id == "load-selected-profile" and selected_profile_name:
            try:
                df_basals, df_non_basals, _ = autotune.get_specific_profile(NS_HOST, token, insulin_type, selected_profile_name)
                return [{"name": i, "id": i} for i in df_non_basals.columns], df_non_basals.to_dict('records'), \
                       [{"name": i, "id": i} for i in df_basals.columns], df_basals.to_dict('records'), \
                       True, False, True, [], [], f"Step 2: Pick time period (Profile: {selected_profile_name})", html.Div(children=[]), "", "", None, ""
            except Exception as e:
                # If specific profile loading fails, fall back to current profile
                print(f"Error loading selected profile '{selected_profile_name}': {e}")
                df_basals, df_non_basals, _ = autotune.get(NS_HOST, token, insulin_type)
                return [{"name": i, "id": i} for i in df_non_basals.columns], df_non_basals.to_dict('records'), \
                       [{"name": i, "id": i} for i in df_basals.columns], df_basals.to_dict('records'), \
                       True, False, True, [], [], f"Step 2: Pick time period (Error loading {selected_profile_name}, using current)", html.Div(children=[]), "", "", None, ""

        # STEP 3a: IF CHANGE OF FILTER REFRESH GRAPH AND TABLE
        # if interactino id = button increase or decrease
        # use state of % and time to increase values
        # df_recommendations, graph, y1_sum_graph, y2_sum_graph = data_preperation(dropdown_value, dropdown_value2 = .. , time= .. , percentage = ...)

        if interaction_id == "dropdown":
            # FIXED: Use original recommendations instead of modified table_data
            if original_recommendations and len(original_recommendations) > 0:
                # Convert original recommendations to DataFrame and apply new filter
                df_original = pd.DataFrame(original_recommendations)
                df_recommendations, graph, y1_sum_graph, y2_sum_graph = data_preperation(dropdown_value, df_original)
            else:
                # No original data - return empty state with message
                df_recommendations = pd.DataFrame()
                graph = html.Div("Please run Autotune first to generate recommendations before applying filters.")
                y1_sum_graph = 0
                y2_sum_graph = 0
            
            text_under_graph = "* Total amount insulin currently {}. Total amount based on autotune with filter {}. {}".format(
                y1_sum_graph, y2_sum_graph, extra_text),
            text_under_table = text_under_graph
            
            # Ensure we have valid columns for the table
            columns = [{"name": i, "id": i} for i in df_recommendations.columns] if not df_recommendations.empty else []
            data = df_recommendations.to_dict('records') if not df_recommendations.empty else []
            
            filter_message = f"✅ Filter applied: {dropdown_value}" if dropdown_value != "No filter" else "No filter applied"
            return [], [], [], [], True, True, False, columns, data, "Step 3: Review and upload", html.Div(children=[graph]), \
                   text_under_graph, text_under_table, original_recommendations, filter_message

        # STEP 3b: IF CHANGE IN TABLE REFRESH GRAPH AND TABLE
        if interaction_id == "table-recommendations":
            df_recommendations = pd.DataFrame(table_data)
            df_recommendations, graph, y1_sum_graph, y2_sum_graph = data_preperation(dropdown_value, df=df_recommendations)
            text_under_graph = "* Total amount insulin currently {}. Total amount based on autotune with filter {}. {}".format(
                y1_sum_graph, y2_sum_graph, extra_text),
            y1_sum_table = sum_column(table_data, "Pump")
            y2_sum_table = sum_column(table_data, "Autotune")
            text_under_table = "* Total amount insulin currently {}. Total amount based on autotune with filter and changes in table {}. {}".format(
                round(y1_sum_table, 2), round(y2_sum_table, 2), extra_text),
            # convert user adjusted table into new recommendations pandas dataframe
            filter_message = f"✅ Filter applied: {dropdown_value}" if dropdown_value != "No filter" else "No filter applied"
            return [], [], [], [], True, True, False, [{"name": i, "id": i} for i in df_recommendations.columns], \
                   df_recommendations.to_dict('records'), "Step 3: Review and upload", html.Div(children=[graph]), \
                   text_under_graph, text_under_table, original_recommendations, filter_message

        # STEP 2: RUN AUTOTUNE
        if run_autotune and start_date and end_date and NS_HOST and autotune.url_validator(NS_HOST):
            # correct_time to prevent inncongruency between datepicker output and autotune input

            start_date = parse(start_date) + timedelta(1)
            start_date = start_date.date().strftime("%Y-%m-%d")
            end_date = parse(end_date) + timedelta(1)
            end_date = end_date.date().strftime("%Y-%m-%d")
            # run autotune (modern implementation)
            aggressive_mode_enabled = 'aggressive' in (aggressive_mode or [])

            df_recommendations = autotune.run_modern(NS_HOST, start_date, end_date, uam, token=token, aggressive_mode=aggressive_mode_enabled)
            
            # Handle modern implementation results
            if df_recommendations is not None and not df_recommendations.empty:
                # FIXED: Store original recommendations before any processing
                original_recommendations_data = df_recommendations.to_dict('records')
                # Use modern data directly
                df_recommendations, graph, y1_sum_graph, y2_sum_graph = data_preperation(dropdown_value, df_recommendations)
            else:
                # Fallback for empty results
                graph = html.Div("No recommendations generated")
                y1_sum_graph = 0
                y2_sum_graph = 0
                df_recommendations = pd.DataFrame()
                original_recommendations_data = []
            text_under_graph = "* Total amount insulin currently {}. Total amount based on autotune with filter {}. {}".format(
                y1_sum_graph, y2_sum_graph, extra_text),
            text_under_table = text_under_graph
            filter_message = f"✅ Filter applied: {dropdown_value}" if dropdown_value != "No filter" else "No filter applied"
            return [], [], [], [], True, True, False, [{"name": i, "id": i} for i in df_recommendations.columns], \
                   df_recommendations.to_dict('records'), "Step 3: Review and upload", html.Div(children=[graph]), \
                   text_under_graph, text_under_table, original_recommendations_data, filter_message
        else:
            df = pd.DataFrame()

        return [], [], [], [], False, True, True, [{"name": i, "id": i} for i in df.columns], df.to_dict('records'), \
                   "Step 1: Get your current profile", html.Div(children=[]), "", "", None, ""



    # STEP 3C
    # UPLOAD PROFILE
    @app.callback(
        Output('result-alert', 'children'),
        Output('result-alert', 'is_open'),
        Output('activate-profile', 'disabled'),
        [Input('activate-profile', 'n_clicks')],
        State('input-url', 'value'),
        State('input-API-secret', 'value'),
        State('table-recommendations', 'data'),
        State('result-alert', 'is_open'),
    )
    def activate_profile(click, NS_HOST, token, json_data, is_open):

        
        # Use environment variable if form shows masked placeholder
        if token == "••••••••••••••••":
            token = os.environ.get('API_SECRET', '')
        
        if click and NS_HOST and json_data:
            try:
                # Ensure token is properly formatted for API calls
                if token and not token.startswith(('token=', 'api-secret=')):
                    # Format as token parameter - this is what Nightscout expects
                    formatted_token = f"token={token}"
                else:
                    formatted_token = token
                
                # Get current profile with proper error handling
                _, _, profile = autotune.get(NS_HOST, formatted_token)
                new_profile = autotune.create_adjusted_profile(json_data, profile)
                
                # Upload the new profile
                if not development:
                    result = autotune.upload(NS_HOST, new_profile, formatted_token)
                else:
                    result = autotune.upload(NS_HOST, new_profile, formatted_token)
                    
                if result:
                    return "New profile activated. Check your phone in a couple of 5-30 minutes to see if the activation was successful. " \
                           'The new profile should be visible under the name "OpenAPS Autosync".', \
                           not is_open, False
                else:
                    # Upload failed but no exception was thrown
                    return dbc.Alert([
                        html.H5("❌ Profile Upload Failed", className="alert-heading"),
                        html.P("The upload process completed but was not successful."),
                        html.P("Common issues and solutions:"),
                        html.Ul([
                            html.Li("🔑 API Secret: Ensure your API secret has READ/WRITE permissions (not read-only)"),
                            html.Li("🔄 Re-enter API Secret: Type your API secret again instead of using cached values"),
                            html.Li("🌐 Check URL: Verify your Nightscout URL is correct and accessible"),
                            html.Li("📱 Check Status: Wait 5-30 minutes and check your pump/phone for the new profile"),
                        ]),
                    ], color="danger"), not is_open, True
                    
            except ValueError as e:
                # Handle API authentication errors specifically
                error_message = str(e)
                if "401" in error_message or "Unauthorized" in error_message:
                    return dbc.Alert([
                        html.H5("🔐 Authentication Error", className="alert-heading"),
                        html.P("Your API secret doesn't have the required permissions."),
                        html.P("Specific error: " + error_message),
                        html.Hr(),
                        html.P("Solutions:"),
                        html.Ul([
                            html.Li("🔑 Check API Secret: Ensure it has READ/WRITE permissions (not read-only)"),
                            html.Li("🆕 Create New Secret: Generate a new API secret in Nightscout Admin Tools"),
                            html.Li("🔄 Clear Cache: Clear your browser cache and re-enter the API secret"),
                            html.Li("📋 Copy Carefully: Make sure you copied the complete API secret without extra spaces"),
                        ]),
                    ], color="warning"), not is_open, True
                else:
                    return dbc.Alert([
                        html.H5("❌ Profile Upload Error", className="alert-heading"),
                        html.P("An error occurred during profile upload:"),
                        html.P(error_message, style={'font-family': 'monospace', 'background': '#f8f9fa', 'padding': '10px', 'border-radius': '4px'}),
                    ], color="danger"), not is_open, True
                    
            except Exception as e:
                # Handle any other unexpected errors
                return dbc.Alert([
                    html.H5("❌ Unexpected Error", className="alert-heading"),
                    html.P("An unexpected error occurred:"),
                    html.P(str(e), style={'font-family': 'monospace', 'background': '#f8f9fa', 'padding': '10px', 'border-radius': '4px'}),
                    html.Hr(),
                    html.P([
                        "Please try again or ",
                        html.A("report this issue", href="https://github.com/KelvinKramp/Autotune123/issues", target="_blank"),
                        " with the error details above."
                    ])
                ], color="danger"), not is_open, True
        else:
            # No click or missing required data
            return "", is_open, False

    @app.callback(
        Output("modal", "is_open"),
        [Input("about", "n_clicks"), Input("close", "n_clicks")],
        [State("modal", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        Output("modal-autos", "is_open"),
        [Input("autos", "n_clicks"), Input("close-autos", "n_clicks")],
        [State("modal-autos", "is_open")],
    )
    def toggle_modal_autos(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open


    @app.callback(
        Output("download-dataframe-csv", "data"),
        Input("btn_csv", "n_clicks"),
        State('table-recommendations', 'data'),
        prevent_initial_call=True,
    )
    def download_csv(n_clicks, table_data):
        datetime_string = dt.now().strftime("(%d-%m-%Y-%H-%S)")
        df = pd.DataFrame(table_data)
        # Clean the dataframe - remove unnamed columns and empty rows
        df = df.dropna(how='all')  # Remove completely empty rows
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
        return dcc.send_data_frame(df.to_csv, "AutoRec"+datetime_string+".csv", index=False)

    @app.callback(
        Output("download-dataframe-xlsx", "data"),
        Input("btn_xlsx", "n_clicks"),
        State('table-recommendations', 'data'),
        prevent_initial_call=True,
    )
    def download_excel(n_clicks, table_data):
        datetime_string = dt.now().strftime("(%d-%m-%Y-%H-%S)")
        df = pd.DataFrame(table_data)
        # Clean the dataframe - remove unnamed columns and empty rows
        df = df.dropna(how='all')  # Remove completely empty rows
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
        return dcc.send_data_frame(df.to_excel, "AutoRec"+datetime_string+".xlsx", sheet_name="Recommendations")

    @app.callback(
        Output("download-dataframe-text", "data"),
        Input("btn_text", "n_clicks"),
        State('table-recommendations', 'data'),
        prevent_initial_call=True,
    )
    def download_text(n_clicks, table_data):
        datetime_string = dt.now().strftime("(%d-%m-%Y-%H-%S)")
        
        # Create text content from table data
        if table_data:
            df = pd.DataFrame(table_data)
            # Clean the dataframe - remove unnamed columns and empty rows
            df = df.dropna(how='all')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Convert to readable text format
            text_content = "Autotune Recommendations\n"
            text_content += "=" * 50 + "\n\n"
            text_content += df.to_string(index=False)
            text_content += "\n\nGenerated on: " + dt.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            text_content = "No recommendation data available"
            
        return dict(content=text_content, filename="AutoRec"+datetime_string+".txt")



    @app.callback(
        Output("info", "is_open"),
        [Input("more-info", "n_clicks"),
         Input("info-savgol_filter", "n_clicks"),
         Input("close-savgol_filter", "n_clicks"),
         ],
        [State("info", "is_open")],
    )
    def toggle_alert_no_fade(n1, n2, close, is_open):
        if n1 or n2 or close:
            return not is_open
        return is_open

    # NEW GENERATED PROFILE CALLBACKS
    @app.callback(
        [Output('generated-profile-section', 'hidden'),
         Output('profile-json-display', 'value')],
        [Input('show-generated-profile', 'n_clicks'),
         Input('back-to-results', 'n_clicks')],
        [State('table-recommendations', 'data'),
         State('input-url', 'value'),
         State('token', 'value')],
        prevent_initial_call=True,
    )
    def manage_generated_profile_display(show_clicks, back_clicks, recommendations_data, ns_url, token):
        """Handle showing and hiding the generated profile section"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return True, ""
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == 'show-generated-profile' and show_clicks:
            # Generate profile JSON from recommendations
            if recommendations_data:
                try:
                    # # Initialize ProfileManager - disabled
                    # from profile_manager import ProfileManager
                    # profile_manager = ProfileManager()
                    
                    # Convert recommendations to dictionary format
                    recommendations_dict = {}
                    basal_rates = []
                    
                    for row in recommendations_data:
                        param = row.get('Parameter', '')
                        recommended = row.get('Autotune', '')  # Fixed: use 'Autotune' column
                        current = row.get('Pump', '')
                        
                        # Skip empty rows
                        if not param or param == '':
                            continue
                        
                        # Map different parameter types
                        if 'ISF' in param and 'mg/dL' in param:
                            try:
                                recommendations_dict['isf'] = float(recommended) if recommended else None
                            except (ValueError, TypeError):
                                pass
                        elif 'CarbRatio' in param:
                            try:
                                recommendations_dict['carb_ratio'] = float(recommended) if recommended else None
                            except (ValueError, TypeError):
                                pass
                        elif param.replace(':', '') in ['0000', '0030', '0100', '0130', '0200', '0230', '0300', '0330', 
                                                        '0400', '0430', '0500', '0530', '0600', '0630', '0700', '0730',
                                                        '0800', '0830', '0900', '0930', '1000', '1030', '1100', '1130',
                                                        '1200', '1230', '1300', '1330', '1400', '1430', '1500', '1530',
                                                        '1600', '1630', '1700', '1730', '1800', '1830', '1900', '1930',
                                                        '2000', '2030', '2100', '2130', '2200', '2230', '2300', '2330']:
                            # Handle time-based basal rates
                            if recommended and recommended != '':
                                try:
                                    basal_rates.append({
                                        'time': param,
                                        'rate': float(recommended)
                                    })
                                except (ValueError, TypeError):
                                    pass
                    
                    # Create basal profile from the parsed rates
                    basalprofile = []
                    if basal_rates:
                        for i, basal in enumerate(basal_rates):
                            # Convert time to minutes
                            time_parts = basal['time'].split(':')
                            minutes = int(time_parts[0]) * 60 + (int(time_parts[1]) if len(time_parts) > 1 else 0)
                            
                            basalprofile.append({
                                'i': i,
                                'minutes': float(minutes),
                                'start': f"{basal['time']}:00" if ':' in basal['time'] else f"{basal['time'][:2]}:{basal['time'][2:]}:00",
                                'rate': basal['rate']
                            })
                    else:
                        # Default single basal rate if no rates found
                        basalprofile = [{'i': 0, 'minutes': 0.0, 'start': '00:00:00', 'rate': 0.5}]
                    
                    # Create a complete profile structure
                    base_profile = {
                        'dia': 8.0,
                        'carb_ratio': recommendations_dict.get('carb_ratio', 9.0),
                        'carb_ratios': {
                            'first': 1,
                            'units': 'grams',
                            'schedule': [{'i': 0, 'start': '00:00:00', 'offset': 0.0, 'ratio': recommendations_dict.get('carb_ratio', 9.0)}]
                        },
                        'isfProfile': {
                            'first': 1,
                            'sensitivities': [{'i': 0, 'sensitivity': recommendations_dict.get('isf', 41.4), 'offset': 0.0, 'start': '00:00:00'}]
                        },
                        'basalprofile': basalprofile,
                        'bg_targets': {
                            'units': 'mmol',
                            'user_preferred_units': 'mmol',
                            'targets': [{'i': 0, 'start': '00:00:00', 'offset': 0.0, 'low': 4.5, 'min_bg': 4.5, 'high': 5.0, 'max_bg': 5.0}]
                        },
                        'timezone': get_system_timezone(),  # Auto-detect from /etc/localtime or use environment/UTC fallback
                        'min_5m_carbimpact': 8.0,
                        'autosens_max': 1.2,
                        'autosens_min': 0.7
                    }
                    
                    # Create Nightscout-compatible profile JSON
                    profile_name = f"Autotune_{datetime.now().strftime('%Y%m%d_%H%M')}"
                    
                    # Convert OpenAPS format to Nightscout format
                    nightscout_profile = {
                        "defaultProfile": profile_name,
                        "startDate": datetime.now().isoformat() + "Z",
                        "mills": int(datetime.now().timestamp() * 1000),
                        "store": {
                            profile_name: {
                                "dia": base_profile['dia'],
                                "carbratio": [{"time": "00:00", "value": base_profile['carb_ratio'], "timeAsSeconds": 0}],
                                "carbs_hr": 30,
                                "delay": 20,
                                "sens": [{"time": "00:00", "value": base_profile['isfProfile']['sensitivities'][0]['sensitivity'], "timeAsSeconds": 0}],
                                "timezone": base_profile['timezone'],
                                "basal": [
                                    {
                                        "time": basal['start'][:5],  # Convert "00:00:00" to "00:00"
                                        "value": basal['rate'],
                                        "timeAsSeconds": int(basal['minutes'] * 60)
                                    }
                                    for basal in base_profile['basalprofile']
                                ],
                                "target_low": [{"time": "00:00", "value": 4.5, "timeAsSeconds": 0}],
                                "target_high": [{"time": "00:00", "value": 5.0, "timeAsSeconds": 0}],
                                "units": "mmol"
                            }
                        }
                    }
                    
                    # Format JSON for display
                    json_display = json.dumps(nightscout_profile, indent=2)
                    
                    return False, json_display
                except Exception as e:
                    return False, f"Error generating profile: {str(e)}"
            else:
                return False, "No recommendations data available"
        
        elif trigger_id == 'back-to-results':
            return True, ""
        
        return True, ""

    @app.callback(
        Output("download-profile", "data"),
        Input("download-profile-json", "n_clicks"),
        State('profile-json-display', 'value'),
        prevent_initial_call=True,
    )
    def download_profile_json(n_clicks, json_content):
        """Download the generated profile as JSON file"""
        if n_clicks and json_content:
            datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"autotune_profile_{datetime_string}.json"
            return dict(content=json_content, filename=filename)
        return dash.no_update

    @app.callback(
        [Output("upload-instructions-modal", "is_open"),
         Output("upload-instructions-body", "children")],
        [Input("show-upload-instructions", "n_clicks"),
         Input("close-upload-instructions", "n_clicks")],
        [State("upload-instructions-modal", "is_open"),
         State('input-url', 'value')],
        prevent_initial_call=True,
    )
    def toggle_upload_instructions(show_clicks, close_clicks, is_open, ns_url):
        """Show/hide upload instructions modal"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return False, []
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == 'show-upload-instructions' and show_clicks:
            # # Generate upload instructions - disabled
            # from profile_manager import ProfileManager
            # profile_manager = ProfileManager()
            # instructions = profile_manager.get_upload_instructions(ns_url or "https://your-nightscout-site.com")
            instructions = {"url": ns_url or "https://your-nightscout-site.com", "headers": {}, "data": {}}
            
            instruction_content = [
                html.H5("HTTP POST Request Details:"),
                html.P(f"URL: {instructions['url']}"),
                html.P("Method: POST"),
                html.P("Headers:"),
                html.Ul([
                    html.Li("Content-Type: application/json"),
                    html.Li("API-SECRET: [Your API Secret]")
                ]),
                html.Hr(),
                html.H5("cURL Example:"),
                dcc.Textarea(
                    value=instructions['curl_example'],
                    style={'width': '100%', 'height': '120px', 'fontFamily': 'monospace'},
                    readOnly=True
                ),
                html.Hr(),
                html.H5("Important Notes:"),
                html.Ul([html.Li(note) for note in instructions['notes']]),
                html.Hr(),
                html.H5("Alternative: Manual Upload via Nightscout Web Interface"),
                html.Ol([
                    html.Li("Log into your Nightscout site"),
                    html.Li("Go to Profile Editor (hamburger menu → Profile)"),
                    html.Li("Create a new profile or clone an existing one"),
                    html.Li("Manually enter the values from the JSON above"),
                    html.Li("Save and activate the new profile")
                ])
            ]
            
            return True, instruction_content
        
        elif trigger_id == 'close-upload-instructions':
            return False, []
        
        return is_open, []

    # Profile Name Selection Callback
    @app.callback(
        [Output('new-profile-input', 'style'),
         Output('existing-profile-dropdown', 'style'),
         Output('existing-profile-select', 'options')],
        [Input('profile-name-option', 'value')],
        [State('input-url', 'value'),
         State('token', 'value')],
        prevent_initial_call=True,
    )
    def toggle_profile_name_input(option_value, ns_url, token):
        """Show/hide profile name inputs based on selection"""
        if option_value == 'new':
            return {'display': 'block'}, {'display': 'none'}, []
        else:
            # Load existing profiles from Nightscout
            profile_options = []
            if ns_url and token:
                try:
                    from get_profile import get_all_profiles
                    
                    # Format token for API call
                    token_param = f"token={token}" if token and not token.startswith("token=") else token
                    
                    all_profiles = get_all_profiles(ns_url, token_param)
                    
                    if all_profiles:
                        # Get unique profile names
                        unique_profiles = {}
                        for profile in all_profiles:
                            profile_name = profile['name']
                            if profile_name not in unique_profiles or profile['isDefault']:
                                # Keep the default profile or the first occurrence
                                unique_profiles[profile_name] = profile
                        
                        # Create dropdown options
                        profile_options = []
                        for profile_name, profile_data in unique_profiles.items():
                            label = f"{profile_name}"
                            if profile_data['isDefault']:
                                label += " (Default)"
                            if profile_data['startDate']:
                                label += f" - {profile_data['startDate'][:10]}"
                            
                            profile_options.append({
                                'label': label,
                                'value': profile_name
                            })
                        
                        # Sort options - default first, then alphabetically
                        profile_options.sort(key=lambda x: (not '(Default)' in x['label'], x['label']))
                    else:
                        profile_options = [{'label': 'No profiles found', 'value': '', 'disabled': True}]
                        
                except Exception as e:
                    print(f"Error loading existing profiles: {e}")
                    profile_options = [{'label': f'Error: {str(e)}', 'value': '', 'disabled': True}]
            
            return {'display': 'none'}, {'display': 'block'}, profile_options

    # API Secret Clearing Callback
    @app.callback(
        Output('input-API-secret', 'value'),
        [Input('profile-name-option', 'value')],
        prevent_initial_call=True,
    )
    def clear_api_secret_on_profile_change(option_value):
        """Clear API secret when switching to 'Update Existing Profile' to force re-entry"""
        if option_value == 'existing':
            return ''  # Clear the field to force fresh entry
        else:
            # Keep existing value for new profiles
            return "••••••••••••••••" if os.environ.get('API_SECRET') else ''

    # Profile Selection Dropdown Population Callback
    @app.callback(
        [Output('profile-selection-dropdown', 'options'),
         Output('load-selected-profile', 'disabled')],
        [Input('input-url', 'value'),
         Input('token', 'value'),
         Input('profile-selection-dropdown', 'value')],
        prevent_initial_call=False,
    )
    def populate_profile_selection_dropdown(ns_url, token, selected_profile):
        """Populate the profile selection dropdown with available profiles"""
        
        # Use environment variable if form shows masked placeholder
        if token == "••••••••••••••••":
            token = os.environ.get('API_SECRET', '')
        
        profile_options = []
        load_button_disabled = True
        
        if ns_url and token:
            try:
                from get_profile import get_all_profiles
                
                # Format token for API call
                token_param = f"token={token}" if token and not token.startswith("token=") else token
                
                all_profiles = get_all_profiles(ns_url, token_param)
                
                if all_profiles:
                    # Get unique profile names
                    unique_profiles = {}
                    for profile in all_profiles:
                        profile_name = profile['name']
                        if profile_name not in unique_profiles or profile['isDefault']:
                            unique_profiles[profile_name] = profile
                    
                    # Create dropdown options
                    for profile_name, profile_data in unique_profiles.items():
                        label = f"{profile_name}"
                        if profile_data['isDefault']:
                            label += " (Current Default)"
                        if profile_data['startDate']:
                            label += f" - {profile_data['startDate'][:10]}"
                        
                        profile_options.append({
                            'label': label,
                            'value': profile_name
                        })
                    
                    # Sort options - default first, then alphabetically
                    profile_options.sort(key=lambda x: (not 'Current Default' in x['label'], x['label']))
                    
                    # Enable load button if a profile is selected
                    load_button_disabled = not selected_profile
                    
            except Exception as e:
                print(f"Error loading profiles for dropdown: {e}")
                profile_options = [{'label': f'Error loading profiles: {str(e)[:50]}...', 'value': '', 'disabled': True}]
        else:
            profile_options = [{'label': 'Enter Nightscout URL and token first', 'value': '', 'disabled': True}]
        
        return profile_options, load_button_disabled

    # Callback for mode info toggle
    @app.callback(
        Output('mode-info-collapse', 'is_open'),
        Input('mode-info-button', 'n_clicks'),
        State('mode-info-collapse', 'is_open'),
    )
    def toggle_mode_info(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    return app.server


