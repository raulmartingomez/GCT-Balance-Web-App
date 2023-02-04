# bokeh serve --show GCTBalance_web_app.py
from bokeh.io import curdoc
from bokeh.models.widgets import FileInput
from bokeh.models import ColumnDataSource, DataTable, TableColumn, Label, Div
from bokeh.layouts import column, row 
from bokeh.models import Column, Row
import base64
import io
from numpy.lib.utils import source
import pandas as pd
from pandas.io.pytables import Table


# Initialize the plot variable
plot = None

df_all = pd.DataFrame()
df_basic = pd.DataFrame()
df_stats = pd.DataFrame()
df = pd.DataFrame()
source1 = ColumnDataSource(df)
columns = [TableColumn(field=col, title=col) for col in df.columns]
file_input1 = FileInput(accept=".csv", width=400)
# Create a label for displaying progress
progress_bar = Div(text="", width=500, height=30, style={'background-color': 'lightgray', 'border': '1px solid black'})

def update_progress(percent):
    # progress_bar.text = f"<div style='background-color: lightblue; width: {percent}%; height: 100%;'></div>"
    progress_bar.text = str(percent)
    progress_bar.update()
    

def upload_data1(attr, old, new):
    global df_basic, df_all, df_stats
    global file_path
    global time_start
    global time_end
    global time_slider
    global table_widget
    last_altitud = 0
    slope_data = 0
    speed_data = 0
    time_start = 0
    # Reference for slope calculation
    incline_speed_ref=0.2
    decoded = base64.b64decode(new)
    f = io.BytesIO(decoded)
    df = pd.read_csv(f)
    print(df.shape)
    n = len(df)
    for index, row in df.iterrows():
        row_list = row.tolist()
        row = row_list
        percent = (index + 1) / n * 100
        update_progress(percent)
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
    print(df_all.shape)
    print(df_stats) 
    source1.data = df_stats
    data_table1.columns =[TableColumn(field=col, title=col) for col in df_stats.columns]

file_input1.on_change('value', upload_data1)
data_table1 = DataTable(source=source1, columns=columns, width=400, height=1000)

# Layout of the app
curdoc().add_root(column(row(file_input1), row(progress_bar), row(data_table1)))


