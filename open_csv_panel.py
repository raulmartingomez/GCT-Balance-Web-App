import panel as pn
import base64
import io
import pandas as pd

def process_file(event):
    file_input = event.obj
    decoded = base64.b64decode(file_input.value)
    f = io.BytesIO(decoded)
    df = pd.read_csv(f)
    print(df)

file_input = pn.widgets.FileInput(name='Upload a CSV file')
file_input.param.watch(process_file, 'value')

pn.Column(file_input).servable()
