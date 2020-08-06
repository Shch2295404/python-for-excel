from pathlib import Path
import pandas as pd

# Directory of this file
this_dir = Path(__file__).parent

# Read in all files
parts = []
for path in (this_dir / 'sales_data').rglob('*.xls*'):
    part = pd.read_excel(path)
    parts.append(part)

# Combine the DataFrames from each file into a single DataFrame
df = pd.concat(parts)

# Pivot each store into a column and sum up all transaction per date
pivot = pd.pivot_table(df,
                       index='transaction_date', columns='store',
                       values='amount', aggfunc='sum')

# Resample to end of month and assign an index name 
summary = pivot.resample('M').sum()
summary.index.name = 'Month'

# DataFrame position and number of rows/columns
# xlsxwriter uses 0-based indices
startrow = 2
startcol = 1
nrows, ncols = summary.shape

with pd.ExcelWriter(this_dir / 'sales_report_xlsxwriter.xlsx',
                    engine='xlsxwriter', datetime_format='mmm yy') as writer:
    summary.to_excel(writer, sheet_name='Sheet1',
                     startrow=startrow, startcol=startcol)

    # Get xlsxwriter book and sheet object 
    book = writer.book
    sheet = writer.sheets['Sheet1']

    # Set title
    title_format = book.add_format({'bold': True, 'size': 24})
    sheet.write(0, startcol, 'Sales Report', title_format)

    # Sheet formatting
    # 2: hides on screen and when printing
    sheet.hide_gridlines(2)

    # Format the DataFrame with
    # - number format
    # - column width
    # - conditional formatting
    number_format = book.add_format({'num_format': '#,##0',
                                     'align': 'center'})
    below_target_format = book.add_format({'font_color': '#E93423'})
    sheet.set_column(first_col=startcol, last_col=startcol + ncols,
                     width=14, cell_format=number_format)
    sheet.conditional_format(first_row=startrow + 1,
                             first_col=startcol + 1,
                             last_row=startrow + nrows,
                             last_col=startcol + ncols,
                             options={'type': 'cell', 'criteria': '<=',
                                      'value': 20000,
                                      'format': below_target_format})

    # Chart
    chart = book.add_chart({'type': 'column'})
    chart.set_title({'name': 'Sales per Month and Store'})
    chart.set_size({'width': 700, 'height': 450})
    
    # Add each column of the data table as a series
    for col in range(1, ncols + 1):
        chart.add_series({
             # [sheetname, first_row, first_col, last_row, last_col]
            'name': ['Sheet1', startrow, startcol + col],
            'categories': ['Sheet1', startrow + 1, startcol,
                           startrow + nrows, startcol],
            'values': ['Sheet1', startrow + 1, startcol + col,
                       startrow + nrows, startcol + col],
        })
    # Chart formatting
    chart.set_x_axis({'name': summary.index.name,
                      'major_tick_mark': 'none'})
    chart.set_y_axis({'name': 'Sales',
                      'line': {'none': True},
                      'major_gridlines': {'visible': True},
                      'major_tick_mark': 'none'})
    
    # Add the chart to the sheet
    sheet.insert_chart(startrow + nrows + 2, startcol, chart)