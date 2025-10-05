from flask import Flask , request , render_template , redirect , url_for , flash , send_file
import pandas as pd
import os
import io

app = Flask(__name__)
app.secret_key = 'iamlokesh'

allowed = {'csv' ,'xlsx' , 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def perform_cleaning(df , operations , missing_strategy):
    df_cleaned = df.copy()
    if 'remove_duplicates' in operations:
        df_cleaned = df_cleaned.drop_duplicates()
    if 'trim_whitespace' in operations:
        for col in df_cleaned.select_dtypes(include=['object']):
            df_cleaned[col] = df_cleaned[col].str.strip()
    if 'handle_missing' in operations:
        
        if missing_strategy == 'remove_row':
            df_cleaned.dropna(inplace=True)
        else:
            for col in df_cleaned.columns:
                if df_cleaned[col].isnull().any():
                    fill_value = None
                    is_numeric = pd.api.types.is_numeric_dtype(df_cleaned[col])

                    if missing_strategy == 'fill_mean' and is_numeric:
                        fill_value = df_cleaned[col].mean()
                    elif missing_strategy == 'fill_median' and is_numeric:
                        fill_value = df_cleaned[col].median()
                    elif missing_strategy == 'fill_mode':
                        # mode() can return multiple values, we take the first one
                        if not df_cleaned[col].mode().empty:
                            fill_value = df_cleaned[col].mode()[0]
                    
                    if fill_value is not None:
                        df_cleaned[col] = df_cleaned[col].fillna(fill_value)
                        
    return df_cleaned

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/clean' , methods=['POST'])
def clean():
    if 'file' not in request.files:
        flash('No file part in the request')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            filename = file.filename
            df = None
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.lower().endswith(('.xlsx' , '.xls')):
                df = pd.read_excel(file)
            
            operations = request.form.getlist('operations')
            missing_strategy = request.form.get('missing_strategy' , 'remove_row') 
            df_cleaned = perform_cleaning(df, operations, missing_strategy)
            buffer = io.StringIO()
            df_cleaned.to_csv(buffer, index=False)
            buffer.seek(0)
            
            mem_file = io.BytesIO()
            mem_file.write(buffer.getvalue().encode('utf-8'))
            mem_file.seek(0)

            # Create the name for the downloaded file
            original_filename = os.path.splitext(filename)[0]
            download_filename = f"cleaned_{original_filename}.csv"

            # Send the buffer as a file download
            return send_file(
                mem_file,
                mimetype='text/csv',
                as_attachment=True,
                download_name=download_filename
            )
        
        except Exception as e:
            flash(f'Error processing file: {e}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file format. Please upload a CSV or Excel file.')
        return redirect(url_for('index'))
    
if __name__ == '__main__':
    app.run(debug=True)
