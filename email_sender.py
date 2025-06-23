import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_emails_with_notices():
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"当前日期: {today}")
    
    try:
        # 连接数据库
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456',  # 数据库密码
            database='spider_db',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 首先查看所有通知
            debug_query = "SELECT title, publish_date FROM notices ORDER BY publish_date DESC LIMIT 5"
            cursor.execute(debug_query)
            debug_results = cursor.fetchall()
            print("\n最近5条通知:")
            for row in debug_results:
                print(f"标题: {row[0]}, 发布日期: {row[1]}")
            
            # 查询当天发布且包含"课题"的通知
            query = """
            SELECT title, url 
            FROM notices 
            WHERE DATE(publish_date) = %s AND title LIKE %s
            """
            cursor.execute(query, (today, '%课题%'))
            results = cursor.fetchall()
            
            if results:
                # 准备邮件内容
                subject = f"今日课题通知 ({today})"
                body = "今日发现以下课题相关通知：\n\n"
                
                for row in results:
                    title, url = row
                    body += f"• {title}\n  {url}\n\n"
                
                # 发送邮件
                sender_email = "2191370750@qq.com"  # 发送QQ邮箱
                receiver_email = "1103569500@qq.com"  # 接收邮箱
                password = "dsjneitbsyxfdjai"  # QQ邮箱授权码
                
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = receiver_email
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain", "utf-8"))
                
                # 连接QQ邮箱SMTP服务器
                with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_email, message.as_string())
                
                print(f"成功发送邮件，包含 {len(results)} 条通知")
            else:
                print("今日没有符合条件的课题通知")

    except Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"发送邮件时出错: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    send_emails_with_notices()