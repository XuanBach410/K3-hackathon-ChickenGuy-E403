import pandas as pd
import json

def process_topics():
    df = pd.read_excel('DS_K3_Formatted.xlsx')
    # Rename columns to standardized keys
    column_mapping = {
        'STT': 'stt',
        'Khối': 'category',
        'Mã Đề': 'code',
        'Tên Đề Tài': 'title',
        'Mô Tả Bài Toán': 'description',
        'Tech stack gợi ý': 'tech_stack',
        'Yêu cầu đầu ra (Cơ bản + Nâng cao)': 'requirements',
        'Max team / đề tài': 'max_team'
    }
    df = df.rename(columns=column_mapping)
    
    # Fill missing values
    df = df.fillna('')
    
    topics = df.to_dict(orient='records')
    
    with open('topics_data.json', 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"Successfully processed {len(topics)} topics into topics_data.json")

if __name__ == '__main__':
    process_topics()
