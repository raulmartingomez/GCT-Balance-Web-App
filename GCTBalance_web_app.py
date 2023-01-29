# panel serve GCTBalance_web_app.py
# http://localhost:5006/test2
import pandas as pd
import csv
from subprocess import *
import os
import csv
import panel as pn
pn.extension('tabulator')
from bokeh.plotting import figure, show
from bokeh.models.annotations import Label
from bokeh.models import Div
#import holoviews as hv
#import hvplot.pandas

# Initialize the plot variable
plot = None

df_all = pd.DataFrame()
df_basic = pd.DataFrame()
df_stats = None

# Create a file input widget using the panel.widgets.FileInput widget
file_input = pn.widgets.FileInput()

# Define Panel widgets
time_slider = pn.widgets.IntSlider(name='Time slider', start=100, end=1000, step=10, value=500)

# Create a Markdown pane to display the file path
file_path_pane = pn.pane.Markdown("No file selected")

# Define a callback function that will be called when the user selects a file
@pn.depends(file_input)
def on_select(file):

    global df_basic, df_all, df_stats
    global file_path
    global time_start
    global time_end
    global time_slider
    global table_widget
    # Creates de variables
    #altitud = 0
    last_altitud = 0
    slope_data = 0
    speed_data = 0
    time_start = 0

    # Creates the DataFrames
    df_all = pd.DataFrame()
    df_basic = pd.DataFrame()
    df_stats = pd.DataFrame()

    # Reference for slope calculation
    incline_speed_ref=0.2
    if file is not None:
        p = Popen([r'FitToCSV.bat', file_input.filename], stdout=PIPE, stderr=PIPE)
        output, errors = p.communicate()
        p.wait() # wait for process to terminate
        file_name = os.path.splitext(file_input.filename)[0]
        # Open csv file and get the information
        with open(file_name + r".csv") as csv_file:
            csv_reader=csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if "timestamp" in row:
                    if int(row[row.index("timestamp")+1]) > 1:
                        time = int(row[row.index("timestamp")+1])
                        if time_start == 0:
                                time_start = time
                if "altitude" in row:
                    altitud = float(row[row.index("altitude")+1])           
                    if time == time_start:
                        altitudes_anteriores = [altitud, altitud]
                if "speed" in row:
                    speed = float(row[row.index("speed")+1])
                    if speed>0:
                        speed = (1000 / (60 *speed))                
                if "stance_time_balance" in row:
                    balance = round(float(row[row.index("stance_time_balance")+1]), 2)    
                    if balance > 30 and balance < 70:                                   
                        if ((altitud - altitudes_anteriores[0]) > (incline_speed_ref + 0.1)) or ((altitud - altitudes_anteriores[1]) > (incline_speed_ref + 0.0)):                 
                            slope_data = 1                    
                        elif ((altitud - altitudes_anteriores[0]) < -(incline_speed_ref + 0.1)) or ((altitud - altitudes_anteriores[1]) < -(incline_speed_ref + 0.0)):                    
                            slope_data = 2                   
                        else:                   
                            slope_data = 3                   
                        altitudes_anteriores[1] = altitudes_anteriores[0]
                        altitudes_anteriores[0] = altitud
                        if speed > 6:
                                speed_data =  1
                        if speed <= 6 and speed > 5:
                                speed_data =  2
                        if speed <= 5 and speed > 4.5:
                                speed_data =  3
                        if speed <= 4.5 and speed > 4:
                                speed_data =  4
                        if speed <= 4 and speed > 0:
                                speed_data =  5
                    else:
                        balance = 0 # If balance is <30 or >70, balance = 0 and the data is not stored in the df

                    if time > 0 and balance > 0 and slope_data > 0 and speed_data > 0:
                        data = [{'Time_Garmin': time, 'Time_Absolute': (((time+631065600+(12*60*60))/60/60/24)+25569),'Time_r': (time - time_start), 'Balance': balance,'Altitud': altitud ,'Num_Slope': slope_data, 'Speed': speed ,'Num_Speed': speed_data}]
                        new_row = pd.DataFrame(data)

                        data2 = [{'Time_Garmin': time, 'Time_Absolute': (((time+631065600+(12*60*60))/60/60/24)+25569),'Time_r': (time - time_start),'Balance': balance, 'Slope': slope_data, 'Speed': speed_data}]
                        new_row2 = pd.DataFrame(data2)

                        df_all = pd.concat([df_all, new_row], ignore_index=True)
                        df_basic = pd.concat([df_basic, new_row2], ignore_index=True)  

            data = [{'Stat': 'GCT Balance', 'Mean': round(df_basic['Balance'].mean(),2),'STD': round(df_basic['Balance'].std(),2), 'Number of data': df_basic['Balance'].count()}]
            df_stats = pd.DataFrame(data)
            list_stats = [('Slope',1,'GCT Balance UP'),('Slope',2,'GCT Balance DOWN') ,('Slope',3,'GCT Balance FLAT'),('Speed',1, 'Speed1 > 6min/km'),('Speed',2, '6 > Speed2 > 5min/km'),('Speed',3, '5 > Speed3 > 4:30min/km'),('Speed',4, '4:30 > Speed4 > 4min/km'),('Speed',5, '4min/km > Speed5')]
            for i, element in enumerate(list_stats): 
                mean = df_basic[df_basic[element[0]] == element[1]]['Balance'].mean()
                std = df_basic[df_basic[element[0]] == element[1]]['Balance'].std()
                num_data = df_basic[df_basic[element[0]] == element[1]][element[0]].count()
                data = [{'Stat': element[2], 'Mean': round(mean,2),'STD': round(std,2), 'Number of data': num_data}]
                new_row = pd.DataFrame(data)
                df_stats = pd.concat([df_stats, new_row], ignore_index=True)
            
            # Create a new column 'color' that maps the values of the 'Slope' column to specific colors
            df_all['Slope_color'] = df_all['Num_Slope'].map({1: 'red', 2: 'green', 3: 'blue'})
            print(df_stats) 

        create_plot("")       
        # Update the plot widget
        plot_widget.object = plot   
        table_widget._update_data(df_stats)
          
    else:
        print("No file selected")

from bokeh.models import HoverTool
from bokeh.models import LinearAxis, Label
from bokeh.models import Range1d

def create_plot(value):
    global plot   
    print ("create_plo called")
    print (value) 
    plot = figure(title="GCT Balance", x_axis_label="Time (s)", y_axis_label="R     % Balance     L", plot_width=1100, plot_height=350)
    # Pass the 'color' column as the color parameter to the scatter method
    plot.scatter(x=df_all['Time_r'], y=df_all['Balance'], color=df_all['Slope_color'], size=1, alpha=0.8)
    hover = HoverTool(tooltips=[("Time", "@x{0.0}s"), ("Balance", "@y{0.1}%")])
    if value == 'Elevation':
        print ("Yes, the code is inside the conditional Elevation")
        plot.scatter(x=df_all['Time_r'], y=df_all['Altitud'], size=0.2, alpha=0.8, y_range_name="elevation", color='grey')
        plot.yaxis.y_range_name = 'elevation'
        plot.extra_y_ranges = {"elevation": Range1d(start=min(df_all['Altitud']), end=max(df_all['Altitud']))}
        plot.add_layout(LinearAxis(y_range_name="elevation", axis_label='Elevation'), 'right')
        hover = HoverTool(tooltips=[("Time", "@x{0.0}s"), ("Balance", "@y{0.1}%"), ("Elevation", "@y{0.1}m"), ("Speed", "@y{0.1}km/h")])
    elif value == 'Speed':
        print ("Yes, the code is inside the conditional Speed")
        plot.scatter(x=df_all['Time_r'], y=df_all['Speed'], size=0.2, alpha=0.8, y_range_name="speed", color='grey')
        plot.yaxis.y_range_name = 'speed'
        plot.extra_y_ranges = {"speed": Range1d(start=min(df_all['Speed']), end=max(df_all['Speed']))}
        plot.add_layout(LinearAxis(y_range_name="speed", axis_label='Speed'), 'right')
        hover = HoverTool(tooltips=[("Time", "@x{0.0}s"), ("Balance", "@y{0.1}%"), ("Speed", "@y{0.1}km/h")])
    plot.line(x=df_all['Time_r'], y=[50 for _ in range(len(df_all))], line_color='black', line_width=0.5)
    plot.add_tools(hover)
    plot.y_range.start = 44
    plot.y_range.end = 56
    label1 = Label(x=10, y=50, x_units='screen', y_units='screen', text="Balance Up", text_color="red", text_font_size="10pt")
    label2 = Label(x=10, y=30, x_units='screen', y_units='screen', text="Balance Down", text_color="green", text_font_size="10pt")
    label3 = Label(x=10, y=10, x_units='screen', y_units='screen', text="Balance Flat", text_color="blue", text_font_size="10pt")
    plot.add_layout(label1)
    plot.add_layout(label2)
    plot.add_layout(label3)
    plot_widget.object = plot     

extra_data = pn.widgets.RadioButtonGroup(
    name='Extra data', 
    options=['      ', 'Elevation','Speed'],
    button_type='success'
)

def on_change(event):
    print ("on change called")
    print (event)
    create_plot(event.new)
    
extra_data.param.watch(on_change, 'value')


# Create a Bokeh widget to display the plot
plot_widget = pn.pane.Bokeh(plot)

type_balance = pn.widgets.RadioButtonGroup(
    name='Type of Balance', 
    options=['Balance Up/Down/Flat', 'Balance vs Speed'],
    button_type='success'
)



data = [{'Stat': '', 'Mean': '','STD': '', 'Number of data': ''}]
df_stats = pd.DataFrame(data)
print (df_stats)
table_widget = pn.widgets.Tabulator(df_stats,show_index=False)

template = pn.template.FastListTemplate(
    title='GCT Balance', 
    sidebar=[pn.pane.Markdown("# GCT Balance"), 
             pn.pane.Markdown("Explanation"),
             pn.pane.Markdown("## Settings"),
             pn.Column(file_input, on_select),
             type_balance,
             extra_data],
    main=[plot_widget, table_widget],  
    accent_base_color="#88d8b0",
    header_background="#88d8b0",
)

template.servable();
