import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os
import time
import argparse
import mysql.connector
from mysql.connector import Error

def create_database_connection():
    """创建数据库连接"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # MySQL用户名
            password='your_password',  # MySQL密码
            database='your_database'  # 数据库名称
        )
        return connection
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

def create_tables(connection):
    """创建必要的数据表"""
    try:
        cursor = connection.cursor()
        
        # 创建通知表
        create_notices_table = """
        CREATE TABLE IF NOT EXISTS notices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            notice_type VARCHAR(50),
            publish_date DATE,
            deadline_date DATE,
            contact_person VARCHAR(255),
            url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_notices_table)
        connection.commit()
        print("数据表创建成功")
        
    except Error as e:
        print(f"创建表时出错: {e}")
    finally:
        if cursor:
            cursor.close()

def save_to_mysql(connection, notification):
    """保存通知到MySQL数据库"""
    try:
        cursor = connection.cursor()
        
        # 转换日期格式
        publish_date = convert_date_format(notification['发布日期'])
        deadline_date = convert_date_format(notification['截止日期'])
        
        # 将空字符串转换为None
        publish_date = None if not publish_date else publish_date
        deadline_date = None if not deadline_date else deadline_date
        
        # 准备SQL语句
        insert_query = """
        INSERT INTO notices (title, notice_type, publish_date, deadline_date, contact_person, url)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # 准备数据
        values = (
            notification['项目名称'],
            notification['项目类型'],
            publish_date,
            deadline_date,
            notification['联系人'],
            notification['网页URL']
        )
        
        cursor.execute(insert_query, values)
        connection.commit()
        print(f"成功保存通知: {notification['项目名称']}")
        
    except Error as e:
        print(f"保存数据时出错: {e}")
    finally:
        if cursor:
            cursor.close()

def clean_title(title):
    # Remove specific phrases from title
    patterns_to_remove = [
        r'关于组织',
        r'关于',
        r'工作的通知',
        r'的通知'
    ]
    cleaned_title = title
    for pattern in patterns_to_remove:
        cleaned_title = re.sub(pattern, '', cleaned_title)
    return cleaned_title.strip()

def determine_notice_type(title):
    # Define keywords for each type
    type_keywords = {
        '课题申报': ['申报', '课题', '项目申报'],
        '项目结题': ['结题', '结项'],
        '成果认定': ['认定', '认证'],
        '成果评级': ['评级', '评奖', '评优']
    }
    
    for notice_type, keywords in type_keywords.items():
        if any(keyword in title for keyword in keywords):
            return notice_type
    return '其他'

def extract_dates(content):
    # 专门提取截止日期
    deadline_patterns = [
        r'截止[日期时间至到]\s*[为是]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
        r'截至[日期时间至到]\s*[为是]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
        r'提交[日期时间至到]\s*[为是]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
        r'申报[日期时间至到]\s*[为是]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
        r'申请[日期时间至到]\s*[为是]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
        r'于\s*(\d{4}年\d{1,2}月\d{1,2}日)\s*前',
        r'在\s*(\d{4}年\d{1,2}月\d{1,2}日)\s*前',
        r'(\d{4}年\d{1,2}月\d{1,2}日)\s*前',
    ]
    
    deadline_date = ''
    for pattern in deadline_patterns:
        match = re.search(pattern, content)
        if match:
            deadline_date = match.group(1)
            break
    
    return deadline_date

def extract_contact(content):
    # 1. 先找"联系人"字样
    contact_patterns = [
        r'联系人[：:：]\s*([\u4e00-\u9fa5A-Za-z]+老师)',
        r'联系人[：:：]\s*([\u4e00-\u9fa5A-Za-z]+)',
        r'联系人[：:：]\s*([\u4e00-\u9fa5A-Za-z]+)\s*电话',
        r'联系人[：:：]\s*([\u4e00-\u9fa5A-Za-z]+)\s*邮箱',
    ]
    for pattern in contact_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    
    # 2. 再找"某某老师"
    teacher_patterns = [
        r'([\u4e00-\u9fa5A-Za-z]+老师)\s*电话',
        r'([\u4e00-\u9fa5A-Za-z]+老师)\s*邮箱',
        r'([\u4e00-\u9fa5A-Za-z]+老师)',
    ]
    for pattern in teacher_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    
    # 3. 找"电话：xxx 联系人：xxx"格式
    phone_contact_pattern = r'电话[：:：]\s*\d+\s*联系人[：:：]\s*([\u4e00-\u9fa5A-Za-z]+)'
    match = re.search(phone_contact_pattern, content)
    if match:
        return match.group(1).strip()
    
    return ''

def convert_date_format(date_str):
    """支持'2024年05月26日'、'2024.05.26'、'2024/5/26'三种格式，转换为'20240526'"""
    if not date_str:
        return ''
    date_str = date_str.strip('()')
    # 先匹配 2024年05月26日
    match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}{month}{day}"
    # 再匹配 2024.05.26
    match = re.match(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', date_str)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}{month}{day}"
    # 再匹配 2024/5/26 或 2024/05/26
    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}{month}{day}"
    return ''

def scrape_notifications(mode='history'):
    # 创建数据库连接
    connection = create_database_connection()
    if not connection:
        print("无法连接到数据库，程序退出")
        return
        
    # 创建数据表
    create_tables(connection)
    
    base_url = 'http://your_university'#你的学校通知网址
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # 用于存储按日期分类的通知
        notifications_by_date = {}
        page = 1
    
        
        while True:
            # 构建分页URL
            url = f"{base_url}_{page}.html" if page > 1 else f"{base_url}.html"
            print(f"\nProcessing page {page}...")
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the notification list
            notice_list = soup.find('div', class_='xw-list')
            if not notice_list:
                break
                
            notice_items = notice_list.find_all('li')
            if not notice_items:
                break
                
            print(f"Found {len(notice_items)} notifications on page {page}")
            
            for item in notice_items:
                try:
                    link = item.find('a')
                    if not link:
                        continue
                    
                    title = link.text.strip()
                    if not title:
                        continue
                    
                    # Skip if title contains excluded keywords
                    if any(keyword in title for keyword in ['研讨会', '实践']):
                        continue
                    
                    # Get the full URL
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    full_url = f"https://www.your_university/{href}" if not href.startswith('http') else href
                    #改为你的学校通知网址
                    # Get the date from the span
                    date_span = item.find('span')
                    if not date_span:
                        print(f"Warning: No date found for {title}")
                        continue
                        
                    publish_date = date_span.text.strip('()')
                    if not publish_date:
                        print(f"Warning: Empty date for {title}")
                        continue
                        
                    publish_date_key = convert_date_format(publish_date)
                    if not publish_date_key:
                        print(f"Warning: Could not convert date '{publish_date}' for {title}")
                        continue
                    
                
                    
                    print(f"Processing: {title} (Date: {publish_date_key})")
                    
                    # Get the content of the notice
                    try:
                        content_response = requests.get(full_url, headers=headers, timeout=10)
                        content_response.encoding = 'utf-8'
                        content_soup = BeautifulSoup(content_response.text, 'html.parser')
                        
                        # Try different possible content containers
                        content_div = content_soup.find(['div', 'article'], class_=['article-content', 'content', 'article'])
                        if not content_div:
                            # Try to find any div that might contain the content
                            content_div = content_soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'article' in x.lower()))
                        
                        content = content_div.text if content_div else ''
                        
                        # Process the data
                        cleaned_title = clean_title(title)
                        notice_type = determine_notice_type(title)
                        deadline_date = extract_dates(content)
                        contact = extract_contact(content)
                        
                        notification = {
                            '项目名称': cleaned_title,
                            '项目类型': notice_type,
                            '发布日期': publish_date,
                            '截止日期': deadline_date,
                            '联系人': contact,
                            '网页URL': full_url
                        }
                        
                        # 保存到MySQL
                        save_to_mysql(connection, notification)
                        
                        # 将通知添加到对应日期的列表中（用于CSV备份）
                        if publish_date_key not in notifications_by_date:
                            notifications_by_date[publish_date_key] = []
                        notifications_by_date[publish_date_key].append(notification)
                        print(f"Added notification to {publish_date_key}.csv")
                        
                        # Add a small delay between requests
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"Error processing content for {title}: {str(e)}")
                        continue
                    
                except Exception as e:
                    print(f"Error processing item: {str(e)}")
                    continue
            
            # 检查是否有下一页
            pagination = soup.find('div', class_='pagination')
            if not pagination:
                break
                
            next_page = pagination.find('a', string='>>')
            if not next_page:
                break
                
            page += 1
            time.sleep(1)  # 添加页面间的延迟
        
        # 保存每个日期的通知到对应的CSV文件
        for date_key, notifications in notifications_by_date.items():
            if notifications:
                df = pd.DataFrame(notifications)
                filename = f'{date_key}.csv'
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f'\nSuccessfully saved {len(notifications)} notifications to {filename}')
        
        if not notifications_by_date:
            print('No notifications found')
            
    except Exception as e:
        print(f'Error occurred: {str(e)}')
    finally:
        if connection:
            connection.close()
            print("数据库连接已关闭")

def process_existing_csv(input_file):
    """处理已存在的CSV文件，按发布日期重新分组保存"""
    try:
        # 检查文件是否存在
        if not os.path.exists(input_file):
            print(f"Error: File '{input_file}' does not exist!")
            return
            
        print(f"Reading file: {input_file}")
        # 先尝试utf-8-sig编码读取
        try:
            df = pd.read_csv(input_file, encoding='utf-8-sig')
            print("Read CSV with utf-8-sig encoding.")
        except Exception as e1:
            print(f"utf-8-sig decode failed: {e1}, try gbk...")
            try:
                df = pd.read_csv(input_file, encoding='gbk')
                print("Read CSV with gbk encoding.")
            except Exception as e2:
                print(f"gbk decode failed: {e2}")
                return
        print(f"Found {len(df)} rows in the CSV file")
        
        # 用于存储按日期分类的通知
        notifications_by_date = {}
        
        # 遍历每一行
        for index, row in df.iterrows():
            try:
                publish_date = row['发布日期']
                if not publish_date:
                    print(f"Warning: Empty publish date in row {index + 1}")
                    continue
                    
                print(f"Processing row {index + 1}: {publish_date}")
                # 转换日期格式
                date_key = convert_date_format(publish_date)
                if not date_key:
                    print(f"Warning: Could not convert date '{publish_date}' in row {index + 1}")
                    continue
                
                # 将通知添加到对应日期的列表中
                if date_key not in notifications_by_date:
                    notifications_by_date[date_key] = []
                
                notifications_by_date[date_key].append(row.to_dict())
                print(f"Added to {date_key}.csv")
                
            except Exception as e:
                print(f"Error processing row {index + 1}: {str(e)}")
                continue
        
        # 保存每个日期的通知到对应的CSV文件
        for date_key, notifications in notifications_by_date.items():
            if notifications:
                df = pd.DataFrame(notifications)
                filename = f'{date_key}.csv'
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f'\nSuccessfully saved {len(notifications)} notifications to {filename}')
        
        if not notifications_by_date:
            print('No valid notifications found in the input file')
            
    except Exception as e:
        print(f'Error processing CSV file: {str(e)}')
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape notifications from DUFE website')
    parser.add_argument('--mode', choices=['daily', 'history'], default='daily',
                      help='Scraping mode: daily (only today\'s notifications) or history (all notifications)')
    parser.add_argument('--process-csv', type=str,
                      help='Process an existing CSV file and split by publish date')
    args = parser.parse_args()
    
    if args.process_csv:
        print(f"Processing existing CSV file: {args.process_csv}")
        process_existing_csv(args.process_csv)
    else:
        print(f"Running in {args.mode} mode...")
        scrape_notifications(mode=args.mode) 
