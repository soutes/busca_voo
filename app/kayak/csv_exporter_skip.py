import pandas as pd
import os

def export_logs_to_csv_skiplagged(logs_by_dest, filename="euro_volta_skip.csv"):
    all_logs = []
    for dest, log_list in logs_by_dest.items():
        for record in log_list:
            record_with_dest = record.copy()
            record_with_dest['destination'] = dest
            all_logs.append(record_with_dest)
    
    if not all_logs:
        print("Nenhum dado para exportar.")
        return
    
    df = pd.DataFrame(all_logs)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)
    
    # Verifica se o arquivo já existe
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename, parse_dates=['timestamp'])
        df_combined = pd.concat([existing_df, df], ignore_index=True)
        df_combined.drop_duplicates(inplace=True)
        df_combined.sort_values('timestamp', inplace=True)
        df_combined.to_csv(filename, index=False)
        print(f"Dados combinados exportados para {filename}")
    else:
        df.to_csv(filename, index=False)
        print(f"Dados exportados para {filename}")
