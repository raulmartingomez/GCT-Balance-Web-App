# bokeh serve --show GCTBalance_web_app_bokeh.py
from bokeh.io import curdoc
from bokeh.models.widgets import FileInput
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from bokeh.layouts import column, row 
import base64
import io
from numpy.lib.utils import source
import pandas as pd
from pandas.io.pytables import Table

df = pd.DataFrame()
source1 = ColumnDataSource(df)
columns = [TableColumn(field=col, title=col) for col in df.columns]
file_input1 = FileInput(accept=".csv", width=400)
# Callback
def upload_data1(attr, old, new):
	decoded = base64.b64decode(new)
	f = io.BytesIO(decoded)
	df = pd.read_csv(f)
	source1.data = df.head()
	data_table1.columns =[TableColumn(field=col, title=col) for col in df.columns]
	print(df.shape)

file_input1.on_change('value', upload_data1)
data_table1 = DataTable(source=source1, columns=columns, width=400, height=400)

curdoc().add_root(column(row(file_input1),row(data_table1)))
