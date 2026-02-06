import os
import csv
import pandas as pd

class ReportFiles:
    def __init__(self, report_metrics="report_metrics.csv", responses_dir="reports", header=None):
        self.report_metrics = report_metrics
        self.responses_dir = responses_dir
        self.file_path = os.path.join(self.responses_dir, self.report_metrics)
        
        if header is None:
            self.header = [
                'Datetime_request', 'Input_prompt', 'Total_time_request', 'Step', 'Anomaly_detected',
                'Tool', 'Success', 'Latency', 'Confidence', 'Tokens', 'Calls_API', 'Response'
            ]
        else:
            self.header = header

        os.makedirs(self.responses_dir, exist_ok=True)
               
    def create_report_metrics(self):
        df = pd.DataFrame(columns=self.header)
        df[["Total_time_request", "Latency"]] = df[["Total_time_request", "Latency"]].astype(float)  
        if not os.path.exists(self.file_path):                
            df.to_csv(self.file_path, index=False, mode='w', header=True)                 
        return df
    

    def add_report_metrics(self, df, datetime_request, input_prompt, step, anomaly_detected, tool, success, latency, confidence, tokens, calls_api, response):
        new_index = len(df)
        df.loc[new_index] = {
            'Datetime_request': pd.to_datetime(datetime_request, unit='s'),
            'Input_prompt': input_prompt,
            'Total_time_request': 0,
            'Step': step,
            'Tool': tool,
            'Anomaly_detected': anomaly_detected,
            'Success': success,
            'Latency': latency,
            'Confidence': confidence,
            'Tokens': tokens,
            'Calls_API': calls_api,
            'Response': response
        }
        return new_index

    def update_total_time(self, df, total_time_request):
        df.loc[:, "Total_time_request"] = total_time_request

    def save_file_df(self, df):
        if not os.path.exists(self.file_path):
            df.to_csv(self.file_path, index=False, mode='w', header=True)
        else:
            df.to_csv(self.file_path, index=False, mode='a', header=False)
    
    def read_file_csv(self, directory, file_name):
        file_path = os.path.join(directory, file_name)  
        df = pd.read_csv(file_path)
        return df

